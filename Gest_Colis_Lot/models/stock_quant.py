from odoo import models, fields, api

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def _gather(self, product_id, location_id, lot_id=None, package_id=None, owner_id=None, strict=False, *args, **kwargs):
        reserve_package_id = self._context.get('reserve_package_id')
        if reserve_package_id and not package_id:
            package_id = self.env['stock.package'].browse(reserve_package_id)
        return super()._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict, *args, **kwargs)
