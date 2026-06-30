# Architecture MIA Knowledge

## Principe

MIA sépare les modules techniques Odoo des workflows métier. Un workflow peut couvrir plusieurs modules, mais l'utilisateur voit uniquement le workflow.

Exemple : le workflow Location peut utiliser `rental_management`, `packimmo_property_mandate`, `packimmo_habitation_contract`, `packimmo_project_location_workflow` et `packimmo_access_roles`.

## Modèles

- `packimmo.knowledge.workflow` : workflow métier, code, description, groupes.
- `packimmo.knowledge.category` : catégories internes au workflow.
- `packimmo.knowledge.article` : question/réponse validée.
- `packimmo.knowledge.keyword` : mots-clés de recherche.
- `packimmo.knowledge.image` : images ajoutées manuellement dans Odoo.
- `packimmo.knowledge.video` : vidéos YouTube ajoutées manuellement dans Odoo.
- `packimmo.knowledge.document` : documents PDF ajoutés manuellement dans Odoo.
- `packimmo.knowledge.link` : liens utiles importés depuis les datasets.
- `packimmo.knowledge.unanswered.question` : questions non répondues.
- `packimmo.knowledge.sync.wizard` : bouton de synchronisation.

## Source des datasets

Le module ne contient aucun dataset métier. Le moteur lit uniquement le dossier externe configuré par le paramètre `packimmo_odoobot_assistant.mia_dataset_path`.

Le scanner parcourt récursivement ce dossier et importe chaque fichier `dataset.yaml` ou `dataset.yml` trouvé. Si le paramètre est vide, l'assistant demande de configurer le chemin. Si aucun dataset n'est présent, la synchronisation ne crée aucun contenu et ne génère pas d'erreur.

Le ZIP est uniquement un moyen de dépôt optionnel. L'assistant ZIP extrait des fichiers YAML autorisés dans le dossier externe, refuse les chemins dangereux et lance ensuite la synchronisation standard.

Les datasets ne pilotent que la connaissance métier textuelle : workflows, catégories, articles, FAQ, mots-clés, liens métier et questions liées. Les médias restent administrés depuis Odoo et sont conservés lors des resynchronisations.

## Recherche

Le moteur calcule un score à partir de :

- question ;
- titre ;
- mots-clés ;
- réponse ;
- workflow ;
- catégorie ;
- groupes de l'utilisateur.

Le seuil par défaut est `0.45` via le paramètre `packimmo_odoobot_assistant.mia_min_score`.

## Compatibilité

Le modèle historique `packimmo.odoobot.answer` est conservé. Le nouveau moteur Knowledge est prioritaire, puis l'ancien moteur répond en fallback.

## Historique de chat

Le modèle `res.users.log` déclenche le nettoyage du canal MIA à la connexion si `mia_auto_clear_history` est actif. Seuls les messages du canal de chat entre l'utilisateur et MIA sont supprimés.
