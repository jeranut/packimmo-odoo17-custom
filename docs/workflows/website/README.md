# Workflow Website

## 1. Objectif métier

Le workflow Website couvre l'affichage public des biens, projets, brochures, filtres de recherche, cartes, formulaires de demande et pages de lots.

Il s'appuie sur `rental_management`, `property_list_dynamic_slider`, `packimmo_property_brochure_layout`, `property_location_esri`, `property_unit_mapping`, `property_land_phase_management`, `packimmo_map_annotations` et `packimmo_rental_custom_fields`.

## 2. Utilisateurs concernés

- Agent commercial qui prépare les biens à publier.
- Responsable marketing.
- Visiteur du site.
- Prospect.
- Administrateur website.

## 3. Menus utilisés

- Properties > Projects > Properties pour préparer les données.
- Properties > Projects > Projects et Sub Projects.
- Website Odoo pour les pages publiques.
- Pages publiques :
  - `/properties-list`
  - `/properties-list?sale_lease=for_tenancy`
  - pages détail / brochure de bien
  - pages projets
  - pages cartes de lots

## 4. Étapes principales

1. Créer le bien ou projet.
2. Renseigner les informations commerciales.
3. Ajouter images, descriptions, équipements, spécifications et connectivités.
4. Renseigner prix, devise d'affichage et option prix sur demande.
5. Renseigner la localisation.
6. Passer le bien hors Draft.
7. Vérifier la liste publique.
8. Vérifier la page détail ou brochure.
9. Pour les lots, préparer la cartographie.
10. Recevoir les demandes via CRM Lead ou formulaires liés.

## 5. Champs importants

Bien :

- Name
- Property For
- Property Type / Sub Type
- Status
- Price
- Website Price On Request
- Website Price Currency
- Foreign Currency / Foreign Price
- Region / City
- Total Area / Usable Area
- Images
- Video URL
- Amenities
- Specifications
- Nearby Connectivities
- Latitude / Longitude
- Brochure URL

Projet :

- Name
- Project For
- Type / Sub Type
- Images
- Description
- Address
- Units

Carte :

- Map Image
- Polygon JSON
- Unit labels
- Annotations

## 6. Boutons et actions

- Copier ou ouvrir l'URL brochure.
- Ouvrir le sélecteur de localisation ESRI.
- Rechercher une adresse.
- Utiliser la position actuelle.
- Voir la carte de lots.
- Modifier, enregistrer, renommer ou supprimer un dessin de lot.
- Filtrer sur le site par vente, location, type, région, projet, prix, surface et recherche texte.

## 7. Règles métier

- Le site liste les biens dont le statut n'est pas Draft.
- Le badge public dépend de l'opération : vente ou location.
- Les prix peuvent être affichés en Ariary, devise étrangère ou sur demande.
- Les formulaires de demande créent ou alimentent des prospects CRM.
- La carte ESRI sauvegarde les coordonnées sur le bien.
- Les cartes de lots utilisent les polygones enregistrés sur les unités.

## 8. Contrôles et blocages

- La localisation d'un bien doit être faite sur un bien enregistré.
- Les filtres dépendent des données réellement renseignées.
- Une carte de lot vide indique souvent que les lignes ou polygones ne sont pas préparés.
- Une image manquante réduit fortement la qualité de la page publique.
- Les biens en Draft ne sont pas visibles publiquement.

## 9. Statuts

Visibilité public :

- Draft : non publié dans la liste principale.
- Available, Booked, On Rent, In Sale, Sold : visibles selon les templates et filtres.

Lot sur carte :

- Couleur calculée selon le statut du bien.

## 10. Rapports ou PDF

- Brochure publique du bien.
- Rapport de bien.
- La page brochure peut inclure la carte ESRI et les informations commerciales.

## 11. Tableaux de bord

Pas de dashboard website dédié identifié. Le suivi marketing se fait par les leads, les listes de biens et les dashboards Properties.

## 12. Sécurité et groupes utilisateurs

- Les visiteurs voient seulement les pages publiques.
- Les utilisateurs internes préparent les données selon leurs droits Properties.
- Les menus backend restent soumis aux groupes PACKIMMO et Odoo.

## 13. Cas d'utilisation complets

### Publier un bien à louer

1. Ouvrir le bien.
2. Renseigner Property For = Rent.
3. Ajouter prix, images, type, région et ville.
4. Passer Available.
5. Ouvrir `/properties-list?sale_lease=for_tenancy`.
6. Vérifier le badge et le prix.

### Préparer une brochure

1. Ouvrir le bien.
2. Ajouter l'image principale et les images secondaires.
3. Ajouter descriptions et équipements.
4. Renseigner la localisation.
5. Ouvrir l'URL brochure.

### Publier une carte de lots

1. Ouvrir le projet.
2. Créer les unités.
3. Importer le plan.
4. Dessiner les lots.
5. Ouvrir la vue website de carte.

## 14. Erreurs fréquentes

- Bien absent du site : statut Draft.
- Prix incorrect : devise website ou prix étranger mal renseigné.
- Carte absente : coordonnées ou polygones manquants.
- Filtres vides : type, région ou projet non renseigné.
- Prospect non lié : demande sans propriété associée.

## 15. Bonnes pratiques

- Toujours ajouter des images nettes.
- Vérifier les prix et devises avant publication.
- Renseigner ville, région et type pour les filtres.
- Tester la page publique après chaque changement important.
- Garder les brochures cohérentes avec les données du bien.

## 16. Questions/Réponses MIA potentielles

- Comment publier un bien sur le site ?
- Pourquoi mon bien n'apparaît pas ?
- Comment afficher un prix en devise étrangère ?
- Comment mettre le prix sur demande ?
- Comment ajouter une localisation ?
- Comment ouvrir la brochure ?
- Quels filtres existent sur la liste des biens ?
- Comment publier une carte de lots ?
- Pourquoi la carte est vide ?
- Où arrivent les demandes du site ?
