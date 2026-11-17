# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResUsersRoleLine(models.Model):
    _name = 'res.users.role.line'
    _description = "Ligne de Droit d'Accès par Modèle"
    _order = 'sequence asc, id asc'

    role_id = fields.Many2one(
        'res.users.role',
        string="Rôle",
        ondelete='cascade',
        required=True
    )

    sequence = fields.Integer(string="Séquence", default=10)

    name = fields.Char(
        string="Entité / Fonctionnalité",
        required=True,
        help="Nom lisible de l'entité (ex: Factures Clients, Bons de Commande, Paiements, etc.)"
    )

    model_id = fields.Many2one(
        'ir.model',
        string="Modèle Odoo",
        required=True,
        ondelete='cascade',
        help="Modèle technique Odoo sur lequel s'appliquent les droits."
    )

    model_name = fields.Char(
        string="Code Modèle",
        related='model_id.model',
        readonly=True,
        store=True
    )

    perm_read = fields.Boolean(
        string="Lecture",
        default=True,
        help="Autorise la consultation et l'affichage des enregistrements."
    )

    perm_create = fields.Boolean(
        string="Création",
        default=False,
        help="Autorise la création de nouveaux enregistrements."
    )

    perm_write = fields.Boolean(
        string="Modification",
        default=False,
        help="Autorise la modification et mise à jour des enregistrements existants."
    )

    perm_unlink = fields.Boolean(
        string="Suppression",
        default=False,
        help="Autorise la suppression définitive des enregistrements."
    )

    notes = fields.Char(string="Périmètre / Remarques")

