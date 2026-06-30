# Workflow Syndic

## 1. Objectif métier

Le workflow Syndic permet de gérer un périmètre de copropriété ou résidence, de répartir les charges entre lots, de facturer les propriétaires ou locataires et de suivre les consommations d'eau ou d'électricité par compteurs.

Il s'appuie sur `packimmo_syndic_management` et `packimmo_syndic_meter`.

## 2. Utilisateurs concernés

- Gestionnaire syndic.
- Responsable résidence.
- Comptable.
- Manager.
- Administrateur.

## 3. Menus utilisés

- Menu Syndic.
- Syndic > Syndics.
- Syndic > Charges.
- Syndic > JIRAMA / Compteurs.
- Syndic > Relevés compteurs.
- Factures Odoo liées aux charges ou relevés.

## 4. Étapes principales

1. Créer une fiche syndic sur un projet ou un sous-projet.
2. Renseigner le gestionnaire et la société.
3. Actualiser les biens du périmètre.
4. Activer le syndic.
5. Créer une charge.
6. Choisir le mode de répartition.
7. Distribuer la charge.
8. Créer les factures.
9. Créer ou actualiser les compteurs si le module compteur est installé.
10. Saisir les relevés.
11. Confirmer et facturer les consommations.

## 5. Champs importants

Syndic :

- Nom
- Scope : projet ou sous-projet
- Projet
- Sous-projet
- Manager
- Société
- Devise
- Surface totale
- Total tantièmes
- State
- Lignes propriétaires

Charge :

- Libellé
- Syndic
- Date
- Type de charge
- Méthode de distribution
- Facturé à
- Montant
- Lignes de répartition
- Factures

Compteur :

- Nom
- Syndic
- Bien / lot
- Type compteur : eau ou électricité selon le module
- Dernier index
- Redevance fixe si configurée
- Actif

Relevé :

- Nom
- Syndic
- Type compteur
- Date
- State
- Lignes de relevé
- Montants
- Factures

## 6. Boutons et actions

- Actualiser les biens.
- Activer.
- Clôturer.
- Remettre en brouillon.
- Distribuer une charge.
- Créer les factures propriétaires.
- Voir les factures.
- Actualiser compteurs.
- Générer les lignes de relevé.
- Confirmer un relevé.
- Créer les factures de relevé.

## 7. Règles métier

- Un syndic porte sur un projet ou un sous-projet.
- Les lignes propriétaires reprennent les biens, propriétaires, locataires, surfaces et tantièmes.
- La répartition peut utiliser la surface, les tantièmes ou une part égale selon le champ de distribution.
- La charge peut être facturée au propriétaire ou au locataire selon le type de partenaire choisi.
- Les relevés compteur créent des factures à partir des consommations et des redevances fixes.

## 8. Contrôles et blocages

- Un syndic de scope projet demande un projet.
- Un syndic de scope sous-projet demande un sous-projet.
- L'activation est refusée si aucun bien n'est trouvé.
- Une charge sans ligne ne peut pas être facturée.
- La distribution peut être refusée si le total de surface ou de tantièmes nécessaire est nul.
- Une ligne déjà facturée ne doit pas être refacturée.
- Les relevés sans compteur ou sans ligne exploitable ne peuvent pas produire de facture utile.

## 9. Statuts

Syndic :

- Draft
- Active
- Closed

Charge :

- Draft
- Distributed
- Invoiced
- Cancelled

Relevé compteur :

- Draft
- Confirmed
- Invoiced
- Cancelled

## 10. Rapports ou PDF

Le code présent crée des factures Odoo pour charges et compteurs. Aucun rapport PDF syndic dédié n'a été identifié dans les modules syndic analysés.

## 11. Tableaux de bord

Les vues syndic affichent les lignes, totaux, factures et historiques. Aucun dashboard OWL syndic dédié n'a été identifié dans le code analysé.

## 12. Sécurité et groupes utilisateurs

Les modules syndic fournissent leurs accès via `ir.model.access.csv`. Le périmètre réel dépend aussi des groupes Properties et PACKIMMO si les menus sont protégés par la sécurité générale.

## 13. Cas d'utilisation complets

### Répartir une charge commune

1. Ouvrir Syndic > Syndics.
2. Créer une fiche sur le projet.
3. Actualiser les biens.
4. Activer.
5. Créer une charge.
6. Choisir le mode de distribution.
7. Cliquer sur Distribuer.
8. Vérifier les lignes.
9. Créer les factures.

### Facturer une consommation JIRAMA

1. Actualiser les compteurs du syndic.
2. Ouvrir Relevés compteurs.
3. Créer un relevé.
4. Générer les lignes.
5. Saisir les index.
6. Confirmer.
7. Créer les factures.

## 14. Erreurs fréquentes

- Activation refusée : aucun bien dans le périmètre.
- Distribution impossible : surface ou tantièmes manquants.
- Facturation impossible : aucune ligne à facturer.
- Compteur absent : les compteurs n'ont pas été actualisés.
- Facture introuvable : la ligne n'a pas encore été facturée.

## 15. Bonnes pratiques

- Vérifier les propriétaires et locataires des lots avant de distribuer.
- Mettre à jour les surfaces et tantièmes.
- Contrôler les lignes avant facturation.
- Ne pas modifier une charge facturée sans analyse comptable.
- Saisir les index compteur avec une période claire.

## 16. Questions/Réponses MIA potentielles

- Comment créer un syndic ?
- Comment actualiser les biens d'un syndic ?
- Comment répartir une charge ?
- Comment facturer une charge syndic ?
- Quelle différence entre surface, tantièmes et part égale ?
- Pourquoi la distribution est refusée ?
- Comment créer les compteurs ?
- Comment saisir un relevé JIRAMA ?
- Comment créer les factures de consommation ?
- Où voir les factures syndic ?
