# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools

class ReportFactureAvance(models.Model):
    _name = 'report.facture.avance'
    _description = 'Suivi Factures et Avances'
    _auto = False
    _order = 'date desc, id desc'

    move_id = fields.Many2one('account.move', string="Pièce Comptable", readonly=True)
    partner_id = fields.Many2one('res.partner', string="Client", readonly=True)
    company_id = fields.Many2one('res.company', string="Société", readonly=True)
    currency_id = fields.Many2one('res.currency', string="Devise", readonly=True)

    line_type = fields.Selection([
        ('FACTURE', 'Facture'),
        ('AVANCE', 'Avance')
    ], string="Type", readonly=True)

    reference = fields.Char("Référence", readonly=True)
    client = fields.Char("Client (Nom)", readonly=True)
    date = fields.Date("Date", readonly=True)
    total_facture = fields.Monetary("Total Facture", currency_field='currency_id', readonly=True)
    avance = fields.Monetary("Avance", currency_field='currency_id', readonly=True)
    reste = fields.Monetary("Reste", currency_field='currency_id', readonly=True)
    statut = fields.Char("Statut", readonly=True)
    payment_mode = fields.Char("Mode de Règlement", readonly=True)
    check_number = fields.Char("N° Chèque / Effet", readonly=True)
    check_client_name = fields.Char("Émetteur Chèque", readonly=True)

    is_hidden = fields.Boolean("Masqué", default=False)

    def write(self, vals):
        if 'is_hidden' in vals:
            moves = self.env['account.move'].browse(self.ids)
            moves.write({'is_report_hidden': vals['is_hidden']})
        return True

    def action_toggle_hidden(self):
        """Bascule l'état masqué/visible pour les enregistrements sélectionnés."""
        for rec in self:
            move = self.env['account.move'].browse(rec.id)
            if move.exists():
                move.is_report_hidden = not move.is_report_hidden
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_hide_movements(self):
        """Action de masse : Masquer les mouvements sélectionnés."""
        moves = self.env['account.move'].browse(self.ids)
        moves.write({'is_report_hidden': True})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_unhide_movements(self):
        """Action de masse : Rendre visibles les mouvements sélectionnés."""
        moves = self.env['account.move'].browse(self.ids)
        moves.write({'is_report_hidden': False})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_open_move(self):
        """Ouvre la pièce comptable originale (facture ou écriture de paiement)."""
        self.ensure_one()
        return {
            'name': self.reference or 'Pièce Comptable',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW report_facture_avance AS (

                SELECT 
                    m.id AS id,
                    m.id AS move_id,
                    m.partner_id AS partner_id,
                    m.company_id AS company_id,
                    m.currency_id AS currency_id,
                    'FACTURE' AS line_type,
                    m.name AS reference,
                    rp.name AS client,
                    COALESCE(m.invoice_date, m.date) AS date,
                    COALESCE(m.amount_total, 0.0) AS total_facture,
                    0.0 AS avance,
                    COALESCE(m.amount_residual, 0.0) AS reste,
                    m.payment_state AS statut,
                    COALESCE(m.payment_mode, '') AS payment_mode,
                    COALESCE(m.check_number, '') AS check_number,
                    COALESCE(m.check_client_name, '') AS check_client_name,
                    COALESCE(m.is_report_hidden, FALSE) AS is_hidden
                FROM account_move m
                LEFT JOIN res_partner rp ON rp.id = m.partner_id
                WHERE m.move_type = 'out_invoice'
                  AND m.state = 'posted'

                UNION ALL

                SELECT
                    pm.id AS id,
                    pm.id AS move_id,
                    pm.partner_id AS partner_id,
                    pm.company_id AS company_id,
                    pm.currency_id AS currency_id,
                    'AVANCE' AS line_type,
                    pm.name AS reference,
                    rp.name AS client,
                    pm.date AS date,
                    0.0 AS total_facture,
                    COALESCE(p.amount, pm.amount_total, 0.0) AS avance,
                    0.0 AS reste,
                    'avance' AS statut,
                    COALESCE(p.payment_mode, pm.payment_mode, '') AS payment_mode,
                    COALESCE(p.check_number, pm.check_number, '') AS check_number,
                    COALESCE(p.check_client_name, pm.check_client_name, '') AS check_client_name,
                    COALESCE(pm.is_report_hidden, FALSE) AS is_hidden
                FROM account_move pm
                JOIN account_payment p ON p.move_id = pm.id
                LEFT JOIN res_partner rp ON rp.id = pm.partner_id
                WHERE pm.state = 'posted'
                  AND p.partner_type = 'customer'
                  AND p.payment_type = 'inbound'

            )
        """)
