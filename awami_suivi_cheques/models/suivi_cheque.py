# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SuiviCheque(models.Model):
    _name = 'suivi.cheque'
    _description = 'Suivi des Chèques et Effets'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'check_date_due asc, date_reception desc, id desc'

    name = fields.Char(
        string="Référence",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nouveau')
    )

    check_number = fields.Char(
        string="N° de Chèque / Effet",
        required=True,
        tracking=True,
        index=True,
        help="Numéro de série du chèque ou de l'effet commercial."
    )

    check_type = fields.Selection([
        ('inbound', 'Chèque Client (Reçu)'),
        ('outbound', 'Chèque Fournisseur (Émis)'),
    ], string="Type de Chèque", required=True, default='inbound', tracking=True)

    payment_mode = fields.Selection([
        ('cheque', 'Chèque'),
        ('effet', 'Effet / Traite'),
    ], string="Nature du Document", default='cheque', required=True, tracking=True)

    partner_id = fields.Many2one(
        'res.partner',
        string="Client / Fournisseur",
        required=True,
        tracking=True,
        index=True
    )

    check_client_name = fields.Char(
        string="Tireur / Émetteur",
        tracking=True,
        help="Nom figurant sur le chèque (titulaire du compte ou émetteur effectif)."
    )

    bank_name = fields.Char(
        string="Banque Émettrice",
        tracking=True,
        help="Nom de la banque d'où provient le chèque (ex: Attijariwafa, BCP, BMCE, CIH...)"
    )

    bank_account = fields.Char(
        string="N° Compte / RIB",
        help="Numéro de compte bancaire ou RIB du tireur."
    )

    amount = fields.Monetary(
        string="Montant",
        required=True,
        tracking=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string="Devise",
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    company_id = fields.Many2one(
        'res.company',
        string="Société",
        default=lambda self: self.env.company,
        required=True
    )

    # Dates de gestion
    date_reception = fields.Date(
        string="Date de Réception",
        default=fields.Date.context_today,
        required=True,
        tracking=True
    )

    check_date_due = fields.Date(
        string="Date d'Échéance",
        tracking=True,
        index=True,
        help="Date limite d'encaissement prévue."
    )

    date_deposit = fields.Date(
        string="Date de Dépôt / Remise",
        tracking=True,
        help="Date à laquelle le chèque a été remis à l'encaissement à la banque."
    )

    date_cleared = fields.Date(
        string="Date d'Encaissement",
        tracking=True,
        help="Date effective du paiement / crédit sur le relevé bancaire."
    )

    date_rejection = fields.Date(
        string="Date de Retour / Rejet",
        tracking=True,
        help="Date du retour du chèque impayé par la banque."
    )

    # Statuts
    state = fields.Selection([
        ('en_caisse', 'En Portefeuille'),
        ('depose', 'Déposé à la Banque'),
        ('paye', 'Payé / Encaissé'),
        ('retour_banque', 'Retour de la Banque'),
        ('impaye', 'Impayé'),
        ('annule', 'Annulé'),
    ], string="Statut", default='en_caisse', required=True, tracking=True, index=True)

    # Motifs de rejet
    rejection_reason = fields.Selection([
        ('sans_provision', 'Défaut de provision (Sans provision)'),
        ('signature', 'Signature non conforme / Absente'),
        ('opposition', 'Opposition pour perte / vol / litige'),
        ('vice_forme', 'Vice de forme (Date, montant en lettres...)'),
        ('compte_bloque', 'Compte bloqué ou clôturé'),
        ('autre', 'Autre motif'),
    ], string="Motif du Retour Banque", tracking=True)

    rejection_notes = fields.Text(
        string="Détails du Rejet / Mesures",
        tracking=True,
        help="Précisions sur les motifs du rejet, démarches auprès du client, relances..."
    )

    # Liens comptables
    payment_id = fields.Many2one(
        'account.payment',
        string="Paiement Comptable",
        copy=False,
        ondelete='set null',
        index=True
    )

    journal_id = fields.Many2one(
        'account.journal',
        string="Journal Comptable",
        domain="[('type', 'in', ('bank', 'cash'))]"
    )

    deposit_journal_id = fields.Many2one(
        'account.journal',
        string="Banque de Dépôt",
        domain="[('type', '=', 'bank')]",
        help="Compte bancaire de votre société où le chèque est remis à l'encaissement."
    )

    move_id = fields.Many2one(
        'account.move',
        string="Pièce Comptable",
        related='payment_id.move_id',
        store=True,
        readonly=True
    )

    invoice_ids = fields.Many2many(
        'account.move',
        string="Factures Réglées",
        compute='_compute_invoice_ids',
        store=True
    )

    notes = fields.Text(string="Notes internes")

    # Alertes et échéances calculées
    is_overdue = fields.Boolean(
        string="Échu",
        compute='_compute_due_status',
        store=True
    )

    due_status = fields.Selection([
        ('future', 'À venir'),
        ('today', 'Échéance aujourd\'hui'),
        ('overdue', 'Échu (En retard)'),
    ], string="Alerte Échéance", compute='_compute_due_status', store=True)

    days_due = fields.Integer(
        string="Jours restants / Retard",
        compute='_compute_due_status'
    )

    invoice_count = fields.Integer(
        string="Nombre de Factures",
        compute='_compute_invoice_ids'
    )

    @api.depends('payment_id', 'payment_id.reconciled_invoice_ids', 'payment_id.reconciled_bill_ids')
    def _compute_invoice_ids(self):
        for rec in self:
            if rec.payment_id:
                invoices = rec.payment_id.reconciled_invoice_ids | rec.payment_id.reconciled_bill_ids
                rec.invoice_ids = invoices
                rec.invoice_count = len(invoices)
            else:
                rec.invoice_ids = False
                rec.invoice_count = 0

    @api.depends('check_date_due', 'state')
    def _compute_due_status(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if not rec.check_date_due or rec.state in ('paye', 'annule'):
                rec.is_overdue = False
                rec.due_status = False
                rec.days_due = 0
            else:
                delta = (rec.check_date_due - today).days
                rec.days_due = delta
                if delta < 0:
                    rec.is_overdue = True
                    rec.due_status = 'overdue'
                elif delta == 0:
                    rec.is_overdue = False
                    rec.due_status = 'today'
                else:
                    rec.is_overdue = False
                    rec.due_status = 'future'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nouveau')) == _('Nouveau'):
                vals['name'] = self.env['ir.sequence'].next_by_code('suivi.cheque') or '/'
        return super().create(vals_list)

    # -------------------------------------------------------------------------
    # WORKFLOW ACTIONS
    # -------------------------------------------------------------------------

    def action_deposer(self):
        """Passer au statut 'Déposé à la Banque'."""
        today = fields.Date.context_today(self)
        for rec in self:
            rec.write({
                'state': 'depose',
                'date_deposit': rec.date_deposit or today,
            })
            rec.message_post(body=_("Chèque déposé à la banque pour encaissement le %s.") % (rec.date_deposit or today))

    def action_payer(self):
        """Passer au statut 'Payé / Encaissé' et synchroniser le paiement lié."""
        today = fields.Date.context_today(self)
        for rec in self:
            rec.write({
                'state': 'paye',
                'date_cleared': rec.date_cleared or today,
            })
            rec.message_post(body=_("Chèque marqué comme **Payé / Encaissé** avec succès le %s.") % (rec.date_cleared or today))
            if rec.payment_id:
                rec.payment_id.write({
                    'is_marked_paid': True,
                    'state': 'paid',
                })

    def action_retour_banque(self):
        """Passer au statut 'Retour de la Banque' (Rejet bancaire)."""
        today = fields.Date.context_today(self)
        for rec in self:
            rec.write({
                'state': 'retour_banque',
                'date_rejection': rec.date_rejection or today,
            })
            reason = dict(rec._fields['rejection_reason'].selection).get(rec.rejection_reason, 'Non spécifié')
            rec.message_post(body=_(
                "**Alerte : Retour de la banque** enregistré le %s.<br/>"
                "Motif : <b>%s</b><br/>"
                "Détails : %s"
            ) % (rec.date_rejection or today, reason, rec.rejection_notes or '-'))
            if rec.payment_id and rec.payment_id.is_marked_paid:
                rec.payment_id.write({'is_marked_paid': False})

    def action_impaye(self):
        """Déclarer le chèque comme 'Impayé'."""
        today = fields.Date.context_today(self)
        for rec in self:
            rec.write({
                'state': 'impaye',
                'date_rejection': rec.date_rejection or today,
            })
            reason = dict(rec._fields['rejection_reason'].selection).get(rec.rejection_reason, 'Non spécifié')
            rec.message_post(body=_(
                "**Chèque déclaré IMPAYÉ** le %s.<br/>"
                "Motif : <b>%s</b><br/>"
                "Détails : %s"
            ) % (rec.date_rejection or today, reason, rec.rejection_notes or '-'))
            if rec.payment_id and rec.payment_id.is_marked_paid:
                rec.payment_id.write({'is_marked_paid': False})

    def action_remettre_en_caisse(self):
        """Remettre le chèque en portefeuille (ex: après régularisation ou réclamation)."""
        for rec in self:
            rec.write({'state': 'en_caisse'})
            rec.message_post(body=_("Chèque remis en portefeuille."))

    def action_annuler(self):
        """Annuler le chèque."""
        for rec in self:
            rec.write({'state': 'annule'})
            rec.message_post(body=_("Chèque annulé."))

    # -------------------------------------------------------------------------
    # SMART BUTTONS
    # -------------------------------------------------------------------------

    def action_view_payment(self):
        self.ensure_one()
        if not self.payment_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('Paiement Comptable'),
            'res_model': 'account.payment',
            'res_id': self.payment_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_invoices(self):
        self.ensure_one()
        invoices = self.invoice_ids
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Factures Réglées'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('id', 'in', invoices.ids)],
        }
        if len(invoices) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = invoices.id
        return action

    # -------------------------------------------------------------------------
    # INITIALISATION AUTOMATIQUE DES CHÈQUES EXISTANTS
    # -------------------------------------------------------------------------

    @api.model
    def _init_existing_cheques(self):
        """Scanne la base pour importer automatiquement tous les chèques déjà saisis."""
        Payment = self.env['account.payment']
        payments = Payment.search([
            '|',
            ('check_number', '!=', False),
            ('payment_mode', 'in', ('cheque', 'effet', 'traite', 'effet_cheque'))
        ])
        created_count = 0
        for pay in payments:
            existing = self.search([('payment_id', '=', pay.id)], limit=1)
            if not existing and pay.check_number:
                existing = self.search([('check_number', '=', pay.check_number), ('partner_id', '=', pay.partner_id.id)], limit=1)
            if existing:
                if not pay.check_tracking_id:
                    pay.sudo().write({'check_tracking_id': existing.id})
                continue

            # Détermination de l'état
            if pay.state == 'paid' or getattr(pay, 'is_marked_paid', False):
                initial_state = 'paye'
            elif pay.state == 'posted':
                initial_state = 'depose' if pay.journal_id.type == 'bank' else 'en_caisse'
            else:
                initial_state = 'en_caisse'

            vals = {
                'name': self.env['ir.sequence'].next_by_code('suivi.cheque') or '/',
                'check_number': pay.check_number or pay.name,
                'check_type': 'inbound' if pay.payment_type == 'inbound' else 'outbound',
                'payment_mode': 'effet' if pay.payment_mode in ('effet', 'traite') else 'cheque',
                'partner_id': pay.partner_id.id,
                'check_client_name': getattr(pay, 'check_client_name', False) or (pay.partner_id.name if pay.partner_id else ''),
                'amount': pay.amount,
                'currency_id': pay.currency_id.id,
                'company_id': pay.company_id.id,
                'journal_id': pay.journal_id.id,
                'date_reception': pay.date,
                'check_date_due': getattr(pay, 'check_date_due', False) or False,
                'date_cleared': pay.date if initial_state == 'paye' else False,
                'payment_id': pay.id,
                'state': initial_state,
            }
            tracking = self.create(vals)
            pay.sudo().write({'check_tracking_id': tracking.id})
            created_count += 1

        # Scanner également les factures ayant un numéro de chèque sans paiement direct
        Move = self.env['account.move']
        moves_with_checks = Move.search([
            ('check_number', '!=', False),
            ('move_type', 'in', ('out_invoice', 'in_invoice', 'out_refund', 'in_refund'))
        ])
        for mv in moves_with_checks:
            existing = self.search([
                ('check_number', '=', mv.check_number),
                ('partner_id', '=', mv.partner_id.id)
            ], limit=1)
            if existing:
                continue

            initial_state = 'paye' if mv.payment_state in ('paid', 'in_payment') else 'en_caisse'
            vals = {
                'name': self.env['ir.sequence'].next_by_code('suivi.cheque') or '/',
                'check_number': mv.check_number,
                'check_type': 'inbound' if mv.move_type in ('out_invoice', 'out_refund') else 'outbound',
                'payment_mode': 'effet' if mv.payment_mode in ('effet', 'traite') else 'cheque',
                'partner_id': mv.partner_id.id,
                'check_client_name': getattr(mv, 'check_client_name', False) or (mv.partner_id.name if mv.partner_id else ''),
                'amount': mv.amount_total,
                'currency_id': mv.currency_id.id,
                'company_id': mv.company_id.id,
                'journal_id': mv.journal_id.id,
                'date_reception': mv.date or mv.invoice_date,
                'check_date_due': getattr(mv, 'check_date_due', False) or False,
                'date_cleared': mv.date if initial_state == 'paye' else False,
                'state': initial_state,
            }
            self.create(vals)
            created_count += 1

        return created_count
