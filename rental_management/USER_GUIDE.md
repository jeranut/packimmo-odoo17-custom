# Guide Utilisateur - Tableau de Bord Rental Management

## 📊 Santé du Portefeuille (Vue Radar)

### Qu'est-ce que c'est?

La **vue Radar** affiche une représentation visuelle de la **santé globale de votre portefeuille immobilier** à travers 6 dimensions clés. Elle permet de comparer votre performance **période actuelle vs période précédente** en un coup d'œil.

### Les 6 Indicateurs de Santé

#### 1️⃣ **Occupation** 
- **Définition**: Pourcentage de propriétés actuellement louées
- **Calcul**: (Propriétés en location / Total propriétés) × 100
- **Cible**: 100% = toutes les propriétés sont louées
- **Impact**: Plus élevé = meilleures revenus

#### 2️⃣ **Rendement (Yield)**
- **Définition**: Rendement annuel de votre portefeuille
- **Calcul**: (Loyer annuel / Valeur propriété) × 100, normalisé à 15% = 100 points
- **Exemple**: 
  - 15% de yield annuel = 100 points
  - 7.5% de yield annuel = 50 points
- **Impact**: Indicateur clé de rentabilité

#### 3️⃣ **Collection**
- **Définition**: Taux de recouvrement - part des factures réellement payées
- **Calcul**: (Montant payé / Montant facturé) × 100
- **Cible**: 100% = tous les paiements reçus
- **Alerte**: < 90% = problème de recouvrement à investiguer

#### 4️⃣ **Maintenance**
- **Définition**: Santé du processus de maintenance
- **Calcul**: (Tickets fermés / Total tickets) × 100
- **Cible**: 100% = tous les problèmes réglés
- **Implication**: Gestion préventive vs corrective

#### 5️⃣ **Contrats**
- **Définition**: Santé de votre base de contrats actifs
- **Calcul**: (Contrats actifs / Total contrats) × 100
- **Statuts comptés**: "running_contract" et "new_contract"
- **Cible**: 100% = contrats stables et renouvelables

#### 6️⃣ **Croissance**
- **Définition**: Croissance des revenus d'une période à l'autre
- **Calcul**: (Revenus actuels / Revenus période -1) × 50, plafonné à 100
- **Exemple**:
  - 50% croissance = 100 points
  - 100% croissance (doublement) = 100 points (plafonné)
  - 0% croissance = 0 points
- **Significatif**: Tendance à la hausse ou baisse

### Comment Lire le Radar

```
        Occupation
             ↑
            /\
    Contrats    Rendement
         /  \
        /    \
Croissance    Collection
        \    /
         \  /
      Maintenance
```

- **Légende bleu foncé** = Performance **Actuelle**
- **Légende teal pointillée** = Performance **Période Précédente**
- **Zone remplie** = Plus grande la surface = meilleures performances

### Cas d'Usage

#### 🟢 **Radar Équilibré et Ample**
- ✅ Portefeuille en excellente santé
- ✅ Toutes les dimensions performantes
- ✅ Croissance soutenue

#### 🟡 **Radar avec Un ou Deux Creux**
- ⚠️ Un indicateur faible détecté
- Exemples:
  - Collection basse → problème de recouvrement
  - Maintenance basse → arriérés d'entretien
  - Contrats bas → base fragile

#### 🔴 **Radar Peu Ample / Tous Bas**
- 🚨 Problème systémique
- À investiguer immédiatement
- Possible: pas de données, mauvaise saisie, crise opérationnelle

### Quelle Période est Affichée?

- **Actuel (Bleu)**: La période que vous avez sélectionnée dans les filtres
- **Précédent (Teal pointillé)**: La même durée, une période avant
  - Si vous sélectionnez "31/05/2026 - 29/06/2026" (30 jours)
  - Le précédent sera "01/05/2026 - 30/05/2026" (30 jours)

---

## 💰 Répartition des Revenus (Diagramme Donut)

### Qu'est-ce que c'est?

La **Répartition des revenus** visualise **comment vos revenus sont distribués par type de bien** durant la période sélectionnée. C'est un diagramme donut qui montre la composition de votre portfolio en termes générateurs de revenu.

### Types de Bien Affichés

- 🏘️ **Résidentiel** - Appartements, maisons, studios, etc.
- 🏢 **Commercial** - Bureaux, commerces, locaux professionnels
- 🏭 **Industriel** - Hangars, usines, zones logistiques
- 🌾 **Terrain** - Terrains non construits

### Comment Est Calculé?

```sql
SELECT type_de_bien, 
       SUM(amount_factured) as revenue
FROM invoices
WHERE status = 'validée'
  AND type_facture = 'vente_location'
  AND date BETWEEN period_start AND period_end
GROUP BY type_de_bien
```

