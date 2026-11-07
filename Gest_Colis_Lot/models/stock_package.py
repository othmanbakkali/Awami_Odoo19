from odoo import models, fields, api

class StockPackage(models.Model):
    _inherit = 'stock.package'

    photo = fields.Image(string="Photo du colis", max_width=512, max_height=512)
    designation = fields.Char(string="Désignation du colis")
    date_creation = fields.Date(string="Date de création", default=fields.Date.today, required=True)
    state = fields.Selection([
        ('available', 'Disponible'),
        ('partially_sold', 'Partiellement vendu'),
        ('sold', 'Vendu'),
        ('cancelled', 'Annulé')
    ], string="État du colis", default='available', compute='_compute_state', store=True, readonly=False)
    observations = fields.Text(string="Observations")
    supplier_ref = fields.Char(string="Référence Fournisseur")
    colis_line_ids = fields.One2many('stock.package.line', 'package_id', string="Composition du colis")

    @api.depends('colis_line_ids.qty_available', 'colis_line_ids.qty_package', 'colis_line_ids.qty_sold')
    def _compute_state(self):
        for package in self:
            if package.state == 'cancelled':
                continue
            if not package.colis_line_ids:
                package.state = 'available'
                continue
            
            total_sold = sum(line.qty_sold for line in package.colis_line_ids)
            all_zero = all(line.qty_available == 0 for line in package.colis_line_ids)
            
            if total_sold == 0:
                package.state = 'available'
            elif all_zero:
                package.state = 'sold'
            else:
                package.state = 'partially_sold'

    def action_sync_physical_content(self):
        for package in self:
            move_lines = self.env['stock.move.line'].search([
                ('move_id.package_id', '=', package.id),
                ('state', '=', 'done'),
                ('result_package_id', '=', False)
            ])
            po_move_lines = self.env['stock.move.line'].search([
                ('move_id.purchase_line_id.package_id', '=', package.id),
                ('state', '=', 'done'),
                ('result_package_id', '=', False)
            ])
            all_lines = move_lines | po_move_lines
            
            for line in all_lines:
                line.result_package_id = package.id
                
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', line.location_dest_id.id),
                    ('package_id', '=', False)
                ])
                
                qty_to_assign = getattr(line, 'quantity', None) or getattr(line, 'qty_done', 0.0)
                for quant in quants:
                    if qty_to_assign <= 0:
                        break
                    if quant.quantity <= qty_to_assign:
                        quant.package_id = package.id
                        qty_to_assign -= quant.quantity
                    else:
                        self.env['stock.quant'].create({
                            'product_id': quant.product_id.id,
                            'location_id': quant.location_id.id,
                            'package_id': package.id,
                            'quantity': qty_to_assign,
                        })
                        quant.quantity -= qty_to_assign
                        qty_to_assign = 0
            
            package._compute_state()


class StockPackageLine(models.Model):
    _name = 'stock.package.line'
    _description = 'Ligne de composition du colis'

    package_id = fields.Many2one('stock.package', string="Colis", ondelete='cascade', required=True)
    product_id = fields.Many2one('product.product', string="Produit", required=True)
    qty_package = fields.Float(string="Quantité Initiale", required=True, default=1.0)
    product_uom_id = fields.Many2one('uom.uom', string="Unité de mesure", required=True)
    dimensions = fields.Char(string="Dimensions / Métrage")
    qty_sold = fields.Float(string="Quantité Vendue", compute='_compute_qty_sold')
    qty_available = fields.Float(string="Quantité Actuelle", compute='_compute_qty_available')

    @api.depends('package_id', 'product_id')
    def _compute_qty_sold(self):
        for line in self:
            sale_lines = self.env['sale.order.line'].search([
                ('package_id', '=', line.package_id.id),
                ('product_id', '=', line.product_id.id),
                ('state', 'in', ['sale', 'done'])
            ])
            line.qty_sold = sum(sale_lines.mapped('product_uom_qty'))

    @api.depends('qty_package', 'qty_sold')
    def _compute_qty_available(self):
        for line in self:
            line.qty_available = max(0.0, line.qty_package - line.qty_sold)
