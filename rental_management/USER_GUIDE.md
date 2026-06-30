# Guide utilisateur PACKIMMO - Location

Ce guide couvre uniquement le parcours LOCATION de PACKIMMO : bien à louer, propriétaire, mandat de location, publication web, prospects, visites, choix du locataire, contrat de location, état des lieux, loyers, maintenance, fin ou renouvellement, suivi dans le projet LOCATION, tableaux de bord et droits des utilisateurs Location.

Il ne documente pas la vente, le morcellement, le dessin, ni la comptabilité complète.

## 1. Vue d'ensemble du workflow Location

Le parcours standard est le suivant :

1. Créer le bien à louer.
2. Vérifier le propriétaire.
3. Créer et activer le mandat de location.
4. Rendre le bien disponible et le publier sur le site.
5. Recevoir ou créer les prospects.
6. Planifier les visites.
7. Valider la visite et sélectionner le locataire.
8. Régulariser le mandat si nécessaire.
9. Créer le contrat de location.
10. Activer le contrat et générer les premières factures.
11. Réaliser l'état des lieux.
12. Suivre les loyers, charges, factures et pénalités.
13. Suivre les maintenances et travaux.
14. Renouveler, clôturer ou annuler le contrat.
15. Piloter le dossier dans le projet LOCATION et les tableaux de bord.

Dans le projet LOCATION, les étapes utilisées sont :

- BIENS DISPONIBLE
- VISITE
- REGULARISATION MANDAT
- CONTRAT
- ETAT DES LIEUX
- FIN
- VISITES PERDUE

Les tâches du projet LOCATION sont créées automatiquement à partir des biens. La création manuelle de tâches dans ce workflow est bloquée : il faut créer le bien depuis le flux prévu.

## 2. Création d'un bien à louer

### Accès

Ouvrir le menu Location / LOCATION, puis utiliser l'action de création du bien à louer. Selon la configuration, le bien peut aussi être créé depuis le menu Properties > Projects > Properties.

### Champs essentiels

Sur la fiche du bien, renseigner au minimum :

- Name : nom commercial ou référence du bien.
- Property For : Rent / Location.
- Property Type : Residential, Commercial, Industrial ou Land si applicable.
- Property Sub Type : sous-type du bien.
- Region, City, adresse, coordonnées GPS si utilisées.
- LandLord : propriétaire.
- Price : loyer.
- Rent Unit : Day, Month ou Year.
- Total Area et Usable Area si disponibles.
- Images, documents, amenities, specifications, floor plans et nearby connectivities si le bien doit être présenté sur le site.

Pour une location, vérifier que le champ `sale_lease` est bien positionné sur `for_tenancy`.

### Prix et devise affichée

Le prix public peut être géré en Ariary ou en devise étrangère :

- Website Price On Request : affiche le prix sur demande.
- Website Price Currency : choisit Ariary ou Foreign Currency.
- Foreign Currency et Foreign Price : utilisés si le loyer est exprimé en devise étrangère.

Le site utilise le prix d'affichage calculé à partir de ces champs.

### Statuts du bien

Les statuts principaux sont :

- Draft : bien en préparation.
- Available : bien disponible.
- Booked : réservation en cours.
- On Rent : bien loué.

Pour un bien externe, PACKIMMO impose un mandat actif avant de le passer disponible. Si le bien appartient à la société PACKIMMO, le mandat actif n'est pas obligatoire.

## 3. Vérification du propriétaire

Le propriétaire est le contact indiqué dans LandLord sur le bien. Il doit être un partenaire de type propriétaire.

Avant de rendre le bien disponible, vérifier :

- nom complet ou raison sociale ;
- téléphone et email ;
- société concernée ;
- compte bancaire si le mandat ou le contrat doit mentionner le compte de réception du loyer ;
- documents justificatifs attachés au bien ou au mandat ;
- cohérence entre le propriétaire et la société du bien.

Si le propriétaire est aussi le partenaire de la société, PACKIMMO considère le bien comme appartenant à la société et ne bloque pas la disponibilité pour absence de mandat actif.

## 4. Création du mandat de location

### Depuis le bien

Depuis la fiche du bien, utiliser le bouton Mandat ou Nouveau mandat. Le système préremplit :

- propriétaire depuis LandLord ;
- type d'opération Location ;
- bien lié ;
- société du bien.

### Informations à renseigner

Sur le mandat, choisir :

