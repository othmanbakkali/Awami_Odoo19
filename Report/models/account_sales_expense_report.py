# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import base64
import io
import json
import csv
import xlsxwriter

class AccountSalesExpenseReport(models.Model):
    _name = 'account.sales.expense.report'
    _description = 'Rapport Journalier des Ventes, Dépenses et Charges'
    _order = 'date_generation desc, id desc'

    name = fields.Char(string='Numéro Rapport', required=True, copy=False, default='/')
    report_type = fields.Selection([
        ('x', 'Rapport X (Aperçu Provisoire)'),
        ('z', 'Rapport Z (Clôture Journalière)')
    ], string='Type de Rapport', required=True, default='z')
    date_start = fields.Date(string='Date Début', required=True, default=fields.Date.context_today)
    date_end = fields.Date(string='Date Fin', required=True, default=fields.Date.context_today)
    date_generation = fields.Datetime(string='Date de Génération', default=fields.Datetime.now, readonly=True)
    user_id = fields.Many2one('res.users', string='Utilisateur', default=lambda self: self.env.user, readonly=True)
    company_id = fields.Many2one('res.company', string='Société', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Devise', related='company_id.currency_id', readonly=True)
    
    sale_journal_id = fields.Many2one('account.journal', string='Journal de Vente', domain="[('type', '=', 'sale')]")
    purchase_journal_id = fields.Many2one('account.journal', string='Journal d\'Achat/Charges', domain="[('type', '=', 'purchase')]")
    salesperson_id = fields.Many2one('res.users', string='Commercial / Responsable')
    invoice_state = fields.Selection([
        ('posted', 'Factures comptabilisées'),
        ('paid', 'Factures payées uniquement')
    ], string='État des pièces', required=True, default='posted')
    
    # --- Synthèse Ventes ---
    sales_total_untaxed = fields.Float(string='Ventes HT', readonly=True)
    sales_total_tax = fields.Float(string='TVA Collectée', readonly=True)
    sales_total_gross = fields.Float(string='Ventes Brut TTC', readonly=True)
    sales_refunds_total = fields.Float(string='Avoirs Clients TTC', readonly=True)
    sales_total_net = fields.Float(string='Ventes Nettes TTC', readonly=True)
    sales_total_paid = fields.Float(string='Encaissements Ventes', readonly=True)
    sales_total_residual = fields.Float(string='Crédits Clients Restants', readonly=True)
    invoice_count = fields.Integer(string='Nb Factures Clients', readonly=True)
    refund_count = fields.Integer(string='Nb Avoirs Clients', readonly=True)
    
    # --- Synthèse Charges Fournisseurs ---
    expenses_total_untaxed = fields.Float(string='Charges HT', readonly=True)
    expenses_total_tax = fields.Float(string='TVA Déductible', readonly=True)
    expenses_total_gross = fields.Float(string='Charges Brut TTC', readonly=True)
    expenses_refunds_total = fields.Float(string='Avoirs Fournisseurs TTC', readonly=True)
    expenses_total_net = fields.Float(string='Charges Nettes Fournisseurs TTC', readonly=True)
    expenses_total_paid = fields.Float(string='Décaissements Charges', readonly=True)
    expenses_total_residual = fields.Float(string='Dettes Fournisseurs Restantes', readonly=True)
    vendor_bill_count = fields.Integer(string='Nb Factures d\'Achat / Charges', readonly=True)
    vendor_refund_count = fields.Integer(string='Nb Avoirs Fournisseurs', readonly=True)
    
    # --- Notes de Frais & Dépenses RH (Salaires journaliers, pourboires, maintenance) ---
    hr_expenses_total = fields.Float(string='Notes de Frais & Salaires (RH)', readonly=True)
    hr_expenses_count = fields.Integer(string='Nb Dépenses RH / Salaires', readonly=True)

    # --- Dépenses Directes de Caisse (Menues dépenses) ---
    direct_cash_expenses_total = fields.Float(string='Dépenses Directes de Caisse', readonly=True)
    direct_cash_expenses_count = fields.Integer(string='Nb Dépenses Directes', readonly=True)

    # --- Synthèse Totale Dépenses & Résultat Net ---
    total_expenses_all = fields.Float(string='Total Général Dépenses & Charges', readonly=True)
    net_result = fields.Float(string='Résultat Net Journalier', readonly=True)
    net_cash_flow = fields.Float(string='Flux Net de Trésorerie', readonly=True)
    net_cashbox = fields.Float(string='Solde Net Caisse (Espèces)', readonly=True)

    # Liens many2many
    invoice_ids = fields.Many2many('account.move', 'rel_sales_expense_invoices', 'report_id', 'move_id', string='Factures de Vente Incluses')
    expense_ids = fields.Many2many('account.move', 'rel_sales_expense_bills', 'report_id', 'move_id', string='Factures d\'Achat/Charges Incluses')
    payment_ids = fields.Many2many('account.payment', 'rel_sales_expense_payments', 'report_id', 'payment_id', string='Paiements et Décaissements Directs')
    hr_expense_ids = fields.Many2many('hr.expense', 'rel_sales_expense_hr_expenses', 'report_id', 'expense_id', string='Notes de Frais & Salaires Incluses')

    # Fichiers joints
    pdf_attachment_id = fields.Many2one('ir.attachment', string='Rapport PDF Archivé', readonly=True)
    excel_file = fields.Binary(string='Fichier Excel', readonly=True)
    excel_filename = fields.Char(string='Nom de fichier Excel', readonly=True)
    csv_file = fields.Binary(string='Fichier CSV', readonly=True)
    csv_filename = fields.Char(string='Nom de fichier CSV', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('report_type', 'z') == 'z':
                vals['name'] = self.env['ir.sequence'].next_by_code('account.sales.expense.report') or '/'
            else:
                vals['name'] = "PROVISOIRE (Rapport X) - %s" % fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        reports = super().create(vals_list)
        for rep in reports:
            rep._compute_and_store_report_data()
        return reports

    def _determine_move_payment_mode(self, move, pay_info=None, payment=None):
        """
        Détermine le mode de paiement avec priorité :
        1. Enregistrement account.payment lié (mode explicite, chèque, virement, espèces, effet)
        2. Widget JSON pay_info
        3. Champ payment_mode explicite de la facture (awami_bon_magasin)
        4. Journal de la facture
        """
        # 1. Objet account.payment
        if not payment and move:
            payments = getattr(move, 'matched_payment_ids', False) or getattr(move, 'reconciled_payment_ids', False)
            if payments:
                payment = payments[:1]

        if payment and payment.exists():
            pmode = getattr(payment, 'payment_mode', False)
            if pmode:
                if pmode == 'especes': return 'Espèces'
                elif pmode == 'virement': return 'Virement'
                elif pmode == 'cheque': return 'Chèque'
                elif pmode in ('effet', 'traite', 'effet_cheque'): return 'Effet'

            if payment.journal_id.type == 'cash':
                return 'Espèces'
            name_lower = (payment.journal_id.name or '').lower()
            method_lower = (payment.payment_method_line_id.name or '').lower() if hasattr(payment, 'payment_method_line_id') else ''
            if any(x in name_lower or x in method_lower for x in ['espece', 'espèces', 'cash', 'caisse']):
                return 'Espèces'
            elif any(x in name_lower or x in method_lower for x in ['carte', 'card', 'cb', 'visa', 'mastercard', 'cmi']):
                return 'Carte bancaire'
            elif any(x in name_lower or x in method_lower for x in ['chèque', 'cheque', 'check']):
                return 'Chèque'
            elif any(x in name_lower or x in method_lower for x in ['effet', 'traite', 'lcn']):
                return 'Effet'
            elif any(x in name_lower or x in method_lower for x in ['virement', 'transfer', 'banque', 'bank']):
                return 'Virement'
            else:
                return 'Virement'

        # 2. Widget JSON
        if pay_info:
            jname = (pay_info.get('journal_name') or '').lower()
            if any(x in jname for x in ['cash', 'espèces', 'espece', 'caisse']):
                return 'Espèces'
            elif any(x in jname for x in ['carte', 'card', 'cb', 'visa', 'mastercard', 'cmi']):
                return 'Carte bancaire'
            elif any(x in jname for x in ['chèque', 'cheque', 'check']):
                return 'Chèque'
            elif any(x in jname for x in ['effet', 'traite', 'lcn']):
                return 'Effet'
            else:
                return 'Virement'

        # 3. Mode explicite sur move
        inv_mode = getattr(move, 'payment_mode', False)
        if inv_mode:
            if inv_mode == 'especes':
                return 'Espèces'
            elif inv_mode == 'cheque':
                return 'Chèque'
            elif inv_mode in ('effet', 'traite', 'effet_cheque'):
                return 'Effet'
            elif inv_mode == 'virement':
                return 'Virement'

        # 4. Fallback journal
        if getattr(move, 'journal_id', False) and move.journal_id.type == 'cash':
            return 'Espèces'

        return 'Virement'

    def get_report_data(self):
        """
        Calcule toutes les données consolidées :
        - Ventes (Factures et Avoirs Clients)
        - Dépenses & Charges (Factures d'achat fournisseurs et Avoirs)
        - Notes de Frais & Dépenses RH (Salaires journaliers, avances, pourboires, maintenance)
        - Décaissements directs de caisse / menues dépenses
        - Ventilation Trésorerie par mode de règlement
        - Résultat Net Journalier
        """
        self.ensure_one()
        currency = self.company_id.currency_id

        # =========================================================================
        # 1. RÉCUPÉRATION DES VENTES (Factures et Avoirs Clients)
        # =========================================================================
        sale_domain = [
            ('company_id', '=', self.company_id.id),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
        ]
        if self.sale_journal_id:
            sale_domain.append(('journal_id', '=', self.sale_journal_id.id))
        if self.salesperson_id:
            sale_domain.append(('invoice_user_id', '=', self.salesperson_id.id))
        if self.invoice_state == 'posted':
            sale_domain.append(('state', '=', 'posted'))
        elif self.invoice_state == 'paid':
            sale_domain.append(('state', '=', 'posted'))
            sale_domain.append(('payment_state', 'in', ('paid', 'in_payment')))

        sale_moves = self.env['account.move'].search(sale_domain, order='date asc, name asc')

        # =========================================================================
        # 2. RÉCUPÉRATION DES CHARGES FOURNISSEURS (Factures d'Achat & Avoirs)
        # =========================================================================
        purchase_domain = [
            ('company_id', '=', self.company_id.id),
            ('move_type', 'in', ('in_invoice', 'in_refund')),
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
        ]
        if self.purchase_journal_id:
            purchase_domain.append(('journal_id', '=', self.purchase_journal_id.id))
        if self.invoice_state in ('posted', 'paid'):
            purchase_domain.append(('state', '=', 'posted'))
        if self.invoice_state == 'paid':
            purchase_domain.append(('payment_state', 'in', ('paid', 'in_payment')))

        purchase_moves = self.env['account.move'].search(purchase_domain, order='date asc, name asc')

        # =========================================================================
        # 3. RÉCUPÉRATION DES NOTES DE FRAIS & DÉPENSES RH (Salaires journaliers, etc.)
        # =========================================================================
        hr_domain = [
            ('company_id', '=', self.company_id.id),
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
            ('state', 'not in', ('refused',)),
        ]
        hr_expenses_records = self.env['hr.expense'].search(hr_domain, order='date asc, id asc')

        # =========================================================================
        # 4. RÉCUPÉRATION DES DÉCAISSEMENTS DIRECTS (Paiements Caisse sortants hors facture)
        # =========================================================================
        direct_payment_domain = [
            ('company_id', '=', self.company_id.id),
            ('payment_type', '=', 'outbound'),
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
            ('state', 'in', ('paid', 'in_process', 'posted')),
        ]
        all_out_payments = self.env['account.payment'].search(direct_payment_domain, order='date asc, name asc')
        # Filtrer pour exclure les transferts internes appariés éventuels
        all_out_payments = all_out_payments.filtered(lambda p: not getattr(p, 'paired_internal_transfer_payment_id', False))
        
        # Filtrer ceux qui ne sont pas rattachés aux factures d'achat déjà listées
        invoiced_payment_ids = set()
        for pmove in purchase_moves:
            wjson = pmove.invoice_payments_widget
            if wjson:
                try:
                    if isinstance(wjson, (bytes, bytearray)):
                        wjson = wjson.decode('utf-8')
                    wd = json.loads(wjson) if isinstance(wjson, str) else wjson
                    for item in wd.get('content', []):
                        pid = item.get('account_payment_id')
                        if pid:
                            invoiced_payment_ids.add(pid)
                except Exception:
                    pass

        direct_cash_payments = all_out_payments.filtered(lambda p: p.id not in invoiced_payment_ids)

        # =========================================================================
        # 5. STRUCTURES ET CUMULS
        # =========================================================================
        payment_states_map = {
            'not_paid': 'Non payé',
            'in_payment': 'En paiement',
            'paid': 'Payé',
            'partial': 'Partiel',
            'reversed': 'Annulé'
        }

        hr_states_map = {
            'draft': 'Brouillon',
            'reported': 'Soumis',
            'approved': 'Approuvé',
            'done': 'Payé',
            'refused': 'Refusé'
        }

        # Trésorerie par mode
        treasury_modes = ['Espèces', 'Virement', 'Chèque', 'Effet', 'Carte bancaire', 'Autre']
        treasury = {m: {'in': 0.0, 'out': 0.0, 'net': 0.0} for m in treasury_modes}

        # Listes détaillées
        invoices_list = []
        refunds_list = []
        vendor_bills_list = []
        vendor_refunds_list = []
        hr_expenses_list = []
        direct_expenses_list = []

        # Cumuls Ventes
        sales_untaxed = 0.0
        sales_tax = 0.0
        sales_gross = 0.0
        sales_refunds = 0.0
        sales_paid = 0.0
        sales_residual = 0.0

        # Cumuls Charges Fournisseurs
        exp_untaxed = 0.0
        exp_tax = 0.0
        exp_gross = 0.0
        exp_refunds = 0.0
        exp_paid = 0.0
        exp_residual = 0.0

        # ------------------- Traitement des Ventes -------------------
        for move in sale_moves:
            sign = 1 if move.move_type == 'out_invoice' else -1
            total_ttc = move.amount_total
            total_ht = move.amount_untaxed
            total_tva = total_ttc - total_ht
            paid_amount = max(0.0, total_ttc - move.amount_residual)
            residual = move.amount_residual

            # Recherche du paiement lié (account.payment) pour extraire mode réel et informations de chèque
            linked_pay = False
            for p in (getattr(move, 'matched_payment_ids', self.env['account.payment']) | getattr(move, 'reconciled_payment_ids', self.env['account.payment'])):
                if p.exists():
                    linked_pay = p
                    break
            if not linked_pay:
                wjson = move.invoice_payments_widget
                if wjson:
                    try:
                        if isinstance(wjson, (bytes, bytearray)):
                            wjson = wjson.decode('utf-8')
                        wd = json.loads(wjson) if isinstance(wjson, str) else wjson
                        for item in wd.get('content', []):
                            pid = item.get('account_payment_id')
                            if pid:
                                p = self.env['account.payment'].browse(pid)
                                if p.exists():
                                    linked_pay = p
                                    break
                    except Exception:
                        pass

            if linked_pay:
                mode = self._determine_move_payment_mode(move, payment=linked_pay)
                check_client = getattr(linked_pay, 'check_client_name', False) or getattr(move, 'check_client_name', False) or (move.partner_id.name if move.partner_id else '')
                check_num = getattr(linked_pay, 'check_number', False) or getattr(move, 'check_number', False) or ''
                check_due = getattr(linked_pay, 'check_date_due', False) or getattr(move, 'check_date_due', False) or False
            else:
                mode = self._determine_move_payment_mode(move)
                check_client = getattr(move, 'check_client_name', False) or (move.partner_id.name if move.partner_id else '')
                check_num = getattr(move, 'check_number', False) or ''
                check_due = getattr(move, 'check_date_due', False) or False

            due_str = check_due.strftime('%d/%m/%Y') if hasattr(check_due, 'strftime') else (str(check_due) if check_due else '')

            item_data = {
                'id': move.id,
                'name': move.name or '/',
                'date': move.date,
                'partner': move.partner_id.name or 'Client divers',
                'payment_mode': mode,
                'check_client_name': check_client,
                'check_number': check_num,
                'check_date_due': due_str,
                'total_ht': total_ht,
                'total_tva': total_tva,
                'total_ttc': total_ttc,
                'paid': paid_amount,
                'residual': residual,
                'payment_state': payment_states_map.get(move.payment_state, move.payment_state or 'Non payé')
            }

            if move.move_type == 'out_invoice':
                sales_untaxed += total_ht
                sales_tax += total_tva
                sales_gross += total_ttc
                sales_paid += paid_amount
                sales_residual += residual
                invoices_list.append(item_data)
            else:
                sales_refunds += total_ttc
                refunds_list.append(item_data)

            # Règlements rattachés aux ventes (Encaissements)
            if paid_amount > 0.005:
                wjson = move.invoice_payments_widget
                allocated = 0.0
                if wjson:
                    try:
                        if isinstance(wjson, (bytes, bytearray)):
                            wjson = wjson.decode('utf-8')
                        wd = json.loads(wjson) if isinstance(wjson, str) else wjson
                        for pinfo in wd.get('content', []):
                            amt = pinfo.get('amount', 0.0) * sign
                            pid = pinfo.get('account_payment_id')
                            pay = self.env['account.payment'].browse(pid) if pid else False
                            pmode = self._determine_move_payment_mode(move, pay_info=pinfo, payment=pay)
                            if pmode not in treasury:
                                pmode = 'Autre'
                            treasury[pmode]['in'] += amt
                            allocated += amt
                    except Exception:
                        pass
                unallocated = paid_amount - allocated
                if abs(unallocated) > 0.005:
                    inv_mode = mode if mode in treasury else 'Autre'
                    treasury[inv_mode]['in'] += unallocated * sign

        # ------------------- Traitement des Charges & Factures Fournisseurs -------------------
        for move in purchase_moves:
            sign = 1 if move.move_type == 'in_invoice' else -1
            total_ttc = move.amount_total
            total_ht = move.amount_untaxed
            total_tva = total_ttc - total_ht
            paid_amount = max(0.0, total_ttc - move.amount_residual)
            residual = move.amount_residual

            # Recherche du paiement lié pour les achats
            linked_pay = False
            for p in (getattr(move, 'matched_payment_ids', self.env['account.payment']) | getattr(move, 'reconciled_payment_ids', self.env['account.payment'])):
                if p.exists():
                    linked_pay = p
                    break
            if not linked_pay:
                wjson = move.invoice_payments_widget
                if wjson:
                    try:
                        if isinstance(wjson, (bytes, bytearray)):
                            wjson = wjson.decode('utf-8')
                        wd = json.loads(wjson) if isinstance(wjson, str) else wjson
                        for item in wd.get('content', []):
                            pid = item.get('account_payment_id')
                            if pid:
                                p = self.env['account.payment'].browse(pid)
                                if p.exists():
                                    linked_pay = p
                                    break
                    except Exception:
                        pass

            if linked_pay:
                mode = self._determine_move_payment_mode(move, payment=linked_pay)
                ref_str = move.ref or getattr(linked_pay, 'check_number', False) or getattr(move, 'check_number', False) or ''
            else:
                mode = self._determine_move_payment_mode(move)
                ref_str = move.ref or getattr(move, 'check_number', False) or ''

            supplier_name = move.partner_id.name or 'Fournisseur / Dépense'
            lines_desc = ", ".join([l.name for l in move.invoice_line_ids.filtered(lambda l: l.name)[:2]]) if move.invoice_line_ids else ''

            item_data = {
                'id': move.id,
                'name': move.name or '/',
                'ref': ref_str,
                'date': move.date,
                'partner': supplier_name,
                'description': lines_desc,
                'payment_mode': mode,
                'total_ht': total_ht,
                'total_tva': total_tva,
                'total_ttc': total_ttc,
                'paid': paid_amount,
                'residual': residual,
                'payment_state': payment_states_map.get(move.payment_state, move.payment_state or 'Non payé')
            }

            if move.move_type == 'in_invoice':
                exp_untaxed += total_ht
                exp_tax += total_tva
                exp_gross += total_ttc
                exp_paid += paid_amount
                exp_residual += residual
                vendor_bills_list.append(item_data)
            else:
                exp_refunds += total_ttc
                vendor_refunds_list.append(item_data)

            # Règlements rattachés aux achats (Décaissements)
            if paid_amount > 0.005:
                wjson = move.invoice_payments_widget
                allocated = 0.0
                if wjson:
                    try:
                        if isinstance(wjson, (bytes, bytearray)):
                            wjson = wjson.decode('utf-8')
                        wd = json.loads(wjson) if isinstance(wjson, str) else wjson
                        for pinfo in wd.get('content', []):
                            amt = pinfo.get('amount', 0.0) * sign
                            pid = pinfo.get('account_payment_id')
                            pay = self.env['account.payment'].browse(pid) if pid else False
                            pmode = self._determine_move_payment_mode(move, pay_info=pinfo, payment=pay)
                            if pmode not in treasury:
                                pmode = 'Autre'
                            treasury[pmode]['out'] += amt
                            allocated += amt
                    except Exception:
                        pass
                unallocated = paid_amount - allocated
                if abs(unallocated) > 0.005:
                    inv_mode = mode if mode in treasury else 'Autre'
                    treasury[inv_mode]['out'] += unallocated * sign

        # ------------------- Traitement des Notes de Frais & Dépenses RH -------------------
        hr_expenses_total = 0.0
        for exp in hr_expenses_records:
            amt = exp.total_amount
            hr_expenses_total += amt

            # Les salaires journaliers ouvriers / chauffeurs et menues dépenses RH sont décaissés en espèces depuis la caisse
            t_mode = 'Espèces'
            treasury[t_mode]['out'] += amt

            cat_name = exp.product_id.name if exp.product_id else 'Dépense / Salaire'
            emp_name = exp.employee_id.name if exp.employee_id else 'Employé'
            pmode_lbl = 'Espèces (Caisse)' if exp.payment_mode == 'own_account' else 'Société'
            state_lbl = hr_states_map.get(exp.state, exp.state or 'Approuvé')

            hr_expenses_list.append({
                'id': exp.id,
                'date': exp.date,
                'name': exp.name or '/',
                'employee': emp_name,
                'category': cat_name,
                'payment_mode': pmode_lbl,
                'amount': amt,
                'state': state_lbl,
            })

        # ------------------- Traitement des Dépenses Directes de Caisse -------------------
        direct_cash_total = 0.0
        for pay in direct_cash_payments:
            amt = pay.amount
            jtype = pay.journal_id.type
            pmode = 'Espèces' if jtype == 'cash' else 'Virement'
            if any(k in (pay.journal_id.name or '').lower() for k in ['cheque', 'chèque']):
                pmode = 'Chèque'

            if pmode not in treasury:
                pmode = 'Autre'
            treasury[pmode]['out'] += amt

            if jtype == 'cash':
                direct_cash_total += amt

            direct_expenses_list.append({
                'id': pay.id,
                'name': pay.name or '/',
                'date': pay.date,
                'partner': pay.partner_id.name if pay.partner_id else 'Dépense Diverse',
                'memo': pay.memo or getattr(pay, 'ref', '') or 'Dépense / Décaissement',
                'journal': pay.journal_id.name,
                'mode': pmode,
                'amount': amt,
            })

        # Calcul des soldes nets de trésorerie
        for m in treasury:
            treasury[m]['net'] = treasury[m]['in'] - treasury[m]['out']

        sales_net = sales_gross - sales_refunds
        exp_net = exp_gross - exp_refunds
        total_exp_global = exp_net + direct_cash_total + hr_expenses_total
        net_result = sales_net - total_exp_global
        net_cash_flow = sum(treasury[m]['in'] for m in treasury) - sum(treasury[m]['out'] for m in treasury)
        net_cashbox = treasury['Espèces']['net']

        summary = {
            # Ventes
            'sales_untaxed': sales_untaxed,
            'sales_tax': sales_tax,
            'sales_gross': sales_gross,
            'sales_refunds': sales_refunds,
            'sales_net': sales_net,
            'sales_paid': sales_paid,
            'sales_residual': sales_residual,
            'invoice_count': len(invoices_list),
            'refund_count': len(refunds_list),

            # Charges Fournisseurs
            'expenses_untaxed': exp_untaxed,
            'expenses_tax': exp_tax,
            'expenses_gross': exp_gross,
            'expenses_refunds': exp_refunds,
            'expenses_net': exp_net,
            'expenses_paid': exp_paid,
            'expenses_residual': exp_residual,
            'vendor_bill_count': len(vendor_bills_list),
            'vendor_refund_count': len(vendor_refunds_list),
            
            # Notes de Frais & Salaires Journaliers (HR Expenses)
            'hr_expenses_total': hr_expenses_total,
            'hr_expenses_count': len(hr_expenses_list),

            # Dépenses directes caisse
            'direct_cash_total': direct_cash_total,
            'direct_cash_count': len(direct_expenses_list),

            # Total Global Dépenses
            'total_expenses_global': total_exp_global,

            # Bilan & Solde Net
            'net_result': net_result,
            'net_cash_flow': net_cash_flow,
            'net_cashbox': net_cashbox,
        }

        # Treasury list for presentation
        treasury_list = []
        for m in ['Espèces', 'Virement', 'Chèque', 'Effet', 'Carte bancaire', 'Autre']:
            if treasury[m]['in'] > 0.001 or treasury[m]['out'] > 0.001:
                treasury_list.append({
                    'mode': m,
                    'in': treasury[m]['in'],
                    'out': treasury[m]['out'],
                    'net': treasury[m]['net'],
                })

        return {
            'summary': summary,
            'treasury': treasury_list,
            'treasury_totals': {
                'in': sum(t['in'] for t in treasury_list),
                'out': sum(t['out'] for t in treasury_list),
                'net': sum(t['net'] for t in treasury_list),
            },
            'invoices': invoices_list,
            'refunds': refunds_list,
            'vendor_bills': vendor_bills_list,
            'vendor_refunds': vendor_refunds_list,
            'hr_expenses': hr_expenses_list,
            'direct_expenses': direct_expenses_list,
            'currency': currency,
        }

    def _compute_and_store_report_data(self):
        """Met à jour les champs persistants du rapport et génère les fichiers joints"""
        for rec in self:
            data = rec.get_report_data()
            s = data['summary']
            
            rec.write({
                'sales_total_untaxed': s['sales_untaxed'],
                'sales_total_tax': s['sales_tax'],
                'sales_total_gross': s['sales_gross'],
                'sales_refunds_total': s['sales_refunds'],
                'sales_total_net': s['sales_net'],
                'sales_total_paid': s['sales_paid'],
                'sales_total_residual': s['sales_residual'],
                'invoice_count': s['invoice_count'],
                'refund_count': s['refund_count'],

                'expenses_total_untaxed': s['expenses_untaxed'],
                'expenses_total_tax': s['expenses_tax'],
                'expenses_total_gross': s['expenses_gross'],
                'expenses_refunds_total': s['expenses_refunds'],
                'expenses_total_net': s['expenses_net'],
                'expenses_total_paid': s['expenses_paid'],
                'expenses_total_residual': s['expenses_residual'],
                'vendor_bill_count': s['vendor_bill_count'],
                'vendor_refund_count': s['vendor_refund_count'],

                'hr_expenses_total': s['hr_expenses_total'],
                'hr_expenses_count': s['hr_expenses_count'],

                'direct_cash_expenses_total': s['direct_cash_total'],
                'direct_cash_expenses_count': s['direct_cash_count'],

                'total_expenses_all': s['total_expenses_global'],
                'net_result': s['net_result'],
                'net_cash_flow': s['net_cash_flow'],
                'net_cashbox': s['net_cashbox'],

                'invoice_ids': [(6, 0, [inv['id'] for inv in data['invoices']] + [ref['id'] for ref in data['refunds']])],
                'expense_ids': [(6, 0, [vb['id'] for vb in data['vendor_bills']] + [vr['id'] for vr in data['vendor_refunds']])],
                'hr_expense_ids': [(6, 0, [he['id'] for he in data['hr_expenses']])],
                'payment_ids': [(6, 0, [de['id'] for de in data['direct_expenses']])],
            })

            # Génération Excel et CSV
            excel_bytes = rec._generate_excel_data(data)
            csv_bytes = rec._generate_csv_data(data)
            slug_date = rec.date_start.strftime('%Y%m%d') if rec.date_start else fields.Date.today().strftime('%Y%m%d')
            
            rec.write({
                'excel_file': base64.b64encode(excel_bytes),
                'excel_filename': f"Rapport_Ventes_Depenses_{slug_date}.xlsx",
                'csv_file': base64.b64encode(csv_bytes),
                'csv_filename': f"Rapport_Ventes_Depenses_{slug_date}.csv",
            })

    def action_print_pdf(self):
        """Action d'impression du rapport PDF"""
        self.ensure_one()
        return self.env.ref('Report.action_report_sales_expense_pdf').report_action(self)

    def action_refresh(self):
        """Recalcule toutes les données du rapport en cas de modification des écritures"""
        self.ensure_one()
        self._compute_and_store_report_data()
        return True

    # =========================================================================
    # GÉNÉRATION EXCEL (.xlsx)
    # =========================================================================
    def _generate_excel_data(self, data):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Styles
        title_fmt = workbook.add_format({'bold': True, 'font_size': 16, 'font_color': '#1e3a8a', 'align': 'center'})
        subtitle_fmt = workbook.add_format({'italic': True, 'font_size': 10, 'font_color': '#475569', 'align': 'center'})
        section_fmt = workbook.add_format({'bold': True, 'font_size': 12, 'bg_color': '#1e3a8a', 'font_color': '#ffffff', 'align': 'left', 'indent': 1})
        sec_green_fmt = workbook.add_format({'bold': True, 'font_size': 12, 'bg_color': '#166534', 'font_color': '#ffffff', 'align': 'left', 'indent': 1})
        sec_red_fmt = workbook.add_format({'bold': True, 'font_size': 12, 'bg_color': '#991b1b', 'font_color': '#ffffff', 'align': 'left', 'indent': 1})
        sec_amber_fmt = workbook.add_format({'bold': True, 'font_size': 12, 'bg_color': '#b45309', 'font_color': '#ffffff', 'align': 'left', 'indent': 1})
        
        head_fmt = workbook.add_format({'bold': True, 'bg_color': '#f1f5f9', 'font_color': '#1e293b', 'border': 1, 'align': 'center'})
        border_fmt = workbook.add_format({'border': 1, 'font_size': 10})
        center_fmt = workbook.add_format({'border': 1, 'font_size': 10, 'align': 'center'})
        num_fmt = workbook.add_format({'border': 1, 'font_size': 10, 'align': 'right', 'num_format': '#,##0.00 "DH"'})
        bold_num_fmt = workbook.add_format({'bold': True, 'border': 1, 'font_size': 11, 'align': 'right', 'num_format': '#,##0.00 "DH"'})
        total_green_fmt = workbook.add_format({'bold': True, 'border': 2, 'bg_color': '#dcfce7', 'font_color': '#166534', 'font_size': 11, 'align': 'right', 'num_format': '#,##0.00 "DH"'})
        total_red_fmt = workbook.add_format({'bold': True, 'border': 2, 'bg_color': '#fee2e2', 'font_color': '#991b1b', 'font_size': 11, 'align': 'right', 'num_format': '#,##0.00 "DH"'})

        # Onglet 1 : Synthèse & Bilan
        ws_sum = workbook.add_worksheet('Bilan Synthétique')
        ws_sum.set_column('A:A', 38)
        ws_sum.set_column('B:D', 20)
        
        ws_sum.merge_range('A1:D1', f"RAPPORT JOURNALIER VENTES & DÉPENSES - {self.name}", title_fmt)
        ws_sum.merge_range('A2:D2', f"Période du {self.date_start} au {self.date_end} | Société : {self.company_id.name}", subtitle_fmt)

        row = 4
        # 1. Bilan Financier Global
        ws_sum.merge_range(row, 0, row, 3, "1. SYNTHÈSE FINANCIÈRE & RÉSULTAT NET", section_fmt)
        row += 1
        s = data['summary']
        ws_sum.write(row, 0, "Chiffre d'Affaires Brut TTC (Factures)", border_fmt)
        ws_sum.write(row, 1, s['sales_gross'], num_fmt)
        row += 1
        ws_sum.write(row, 0, "Avoirs Clients TTC", border_fmt)
        ws_sum.write(row, 1, s['sales_refunds'], num_fmt)
        row += 1
        ws_sum.write(row, 0, "TOTAL VENTES NETTES TTC", head_fmt)
        ws_sum.write(row, 1, s['sales_net'], total_green_fmt)
        row += 2

        ws_sum.write(row, 0, "Charges Fournisseurs TTC (Factures d'Achat)", border_fmt)
        ws_sum.write(row, 1, s['expenses_gross'], num_fmt)
        row += 1
        ws_sum.write(row, 0, "Avoirs Fournisseurs TTC", border_fmt)
        ws_sum.write(row, 1, s['expenses_refunds'], num_fmt)
        row += 1
        ws_sum.write(row, 0, "Notes de Frais & Salaires Journaliers (Dépenses RH)", border_fmt)
        ws_sum.write(row, 1, s['hr_expenses_total'], num_fmt)
        row += 1
        ws_sum.write(row, 0, "Dépenses Directes de Caisse (Menues Dépenses)", border_fmt)
        ws_sum.write(row, 1, s['direct_cash_total'], num_fmt)
        row += 1
        ws_sum.write(row, 0, "TOTAL CHARGES & DÉPENSES NETTES TTC", head_fmt)
        ws_sum.write(row, 1, s['total_expenses_global'], total_red_fmt)
        row += 2

        ws_sum.write(row, 0, "RÉSULTAT NET JOURNALIER (Ventes - Dépenses)", head_fmt)
        net_style = total_green_fmt if s['net_result'] >= 0 else total_red_fmt
        ws_sum.write(row, 1, s['net_result'], net_style)
        row += 1
        ws_sum.write(row, 0, "SOLDE NET DE CAISSE (Espèces encaissées - décaissées)", head_fmt)
        caisse_style = total_green_fmt if s['net_cashbox'] >= 0 else total_red_fmt
        ws_sum.write(row, 1, s['net_cashbox'], caisse_style)
        row += 3

        # 2. Ventilation de Trésorerie
        ws_sum.merge_range(row, 0, row, 3, "2. FLUX DE TRÉSORERIE PAR MODE DE RÈGLEMENT", section_fmt)
        row += 1
        headers_tres = ["Mode de Règlement", "Entrées (Encaissements)", "Sorties (Décaissements)", "Solde Net"]
        for c, h in enumerate(headers_tres):
            ws_sum.write(row, c, h, head_fmt)
        row += 1
        for tr in data['treasury']:
            ws_sum.write(row, 0, tr['mode'], border_fmt)
            ws_sum.write(row, 1, tr['in'], num_fmt)
            ws_sum.write(row, 2, tr['out'], num_fmt)
            ws_sum.write(row, 3, tr['net'], bold_num_fmt)
            row += 1
        ws_sum.write(row, 0, "TOTAL TRÉSORERIE", head_fmt)
        ws_sum.write(row, 1, data['treasury_totals']['in'], total_green_fmt)
        ws_sum.write(row, 2, data['treasury_totals']['out'], total_red_fmt)
        ws_sum.write(row, 3, data['treasury_totals']['net'], bold_num_fmt)

        # Onglet 2 : Ventes
        ws_v = workbook.add_worksheet('Détail Ventes')
        ws_v.set_column('A:A', 12)
        ws_v.set_column('B:B', 18)
        ws_v.set_column('C:C', 30)
        ws_v.set_column('D:D', 22)
        ws_v.set_column('E:G', 16)
        ws_v.set_column('H:H', 14)
        
        ws_v.merge_range('A1:H1', "DÉTAIL DES FACTURES DE VENTE & AVOIRS CLIENTS", sec_green_fmt)
        v_headers = ["Date", "Numéro", "Client", "Mode Règlement & Réf", "Total TTC", "Encaissé", "Reste Dû", "Statut"]
        for c, h in enumerate(v_headers):
            ws_v.write(2, c, h, head_fmt)
        
        v_row = 3
        for inv in data['invoices']:
            mode_lbl = inv['payment_mode']
            if inv.get('check_client_name') and inv['payment_mode'] in ('Chèque', 'Effet', 'Virement'):
                mode_lbl += f" - {inv['check_client_name']}"
            if inv.get('check_number'):
                mode_lbl += f" (N° {inv['check_number']})"
                
            ws_v.write(v_row, 0, str(inv['date']), center_fmt)
            ws_v.write(v_row, 1, inv['name'], border_fmt)
            ws_v.write(v_row, 2, inv['partner'], border_fmt)
            ws_v.write(v_row, 3, mode_lbl, border_fmt)
            ws_v.write(v_row, 4, inv['total_ttc'], num_fmt)
            ws_v.write(v_row, 5, inv['paid'], num_fmt)
            ws_v.write(v_row, 6, inv['residual'], num_fmt)
            ws_v.write(v_row, 7, inv['payment_state'], center_fmt)
            v_row += 1

        # Onglet 3 : Dépenses RH & Salaires
        ws_hr = workbook.add_worksheet('Salaires & Dépenses RH')
        ws_hr.set_column('A:A', 12)
        ws_hr.set_column('B:B', 32)
        ws_hr.set_column('C:C', 20)
        ws_hr.set_column('D:D', 24)
        ws_hr.set_column('E:E', 18)
        ws_hr.set_column('F:F', 18)
        ws_hr.set_column('G:G', 14)

        ws_hr.merge_range('A1:G1', "NOTES DE FRAIS & SALAIRES JOURNALIERS (HR EXPENSES)", sec_amber_fmt)
        hr_headers = ["Date", "Description / Motif", "Catégorie", "Employé", "Mode de Règlement", "Montant Total", "Statut"]
        for c, h in enumerate(hr_headers):
            ws_hr.write(2, c, h, head_fmt)

        hr_row = 3
        for he in data['hr_expenses']:
            ws_hr.write(hr_row, 0, str(he['date']), center_fmt)
            ws_hr.write(hr_row, 1, he['name'], border_fmt)
            ws_hr.write(hr_row, 2, he['category'], border_fmt)
            ws_hr.write(hr_row, 3, he['employee'], border_fmt)
            ws_hr.write(hr_row, 4, he['payment_mode'], center_fmt)
            ws_hr.write(hr_row, 5, he['amount'], num_fmt)
            ws_hr.write(hr_row, 6, he['state'], center_fmt)
            hr_row += 1
        
        ws_hr.write(hr_row, 0, "TOTAL DÉPENSES RH", head_fmt)
        ws_hr.merge_range(hr_row, 0, hr_row, 4, "TOTAL SALAIRES & DÉPENSES RH :", head_fmt)
        ws_hr.write(hr_row, 5, s['hr_expenses_total'], total_red_fmt)
        ws_hr.write(hr_row, 6, "", head_fmt)

        # Onglet 4 : Charges Fournisseurs & Décaissements
        ws_e = workbook.add_worksheet('Charges Fournisseurs')
        ws_e.set_column('A:A', 12)
        ws_e.set_column('B:B', 18)
        ws_e.set_column('C:C', 30)
        ws_e.set_column('D:D', 30)
        ws_e.set_column('E:E', 20)
        ws_e.set_column('F:H', 16)
        ws_e.set_column('I:I', 14)

        ws_e.merge_range('A1:I1', "FACTURES D'ACHAT, CHARGES FOURNISSEURS & DÉPENSES DIRECTES", sec_red_fmt)
        e_headers = ["Date", "Pièce", "Fournisseur / Bénéficiaire", "Description / Motif", "Mode Règlement", "Total TTC", "Payé", "Reste Dû", "Statut"]
        for c, h in enumerate(e_headers):
            ws_e.write(2, c, h, head_fmt)

        e_row = 3
        for vb in data['vendor_bills']:
            ws_e.write(e_row, 0, str(vb['date']), center_fmt)
            ws_e.write(e_row, 1, vb['name'], border_fmt)
            ws_e.write(e_row, 2, vb['partner'], border_fmt)
            ws_e.write(e_row, 3, vb.get('description', ''), border_fmt)
            ws_e.write(e_row, 4, vb['payment_mode'], border_fmt)
            ws_e.write(e_row, 5, vb['total_ttc'], num_fmt)
            ws_e.write(e_row, 6, vb['paid'], num_fmt)
            ws_e.write(e_row, 7, vb['residual'], num_fmt)
            ws_e.write(e_row, 8, vb['payment_state'], center_fmt)
            e_row += 1

        if data['direct_expenses']:
            e_row += 1
            ws_e.merge_range(e_row, 0, e_row, 8, "DÉPENSES DIRECTES DE CAISSE (SANS FACTURE FOURNISSEUR)", head_fmt)
            e_row += 1
            for de in data['direct_expenses']:
                ws_e.write(e_row, 0, str(de['date']), center_fmt)
                ws_e.write(e_row, 1, de['name'], border_fmt)
                ws_e.write(e_row, 2, de['partner'], border_fmt)
                ws_e.write(e_row, 3, f"{de['memo']} ({de['journal']})", border_fmt)
                ws_e.write(e_row, 4, de['mode'], border_fmt)
                ws_e.write(e_row, 5, de['amount'], num_fmt)
                ws_e.write(e_row, 6, de['amount'], num_fmt)
                ws_e.write(e_row, 7, 0.0, num_fmt)
                ws_e.write(e_row, 8, "Payé direct", center_fmt)
                e_row += 1

        workbook.close()
        return output.getvalue()

    # =========================================================================
    # GÉNÉRATION CSV
    # =========================================================================
    def _generate_csv_data(self, data):
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        
        # En-tête
        writer.writerow([f"RAPPORT VENTES & DÉPENSES - {self.name}"])
        writer.writerow(['Société', self.company_id.name])
        writer.writerow(['Période', f"Du {self.date_start} au {self.date_end}"])
        writer.writerow(['Date Génération', self.date_generation.strftime('%d/%m/%Y %H:%M:%S') if self.date_generation else ''])
        writer.writerow([])
        
        s = data['summary']
        writer.writerow(['=== 1. SYNTHÈSE FINANCIÈRE ==='])
        writer.writerow(['Indicateur', 'Montant TTC (DH)'])
        writer.writerow(['Total Ventes Nettes TTC', s['sales_net']])
        writer.writerow(['Total Charges & Achats Fournisseurs TTC', s['expenses_net']])
        writer.writerow(['Notes de Frais & Salaires Journaliers (RH)', s['hr_expenses_total']])
        writer.writerow(['Dépenses Directes de Caisse', s['direct_cash_total']])
        writer.writerow(['TOTAL DÉPENSES & CHARGES NETTES TTC', s['total_expenses_global']])
        writer.writerow(['RÉSULTAT NET JOURNALIER', s['net_result']])
        writer.writerow(['SOLDE NET CAISSE (ESPÈCES)', s['net_cashbox']])
        writer.writerow([])

        writer.writerow(['=== 2. FLUX DE TRÉSORERIE ==='])
        writer.writerow(['Mode de Règlement', 'Entrées', 'Sorties', 'Solde Net'])
        for tr in data['treasury']:
            writer.writerow([tr['mode'], tr['in'], tr['out'], tr['net']])
        writer.writerow(['TOTAL', data['treasury_totals']['in'], data['treasury_totals']['out'], data['treasury_totals']['net']])
        writer.writerow([])

        writer.writerow(['=== 3. DÉTAIL DES VENTES ==='])
        writer.writerow(['Date', 'Facture', 'Client', 'Mode Règlement', 'Total TTC', 'Encaissé', 'Reste', 'Statut'])
        for inv in data['invoices']:
            writer.writerow([inv['date'], inv['name'], inv['partner'], inv['payment_mode'], inv['total_ttc'], inv['paid'], inv['residual'], inv['payment_state']])
        writer.writerow([])

        writer.writerow(['=== 4. NOTES DE FRAIS & SALAIRES JOURNALIERS (HR EXPENSES) ==='])
        writer.writerow(['Date', 'Description / Motif', 'Catégorie', 'Employé', 'Payé par', 'Montant (DH)', 'Statut'])
        for he in data['hr_expenses']:
            writer.writerow([he['date'], he['name'], he['category'], he['employee'], he['payment_mode'], he['amount'], he['state']])
        writer.writerow([])

        writer.writerow(['=== 5. FACTURES D\'ACHAT & CHARGES FOURNISSEURS ==='])
        writer.writerow(['Date', 'Pièce', 'Fournisseur / Bénéficiaire', 'Description', 'Mode Règlement', 'Total TTC', 'Payé', 'Reste', 'Statut'])
        for vb in data['vendor_bills']:
            writer.writerow([vb['date'], vb['name'], vb['partner'], vb.get('description', ''), vb['payment_mode'], vb['total_ttc'], vb['paid'], vb['residual'], vb['payment_state']])
        for de in data['direct_expenses']:
            writer.writerow([de['date'], de['name'], de['partner'], de['memo'], de['mode'], de['amount'], de['amount'], 0.0, 'Payé direct'])

        return output.getvalue().encode('utf-8-sig')
