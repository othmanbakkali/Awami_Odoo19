# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    payment_mode = fields.Selection([
        ('virement', 'Virement bancaire'),
        ('cheque', 'Chèque'),
        ('effet', 'Effet'),
        ('traite', 'Effet / Traite'),
        ('effet_cheque', 'Effet / Chèque'),
        ('especes', 'Espèces'),
    ], string="Mode de règlement", default='virement', tracking=True)

    check_number = fields.Char(
        string="N° de série / Chèque / Effet",
        tracking=True,
        copy=False,
        help="Numéro de série du chèque ou de l'effet commercial (Traite/LCN)."
    )

    check_client_name = fields.Char(
        string="Nom du client (Chèque / Effet)",
        tracking=True,
        copy=False,
        help="Nom du client ou titulaire figurant sur le chèque ou l'effet."
    )

    check_date_due = fields.Date(
        string="Date d'échéance",
        tracking=True,
        copy=False,
        help="Date d'échéance de l'effet ou date d'encaissement prévue du chèque."
    )

    @api.onchange('partner_id')
    def _onchange_partner_id_check_client(self):
        if self.partner_id and not self.check_client_name:
            self.check_client_name = self.partner_id.name

    @api.onchange('payment_mode')
    def _onchange_payment_mode_check(self):
        if self.payment_mode in ('cheque', 'effet', 'traite', 'effet_cheque'):
            if self.partner_id and not self.check_client_name:
                self.check_client_name = self.partner_id.name

    # Les informations de chèque / effet sont saisies au niveau du Paiement


    has_m3_lines = fields.Boolean(compute='_compute_has_m3_lines')

    @api.depends('order_line.is_m3', 'order_line.volume_m3')
    def _compute_has_m3_lines(self):
        for order in self:
            order.has_m3_lines = any(line.is_m3 or line.volume_m3 > 0 for line in order.order_line)

    manual_amount_total = fields.Monetary(
        string="Montant Total Souhaité",
        currency_field='currency_id',
        copy=False,
        tracking=True,
        help="Saisissez ici le montant total TTC souhaité pour le Bon Magasin. Le système ajoutera ou ajustera automatiquement une ligne de remise/ajustement."
    )

    @api.onchange('manual_amount_total')
    def _onchange_manual_amount_total(self):
        if self.state in ('draft', 'sent'):
            self._apply_manual_amount_total()

    def action_apply_manual_amount_total(self):
        for order in self:
            if order.state in ('draft', 'sent'):
                order._apply_manual_amount_total()

    def _apply_manual_amount_total(self):
        self.ensure_one()
        if not self.manual_amount_total or self.manual_amount_total <= 0:
            adj_lines = self.order_line.filtered(lambda l: l.is_adjustment_line)
            if adj_lines:
                self.order_line -= adj_lines
            return

        non_adj_lines = self.order_line.filtered(lambda l: not l.is_adjustment_line and not l.display_type)
        if not non_adj_lines:
            return

        current_total = sum(l.price_total for l in non_adj_lines)
        diff_total = self.manual_amount_total - current_total

        if abs(diff_total) < 0.005:
            adj_lines = self.order_line.filtered(lambda l: l.is_adjustment_line)
            if adj_lines:
                self.order_line -= adj_lines
            return

        taxes = non_adj_lines[:1].tax_ids if non_adj_lines else False
        if taxes:
            res = taxes.compute_all(diff_total, currency=self.currency_id, quantity=1.0, handle_price_include=True)
            price_unit_net = res['total_excluded']
        else:
            price_unit_net = diff_total

        label = "Remise commerciale" if diff_total < 0 else "Ajustement global"
        existing_adj = self.order_line.filtered(lambda l: l.is_adjustment_line)

        if existing_adj:
            existing_adj[:1].write({
                'name': label,
                'price_unit': price_unit_net,
                'tax_ids': [fields.Command.set(taxes.ids)] if taxes else False,
            })
            if len(existing_adj) > 1:
                self.order_line -= existing_adj[1:]
        else:
            self.order_line = [fields.Command.create({
                'name': label,
                'product_uom_qty': 1.0,
                'price_unit': price_unit_net,
                'tax_ids': [fields.Command.set(taxes.ids)] if taxes else False,
                'is_adjustment_line': True,
            })]

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        if self.payment_mode:
            invoice_vals['payment_mode'] = self.payment_mode
        if self.check_number:
            invoice_vals['check_number'] = self.check_number
        if self.check_client_name:
            invoice_vals['check_client_name'] = self.check_client_name
        if self.check_date_due:
            invoice_vals['check_date_due'] = self.check_date_due
        if self.manual_amount_total:
            invoice_vals['manual_amount_total'] = self.manual_amount_total
        return invoice_vals


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Suppression du domaine restrictif
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string="Unit",
        domain="[]",
        compute='_compute_product_uom_id',
        store=True,
        readonly=False,
        precompute=True,
        ondelete='restrict'
    )

    # Colonne Prix Unitaire de Base (modifiable librement par l'utilisateur)
    base_price_unit = fields.Float(
        string="P.U Base",
        digits='Product Price',
        compute='_compute_base_price_unit',
        store=True,
        readonly=False,
        precompute=True,
        copy=True,
        help="Prix unitaire de référence (ex: prix au ml ou prix au m³). Utilisé comme base pour tous les calculs."
    )

    # Sauvegarde du prix unitaire manuel personnalisé
    custom_price_unit = fields.Float(string="Prix Unitaire Manuel", digits='Product Price', copy=True)

    is_adjustment_line = fields.Boolean(string="Ligne d'ajustement / remise", default=False, copy=False)
    is_m3 = fields.Boolean(string="Article en m³", compute="_compute_is_m3", store=True)
    wood_length = fields.Float(string="Long. (m)", digits=(12, 5), default=0.0)
    wood_width = fields.Float(string="Larg. (m)", digits=(12, 5), default=0.0)
    wood_thickness = fields.Float(string="Épais. (m)", digits=(12, 5), default=0.0)
    wood_pieces = fields.Float(string="Nb Pièces", digits=(12, 0), default=1.0)
    volume_m3 = fields.Float(string="Vol. (m³)", digits=(12, 5), compute="_compute_volume_m3", store=True)

    @api.depends('product_id', 'product_uom_id')
    def _compute_is_m3(self):
        for line in self:
            uom_name = (line.product_uom_id.name or line.product_id.uom_id.name or '').lower()
            prod_name = (line.product_id.name or '').lower()
            line.is_m3 = ('m³' in uom_name or 'm3' in uom_name or 'cube' in uom_name or 'm³' in prod_name or 'm3' in prod_name)

    @api.depends('product_id')
    def _compute_base_price_unit(self):
        """Calculer ou initialiser le prix de base à partir de l'article"""
        for line in self:
            if not line.product_id or line.display_type:
                line.base_price_unit = 0.0
            elif not line.base_price_unit:
                base_price = line.product_id.lst_price
                if line.order_id.pricelist_id:
                    try:
                        base_price = line.order_id.pricelist_id._get_product_price(
                            line.product_id, line.product_uom_qty or 1.0, uom=line.product_id.uom_id
                        )
                    except Exception:
                        base_price = line.product_id.lst_price
                line.base_price_unit = base_price

    def _get_uom_ratio(self, base_uom, target_uom):
        """Calculer le ratio multiplicateur entre l'unité de base et l'unité choisie (ex: 4.2 ml -> 4.2)"""
        if not base_uom or not target_uom or base_uom == target_uom:
            return 1.0
        try:
            return base_uom._compute_price(1.0, to_unit=target_uom)
        except Exception:
            pass
        if hasattr(target_uom, 'factor') and hasattr(base_uom, 'factor') and base_uom.factor:
            return target_uom.factor / base_uom.factor
        if hasattr(target_uom, 'relative_factor'):
            return target_uom.relative_factor
        return 1.0

    @api.depends('base_price_unit', 'product_uom_id')
    def _compute_price_unit(self):
        """Prendre en compte le Prix Unitaire de Base dans le calcul du prix unitaire de la ligne"""
        super()._compute_price_unit()
        for line in self:
            if line.is_adjustment_line or not line.product_id or line.display_type:
                continue
            if line.base_price_unit:
                base_uom = line.product_id.uom_id
                if line.is_m3 or line.wood_length:
                    line.price_unit = line.base_price_unit
                elif base_uom and line.product_uom_id:
                    ratio = line._get_uom_ratio(base_uom, line.product_uom_id)
                    line.price_unit = line.base_price_unit * ratio
                else:
                    line.price_unit = line.base_price_unit
                line.technical_price_unit = line.price_unit
            elif line.custom_price_unit:
                line.price_unit = line.custom_price_unit
                line.technical_price_unit = line.price_unit

    @api.onchange('product_id')
    def _onchange_product_id_set_base_price(self):
        """Initialiser le prix unitaire de base lors du choix de l'article"""
        for line in self:
            if line.product_id:
                base_price = line.product_id.lst_price
                if line.order_id.pricelist_id:
                    try:
                        base_price = line.order_id.pricelist_id._get_product_price(
                            line.product_id, line.product_uom_qty or 1.0, uom=line.product_id.uom_id
                        )
                    except Exception:
                        base_price = line.product_id.lst_price
                line.base_price_unit = base_price
                base_uom = line.product_id.uom_id
                if line.is_m3 or line.wood_length:
                    line.price_unit = base_price
                elif base_uom and line.product_uom_id:
                    ratio = line._get_uom_ratio(base_uom, line.product_uom_id)
                    line.price_unit = base_price * ratio
                else:
                    line.price_unit = base_price
                line.custom_price_unit = line.price_unit
                line.technical_price_unit = line.price_unit

    @api.depends('wood_length', 'wood_width', 'wood_thickness')
    def _compute_volume_m3(self):
        for line in self:
            if line.wood_length and line.wood_width and line.wood_thickness:
                line.volume_m3 = round(line.wood_length * line.wood_width * line.wood_thickness, 5)
            else:
                line.volume_m3 = 0.0

    @api.onchange('base_price_unit')
    def _onchange_base_price_unit(self):
        """Prendre en compte le nouveau Prix Unitaire de Base dans tous les calculs"""
        for line in self:
            if line.base_price_unit is not False:
                base_uom = line.product_id.uom_id if line.product_id else False
                if line.is_m3 or line.wood_length:
                    # En mètre cube ou dimensions bois, le prix unitaire est le prix de base
                    line.price_unit = line.base_price_unit
                elif base_uom and line.product_uom_id:
                    # Conversion selon le ratio de l'unité choisie (ex: 4.2 ml = base * 4.2)
                    ratio = line._get_uom_ratio(base_uom, line.product_uom_id)
                    line.price_unit = line.base_price_unit * ratio
                else:
                    line.price_unit = line.base_price_unit
                line.custom_price_unit = line.price_unit
                line.technical_price_unit = line.price_unit

    @api.onchange('price_unit')
    def _onchange_price_unit_manual(self):
        """Synchronisation bidirectionnelle si l'utilisateur modifie directement le prix unitaire"""
        for line in self:
            if line.price_unit is not False:
                line.custom_price_unit = line.price_unit
                line.technical_price_unit = line.price_unit
                base_uom = line.product_id.uom_id if line.product_id else False
                if line.is_m3 or line.wood_length:
                    line.base_price_unit = line.price_unit
                elif base_uom and line.product_uom_id:
                    ratio = line._get_uom_ratio(base_uom, line.product_uom_id)
                    if ratio:
                        line.base_price_unit = line.price_unit / ratio
                else:
                    line.base_price_unit = line.price_unit

    @api.onchange('wood_length', 'wood_width', 'wood_thickness')
    def _onchange_wood_dimensions(self):
        """Calcul automatique du volume en m3 avec le prix unitaire de base"""
        for line in self:
            if line.wood_length and line.wood_width and line.wood_thickness:
                vol = round(line.wood_length * line.wood_width * line.wood_thickness, 5)
                line.volume_m3 = vol
                line.product_uom_qty = vol
                if line.base_price_unit:
                    line.price_unit = line.base_price_unit
                    line.technical_price_unit = line.base_price_unit
                    line.custom_price_unit = line.base_price_unit

    @api.onchange('product_uom_id')
    def _onchange_product_uom_id_convert_price(self):
        """Recalcul du prix unitaire à base du Prix Unitaire de Base lors du changement d'unité"""
        for line in self:
            if not line.product_id or not line.product_uom_id:
                continue
            base_uom = line.product_id.uom_id
            ref_price = line.base_price_unit or line.custom_price_unit or line.product_id.lst_price
            if line.is_m3 or line.wood_length:
                line.price_unit = ref_price
            elif base_uom and line.product_uom_id:
                ratio = line._get_uom_ratio(base_uom, line.product_uom_id)
                line.price_unit = ref_price * ratio
            else:
                line.price_unit = ref_price
            line.custom_price_unit = line.price_unit
            line.technical_price_unit = line.price_unit

    def _prepare_invoice_line(self, **optional_values):
        """Transmettre le Prix Unitaire de Base et les dimensions à la facture"""
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        if self.is_adjustment_line:
            res['is_adjustment_line'] = True
            res['name'] = self.name
        if self.product_uom_id:
            res['product_uom_id'] = self.product_uom_id.id
            res['quantity'] = self.qty_to_invoice
            res['price_unit'] = self.price_unit
            res['custom_price_unit'] = self.price_unit
        if self.base_price_unit:
            res['base_price_unit'] = self.base_price_unit
        if self.wood_length and self.wood_width and self.wood_thickness:
            res['wood_length'] = self.wood_length
            res['wood_width'] = self.wood_width
            res['wood_thickness'] = self.wood_thickness
            res['wood_pieces'] = self.wood_pieces
            res['volume_m3'] = self.volume_m3
        return res