- Type d'opération : Location.
- Type de mandat : Mandat simple, Mandat exclusif ou Mandat exclusif absolu.
- Date de début, durée et date de fin.
- Renouvellement par tacite reconduction si applicable.
- Base honoraires location : nombre de mois de loyer, pourcentage du loyer ou montant fixe.
- Pourcentage commission et taxe.
- Facturé à : locataire, propriétaire ou les deux.
- Locataire trouvé lorsque le locataire est identifié.
- Type de caution : aucune, nombre de mois de loyer, montant fixe ou pourcentage annuel.
- Jirama, compte bancaire du loyer, révision de loyer et options de devise pour les mandats exclusifs.

Le montant de caution est calculé automatiquement selon le type choisi. Si une caution est définie sur le mandat, l'assistant de contrat de location la reprend automatiquement.

### Cycle de validation

Le mandat suit ce cycle :

- Brouillon
- A valider
- Approuvé
- Actif
- Terminé
- Expiré
- Annulé

Actions principales :

- Soumettre : envoie le mandat en validation.
- Approuver : valide le mandat avant activation.
- Activer : rend le mandat actif et rend disponibles les biens liés encore en brouillon.
- Imprimer le mandat : génère le PDF du mandat dans le chatter.
- Terminer et facturer : crée les factures d'honoraires.
- Expirer ou Annuler : ferme le mandat sans poursuivre le flux.

Quand les factures d'honoraires du mandat sont toutes payées, le mandat peut passer Terminé automatiquement.

### Impact du type de mandat sur le workflow Location

Après une visite validée, le dossier passe en REGULARISATION MANDAT.

- Mandat exclusif absolu terminé : le dossier peut avancer vers CONTRAT.
- Mandat simple ou exclusif terminé : le dossier peut avancer vers ETAT DES LIEUX.
- Mandat actif mais non régularisé : l'action demande de régulariser le mandat.
- Mandat expiré ou annulé : le dossier va vers FIN.

Important : la création du contrat de bail est bloquée pour un mandat simple ou exclusif. Le contrat de location est autorisé uniquement lorsque les règles du mandat le permettent, notamment avec le mandat exclusif absolu.

## 5. Publication du bien sur le site

Le site public liste les biens dont le statut n'est pas Draft. Pour publier un bien à louer :

1. S'assurer que le bien est en Location.
2. Renseigner les images, ville, région, projet, surface, type et prix.
3. Activer le mandat si le bien nécessite un mandat.
4. Passer le bien en Available.
5. Vérifier l'affichage sur `/properties-list?sale_lease=for_tenancy`.

Le site permet de filtrer par :

- opération Location ;
- type de bien ;
- région ;
- projet ;
- prix minimum et maximum ;
- surface minimum et maximum ;
- recherche texte.

Le badge public affiche EN LOCATION lorsque le bien est proposé à la location.

## 6. Réception des prospects

Les prospects sont gérés via CRM Lead et sont liés au bien par le champ Property.

Un prospect de location contient notamment :

- client ou contact ;
- bien concerné ;
- type Lead ou Opportunity ;
- note ou description ;
- prix demandé si renseigné.

Depuis la fiche du bien, les smart buttons Leads et Opportunity ouvrent les prospects liés au bien.

Lorsqu'un contrat est créé depuis un prospect, cocher From Enquiry dans l'assistant de contrat puis sélectionner le lead. Le système reprend le client et la note du prospect.

## 7. Organisation des visites

### Depuis le projet LOCATION

Ouvrir le kanban LOCATION. Un bien disponible apparaît dans l'étape BIENS DISPONIBLE.

Pour planifier une visite :

1. Ouvrir la tâche du bien.
2. Cliquer sur Planifier une visite.
3. Sélectionner le client.
4. Ajouter une observation si nécessaire.
5. Confirmer.

Le système :

- renseigne le client visite sur la tâche ;
- déplace la tâche parent en VISITE ;
- crée une sous-tâche Visite liée au client ;
- conserve l'observation de visite.

Le passage manuel vers VISITE est bloqué si le client n'est pas renseigné via le bouton prévu.

### Annuler une visite

Depuis la sous-tâche de visite, utiliser l'action d'annulation. Si le dossier n'est pas déjà en régularisation ou réservation, le bien revient en BIENS DISPONIBLE et le client visite est vidé.

## 8. Sélection du locataire

Après la visite :

1. Ouvrir la sous-tâche de visite.
2. Cliquer sur Valider visite.
3. Le dossier passe en REGULARISATION MANDAT.
4. Vérifier ou compléter le mandat avec le locataire retenu.
5. Régulariser le mandat selon le type de mandat.

