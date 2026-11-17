# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError

class AccountMoveGuard(models.Model):
    _inherit = 'account.move'

    def unlink(self):
        # Les super-administrateurs peuvent supprimer
        if not self.env.is_superuser() and not self.env.user.has_group('base.group_system'):
            roles = self.env.user.role_ids.filtered(lambda r: r.active)
            if roles and any(r.prevent_invoice_unlink for r in roles):
                raise UserError(_(
                    "Action Interdite : Votre rôle utilisateur ne vous autorise pas à supprimer les factures.\n"
                    "Veuillez contacter un administrateur ou la Direction."
                ))
            if roles and any(r.is_readonly_role for r in roles):
                raise UserError(_("Action Interdite : Votre profil est configuré en Consultation Seule."))
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.is_superuser() and not self.env.user.has_group('base.group_system'):
            roles = self.env.user.role_ids.filtered(lambda r: r.active)
            if roles and any(r.is_readonly_role for r in roles):
                raise UserError(_("Action Interdite : Votre profil est configuré en Consultation Seule (création impossible)."))
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.is_superuser() and not self.env.user.has_group('base.group_system'):
            roles = self.env.user.role_ids.filtered(lambda r: r.active)
            if roles and any(r.is_readonly_role for r in roles):
                raise UserError(_("Action Interdite : Votre profil est configuré en Consultation Seule (modification impossible)."))
        return super().write(vals)


class AccountPaymentGuard(models.Model):
    _inherit = 'account.payment'

    def unlink(self):
        if not self.env.is_superuser() and not self.env.user.has_group('base.group_system'):
            roles = self.env.user.role_ids.filtered(lambda r: r.active)
            if roles and any(r.prevent_payment_unlink for r in roles):
                raise UserError(_(
                    "Action Interdite : Votre rôle utilisateur ne vous autorise pas à supprimer les paiements et encaissements.\n"
                    "Veuillez contacter un administrateur ou la Direction."
                ))
            if roles and any(r.is_readonly_role for r in roles):
                raise UserError(_("Action Interdite : Votre profil est configuré en Consultation Seule."))
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.is_superuser() and not self.env.user.has_group('base.group_system'):
            roles = self.env.user.role_ids.filtered(lambda r: r.active)
            if roles and any(r.is_readonly_role for r in roles):
                raise UserError(_("Action Interdite : Votre profil est configuré en Consultation Seule (création de paiement impossible)."))
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.is_superuser() and not self.env.user.has_group('base.group_system'):
            roles = self.env.user.role_ids.filtered(lambda r: r.active)
            if roles and any(r.is_readonly_role for r in roles):
                raise UserError(_("Action Interdite : Votre profil est configuré en Consultation Seule (modification de paiement impossible)."))
        return super().write(vals)


class SaleOrderGuard(models.Model):
    _inherit = 'sale.order'

    def unlink(self):
        if not self.env.is_superuser() and not self.env.user.has_group('base.group_system'):
            roles = self.env.user.role_ids.filtered(lambda r: r.active)
            if roles and any(r.prevent_sale_order_unlink for r in roles):
                raise UserError(_(
                    "Action Interdite : Votre rôle utilisateur ne vous autorise pas à supprimer les bons de vente ou devis.\n"
                    "Veuillez contacter un administrateur."
                ))
            if roles and any(r.is_readonly_role for r in roles):
                raise UserError(_("Action Interdite : Votre profil est configuré en Consultation Seule."))
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.is_superuser() and not self.env.user.has_group('base.group_system'):
            roles = self.env.user.role_ids.filtered(lambda r: r.active)
            if roles and any(r.is_readonly_role for r in roles):
                raise UserError(_("Action Interdite : Votre profil est configuré en Consultation Seule (création de bon impossible)."))
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.is_superuser() and not self.env.user.has_group('base.group_system'):
            roles = self.env.user.role_ids.filtered(lambda r: r.active)
            if roles and any(r.is_readonly_role for r in roles):
                raise UserError(_("Action Interdite : Votre profil est configuré en Consultation Seule (modification impossible)."))
        return super().write(vals)


class ResPartnerGuard(models.Model):
    _inherit = 'res.partner'

    def unlink(self):
        if not self.env.is_superuser() and not self.env.user.has_group('base.group_system'):
            roles = self.env.user.role_ids.filtered(lambda r: r.active)
            if roles and any(r.prevent_partner_unlink for r in roles):
                raise UserError(_(
                    "Action Interdite : Votre rôle utilisateur ne vous autorise pas à supprimer les contacts ou clients."
                ))
            if roles and any(r.is_readonly_role for r in roles):
                raise UserError(_("Action Interdite : Votre profil est configuré en Consultation Seule."))
        return super().unlink()


class SuiviChequeGuard(models.Model):
    _inherit = 'suivi.cheque'

    def unlink(self):
        if not self.env.is_superuser() and not self.env.user.has_group('base.group_system'):
            roles = self.env.user.role_ids.filtered(lambda r: r.active)
            if roles and any(r.prevent_cheque_unlink for r in roles):
                raise UserError(_(
                    "Action Interdite : Votre rôle utilisateur ne vous autorise pas à supprimer les chèques ou effets enregistrés."
                ))
            if roles and any(r.is_readonly_role for r in roles):
                raise UserError(_("Action Interdite : Votre profil est configuré en Consultation Seule."))
        return super().unlink()

