# Workflow Dashboard

## 1. Objectif métier

Le workflow Dashboard permet de piloter l'activité immobilière : portefeuille, contrats, revenus, factures, ventes, locations, maintenance et indicateurs de santé.

Il s'appuie sur les composants backend de `rental_management` et les extensions d'affichage de `packimmo_rental_custom_fields`.

## 2. Utilisateurs concernés

- Manager.
- Responsable location.
- Responsable vente.
- Gestionnaire.
- Direction.

## 3. Menus utilisés

- Properties > Dashboard
- Properties > Renting > Contracts
- Properties > Selling > Contracts
- Properties > Maintenances > Request
- Listes enrichies avec dashboards de contrats.

## 4. Étapes principales

1. Ouvrir Properties > Dashboard.
2. Sélectionner la société active si nécessaire.
3. Analyser les indicateurs globaux.
4. Ouvrir les contrats ou factures en anomalie.
5. Vérifier les maintenances en retard.
6. Utiliser les listes de contrats pour détailler les statuts.

## 5. Champs importants

Les indicateurs calculés utilisent notamment :

- Property Status
- Contract Type
- Sale Stage
- Payment State
- Invoice Date
- Amount
- Maintenance State
- Company
- Property Type
- Project
- Customer / Landlord

## 6. Boutons et actions

- Ouvrir les menus depuis les cartes ou listes.
- Filtrer et grouper les listes.
- Utiliser les smart buttons sur contrats et biens.
- Changer de société dans Odoo pour modifier le périmètre.

## 7. Règles métier

- Les dashboards lisent les données existantes : biens, contrats, factures, bills et maintenances.
- Les indicateurs sont dépendants de la société et des droits de l'utilisateur.
- Les contrats location et vente ont des dashboards de liste dédiés.
- Les maintenances utilisent les états Odoo et les dates planifiées.

## 8. Contrôles et blocages

- Un indicateur vide peut venir d'une absence de données, d'un mauvais périmètre société ou de droits insuffisants.
- Les factures non postées peuvent ne pas être prises en compte dans certains calculs comptables.
- Les données de marge nécessitent des factures et bills liés.

## 9. Statuts suivis

Biens :

- Draft
- Available
- Booked
- On Rent
- In Sale
- Sold

Location :

- Draft
- Running
- Close
- Cancel
- Expire

Vente :

- Booked
- Refund
- Sold
- Cancel
- Locked

Maintenance :

- In Progress
- Blocked
- Done
- Cancelled
- Corrective
- Preventive

## 10. Rapports ou PDF

Le dashboard n'est pas un rapport PDF. Les rapports associés se trouvent dans Properties > Reports et dans les factures ou contrats.

## 11. Tableaux de bord

Indicateurs identifiés dans le code :

- Portefeuille immobilier.
- Contrats de location.
- Contrats de vente.
- Revenus.
- Factures.
- Bills.
- Marges.
- Maintenance.
- Demandes dues aujourd'hui et en retard.
- Répartition par type de bien ou statut.

## 12. Sécurité et groupes utilisateurs

- Packimmo Manager est le rôle naturel pour consulter les tableaux de bord.
- Les droits historiques Property Rental Manager / Officer donnent accès au menu principal.
- Les profils de visibilité peuvent restreindre les résultats.
- La société active influence le périmètre.

## 13. Cas d'utilisation complets

### Suivre les impayés

1. Ouvrir Dashboard.
2. Identifier les factures en retard ou montants restants.
3. Ouvrir les contrats concernés.
4. Vérifier les factures liées.

### Suivre la maintenance

1. Ouvrir Dashboard.
2. Regarder les maintenances dues aujourd'hui ou en retard.
3. Ouvrir la demande.
4. Vérifier équipe, client, prestataire et facture.

### Suivre les ventes

1. Ouvrir Selling > Contracts.
2. Utiliser le dashboard de liste.
3. Filtrer par Booked, Sold ou Refund.

## 14. Erreurs fréquentes

- Dashboard vide : pas de données dans la société active.
- Revenus incomplets : factures non créées ou non liées.
- Maintenance en retard incorrecte : date planifiée manquante ou ancienne.
- Contrats absents : droits ou profil de visibilité.

## 15. Bonnes pratiques

- Vérifier la société active avant analyse.
- Utiliser les filtres et groupements.
- Contrôler les factures non postées.
- Examiner les données source avant de conclure.
- Réserver le dashboard au pilotage ; faire les corrections dans les fiches métier.

## 16. Questions/Réponses MIA potentielles

- Où voir le dashboard ?
- Pourquoi mon dashboard est vide ?
- Comment suivre les impayés ?
- Comment voir les biens loués ?
- Comment voir les ventes confirmées ?
- Comment suivre les maintenances en retard ?
- Pourquoi les revenus ne correspondent pas ?
- Quel rôle donne accès au dashboard ?
- Comment filtrer par société ?
- Où voir la marge d'un contrat ?
