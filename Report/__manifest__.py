# -*- coding: utf-8 -*-
{
    'name': 'Rapport Journalier des Ventes, Dépenses et Charges',
    'version': '19.0.1.0.5',
    'category': 'Accounting/Accounting',
    'summary': 'Génération des rapports journaliers de vente avec détail des dépenses, charges, trésorerie et résultat net',
    'description': """
Rapport Journalier des Ventes, Dépenses et Charges (Odoo 19)
============================================================
Ce module permet d'éditer et de clôturer les journées d'activité commerciale et financière :
- Suivi et clôture des Ventes Journalières (Factures clients, avoirs, encaissements).
- Suivi détaillé des Dépenses et Charges (Factures d'achat fournisseurs, charges externes, frais généraux).
- Suivi des Notes de Frais et Dépenses RH (Salaires journaliers ouvriers/chauffeurs, avances, pourboires, maintenance).
- Suivi des décaissements directs de caisse (menues dépenses de caisse, avances, transport, etc.).
- Synthèse financière globale : Chiffre d'Affaires Net, Dépenses Nettes, Résultat Net Journalier.
- Trésorerie nette et contrôle de caisse (Encaissements espèces vs Décaissements espèces et salaires).
- Ventilation par mode de règlement (Espèces, Virement bancaire, Chèque, Effet/Traite).
- Historique complet, impressions PDF A4 haute définition, exports Excel (.xlsx) et CSV.
- Modes Rapport X (Aperçu provisoire en direct) et Rapport Z (Clôture journalière officielle).
    """,
    'author': 'Antigravity / SDBO',
    'depends': ['account', 'awami_bon_magasin', 'hr_expense'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'report/report_sales_expense_reports.xml',
        'report/report_sales_expense_pdf.xml',
        'views/account_sales_expense_report_views.xml',
        'views/account_sales_expense_report_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
