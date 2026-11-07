from odoo import models, fields, api

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    package_id = fields.Many2one('stock.package', string="Colis")
    package_photo = fields.Image(related='package_id.photo', readonly=False, string="Photo du colis")
    package_supplier_ref = fields.Char(related='package_id.supplier_ref', readonly=False, string="Référence Fournisseur")
    package_name = fields.Char(related='package_id.name', readonly=True, string="Numéro du colis")
    longueur_totale = fields.Char(
        string='Résultat',
        compute='_compute_longueur_totale'
    )

    @api.depends('product_qty', 'product_id', 'product_id.uom_id')
    def _compute_longueur_totale(self):
        import re
        for line in self:
            uom = getattr(line, 'product_uom_id', None) or getattr(line, 'product_uom', None) or line.product_id.uom_id
            uom_name = uom.name if uom else ""
            if uom_name and line.product_qty:
                match = re.search(r"[-+]?\d*\.\d+|\d+", uom_name)
                if match:
                    try:
                        val = float(match.group())
                        total = line.product_qty * val
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

    def _prepare_stock_move_vals(self, *args, **kwargs):
        vals = super()._prepare_stock_move_vals(*args, **kwargs)
        if self.package_id:
            vals['package_id'] = self.package_id.id
        return vals

    def _prepare_invoice_line(self, *args, **kwargs):
        vals = super()._prepare_invoice_line(*args, **kwargs)
        if self.package_id:
            vals['package_id'] = self.package_id.id
        return vals


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        res = super().button_confirm()
        for order in self:
            for line in order.order_line:
                if line.package_id and line.product_id:
                    package = line.package_id
                    colis_line = package.colis_line_ids.filtered(lambda l: l.product_id == line.product_id)
                    if colis_line:
                        colis_line.qty_package += line.product_qty
                    else:
                        self.env['stock.package.line'].create({
                            'package_id': package.id,
                            'product_id': line.product_id.id,
                            'qty_package': line.product_qty,
                            'product_uom_id': (getattr(line, 'product_uom_id', None) or getattr(line, 'product_uom', None) or line.product_id.uom_id).id,
                        })
        return res

