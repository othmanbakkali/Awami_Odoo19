# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class ResUsersRole(models.Model):
    _name = 'res.users.role'
    _description = "Rôle & Profil Utilisateur"
    _order = 'sequence asc, name asc'

    name = fields.Char(
        string="Nom du Rôle",
        required=True,
        help="Ex: Caissier Magasin, Commercial Ventes, Responsable Facturation, etc."
    )

    code = fields.Char(
        string="Code Réf",
        help="Code court ou identifiant (ex: CAISSE, COMM, COMPTA, ADMIN)"
    )

    active = fields.Boolean(
        string="Actif",
        default=True,
        help="Permet de désactiver temporairement un rôle."
    )

    sequence = fields.Integer(string="Ordre d'affichage", default=10)

    color = fields.Integer(string="Couleur", default=4)

    description = fields.Text(
        string="Description / Périmètre des Missions",
        help="Détail des prérogatives et responsabilités attribuées à ce rôle."
    )

    # Utilisateurs assignés
    user_ids = fields.Many2many(
        'res.users',
        'res_users_role_rel',
        'role_id',
        'user_id',
        string="Utilisateurs Assignés",
        help="Employés et utilisateurs disposant de ce rôle."
    )

    users_count = fields.Integer(
        string="Nombre d'Utilisateurs",
        compute='_compute_users_count',
        store=True
    )

    # Groupe technique Odoo
    group_id = fields.Many2one(
        'res.groups',
        string="Groupe Technique Lié",
        ondelete='cascade',
        copy=False,
        help="Groupe technique Odoo généré pour porter les droits d'accès de ce rôle."
    )

    # Groupes Odoo standards inclus (Ventes, Facturation, Stock, etc.)
    base_group_ids = fields.Many2many(
        'res.groups',
        'res_users_role_group_rel',
        'role_id',
        'group_id',
        string="Profils / Groupes Standards Inclus",
        help="Associe des groupes Odoo standards (ex: Ventes / Tous les documents, Facturation, Stock / Utilisateur)."
    )

    # Matrice des droits CRUD
    line_ids = fields.One2many(
        'res.users.role.line',
        'role_id',
        string="Matrice des Droits d'Accès",
        copy=True
    )

    # Garde-fous et restrictions de sécurité matérielles
    prevent_invoice_unlink = fields.Boolean(
        string="Interdire la Suppression des Factures",
        default=True,
        help="Bloque toute tentative de suppression définitive de facture client ou fournisseur."
    )

    prevent_payment_unlink = fields.Boolean(
        string="Interdire la Suppression des Paiements",
        default=True,
        help="Bloque toute tentative de suppression définitive des règlements et encaissements."
    )

    prevent_sale_order_unlink = fields.Boolean(
        string="Interdire la Suppression des Bons de Vente / Devis",
        default=True,
        help="Bloque toute tentative de suppression de bon de vente ou devis."
    )

    prevent_cheque_unlink = fields.Boolean(
        string="Interdire la Suppression des Chèques & Effets",
        default=True,
        help="Bloque toute tentative de suppression de chèque ou effet dans le suivi."
    )

    prevent_partner_unlink = fields.Boolean(
        string="Interdire la Suppression des Clients / Contacts",
        default=True,
        help="Bloque toute tentative de suppression de fiche client ou fournisseur."
    )

    is_readonly_role = fields.Boolean(
        string="Rôle Consultation Seule (Lecture Uniquement)",
        default=False,
        help="Si coché, ce rôle est strictement bridé en lecture seule : toute tentative de création, modification ou suppression sur les entités métiers sera bloquée."
    )

    @api.depends('user_ids')
    def _compute_users_count(self):
        for role in self:
            role.users_count = len(role.user_ids)

    def action_populate_default_models(self):
        """Remplit la matrice avec les modèles métiers clés d'Awami Bois."""
        self.ensure_one()
        Model = self.env['ir.model']

        # Liste des modèles cibles clés
        target_models = [
            ('sale.order', "Bons de Vente & Devis (Magasin)", 10, True, True, True, not self.prevent_sale_order_unlink),
            ('account.move', "Factures Clients & Fournisseurs", 20, True, True, True, not self.prevent_invoice_unlink),
            ('account.payment', "Paiements & Encaissements", 30, True, True, True, not self.prevent_payment_unlink),
            ('suivi.cheque', "Suivi des Chèques & Effets", 40, True, True, True, not self.prevent_cheque_unlink),
            ('res.partner', "Clients, Fournisseurs & Contacts", 50, True, True, True, not self.prevent_partner_unlink),
            ('product.template', "Articles & Produits", 60, True, False, False, False),
            ('stock.picking', "Livraisons & Mouvements Stock", 70, True, True, True, False),
            ('account.z.report', "Rapports de Vente Journaliers", 80, True, True, False, False),
        ]

        existing_models = self.line_ids.mapped('model_name')
        lines_to_create = []

        for model_code, label, seq, r, c, w, u in target_models:
            if model_code in existing_models:
                continue
            model_rec = Model.search([('model', '=', model_code)], limit=1)
            if model_rec:
                if self.is_readonly_role:
                    c = w = u = False
                lines_to_create.append({
                    'role_id': self.id,
                    'sequence': seq,
                    'name': label,
                    'model_id': model_rec.id,
                    'perm_read': r,
                    'perm_create': c,
                    'perm_write': w,
                    'perm_unlink': u,
                })

        if lines_to_create:
            self.env['res.users.role.line'].create(lines_to_create)

        return True

    def _sync_role_group(self):
        """Crée ou met à jour le groupe technique et les droits ir.model.access."""
        Group = self.env['res.groups']
        ModelAccess = self.env['ir.model.access']

        for role in self:
            # 1. Groupe technique
            if not role.group_id:
                grp_name = f"Rôle : {role.name}"
                grp = Group.sudo().create({
                    'name': grp_name,
                    'comment': f"Groupe généré automatiquement pour le rôle {role.name}",
                })
                role.group_id = grp.id
            else:
                expected_name = f"Rôle : {role.name}"
                if role.group_id.name != expected_name:
                    role.group_id.sudo().write({'name': expected_name})

            grp = role.group_id.sudo()

            # 2. Utilisateurs du groupe
            grp.write({'user_ids': [(6, 0, role.user_ids.ids)]})

            # 3. Synchronisation des groupes de base Odoo vers les utilisateurs
            if role.base_group_ids and role.user_ids:
                for base_grp in role.base_group_ids.sudo():
                    users_to_add = role.user_ids - base_grp.user_ids
                    if users_to_add:
                        base_grp.write({'user_ids': [(4, u.id) for u in users_to_add]})

            # 4. Synchronisation de la matrice ir.model.access
            existing_access = ModelAccess.sudo().search([('group_id', '=', grp.id)])
            existing_by_model = {acc.model_id.id: acc for acc in existing_access}

            active_model_ids = set()
            for line in role.line_ids:
                if not line.model_id:
                    continue
                active_model_ids.add(line.model_id.id)
                vals = {
                    'name': f"role.{role.code or role.id}.{line.model_id.model}",
                    'model_id': line.model_id.id,
                    'group_id': grp.id,
                    'perm_read': line.perm_read,
                    'perm_create': line.perm_create if not role.is_readonly_role else False,
                    'perm_write': line.perm_write if not role.is_readonly_role else False,
                    'perm_unlink': line.perm_unlink if not role.is_readonly_role else False,
                }
                if line.model_id.id in existing_by_model:
                    existing_by_model[line.model_id.id].write(vals)
                else:
                    ModelAccess.sudo().create(vals)

            # Supprimer les accès qui ne sont plus dans la matrice
            to_delete = existing_access.filtered(lambda a: a.model_id.id not in active_model_ids)
            if to_delete:
                to_delete.unlink()

    def action_apply_role(self):
        """Action déclenchée pour forcer l'application immédiate des droits."""
        self._sync_role_group()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Rôle Appliqué"),
                'message': _("Les droits et utilisateurs du rôle '%s' ont été synchronisés avec succès.") % self.name,
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model_create_multi
    def create(self, vals_list):
        roles = super().create(vals_list)
        for role in roles:
            if not role.line_ids:
                role.action_populate_default_models()
            role._sync_role_group()
        return roles

    def write(self, vals):
        res = super().write(vals)
        if any(f in vals for f in ['name', 'user_ids', 'base_group_ids', 'line_ids', 'is_readonly_role',
                                  'prevent_invoice_unlink', 'prevent_payment_unlink', 'prevent_sale_order_unlink',
                                  'prevent_cheque_unlink', 'prevent_partner_unlink']):
            self._sync_role_group()
        return res

    def unlink(self):
        for role in self:
            if role.group_id:
                role.group_id.sudo().unlink()
        return super().unlink()

    @api.model
    def _init_default_roles(self):
        """Initialise 5 rôles prêts à l'emploi si aucun rôle n'existe."""
        if self.search_count([]) > 0:
            return

        Model = self.env['ir.model']
        Role = self.sudo()

        # Groupes Odoo standards
        g_salesman_all = self.env.ref('sales_team.group_sale_salesman_all_leads', raise_if_not_found=False)
        g_salesman_own = self.env.ref('sales_team.group_sale_salesman', raise_if_not_found=False)
        g_sales_admin = self.env.ref('sales_team.group_sale_manager', raise_if_not_found=False)
        g_invoice = self.env.ref('account.group_account_invoice', raise_if_not_found=False)
        g_compta_user = self.env.ref('account.group_account_user', raise_if_not_found=False)
        g_compta_admin = self.env.ref('account.group_account_manager', raise_if_not_found=False)
        g_stock_user = self.env.ref('stock.group_stock_user', raise_if_not_found=False)
        g_stock_admin = self.env.ref('stock.group_stock_manager', raise_if_not_found=False)

        # 1. Caissier / Vendeur Magasin
        caisse_base_groups = [g for g in [g_salesman_all, g_invoice, g_stock_user] if g]
        role_caisse = Role.create({
            'name': "Caissier / Vendeur Magasin",
            'code': "CAISSE",
            'color': 2,
            'description': "Permet de saisir les devis/bons magasin, facturer et encaisser les règlements (espèces, chèques, virements). Suppression des factures et paiements strictement verrouillée.",
            'base_group_ids': [(6, 0, [g.id for g in caisse_base_groups])],
            'prevent_invoice_unlink': True,
            'prevent_payment_unlink': True,
            'prevent_sale_order_unlink': True,
            'prevent_cheque_unlink': True,
            'prevent_partner_unlink': True,
        })
        role_caisse.action_populate_default_models()

        # 2. Responsable Commercial & Facturation
        compta_base_groups = [g for g in [g_sales_admin, g_compta_user, g_stock_user] if g]
        role_resp = Role.create({
            'name': "Responsable Commercial & Facturation",
            'code': "RESP_VENTES",
            'color': 3,
            'description': "Gestion avancée des ventes, validation des factures, suivi des règlements et chèques. Suppression des paiements verrouillée.",
            'base_group_ids': [(6, 0, [g.id for g in compta_base_groups])],
            'prevent_invoice_unlink': False,
            'prevent_payment_unlink': True,
            'prevent_sale_order_unlink': False,
            'prevent_cheque_unlink': True,
            'prevent_partner_unlink': False,
        })
        role_resp.action_populate_default_models()

        # 3. Commercial / Vendeur Terrain
        comm_base_groups = [g for g in [g_salesman_own] if g]
        role_comm = Role.create({
            'name': "Commercial / Vendeur Terrain",
            'code': "COMMERCIAL",
            'color': 4,
            'description': "Création de devis et gestion de ses clients uniquement. Aucun accès à la facturation comptable ni aux suppressions de données.",
            'base_group_ids': [(6, 0, [g.id for g in comm_base_groups])],
            'prevent_invoice_unlink': True,
            'prevent_payment_unlink': True,
            'prevent_sale_order_unlink': True,
            'prevent_cheque_unlink': True,
            'prevent_partner_unlink': True,
        })
        role_comm.action_populate_default_models()

        # 4. Consultation Seule / Contrôle
        role_read = Role.create({
            'name': "Consultation / Contrôle (Lecture Seule)",
            'code': "AUDIT",
            'color': 5,
            'description': "Accès en lecture seule sur l'ensemble des modules (Bons, Factures, Paiements, Stocks, Rapports). Aucune création, modification ou suppression possible.",
            'is_readonly_role': True,
            'prevent_invoice_unlink': True,
            'prevent_payment_unlink': True,
            'prevent_sale_order_unlink': True,
            'prevent_cheque_unlink': True,
            'prevent_partner_unlink': True,
        })
        role_read.action_populate_default_models()

        # 5. Direction Générale / Administrateur
        admin_base_groups = [g for g in [g_sales_admin, g_compta_admin, g_stock_admin] if g]
        role_admin = Role.create({
            'name': "Direction Générale / Administrateur",
            'code': "DIRECTION",
            'color': 1,
            'description': "Accès intégral sans restriction avec droits de suppression et d'administration complets.",
            'base_group_ids': [(6, 0, [g.id for g in admin_base_groups])],
            'prevent_invoice_unlink': False,
            'prevent_payment_unlink': False,
            'prevent_sale_order_unlink': False,
            'prevent_cheque_unlink': False,
            'prevent_partner_unlink': False,
        })
        role_admin.action_populate_default_models()
        # Mettre les utilisateurs admin existants dans ce rôle
        admin_users = self.env['res.users'].search([('share', '=', False)])
        role_admin.write({'user_ids': [(6, 0, admin_users.ids)]})
        role_admin._sync_role_group()
