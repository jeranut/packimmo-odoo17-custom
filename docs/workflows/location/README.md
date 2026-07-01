# Workflow Location

## 1. Objectif métier

Le workflow Location couvre le cycle complet d'un bien destiné à être loué : création du bien, mandat de location, publication, prospects, visites, contrat de bail, factures de loyer, maintenance, renouvellement et clôture.

Ce guide se base sur les modules `rental_management`, `packimmo_property_mandate`, `packimmo_project_location_workflow`, `packimmo_habitation_contract`, `packimmo_rental_custom_fields` et `packimmo_access_roles`.

## 2. Utilisateurs concernés

- Agent location : crée et suit les biens à louer, prospects, visites et contrats.
- Gestionnaire : suit les contrats, loyers, factures, maintenances et dossiers administratifs.
- Manager : supervise les dossiers et les tableaux de bord.
- Administrateur : configure les produits, modèles, droits et paramètres.

## 3. Menus utilisés

- Properties > Dashboard
- Properties > Projects > Properties
- Properties > Leads
- Properties > Renting > Contracts
- Properties > Renting > Invoices
- Properties > Renting > Bills
- Properties > Renting > Penalties
- Properties > Vendors > Landlords / Customers / Brokers
- Properties > Maintenances
- Properties > Reports
- Properties > Configurations
- Menu Mandats ajouté dans Location et Vente par le module de mandat.
- Projet Odoo `LOCATION` pour le suivi opérationnel par étapes.

## 4. Étapes principales

1. Créer le propriétaire dans les contacts avec le type LandLord.
2. Créer le bien avec Property For = Rent.
3. Renseigner le loyer, l'unité de loyer, le type, le sous-type, la surface, l'adresse et les images.
4. Créer un mandat de location si le bien appartient à un propriétaire externe.
5. Imprimer le mandat.
6. Faire signer le mandat par le propriétaire.
7. Téléverser le mandat signé depuis le bouton du mandat.
8. Vérifier que le document signé est classé automatiquement dans la GED Location / année / mois / Mandats et que la synchronisation Google Drive est en attente ou effectuée.
9. Soumettre, approuver puis activer le mandat.
10. Passer le bien en Available.
11. Publier le bien sur le site si les informations web sont renseignées.
12. Recevoir ou créer un prospect lié au bien.
13. Planifier une visite depuis le projet LOCATION.
14. Valider la visite et compléter le mandat avec le locataire retenu.
15. Créer le contrat de location depuis l'assistant de contrat.
16. Activer le contrat pour générer la première facture.
17. Suivre les factures, bills, pénalités et maintenances.
18. Renouveler, clôturer ou annuler le contrat.

## 5. Champs importants

Sur le bien :

- Name
- Property For = Rent
- Property Type et Property Sub Type
- Status
- LandLord
- Price
- Rent Unit : Day, Month ou Year
- Region, City, adresse, latitude et longitude
- Total Area, Usable Area
- Website Price On Request
- Website Price Currency, Foreign Currency, Foreign Price
- Images, documents, amenities, specifications, floor plans et nearby connectivities

Sur le mandat :

- Type d'opération
- Type de mandat
- Propriétaire
- Bien
- Date de début, durée, date de fin
- Base honoraires location
- Pourcentage commission et taxe
- Facturé à
- Locataire trouvé
- Type de caution et montant calculé
- Compte bancaire de réception du loyer
- Mandat signé uploadé
- Document GED du mandat signé
- Nom et date de téléversement du fichier signé

Sur le contrat :

- Customer
- Property
- Rent Unit
- Total Rent
- Deposit / Security Deposit
- Payment Term
- Duration ou Date de fin
- Start Date
- Broker
- Agreement Template
- Taxes
- Services, maintenance et pénalités

## 6. Boutons et actions

- Sur le bien : passer en Draft, Available, créer contrat, créer maintenance, ouvrir mandat.
- Sur le mandat : Soumettre, Approuver, Activer, Expirer, Annuler, Imprimer le mandat, Téléverser mandat signé, Ouvrir document GED, Terminer et facturer.
- Sur le contrat : Active, Create Invoice, Ajouter un frais, Extend Contract, Maintenance Request, Close Contract, Cancel.
- Sur les lignes d'échéance : Create Invoice.
- Dans LOCATION : Planifier une visite, Valider visite, Annuler visite, passer vers contrat ou état des lieux selon les règles.

## 7. Règles métier

- Un bien en location utilise techniquement `sale_lease = for_tenancy`.
- Les biens peuvent être Draft, Available, In Booking, On Rent, In Sale ou Sold.
- Le contrat de location est créé sur `tenancy.details`.
- Un contrat actif passe le bien en On Rent.
- Un bien externe ne peut pas passer en Available tant que le mandat de location actif n'a pas de mandat signé téléversé.
- Le mandat signé téléversé crée automatiquement une pièce jointe, un `document.file` GED et une entrée de synchronisation Google Drive si le connecteur est activé.
- Le document GED du mandat signé est classé dans Location / année / mois / Mandats.
- Le paiement peut être mensuel, trimestriel, semestriel, annuel, quotidien ou en paiement complet.
- Les services et maintenances peuvent être fusionnés avec les échéances ou facturés séparément.
- Les pénalités sont créées par planificateur si la configuration les active.
- Le module de bail habitation génère un PDF habitation pour les biens résidentiels et commercial pour les autres types.

