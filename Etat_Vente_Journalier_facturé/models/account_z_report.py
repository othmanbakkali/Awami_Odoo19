# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import base64
import io
import json
import csv
import xlsxwriter

class AccountZReport(models.Model):
    _name = 'account.z.report'
    _description = 'Rapport des Ventes Journalier'
    _order = 'date_generation desc, id desc'

    name = fields.Char(string='Numéro', required=True, copy=False, default='/')
    report_type = fields.Selection([
        ('x', 'Rapport des Ventes (Provisoire)'),
        ('z', 'Rapport des Ventes (Clôture)')
    ], string='Type de Rapport', required=True, default='z')
    date_start = fields.Date(string='Date Début', required=True)
    date_end = fields.Date(string='Date Fin', required=True)
    date_generation = fields.Datetime(string='Date de Génération', default=fields.Datetime.now, readonly=True)
    user_id = fields.Many2one('res.users', string='Utilisateur', default=lambda self: self.env.user, readonly=True)
    company_id = fields.Many2one('res.company', string='Société', required=True)
    journal_id = fields.Many2one('account.journal', string='Journal de Vente', domain="[('type', '=', 'sale')]")
    salesperson_id = fields.Many2one('res.users', string='Commercial')
    invoice_state = fields.Selection([
        ('posted', 'Factures comptabilisées'),
        ('paid', 'Factures payées uniquement')
    ], string='État des factures', required=True, default='posted')
    
    # Financial summaries (Stored Snapshots)
    total_untaxed = fields.Float(string='Total HT', readonly=True)
    total_tax = fields.Float(string='Total TVA', readonly=True)
    total_total = fields.Float(string='Total TTC', readonly=True)
    total_paid = fields.Float(string='Montant Payé', readonly=True)
    total_residual = fields.Float(string='Reste à Encasser', readonly=True)
    invoice_count = fields.Integer(string='Nombre de Factures', readonly=True)
    refund_count = fields.Integer(string='Nombre d\'Avoirs', readonly=True)
    
    invoice_ids = fields.Many2many('account.move', string='Factures Incluses')
    
    # Files
    pdf_attachment_id = fields.Many2one('ir.attachment', string='Rapport PDF Archivé', readonly=True)
    excel_file = fields.Binary(string='Fichier Excel', readonly=True)
    excel_filename = fields.Char(string='Nom de fichier Excel', readonly=True)
    csv_file = fields.Binary(string='Fichier CSV', readonly=True)
    csv_filename = fields.Char(string='Nom de fichier CSV', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('report_type', 'z') == 'z':
                vals['name'] = self.env['ir.sequence'].next_by_code('account.z.report') or '/'
            else:
                vals['name'] = "PROVISOIRE (Rapport X) - %s" % fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return super().create(vals_list)

    def _determine_move_payment_mode(self, move, pay_info=None, payment=None):
        """
        Détermine le mode de paiement avec priorité aux paiements réels (Chèque, Virement, Espèces, Effet).
        """
        # 1. Priorité absolue : l'enregistrement de paiement (account.payment)
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

        # 2. Vérification des données pay_info du widget
        if pay_info:
            journal_name = (pay_info.get('journal_name') or '').lower()
            if any(x in journal_name for x in ['cash', 'espèces', 'espece', 'caisse']):
                return 'Espèces'
            elif any(x in journal_name for x in ['carte', 'card', 'cb', 'visa', 'mastercard', 'cmi']):
                return 'Carte bancaire'
            elif any(x in journal_name for x in ['chèque', 'cheque', 'check']):
                return 'Chèque'
            elif any(x in journal_name for x in ['effet', 'traite', 'lcn']):
                return 'Effet'
            elif any(x in journal_name for x in ['virement', 'transfer', 'bank', 'banque']):
                return 'Virement'

        # 3. Vérification du mode sur la facture
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

        # 4. Fallback sur le type de journal de la facture
        if getattr(move, 'journal_id', False):
            if move.journal_id.type == 'cash':
                return 'Espèces'

        return 'Virement'

    def _get_reconciled_amount_between(self, pay, inv):
        """Calcule le montant exact lettré entre un paiement et une facture spécifique."""
        try:
            pay_lines = pay.move_id.line_ids.filtered(lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable'))
            inv_lines = inv.line_ids.filtered(lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable'))
            total_allocated = 0.0
            for pl in pay_lines:
                for pr in (pl.matched_debit_ids | pl.matched_credit_ids):
                    other_line = pr.debit_move_id if pr.credit_move_id.id == pl.id else pr.credit_move_id
                    if other_line in inv_lines:
                        total_allocated += pr.amount
            if total_allocated > 0.005:
                return total_allocated
        except Exception:
            pass

        try:
            wjson = inv.invoice_payments_widget
            if wjson:
                if isinstance(wjson, (bytes, bytearray)):
                    wjson = wjson.decode('utf-8')
                wd = json.loads(wjson) if isinstance(wjson, str) else wjson
                for item in wd.get('content', []):
                    if item.get('account_payment_id') == pay.id:
                        return item.get('amount', 0.0)
        except Exception:
            pass

        return min(pay.amount, inv.amount_total)

    def get_report_data(self):

        self.ensure_one()
        # 1. Fetch invoices
        domain = [
            ('company_id', '=', self.company_id.id),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
        ]
        if self.journal_id:
            domain.append(('journal_id', '=', self.journal_id.id))
        if self.salesperson_id:
            domain.append(('invoice_user_id', '=', self.salesperson_id.id))
            
        if self.invoice_state == 'posted':
            domain.append(('state', '=', 'posted'))
        elif self.invoice_state == 'paid':
            domain.append(('state', '=', 'posted'))
            domain.append(('payment_state', 'in', ('paid', 'in_payment')))
            
        moves = self.env['account.move'].search(domain, order='date asc, name asc')
        
        # Financial summaries
        total_untaxed = 0.0
        total_tax = 0.0
        total_total = 0.0
        total_residual = 0.0
        
        invoice_count = 0
        refund_count = 0
        
        invoices_list = []
        refunds_list = []
        
        # Taxes
        tax_details = {} # rate -> {'base': 0.0, 'tax': 0.0, 'name': ''}
        
        # Payments
        payments_by_mode = {
            'Espèces': 0.0,
            'Virement': 0.0,
            'Chèque': 0.0,
            'Effet': 0.0,
            'Carte bancaire': 0.0,
            'Autre': 0.0
        }
        
        # Products
        products_sold = {} # product_id -> {'name': '', 'qty': 0.0, 'ca': 0.0}
        
        payment_states_map = {
            'not_paid': 'Non payé',
            'in_payment': 'En cours',
            'paid': 'Payé',
            'partial': 'Partiel',
            'reversed': 'Extourné',
        }
        
        detailed_payments = []
        cheques_list = []
        cheques_seen = set()

        for move in moves:
            sign = -1 if move.move_type == 'out_refund' else 1
            inv_mode = 'Espèces'
            check_num = ''
            check_client = ''
            check_due = False
            
            # Totals
            total_untaxed += move.amount_untaxed_signed
            total_tax += move.amount_tax_signed
            total_total += move.amount_total_signed
            total_residual += move.amount_residual_signed
            
            paid_amount = move.amount_total_signed - move.amount_residual_signed
            
            # Recherche du paiement lié (account.payment) pour extraire mode réel et informations de chèque
            linked_pay = False
            for p in (getattr(move, 'matched_payment_ids', self.env['account.payment']) | getattr(move, 'reconciled_payment_ids', self.env['account.payment'])):
                if p.exists() and p.company_id == self.company_id:
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
                                if p.exists() and p.company_id == self.company_id:
                                    linked_pay = p
                                    break
                    except Exception:
                        pass


            if linked_pay:
                inv_mode = self._determine_move_payment_mode(move, payment=linked_pay)
                if inv_mode in ('Chèque', 'Effet'):
                    check_num = getattr(linked_pay, 'check_number', False) or getattr(move, 'check_number', False) or ''
                    check_client = getattr(linked_pay, 'check_client_name', False) or getattr(move, 'check_client_name', False) or (move.partner_id.name if move.partner_id else '')
                    check_due = getattr(linked_pay, 'check_date_due', False) or getattr(move, 'check_date_due', False) or False
                else:
                    check_num = ''
                    check_client = ''
                    check_due = False
            else:
                inv_mode = self._determine_move_payment_mode(move)
                if inv_mode in ('Chèque', 'Effet'):
                    check_num = getattr(move, 'check_number', False) or ''
                    check_client = getattr(move, 'check_client_name', False) or (move.partner_id.name if move.partner_id else '')
                    check_due = getattr(move, 'check_date_due', False) or False
                else:
                    check_num = ''
                    check_client = ''
                    check_due = False

            due_str = check_due.strftime('%d/%m/%Y') if hasattr(check_due, 'strftime') else (str(check_due) if check_due else '')

            # Extraction des dates de règlement pour traçabilité
            pay_dates_set = []
            for p in (getattr(move, 'matched_payment_ids', self.env['account.payment']) | getattr(move, 'reconciled_payment_ids', self.env['account.payment'])):
                if p.exists() and p.date:
                    d_str = p.date.strftime('%d/%m/%Y')
                    if d_str not in pay_dates_set:
                        pay_dates_set.append(d_str)

            if not pay_dates_set and move.invoice_payments_widget:
                try:
                    wjson = move.invoice_payments_widget
                    if isinstance(wjson, (bytes, bytearray)):
                        wjson = wjson.decode('utf-8')
                    wd = json.loads(wjson) if isinstance(wjson, str) else wjson
                    for item in wd.get('content', []):
                        d = item.get('date')
                        if d:
                            d_str = d.strftime('%d/%m/%Y') if hasattr(d, 'strftime') else str(d)
                            if d_str not in pay_dates_set:
                                pay_dates_set.append(d_str)
                except Exception:
                    pass

            payment_date_str = ', '.join(pay_dates_set) if pay_dates_set else False

            item_data = {
                'date': move.date,
                'name': move.name,
                'partner': move.partner_id.name or 'Client comptoir',
                'payment_mode': inv_mode,
                'check_number': check_num,
                'check_client_name': check_client,
                'check_date_due': due_str,
                'payment_date': payment_date_str,
                'untaxed': move.amount_untaxed_signed,
                'tax': move.amount_tax_signed,
                'total': move.amount_total_signed,
                'paid': paid_amount,
                'residual': move.amount_residual_signed,
                'payment_state': payment_states_map.get(move.payment_state, move.payment_state or 'Non payé')
            }
            
            if move.move_type == 'out_invoice':
                invoice_count += 1
                invoices_list.append(item_data)
            else:
                refund_count += 1
                refunds_list.append(item_data)
                
            # Taxes Breakdown
            # 1. Base from product lines
            for line in move.invoice_line_ids:
                if not line.display_type or line.display_type == 'product':
                    # Product stats
                    prod = line.product_id
                    if prod:
                        if prod.id not in products_sold:
                            products_sold[prod.id] = {
                                'name': prod.display_name or prod.name,
                                'qty': 0.0,
                                'ca': 0.0
                            }
                        products_sold[prod.id]['qty'] += line.quantity * sign
                        products_sold[prod.id]['ca'] += line.price_subtotal * sign
                        
                    for tax in line.tax_ids:
                        rate = tax.amount
                        if rate not in tax_details:
                            tax_details[rate] = {'base': 0.0, 'tax': 0.0, 'name': tax.name}
                        tax_details[rate]['base'] += line.price_subtotal * sign
                        
            # 2. Tax from tax lines
            for line in move.line_ids.filtered(lambda l: l.tax_line_id):
                tax = line.tax_line_id
                rate = tax.amount
                if rate not in tax_details:
                    tax_details[rate] = {'base': 0.0, 'tax': 0.0, 'name': tax.name}
                # credit - debit is positive for customer invoice, negative for credit note
                tax_details[rate]['tax'] += (line.credit - line.debit)
                
            # Reconciled payments breakdown
            paid_portion = (move.amount_total_signed - move.amount_residual_signed)
            if abs(paid_portion) > 0.005:
                widget_json = move.invoice_payments_widget
                widget_allocated = 0.0
                
                if widget_json:
                    try:
                        if isinstance(widget_json, (bytes, bytearray)):
                            widget_json = widget_json.decode('utf-8')
                        wdata = json.loads(widget_json) if isinstance(widget_json, str) else widget_json
                        content = wdata.get('content', []) if wdata else []
                        for pay_info in content:
                            amt = pay_info.get('amount', 0.0) * sign
                            payment_id = pay_info.get('account_payment_id')
                            payment = self.env['account.payment'].browse(payment_id) if payment_id else False
                            mode = self._determine_move_payment_mode(move, pay_info=pay_info, payment=payment)
                            
                            p_num = ''
                            p_client = ''
                            if mode in ('Chèque', 'Effet'):
                                if payment and payment.exists():
                                    p_num = getattr(payment, 'check_number', False) or getattr(payment, 'memo', False) or check_num
                                    p_client = getattr(payment, 'check_client_name', False) or (payment.partner_id.name if payment.partner_id else check_client)
                                else:
                                    p_num = check_num
                                    p_client = check_client

                            client_disp = p_client if mode in ('Chèque', 'Effet') else (payment.partner_id.name if payment and payment.partner_id else (move.partner_id.name or 'Client comptoir'))
                            check_disp = p_num if mode in ('Chèque', 'Effet') else ''

                            payments_by_mode[mode] = payments_by_mode.get(mode, 0.0) + amt
                            widget_allocated += amt
                            
                            detailed_payments.append({
                                'mode': mode,
                                'client': client_disp,
                                'check_number': check_disp,
                                'amount': amt,
                                'invoice_name': move.name,
                            })
                    except Exception:
                        pass
                        
                remaining_unallocated = paid_portion - widget_allocated
                if abs(remaining_unallocated) > 0.005:
                    inv_mode = self._determine_move_payment_mode(move)
                    payments_by_mode[inv_mode] = payments_by_mode.get(inv_mode, 0.0) + remaining_unallocated
                    detailed_payments.append({
                        'mode': inv_mode,
                        'client': check_client if inv_mode in ('Chèque', 'Effet') else '',
                        'check_number': check_num if inv_mode in ('Chèque', 'Effet') else '',
                        'amount': remaining_unallocated,
                        'invoice_name': move.name,
                    })

        # Traçabilité des règlements de factures antérieures (Créances recouvrées durant la période)
        period_payments = self.env['account.payment'].search([
            ('company_id', '=', self.company_id.id),
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
            ('payment_type', '=', 'inbound'),
            ('state', 'in', ('posted', 'paid'))
        ], order='date asc, id asc')

        prior_payments_list = []
        prior_payments_total = 0.0

        for pay in period_payments:
            # RÈGLE FONDAMENTALE : Ne retenir que les factures dont la date est <= date de fin du rapport!
            # Les mouvements postérieurs (inv.date > self.date_end) n'existaient pas encore à cette date.
            valid_reconciled_invs = pay.reconciled_invoice_ids.filtered(
                lambda m: m.move_type in ('out_invoice', 'out_refund') 
                and m.company_id == self.company_id 
                and m.date <= self.date_end
            )
            prior_invs = valid_reconciled_invs.filtered(lambda m: m.id not in moves.ids and m.date < self.date_start)
            current_invs = valid_reconciled_invs.filtered(lambda m: m.id in moves.ids)

            p_mode_raw = getattr(pay, 'payment_mode', False)
            if not p_mode_raw:
                j_name = (pay.journal_id.name or '').lower()
                j_type = pay.journal_id.type or ''
                if 'chèque' in j_name or 'cheque' in j_name:
                    p_mode_raw = 'cheque'
                elif 'effet' in j_name or 'traite' in j_name:
                    p_mode_raw = 'effet'
                elif 'virement' in j_name or j_type == 'bank':
                    p_mode_raw = 'virement'
                elif j_type == 'cash' or 'espece' in j_name or 'caisse' in j_name:
                    p_mode_raw = 'especes'

            mode_map = {
                'especes': 'Espèces',
                'cheque': 'Chèque',
                'effet': 'Effet',
                'traite': 'Effet',
                'effet_cheque': 'Effet',
                'virement': 'Virement'
            }
            pay_mode_label = mode_map.get(p_mode_raw, pay.journal_id.name or 'Autre')

            chk_num = (getattr(pay, 'check_number', False) or getattr(pay, 'memo', False) or '') if pay_mode_label in ('Chèque', 'Effet') else ''
            chk_client = (getattr(pay, 'check_client_name', False) or (pay.partner_id.name if pay.partner_id else '')) if pay_mode_label in ('Chèque', 'Effet') else ''
            chk_due = getattr(pay, 'check_date_due', False) if pay_mode_label in ('Chèque', 'Effet') else False
            chk_due_str = chk_due.strftime('%d/%m/%Y') if hasattr(chk_due, 'strftime') else (str(chk_due) if chk_due else '')

            total_allocated_to_prior = 0.0
            for inv in prior_invs:
                inv_alloc = self._get_reconciled_amount_between(pay, inv)
                inv_alloc = min(inv_alloc, pay.amount)
                total_allocated_to_prior += inv_alloc
                prior_payments_total += inv_alloc

                prior_payments_list.append({
                    'payment_id': pay.id,
                    'payment_name': pay.name,
                    'payment_date': pay.date,
                    'invoice_id': inv.id,
                    'invoice_name': inv.name or '/',
                    'invoice_date': inv.date,
                    'partner': inv.partner_id.name or pay.partner_id.name or 'Client comptoir',
                    'mode': pay_mode_label,
                    'check_number': chk_num,
                    'check_client_name': chk_client,
                    'check_date_due': chk_due_str,
                    'amount': inv_alloc,
                    'type': 'Facture Antérieure'
                })
                payments_by_mode[pay_mode_label] = payments_by_mode.get(pay_mode_label, 0.0) + inv_alloc
                detailed_payments.append({
                    'mode': pay_mode_label,
                    'client': chk_client,
                    'check_number': chk_num,
                    'amount': inv_alloc,
                    'invoice_name': f"{inv.name} (Antérieure)",
                })

            # Reliquat Acompte / Avance non encore alloué aux factures antérieures ou du jour
            allocated_to_current = sum(
                (inv.amount_total - inv.amount_residual) for inv in current_invs
            ) if current_invs else 0.0
            unallocated_advance = max(0.0, pay.amount - total_allocated_to_prior - allocated_to_current)

            if unallocated_advance > 0.005 and not current_invs:
                prior_payments_total += unallocated_advance
                prior_payments_list.append({
                    'payment_id': pay.id,
                    'payment_name': pay.name,
                    'payment_date': pay.date,
                    'invoice_id': False,
                    'invoice_name': 'Acompte / Avance',
                    'invoice_date': pay.date,
                    'partner': pay.partner_id.name or 'Client comptoir',
                    'mode': pay_mode_label,
                    'check_number': chk_num,
                    'check_client_name': chk_client,
                    'check_date_due': chk_due_str,
                    'amount': unallocated_advance,
                    'type': 'Acompte libre'
                })
                payments_by_mode[pay_mode_label] = payments_by_mode.get(pay_mode_label, 0.0) + unallocated_advance
                detailed_payments.append({
                    'mode': pay_mode_label,
                    'client': chk_client,
                    'check_number': chk_num,
                    'amount': unallocated_advance,
                    'invoice_name': 'Acompte / Avance',
                })

            # TABLE DES CHÈQUES & EFFETS : UNE SEULE LIGNE PAR CHÈQUE PHYSIQUE (MONTANT DU CHÈQUE)
            if pay_mode_label in ('Chèque', 'Effet'):
                pay_key = pay.id
                if pay_key not in cheques_seen:
                    cheques_seen.add(pay_key)
                    if valid_reconciled_invs:
                        inv_names = ', '.join([m.name for m in valid_reconciled_invs if m.name])
                        total_inv_alloc = sum(self._get_reconciled_amount_between(pay, inv) for inv in valid_reconciled_invs)
                        if total_inv_alloc < pay.amount - 0.005:
                            state_str = f"Encaissé ({inv_names} + Acompte)"
                            inv_display = f"{inv_names} (+ Acompte)"
                        else:
                            state_str = f"Encaissé ({inv_names})"
                            inv_display = inv_names
                    else:
                        inv_display = 'Acompte / Avance'
                        state_str = 'Encaissé (Acompte)'

                    cheques_list.append({
                        'date': pay.date,
                        'invoice_name': inv_display,
                        'partner': pay.partner_id.name or 'Client comptoir',
                        'check_client_name': chk_client or pay.partner_id.name or '-',
                        'check_number': chk_num or '-',
                        'check_date_due': chk_due_str or '-',
                        'amount': pay.amount,
                        'mode': pay_mode_label,
                        'state': state_str
                    })

        # Ajouter les factures du jour en chèque/effet non encore lettrées à un paiement
        for move in moves:
            inv_mode = self._determine_move_payment_mode(move)
            if inv_mode in ('Chèque', 'Effet'):
                linked_p = (getattr(move, 'matched_payment_ids', self.env['account.payment']) | getattr(move, 'reconciled_payment_ids', self.env['account.payment'])).filtered(lambda p: p.id in cheques_seen)
                if not linked_p and move.id not in cheques_seen:
                    has_prior_check = False
                    if move.invoice_payments_widget:
                        try:
                            wj = move.invoice_payments_widget
                            if isinstance(wj, (bytes, bytearray)):
                                wj = wj.decode('utf-8')
                            wjd = json.loads(wj) if isinstance(wj, str) else wj
                            for item in wjd.get('content', []):
                                p_id = item.get('account_payment_id')
                                if p_id:
                                    p_obj = self.env['account.payment'].browse(p_id)
                                    if p_obj.exists() and p_obj.date < self.date_start:
                                        has_prior_check = True
                                        break
                        except Exception:
                            pass
                    if not has_prior_check:
                        cheques_seen.add(move.id)
                        check_n = getattr(move, 'check_number', False) or '-'
                        check_c = getattr(move, 'check_client_name', False) or move.partner_id.name or '-'
                        check_d = getattr(move, 'check_date_due', False)
                        d_str = check_d.strftime('%d/%m/%Y') if hasattr(check_d, 'strftime') else (str(check_d) if check_d else '-')
                        cheques_list.append({
                            'date': move.date,
                            'invoice_name': move.name or '/',
                            'partner': move.partner_id.name or 'Client comptoir',
                            'check_client_name': check_c,
                            'check_number': check_n,
                            'check_date_due': d_str,
                            'amount': move.amount_total_signed,
                            'mode': inv_mode,
                            'state': payment_states_map.get(move.payment_state, move.payment_state or 'Non payé')
                        })

                    
        # Format Taxes and Products list
        taxes_list = []
        for rate in sorted(tax_details.keys()):
            taxes_list.append({
                'rate': f"{rate} %" if rate != 0.0 else "0 %",
                'base': tax_details[rate]['base'],
                'tax': tax_details[rate]['tax']
            })
            
        # Ventilation des Règlements : Total par type de règlement
        order_priority = ['Espèces', 'Virement', 'Chèque', 'Effet', 'Carte bancaire', 'Autre']
        all_present_modes = []
        for m in order_priority:
            if abs(payments_by_mode.get(m, 0.0)) > 0.005:
                all_present_modes.append(m)
        for m in sorted(payments_by_mode.keys()):
            if m not in all_present_modes and abs(payments_by_mode.get(m, 0.0)) > 0.005:
                all_present_modes.append(m)

        payments_list = []
        for mode in all_present_modes:
            mode_amount = payments_by_mode.get(mode, 0.0)
            mode_payments = [p for p in detailed_payments if p['mode'] == mode]
            mode_count = len(mode_payments)
            
            checks_details = []
            if mode in ('Chèque', 'Effet', 'cheque', 'effet'):
                for p in mode_payments:
                    checks_details.append({
                        'client': p.get('client') or 'Client comptoir',
                        'number': p.get('check_number') or '',
                        'amount': p['amount'],
                        'invoice': p.get('invoice_name', '')
                    })
                    
            payments_list.append({
                'mode': mode,
                'count': mode_count,
                'amount': mode_amount,
                'details': checks_details,
            })
            
        top_products_list = []
        # Sort products by CA descending
        sorted_products = sorted(products_sold.items(), key=lambda x: x[1]['ca'], reverse=True)
        for prod_id, info in sorted_products:
            top_products_list.append({
                'name': info['name'],
                'qty': info['qty'],
                'ca': info['ca']
            })
            
        payments_total = sum(p['amount'] for p in payments_list)
        total_paid = payments_total

        invoices_untaxed = sum(inv['untaxed'] for inv in invoices_list)
        invoices_tax = sum(inv['tax'] for inv in invoices_list)
        invoices_total = sum(inv['total'] for inv in invoices_list)
        invoices_paid = sum(inv['paid'] for inv in invoices_list)
        invoices_residual = sum(inv['residual'] for inv in invoices_list)

        refunds_untaxed = sum(ref['untaxed'] for ref in refunds_list)
        refunds_tax = sum(ref['tax'] for ref in refunds_list)
        refunds_total = sum(ref['total'] for ref in refunds_list)
        refunds_paid = sum(ref['paid'] for ref in refunds_list)
        refunds_residual = sum(ref['residual'] for ref in refunds_list)

        # Encaissements sur Factures Antérieures (Créances Recouvrées) par mode
        prior_payments_by_mode = {}
        for pp in prior_payments_list:
            m = pp.get('mode') or 'Autre'
            prior_payments_by_mode[m] = prior_payments_by_mode.get(m, 0.0) + pp.get('amount', 0.0)

        prior_payments_summary = [
            {'mode': m, 'amount': amt}
            for m, amt in sorted(prior_payments_by_mode.items(), key=lambda x: (
                0 if x[0] == 'Espèces' else (1 if x[0] == 'Virement' else (2 if x[0] == 'Chèque' else (3 if x[0] == 'Effet' else 4)))
            ))
            if amt > 0.005
        ]
        
        return {
            'moves': moves,
            'summary': {
                'invoice_count': invoice_count,
                'refund_count': refund_count,
                'total_untaxed': total_untaxed,
                'total_tax': total_tax,
                'total_total': total_total,
                'total_paid': total_paid,
                'total_residual': total_residual,
                'invoices_untaxed': invoices_untaxed,
                'invoices_tax': invoices_tax,
                'invoices_total': invoices_total,
                'invoices_paid': invoices_paid,
                'invoices_residual': invoices_residual,
                'refunds_untaxed': refunds_untaxed,
                'refunds_tax': refunds_tax,
                'refunds_total': refunds_total,
                'refunds_paid': refunds_paid,
                'refunds_residual': refunds_residual,
                'payments_total': payments_total,
                'prior_payments_total': prior_payments_total,
                'prior_payments_by_mode': prior_payments_by_mode,
                'prior_payments_summary': prior_payments_summary,
                'total_collected': payments_total,
            },
            'taxes': taxes_list,
            'payments': payments_list,
            'cheques': cheques_list,
            'cheques_count': len(cheques_list),
            'cheques_total_amount': sum(c['amount'] for c in cheques_list if c['mode'] == 'Chèque'),
            'effets_total_amount': sum(c['amount'] for c in cheques_list if c['mode'] == 'Effet'),
            'cheques_global_amount': sum(c['amount'] for c in cheques_list),
            'prior_payments': prior_payments_list,
            'prior_payments_count': len(prior_payments_list),
            'prior_payments_total': prior_payments_total,
            'prior_payments_by_mode': prior_payments_by_mode,
            'prior_payments_summary': prior_payments_summary,
            'invoices': invoices_list,
            'refunds': refunds_list,
            'products': top_products_list,
        }

    def generate_snapshot_data(self):
        self.ensure_one()
        report_data = self.get_report_data()
        
        # 1. Update Database fields
        self.write({
            'total_untaxed': report_data['summary']['total_untaxed'],
            'total_tax': report_data['summary']['total_tax'],
            'total_total': report_data['summary']['total_total'],
            'total_paid': report_data['summary']['total_paid'],
            'total_residual': report_data['summary']['total_residual'],
            'invoice_count': report_data['summary']['invoice_count'],
            'refund_count': report_data['summary']['refund_count'],
            'invoice_ids': [(6, 0, report_data['moves'].ids)],
        })
        
        # 2. Excel & CSV Generation
        excel_filename = "Rapport_%s_%s.xlsx" % (self.name.replace('/', '_'), self.date_generation.strftime('%Y%m%d_%H%M%S'))
        csv_filename = "Rapport_%s_%s.csv" % (self.name.replace('/', '_'), self.date_generation.strftime('%Y%m%d_%H%M%S'))
        
        excel_content = self._generate_excel_data(report_data)
        csv_content = self._generate_csv_data(report_data)
        
        self.write({
            'excel_file': base64.b64encode(excel_content),
            'excel_filename': excel_filename,
            'csv_file': base64.b64encode(csv_content),
            'csv_filename': csv_filename,
        })
        
        # 3. PDF Generation & Archive (only if PDF report action is registered)
        try:
            report_action = self.env.ref('etat_vente_journalier_facture.action_report_z', False) or self.env.ref('Etat_Vente_Journalier_facturé.action_report_z', False)
            if report_action:
                if not self.env.ref(report_action.report_name, False):
                    alt_name = 'Etat_Vente_Journalier_facturé.report_z_document_template' if 'etat_vente_journalier_facture' in (report_action.report_name or '') else 'etat_vente_journalier_facture.report_z_document_template'
                    if self.env.ref(alt_name, False):
                        report_action.sudo().write({'report_name': alt_name, 'report_file': alt_name})
                pdf_content, _ = report_action._render_qweb_pdf(self.ids)
                if self.pdf_attachment_id:
                    try:
                        self.pdf_attachment_id.unlink()
                    except Exception:
                        pass
                attachment = self.env['ir.attachment'].create({
                    'name': "%s.pdf" % self.name.replace('/', '_'),
                    'type': 'binary',
                    'datas': base64.b64encode(pdf_content),
                    'res_model': 'account.z.report',
                    'res_id': self.id,
                    'mimetype': 'application/pdf',
                })
                self.write({'pdf_attachment_id': attachment.id})
        except Exception:
            pass

    def action_print_pdf(self):
        self.ensure_one()
        report_action = self.env.ref('etat_vente_journalier_facture.action_report_z', False) or self.env.ref('Etat_Vente_Journalier_facturé.action_report_z', False)
        if report_action:
            if not self.env.ref(report_action.report_name, False):
                alt_name = 'Etat_Vente_Journalier_facturé.report_z_document_template' if 'etat_vente_journalier_facture' in (report_action.report_name or '') else 'etat_vente_journalier_facture.report_z_document_template'
                if self.env.ref(alt_name, False):
                    report_action.sudo().write({'report_name': alt_name, 'report_file': alt_name})
            return report_action.report_action(self)
        if self.pdf_attachment_id:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true' % self.pdf_attachment_id.id,
                'target': 'self',
            }
        return False

    def action_export_excel(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model=account.z.report&id=%s&field=excel_file&filename_field=excel_filename&download=true' % self.id,
            'target': 'self',
        }

    def action_export_csv(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model=account.z.report&id=%s&field=csv_file&filename_field=csv_filename&download=true' % self.id,
            'target': 'self',
        }

    def _generate_excel_data(self, data):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Rapport Z')
        
        # Set column widths
        sheet.set_column('A:A', 14)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 32)
        sheet.set_column('D:D', 26)
        sheet.set_column('E:E', 16)
        sheet.set_column('F:F', 16)
        sheet.set_column('G:G', 16)
        sheet.set_column('H:H', 14)
        
        # Formatting
        title_format = workbook.add_format({
            'bold': True, 'size': 14, 'align': 'center', 'valign': 'vcenter', 'fg_color': '#1f4e78', 'font_color': 'white'
        })
        section_format = workbook.add_format({
            'bold': True, 'size': 11, 'fg_color': '#d9e1f2', 'bottom': 2, 'top': 2
        })
        header_format = workbook.add_format({
            'bold': True, 'fg_color': '#2f5597', 'font_color': 'white', 'border': 1, 'align': 'center'
        })
        bold_format = workbook.add_format({'bold': True})
        num_format = workbook.add_format({'num_format': '#,##0.00" DH"', 'align': 'right', 'border': 1})
        center_format = workbook.add_format({'align': 'center', 'border': 1})
        border_format = workbook.add_format({'border': 1})
        
        # Header Info
        sheet.merge_range('A1:H1', f"{self.report_type == 'z' and 'RAPPORT Z' or 'RAPPORT X'} - CLÔTURE DES VENTES", title_format)
        
        # Metadata
        sheet.write('A3', 'Société:', bold_format)
        sheet.write('B3', self.company_id.name)
        sheet.write('A4', 'ICE:', bold_format)
        sheet.write('B4', self.company_id.ice or '')
        sheet.write('A5', 'Période:', bold_format)
        sheet.write('B5', f"Du {self.date_start} au {self.date_end}")
        
        sheet.write('E3', 'Date Génération:', bold_format)
        sheet.write('F3', self.date_generation.strftime('%d/%m/%Y %H:%M:%S') if self.date_generation else '')
        sheet.write('E4', 'Utilisateur:', bold_format)
        sheet.write('F4', self.user_id.name)
        sheet.write('E5', 'Numéro Rapport:', bold_format)
        sheet.write('F5', self.name)
        
        # 1. Summary Section
        row_idx = 7
        sheet.merge_range(f'A{row_idx+1}:H{row_idx+1}', 'RÉSUMÉ DES VENTES', section_format)
        row_idx += 1
        sheet.write(row_idx, 0, 'Indicateur', header_format)
        sheet.write(row_idx, 1, 'Valeur', header_format)
        row_idx += 1
        
        sum_data = [
            ('Nombre de factures', data['summary']['invoice_count']),
            ('Nombre d\'avoirs', data['summary']['refund_count']),
            ('Total Ventes TTC', data['summary']['total_total']),
            ('Factures réglées', data['summary']['invoices_paid']),
            ('Reste à encaisser factures', data['summary']['total_residual']),
            ('Encaissements créances antérieures', data['summary']['prior_payments_total']),
            ('Total général encaissé', data['summary']['payments_total']),
        ]
        
        for label, val in sum_data:
            sheet.write(row_idx, 0, label, border_format)
            if isinstance(val, float):
                sheet.write(row_idx, 1, val, num_format)
            else:
                sheet.write(row_idx, 1, val, border_format)
            row_idx += 1
            
        # 2. Payments Section
        row_idx += 1
        sheet.merge_range(f'A{row_idx+1}:H{row_idx+1}', 'VENTILATION DES RÈGLEMENTS', section_format)
        row_idx += 1
        pay_headers = ['Type de règlement', 'Nombre de règlements', 'Montant Total']
        for col_idx, h in enumerate(pay_headers):
            sheet.write(row_idx, col_idx, h, header_format)
        row_idx += 1
        for p in data['payments']:
            sheet.write(row_idx, 0, p['mode'], border_format)
            sheet.write(row_idx, 1, p['count'], center_format)
            sheet.write(row_idx, 2, p['amount'], num_format)
            row_idx += 1
        sheet.write(row_idx, 0, 'TOTAL ENCAISSÉ', bold_format)
        sheet.write(row_idx, 1, sum(p['count'] for p in data['payments']), bold_format)
        sheet.write(row_idx, 2, sum(p['amount'] for p in data['payments']), num_format)
        row_idx += 1
            
        # 3. Details Table
        row_idx += 1
        sheet.merge_range(f'A{row_idx+1}:H{row_idx+1}', 'DÉTAIL DES FACTURES', section_format)
        row_idx += 1
        detail_headers = ['Date', 'Facture', 'Client', 'Mode Règlement', 'Total TTC', 'Payé', 'Reste', 'Statut']
        for col_idx, h in enumerate(detail_headers):
            sheet.write(row_idx, col_idx, h, header_format)
        row_idx += 1
        for inv in data['invoices']:
            mode_str = inv.get('payment_mode', '')
            if inv.get('payment_mode') in ('Chèque', 'Effet', 'Virement', 'cheque', 'effet', 'virement'):
                client_disp = inv.get('check_client_name') or inv.get('partner') or ''
                if client_disp:
                    mode_str += f" - {client_disp}"
            if inv.get('check_number'):
                mode_str += f" (N° {inv['check_number']})"
            sheet.write(row_idx, 0, str(inv['date']), center_format)
            sheet.write(row_idx, 1, inv['name'], border_format)
            sheet.write(row_idx, 2, inv['partner'], border_format)
            sheet.write(row_idx, 3, mode_str, center_format)
            sheet.write(row_idx, 4, inv['total'], num_format)
            sheet.write(row_idx, 5, inv.get('paid', 0.0), num_format)
            sheet.write(row_idx, 6, inv.get('residual', 0.0), num_format)
            sheet.write(row_idx, 7, inv['payment_state'], center_format)
            row_idx += 1
            
        # 4. Refunds Table
        row_idx += 1
        sheet.merge_range(f'A{row_idx+1}:H{row_idx+1}', 'AVOIRS ÉMIS', section_format)
        row_idx += 1
        for col_idx, h in enumerate(detail_headers):
            sheet.write(row_idx, col_idx, h, header_format)
        row_idx += 1
        for ref in data['refunds']:
            mode_str = ref.get('payment_mode', '')
            if ref.get('payment_mode') in ('Chèque', 'Effet', 'Virement', 'cheque', 'effet', 'virement'):
                client_disp = ref.get('check_client_name') or ref.get('partner') or ''
                if client_disp:
                    mode_str += f" - {client_disp}"
            if ref.get('check_number'):
                mode_str += f" (N° {ref['check_number']})"
            sheet.write(row_idx, 0, str(ref['date']), center_format)
            sheet.write(row_idx, 1, ref['name'], border_format)
            sheet.write(row_idx, 2, ref['partner'], border_format)
            sheet.write(row_idx, 3, mode_str, center_format)
            sheet.write(row_idx, 4, ref['total'], num_format)
            sheet.write(row_idx, 5, ref.get('paid', 0.0), num_format)
            sheet.write(row_idx, 6, ref.get('residual', 0.0), num_format)
            sheet.write(row_idx, 7, ref['payment_state'], center_format)
            row_idx += 1
            
        # 5. Top Products
        row_idx += 1
        sheet.merge_range(f'A{row_idx+1}:H{row_idx+1}', 'PRODUITS LES PLUS VENDUS', section_format)
        row_idx += 1
        prod_headers = ['Produit', 'Quantité', 'CA']
        for col_idx, h in enumerate(prod_headers):
            sheet.write(row_idx, col_idx, h, header_format)
        row_idx += 1
        for prd in data['products']:
            sheet.write(row_idx, 0, prd['name'], border_format)
            sheet.write(row_idx, 1, prd['qty'], center_format)
            sheet.write(row_idx, 2, prd['ca'], num_format)
            row_idx += 1
            
        workbook.close()
        return output.getvalue()

    def _generate_csv_data(self, data):
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        
        # Title
        writer.writerow([f"{self.report_type == 'z' and 'RAPPORT Z' or 'RAPPORT X'} - CLÔTURE DES VENTES"])
        writer.writerow([])
        
        # Metadata
        writer.writerow(['Société', self.company_id.name])
        writer.writerow(['ICE', self.company_id.ice or ''])
        writer.writerow(['IF', self.company_id.company_if or ''])
        writer.writerow(['RC', self.company_id.rc or ''])
        writer.writerow(['Période', f"Du {self.date_start} au {self.date_end}"])
        writer.writerow(['Date de Génération', self.date_generation.strftime('%d/%m/%Y %H:%M:%S') if self.date_generation else ''])
        writer.writerow(['Utilisateur', self.user_id.name])
        writer.writerow(['Numéro Rapport', self.name])
        writer.writerow([])
        
        # 1. Summary
        writer.writerow(['=== RÉSUMÉ DES VENTES ==='])
        writer.writerow(['Indicateur', 'Valeur'])
        writer.writerow(['Nombre de factures', data['summary']['invoice_count']])
        writer.writerow(['Nombre d\'avoirs', data['summary']['refund_count']])
        writer.writerow(['Total Ventes TTC', data['summary']['total_total']])
        writer.writerow(['Factures réglées', data['summary']['invoices_paid']])
        writer.writerow(['Reste à encaisser factures', data['summary']['total_residual']])
        writer.writerow(['Encaissements créances antérieures', data['summary']['prior_payments_total']])
        writer.writerow(['Total général encaissé', data['summary']['payments_total']])
        writer.writerow([])
        
        # 2. Payments
        writer.writerow(['=== VENTILATION DES RÈGLEMENTS ==='])
        writer.writerow(['Type de règlement', 'Nombre', 'Montant Total'])
        for p in data['payments']:
            writer.writerow([p['mode'], p['count'], p['amount']])
        writer.writerow(['TOTAL ENCAISSÉ', sum(p['count'] for p in data['payments']), sum(p['amount'] for p in data['payments'])])
        writer.writerow([])
        
        # 3. Details Invoices
        writer.writerow(['=== DÉTAIL DES FACTURES ==='])
        writer.writerow(['Date', 'Facture', 'Client', 'Mode Règlement', 'Total TTC', 'Payé', 'Reste', 'Statut'])
        for inv in data['invoices']:
            mode_str = inv.get('payment_mode', '')
            if inv.get('payment_mode') in ('Chèque', 'Effet', 'Virement', 'cheque', 'effet', 'virement'):
                client_disp = inv.get('check_client_name') or inv.get('partner') or ''
                if client_disp:
                    mode_str += f" - {client_disp}"
            if inv.get('check_number'):
                mode_str += f" (N° {inv['check_number']})"
            writer.writerow([inv['date'], inv['name'], inv['partner'], mode_str, inv['total'], inv.get('paid', 0.0), inv.get('residual', 0.0), inv['payment_state']])
        writer.writerow([])
        
        # 4. Details Refunds
        writer.writerow(['=== DÉTAIL DES AVOIRS ==='])
        writer.writerow(['Date', 'Avoir', 'Client', 'Mode Règlement', 'Total TTC', 'Payé', 'Reste', 'Statut'])
        for ref in data['refunds']:
            mode_str = ref.get('payment_mode', '')
            if ref.get('payment_mode') in ('Chèque', 'Effet', 'Virement', 'cheque', 'effet', 'virement'):
                client_disp = ref.get('check_client_name') or ref.get('partner') or ''
                if client_disp:
                    mode_str += f" - {client_disp}"
            if ref.get('check_number'):
                mode_str += f" (N° {ref['check_number']})"
            writer.writerow([ref['date'], ref['name'], ref['partner'], mode_str, ref['total'], ref.get('paid', 0.0), ref.get('residual', 0.0), ref['payment_state']])
        writer.writerow([])
        
        # 6. Products
        writer.writerow(['=== PRODUITS LES PLUS VENDUS ==='])
        writer.writerow(['Produit', 'Quantité', 'CA'])
        for prd in data['products']:
            writer.writerow([prd['name'], prd['qty'], prd['ca']])
            
        return output.getvalue().encode('utf-8-sig')
