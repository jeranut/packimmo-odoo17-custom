# Workflow Maintenance

## 1. Objectif métier

Le workflow Maintenance permet de créer, suivre et facturer les demandes d'intervention liées à un bien, un contrat de location ou un contrat de vente.

Il s'appuie sur le module Odoo Maintenance enrichi par `rental_management`.

## 2. Utilisateurs concernés

- Gestionnaire de maintenance.
- Agent location.
- Agent vente.
- Responsable technique.
- Comptable pour les factures et bills.
- Manager.

## 3. Menus utilisés

- Properties > Maintenances > Request
- Properties > Maintenances > Invoices
- Properties > Maintenances > Bills
- Depuis un bien : Maintenance.
- Depuis un contrat de location : Maintenance Request.
- Depuis un contrat de vente : Maintenance Request.

## 4. Étapes principales

1. Ouvrir le bien ou le contrat concerné.
2. Créer une demande de maintenance.
3. Renseigner le sujet, le bien, le contrat, le type et l'équipe.
4. Ajouter les produits ou prestations de maintenance.
5. Choisir si le paiement est facturé à un client ou enregistré en bill.
6. Créer la facture ou le bill.
7. Suivre l'état de la demande et le paiement.

## 5. Champs importants

Demande :

- Request
- Property
- Rent Contract
- Sell Contract
- Customer
- Vendor
- LandLord
- Maintenance Type
- Team
- Payment From : Customer ou Vendor
- Payment Type : Invoice ou Bill
- Products
- Total Untaxed Amount
- Invoice
- Bill

Produit :

- Product
- Description
- Quantity
- Price Unit
- Taxes
- Subtotal

## 6. Boutons et actions

- Create Invoice.
- Create Bill.
- Voir les factures.
- Voir les bills.
- Ouvrir les maintenances depuis les smart buttons des contrats.
- Actions standards Odoo Maintenance selon les étapes de maintenance installées.

## 7. Règles métier

- Une maintenance peut être liée à un bien, à un contrat de location ou à un contrat de vente.
- La facture client est une `account.move` de type customer invoice.
- Le bill est une `account.move` fournisseur.
- Le produit doit exister avant création de facture ou bill.
- Le mode de validation automatique des factures dépend de la configuration `invoice_post_type`.

## 8. Contrôles et blocages

- Une facture ne peut pas être créée sans produit de maintenance.
- Un bill ne peut pas être créé sans produit de maintenance.
- Si le paiement vient du client, le client est obligatoire.
- Si le paiement vient du vendeur/prestataire, le vendor est obligatoire.
- Les lignes doivent contenir des valeurs cohérentes de quantité et prix.

## 9. Statuts

Le module utilise les états standards de maintenance Odoo et les indicateurs :

- In Progress
- Blocked
- Done
- Cancelled ou archived
- Corrective
- Preventive
- Due today
- Overdue

## 10. Rapports ou PDF

- Facture client de maintenance.
- Bill fournisseur de maintenance.
- Les demandes sont visibles depuis les contrats et les menus maintenance.

## 11. Tableaux de bord

Le dashboard maintenance calcule :

- total des demandes ;
- demandes en cours ;
- demandes bloquées ;
- demandes terminées ;
- demandes annulées ;
- correctives et préventives ;
- demandes dues aujourd'hui ;
- demandes en retard ;
- montants de factures et bills par mois.

## 12. Sécurité et groupes utilisateurs

- Property Rental Manager et Property Rental Officer ont accès aux menus Properties.
- Packimmo Gestionnaire et Manager peuvent suivre la maintenance selon les droits configurés.
- Le profil de visibilité et la société active peuvent limiter les demandes visibles.

## 13. Cas d'utilisation complets

### Facturer une intervention au locataire

1. Ouvrir le contrat de location.
2. Cliquer sur Maintenance Request.
3. Créer ou ouvrir la demande.
4. Ajouter les produits.
5. Choisir Payment From = Customer.
6. Renseigner le client.
7. Cliquer sur Create Invoice.

### Enregistrer un coût prestataire

1. Ouvrir la demande de maintenance.
2. Ajouter les produits.
3. Choisir Payment From = Vendor.
4. Renseigner le prestataire.
5. Cliquer sur Create Bill.

## 14. Erreurs fréquentes

- "Add Product for create invoice" : aucune ligne produit.
- "Add customer to create invoice" : client manquant.
- "Add vendor to create bill" : prestataire manquant.
- Maintenance introuvable depuis le contrat : elle n'est pas liée au bon contrat.

## 15. Bonnes pratiques

- Toujours lier la demande au bien et au contrat si possible.
- Ajouter une description claire.
- Utiliser des produits de maintenance dédiés.
- Créer le bill prestataire pour suivre la marge réelle.
- Vérifier le paiement des factures avant clôture administrative.

## 16. Questions/Réponses MIA potentielles

- Comment créer une maintenance ?
- Comment lier une maintenance à un contrat ?
- Comment facturer une maintenance au locataire ?
- Comment créer un bill prestataire ?
- Pourquoi la facture de maintenance est refusée ?
- Où voir les maintenances d'un contrat ?
- Comment suivre les maintenances en retard ?
- Que signifie maintenance blocked ?
- Où voir les factures de maintenance ?
- Comment suivre les coûts de maintenance ?
