# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

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
    ], string="Mode de règlement", compute="_compute_payment_mode", store=True, readonly=False, tracking=True, default='especes')

    check_number = fields.Char(
        string="N° de série / Chèque / Effet",
        tracking=True,
        copy=False,
        help="Numéro de série du chèque ou de l'effet commercial (Traite/LCN) ou référence de virement."
    )

    transfer_order_number = fields.Char(
        string="N° Ordre de Virement",
        tracking=True,
        copy=False,
        help="Numéro ou référence de l'ordre de virement bancaire."
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

    check_image = fields.Binary(
        string="Photo du Chèque / Effet",
        attachment=True,
        copy=False,
        help="Photo ou scan du chèque ou de l'effet commercial."
    )

    @api.depends('company_id', 'partner_id', 'payment_mode')
    def _compute_journal_id(self):
        super()._compute_journal_id()
        for payment in self:
            company = payment.company_id or self.env.company
            domain = self.env['account.journal']._check_company_domain(company)
            mode = payment.payment_mode or 'especes'
            matching_j = False
            if mode == 'especes':
                matching_j = self.env['account.journal'].search([*domain, ('type', '=', 'cash')], limit=1)
            elif mode == 'cheque':
                matching_j = self.env['account.journal'].search([*domain, ('name', 'ilike', 'chèque')], limit=1)
            elif mode in ('effet', 'traite', 'effet_cheque'):
                matching_j = self.env['account.journal'].search([*domain, ('name', 'ilike', 'effet')], limit=1)
            elif mode == 'virement':
                matching_j = self.env['account.journal'].search([*domain, ('type', '=', 'bank'), ('name', 'not ilike', 'chèque'), ('name', 'not ilike', 'effet')], limit=1)
            
            if matching_j:
                payment.journal_id = matching_j
            elif not payment.journal_id:
                cash_j = self.env['account.journal'].search([*domain, ('type', '=', 'cash')], limit=1)
                if cash_j:
                    payment.journal_id = cash_j

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
                pay.payment_mode = 'especes'

    @api.depends('payment_method_line_id', 'journal_id', 'payment_type')
    def _compute_outstanding_account_id(self):
        super()._compute_outstanding_account_id()
        for pay in self:
            if not pay.outstanding_account_id and pay.payment_type:
                try:
                    pay.outstanding_account_id = pay._get_outstanding_account(pay.payment_type)
                except Exception:
                    pass
                if not pay.outstanding_account_id and pay.journal_id.default_account_id:
                    pay.outstanding_account_id = pay.journal_id.default_account_id

    @api.onchange('partner_id')
    def _onchange_partner_id_check_client(self):
        if self.payment_mode in ('cheque', 'effet', 'traite', 'effet_cheque'):
            if self.partner_id and not self.check_client_name:
                self.check_client_name = self.partner_id.name
            self.transfer_order_number = False
        elif self.payment_mode == 'virement':
            self.check_client_name = False
            self.check_date_due = False
            self.check_image = False
            if self.transfer_order_number:
                self.check_number = self.transfer_order_number
        else:
            self.check_client_name = False
            self.check_number = False
            self.check_date_due = False
            self.check_image = False
            self.transfer_order_number = False

    @api.onchange('payment_mode')
    def _onchange_payment_mode_check(self):
        if self.payment_mode in ('cheque', 'effet', 'traite', 'effet_cheque'):
            if self.partner_id and not self.check_client_name:
                self.check_client_name = self.partner_id.name
            self.transfer_order_number = False
        elif self.payment_mode == 'virement':
            self.check_client_name = False
            self.check_date_due = False
            self.check_image = False
            if self.transfer_order_number:
                self.check_number = self.transfer_order_number
            else:
                self.check_number = False
        else:
            self.check_client_name = False
            self.check_number = False
            self.check_date_due = False
            self.check_image = False
            self.transfer_order_number = False

        company = self.company_id or self.env.company
        domain = self.env['account.journal']._check_company_domain(company)
        if self.payment_mode == 'especes':
            j = self.env['account.journal'].search([*domain, ('type', '=', 'cash')], limit=1)
            if j:
                self.journal_id = j
        elif self.payment_mode == 'cheque':
            j = self.env['account.journal'].search([*domain, ('name', 'ilike', 'chèque')], limit=1)
            if j:
                self.journal_id = j
        elif self.payment_mode in ('effet', 'traite', 'effet_cheque'):
            j = self.env['account.journal'].search([*domain, ('name', 'ilike', 'effet')], limit=1)
            if j:
                self.journal_id = j
        elif self.payment_mode == 'virement':
            j = self.env['account.journal'].search([*domain, ('type', '=', 'bank'), ('name', 'not ilike', 'chèque'), ('name', 'not ilike', 'effet')], limit=1)
            if j:
                self.journal_id = j

    @api.onchange('transfer_order_number')
    def _onchange_transfer_order_number(self):
        if self.payment_mode == 'virement' and self.transfer_order_number:
            self.check_number = self.transfer_order_number

    @api.onchange('journal_id')
    def _onchange_journal_id_sync_mode(self):
        if self.journal_id:
            j_type = self.journal_id.type or ''
            j_name = (self.journal_id.name or '').lower()
            if 'chèque' in j_name or 'cheque' in j_name:
                self.payment_mode = 'cheque'
            elif 'effet' in j_name or 'traite' in j_name:
                self.payment_mode = 'effet'
            elif 'espèce' in j_name or 'espece' in j_name or j_type == 'cash' or 'caisse' in j_name:
                self.payment_mode = 'especes'
            elif 'virement' in j_name or j_type == 'bank':
                self.payment_mode = 'virement'

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

    def action_post(self):
        for pay in self:
            if pay.payment_mode == 'virement' and not (pay.transfer_order_number or pay.check_number):
                raise UserError(_("Le numéro d'ordre de virement est obligatoire pour valider un paiement par virement."))
            if pay.payment_mode in ('cheque', 'effet', 'traite', 'effet_cheque') and not pay.check_number:
                raise UserError(_("Le numéro de chèque / effet est obligatoire pour valider ce mode de règlement."))
            if pay.payment_mode == 'virement' and pay.transfer_order_number and not pay.check_number:
                pay.check_number = pay.transfer_order_number
        return super().action_post()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('transfer_order_number') and not vals.get('check_number'):
                vals['check_number'] = vals['transfer_order_number']
            elif vals.get('check_number') and not vals.get('transfer_order_number') and vals.get('payment_mode') == 'virement':
                vals['transfer_order_number'] = vals['check_number']
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('transfer_order_number') and 'check_number' not in vals:
            vals['check_number'] = vals['transfer_order_number']
        elif vals.get('check_number') and 'transfer_order_number' not in vals:
            for pay in self:
                if (vals.get('payment_mode') or pay.payment_mode) == 'virement':
                    vals['transfer_order_number'] = vals['check_number']
                    break
        return super().write(vals)

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
            if pay.transfer_order_number:
                vals['transfer_order_number'] = pay.transfer_order_number
            if pay.check_number:
                vals['check_number'] = pay.check_number
            elif pay.transfer_order_number:
                vals['check_number'] = pay.transfer_order_number
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
    ], string="Mode de règlement", compute="_compute_payment_mode", store=True, readonly=False, default='especes')

    check_number = fields.Char(string="N° de série / Chèque / Effet", copy=False)
    transfer_order_number = fields.Char(string="N° Ordre de Virement", copy=False)
    check_client_name = fields.Char(string="Nom du client (Chèque / Effet)", copy=False)
    check_date_due = fields.Date(string="Date d'échéance", copy=False)
    check_image = fields.Binary(
        string="Photo du Chèque / Effet",
        attachment=True,
        copy=False,
        help="Photo ou scan du chèque ou de l'effet commercial."
    )

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

    @api.depends('can_edit_wizard')
    def _compute_journal_id(self):
        super()._compute_journal_id()
        for wiz in self:
            active_move = wiz._get_active_move()
            mode = getattr(active_move, 'payment_mode', False) if active_move else False
            if not mode:
                mode = 'especes'
            domain = [('company_id', '=', wiz.company_id.id)]
            matching_journal = False
            if mode == 'especes':
                matching_journal = self.env['account.journal'].search(domain + [('type', '=', 'cash')], limit=1)
            elif mode == 'cheque':
                matching_journal = self.env['account.journal'].search(domain + [('name', 'ilike', 'chèque')], limit=1)
            elif mode in ('effet', 'traite', 'effet_cheque'):
                matching_journal = self.env['account.journal'].search(domain + [('name', 'ilike', 'effet')], limit=1)
            elif mode == 'virement':
                matching_journal = self.env['account.journal'].search(domain + [('type', '=', 'bank'), ('name', 'not ilike', 'chèque'), ('name', 'not ilike', 'effet')], limit=1)
            if matching_journal:
                wiz.journal_id = matching_journal
            elif not wiz.journal_id:
                cash_j = self.env['account.journal'].search(domain + [('type', '=', 'cash')], limit=1)
                if cash_j:
                    wiz.journal_id = cash_j

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
                else:
                    wiz.payment_mode = 'especes'

            # Pré-remplissage des informations de chèque / tiers / virement si disponibles
            active_move = wiz._get_active_move()
            if wiz.payment_mode in ('cheque', 'effet', 'traite', 'effet_cheque'):
                wiz.transfer_order_number = False
                if active_move:
                    if not wiz.check_client_name:
                        wiz.check_client_name = getattr(active_move, 'check_client_name', False) or (active_move.partner_id.name if active_move.partner_id else '')
                    if not wiz.check_number and getattr(active_move, 'check_number', False):
                        wiz.check_number = active_move.check_number
                    if not wiz.check_date_due and getattr(active_move, 'check_date_due', False):
                        wiz.check_date_due = active_move.check_date_due
                elif wiz.partner_id and not wiz.check_client_name:
                    wiz.check_client_name = wiz.partner_id.name
            elif wiz.payment_mode == 'virement':
                wiz.check_client_name = False
                wiz.check_date_due = False
                wiz.check_image = False
                if active_move:
                    if not wiz.transfer_order_number:
                        wiz.transfer_order_number = getattr(active_move, 'transfer_order_number', False) or getattr(active_move, 'check_number', False) or ''
                    wiz.check_number = wiz.transfer_order_number
            else:
                wiz.check_client_name = False
                wiz.check_number = False
                wiz.check_date_due = False
                wiz.check_image = False
                wiz.transfer_order_number = False

    @api.onchange('partner_id')
    def _onchange_partner_id_check_client(self):
        if self.payment_mode in ('cheque', 'effet', 'traite', 'effet_cheque'):
            if self.partner_id and not self.check_client_name:
                self.check_client_name = self.partner_id.name
            self.transfer_order_number = False
        elif self.payment_mode == 'virement':
            self.check_client_name = False
            self.check_date_due = False
            self.check_image = False
            if self.transfer_order_number:
                self.check_number = self.transfer_order_number
        else:
            self.check_client_name = False
            self.check_number = False
            self.check_date_due = False
            self.check_image = False
            self.transfer_order_number = False

    @api.onchange('payment_mode')
    def _onchange_payment_mode_check(self):
        if self.payment_mode in ('cheque', 'effet', 'traite', 'effet_cheque'):
            if self.partner_id and not self.check_client_name:
                self.check_client_name = self.partner_id.name
            self.transfer_order_number = False
        elif self.payment_mode == 'virement':
            self.check_client_name = False
            self.check_date_due = False
            self.check_image = False
            if self.transfer_order_number:
                self.check_number = self.transfer_order_number
            else:
                self.check_number = False
        else:
            self.check_client_name = False
            self.check_number = False
            self.check_date_due = False
            self.check_image = False
            self.transfer_order_number = False

        company = self.company_id or self.env.company
        domain = self.env['account.journal']._check_company_domain(company)
        if self.payment_mode == 'especes':
            j = self.env['account.journal'].search([*domain, ('type', '=', 'cash')], limit=1)
            if j:
                self.journal_id = j
        elif self.payment_mode == 'cheque':
            j = self.env['account.journal'].search([*domain, ('name', 'ilike', 'chèque')], limit=1)
            if j:
                self.journal_id = j
        elif self.payment_mode in ('effet', 'traite', 'effet_cheque'):
            j = self.env['account.journal'].search([*domain, ('name', 'ilike', 'effet')], limit=1)
            if j:
                self.journal_id = j
        elif self.payment_mode == 'virement':
            j = self.env['account.journal'].search([*domain, ('type', '=', 'bank'), ('name', 'not ilike', 'chèque'), ('name', 'not ilike', 'effet')], limit=1)
            if j:
                self.journal_id = j

    @api.onchange('transfer_order_number')
    def _onchange_transfer_order_number(self):
        if self.payment_mode == 'virement' and self.transfer_order_number:
            self.check_number = self.transfer_order_number

    @api.onchange('journal_id')
    def _onchange_journal_id_sync_mode(self):
        if self.journal_id:
            j_type = self.journal_id.type or ''
            j_name = (self.journal_id.name or '').lower()
            if 'chèque' in j_name or 'cheque' in j_name:
                self.payment_mode = 'cheque'
            elif 'effet' in j_name or 'traite' in j_name:
                self.payment_mode = 'effet'
            elif 'espèce' in j_name or 'espece' in j_name or j_type == 'cash' or 'caisse' in j_name:
                self.payment_mode = 'especes'
            elif 'virement' in j_name or j_type == 'bank':
                self.payment_mode = 'virement'

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        if self.payment_mode:
            payment_vals['payment_mode'] = self.payment_mode
        if self.payment_mode in ('cheque', 'effet', 'traite', 'effet_cheque'):
            payment_vals['check_number'] = self.check_number or False
            payment_vals['check_client_name'] = self.check_client_name or False
            payment_vals['check_date_due'] = self.check_date_due or False
            payment_vals['check_image'] = self.check_image or False
            payment_vals['transfer_order_number'] = False
        elif self.payment_mode == 'virement':
            ov_num = self.transfer_order_number or self.check_number or False
            payment_vals['transfer_order_number'] = ov_num
            payment_vals['check_number'] = ov_num
            payment_vals['check_client_name'] = False
            payment_vals['check_date_due'] = False
            payment_vals['check_image'] = False
        else:
            payment_vals['check_number'] = False
            payment_vals['check_client_name'] = False
            payment_vals['check_date_due'] = False
            payment_vals['check_image'] = False
            payment_vals['transfer_order_number'] = False
        return payment_vals

    def _create_payments(self):
        for wiz in self:
            if wiz.payment_mode == 'virement' and not (wiz.transfer_order_number or wiz.check_number):
                raise UserError(_("Le numéro d'ordre de virement est obligatoire pour valider un paiement par virement."))
            if wiz.payment_mode in ('cheque', 'effet', 'traite', 'effet_cheque') and not wiz.check_number:
                raise UserError(_("Le numéro de chèque / effet est obligatoire pour valider ce mode de règlement."))
        payments = super()._create_payments()
        moves = self.line_ids.move_id
        vals = {}
        if self.payment_mode:
            vals['payment_mode'] = self.payment_mode
        if self.payment_mode in ('cheque', 'effet', 'traite', 'effet_cheque'):
            vals['check_number'] = self.check_number or False
            vals['check_client_name'] = self.check_client_name or False
            vals['check_date_due'] = self.check_date_due or False
            vals['transfer_order_number'] = False
        elif self.payment_mode == 'virement':
            ov_num = self.transfer_order_number or self.check_number or False
            vals['transfer_order_number'] = ov_num
            vals['check_number'] = ov_num
            vals['check_client_name'] = False
            vals['check_date_due'] = False
        else:
            vals['check_number'] = False
            vals['check_client_name'] = False
            vals['check_date_due'] = False
            vals['transfer_order_number'] = False
        if vals:
            for move in moves:
                if move.is_invoice(include_receipts=True):
                    move.sudo().write(vals)
        return payments

    def action_create_payments(self):
        for wiz in self:
            if wiz.payment_mode == 'virement' and not (wiz.transfer_order_number or wiz.check_number):
                raise UserError(_("Le numéro d'ordre de virement est obligatoire pour valider un paiement par virement."))
            if wiz.payment_mode in ('cheque', 'effet', 'traite', 'effet_cheque') and not wiz.check_number:
                raise UserError(_("Le numéro de chèque / effet est obligatoire pour valider ce mode de règlement."))
        return super().action_create_payments()
