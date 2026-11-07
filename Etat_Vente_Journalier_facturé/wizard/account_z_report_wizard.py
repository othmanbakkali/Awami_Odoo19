# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountZReportWizard(models.TransientModel):
    _name = 'account.z.report.wizard'
    _description = 'Assistant de Rapport Z Journalier'

    date_start = fields.Date(
        string='Date Début', 
        required=True, 
        default=fields.Date.context_today
    )
    date_end = fields.Date(
        string='Date Fin', 
        required=True, 
        default=fields.Date.context_today
    )
    company_id = fields.Many2one(
        'res.company', 
        string='Société', 
        required=True, 
        default=lambda self: self.env.company
    )
    journal_id = fields.Many2one(
        'account.journal', 
        string='Journal de vente', 
        domain="[('type', '=', 'sale'), ('company_id', '=', company_id)]"
    )
    salesperson_id = fields.Many2one(
        'res.users', 
        string='Commercial'
    )
    report_type = fields.Selection([
        ('x', 'Rapport X (Aperçu)'),
        ('z', 'Rapport Z (Clôture)')
    ], string='Type de Rapport', required=True, default='z')
    
    invoice_state = fields.Selection([
        ('posted', 'Factures comptabilisées'),
        ('paid', 'Factures payées uniquement')
    ], string='État', required=True, default='posted')

    @api.onchange('date_start')
    def _onchange_date_start(self):
        if self.date_start and self.date_end and self.date_start > self.date_end:
            self.date_end = self.date_start

    @api.onchange('date_end')
    def _onchange_date_end(self):
        if self.date_start and self.date_end and self.date_start > self.date_end:
            self.date_start = self.date_end

    def action_generate_report(self):
        self.ensure_one()
        if self.date_start > self.date_end:
            raise UserError(_("La date de début ne peut pas être supérieure à la date de fin."))

        # 1. Create the historical Z-report record
        z_report = self.env['account.z.report'].create({
            'report_type': self.report_type,
            'date_start': self.date_start,
            'date_end': self.date_end,
            'company_id': self.company_id.id,
            'journal_id': self.journal_id.id if self.journal_id else False,
            'salesperson_id': self.salesperson_id.id if self.salesperson_id else False,
            'invoice_state': self.invoice_state,
        })

        # 2. Compute snapshot figures and save attachments (Excel, CSV, PDF)
        z_report.generate_snapshot_data()

        # 3. Open the newly created Z-report form view
        return {
            'name': _('Rapport Généré'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.z.report',
            'res_id': z_report.id,
            'view_mode': 'form',
            'target': 'current',
        }
