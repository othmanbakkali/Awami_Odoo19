from odoo import models, fields, api

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    package_id = fields.Many2one('stock.package', string="Colis")
    package_photo = fields.Image(related='package_id.photo', readonly=True, string="Photo Colis")
    package_supplier_ref = fields.Char(related='package_id.supplier_ref', readonly=True, string="Réf Fournisseur Colis")
    package_name = fields.Char(related='package_id.name', readonly=True, string="Numéro Colis")
    package_product_ids = fields.Many2many('product.product', compute='_compute_package_product_ids', string="Produits du Colis")
    qty_available_colis = fields.Float(string="Qté Colis", compute='_compute_qty_available_colis')

    @api.depends('package_id', 'package_id.colis_line_ids.product_id', 'package_id.quant_ids.product_id')
    def _compute_package_product_ids(self):
        for line in self:
            if line.package_id:
                products = line.package_id.colis_line_ids.mapped('product_id') | line.package_id.quant_ids.mapped('product_id')
                line.package_product_ids = products
            else:
                line.package_product_ids = self.env['product.product'].search([])

    @api.depends('package_id', 'product_id', 'package_id.colis_line_ids.qty_available')
    def _compute_qty_available_colis(self):
        for line in self:
            if line.package_id and line.product_id:
                colis_lines = line.package_id.colis_line_ids.filtered(lambda l: l.product_id == line.product_id)
                line.qty_available_colis = sum(colis_lines.mapped('qty_available'))
            else:
                line.qty_available_colis = 0.0

    @api.onchange('package_id')
    def _onchange_package_id(self):
        if self.package_id:
            products = self.package_id.colis_line_ids.mapped('product_id') | self.package_id.quant_ids.mapped('product_id')
            return {'domain': {'product_id': [('id', 'in', products.ids)]}}
        else:
            return {'domain': {'product_id': []}}
