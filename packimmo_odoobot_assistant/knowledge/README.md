# Datasets MIA

Ce dossier ne contient aucun dataset metier.

Le format officiel de connaissance MIA est YAML. Un fichier ZIP n'est pas un format de connaissance : c'est seulement un moyen optionnel de deposer plusieurs fichiers `dataset.yaml` dans le dossier externe configure.

Le module `packimmo_odoobot_assistant` fournit uniquement le moteur Knowledge. Les datasets doivent etre stockes dans un dossier externe configure dans Odoo, par exemple :

```text
/opt/packimmo-mia-datasets
/home/odoo/mia_datasets
```

Le chemin se configure dans Odoo :

```text
Parametres > MIA > Chemin des datasets MIA
```

## Structure attendue

Le moteur parcourt recursivement le dossier externe et importe chaque fichier nomme `dataset.yaml`. L'extension `dataset.yml` est aussi acceptee, mais `dataset.yaml` reste la convention recommandee.

Depuis la version multi-fichiers, `dataset.yaml` peut etre soit :

- un dataset complet, comme auparavant ;
- un manifeste qui declare une liste `imports` de fichiers YAML du meme dossier de workflow.

Exemple :

```text
/opt/packimmo-mia-datasets/
    location/
        dataset.yaml
        01_workflow.yaml
        02_properties.yaml
        03_owners.yaml
        04_mandates.yaml
        15_faq.yaml
    vente/
        dataset.yaml
    morcellement/
        dataset.yaml
    gestion/
        dataset.yaml
    syndic/
        dataset.yaml
    maintenance/
        dataset.yaml
```

Chaque dossier de workflow doit contenir un unique `dataset.yaml`. Les autres fichiers YAML sont lus uniquement s'ils sont declares dans `imports`.

## Format manifeste multi-fichiers

Exemple de `location/dataset.yaml` :

```yaml
workflow:
  code: location
  name: Location
  version: "1.0"
  description: Workflow complet de gestion des locations Packimmo.

imports:
  - 01_workflow.yaml
  - 02_properties.yaml
  - 03_owners.yaml
  - 04_mandates.yaml
  - 15_faq.yaml
```

Exemple de fichier importe `location/02_properties.yaml` :

```yaml
categories:
  - code: property
    name: Gestion des biens

articles:
  - id: location_property_create
    category: property
    title: Creer un bien a louer
    questions:
      - Comment creer un bien a louer ?
      - Ajouter une villa a louer
      - Creer un appartement a louer
    answer: |
      <p>Creer le bien depuis le menu Location.</p>
    keywords:
      - bien
      - location
    suggested: true
    priority: 100

links:
  - id: location_link_001
    article: location_property_create
    title: Ouvrir les biens
    url: /web#menu_id=...
```

Les `categories`, `articles`, `faq` et `links` de tous les fichiers importes sont fusionnes avant synchronisation.

Si `dataset.yaml` ne contient pas `imports`, le moteur conserve le comportement historique et importe directement les blocs `categories`, `articles`, `faq` et `links` contenus dans ce fichier.

## Regles d'import

- Si aucun chemin n'est configure, aucun dataset n'est importe et aucune erreur n'est generee.
- Si le chemin configure ne contient aucun `dataset.yaml` ou `dataset.yml`, aucun workflow ni article n'est cree.
- Le moteur cree les nouveaux enregistrements et met a jour les enregistrements existants.
- La cle d'un workflow est le champ `workflow` ou `workflow.code`.
- La cle d'un article est le couple `workflow` + `external_id` ou `id`.
- La cle d'une categorie est le couple `workflow` + `category.name`.
- Les liens sont dedoublonnes par article et URL.
- Les mots-cles sont dedoublonnes par article et libelle.
- Les images, captures d'ecran, videos YouTube, documents PDF et pieces jointes ne sont jamais importes, modifies ni supprimes par la synchronisation.
- Une erreur dans un dataset est reportee dans le rapport final sans bloquer les autres datasets.

Regles de securite pour `imports` :

- les chemins absolus sont refuses ;
- les chemins contenant `../` sont refuses ;
- les chemins Windows ou avec antislash sont refuses ;
- seuls les fichiers `.yaml` et `.yml` sont acceptes ;
- un import ne peut jamais sortir du dossier du workflow ;
- si un fichier importe est absent, le rapport indique `Fichier import introuvable` et les autres fichiers continuent a etre importes.

La synchronisation se lance depuis :

```text
MIA > Synchronisation > Synchroniser les datasets
```

## Import ZIP optionnel

