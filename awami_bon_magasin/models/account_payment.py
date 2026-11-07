# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    is_marked_paid = fields.Boolean(
        string="Marqué comme Payé",
        default=False,
        copy=False,
        tracking=True,
        help="Permet de valider manuellement le paiement au statut Payé sans attendre le rapprochement bancaire."
    )

    payment_mode = fields.Selection([
        ('virement', 'Virement bancaire'),
        ('cheque', 'Chèque'),
        ('effet', 'Effet'),
        ('traite', 'Effet / Traite'),
        ('effet_cheque', 'Effet / Chèque'),
        ('especes', 'Espèces'),
    ], string="Mode de règlement", compute="_compute_payment_mode", store=True, readonly=False, tracking=True)

    check_number = fields.Char(
        string="N° de série / Chèque / Effet",
        tracking=True,
        copy=False,
        help="Numéro de série du chèque ou de l'effet commercial (Traite/LCN) ou référence de virement."
    )

    check_client_name = fields.Char(
        string="Nom du client (Chèque / Effet)",
        tracking=True,
        copy=False,
        help="Nom du client ou titulaire figurant sur le chèque ou l'effet."
    )

    check_date_due = fields.Date(
        string="Date d'échéance",
        tracking=True,
        copy=False,
        help="Date d'échéance de l'effet ou date d'encaissement prévue du chèque."
    )

    @api.depends('payment_method_line_id', 'journal_id')
    def _compute_payment_mode(self):
        for pay in self:
            method_name = (pay.payment_method_line_id.name or '').lower()
            journal_type = pay.journal_id.type or ''
            journal_name = (pay.journal_id.name or '').lower()

            if 'virement' in method_name or 'virement' in journal_name:
                pay.payment_mode = 'virement'
            elif 'chèque' in method_name or 'cheque' in method_name or 'chèque' in journal_name or 'cheque' in journal_name:
                pay.payment_mode = 'cheque'
            elif 'effet' in method_name or 'traite' in method_name or 'effet' in journal_name:
                pay.payment_mode = 'effet'
            elif 'espèce' in method_name or 'espece' in method_name or journal_type == 'cash' or 'caisse' in journal_name:
                pay.payment_mode = 'especes'
            elif not pay.payment_mode:
                pay.payment_mode = 'virement' if journal_type == 'bank' else 'especes'

    @api.onchange('partner_id')
    def _onchange_partner_id_check_client(self):
        if self.partner_id and not self.check_client_name:
            self.check_client_name = self.partner_id.name

    @api.onchange('payment_mode')
    def _onchange_payment_mode_check(self):
        if self.payment_mode in ('cheque', 'effet', 'traite', 'effet_cheque'):
            if self.partner_id and not self.check_client_name:
                self.check_client_name = self.partner_id.name

    def action_mark_as_paid(self):
        """Bouton manuel pour passer le statut de 'En cours de traitement' à 'Payé'."""
        for payment in self:
            payment.is_marked_paid = True
            payment.state = 'paid'

    def action_unmark_as_paid(self):
        """Bouton pour réinitialiser le statut 'Payé' forcé."""
        for payment in self:
            payment.is_marked_paid = False
            payment._compute_state()

    def action_cancel(self):
        self.write({'is_marked_paid': False})
        return super().action_cancel()

    def action_draft(self):
        self.write({'is_marked_paid': False})
        return super().action_draft()

    def unlink(self):
        self.write({'is_marked_paid': False})
        return super().unlink()

    @api.depends('is_marked_paid')
    def _compute_state(self):
        super()._compute_state()
        for payment in self:
            # Ne JAMAIS forcer l'état 'paid' si le paiement est annulé, brouillon ou rejeté
            if payment.state in ('draft', 'canceled', 'rejected'):
                continue
            # Ne JAMAIS forcer l'état 'paid' si le paiement n'a pas de pièce comptable alors qu'un compte en suspens existe
            if not payment.move_id and payment.outstanding_account_id:
                continue
            if payment.is_marked_paid:
                payment.state = 'paid'
            elif payment.journal_id.type == 'cash' and payment.state == 'in_process':
                # Les paiements en espèces sont physiquement encaissés immédiatement en caisse
                payment.state = 'paid'

    def _synchronize_to_moves(self, changed_fields):
        super()._synchronize_to_moves(changed_fields)
        for pay in self:
            vals = {}
            if pay.payment_mode:
                vals['payment_mode'] = pay.payment_mode
            if pay.check_number:
                vals['check_number'] = pay.check_number
            if pay.check_client_name:
                vals['check_client_name'] = pay.check_client_name
            if pay.check_date_due:
                vals['check_date_due'] = pay.check_date_due
            
            if vals and pay.move_id:
                pay.move_id.write(vals)
                
            if vals:
                # Synchroniser également vers les factures clients/fournisseurs rapprochées
                invoices = pay.reconciled_invoice_ids | pay.reconciled_bill_ids
                for inv in invoices:
                    inv.sudo().write(vals)


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    payment_mode = fields.Selection([
        ('virement', 'Virement bancaire'),
        ('cheque', 'Chèque'),
        ('effet', 'Effet'),
        ('traite', 'Effet / Traite'),
        ('effet_cheque', 'Effet / Chèque'),
        ('especes', 'Espèces'),
    ], string="Mode de règlement", compute="_compute_payment_mode", store=True, readonly=False)

    check_number = fields.Char(string="N° de série / Chèque / Effet", copy=False)
    check_client_name = fields.Char(string="Nom du client (Chèque / Effet)", copy=False)
    check_date_due = fields.Date(string="Date d'échéance", copy=False)

    def _get_active_move(self):
        self.ensure_one()
        moves = self.line_ids.move_id
        if not moves:
            active_model = self._context.get('active_model')
            active_ids = self._context.get('active_ids', [])
            if active_model == 'account.move':
                moves = self.env['account.move'].browse(active_ids).exists()
            elif active_model == 'account.move.line':
                moves = self.env['account.move.line'].browse(active_ids).exists().move_id
        return moves[:1]

    @api.depends('payment_method_line_id', 'journal_id')
    def _compute_payment_mode(self):
        for wiz in self:
            method_name = (wiz.payment_method_line_id.name or '').lower()
            journal_type = wiz.journal_id.type or ''
            journal_name = (wiz.journal_id.name or '').lower()

            if 'virement' in method_name or 'virement' in journal_name:
                wiz.payment_mode = 'virement'
            elif 'chèque' in method_name or 'cheque' in method_name or 'chèque' in journal_name or 'cheque' in journal_name:
                wiz.payment_mode = 'cheque'
            elif 'effet' in method_name or 'traite' in method_name or 'effet' in journal_name:
                wiz.payment_mode = 'effet'
            elif 'espèce' in method_name or 'espece' in method_name or journal_type == 'cash' or 'caisse' in journal_name:
                wiz.payment_mode = 'especes'
            else:
                active_move = wiz._get_active_move()
                if active_move and getattr(active_move, 'payment_mode', False):
                    wiz.payment_mode = active_move.payment_mode
                elif not wiz.payment_mode:
                    wiz.payment_mode = 'virement' if journal_type == 'bank' else 'especes'

            # Pré-remplissage des informations de chèque / tiers si disponibles
            active_move = wiz._get_active_move()
            if active_move:
                if not wiz.check_client_name:
                    wiz.check_client_name = getattr(active_move, 'check_client_name', False) or (active_move.partner_id.name if active_move.partner_id else '')
                if not wiz.check_number and getattr(active_move, 'check_number', False):
                    wiz.check_number = active_move.check_number
                if not wiz.check_date_due and getattr(active_move, 'check_date_due', False):
                    wiz.check_date_due = active_move.check_date_due
            elif wiz.partner_id and not wiz.check_client_name:
                wiz.check_client_name = wiz.partner_id.name

    @api.onchange('partner_id')
    def _onchange_partner_id_check_client(self):
        if self.partner_id and not self.check_client_name:
            self.check_client_name = self.partner_id.name

    @api.onchange('payment_mode')
    def _onchange_payment_mode_check(self):
        if self.payment_mode in ('cheque', 'effet', 'traite', 'effet_cheque'):
            if self.partner_id and not self.check_client_name:
                self.check_client_name = self.partner_id.name

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        if self.payment_mode:
            payment_vals['payment_mode'] = self.payment_mode
        if self.check_number:
            payment_vals['check_number'] = self.check_number
        if self.check_client_name:
            payment_vals['check_client_name'] = self.check_client_name
        if self.check_date_due:
            payment_vals['check_date_due'] = self.check_date_due
        return payment_vals

    def _create_payments(self):
        payments = super()._create_payments()
        moves = self.line_ids.move_id
        vals = {}
        if self.payment_mode:
            vals['payment_mode'] = self.payment_mode
        if self.check_number:
            vals['check_number'] = self.check_number
        if self.check_client_name:
            vals['check_client_name'] = self.check_client_name
        if self.check_date_due:
            vals['check_date_due'] = self.check_date_due
        if vals:
            for move in moves:
                if move.is_invoice(include_receipts=True):
                    move.sudo().write(vals)
        return payments

