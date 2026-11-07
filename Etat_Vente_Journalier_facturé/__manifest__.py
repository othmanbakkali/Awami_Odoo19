# -*- coding: utf-8 -*-
{
    'name': 'Rapport Z Journalier des Ventes Facturées',
    'version': '19.0.1.0.7',
    'category': 'Accounting/Accounting',
    'summary': 'Rapport Z et X journalier haute lisibilité : affichage du nom du client pour Banque/Virement, Chèque et Effet, ventilation stricte et exports complets',
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
