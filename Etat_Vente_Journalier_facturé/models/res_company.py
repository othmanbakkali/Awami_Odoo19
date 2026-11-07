# -*- coding: utf-8 -*-
from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    ice = fields.Char(string='ICE', help='Identifiant Commun de l\'Entreprise (Maroc)')
    company_if = fields.Char(string='IF', help='Identifiant Fiscal (Maroc)')
    rc = fields.Char(string='RC', help='Registre du Commerce (Maroc)')
