MIA - Assistant métier PACKIMMO
================================

MIA est le centre d'aide officiel PACKIMMO. Il répond depuis une base de connaissances métier organisée par workflows et importée depuis un dossier externe configurable.

Workflows
---------

- Location
- Vente
- Gestion
- Morcellement
- Maintenance
- Syndic
- Comptabilité
- Website
- Administration
- Dashboard

Les modules Odoo restent techniques. Les utilisateurs voient seulement les workflows métier.

Source de connaissance
----------------------

MIA ne lit pas automatiquement les ``README.md`` ni les ``USER_GUIDE.md``.

La source principale est le dataset YAML de chaque workflow. Le YAML est le format officiel de connaissance MIA. Le dossier racine se configure dans Odoo, par exemple ``/opt/packimmo-mia-datasets``.

::

    <chemin_configure>/<workflow>/dataset.yaml

Les médias ne sont jamais importés depuis les datasets YAML ni depuis les ZIP. Images, vidéos YouTube, documents PDF et pièces jointes sont ajoutés manuellement dans Odoo sur la fiche article.

Un ZIP peut être importé depuis ``MIA > Synchronisation``, mais il sert uniquement de moyen de transport : il doit contenir des fichiers YAML et le système les extrait dans le dossier externe avant de lancer la synchronisation.

Synchronisation
---------------

Menu :

::

    MIA > Synchronisation > Synchroniser les datasets MIA

La synchronisation est idempotente : elle crée ou met à jour workflows, catégories, articles, formulations de questions, mots-clés, liens métier, FAQ et questions liées sans modifier les médias manuels.

Le moteur accepte l'ancien format :

::

    question: Comment créer un bien ?

Il accepte aussi le format enrichi :

::

    questions:
      - Comment créer un bien ?
      - Créer un bien
      - Nouveau bien

Toutes les formulations pointent vers le même article.

Réponse MIA
-----------

MIA cherche d'abord dans la nouvelle base Knowledge. Si aucun article validé n'est trouvé, l'ancien modèle ``packimmo.odoobot.answer`` reste utilisé en fallback.

Si aucun moteur ne répond avec un score suffisant, la question est enregistrée dans ``MIA > Questions sans réponse``.

La recherche tient compte des formulations multiples, du titre, de la réponse, des mots-clés, de la catégorie et du workflow.

Suggestions dans Discuss
------------------------

Les articles avec ``suggested: true`` peuvent apparaître dans la conversation MIA. Les suggestions sont filtrées par les rôles et groupes Packimmo de l'utilisateur, puis triées par ``priority`` décroissante.

À l'ouverture du chat MIA, MIA vide la session de cet utilisateur si l'option est active, puis poste un bloc ``Questions suggérées`` avec au maximum 15 questions copiables. Cette première version privilégie un affichage fiable ; le clic interactif pourra être ajouté ensuite.

Rôles et médias
---------------

Le champ ``roles`` accepte notamment ``location``, ``vente``, ``morcellement``, ``dessinateur``, ``gestionnaire``, ``comptable``, ``manager``, ``admin`` et ``administrateur``.

Les champs ``images``, ``videos`` et ``documents`` peuvent rester dans le YAML comme références, mais ils ne déclenchent aucun import automatique. Les médias attachés manuellement dans Odoo sont conservés à chaque synchronisation.
