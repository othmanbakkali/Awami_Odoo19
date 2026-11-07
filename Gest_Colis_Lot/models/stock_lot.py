from odoo import models, fields

class StockLot(models.Model):
    _inherit = 'stock.lot'

    nb_pieces = fields.Integer(string='Nombre de pièces')
    longueur = fields.Char(string='Longueur')
    quantite_uv = fields.Float(string='Quantité UV')
    photo_lot = fields.Image(string='Photo du Lot', max_width=1024, max_height=1024)
