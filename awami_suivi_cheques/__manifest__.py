# -*- coding: utf-8 -*-
{
    'name': 'Awami - Suivi des Chèques et Effets',
    'version': '19.0.1.0.1',
    'category': 'Accounting/Accounting',
    'summary': 'Module de monitoring et suivi des chèques et effets : Payé, Impayé, Date d\'échéance, Retour banque, à base des paiements.',
    'description': """
Module de Suivi des Chèques &amp; Effets pour Awami Bois
--------------------------------------------------------
- Monitoring complet des chèques clients et fournisseurs à partir des paiements saisis.
- Statuts de suivi : En portefeuille, Déposé à la banque, Payé / Encaissé, Retour de la banque, Impayé, Annulé.
- Gestion des dates : Date de réception, Date d'échéance avec alertes de retard (échus), Date de remise, Date d'encaissement, Date de rejet/retour.
- Enregistrement des motifs de retour banque (sans provision, signature, etc.) et notes de relance.
- Synchronisation automatique bidirectionnelle avec les paiements (account.payment) et factures.
- Tableaux de bord Kanban, Liste décorée avec codes couleurs, Recherche avancée, Graphiques et Pivots.
- Intégration dans le menu Comptabilité / Facturation et menu dédié de premier niveau.
    """,
    'author': 'Awami Bois',
    'website': 'https://awamibois.sdbo.ma',
    'depends': [
        'base',
        'account',
        'mail',
        'awami_bon_magasin',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/suivi_cheque_views.xml',
        'views/account_payment_views.xml',
        'views/menu_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
