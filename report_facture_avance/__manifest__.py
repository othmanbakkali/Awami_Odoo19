# -*- coding: utf-8 -*-
{
    'name': 'Suivi Factures & Avances',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Suivi des Factures et Avances clients avec gestion des mouvements masqués',
    'description': """
Module de Suivi des Factures et Avances pour Odoo 19:
=====================================================
- Consolidation des factures de vente clients et des avances / règlements perçus.
- Recherche avancée et filtres par type, statut de paiement, période et visibilité.
- Possibilité de masquer (hidden) ou rendre visibles des mouvements individuellement ou en lot.
- Vues Liste moderne Odoo 19, Formulaire détaillé, Pivot et Graphique analytiques.
    """,
    'author': 'Custom',
    'license': 'LGPL-3',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'views/report_facture_avance_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
