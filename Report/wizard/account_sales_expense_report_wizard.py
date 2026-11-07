# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AccountSalesExpenseReportWizard(models.TransientModel):
    _name = 'account.sales.expense.report.wizard'
    _description = 'Assistant de Génération du Rapport Ventes et Dépenses'

    report_type = fields.Selection([
        ('x', 'Rapport X (Aperçu Provisoire en direct)'),
        ('z', 'Rapport Z (Clôture Journalière Officielle)')
    ], string='Type de Rapport', required=True, default='z',
       help="Rapport X pour consulter l'état en cours de journée sans figer. Rapport Z pour la clôture officielle du soir.")

    date_start = fields.Date(string='Date Début', required=True, default=fields.Date.context_today)
    date_end = fields.Date(string='Date Fin', required=True, default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', string='Société', required=True, default=lambda self: self.env.company)
    
    sale_journal_id = fields.Many2one('account.journal', string='Journal de Vente', domain="[('type', '=', 'sale')]",
                                     help="Laisser vide pour inclure tous les journaux de vente.")
    purchase_journal_id = fields.Many2one('account.journal', string='Journal d\'Achat/Charges', domain="[('type', '=', 'purchase')]",
                                         help="Laisser vide pour inclure tous les journaux d'achat et de charges.")
    salesperson_id = fields.Many2one('res.users', string='Commercial / Responsable')
    invoice_state = fields.Selection([
        ('posted', 'Factures comptabilisées uniquement'),
        ('paid', 'Factures payées uniquement')
    ], string='Filtrage des pièces', required=True, default='posted')

    def action_generate_report(self):
        """Crée l'enregistrement de rapport persistant et ouvre sa vue détaillée"""
        self.ensure_one()
        report = self.env['account.sales.expense.report'].create({
            'report_type': self.report_type,
            'date_start': self.date_start,
            'date_end': self.date_end,
            'company_id': self.company_id.id,
            'sale_journal_id': self.sale_journal_id.id if self.sale_journal_id else False,
            'purchase_journal_id': self.purchase_journal_id.id if self.purchase_journal_id else False,
            'salesperson_id': self.salesperson_id.id if self.salesperson_id else False,
            'invoice_state': self.invoice_state,
        })
        
        return {
            'name': _('Rapport Ventes et Dépenses : %s') % report.name,
            'type': 'ir.actions.act_window',
            'res_model': 'account.sales.expense.report',
            'res_id': report.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_print_pdf(self):
        """Génère le rapport et déclenche l'impression PDF immédiate"""
        self.ensure_one()
        report = self.env['account.sales.expense.report'].create({
            'report_type': self.report_type,
            'date_start': self.date_start,
            'date_end': self.date_end,
            'company_id': self.company_id.id,
            'sale_journal_id': self.sale_journal_id.id if self.sale_journal_id else False,
            'purchase_journal_id': self.purchase_journal_id.id if self.purchase_journal_id else False,
            'salesperson_id': self.salesperson_id.id if self.salesperson_id else False,
            'invoice_state': self.invoice_state,
        })
        return self.env.ref('Report.action_report_sales_expense_pdf').report_action(report)

    def action_export_excel(self):
        """Génère le rapport et retourne l'URL de téléchargement direct du fichier Excel"""
        self.ensure_one()
        report = self.env['account.sales.expense.report'].create({
            'report_type': self.report_type,
            'date_start': self.date_start,
            'date_end': self.date_end,
            'company_id': self.company_id.id,
            'sale_journal_id': self.sale_journal_id.id if self.sale_journal_id else False,
            'purchase_journal_id': self.purchase_journal_id.id if self.purchase_journal_id else False,
            'salesperson_id': self.salesperson_id.id if self.salesperson_id else False,
            'invoice_state': self.invoice_state,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model=account.sales.expense.report&id={report.id}&field=excel_file&download=true&filename={report.excel_filename}',
            'target': 'self',
        }