## 8. Contrôles et blocages

- La date de fin du contrat doit être supérieure ou égale à la date de début.
- Les périodes de contrat actif ne doivent pas se chevaucher sur le même bien.
- Les montants de loyer, dépôt, commission et pourcentage ne doivent pas être négatifs.
- Un contrat Running ou Expired ne peut pas être supprimé directement ; il faut le clôturer ou l'annuler.
- La clôture est bloquée si des loyers restent impayés.
- Pour un bien externe, le module mandat impose un mandat actif avant disponibilité.
- La disponibilité est aussi bloquée si le mandat actif n'a pas de document signé lié dans la GED.
- Si Google Drive est activé, la disponibilité exige que le document signé soit déjà synchronisé ou présent dans la queue `packimmo.google.drive.sync.queue`.
- Le message affiché est : "Veuillez d’abord téléverser le mandat signé avant de rendre le bien disponible."
- Le blocage s'applique aussi si l'utilisateur modifie directement le statut du bien vers Available.
- Le workflow LOCATION bloque les retours arrière manuels entre les étapes sensibles.
- Depuis CONTRAT vers ETAT DES LIEUX, un contrat actif lié au bien est obligatoire.

## 9. Statuts

Bien :

- Draft
- Available
- In Booking
- On Rent
- In Sale
- Sold

Contrat de location :

- Draft
- Running
- Cancel
- Close
- Expire

Mandat :

- Brouillon
- A valider
- Approuvé
- Actif
- Terminé
- Expiré
- Annulé

Projet LOCATION :

- BIENS DISPONIBLE
- VISITE
- REGULARISATION MANDAT
- CONTRAT
- ETAT DES LIEUX
- FIN
- VISITES PERDUE

## 10. Rapports ou PDF

- Rapport contrat de location.
- Rapport rappel de contrat.
- PDF mandat.
- PDF contrat de bail habitation ou commercial si le module est installé.
- Rapports Excel Property Reports et Landlord wise Report.

## 11. Tableaux de bord

Le dashboard immobilier affiche des indicateurs sur les biens, contrats, ventes, locations, factures et maintenance. Les vues liste de contrats utilisent aussi des dashboards dédiés côté interface.

## 12. Sécurité et groupes utilisateurs

- Groupes historiques : Property Rental Manager et Property Rental Officer.
- Groupes PACKIMMO : Location, Gestionnaire, Manager et Administrateur.
- Le profil de visibilité PACKIMMO peut limiter les données à soi-même, son équipe, son agence, sa société ou tout le périmètre.
- Les options de visibilité peuvent inclure les brouillons, archives, contrats terminés, biens loués et biens vendus.

## 13. Cas d'utilisation complets

### Louer un appartement

1. Créer le propriétaire.
2. Créer le bien en Rent.
3. Ajouter l'adresse, le type, le loyer et les images.
4. Créer le mandat.
5. Imprimer le mandat et le faire signer.
6. Téléverser le mandat signé.
7. Vérifier le statut "Mandat signé uploadé" et le document GED.
8. Activer le mandat.
9. Passer le bien Available.
10. Publier le bien.
11. Créer le prospect.
12. Planifier puis valider la visite.
13. Créer le contrat.
14. Activer le contrat.
15. Vérifier la première facture.

### Renouveler un bail

1. Ouvrir le contrat Running.
2. Utiliser Extend Contract.
3. Renseigner la nouvelle durée et, si besoin, l'augmentation.
4. Valider le nouveau contrat.
5. Vérifier les références Extend From et Extend Ref.

### Clôturer un contrat

1. Ouvrir le contrat.
2. Vérifier que les factures sont payées.
3. Cliquer sur Close Contract.
4. Confirmer que le bien repasse Available.

## 14. Erreurs fréquentes

- Impossible de rendre le bien disponible : mandat actif manquant.
- Impossible de rendre le bien disponible : mandat signé non téléversé ou document GED/queue Drive manquant.
- Contrat impossible : période déjà couverte par un contrat actif.
- Clôture impossible : factures de loyer non soldées.
- Payment Term refusé : l'unité de loyer ne correspond pas au terme choisi.
- Facture de maintenance impossible : aucun produit de maintenance n'a été ajouté.

## 15. Bonnes pratiques

- Toujours vérifier propriétaire, téléphone, email et société.
- Créer, imprimer, faire signer et téléverser le mandat avant la publication.
- Contrôler le bouton "Ouvrir document GED" avant de passer le bien Available.
- Ajouter au moins une image claire.
- Lier les prospects au bien.
- Utiliser les boutons du workflow au lieu de déplacer les tâches manuellement.
- Activer le contrat dès signature.
- Contrôler la première facture après activation.
- Créer les maintenances depuis le bien ou le contrat.

## 16. Questions/Réponses MIA potentielles

- Comment créer un bien à louer ?
- Pourquoi mon bien ne passe pas disponible ?
- Comment créer un mandat de location ?
- Comment planifier une visite ?
- Comment créer un contrat de location ?
- Que fait le bouton Active sur un contrat ?
- Où trouver les factures de loyer ?
- Comment créer une facture supplémentaire ?
- Comment clôturer un contrat ?
- Pourquoi le workflow LOCATION bloque un retour arrière ?
