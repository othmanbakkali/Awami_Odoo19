# Note de Cadrage & Spécifications du Projet - Module Odoo 19

**Client / Projet :** Awami Oussama  
**Serveur :** `167.172.158.168` (Domaine : `awamibois.sdbo.ma`)  
**Version Odoo :** Odoo 19 Community  
**Base de données :** `Hanouty`

---

## 1. Contexte & Résolution de l'incident Serveur / Base de Données

### Diagnostic & Actions Réalisées :
1. **Cause de la panne :**
   - Le service PostgreSQL (`postgresql@16-main`) s'était arrêté suite à un déclenchement de l'OOM Killer Linux (Out of Memory) car le serveur ne possède que 1 Go de RAM et **aucun espace Swap** n'était configuré.
   - De plus, un processus mineur non autorisé (`xmrig`) tournait en arrière-plan et consommait le CPU et la RAM.
2. **Corrections appliquées :**
   - Processus indésirables éliminés et fichiers temporaires nettoyés (`/var/tmp/xmrig`, `/tmp/boot.sh`).
   - Cluster PostgreSQL 16 réactivé et vérifié (`pg_lsclusters` : cluster `main` en ligne).
   - Création et activation d'un fichier **Swap de 2.0 Go** (`/swapfile`) avec montage automatique au démarrage (`/etc/fstab`) pour prémunir le serveur contre tout arrêt mémoire futur.
   - Redémarrage et vérification d'Odoo 19 (`active running`, port 8069 fonctionnel, redirection HTTP 303 OK).

---

## 2. Spécifications Fonctionnelles du Nouveau Module

### A. Génération de Factures Format A5 (Double Exemplaire & Exemplaire Unique)
* **Format papier :** 
  - **Option 1 (Double Bon sur A4) :** Format **A4 Portrait** avec 2 bons superposés et ligne de découpe au milieu (`paperformat_a5_portrait`).
  - **Option 2 (Un seul Bon sur papier A5) :** Format **A5 Paysage** natif pour impression directe sur papier A5 (`paperformat_a5_single`).
* **Rapports d'impression (QWeb Reports) :**
  - **Rapport 1 : "Reçu A5 (2 Bons sur la même page)" :**
    - Exemplaire 1 : Copie Client (*"Copie Client"*).
    - Exemplaire 2 : Copie Contrôle (*"Copie Contrôle / Magasin"*).
  - **Rapport 2 : "Reçu A5 (1 Seul Exemplaire)" :**
    - Exemplaire unique format A5 Paysage (*"Copie Client"*).
* **Règles d'édition :**
  - Mention explicite du statut (Copie Client / Copie Contrôle).
  - Détail des articles, quantités, prix unitaires, remises éventuelles, taxes et montants totaux.
  - Pagination et mise en page adaptée pour une impression nette et optimisée sur papier A5.

---

### B. Renommage des Devis en "Bon Magasin"
* **Objectif :** Remplacer le terme standard *"Devis"* (Quotation) par **"Bon Magasin"**.
* **Périmètre du renommage :**
  - **Interface utilisateur (Ventes / Sales) :**
    - Titres de menus, listes, formulaires et boutons de création.
  - **Documents imprimés / PDF :**
    - En-tête du document devis : affichage de **"Bon Magasin N° [Numéro]"** au lieu de "Devis N°".
  - **Traductions & Termes :** Surcharge propre des chaînes de traduction (i18n) et des vues pour préserver l'intégrité sans altérer le cœur d'Odoo.

---

### C. Gestion Multi UoM & Calcul Bois au Mètre Cube (m³)
* **Objectif :** Permettre la vente et la facturation selon les unités multiples (ml, m³, pièces...) avec calcul dimensionnel spécifique pour le bois.
* **Calcul automatique pour les articles en Mètre Cube (m³) :**
  - Ajout des champs de saisie sur la commande et la facture (tous en mètres avec 5 chiffres après la virgule) :
    - **Longueur** ($L$, en mètres - 5 décimales)
    - **Largeur** ($l$, en mètres - 5 décimales)
    - **Épaisseur** ($E$, en mètres - 5 décimales)
  - **Formule de calcul automatique :**
    $$\text{Volume } (m^3) = \text{Longueur (m)} \times \text{Largeur (m)} \times \text{Épaisseur (m)}$$
    $$\text{Total} = \text{Volume } (m^3) \times \text{Prix du } m^3$$
  - La quantité facturée devient automatiquement le volume calculé en $m^3$ (avec 5 décimales).
  - Affichage clair des dimensions sur les documents imprimés (**Bon Magasin** et **Facture A5**).
