# -*- coding: utf-8 -*-
import datetime
from odoo import fields, models, api
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT


class PosConfig(models.Model):
    _inherit = 'pos.config'

    omax_session_z_report = fields.Boolean(
        string='Session Z Report ',
        help='This will allow to print Session Z Report directly from POS screen',
        default=True
    )

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields_list = super()._load_pos_data_fields(config_id)
        if 'omax_session_z_report' not in fields_list:
            fields_list.append('omax_session_z_report')
        return fields_list


class ResConfigZreport(models.TransientModel):
    _inherit = 'res.config.settings'

    omax_session_z_report = fields.Boolean(related='pos_config_id.omax_session_z_report', readonly=False)


class PosSession(models.Model):
    _inherit = 'pos.session'
    
    def action_session_z_report(self):
        return self.env.ref('pos_session_z_report_omax.action_report_session_z').report_action(self)
    
    def get_current_datetime(self):
        current = fields.Datetime.now()
        return current.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        
    def get_opened_date(self):
        if self.start_at:
            return self.start_at.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return ''
        
    def get_closed_date(self):
        if self.stop_at:
            return self.stop_at.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return ''
        
    def get_session_amount_data(self):
        pos_order_ids = self.env['pos.order'].search([('session_id', '=', self.id), ('state', 'not in', ['draft', 'cancel'])])
        discount_amount = 0.0
        taxes_amount = 0.0
        total_sale_amount = 0.0
        total_gross_amount = 0.0
        sold_product = {}
        for pos_order in pos_order_ids:
            currency = pos_order.session_id.currency_id
            total_gross_amount += pos_order.amount_total
            for line in pos_order.lines:
                categ_name = line.product_id.pos_categ_ids[:1].name if line.product_id.pos_categ_ids else False
                if categ_name:
                    if categ_name in sold_product:
                        sold_product[categ_name] += line.qty
                    else:
                        sold_product.update({categ_name: line.qty})
                else:
                    if 'undefine' in sold_product:
                        sold_product['undefine'] += line.qty
                    else:
                        sold_product.update({'undefine': line.qty})
                if line.tax_ids_after_fiscal_position:
                    line_taxes = line.tax_ids_after_fiscal_position.compute_all(
                        line.price_unit * (1 - (line.discount or 0.0) / 100.0),
                        currency,
                        line.qty,
                        product=line.product_id,
                        partner=line.order_id.partner_id or False
                    )
                    for tax in line_taxes['taxes']:
                        taxes_amount += tax.get('amount', 0)
                if line.discount > 0:
                    discount_amount += (((line.price_unit * line.qty) * line.discount) / 100)
                if line.qty > 0:
                    total_sale_amount += line.price_unit * line.qty

        return {
            'total_sale': total_sale_amount,
            'discount': discount_amount,
            'tax': taxes_amount,
            'products_sold': sold_product,
            'total_gross': total_gross_amount - taxes_amount - discount_amount,
            'final_total': total_gross_amount
        }
    
    def get_taxes_data(self):
        order_ids = self.env['pos.order'].search([('session_id', '=', self.id), ('state', 'not in', ['draft', 'cancel'])])
        taxes = {}
        for order in order_ids:
            currency = order.pricelist_id.currency_id
            for line in order.lines:
                if line.tax_ids_after_fiscal_position:
                    for tax in line.tax_ids_after_fiscal_position:
                        discount_amount = 0
                        if line.discount > 0:
                            discount_amount = ((line.qty * line.price_unit) * line.discount) / 100
                        untaxed_amount = (line.qty * line.price_unit) - discount_amount
                        tax_amount = ((untaxed_amount * tax.amount) / 100)
                        if tax.name:
                            if tax.name in taxes:
                                taxes[tax.name] += tax_amount
                            else:
                                taxes.update({tax.name: tax_amount})
                        else:
                            if 'undefine' in taxes:
                                taxes['undefine'] += tax_amount
                            else:
                                taxes.update({'undefine': tax_amount})
        return taxes    
    
    def get_pricelist(self):
        pos_order_ids = self.env['pos.order'].search([('session_id', '=', self.id), ('state', 'not in', ['draft', 'cancel'])])
        pricelist = {}
        for pos_order in pos_order_ids:
            if pos_order.pricelist_id.name:
                if pos_order.pricelist_id.name in pricelist:
                    pricelist[pos_order.pricelist_id.name] += pos_order.amount_total
                else:
                    pricelist.update({pos_order.pricelist_id.name: pos_order.amount_total})
            else:
                if 'undefine' in pricelist:
                    pricelist['undefine'] += pos_order.amount_total
                else:
                    pricelist.update({'undefine': pos_order.amount_total})
        return pricelist
        
    def get_pricelist_qty(self, pricelist):
        if pricelist:
            qty_pricelist = 0
            pricelist_obj = self.env['product.pricelist'].search([('name', '=', str(pricelist))], limit=1)
            if pricelist_obj:
                pos_order_ids = self.env['pos.order'].search([('session_id', '=', self.id), ('state', 'not in', ['draft', 'cancel']), ('pricelist_id', '=', pricelist_obj.id)])
                qty_pricelist = len(pos_order_ids)
            else:
                if pricelist == 'undefine':
                    pos_order_ids = self.env['pos.order'].search([('session_id', '=', self.id), ('state', 'not in', ['draft', 'cancel']), ('pricelist_id', '=', False)])
                    qty_pricelist = len(pos_order_ids)
            return int(qty_pricelist)
        return 0
            
    def get_payment_data(self):
        pos_payments = self.env["pos.payment"].search([('session_id', '=', self.id)])
        payments = []
        methods = pos_payments.mapped('payment_method_id')
        for method in methods:
            method_payments = pos_payments.filtered(lambda p: p.payment_method_id == method)
            payments.append({
                'name': method.name,
                'total': sum(method_payments.mapped('amount'))
            })
        return payments
        
    def get_payment_qty(self, payment_method):
        if not payment_method:
            return 0
        pos_payments = self.env["pos.payment"].search([('session_id', '=', self.id)])
        matching = [p for p in pos_payments if p.payment_method_id.name == payment_method]
        return len(matching)