Lorsque plusieurs visites existent, PACKIMMO utilise la première sous-tâche de visite encore ouverte pour afficher les actions de suite. Les autres visites peuvent être annulées automatiquement lorsque le dossier avance.

## 9. Création du contrat de location

### Depuis le bien ou le dossier LOCATION

La création du contrat ouvre l'assistant Contract Wizard. Le contrat créé est un enregistrement `tenancy.details`.

Renseigner :

- Customer : locataire.
- Property : bien.
- Rent Unit : Day, Month ou Year.
- Total Rent : loyer.
- Deposit et Security Deposit si applicable.
- Payment Term : Monthly, Quarterly, Half Year, Yearly, Daily ou Full Payment selon l'unité de loyer.
- Duration ou Date de fin selon le mode de durée.
- Start Date.
- Broker si un intermédiaire intervient.
- Agreement Template et Term and Condition.
- Taxes sur loyer, dépôt ou services si utilisées.
- Services et maintenance à fusionner avec les échéances ou à facturer séparément.
- Pénalités si la configuration les active.

Le système vérifie que les dates ne chevauchent pas un contrat actif existant pour le même bien.

### Contrat en paiement complet

Si Payment Term = Full Payment :

- le contrat est créé directement en Running ;
- la facture de paiement complet est générée ;
- le bien passe en On Rent.

### Contrat avec échéances

Si le paiement est mensuel, trimestriel, semestriel, annuel ou quotidien :

- le contrat est créé en Draft / New Contract ;
- le bien passe en On Rent ;
- l'utilisateur doit ensuite activer le contrat.

### Activation du contrat

Sur le contrat, cliquer sur Activer le contrat.

L'activation :

- génère la première facture de loyer ;
- ajoute le dépôt si prévu ;
- ajoute la maintenance ou les services selon le mode choisi ;
- crée la facture de courtage si un broker est renseigné ;
- envoie l'email de contrat actif si le modèle est configuré ;
- passe le contrat en Running ;
- mémorise la dernière date de facturation.

Le contrat actif devient la référence de suivi des loyers, factures, bills et maintenances.

### Contrat habitation ou commercial

Si le module `packimmo_habitation_contract` est installé, l'assistant de contrat génère automatiquement un PDF :

- contrat bail habitation pour les biens résidentiels ;
- contrat bail commercial pour les autres types.

Le PDF est attaché au contrat de location et publié dans le chatter. Le contrat conserve aussi :

- Dernier contrat bail habitation ;
- Date impression bail habitation ;
- Mode de conversion : taux fixe ou taux du MID ;
- Taux fixe contrat si la location est en devise.

## 10. Etat des lieux

Dans le projet LOCATION, l'étape ETAT DES LIEUX intervient après la régularisation du mandat et/ou le contrat selon le type de mandat.

Règles importantes :

- Depuis l'étape CONTRAT, il est interdit de passer en ETAT DES LIEUX si aucun contrat actif n'est lié au bien.
- Une fois en ETAT DES LIEUX, le retour vers une étape précédente est bloqué.
- Les sous-tâches de visite peuvent être marquées terminées pour finaliser l'étape.

L'état des lieux sert à confirmer l'entrée du locataire et à clôturer le dossier commercial dans le projet LOCATION.

## 11. Suivi des paiements et loyers

### Factures de loyer

Les factures de location sont suivies dans Renting > Invoices et dans le smart button Invoices du contrat.

Chaque ligne `rent.invoice` contient :

- contrat ;
- locataire ;
- type de paiement : rent, deposit, maintenance, penalty, full rent ou other ;
- date de facture ;
- montant ;
- facture comptable liée ;
- statut de paiement.

Les factures récurrentes peuvent être créées automatiquement par le planificateur pour les contrats mensuels actifs en mode Auto Installment.

### Paiement complémentaire

Depuis un contrat, l'assistant de paiement permet de créer une facture supplémentaire pour :

- dépôt ;
- maintenance ;
- pénalité ;
- service extra ;
- autre motif.

Le paiement extra service peut aussi ajouter une ligne de service au contrat.

### Bills et dépenses liées au contrat

Les bills de location sont suivis dans Renting > Bills et sur le contrat.

Un bill peut être créé pour un prestataire ou le propriétaire avec :

- motif du paiement ;
- date ;
- montant ;
- produit/service ;
- taxes ;
- facture fournisseur liée.

