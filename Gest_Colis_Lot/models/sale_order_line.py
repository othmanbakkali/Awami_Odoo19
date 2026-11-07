import logging
_logger = logging.getLogger(__name__)

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.osv import expression

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    lot_id = fields.Many2one(
        'stock.lot', 
        string='Lot',
        domain="[('product_id', '=', product_id)]"
    )
    nb_pieces = fields.Integer(
        string='Pièces',
        related='lot_id.nb_pieces',
        readonly=True,
        store=True
    )
    longueur = fields.Char(
        string='Longueur',
        related='lot_id.longueur',
        readonly=True,
        store=True
    )
    longueur_totale = fields.Char(
        string='Longueur Totale',
        compute='_compute_longueur_totale'
    )
    quantite_uv = fields.Float(
        string='Qté UV',
        related='lot_id.quantite_uv',
        readonly=True,
        store=True
    )

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
                _logger.info("Gest_Colis_Lot: Colis %s -> Produits trouves: %s", line.package_id.name, products.mapped('display_name'))
                line.package_product_ids = products
            else:
                line.package_product_ids = self.env['product.product'].search([('sale_ok', '=', True)])

    @api.depends('package_id', 'product_id', 'package_id.colis_line_ids.qty_available')
    def _compute_qty_available_colis(self):
        for line in self:
            if line.package_id and line.product_id:
                colis_lines = line.package_id.colis_line_ids.filtered(lambda l: l.product_id == line.product_id)
                line.qty_available_colis = sum(colis_lines.mapped('qty_available'))
            else:
                line.qty_available_colis = 0.0

    @api.depends('product_uom_qty', 'longueur')
    def _compute_longueur_totale(self):
        import re
        for line in self:
            if line.longueur and line.product_uom_qty:
                # Extraire le premier nombre décimal ou entier
                match = re.search(r"[-+]?\d*\.\d+|\d+", line.longueur)
                if match:
                    try:
                        val = float(match.group())
                        total = line.product_uom_qty * val
                        if total.is_integer():
                            line.longueur_totale = f"{int(total)} ML"
                        else:
                            line.longueur_totale = f"{total:.2f} ML"
                    except ValueError:
                        line.longueur_totale = ""
                else:
                    line.longueur_totale = ""
            else:
                line.longueur_totale = ""

    @api.constrains('package_id', 'product_id', 'product_uom_qty')
    def _check_package_sale_constraints(self):
        for line in self:
            if line.package_id and line.product_id:
                colis_lines = line.package_id.colis_line_ids.filtered(lambda l: l.product_id == line.product_id)
                if not colis_lines:
                    raise ValidationError(
                        f"Le produit {line.product_id.display_name} ne fait pas partie du colis {line.package_id.name}."
                    )
                
                # Récupérer la quantité actuelle restante dans le colis
                available_qty = sum(colis_lines.mapped('qty_available'))
                
                # Si la ligne est déjà validée, sa quantité fait déjà partie de la quantité vendue,
                # on la rajoute temporairement pour le contrôle.
                if line.state in ['sale', 'done']:
                    available_qty += line.product_uom_qty

                if line.product_uom_qty > available_qty:
                    raise ValidationError(
                        f"La quantité demandée ({line.product_uom_qty}) dépasse la quantité actuelle disponible "
                        f"({available_qty}) pour le produit {line.product_id.display_name} dans le colis {line.package_id.name}."
                    )

    def _prepare_procurement_values(self, *args, **kwargs):
        values = super()._prepare_procurement_values(*args, **kwargs)
        if self.package_id:
            values['package_id'] = self.package_id.id
        return values

    def _prepare_invoice_line(self, *args, **kwargs):
        vals = super()._prepare_invoice_line(*args, **kwargs)
        if self.package_id:
            vals['package_id'] = self.package_id.id
        return vals

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        if self.lot_id and self.lot_id.quantite_uv:
            # Optionally, you can set the quantity of the order line based on the lot's UV
            # self.product_uom_qty = self.lot_id.quantite_uv
            pass

    @api.onchange('package_id')
    def _onchange_package_id(self):
        if self.package_id:
            products = self.package_id.colis_line_ids.mapped('product_id') | self.package_id.quant_ids.mapped('product_id')
            return {'domain': {'product_id': [('sale_ok', '=', True), ('id', 'in', products.ids)]}}
        else:
            return {'domain': {'product_id': [('sale_ok', '=', True)]}}


    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        packages = lines.mapped('package_id')
        if packages:
            packages.colis_line_ids.invalidate_recordset(['qty_sold', 'qty_available'])
            packages.invalidate_recordset(['state'])
            packages._compute_state()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if any(key in vals for key in ['package_id', 'product_id', 'product_uom_qty', 'state']):
            packages = self.mapped('package_id')
            if packages:
                packages.colis_line_ids.invalidate_recordset(['qty_sold', 'qty_available'])
                packages.invalidate_recordset(['state'])
                packages._compute_state()
        return res

    def unlink(self):
        packages = self.mapped('package_id')
        res = super().unlink()
        if packages:
            packages.colis_line_ids.invalidate_recordset(['qty_sold', 'qty_available'])
            packages.invalidate_recordset(['state'])
            packages._compute_state()
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super().action_confirm()
        packages = self.order_line.mapped('package_id')
        if packages:
            packages.colis_line_ids.invalidate_recordset(['qty_sold', 'qty_available'])
            packages.invalidate_recordset(['state'])
            packages._compute_state()
        return res

    def action_cancel(self):
        res = super().action_cancel()
        packages = self.order_line.mapped('package_id')
        if packages:
            packages.colis_line_ids.invalidate_recordset(['qty_sold', 'qty_available'])
            packages.invalidate_recordset(['state'])
            packages._compute_state()
        return res