**Critères d'inclusion:**
- ✅ Factures **validées** (state = 'posted')
- ✅ Factures de **location** (type = 'out_invoice')
- ✅ Au moins un **contrat de location actif** sur la propriété
- ✅ Period sélectionnée dans les filtres

### Lecture du Diagramme

```
        Résidentiel (45%)
              ↗
    
    Commercial → Diagramme Donut ← Industriel (15%)
    (30%)              ↓
           
        Terrain (10%)
```

**Les segments:**
- Plus grand le segment = plus gros contributeur aux revenus
- Voir le % et le montant en euros au survol
- Cliquer sur un segment pour filtrer par type

### Pourquoi C'est Vide?

Si vous voyez **"Aucune répartition des revenus"**, c'est parce que:

| Cause | Diagnostic |
|-------|-----------|
| Aucune facture validée | Vérifier les statuts dans Factures > Ventes |
| Pas de locations actives | Ajouter des contrats de location |
| Factures non liées | S'assurer les factures référencent les tenancies |
| Période incorrecte | Vérifier le filtre date - élargir la période |
| Mauvaise société sélectionnée | Changer de société dans le sélecteur |
| Revenus à zéro | Vérifier les montants des factures (> 0) |

### Comment Corriger

**Étape 1 - Vérifier les Factures**
```
Menu > Factures > Ventes
Filtrer: État = "Validée"
Si aucune facture → Créer des factures de location
```

**Étape 2 - Vérifier les Contrats**
```
Menu > Locations > Contrats de Location
Vérifier: Statut = "Actif" ET Propriété a un type
```

**Étape 3 - Vérifier la Période**
```
Dashboard: Cocher une période plus large
Exemple: Dernier trimestre au lieu d'un mois
```

**Étape 4 - Vérifier la Société**
```
Haut-droit: Sélecteur d'entreprise
S'assurer de choisir la bonne société
```

---

## 🔄 Interaction Entre les Deux Vues

### Lien Logique

```
Factures Validées (account_move)
    ↓
Liées à Contrats (tenancy_details)
    ↓
Liées à Propriétés (property_details)
    ↓
Agrégées par PÉRIODE + TYPE
    ├─→ Répartition des Revenus (par TYPE)
    ├─→ Radar - Collection (taux payé/facturé)
    ├─→ Radar - Croissance (YoY)
    └─→ Radar - Rendement (valeur/loyer)
```

### Cohérence des Données

- ✅ Les revenus du Radar (Collection, Croissance) = mêmes factures que Répartition
- ✅ Augmentation dans Répartition = Augmentation dans Radar Croissance
- ✅ Collection basse = factureilles impayées = problème Radar Collection

---

## 📋 Checklist - Configuration Requise

### Pour que la Répartition des Revenus Fonctionne

- [ ] Au moins une **Facture de vente validée**
- [ ] Facture liée à un **Contrat de location**
- [ ] Contrat lié à une **Propriété avec type**
- [ ] Montants des factures **> 0 €**
- [ ] Propriété et facture même **société**
- [ ] Période sélectionnée contient la facture

### Pour que le Radar Fonctionne

- [ ] Au moins une **Propriété avec type et prix**
- [ ] Au moins un **Contrat de location**
- [ ] Au moins une **Facture de vente validée**
- [ ] Au moins une **Demande de maintenance** (pour Maintenance)
- [ ] Données réparties sur **2 périodes minimum** (pour comparaison)

---

## 🎯 Bonnes Pratiques

### Pour une Répartition Pertinente

1. **Validez régulièrement vos factures** - Ne pas rester en brouillon
2. **Utilisez des périodes cohérentes** - Mois ou trimestre
3. **Liez les factures aux contrats** - Traçabilité complète
4. **Gardez les types de propriétés à jour** - Classification claire

### Pour un Radar Représentatif

1. **Comparaison périodique** - Regarder chaque mois/trimestre
2. **Identifiez les tendances** - Croissance vs déclin
3. **Agissez sur les creux** - Collection basse → relance clients
4. **Trackez les améliorations** - Avant/après actions correctives

---

## 🔧 Support & Dépannage

### Questions Fréquentes

**Q: Le Radar montre 0 partout**
> A: Vérifier qu'il y a des données pour la période. Élargir la plage de dates.

**Q: Répartition des revenus vide mais j'ai des factures**
> A: Vérifier que les factures sont validées (state='posted'), pas en brouillon.

**Q: Croissance très basse / négative**
> A: Normal si revenus en baisse. Analyser les contrats expirés ou clients perdus.

**Q: Collection à 50%, que faire?**
> A: Relancer les clients avec paiements impayés. Vérifier les conditions de paiement.

---

## 📧 Contact Support

Pour toute question, contactez l'équipe Rental Management.

**Document version**: 1.0  
**Dernière mise à jour**: Juin 2026