Le contrat calcule :

- total facturé ;
- total payé ;
- reste à payer ;
- total bills ;
- marge ;
- marge réelle ;
- pourcentage de marge.

Ce guide ne couvre pas la comptabilité complète : il décrit seulement les suivis de loyers et bills rattachés à la location.

## 12. Maintenance et travaux

### Créer une demande

Depuis le bien ou le contrat de location, utiliser l'assistant Maintenance.

Renseigner :

- Request : sujet de la demande ;
- Property ou Rent Contract ;
- Type de maintenance ;
- Team ;
- client ou prestataire selon le cas.

La demande créée est une `maintenance.request` liée au bien et, si applicable, au contrat de location.

### Facturer ou enregistrer un coût

Sur la demande de maintenance, ajouter les produits de maintenance puis utiliser :

- Create Invoice : facture au client ou au partenaire choisi ;
- Create Bill : facture fournisseur ou coût prestataire.

Les demandes de maintenance alimentent le tableau de bord maintenance : en cours, bloquées, terminées, annulées, correctives, préventives, dues aujourd'hui et en retard.

## 13. Renouvellement ou fin de contrat

### Renouveler

Depuis un contrat existant, relancer l'assistant de contrat ou l'assistant d'extension.

Le renouvellement :

- ferme l'ancien contrat ;
- crée un nouveau contrat ;
- reprend le locataire, le bien, les produits, le dépôt, le broker et les conditions ;
- permet d'appliquer une augmentation de loyer fixe ou en pourcentage ;
- renseigne les références Extend From et Extend Ref.

La date de début du nouveau contrat doit être postérieure à la date de fin du contrat précédent.

### Clôturer

Sur un contrat Running, cliquer sur Close Contract.

Le système bloque la clôture si des factures de loyer restent impayées. Lorsque tout est soldé :

- le contrat passe en Close ;
- la date de terminaison est renseignée ;
- le bien repasse Available.

### Annuler

L'action Cancel Contract :

- passe le contrat en Cancel ;
- renseigne la date de terminaison ;
- remet le bien Available.

Un contrat Running ou Expired ne peut pas être supprimé directement. Il faut d'abord le clôturer ou l'annuler.

## 14. Suivi dans le projet LOCATION

Le projet LOCATION donne une vue opérationnelle du dossier, de la disponibilité à la fin.

### Ce que montre la tâche

La tâche liée au bien affiche notamment :

- bien immobilier ;
- référence bien ;
- image ;
- type et sous-type ;
- projet, phase, référence plan ;
- propriétaire ;
- adresse ;
- prix affiché ;
- date de fin du mandat ;
- type de mandat ;
- client visite ;
- observation de visite.

### Règles de déplacement

PACKIMMO bloque les retours arrière manuels entre VISITE et FIN. Quelques règles à retenir :

- De BIENS DISPONIBLE vers VISITE : passer par Planifier visite.
- De VISITE vers REGULARISATION MANDAT : passer par Valider visite.
- Depuis REGULARISATION MANDAT : pas de retour vers VISITE ou BIENS DISPONIBLE.
- Depuis CONTRAT vers ETAT DES LIEUX : contrat actif obligatoire.
- Depuis ETAT DES LIEUX : pas de retour à une étape précédente.
- Depuis FIN : aucun retour vers une autre étape.

Ces règles protègent l'historique commercial et évitent qu'un dossier finalisé soit remis en circulation par erreur.

## 15. Tableaux de bord Location

Le tableau de bord Rental Dashboard regroupe les indicateurs location et portefeuille.

Il peut afficher notamment :

- KPIs de portefeuille ;
- revenus de location ;
- factures en retard ;
- occupation ;
- prévision ;
- top biens ;
- maintenance ;
- prospects ;
- flux d'activité ;
- répartition des revenus ;
- radar de santé du portefeuille.

Les données sont filtrées par société et période.

### Indicateurs utiles pour la location

- Occupation : part des biens loués.
- Collection : part des factures payées sur les factures émises.
- Contrats : état du parc de contrats.
- Maintenance : suivi des demandes ouvertes et clôturées.
- Croissance : évolution des revenus sur la période.
- Overdue invoices : factures de loyers en retard.
- Leads : prospects liés aux biens.

Si un widget est vide, vérifier :

- présence de biens Location ;
- contrats de location créés et actifs ;
- factures liées aux contrats ;
- factures postées si le widget dépend de la validation ;
- période sélectionnée ;
- société active.