L'assistant `MIA > Synchronisation` propose aussi `Importer un ZIP de datasets`.

Le ZIP doit contenir une arborescence de dossiers avec des fichiers YAML, par exemple :

```text
location/dataset.yaml
vente/dataset.yaml
gestion/dataset.yaml
maintenance/dataset.yaml
README.md
```

Le systeme extrait le ZIP dans le dossier externe configure, puis lance automatiquement la synchronisation des `dataset.yaml` et `dataset.yml`.

Regles de securite ZIP :

- les chemins absolus sont refuses ;
- les chemins contenant `../` sont refuses ;
- toute extraction hors du dossier configure est refusee ;
- les chemins Windows ou avec antislash sont refuses ;
- seuls les fichiers `.yaml`, `.yml` et `README.md` sont acceptes ;
- les images, PDF et autres fichiers binaires ne sont jamais extraits ni importes.

## Format YAML

Exemple minimal :

```yaml
workflow: location
name: Location
version: "17.0"
description: Workflow Location PACKIMMO.
sequence: 10
roles:
  - Location
  - Manager
categories:
  - name: Bien a louer
    sequence: 10
articles:
  - id: location-001
    title: Creer un bien a louer
    category: Bien a louer
    difficulty: beginner
    roles:
      - Location
    suggested: true
    priority: 10
    question: Comment creer un bien a louer ?
    answer: >
      <p>Reponse validee.</p>
    keywords:
      - bien
      - location
    links:
      - url: https://example.com/guide-location
        title: Guide location
        description: Documentation interne
    guide_anchor: creation-bien-location
    source_reference: guide_location
    related_questions:
      - location-002
faq:
  - id: location-faq-001
    question: Ou trouver les contrats de location ?
    answer: >
      <p>Depuis le menu Location, ouvrir les contrats.</p>
    keywords:
      - contrat
      - bail
```

## Champs racine

- `workflow` : code technique du workflow. Obligatoire.
- `name` : nom affiche du workflow.
- `version` : version du dataset.
- `description` : description du workflow.
- `sequence` : ordre d'affichage.
- `roles` ou `groups` : roles ou groupes autorises au niveau workflow.
- `categories` : liste des categories.
- `articles` : liste des articles.
- `faq` : liste optionnelle de questions/reponses importees comme articles FAQ.
- `imports` : liste optionnelle de fichiers YAML a fusionner dans le cas d'un manifeste.

## Champs categorie

- `name` : nom de la categorie. Obligatoire.
- `sequence` : ordre d'affichage.
- `active` : actif ou non.

## Champs article et FAQ

- `id` : identifiant stable dans le workflow. Obligatoire pour les articles.
- `title` : titre affiche. Si absent, la question est utilisee.
- `category` : categorie rattachee.
- `difficulty` : `beginner`, `intermediate` ou `advanced`.
- `roles` : roles ou groupes autorises sur l'article.
- `suggested` : rend la question eligible aux suggestions.
- `priority` : priorite de recherche et de suggestion.
- `question` : question utilisateur.
- `questions` : formulations multiples. Si present, la premiere formulation devient la question principale.
- `answer` : reponse HTML validee.
- `keywords` : mots-cles de recherche.
- `youtube` : ancien champ conserve pour compatibilite, ignore par la synchronisation.
- `links` ou `liens` : liens utiles.
- `guide_anchor` : ancre de guide optionnelle.
- `source_reference` : reference de validation.
- `related_questions` : IDs d'articles lies dans le meme workflow.
- `active` : actif ou non.

## Champs lien

- `url` : URL. Obligatoire.
- `title` : titre affiche.
- `description` : description courte.
- `sequence` : ordre d'affichage.
- `active` : actif ou non.

## Rapport d'import

Le bouton de synchronisation affiche un rapport :

```text
Import termine

✓ Workflows crees
✓ Workflows mis a jour
✓ Fichiers YAML lus
✓ Fichiers YAML absents
✓ Categories creees
✓ Categories mises a jour
✓ Articles crees
✓ Articles mis a jour
✓ Articles ignores
✓ Medias conserves
✓ FAQ creees / mises a jour
✓ Liens crees / mis a jour
✓ Mots-cles
✓ Erreurs
```

## Medias

Les images, captures d'ecran, videos YouTube, documents PDF et pieces jointes ne font pas partie des datasets YAML et ne sont pas importes depuis les ZIP. Ils restent configures manuellement dans Odoo sur les articles MIA.

Une nouvelle synchronisation peut mettre a jour le texte de l'article, ses mots-cles et ses liens metier, mais elle conserve les medias deja associes.
