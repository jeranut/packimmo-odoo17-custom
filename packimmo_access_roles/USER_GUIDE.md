# Guide utilisateur - Packimmo Access Roles

## Objectif

`packimmo_access_roles` est le point central de sécurité Packimmo pour Odoo 17 Community. Il complète `access_roles` avec des groupes métier, des profils de visibilité, une matrice de permissions et une API Python réutilisable par `rental_management`, les mandats, les contrats, les cartes, les tableaux de bord et les futurs modules Packimmo.

Le moteur s'applique au backend. Il ne doit pas filtrer le Website public : les visiteurs continuent à voir les biens, projets, phases, lots, cartes et brochures publiés selon les contrôleurs website existants.

## Groupes et hiérarchie

Groupes disponibles :

- Utilisateur Packimmo
- Packimmo Vente
- Packimmo Location
- Packimmo Morcellement
- Packimmo Dessinateur
- Packimmo Gestionnaire
- Packimmo Comptable
- Packimmo Manager
- Packimmo Administrateur

Le Manager implique automatiquement Vente, Location, Morcellement, Dessinateur, Gestionnaire et Comptable. L'Administrateur implique le Manager et l'administration Odoo.

## Rôle Comptable

Le Comptable peut consulter les biens, propriétaires, locataires, contrats et mandats. Il peut gérer les objets comptables disponibles dans la base, par exemple paiements, écritures, encaissements, décaissements et rapprochements.

Il ne doit pas modifier les objets métier sensibles : mandat, contrat, bien, plan, carte, phase ou lot. Cette règle est déclarée dans la matrice de permissions et dans les ACL dynamiques lorsque les modèles existent.

## Profils de visibilité

Menu : `Paramètres > Sécurité Packimmo > Profils de visibilité`.

Chaque profil peut être global ou rattaché à une société. Un profil global est disponible dans toutes les sociétés. Un profil avec `Société` renseignée n'est disponible que pour cette société.

Scopes :

- Moi uniquement
- Mon équipe
- Mon agence
- Toute la société
- Tout

Options :

- Voir les archives
- Voir les brouillons
- Voir les contrats terminés
- Voir les biens vendus
- Voir les biens loués

Le profil est affecté sur la fiche utilisateur avec le champ `Profil de visibilité Packimmo`. Cette affectation est multi-société : le même utilisateur peut avoir un profil différent selon la société active.

## Matrice de permissions

Menu : `Paramètres > Sécurité Packimmo > Matrice de permissions`.

Chaque permission peut être globale ou spécifique à une société. Si une permission existe pour la société active, elle est prioritaire. Sinon, le moteur utilise la permission globale.

La matrice est générée automatiquement lors de l'installation et de la mise à jour du module. Le scanner détecte les modules `packimmo_*` et les modules immobiliers suivis dans le dépôt, cartographie les modèles, vues, menus, actions, boutons, rapports, contrôleurs, dashboards et éléments website, puis crée ou met à jour les lignes `packimmo.permission.matrix` sans doublons.

Chaque ligne définit les droits d'un groupe sur un objet technique :

- Lecture
- Création
- Modification
- Suppression
- Validation
- Export
- Impression

Objets courants : `property.details`, `property.mandate`, `tenancy.details`, `property.vendor`, `property.phase`, `property.lot`, `property.project`, `maintenance.request`, `syndic.management`, `account.payment`, `account.move`, `documents`.

## Cartographie automatique

Menu : `Paramètres > Sécurité Packimmo > Objets métier détectés`.

Cette vue montre les objets détectés automatiquement dans le dépôt : module source, modèle, héritages, vues, menus, actions, boutons, rapports, contrôleurs, dashboards et éléments website. Si un nouveau module `packimmo_*` est ajouté plus tard dans `/opt/odoo17/packimmo_git`, il est détecté lors du prochain `-u packimmo_access_roles`.

## Gestion automatique des menus

Menu : `Paramètres > Sécurité Packimmo > Permissions des menus`.

La matrice de permissions protège les objets métier, mais elle ne masque pas à elle seule les entrées du menu Odoo. Le modèle `packimmo.menu.permission` ajoute cette couche de visibilité backend.

Fonctionnement :

- sans règle ou avec une règle sans groupe, le comportement Odoo standard s'applique ;
- avec des groupes autorisés, le menu est visible uniquement pour ces groupes ;
- Packimmo Manager et Packimmo Administrateur voient tous les menus métier Packimmo ;
- le filtrage est appliqué côté serveur via `ir.ui.menu`, pas en CSS ou JavaScript ;
- les raccourcis `web_responsive` suivent automatiquement le même filtrage, car ils utilisent les menus visibles ;
- le Website public n'est pas impacté.

Pour tester le rôle Location, connecter un utilisateur qui possède uniquement `Packimmo Location` et les groupes internes nécessaires à l'application Propriétés. Le menu `Configurations`, `Selling`, les mandats de vente, contrats de vente, morcellements, dessin avancé et comptabilité ne doivent pas apparaître. Les menus de location, contrats de location, maintenance, courtiers et rapports utiles doivent rester visibles.

