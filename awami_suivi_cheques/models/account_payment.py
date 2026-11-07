# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    check_tracking_id = fields.Many2one(
        'suivi.cheque',
        string="Fiche de Suivi Chèque",
        copy=False,
        ondelete='set null',
        help="Lien vers la fiche de suivi et de monitoring du chèque."
    )

    check_state = fields.Selection(
        related='check_tracking_id.state',
        string="Statut du Chèque",
        store=True,
        readonly=True,
        help="Statut de suivi bancaire du chèque (Portefeuille, Déposé, Payé, Retour banque, Impayé)."
    )

    bank_name = fields.Char(
        string="Banque Émettrice",
        tracking=True,
        copy=False,
        help="Nom de la banque d'où provient le chèque (ex: Attijariwafa, BCP, BMCE, CIH...)"
    )

    def action_view_check_tracking(self):
        """Ouvre directement la fiche de suivi du chèque depuis le paiement."""
        self.ensure_one()
        if not self.check_tracking_id:
            # Si pas encore lié mais mode chèque, créer la fiche immédiatement
            self._sync_check_tracking()
        if self.check_tracking_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Suivi du Chèque / Effet'),
                'res_model': 'suivi.cheque',
                'res_id': self.check_tracking_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return False

    def _sync_check_tracking(self):
        """Synchronise ou crée la fiche de suivi pour chaque paiement chèque/effet."""
        Suivi = self.env['suivi.cheque']
        for pay in self:
            is_check = (
                pay.payment_mode in ('cheque', 'effet', 'traite', 'effet_cheque')
                or bool(pay.check_number)
            )
            if not is_check or not pay.partner_id:
                continue

            vals = {
                'check_number': pay.check_number or pay.memo or pay.name,
                'check_type': 'inbound' if pay.payment_type == 'inbound' else 'outbound',
                'payment_mode': 'effet' if pay.payment_mode in ('effet', 'traite') else 'cheque',
                'partner_id': pay.partner_id.id,
                'check_client_name': getattr(pay, 'check_client_name', False) or pay.partner_id.name,
                'amount': pay.amount,
                'currency_id': pay.currency_id.id,
                'company_id': pay.company_id.id,
                'journal_id': pay.journal_id.id,
                'date_reception': pay.date,
                'check_date_due': getattr(pay, 'check_date_due', False) or False,
                'payment_id': pay.id,
            }
            if getattr(pay, 'bank_name', False):
                vals['bank_name'] = pay.bank_name

            # Si le paiement est payé, répercuter
            if pay.state == 'paid' or getattr(pay, 'is_marked_paid', False):
                if not pay.check_tracking_id or pay.check_tracking_id.state in ('en_caisse', 'depose'):
                    vals['state'] = 'paye'
                    vals['date_cleared'] = pay.date or fields.Date.context_today(pay)
            elif pay.state == 'canceled':
                if pay.check_tracking_id and pay.check_tracking_id.state != 'annule':
                    vals['state'] = 'annule'

            if not pay.check_tracking_id:
                # Chercher si une fiche existe déjà par payment_id ou (check_number, partner_id)
                existing = Suivi.search([('payment_id', '=', pay.id)], limit=1)
                if not existing and pay.check_number:
                    existing = Suivi.search([
                        ('check_number', '=', pay.check_number),
                        ('partner_id', '=', pay.partner_id.id)
                    ], limit=1)
                if existing:
                    existing.write(vals)
                    pay.check_tracking_id = existing.id
                else:
                    tracking = Suivi.create(vals)
                    pay.check_tracking_id = tracking.id
            else:
                pay.check_tracking_id.write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        payments = super().create(vals_list)
        payments._sync_check_tracking()
        return payments

    def write(self, vals):
        res = super().write(vals)
        check_related_fields = [
            'payment_mode', 'check_number', 'check_client_name',
            'check_date_due', 'bank_name', 'amount', 'date',
            'partner_id', 'is_marked_paid', 'state'
        ]
        if any(f in vals for f in check_related_fields):
            self._sync_check_tracking()
        return res


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    bank_name = fields.Char(
        string="Banque Émettrice",
        copy=False,
        help="Nom de la banque émettrice du chèque ou de l'effet."
    )

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        if self.bank_name:
            payment_vals['bank_name'] = self.bank_name
        return payment_vals

