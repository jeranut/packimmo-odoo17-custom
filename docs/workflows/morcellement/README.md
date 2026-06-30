# Workflow Morcellement

## 1. Objectif métier

Le workflow Morcellement sert à gérer un projet terrain découpé en lots ou unités : création du projet, sous-projets ou phases, génération des unités, cartographie interactive, publication et suivi commercial des lots.

Il s'appuie sur `rental_management`, `property_unit_mapping`, `property_land_phase_management`, `packimmo_map_annotations` et les extensions de champs PACKIMMO.

## 2. Utilisateurs concernés

- Responsable morcellement.
- Agent commercial terrain.
- Dessinateur ou utilisateur chargé de la cartographie.
- Manager.
- Administrateur.

## 3. Menus utilisés

- Properties > Projects > Projects
- Properties > Projects > Sub Projects
- Properties > Projects > Properties
- Assistants Create Subproject et Create Units.
- Boutons de cartographie sur projet ou sous-projet.
- Pages website de cartographie des lots.

## 4. Étapes principales

1. Créer le projet terrain.
2. Renseigner le titre, le nom du terrain, le type, la région, la surface et les valeurs.
3. Créer les sous-projets ou phases si nécessaire.
4. Créer les unités depuis l'assistant.
5. Importer une image ou ouvrir l'éditeur de cartographie si plusieurs unités existent.
6. Dessiner ou modifier les polygones des lots.
7. Ajouter les légendes et zones d'intérêt si le module d'annotations est installé.
8. Publier la carte ou la page des lots.
9. Suivre les lots disponibles, réservés, vendus ou loués.

## 5. Champs importants

Projet et sous-projet :

- Name
- Code / Project Sequence
- Property Type
- Property Sub Type
- Land name
- Title number
- Region, City, adresse
- Total Property Area
- Available Area
- Total Value of Project
- Status
- Land Phase Map Background
- Map Image
- Phase Polygon

Unité :

- Property Code
- Name
- Property For
- Status
- Project / Sub Project
- Total Area
- Price
- Réf Plan
- Map Polygon JSON
- Map Color

Cartographie :

- Map Image Filename
- Polygon JSON
- Note
- Unit Map Label
- Légendes avec flèches
- Zones d'intérêt

## 6. Boutons et actions

- Create Subproject.
- Create Units.
- Import Image / Cartographie.
- Import and Open Map.
- Open Unit Map Editor.
- View Unit Map Website.
- Prepare Unit Map Lines.
- Modifier dessin.
- Enregistrer dessin.
- Renommer.
- Supprimer dessin.
- Finaliser.
- Ajouter ou gérer légendes et zones d'intérêt.

## 7. Règles métier

- La cartographie est disponible lorsqu'il y a plusieurs unités.
- Une ligne de carte doit être liée à une unité du même projet.
- Les couleurs de carte dépendent du statut du bien.
- Les phases peuvent utiliser le fond de carte du projet, du sous-projet ou une image dédiée selon le champ `land_phase_map_background`.
- Les annotations doivent être liées à un projet ou à un sous-projet.

## 8. Contrôles et blocages

- La cartographie ouverte depuis l'assistant demande un projet ou sous-projet actif.
- Si une seule unité existe, l'import cartographie peut être refusé.
- Une unité sélectionnée dans une ligne de carte doit appartenir au projet.
- Un polygone de bien doit être cohérent et unique selon les contraintes du modèle.
- Une légende ou zone d'intérêt sans projet ni sous-projet est refusée.
- Le titre foncier est obligatoire pour certains projets terrain selon les validations PACKIMMO.

## 9. Statuts

Projet ou sous-projet :

- Draft
- Available

Lots / biens :

- Draft
- Available
- In Booking
- In Sale
- Sold
- On Rent

## 10. Rapports ou PDF

- Rapport de bien.
- Brochure de bien.
- Pages website de lots avec carte.
- Les rapports de vente ou location s'appliquent aux lots selon leur workflow commercial.

## 11. Tableaux de bord

Les smart buttons de projet affichent les unités, unités disponibles, vendues et louées. Le dashboard global peut afficher les volumes de biens selon statut.

## 12. Sécurité et groupes utilisateurs

- Packimmo Morcellement : suivi des projets terrain et lots.
- Packimmo Dessinateur : cartographie et dessin si configuré.
- Packimmo Vente ou Location selon le devenir commercial du lot.
- Packimmo Manager : supervision.

## 13. Cas d'utilisation complets

### Créer un morcellement simple

1. Créer le projet terrain.
2. Renseigner les informations administratives.
3. Cliquer sur Create Units.
4. Indiquer le nombre d'unités et le préfixe.
5. Ouvrir la cartographie.
6. Importer le plan.
7. Dessiner les lots.
8. Enregistrer les dessins.

### Modifier le dessin d'un lot

1. Ouvrir la carte du projet.
2. Sélectionner le lot.
3. Cliquer sur Modifier dessin.
4. Ajuster le polygone.
5. Cliquer sur Enregistrer dessin.

### Préparer une phase

1. Créer ou ouvrir le sous-projet.
2. Choisir le fond de carte de phase.
3. Préparer les lignes de carte.
4. Publier la vue website si nécessaire.

## 14. Erreurs fréquentes

- Cartographie indisponible : pas assez d'unités.
- Lot refusé : l'unité ne dépend pas du projet.
- Annotation refusée : pas de projet ou sous-projet lié.
- Projet bloqué : titre ou informations terrain manquants.
- Carte vide : lignes de carte non préparées.

## 15. Bonnes pratiques

- Créer les unités avant d'ouvrir la cartographie.
- Utiliser des codes de lot clairs.
- Vérifier les surfaces avant publication.
- Enregistrer les dessins après chaque modification importante.
- Ne pas mélanger les unités de projets différents.
- Utiliser les annotations pour clarifier les accès, zones et repères.

## 16. Questions/Réponses MIA potentielles

- Comment créer un projet de morcellement ?
- Comment créer les lots d'un projet ?
- Pourquoi la cartographie ne s'ouvre pas ?
- Comment importer un plan ?
- Comment dessiner un lot ?
- Comment modifier le dessin d'un lot ?
- Comment ajouter une légende ?
- Pourquoi mon lot n'apparaît pas sur la carte ?
- Comment publier une carte de lots ?
- Que signifient les couleurs des lots ?
