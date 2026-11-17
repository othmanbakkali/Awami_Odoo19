# -*- coding: utf-8 -*-
{
    'name': 'Rapport des Ventes Journalier',
    'version': '19.0.1.0.9',
    'category': 'Accounting/Accounting',
    'summary': 'Rapport des Ventes journalier haute lisibilité : détail des chèques & effets, ventilation stricte des modes de paiement et exports complets',
    'description': """
Ce module permet de générer des Rapports Z (Clôtures journalières) et Rapports X (Aperçus)
des ventes facturées pour Odoo 19 :
- Présentation haute lisibilité avec format papier optimisé A4 (marges 8mm) et typographie soignée.
- Ventilation stricte et fidèle des modes de règlement (Espèces, Virement bancaire, Chèque, Effet/Traite).
- Affichage explicite du Nom du Client à côté des règlements par Banque (Virement), Chèque et Effet (avec N° de série).
- Détail exhaustif des factures et avoirs avec badges colorés par mode de règlement, statuts de paiement et totalisation.
- Synthèse financière, ventilation TVA et classement des meilleures ventes.
- Historique complet, archives PDF automatiques et exports Excel/CSV.
    """,
    'author': 'Antigravity',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'security/account_z_report_security.xml',
        'data/ir_sequence_data.xml',

        'views/res_company_views.xml',
        'views/account_z_report_wizard_views.xml',
        'views/account_z_report_views.xml',
        'report/account_z_report_reports.xml',
        'report/account_z_report_pdf.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
