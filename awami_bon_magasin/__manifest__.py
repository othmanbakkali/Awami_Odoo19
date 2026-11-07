# -*- coding: utf-8 -*-
{
    'name': 'Awami - Bon Magasin & Facturation A5',
    'version': '19.0.1.3.1',
    'category': 'Sales/Sales',
    'summary': 'Renommage Devis en Bon Magasin, Facture A5 double exemplaire (A4), 2 Pages A5 (Client & Contrôle) et exemplaire unique (Format Papier A5), Multi-UoM, modes de paiement Chèque et Effet, validation manuelle statut Payé.',
    'description': """
Module personnalisé pour Awami Bois :
=======================================
1. Renommage des Devis en "Bon Magasin" (Interface & Impressions PDF).
2. Impression de facture / reçu au format A5 :
   - Rapport 1 : Reçu A5 (2 Pages A5 : Client & Contrôle) sur format papier A5
   - Rapport 2 : Double exemplaire sur feuille A4 (Copie Client + Copie Contrôle avec trait de découpe)
   - Rapport 3 : Exemplaire unique sur papier format A5 (1 seul bon)
3. Intégration complète Multi-Unités de Mesure (UoM) sur les lignes de vente et de facturation.
4. Prise en charge des modes de règlement Virement, Espèces, Chèque et Effet avec nom client et numéro de série obligatoires, reportés sur les documents PDF.
5. Gestion des paiements clients : bouton de validation 'Marquer comme Payé', synchronisation des modes de règlement Virement et Chèque sur les paiements et le formulaire d'enregistrement.
    """,
    'author': 'Awami Bois',
    'website': 'https://awamibois.sdbo.ma',
    'depends': [
        'base',
        'sale',
        'account',
        'uom',
    ],
    'data': [
        'data/uom_data.xml',
        'report/paperformat.xml',
        'report/report_bon_magasin.xml',
        'report/report_invoice_a5.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'views/account_payment_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
