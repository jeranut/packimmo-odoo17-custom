# Workflow Vente

## 1. Objectif métier

Le workflow Vente couvre la commercialisation d'un bien à vendre : création du bien, mandat de vente, prospect, réservation, contrat de vente, factures, pénalités, confirmation de vente et suivi du bien vendu.

Ce guide s'appuie sur `rental_management`, `packimmo_property_mandate`, `packimmo_project_location_workflow`, `packimmo_rental_custom_fields` et les rapports associés.

## 2. Utilisateurs concernés

- Agent commercial vente.
- Responsable commercial.
- Gestionnaire administratif.
- Comptable pour le suivi des factures.
- Manager.

## 3. Menus utilisés

- Properties > Projects > Properties
- Properties > Leads
- Properties > Selling > Contracts
- Properties > Selling > Invoices
- Properties > Selling > Penalties
- Properties > Vendors > Customers
- Properties > Vendors > Brokers
- Properties > Reports
- Mandats dans le menu de vente si le module mandat est installé.
- Projet de workflow vente créé par `packimmo_project_location_workflow` lorsque configuré.

## 4. Étapes principales

1. Créer ou vérifier le propriétaire.
2. Créer le bien avec Property For = Sale.
3. Renseigner le prix, la surface, le type, l'adresse, le projet et les médias.
4. Créer le mandat de vente si nécessaire.
5. Rendre le bien disponible.
6. Recevoir ou créer un lead.
7. Réserver le bien ou créer un contrat de vente.
8. Créer la facture d'acompte si une réservation est utilisée.
9. Créer les échéances de vente.
10. Confirmer la vente.
11. Suivre les factures, pénalités et commissions broker.

## 5. Champs importants

Sur le bien :

- Property For = Sale
- Price
- Property Type et Property Sub Type
- LandLord
- Project / Sub Project
- Region, City, adresse
- Total Area et Usable Area
- Website Price On Request
- Images et brochure

Sur le contrat de vente :

- Property
- Customer
- Stage
- Book Price
- Confirmed Sale Price
- Ask Price
- Payment Term : Monthly, Full Payment ou Quarterly
- Broker, commission, commission type, commission from
- Taxes
- Sale invoices
- Sold Document
- Term and Condition
- Pénalités

## 6. Boutons et actions

- Sur le bien : passer Available, In Sale, créer contrat ou réservation.
- Sur le contrat de vente : créer facture d'acompte, rembourser, annuler, verrouiller, recevoir le paiement restant, réinitialiser les échéances, confirmer la vente.
- Sur une échéance de vente : Create Invoice.
- Sur les maintenances liées : ouvrir les demandes.
- Sur le mandat : Soumettre, Approuver, Activer, Imprimer, Terminer et facturer.

## 7. Règles métier

- Un bien à vendre utilise `sale_lease = for_sale`.
- Le contrat de vente est enregistré sur `property.vendor`.
- La réservation place le contrat en Booked et le bien en Booked.
- La confirmation de vente passe le contrat en Sold et le bien en Sold.
- Une commission broker peut générer une facture fournisseur et une facture client ou propriétaire.
- Les échéances de vente peuvent être créées puis facturées.
- Les pénalités de vente peuvent être générées sur facture en retard si la configuration du contrat le prévoit.

## 8. Contrôles et blocages

- Un contrat de vente ne peut être supprimé que s'il est annulé.
- La confirmation de vente demande des échéances ; sinon une notification indique de créer les installments.
- La validation de paiement par chèque peut demander une référence chèque et une observation selon les champs personnalisés.
- Les contraintes de mandat peuvent bloquer certaines actions si le mandat n'est pas régularisé.

## 9. Statuts

Bien :

- Draft
- Available
- In Booking
- In Sale
- Sold

Contrat de vente :

- Booked
- Refund
- Sold
- Cancel
- Locked

Mandat :

- Brouillon
- A valider
- Approuvé
- Actif
- Terminé
- Expiré
- Annulé

## 10. Rapports ou PDF

- Rapport de bien.
- Rapport de vente.
- Factures client.
- Mandat de vente.
- Contrat de mandat exclusif si les champs requis sont renseignés.
- Rapports Excel Property Reports et Landlord wise Report.

## 11. Tableaux de bord

Les tableaux de bord de vente affichent notamment des compteurs par statut de contrat et par type de bien. Le dashboard global Properties regroupe les indicateurs immobiliers.

## 12. Sécurité et groupes utilisateurs

- Property Rental Manager et Property Rental Officer donnent accès au menu Properties.
- Les groupes PACKIMMO Vente, Manager et Administrateur peuvent être utilisés par le moteur de sécurité PACKIMMO.
- Les profils de visibilité limitent le périmètre utilisateur.

## 13. Cas d'utilisation complets

### Vendre un terrain

1. Créer le bien en Sale.
2. Renseigner le prix et les informations terrain.
3. Activer le mandat de vente.
4. Passer le bien Available.
5. Enregistrer le prospect.
6. Créer un contrat de vente.
7. Créer la facture d'acompte si besoin.
8. Ajouter les échéances.
9. Confirmer la vente.
10. Contrôler les factures.

### Annuler une vente

1. Ouvrir le contrat de vente.
2. Cliquer sur Cancel.
3. Vérifier que le bien repasse Available.

### Encaisser le reste à payer

1. Ouvrir le contrat.
2. Cliquer sur Receive Remaining.
3. Le système crée une ligne de facture restante et supprime les échéances non facturées.

## 14. Erreurs fréquentes

- Confirmation impossible : aucune échéance n'existe.
- Suppression impossible : le contrat n'est pas annulé.
- Chèque refusé : référence ou observation manquante.
- Facture non créée : l'échéance est déjà facturée ou les produits de configuration sont absents.

## 15. Bonnes pratiques

- Vérifier le prix avant réservation.
- Renseigner le client et le broker avant facturation.
- Garder les documents de vente attachés au contrat.
- Ne confirmer la vente qu'après vérification des échéances.
- Utiliser les statuts Cancel ou Refund plutôt que supprimer.

## 16. Questions/Réponses MIA potentielles

- Comment créer un bien à vendre ?
- Comment réserver un bien ?
- Comment confirmer une vente ?
- Pourquoi la vente ne se confirme pas ?
- Où trouver les factures de vente ?
- Comment créer une facture d'acompte ?
- Comment annuler un contrat de vente ?
- Que signifie le statut Locked ?
- Comment gérer une commission broker ?
- Pourquoi je ne peux pas supprimer un contrat de vente ?
