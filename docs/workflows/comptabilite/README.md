# Workflow Comptabilité

## 1. Objectif métier

Le workflow Comptabilité décrit les flux comptables utilisés par PACKIMMO : factures de loyers, factures de vente, bills, commissions broker, pénalités, maintenance et charges syndic.

Ce guide ne couvre pas toute la comptabilité Odoo. Il documente uniquement les écritures créées ou suivies par les modules PACKIMMO analysés.

## 2. Utilisateurs concernés

- Comptable.
- Gestionnaire.
- Manager.
- Agent location ou vente pour consultation.
- Administrateur pour la configuration.

## 3. Menus utilisés

- Properties > Renting > Invoices
- Properties > Renting > Bills
- Properties > Renting > Penalties
- Properties > Selling > Invoices
- Properties > Selling > Penalties
- Properties > Maintenances > Invoices
- Properties > Maintenances > Bills
- Syndic > Charges
- Syndic > Relevés compteurs
- Factures Odoo standard.
- Properties > Configurations > Agreement Templates et produits de configuration.

## 4. Étapes principales

1. Configurer les produits : loyer, dépôt, commission broker, maintenance, pénalité.
2. Configurer le mode de validation des factures : manuel ou automatique.
3. Créer un contrat de location ou de vente.
4. Générer les échéances.
5. Créer les factures depuis les lignes.
6. Suivre le statut de paiement.
7. Créer les bills liés aux contrats ou maintenances.
8. Créer les pénalités si applicable.
9. Vérifier les marges sur les contrats.

## 5. Champs importants

Configuration :

- Invoice Post Type
- Installment Item
- Deposit Item
- Broker Commission Item
- Maintenance Item
- Contract Penalty Item
- Is Any Penalty
- Reminder days

Factures de location :

- Contract
- Customer
- Payment type
- Invoice date
- Amount
- Account invoice
- Payment state

Factures de vente :

- Contract
- Invoice date
- Amount
- Taxes
- Invoice created
- Payment state

Bills :

- Contract
- Vendor
- Motif du paiement
- Amount
- Product
- Taxes
- Account bill

## 6. Boutons et actions

- Create Invoice sur échéance location.
- Create Invoice sur échéance vente.
- Create Invoice et Create Bill sur maintenance.
- Create Invoice dans l'assistant de paiement complémentaire.
- Action Active sur contrat de location.
- Receive Remaining sur contrat de vente.
- Créer factures sur charges syndic et relevés compteurs.

## 7. Règles métier

- Les factures sont des `account.move`.
- Les factures client utilisent `move_type = out_invoice`.
- Les bills fournisseur utilisent `move_type = in_invoice`.
- Le paramètre `invoice_post_type` décide si la facture est postée automatiquement ou laissée en brouillon.
- Les lignes de location sont dans `rent.invoice`.
- Les lignes de vente sont dans `sale.invoice`.
- Les bills de location sont dans `rent.bill`.
- Les pénalités sont dans `penalty.invoice`.

## 8. Contrôles et blocages

- Les montants négatifs sont refusés dans les assistants.
- Un contrat de location ne peut pas être clôturé si des loyers restent impayés.
- Une facture de maintenance demande des produits.
- Une charge syndic sans ligne ne peut pas être facturée.
- Une vente demande des échéances avant confirmation.
- Les pénalités ne sont créées que sur factures postées et impayées selon les conditions du contrat.

## 9. Statuts

Facture Odoo :

- Draft
- Posted
- Paid / Not paid / Partial selon Odoo.

Contrat location :

- Draft
- Running
- Close
- Cancel
- Expire

Contrat vente :

- Booked
- Sold
- Cancel
- Refund
- Locked

## 10. Rapports ou PDF

- Factures Odoo.
- Bills Odoo.
- Rapport contrat de location.
- Rapport vente.
- Rapport de rappel.
- Exports Excel Property Reports et Landlord wise Report.

## 11. Tableaux de bord

Les dashboards calculent notamment les revenus, factures en retard, montants payés, montants restants, bills, marges et indicateurs de performance.

## 12. Sécurité et groupes utilisateurs

- Les comptables utilisent généralement les droits Odoo Accounting.
- Les gestionnaires PACKIMMO peuvent consulter ou déclencher des factures selon la matrice de permissions.
- Le profil de visibilité et la société active limitent les données métier.

## 13. Cas d'utilisation complets

### Générer une facture de loyer

1. Ouvrir le contrat de location.
2. Vérifier les échéances.
3. Cliquer sur Create Invoice sur la ligne.
4. Ouvrir la facture.
5. Poster ou vérifier le postage automatique.

### Créer un bill lié à un contrat

1. Ouvrir le contrat.
2. Lancer l'assistant de paiement complémentaire ou une maintenance.
3. Choisir le vendor, le produit et le montant.
4. Créer le bill.
5. Suivre son paiement.

### Contrôler la marge

1. Ouvrir le contrat de location.
2. Aller dans l'onglet P/L.
3. Comparer total facturé, total bills, payé, résiduel et marge.

## 14. Erreurs fréquentes

- Facture non postée : configuration en mode manuel.
- Montant refusé : valeur négative.
- Clôture refusée : loyer impayé.
- Pénalité absente : facture non postée ou pas en retard.
- Bill de maintenance refusé : produit ou vendor manquant.

## 15. Bonnes pratiques

- Vérifier les produits comptables avant mise en production.
- Contrôler les taxes sur loyer, dépôt et services.
- Ne pas confirmer une vente sans échéancier clair.
- Suivre les impayés depuis les menus Invoices et Penalties.
- Utiliser les bills pour mesurer la marge réelle.

## 16. Questions/Réponses MIA potentielles

- Où trouver les factures de loyer ?
- Comment créer une facture de vente ?
- Pourquoi une facture reste en brouillon ?
- Comment créer un bill ?
- Comment suivre les pénalités ?
- Pourquoi un contrat ne se clôture pas ?
- Où voir la marge d'un contrat ?
- Quels produits doivent être configurés ?
- Comment facturer une charge syndic ?
- Comment facturer une maintenance ?