## 16. Rôles et droits des utilisateurs Location

PACKIMMO utilise des groupes métier et un profil de visibilité.

### Groupe Packimmo Location

Le groupe Packimmo Location donne accès aux biens à louer, locataires, contrats, visites et dossiers de location.

Il est destiné aux utilisateurs qui traitent le cycle Location au quotidien :

- consulter et suivre les biens à louer ;
- gérer les prospects location ;
- planifier les visites ;
- suivre les contrats de location ;
- suivre les maintenances liées à la location ;
- utiliser le projet LOCATION selon les permissions accordées.

### Groupe Packimmo Gestionnaire

Le groupe Packimmo Gestionnaire est orienté gestion opérationnelle et administrative.

Il peut intervenir sur :

- tâches ;
- contrats ;
- suivis administratifs ;
- dossiers de gestion ;
- opérations de suivi après mise en location.

Selon la matrice de permissions, ce rôle peut avoir plus de droits de modification ou de validation que l'utilisateur Location simple.

### Groupe Packimmo Manager

Le groupe Packimmo Manager inclut les principaux groupes opérationnels Packimmo, dont Location et Gestionnaire.

Il sert aux responsables qui doivent :

- superviser les dossiers Location ;
- valider ou débloquer les opérations ;
- accéder aux tableaux de bord ;
- contrôler plusieurs périmètres métier ;
- piloter les utilisateurs et les dossiers.

### Profil de visibilité Packimmo

Sur la fiche utilisateur, le champ Profil de visibilité Packimmo limite le périmètre de données :

- Moi uniquement ;
- Mon équipe ;
- Mon agence ;
- Toute la société ;
- Tout.

Options complémentaires :

- voir les archives ;
- voir les brouillons ;
- voir les contrats terminés ;
- voir les biens loués.

Les permissions peuvent être globales ou spécifiques à une société. Si une permission existe pour la société active, elle est prioritaire.

## 17. Bonnes pratiques Location

- Créer ou vérifier le propriétaire avant le bien.
- Ne pas passer un bien disponible tant que le mandat n'est pas actif.
- Ajouter au moins une image claire avant publication.
- Garder le loyer, la surface, la région et le type de bien à jour.
- Lier chaque prospect au bien concerné.
- Utiliser Planifier visite au lieu de déplacer manuellement la tâche.
- Renseigner le locataire trouvé sur le mandat avant la facturation des honoraires.
- Activer le contrat dès que le bail est signé.
- Vérifier la première facture après activation du contrat.
- Ne pas clôturer un contrat tant que les loyers ne sont pas soldés.
- Créer les maintenances depuis le bien ou le contrat pour conserver le lien dossier.

## 18. DATASET MIA - Questions / Réponses Location

### Q1. Comment créer un bien à louer dans PACKIMMO ?

Créer un bien avec Property For = Rent, renseigner le propriétaire, le loyer, l'unité de loyer, l'adresse, le type de bien, les surfaces et les images, puis lier un mandat de location actif avant de le passer disponible.

### Q2. Pourquoi mon bien ne peut-il pas passer en disponible ?

Si le bien appartient à un propriétaire externe, PACKIMMO exige un mandat actif lié au bien. Créer, approuver puis activer le mandat de location avant de rendre le bien disponible.

### Q3. Quel champ indique que le bien est destiné à la location ?

Le champ Property For doit être positionné sur Rent, techniquement `sale_lease = for_tenancy`.

### Q4. Comment créer un mandat de location depuis un bien ?

Depuis la fiche du bien, utiliser le bouton Mandat ou Nouveau mandat. Le propriétaire, le bien, la société et le type d'opération Location sont préremplis.

### Q5. Quels sont les statuts d'un mandat de location ?

Un mandat passe par Brouillon, A valider, Approuvé, Actif, puis Terminé, Expiré ou Annulé selon le traitement.

### Q6. Que fait l'action Activer sur un mandat ?

Elle passe le mandat en Actif et rend disponibles les biens liés au mandat qui étaient encore en brouillon.

### Q7. Comment calculer la caution d'un mandat de location ?

La caution peut être calculée par nombre de mois de loyer, montant fixe ou pourcentage du loyer annuel. PACKIMMO calcule automatiquement le montant de caution.

### Q8. Comment publier un bien à louer sur le site ?

Le bien doit être en Location, ne plus être en Draft, avoir ses informations commerciales renseignées et être accessible via la page `/properties-list?sale_lease=for_tenancy`.