Pour ajouter un nouveau menu Packimmo, aucune modification de code n'est nécessaire dans le cas général : au prochain `-u packimmo_access_roles`, le générateur analyse le menu, son module, son action et son modèle pour créer ou mettre à jour la règle. L'administrateur peut ensuite ajuster la règle manuellement dans `Permissions des menus`.

## API Python

Le service central est `packimmo.security.mixin`.

Exemples :

```python
security = self.env['packimmo.security.mixin']
domain = security.get_domain('property.details')
can_edit = security.can_edit('property.mandate')
can_delete = security.can_delete('property.details')
can_validate = security.can_validate('tenancy.details')
can_export = security.can_export('property.vendor')
can_print = security.can_print('property.mandate')
scope = security.get_scope()
```

Dans un contrôleur backend :

```python
security = request.env['packimmo.security.mixin']
domain = security.get_domain('property.details')
records = request.env['property.details'].search(domain)
```

Dans le Website public, conserver les domaines publics existants :

```python
properties = request.env['property.details'].sudo().search([
    ('website_published', '=', True),
])
```

## Domaines centralisés

Le moteur calcule les domaines avec :

- `_get_company_domain()`
- `_get_visibility_domain()`
- `_get_security_domain()`

La logique inspecte les champs disponibles (`company_id`, `user_id`, `responsible_id`, `salesperson_id`, `create_uid`, `stage`, `state`, `contract_type`, `active`) pour rester compatible avec les modules optionnels. Les domaines société utilisent les sociétés autorisées de l'utilisateur (`user.company_ids`) et la matrice de permissions utilise la société active (`env.company`).

## Web Responsive

Les raccourcis `web.responsive.app.shortcut` reçoivent un champ `Visible pour les groupes`.

Si le champ est vide, le raccourci suit seulement la visibilité du menu. S'il contient des groupes, l'utilisateur doit appartenir à au moins l'un d'eux.

## Rental Management et tableaux de bord

Les KPI et listes backend doivent appeler :

```python
domain = self.env['packimmo.security.mixin'].get_domain('property.details')
```

Un commercial voit ses biens si son profil est `Moi uniquement`. Un manager voit le périmètre de sa société ou tout selon son profil. Un gestionnaire peut être limité à son agence via `company_id`.

## Exemples XML

Les filtres de recherche communs doivent être ajoutés sur des modèles concrets. Il ne faut pas déclarer un filtre contenant `user_id`, `responsible_id` ou `company_id` sur le mixin abstrait `packimmo.security.mixin`, car Odoo valide les champs au chargement des vues.

Limiter un menu à la Location :

```xml
<menuitem id="menu_location"
          name="Location"
          groups="packimmo_access_roles.group_packimmo_location"/>
```

Limiter un bouton aux managers :

```xml
<button name="action_validate"
        type="object"
        string="Valider"
        groups="packimmo_access_roles.group_packimmo_manager"/>
```

## Exemple de Record Rule

```xml
<record id="rule_property_company_packimmo" model="ir.rule">
    <field name="name">Biens par sociétés autorisées</field>
    <field name="model_id" ref="rental_management.model_property_details"/>
    <field name="domain_force">[('company_id', 'in', company_ids)]</field>
    <field name="groups" eval="[(4, ref('packimmo_access_roles.group_packimmo_user'))]"/>
</record>
```

## Ajouter un nouveau rôle

1. Créer un groupe dans `security/packimmo_security_groups.xml`.
2. Ajouter le code dans `ROLE_GROUP_XMLIDS`.
3. Ajouter les lignes nécessaires dans `PACKIMMO_MODEL_ACCESS`.
4. Mettre à jour la matrice depuis le hook ou depuis l'interface.
5. Documenter le rôle dans ce guide.

## Ajouter un module Packimmo

1. Déclarer les groupes sur les menus.
2. Appeler `get_domain()` dans les recherches backend.
3. Appeler `has_permission()` ou `can_*()` pour les boutons, exports, impressions et validations.
4. Ne pas utiliser le moteur dans les routes Website publiques.
5. Ajouter les modèles importants dans le hook pour les ACL dynamiques.

## Migration

Après mise à jour :

```bash
./odoo-bin -c /etc/odoo17.conf -d NOM_BASE -u packimmo_access_roles --stop-after-init
```

Vérifier ensuite :

- les groupes sur les utilisateurs ;
- le profil de visibilité ;
- la matrice de permissions ;
- les menus visibles ;
- les KPI backend ;
- les routes Website publiques.

## Bonnes pratiques

- Ne pas dupliquer les domaines dans les contrôleurs.
- Préférer `get_domain()` pour les recherches backend.
- Préférer `can_validate()`, `can_export()` et `can_print()` pour les actions sensibles.
- Garder les règles Website publiques séparées.
- Tester avec un utilisateur par rôle avant mise en production.
