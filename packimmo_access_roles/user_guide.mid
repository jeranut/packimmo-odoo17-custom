# Guide utilisateur - Packimmo Access Roles

## 1. Objectif du module

`packimmo_access_roles` ajoute une couche de rôles métier pour Packimmo afin de mieux organiser les accès des utilisateurs de `rental_management`.

Le module crée les groupes suivants :

- Utilisateur Packimmo
- Packimmo Vente
- Packimmo Location
- Packimmo Morcellement
- Packimmo Dessinateur
- Packimmo Gestionnaire
- Packimmo Manager
- Packimmo Administrateur

Ces groupes apparaissent dans la fiche utilisateur et peuvent aussi être utilisés dans le module `access_roles` pour créer des rôles configurables.

## 2. Pourquoi ce module est nécessaire

Le module `access_roles` ne crée pas automatiquement des rôles métier propres à Packimmo. Il affiche seulement les groupes Odoo existants.

Si `rental_management` ne fournit pas de groupes séparés pour la vente, la location, le morcellement ou le dessin, il devient difficile de créer un rôle propre pour chaque service.

Ce module corrige ce manque en ajoutant une catégorie `Packimmo` et des groupes clairs par métier.

## 3. Installation

1. Copier le dossier `packimmo_access_roles` dans ton dossier d'addons.
2. Vérifier que les modules suivants sont installés :
   - `access_roles`
   - `rental_management`
   - `project`
3. Redémarrer Odoo.
4. Mettre à jour la liste des applications.
5. Installer `Packimmo Access Roles`.

Commande possible :

```bash
./odoo-bin -c /etc/odoo17.conf -d NOM_BASE -u packimmo_access_roles --stop-after-init
```

## 4. Utilisation dans la fiche utilisateur

Aller dans :

**Paramètres > Utilisateurs & Sociétés > Utilisateurs**

Ouvrir un utilisateur, puis attribuer un ou plusieurs groupes Packimmo :

- `Packimmo Vente` pour les agents commerciaux vente.
- `Packimmo Location` pour les agents location.
- `Packimmo Morcellement` pour les responsables terrain, phases et lots.
- `Packimmo Dessinateur` pour les personnes qui dessinent ou annotent les plans.
- `Packimmo Gestionnaire` pour la gestion, le syndic, les contrats et le suivi administratif.
- `Packimmo Manager` pour les responsables opérationnels.
- `Packimmo Administrateur` pour les administrateurs Packimmo.

Un champ `Résumé des rôles Packimmo` s'affiche sur la fiche utilisateur pour vérifier rapidement les rôles attribués.

## 5. Utilisation avec access_roles

Après installation, les groupes Packimmo deviennent disponibles dans la création des rôles `access.role`.

Exemple de rôles à créer :

### Rôle Vente

Ajouter le groupe :

- `Packimmo Vente`

Puis utiliser `access_roles` pour masquer les menus non nécessaires :

- Location
- Morcellement
- Dessin de carte
- Gestion technique
- Administration

### Rôle Location

Ajouter le groupe :

- `Packimmo Location`

Masquer les menus non nécessaires :

- Vente si séparée de la location
- Morcellement
- Configuration technique
- Administration

### Rôle Morcellement

Ajouter le groupe :

- `Packimmo Morcellement`

Autoriser les menus liés aux terrains, phases, lots et cartes.

### Rôle Dessinateur

Ajouter le groupe :

- `Packimmo Dessinateur`

Ce rôle doit être limité aux plans, cartes, lots et annotations. Il ne doit pas valider les ventes, contrats ou factures.

### Rôle Gestionnaire

Ajouter le groupe :

- `Packimmo Gestionnaire`

Ce rôle peut accéder à la gestion courante, aux contrats, aux tâches et au suivi administratif.

### Rôle Manager

Ajouter le groupe :

- `Packimmo Manager`

Ce groupe implique automatiquement Vente, Location, Morcellement, Dessinateur et Gestionnaire.

### Rôle Administrateur

Ajouter le groupe :

- `Packimmo Administrateur`

Ce groupe donne l'administration complète Packimmo et implique aussi `Administration / Settings` d'Odoo.

## 6. Droits créés automatiquement

Le module crée dynamiquement des droits de base sur les modèles qui existent dans la base.

Modèles ciblés :

- `property.details`
- `project.task`
- `property.mandate`
- `tenancy.details`
- `property.phase`
- `property.lot`

Si un modèle n'existe pas dans ta base, le module l'ignore automatiquement pour éviter une erreur d'installation.

## 7. Point très important sur la sécurité

Les droits Odoo sont additifs. Cela veut dire qu'un module complémentaire peut ajouter des droits, mais il ne retire pas toujours les droits déjà donnés par un autre module.

Si `rental_management` donne déjà trop de droits à `base.group_user`, alors tous les utilisateurs internes peuvent encore avoir accès à certaines données.

Dans ce cas, il faut vérifier les fichiers suivants dans les modules existants :

- `security/ir.model.access.csv`
- `security/*.xml`
- règles `ir.rule`

Puis remplacer les droits trop larges par les groupes Packimmo.

## 8. Sécurisation de access_roles

Le hook d'installation tente de réduire les droits trop larges sur les modèles :

- `access.role`
- `role.management`

L'objectif est d'éviter qu'un simple utilisateur interne puisse administrer les rôles.

Seul le groupe `Packimmo Administrateur` doit pouvoir gérer la configuration des rôles.

## 9. Développement futur recommandé

Pour une sécurité complète, il est conseillé d'ajouter progressivement :

1. Des groupes sur les menus de `rental_management`.
2. Des règles par type de bien : vente, location, terrain.
3. Des restrictions sur les boutons sensibles : validation, facturation, suppression.
4. Des vues spécifiques par rôle.
5. Des règles sur les projets Packimmo : LOCATION, VENTE, MORCELLEMENT.
6. Une séparation claire entre lecture, édition, validation et administration.

## 10. Test après installation

Créer ou utiliser plusieurs utilisateurs de test :

- Agent Vente
- Agent Location
- Dessinateur
- Gestionnaire
- Manager
- Administrateur

Pour chaque utilisateur :

1. Attribuer uniquement le groupe Packimmo nécessaire.
2. Se connecter avec cet utilisateur.
3. Vérifier les menus visibles.
4. Vérifier les boutons visibles.
5. Vérifier la création, modification et suppression.
6. Vérifier que l'utilisateur ne peut pas accéder aux menus interdits.

## 11. Commandes utiles

Mise à jour du module :

```bash
./odoo-bin -c /etc/odoo17.conf -d NOM_BASE -u packimmo_access_roles
```

Redémarrage service :

```bash
sudo systemctl restart odoo17
```

Vérification logs :

```bash
sudo journalctl -u odoo17 -f
```

## 12. Résumé

Ce module est une base propre pour intégrer les restrictions métier Packimmo dans `access_roles`.

Il ne remplace pas une vraie stratégie de sécurité serveur, mais il prépare une structure solide pour séparer les responsabilités entre Vente, Location, Morcellement, Dessinateur, Gestionnaire, Manager et Administrateur.
