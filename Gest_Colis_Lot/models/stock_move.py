from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StockMove(models.Model):
    _inherit = 'stock.move'

    package_id = fields.Many2one('stock.package', string="Colis")
    package_photo = fields.Image(related='package_id.photo', readonly=True, string="Photo du colis")
    package_supplier_ref = fields.Char(related='package_id.supplier_ref', readonly=True, string="Référence Fournisseur")
    package_name = fields.Char(related='package_id.name', readonly=True, string="Numéro du colis")
    qty_available_colis = fields.Float(string="Qté Disponible Colis", compute='_compute_qty_available_colis')

    @api.depends('package_id', 'product_id', 'package_id.colis_line_ids.qty_available')
    def _compute_qty_available_colis(self):
        for move in self:
            if move.package_id and move.product_id:
                colis_lines = move.package_id.colis_line_ids.filtered(lambda l: l.product_id == move.product_id)
                move.qty_available_colis = sum(colis_lines.mapped('qty_available'))
            else:
                move.qty_available_colis = 0.0

    @api.onchange('package_id')
    def _onchange_package_id(self):
        for move in self:
            if move.package_id:
                move.result_package_id = move.package_id
                for line in move.move_line_ids:
                    if move.picking_type_id.code == 'incoming':
                        line.result_package_id = move.package_id
                    elif move.picking_type_id.code == 'outgoing':
                        line.package_id = move.package_id

    @api.onchange('result_package_id')
    def _onchange_result_package_id(self):
        for move in self:
            if move.result_package_id:
                move.package_id = move.result_package_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'result_package_id' in vals:
                if not vals.get('package_id'):
                    vals['package_id'] = vals['result_package_id']
                vals.pop('result_package_id')
        
        moves = super().create(vals_list)
        for move in moves:
            if move.package_id:
                for line in move.move_line_ids:
                    if move.picking_type_id.code == 'incoming':
                        line.result_package_id = move.package_id
                    elif move.picking_type_id.code == 'outgoing':
                        line.package_id = move.package_id
        return moves

    def write(self, vals):
        if 'result_package_id' in vals:
            if 'package_id' not in vals:
                vals['package_id'] = vals['result_package_id']
            vals.pop('result_package_id')
            
        res = super().write(vals)
        if 'package_id' in vals:
            for move in self:
                if move.package_id:
                    for line in move.move_line_ids:
                        if move.picking_type_id.code == 'incoming':
                            line.result_package_id = move.package_id
                        elif move.picking_type_id.code == 'outgoing':
                            line.package_id = move.package_id
        return res

    def _action_assign(self, *args, **kwargs):
        moves_with_package = self.filtered(lambda m: m.package_id)
        moves_without_package = self - moves_with_package
        
        if moves_without_package:
            super(StockMove, moves_without_package)._action_assign(*args, **kwargs)
            
        for move in moves_with_package:
            super(StockMove, move.with_context(reserve_package_id=move.package_id.id))._action_assign(*args, **kwargs)

    def _prepare_move_line_vals(self, *args, **kwargs):
        vals = super()._prepare_move_line_vals(*args, **kwargs)
        if self.package_id:
            if self.picking_type_id.code == 'incoming':
                vals['result_package_id'] = self.package_id.id
            elif self.picking_type_id.code == 'outgoing':
                vals['package_id'] = self.package_id.id
        return vals

    def _action_done(self, *args, **kwargs):
        res = super()._action_done(*args, **kwargs)
        for move in self:
            if move.state == 'done' and move.package_id:
                if move.picking_type_id.code == 'incoming':
                    if move.purchase_line_id:
                        continue
                    package = move.package_id
                    line = package.colis_line_ids.filtered(lambda l: l.product_id == move.product_id)
                    if line:
                        line.qty_package += move.product_uom_qty
                    else:
                        self.env['stock.package.line'].create({
                            'package_id': package.id,
                            'product_id': move.product_id.id,
                            'qty_package': move.product_uom_qty,
                            'product_uom_id': move.product_uom.id,
                        })
        return res


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    package_id = fields.Many2one('stock.package', string="Colis de la réception")
    package_photo = fields.Image(related='package_id.photo', readonly=False, string="Photo du colis")
    package_supplier_ref = fields.Char(related='package_id.supplier_ref', readonly=False, string="Référence Fournisseur")
    package_designation = fields.Char(related='package_id.designation', readonly=False, string="Désignation du colis")

    @api.onchange('package_id')
    def _onchange_package_id(self):
        if self.package_id:
            for move in self.move_ids:
                move.package_id = self.package_id

    def button_validate(self):
        for picking in self:
            for move in picking.move_ids:
                if move.package_id:
                    for line in move.move_line_ids:
                        if picking.picking_type_id.code == 'incoming':
                            line.result_package_id = move.package_id
                        elif picking.picking_type_id.code == 'outgoing':
                            line.package_id = move.package_id
        return super().button_validate()
