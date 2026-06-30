# Workflow Administration / Sécurité

## 1. Objectif métier

Le workflow Administration / Sécurité permet de configurer les utilisateurs, groupes, profils de visibilité, menus, paramètres métier, produits comptables et base de connaissance MIA.

Il s'appuie sur `packimmo_access_roles`, `web_responsive`, `rental_management`, `packimmo_rental_custom_fields` et `packimmo_odoobot_assistant`.

## 2. Utilisateurs concernés

- Administrateur PACKIMMO.
- Responsable sécurité.
- Manager.
- Référent métier MIA.
- Administrateur Odoo.

## 3. Menus utilisés

- Settings > Users & Companies > Users.
- Properties > Configurations.
- Menu sécurité PACKIMMO.
- MIA > Workflows.
- MIA > Articles.
- MIA > Catégories.
- MIA > Médias.
- MIA > Questions sans réponse.
- MIA > Synchronisation.
- MIA > Statistiques.
- Paramètres MIA dans la configuration Odoo.

## 4. Étapes principales

1. Créer l'utilisateur Odoo.
2. Affecter les groupes PACKIMMO nécessaires.
3. Choisir le profil de visibilité.
4. Configurer les permissions spécifiques si besoin.
5. Configurer les raccourcis ou menus visibles.
6. Configurer les paramètres Properties : produits, mails, rappels, couleurs.
7. Configurer les paramètres MIA.
8. Synchroniser les datasets MIA si la base de connaissance est utilisée.
9. Suivre les questions sans réponse.

## 5. Champs importants

Utilisateur :

- Groupes Odoo et PACKIMMO.
- Profil de visibilité Packimmo.
- Options : voir les archives, brouillons, contrats terminés, biens vendus, biens loués.
- Résumé des rôles.

Profil d'accès :

- Nom.
- Société.
- Scope : Moi uniquement, Mon équipe, Mon agence, Toute la société, Tout.
- Options de visibilité.

Matrice de permission :

- Module.
- Modèle.
- Groupe.
- Lecture.
- Création.
- Modification.
- Suppression.
- Validation.
- Export.
- Impression.

MIA :

- Chemin des datasets.
- Options de synchronisation.
- Articles, catégories, médias.
- Questions sans réponse.

## 6. Boutons et actions

- Scanner ou consulter les objets de sécurité.
- Modifier les permissions.
- Gérer les profils.
- Créer l'arborescence datasets MIA.
- Synchroniser les datasets MIA.
- Importer un ZIP de datasets.
- Marquer une question MIA comme analysée, traitée ou ignorée.
- Créer un article depuis une question sans réponse.
- Lier une question à un article existant.

## 7. Règles métier

- Les groupes PACKIMMO complètent les groupes Odoo.
- Le profil de visibilité limite le périmètre des données.
- Une permission spécifique société peut être prioritaire sur une permission globale.
- MIA utilise des workflows, catégories et articles synchronisés depuis des datasets.
- Les questions sans réponse sont conservées pour enrichir la base.
- Les médias MIA ajoutés manuellement doivent être conservés par la synchronisation.

## 8. Contrôles et blocages

- Certaines permissions ne peuvent pas être dupliquées pour le même couple module, modèle, groupe et société.
- Les chemins d'import MIA sont sécurisés.
- Un ZIP MIA invalide ou dangereux est refusé.
- Un dataset sans workflow est refusé.
- Une catégorie MIA doit appartenir au même workflow que son article.
- Les champs fiscaux des contacts PACKIMMO sont validés.

## 9. Statuts

Question sans réponse MIA :

- New
- In Review
- Done
- Ignored

Articles MIA :

- Actif ou inactif.
- Suggéré ou non suggéré.

Objets métier :

- Les statuts restent ceux des workflows Location, Vente, Syndic, Maintenance et Morcellement.

## 10. Rapports ou PDF

Ce workflow ne produit pas de PDF métier dédié. Il configure les rapports des autres workflows : contrats, mandats, factures, brochures et exports.

## 11. Tableaux de bord

- Statistiques MIA.
- Menus de sécurité PACKIMMO.
- Dashboard Properties accessible selon droits.

## 12. Sécurité et groupes utilisateurs

Groupes PACKIMMO identifiés :

- Vente.
- Location.
- Morcellement.
- Dessinateur.
- Gestionnaire.
- Manager.
- Administrateur.

Groupes historiques :

- Property Rental Manager.
- Property Rental Officer.

Le module `web_responsive` ajoute une interface responsive, raccourcis d'applications et options utilisateur ; il ne remplace pas les droits métier.

## 13. Cas d'utilisation complets

### Donner accès à un agent location

1. Ouvrir la fiche utilisateur.
2. Ajouter le groupe Packimmo Location.
3. Choisir le profil de visibilité adapté.
4. Vérifier la société active.
5. Tester l'accès aux biens, contrats et projet LOCATION.

### Créer un profil manager

1. Créer ou ouvrir le profil d'accès.
2. Choisir un scope large.
3. Activer les options nécessaires.
4. Affecter le profil au manager.
5. Vérifier le dashboard.

### Synchroniser MIA

1. Ouvrir MIA > Synchronisation.
2. Vérifier le chemin des datasets.
3. Choisir les options.
4. Lancer la synchronisation.
5. Lire le rapport.
6. Contrôler les questions sans réponse.

## 14. Erreurs fréquentes

- Utilisateur sans accès : groupe ou profil manquant.
- Données invisibles : société active ou scope trop restrictif.
- Menu absent : permissions menu ou groupe insuffisants.
- Synchronisation MIA refusée : chemin ou ZIP invalide.
- Article MIA refusé : workflow ou catégorie incohérent.

## 15. Bonnes pratiques

- Donner le minimum de droits nécessaires.
- Utiliser les profils plutôt que modifier chaque accès isolément.
- Tester avec un utilisateur réel après changement de droits.
- Documenter les profils standards.
- Synchroniser MIA après validation des contenus métier.
- Ne pas supprimer les questions sans réponse sans traitement.

## 16. Questions/Réponses MIA potentielles

- Quel groupe donner à un agent location ?
- Quel groupe donner à un responsable ?
- Pourquoi un utilisateur ne voit pas un bien ?
- Comment limiter un utilisateur à son agence ?
- Où configurer les produits de facturation ?
- Comment synchroniser MIA ?
- Où voir les questions sans réponse ?
- Comment créer un article MIA depuis une question ?
- Pourquoi un menu n'apparaît pas ?
- Quelle différence entre groupe et profil de visibilité ?
