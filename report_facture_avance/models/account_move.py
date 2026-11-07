# -*- coding: utf-8 -*-
from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    is_report_hidden = fields.Boolean(
        string="Masqué (Suivi Avances)",
        default=False,
        copy=False,
        index=True,
        help="Si coché, ce mouvement (facture ou avance) sera masqué par défaut dans le Suivi des Factures et Avances."
    )

    def action_toggle_report_hidden(self):
        for move in self:
            move.is_report_hidden = not move.is_report_hidden

    def action_hide_in_report(self):
        self.write({'is_report_hidden': True})

    def action_unhide_in_report(self):
        self.write({'is_report_hidden': False})

