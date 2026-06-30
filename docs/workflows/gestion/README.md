# Workflow Gestion

## 1. Objectif métier

Le workflow Gestion regroupe le suivi administratif quotidien : portefeuille de biens, propriétaires, clients, contrats, documents, factures, bills, marges, rapports et suivi après mise en location ou vente.

Il ne remplace pas les workflows Location, Vente ou Comptabilité ; il les relie pour donner une vision opérationnelle.

## 2. Utilisateurs concernés

- Gestionnaire immobilier.
- Responsable administratif.
- Manager.
- Comptable pour consultation des factures.
- Agent location ou vente selon le dossier.

## 3. Menus utilisés

- Properties > Dashboard
- Properties > Projects
- Properties > Vendors
- Properties > Renting
- Properties > Selling
- Properties > Maintenances
- Properties > Reports
- Properties > Configurations

## 4. Étapes principales

1. Créer les référentiels : régions, villes, types, sous-types, services, modèles de contrat.
2. Créer les propriétaires, clients et brokers.
3. Créer les projets, sous-projets et biens.
4. Attacher les documents, images et informations utiles.
5. Suivre les contrats de location et de vente.
6. Suivre les factures, bills, pénalités et marges.
7. Suivre les maintenances.
8. Produire les rapports.

## 5. Champs importants

Contacts :

- User Type : LandLord, Customer ou Broker.
- Téléphone, email.
- CIN, nationalité, NIF, STAT, RCS, forme juridique et représentant si les champs PACKIMMO sont installés.
- Comptes bancaires.

Biens :

- Property Code
- Project / Sub Project
- LandLord
- Status
- Price
- Surface
- Documents
- Images

Contrats :

- Séquence
- Statut
- Client
- Bien
- Dates
- Montants
- Factures
- Bills
- P/L

## 6. Boutons et actions

- Créer sous-projet.
- Créer unités.
- Voir les documents.
- Voir les unités disponibles, vendues ou louées.
- Ouvrir les factures et bills.
- Créer une maintenance.
- Créer une facture supplémentaire.
- Générer les rapports.

## 7. Règles métier

- Les projets peuvent contenir des sous-projets et des unités.
- Les biens héritent de certaines informations du projet ou sous-projet.
- Les contrats alimentent les factures, bills, maintenances et marges.
- Les contacts sont typés pour filtrer propriétaires, clients et brokers.
- La société active influence les données visibles et les valeurs comptables.

## 8. Contrôles et blocages

- Un sous-projet ne peut pas être supprimé s'il contient des biens liés.
- Un projet ou sous-projet ne peut pas passer Available sans unités lorsque le code l'exige.
- Certains champs fiscaux des contacts sont validés par format.
- Les montants négatifs sont bloqués sur plusieurs assistants.
- Les droits et profils de visibilité peuvent masquer des dossiers.

## 9. Statuts

Projet ou sous-projet :

- Draft
- Available

Bien :

- Draft
- Available
- In Booking
- On Rent
- In Sale
- Sold

Contrat location :

- Draft
- Running
- Cancel
- Close
- Expire

Contrat vente :

- Booked
- Refund
- Sold
- Cancel
- Locked

## 10. Rapports ou PDF

- Property Reports.
- Landlord wise Report.
- Rapport de bien.
- Rapport de contrat de location.
- Rapport de vente.
- Factures et bills Odoo.

## 11. Tableaux de bord

Le dashboard Properties regroupe les indicateurs de portefeuille, revenus, contrats, ventes, locations, maintenance et factures. Des dashboards de liste existent aussi pour les contrats.

## 12. Sécurité et groupes utilisateurs

- Packimmo Gestionnaire : suivi administratif et opérationnel.
- Packimmo Manager : supervision et validation.
- Packimmo Administrateur : configuration et sécurité.
- Profil de visibilité : Moi uniquement, Mon équipe, Mon agence, Toute la société ou Tout.

## 13. Cas d'utilisation complets

### Mettre à jour un dossier propriétaire

1. Ouvrir Vendors > Landlords.
2. Vérifier téléphone, email et identité.
3. Ajouter les informations fiscales et bancaires.
4. Contrôler les biens liés.

### Suivre un portefeuille

1. Ouvrir le dashboard.
2. Filtrer par société ou période si disponible.
3. Ouvrir les contrats en retard.
4. Vérifier les factures et maintenances.

### Préparer un dossier administratif

1. Ouvrir le bien.
2. Ajouter les documents et images.
3. Vérifier propriétaire, projet, surface et prix.
4. Contrôler le mandat ou contrat selon le workflow.

## 14. Erreurs fréquentes

- Un utilisateur ne voit pas un bien : droits, société active ou profil de visibilité.
- Un contact n'apparaît pas comme propriétaire : User Type incorrect.
- Un rapport est vide : aucune donnée dans la période ou mauvaise société.
- Un sous-projet ne se supprime pas : unités liées.

## 15. Bonnes pratiques

- Mettre à jour les contacts avant les contrats.
- Utiliser les documents attachés plutôt que des fichiers externes.
- Maintenir les régions, villes et sous-types propres.
- Contrôler les droits avant de conclure à une absence de données.
- Utiliser les smart buttons pour garder la traçabilité.

## 16. Questions/Réponses MIA potentielles

- Où gérer les propriétaires ?
- Comment retrouver les biens d'un propriétaire ?
- Pourquoi je ne vois pas tous les biens ?
- Comment suivre les bills d'un contrat ?
- Où trouver les rapports propriétaire ?
- Comment créer un sous-projet ?
- Comment créer des unités ?
- Où voir les marges d'un contrat ?
- Comment vérifier les droits d'un utilisateur ?
- Que faire si un dashboard est vide ?
