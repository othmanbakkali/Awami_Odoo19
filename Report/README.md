# Module Odoo 19 : Rapport Journalier des Ventes, Dépenses et Charges

## 1. Présentation
Ce module permet d'éditer, de consolider et de clôturer les journées d'activité commerciale et financière en intégrant :
- Les **Ventes Journalières** (Factures clients, avoirs, encaissements).
- Les **Dépenses et Charges** (Factures d'achat fournisseurs, charges externes, frais généraux).
- Les **Décaissements directs de caisse** (menues dépenses de caisse non facturées, avances, transport, etc.).
- Le **Résultat Net Journalier** ($Ventes - Dépenses$).
- Le **Solde Net de Caisse (Espèces)** ($Entrées\ Espèces - Sorties\ Espèces$) pour le contrôle du tiroir-caisse.
- La **Ventilation Trésorerie par mode de règlement** (Espèces, Virement bancaire, Chèque, Effet/Traite).

---

## 2. Structure Technique du Projet
```text
Report/
├── __init__.py
├── __manifest__.py
├── README.md
├── data/
│   └── ir_sequence_data.xml                  # Séquence de numérotation automatique (RVD/AAAA/MM/XXXX)
├── models/
│   ├── __init__.py
│   └── account_sales_expense_report.py       # Modèle persistant, agrégations, exports Excel/CSV
├── wizard/
│   ├── __init__.py
│   └── account_sales_expense_report_wizard.py# Assistant de génération et d'impression directe
├── views/
│   ├── account_sales_expense_report_views.xml        # Vues Formulaire, Liste, Recherche & Menus
│   └── account_sales_expense_report_wizard_views.xml # Vue dialogue du Wizard
├── report/
│   ├── report_sales_expense_reports.xml      # Action de rapport QWeb PDF & Format papier A4
│   └── report_sales_expense_pdf.xml          # Template haute lisibilité A4 Portrait
└── security/
    └── ir.model.access.csv                   # Droits d'accès utilisateurs et comptables
```

---

## 3. Fonctionnalités Clés

### A. Deux Modes de Génération
- **Rapport X (Aperçu Provisoire) :** Consultable à tout moment en cours de journée sans figer les écritures.
- **Rapport Z (Clôture Journalière Officielle) :** Génère un numéro séquentiel unique officiel avec archivage persistant.

### B. Synthèse Financière & Trésorerie
- **4 Cartes Métriques Clés (KPI) :**
  1. **Ventes Nettes TTC** (avec nombre de factures et avoirs).
  2. **Total Dépenses & Charges** (avec nombre de factures d'achat et décaissements).
  3. **Résultat Net Journalier** ($Ventes - Charges$).
  4. **Solde Net Caisse (Espèces)** ($Entrées - Sorties$).
- **Tableau de Trésorerie par Mode de Règlement :**
  - Entrées, Sorties et Solde Net pour Espèces, Virement bancaire, Chèque, Effet/Traite.

### C. Détails Complets
- Tableau des factures de vente et avoirs avec client, mode de règlement, référence chèque/effet, montant TTC, payé et statut.
- Tableau des dépenses et factures fournisseurs avec libellé/motif de la charge, fournisseur, mode de règlement, total TTC, payé et statut.
- Tableau des dépenses directes de caisse (sorties de caisse diverses sans facture fournisseur).

### D. Multi-Formats
- **Impression PDF QWeb A4 Portrait** avec en-tête société (ICE, IF, RC), contrastes haute lisibilité et cadre de double signature ("Visa Caissier" et "Visa Direction").
- **Export Excel (.xlsx)** complet multi-onglets mis en forme avec formules et totaux.
- **Export CSV** délimité par des points-virgules pour intégration comptable.