### Q9. Où voit-on les prospects d'un bien à louer ?

Depuis la fiche du bien, utiliser les boutons Leads ou Opportunity. Les prospects sont des CRM Leads liés au champ Property.

### Q10. Comment planifier une visite ?

Dans le kanban LOCATION, ouvrir la tâche du bien en BIENS DISPONIBLE, cliquer sur Planifier une visite, choisir le client et confirmer.

### Q11. Que se passe-t-il après confirmation d'une visite ?

La tâche du bien passe en VISITE et une sous-tâche de visite est créée avec le client et l'observation.

### Q12. Comment annuler une visite ?

Annuler la sous-tâche de visite. Si le dossier n'est pas en régularisation, le bien revient en BIENS DISPONIBLE.

### Q13. Comment sélectionner le locataire après une visite ?

Valider la sous-tâche de visite. Le dossier passe en REGULARISATION MANDAT, puis le mandat est complété avec le locataire retenu.

### Q14. Quand peut-on créer le contrat de location ?

Après régularisation du mandat, si les règles du mandat autorisent le contrat. Pour les mandats simples ou exclusifs, la création du bail peut être bloquée.

### Q15. Que crée l'assistant de contrat ?

Il crée un contrat de location `tenancy.details` avec le locataire, le bien, le loyer, la durée, le dépôt, les services, la maintenance, le broker et les conditions.

### Q16. Que fait l'activation d'un contrat de location ?

Elle génère la première facture, ajoute le dépôt et les services prévus, passe le contrat en Running et conserve la date de dernière facturation.

### Q17. Où trouver les factures de loyer ?

Dans Renting > Invoices ou depuis le smart button Invoices du contrat de location.

### Q18. Comment créer une facture supplémentaire sur un contrat ?

Utiliser l'assistant de paiement du contrat pour créer une facture de dépôt, maintenance, pénalité, service extra ou autre motif.

### Q19. Comment suivre les dépenses liées à une location ?

Utiliser les Bills du contrat ou créer une facture fournisseur depuis l'assistant de paiement ou une demande de maintenance.

### Q20. Comment créer une maintenance pour un locataire ?

Depuis le contrat de location, lancer l'assistant Maintenance, renseigner le sujet, le type et l'équipe. La demande sera liée au contrat et au bien.

### Q21. Comment passer en état des lieux ?

Dans le projet LOCATION, le passage vers ETAT DES LIEUX est possible lorsque les conditions du workflow sont remplies. Depuis CONTRAT, un contrat actif lié au bien est obligatoire.

### Q22. Pourquoi le kanban LOCATION refuse-t-il un retour en arrière ?

PACKIMMO bloque les retours manuels entre VISITE et FIN pour protéger l'historique du dossier et éviter une remise en circulation incorrecte.

### Q23. Comment renouveler un contrat de location ?

Depuis le contrat, utiliser l'assistant de renouvellement ou de contrat. Le système ferme l'ancien contrat et crée un nouveau contrat avec possibilité d'augmenter le loyer.

### Q24. Comment clôturer un contrat de location ?

Utiliser Close Contract sur un contrat Running. Le système refuse la clôture si des factures de loyer restent impayées.

### Q25. Que devient le bien après clôture du contrat ?

Lorsque le contrat est clôturé ou annulé, le bien repasse Available.

### Q26. Quel rôle donner à un agent de location ?

Attribuer le groupe Packimmo Location, puis choisir un profil de visibilité adapté : Moi uniquement, Mon équipe, Mon agence ou Toute la société.

### Q27. Quel rôle donner à un responsable location ?

Attribuer Packimmo Manager si la personne supervise et valide plusieurs dossiers. Attribuer Packimmo Gestionnaire si elle gère surtout le suivi administratif et opérationnel.

### Q28. Pourquoi un utilisateur ne voit-il pas tous les biens à louer ?

Vérifier son groupe Packimmo, son profil de visibilité, sa société active et les options comme voir les brouillons, biens loués ou contrats terminés.

### Q29. Que contient le tableau de bord Location ?

Il présente les KPIs de portefeuille, revenus, occupation, factures en retard, prospects, maintenance, activité récente, top biens et indicateurs de santé du portefeuille.

### Q30. Pourquoi un indicateur du dashboard est-il vide ?

Vérifier la société, la période, l'existence de biens Location, de contrats actifs, de factures liées et de données de maintenance ou prospects selon le widget.
