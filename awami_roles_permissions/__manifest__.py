# -*- coding: utf-8 -*-
{
    'name': 'Awami - Rôles & Droits d\'Accès Visuels',
    'version': '19.0.1.0.1',
    'category': 'Administration',
    'summary': 'Gestion lisible des droits d\'accès avec rôles (Lecture, Création, Modification, Suppression) et création de profils utilisateurs sur mesure.',
    'description': """
Gestion Visuelle et Lisible des Rôles & Droits d'Accès pour Awami Bois :
-----------------------------------------------------------------------
- Création simplifiée de Rôles Utilisateurs (Caissier, Commercial, Comptable, etc.).
- Matrice claire des 4 permissions fondamentales (Lecture, Création, Modification, Suppression).
- Garde-fous de sécurité stricts (Interdiction de supprimer les Factures, Paiements, Bons de Vente, Chèques ou Clients).
- Tableau récapitulatif visuel et lisible directement sur chaque fiche utilisateur Odoo.
- 5 Rôles métiers préconfigurés prêts à l'emploi.
    """,
    'author': 'Awami Bois',
    'website': 'https://awamibois.sdbo.ma',
    'depends': [
        'base',
        'sale',
        'account',
        'stock',
        'awami_suivi_cheques',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/multi_company_security.xml',
        'views/res_users_role_views.xml',
        'views/res_users_views.xml',
        'views/menu_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
