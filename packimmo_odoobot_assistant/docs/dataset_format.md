# Format dataset MIA

Le format officiel de connaissance MIA est YAML. Un fichier ZIP n'est pas un format de dataset : c'est uniquement un moyen optionnel de transporter plusieurs fichiers YAML.

Chaque workflow possède un fichier :

```text
<chemin_configure>/<workflow>/dataset.yaml
```

Le chemin racine est configuré dans Odoo via `Paramètres > MIA > Chemin des datasets MIA`.

## Exemple

```yaml
workflow: location
name: Location
version: "17.0"
description: Workflow métier Location PACKIMMO.
sequence: 10
roles:
  - Location
  - Manager
categories:
  - name: Bien à louer
    sequence: 10
articles:
  - id: location-001
    title: Créer un bien à louer
    category: Bien à louer
    difficulty: beginner
    roles:
      - Location
      - Manager
    suggested: true
    priority: 100
    questions:
      - Comment créer un bien à louer ?
      - Créer un bien
      - Nouveau bien
      - Ajouter une villa
    menu: Location > Biens > Nouveau
    model: property.details
    prerequisites:
      - Propriétaire vérifié
      - Mandat prêt à activer
    steps:
      - Ouvrir Location
      - Créer le bien
    tips: Ajouter au moins une image avant publication.
    errors: Un mandat actif peut être obligatoire.
    answer: >
      <p>Créez un bien avec Property For = Rent...</p>
    keywords:
      - bien
      - location
    links:
      - url: https://example.com/guide-location
        title: Guide location
    guide_anchor: creation-bien-location
    source_reference: rental_management
    see_also:
      - location-002
faq:
  - id: location-faq-001
    question: Où trouver les contrats de location ?
    answer: >
      <p>Depuis le menu Location.</p>
    keywords:
      - contrat
      - bail
```

## Règles

- `workflow` est obligatoire.
- `articles[].id` est obligatoire et unique dans le workflow.
- `question` reste accepté pour les anciens datasets.
- `questions` peut remplacer `question` et contenir plusieurs formulations. Toutes pointent vers le même article.
- `answer` est le contenu HTML de réponse. S'il est absent, l'article est importé avec une réponse vide pour ne pas bloquer la synchronisation.
- `keywords` améliore le score de recherche.
- `roles` limite l'article à des groupes Packimmo. Valeurs simples acceptées : `location`, `vente`, `morcellement`, `dessinateur`, `gestionnaire`, `comptable`, `manager`, `admin` ou `administrateur`.
- `suggested: true` rend l'article éligible aux questions suggérées dans Discuss.
- `priority` trie les suggestions : une priorité élevée apparaît avant une priorité plus faible.
- `see_also` référence les IDs d'articles liés et apparaît en réponse sous `Voir aussi`.
- `menu` et `model` sont informatifs pour afficher le chemin Odoo et le modèle cible.
- `prerequisites`, `steps`, `tips` et `errors` sont optionnels et affichés avec la réponse.
- `youtube` est un ancien champ accepté pour compatibilité, mais il est ignoré par la synchronisation. Les vidéos se gèrent dans Odoo.
- `links` ou `liens` peut contenir des URL simples ou des objets avec titre, URL, description.
- `faq` contient des questions/réponses importées comme articles FAQ.
- `related_questions` reste accepté comme alias historique de `see_also`.
- `images`, `videos` et `documents` sont acceptés comme références, mais ne sont jamais importés automatiquement.
- Les images, vidéos YouTube, documents PDF et pièces jointes restent ajoutés manuellement sur l'article MIA dans Odoo.

## Import ZIP optionnel

L'assistant `MIA > Synchronisation > Importer un ZIP de datasets` extrait le ZIP dans le dossier externe configuré, puis lance la synchronisation YAML.

Le ZIP doit respecter les règles suivantes :

- chemins absolus interdits ;
- chemins contenant `../` interdits ;
- extraction hors du dossier configuré interdite ;
- seuls `.yaml`, `.yml` et `README.md` sont acceptés ;
- les images, PDF et fichiers binaires ne sont pas acceptés.

## Synchronisation

La synchronisation :

- crée ou met à jour les workflows ;
- crée ou met à jour les catégories ;
- crée ou met à jour les articles ;
- remplace les mots-clés et liens déclarés dans le YAML ;
- remplace les formulations déclarées dans `questions` ou `question` ;
- met à jour les questions liées via `see_also` ou `related_questions` ;
- ne crée, modifie ni supprime jamais les images, vidéos YouTube, documents PDF ou pièces jointes ajoutés dans Odoo ;
- conserve les questions sans réponse.

## Discuss

Quand l'utilisateur ouvre la conversation MIA, le canal MIA de cet utilisateur est vidé si l'option de session temporaire est active, puis MIA poste jusqu'à 15 questions suggérées adaptées à ses groupes et workflows autorisés.

Les suggestions viennent uniquement des articles importés avec `suggested: true`. Une suggestion n'est jamais affichée si l'utilisateur ne peut pas voir la réponse.
