{
    'name': 'Gestion des Colis et Lots',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Gestion détaillée des lots et colis (Pièces, Longueur, Photos, Composition, Suivi)',
    'description': """
        Ce module ajoute des informations de gestion complète et de traçabilité des colis :
        - Nombre de pièces, Longueur, Quantité UV sur les lots.
        - Gestion complète des colis (stock.package) : composition multi-produit, photo, état (Disponible, Vendu...), observations, référence fournisseur.
        - Gestion dans les flux d'achat, de vente, de stock et de facturation.
    """,
    'author': 'Awami',
    'depends': ['stock', 'sale_management', 'purchase', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_lot_views.xml',
        'views/stock_package_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/stock_picking_views.xml',
        'views/account_move_views.xml',
        'reports/package_report.xml',
        'reports/sale_order_report_templates.xml',
        'reports/purchase_order_report_templates.xml',
        'reports/delivery_report_templates.xml',
        'reports/invoice_report_templates.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