* **Colonne "Prix Unitaire de Base" (P.U Base) :**
  - Ajout d'une colonne dédiée `base_price_unit` (**P.U Base**) dans les lignes de commande et de facture, affichée juste avant le prix unitaire.
  - Saisie libre et dynamique : l'utilisateur peut saisir ou modifier le prix de base de référence (ex: prix au $m^3$ ou prix au mètre linéaire $ml$).
  - **Prise en compte dans tous les calculs :**
    - Pour les articles en $m^3$ ou débit bois : $\text{Prix Unitaire} = \text{P.U Base}$, et $\text{Total} = \text{Volume } (m^3) \times \text{P.U Base}$.
    - Pour les unités multiples (ex: pièce de $4.2\text{ ml}$) : $\text{Prix Unitaire} = \text{P.U Base} \times \text{Ratio d'unité}$ (ex: $250 \times 4.2 = 1050\text{ DH}$).
    - Synchronisation bidirectionnelle : si le prix unitaire est modifié directement, le `P.U Base` s'ajuste en miroir.
    - Transfert automatique du `P.U Base` lors de la génération de la facture depuis le bon de commande.
    - Mention claire sur les impressions PDF (**Bon Magasin** et **Facture A5**).

---

### D. Modes de Paiement
* **Configuration des modes et méthodes de règlement :**
  - **Virement bancaire** : Journal dédié avec coordonnées bancaires (RIB/IBAN).
  - **Chèque** : Suivi des encaissements, nom client/émetteur et **numéro de série obligatoires**.
  - **Effet / Traite / LCN** : Gestion des effets de commerce avec nom client/tireur, **numéro de série obligatoire** et date d'échéance.
  - **Espèces** : Encaissement standard au comptoir.
* **Règles de validation & Sécurité métier :**
  - Si le mode de règlement choisi est **Chèque**, **Effet**, **Effet / Traite** ou **Effet / Chèque** :
    - Le **Nom du client** (`partner_id` / `check_client_name`) est **strictement obligatoire**.
    - Le **Numéro de série** (`check_number` - numéro du chèque ou de l'effet) est **strictement obligatoire**.
    - La **Date d'échéance** (`check_date_due`) est disponible pour le suivi des dates de valeur/échéances.
* **Intégration & Impressions :**
  - Transfert automatique des références de paiement lors de la conversion du Bon Magasin (devis/commande) en Facture.
  - Affichage clair et exhaustif du mode de règlement, du numéro de série et de l'échéance sur le rapport de facture A5 (Copie Client & Contrôle) et le Bon Magasin.
  - Intégration dans le calcul du Rapport Z Journalier des Ventes Facturées.

---

### E. Numérotation & Séquence Journalière des Factures (Format BL)
* **Format officiel exigé :** `BL/AAAA/MM/JJ/XXXX` (ex: `BL/2026/10/13/0001`).
* **Comportement du compteur :**
  - Numérotation incrémentale continue tout au long de la journée (`0001`, `0002`, `0003`...).
  - **Réinitialisation automatique chaque jour** : Dès le lendemain, la séquence recommence à `0001` (ex: `BL/2026/10/14/0001`).
  - Surcharge native des méthodes du mixin de séquence Odoo 19 (`_sequence_daily_regex`, `_deduce_sequence_number_reset`, `_get_sequence_date_range`, `_get_sequence_format_param`, `_get_next_sequence_format`, `_get_starting_sequence`, `_sequence_matches_date`, `_get_last_sequence_domain`).

---

## 3. Architecture Technique du Module Odoo


* **Nom technique suggéré :** `awami_sale_invoice_custom` ou `awami_bon_magasin`
* **Structure :**
  ```text
  awami_bon_magasin/
  ├── __init__.py
  ├── __manifest__.py
  ├── models/
  │   ├── __init__.py
  │   ├── sale_order.py
  │   └── account_move.py
  ├── views/
  │   ├── sale_order_views.xml
  │   └── account_move_views.xml
  ├── report/
  │   ├── paperformat.xml          (Définition du format papier A5)
  │   ├── report_invoice_a5.xml    (Rapport double copie : Client & Contrôle)
  │   └── report_sale_order.xml    (Rapport Bon Magasin)
  ├── data/
  │   └── payment_methods.xml      (Configuration Virement & Chèque)
  └── i18n/
      └── fr.po                    (Traductions personnalisées)
  ```

---

### F. Amélioration de la Qualité & Ventilation du Rapport Z Journalier
* **Module concerné :** `Etat_Vente_Journalier_facturé` (version `19.0.1.0.2`).
* **Résolution du problème de lisibilité :**
  - Ajout d'un format de papier dédié (`paperformat_account_z_report`) en format A4 Portrait avec marges optimisées de 8mm et résolution 96 DPI.
  - Refonte graphique complète du template PDF (`account_z_report_pdf.xml`) avec police standard haute lisibilité (`DejaVu Sans`, Arial), bordures nettes, contrastes renforcés et padding aéré.
  - Structure côte-à-côte robuste pour la synthèse financière et la ventilation des encaissements sans risque de chevauchement sous wkhtmltopdf.
* **Ventilation stricte des modes de paiement & affichage du Nom Client à côté :**
  - **Nom du client affiché explicitement à côté de Banque (Virement), Chèque et Effet :**
    - Dans la boîte **« Ventilation par mode de règlement »** : chaque ligne de Banque/Virement, Chèque et Effet indique clairement le **Nom du client** et le **N° de référence / série**, permettant au caissier ou gestionnaire de rapprocher immédiatement chaque chèque, traite ou virement.
    - Dans le tableau **« Détail des factures clients »** : sous le badge de règlement (Virement, Chèque, Effet), affichage immédiat du nom du client/titulaire et du N° de chèque/série. Si le titulaire du chèque ou de l'effet diffère du client de facturation, la mention est également précisée dans la colonne Client.
    - Dans les exports **Excel et CSV** : ajout des colonnes et mentions `Mode - Nom Client (N° Série)` pour un pointage comptable fluide.
  - Méthode Python `_determine_move_payment_mode()` : respecte prioritairement le mode explicite choisi sur la facture (`especes` -> Espèces, `virement` -> Virement bancaire, `cheque` -> Chèque, `effet` -> Effet / Traite), complété par l'analyse fine des journaux de caisse vs banque et des lignes de paiement réconciliées.
* **Détail des Factures Clients :**
  - Colonne **Règlement & Client** avec badges colorés distinctifs :
    - Vert pour **Espèces**
    - Bleu pour **Virement bancaire** + Nom Client
    - Violet pour **Chèque** + Nom Client + N° de chèque/série
    - Ambre pour **Effet / Traite** + Nom Client + N° de série
  - Colonnes précises : Date, N° Facture, Client, Règlement & Client, Total HT, TVA, Total TTC, Payé, Statut (avec reste éventuel si partiel).
  - Ligne de **Totalisation générale** en pied de tableau (`tfoot`) avec cumul des montants HT, TVA, TTC et Payé.
  - Même structure pour la liste des avoirs émis avec codes couleur bordeaux/rouge.

---

## 4. Statut du Déploiement

* **Mise à jour & Déploiement Réalisés avec Succès :**
  - **Date & Heure :** 31/10/2026 15:56 UTC
  - **Serveur :** `167.172.158.168` (`awamibois.sdbo.ma`), Base `Hanouty`
  - **Sauvegarde pré-déploiement :** `/opt/odoo/backup_etat_vente_1793462100/`
  - **Modules synchronisés & déployés en production :**
    - `etat_vente_journalier_facture` : Version **19.0.1.0.7** (Statut : `installed`)
      - Retrait définitif du tableau *« Top Articles Vendus (par Chiffre d'Affaires) »* du rapport PDF.
      - Correction de l'alignement et de la largeur des colonnes dans le pied de tableau (`tfoot`) : élargissement de la colonne Statut à 13%, passage de la mention *« Impayé »* sur deux lignes (*Libellé* en haut, *Montant* en bas) pour éliminer tout chevauchement avec la colonne *Payé*.
    - `Report` : Version **19.0.1.0.1** (Statut : `installed`)
      - Nouveau module pour la génération des rapports journaliers consolidant Ventes, Dépenses et Charges fournisseurs, Décaissements directs de caisse, Flux de trésorerie net et Solde théorique de caisse.
  - **Service Odoo 19 :** Actif (`running`), 127 modules chargés, port 8069 opérationnel (HTTP 303/200 OK).


