# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ResUsers(models.Model):
    _inherit = 'res.users'

    role_ids = fields.Many2many(
        'res.users.role',
        'res_users_role_rel',
        'user_id',
        'role_id',
        string="Rôles Utilisateur",
        help="Sélectionnez les rôles métiers attribués à cet utilisateur."
    )

    roles_display = fields.Char(
        string="Rôles",
        compute='_compute_roles_display',
        store=True,
        help="Aperçu des rôles sous forme de texte pour les vues listes."
    )

    effective_rights_html = fields.Html(
        string="Matrice Lisible des Droits d'Accès",
        compute='_compute_effective_rights_html',
        sanitize=False,
        help="Tableau récapitulatif visuel des droits d'accès effectifs (Lecture, Création, Modification, Suppression)."
    )

    @api.depends('role_ids', 'role_ids.name')
    def _compute_roles_display(self):
        for user in self:
            user.roles_display = ", ".join(user.role_ids.mapped('name')) if user.role_ids else "Aucun rôle"

    @api.depends('role_ids', 'role_ids.line_ids', 'role_ids.prevent_invoice_unlink',
                 'role_ids.prevent_payment_unlink', 'role_ids.prevent_sale_order_unlink',
                 'role_ids.prevent_cheque_unlink', 'role_ids.prevent_partner_unlink',
                 'role_ids.is_readonly_role')
    def _compute_effective_rights_html(self):
        for user in self:
            if not user.role_ids:
                user.effective_rights_html = """
                <div class="alert alert-warning p-3">
                    <i class="fa fa-info-circle me-2"></i>
                    <strong>Aucun rôle spécifique assigné.</strong>
                    Cet utilisateur utilise les groupes techniques Odoo standards par défaut.
                    Assignez-lui un ou plusieurs rôles ci-dessus pour activer la matrice de sécurité.
                </div>
                """
                continue

            roles = user.role_ids.filtered(lambda r: r.active)
            is_admin = user.has_group('base.group_system')
            is_readonly = any(r.is_readonly_role for r in roles) and not is_admin

            # Anti-suppression combinée
            prevent_inv = any(r.prevent_invoice_unlink for r in roles) and not is_admin
            prevent_pay = any(r.prevent_payment_unlink for r in roles) and not is_admin
            prevent_so = any(r.prevent_sale_order_unlink for r in roles) and not is_admin
            prevent_chq = any(r.prevent_cheque_unlink for r in roles) and not is_admin
            prevent_part = any(r.prevent_partner_unlink for r in roles) and not is_admin

            # Modèles cibles standards pour la synthèse
            entities = [
                ('sale.order', "Bons de Vente / Devis (Magasin)", prevent_so),
                ('account.move', "Factures Clients & Fournisseurs", prevent_inv),
                ('account.payment', "Paiements & Encaissements", prevent_pay),
                ('suivi.cheque', "Chèques & Effets (Suivi bancaire)", prevent_chq),
                ('res.partner', "Clients, Fournisseurs & Contacts", prevent_part),
                ('product.template', "Articles & Produits", False),
                ('stock.picking', "Livraisons & Mouvements Stock", False),
                ('account.z.report', "Rapports Journaliers de Vente", False),
            ]

            rows_html = []
            for model_code, entity_label, is_prevented in entities:
                lines = roles.mapped('line_ids').filtered(lambda l: l.model_name == model_code)

                can_read = any(l.perm_read for l in lines) or is_admin
                can_create = (any(l.perm_create for l in lines) and not is_readonly) or is_admin
                can_write = (any(l.perm_write for l in lines) and not is_readonly) or is_admin
                can_unlink = (any(l.perm_unlink for l in lines) and not is_prevented and not is_readonly) or (is_admin and not is_prevented)

                badge_read = '<span class="badge bg-success text-white px-2 py-1"><i class="fa fa-eye me-1"></i> Autorisé</span>' if can_read else '<span class="badge bg-danger text-white px-2 py-1"><i class="fa fa-times me-1"></i> Refusé</span>'
                badge_create = '<span class="badge bg-success text-white px-2 py-1"><i class="fa fa-plus me-1"></i> Autorisé</span>' if can_create else '<span class="badge bg-danger text-white px-2 py-1"><i class="fa fa-times me-1"></i> Refusé</span>'
                badge_write = '<span class="badge bg-success text-white px-2 py-1"><i class="fa fa-pencil me-1"></i> Autorisé</span>' if can_write else '<span class="badge bg-danger text-white px-2 py-1"><i class="fa fa-times me-1"></i> Refusé</span>'
                
                if is_prevented:
                    badge_unlink = '<span class="badge bg-danger text-white px-2 py-1 fw-bold"><i class="fa fa-lock me-1"></i> VERROUILLÉ</span>'
                elif can_unlink:
                    badge_unlink = '<span class="badge bg-success text-white px-2 py-1"><i class="fa fa-trash me-1"></i> Autorisé</span>'
                else:
                    badge_unlink = '<span class="badge bg-danger text-white px-2 py-1"><i class="fa fa-times me-1"></i> Refusé</span>'

                rows_html.append(f"""
                <tr>
                    <td class="fw-bold text-dark">{entity_label}</td>
                    <td class="text-center">{badge_read}</td>
                    <td class="text-center">{badge_create}</td>
                    <td class="text-center">{badge_write}</td>
                    <td class="text-center">{badge_unlink}</td>
                </tr>
                """)

            roles_badges = " ".join([f'<span class="badge bg-primary text-white me-1 fs-6">{r.name}</span>' for r in roles])
            
            banner_html = ""
            if is_readonly:
                banner_html = """
                <div class="alert alert-info py-2 mb-3">
                    <i class="fa fa-lock me-2"></i>
                    <strong>Mode Consultation Seule actif :</strong> Cet utilisateur a des droits de lecture uniquement.
                </div>
                """
            elif any([prevent_inv, prevent_pay, prevent_so, prevent_chq, prevent_part]):
                banner_html = """
                <div class="alert alert-secondary py-2 mb-3 border-start border-4 border-danger">
                    <i class="fa fa-shield me-2 text-danger"></i>
                    <strong>Sécurité active :</strong> La suppression définitive des factures, paiements ou données sensibles est protégée pour ce profil.
                </div>
                """

            user.effective_rights_html = f"""
            <div class="p-2">
                <div class="mb-3">
                    <span class="text-muted me-2">Rôles effectifs attribués :</span>
                    {roles_badges}
                </div>
                {banner_html}
                <div class="table-responsive">
                    <table class="table table-bordered table-striped table-hover align-middle mb-0">
                        <thead class="table-dark text-white">
                            <tr>
                                <th style="width: 32%;">Entité / Fonctionnalité</th>
                                <th class="text-center" style="width: 17%;">👁️ Lecture (Read)</th>
                                <th class="text-center" style="width: 17%;">➕ Création (Create)</th>
                                <th class="text-center" style="width: 17%;">✏️ Modification (Write)</th>
                                <th class="text-center" style="width: 17%;">🗑️ Suppression (Delete)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join(rows_html)}
                        </tbody>
                    </table>
                </div>
            </div>
            """

    def write(self, vals):
        res = super().write(vals)
        if 'role_ids' in vals:
            for user in self:
                for role in user.role_ids:
                    role._sync_role_group()
        return res
