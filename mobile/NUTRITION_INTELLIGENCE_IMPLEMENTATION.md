# Intelligence Nutritionnelle - Implémentation Complète

## 📋 Résumé

Ajout d'un **système d'intelligence nutritionnelle** qui corrèle automatiquement l'alimentation avec les métriques de santé pour générer des insights actionnables.

**Format** : Nutrition → Conséquence → Action

**Objectif** : Transformer le journal alimentaire d'un outil de tracking passif en **coach nutrition intelligent** qui détecte, explique et recommande.

---

## ✅ Fichiers Créés

### 1. Moteur de détection - `useNutritionInsights.ts`
**Localisation** : `/mobile/src/hooks/useNutritionInsights.ts`

**Responsabilité** :
- Corrèle données nutrition × santé
- Détecte 6 types de patterns automatiquement
- Génère insights avec observation + conséquence + action
- Calcule score de confiance (0-1)
- Trie par sévérité

**Types d'insights détectés** :
1. 🍽️ **Repas tardifs** → Sommeil fragmenté
2. 💪 **Protéines** → Récupération (positif/négatif)
3. 🍷 **Alcool** → HRV réduite
4. ☕ **Caféine tardive** → Sommeil affecté
5. 💧 **Hydratation** → Performance (positif/négatif)
6. 🍞 **Glucides** → Niveau d'énergie

**Algorithmes clés** :
```typescript
// Exemple: Repas tardifs
if (mealHour >= 20 && sleepFragmentation > 3) {
  confidence = 0.75 + (mealHour - 20) * 0.05;
  return insight;
}

// Exemple: Alcool + HRV
const hrvDrop = ((baseline - hrv) / baseline) * 100;
if (alcohol >= 2 && hrvDrop > 10) {
  severity = alcohol >= 4 ? 'alert' : 'warning';
  confidence = 0.85;
  return insight;
}
```

---

### 2. Agrégateur de données - `useNutritionHealthData.ts`
**Localisation** : `/mobile/src/hooks/useNutritionHealthData.ts`

**Responsabilité** :
- Récupère données nutrition (food_logs, food_log_items)
- Récupère données santé (biometrics, daily_state, user_baselines)
- Agrège tout dans un format unifié
- Cache via React Query (5 min)

**Sources Supabase** :
```typescript
// Nutrition
- food_logs (repas du jour)
- food_log_items (détail composition)
→ Calcule: protéines, glucides, calories, timing repas

// Santé
- biometrics (HRV, sommeil, calories actives)
- daily_state (recovery, energy)
- user_baselines (HRV baseline personnelle)
→ Extrait: HRV, qualité sommeil, réveils, récupération
```

**Données retournées** :
```typescript
{
  nutrition: {
    lastMealTime, proteinIntake, alcoholUnits,
    caffeineIntake, caffeineLastTime, waterIntake,
    carbsIntake, caloriesIntake
  },
  health: {
    sleepQuality, sleepDuration, sleepFragmentation,
    hrv, hrvBaseline, recovery, energyLevel, activeCalories
  }
}
```

---

### 3. Composant UI - `NutritionInsightCard.tsx`
**Localisation** : `/mobile/src/components/NutritionInsightCard.tsx`

**Responsabilité** :
- Affiche un insight avec flow visuel clair
- 2 modes : complet (Journal) et compact (Brief)
- Badges de sévérité colorés
- Score de confiance affiché

**Mode complet (Journal)** :
```
┌────────────────────────────────────┐
│ 🍷 Impact alcool détecté      [⚠️] │
│ Fiabilité: 85%                     │
│                                    │
│ • OBSERVATION                      │
│   3 unités d'alcool hier           │
│         ↓                          │
│ • CONSÉQUENCE                      │
│   HRV réduite de 15%               │
│         ↓                          │
│ • ACTION                           │
│   Limite à 1-2 verres maximum      │
└────────────────────────────────────┘
```

**Mode compact (Brief - optionnel)** :
```
┌────────────────────────────────────┐
│ 🍷 Impact alcool détecté           │
│ 3 unités → HRV -15%                │
│ 💡 Limite à 1-2 verres             │
└────────────────────────────────────┘
```

**Composant liste** : `<NutritionInsightsList>` pour afficher plusieurs insights groupés.

---

### 4. Documentation - `nutrition-intelligence.md`
**Localisation** : `/mobile/docs/nutrition-intelligence.md`

**Contenu** (500+ lignes) :
- Description de chaque type d'insight
- Algorithmes de détection détaillés
- Architecture technique complète
- Niveaux de sévérité et confidence
- Interface utilisateur
- Cas limites et gestion d'erreurs
- Tests de validation
- Évolutions futures (Phase 2-4)
- Références scientifiques

---

## 🔧 Fichiers Modifiés

### Écran Journal - `journal.tsx`
**Localisation** : `/mobile/app/(tabs)/journal.tsx`

**Modifications** :

#### Imports ajoutés
```typescript
import { useAuth } from '@/hooks/useAuth'
import { useNutritionHealthData } from '@/hooks/useNutritionHealthData'
import { useNutritionInsights } from '@/hooks/useNutritionInsights'
import { NutritionInsightsList } from '@/components/NutritionInsightCard'
```

#### Logique ajoutée
```typescript
const { userId } = useAuth()

// Récupérer données nutrition + santé
const { data: nutritionHealthData, isLoading: insightsLoading } = 
  useNutritionHealthData(userId, selectedDate)

// Calculer insights
const nutritionInsights = useNutritionInsights(
  nutritionHealthData?.nutrition,
  nutritionHealthData?.health
)
```

#### Affichage ajouté
```typescript
{/* Après NutritionSummary, avant MealCards */}
{!insightsLoading && nutritionInsights.hasData && (
  <NutritionInsightsList insights={nutritionInsights.insights} />
)}
```

**Position dans le layout** :
1. Header (titre + date)
2. Résumé nutrition totale
3. **🆕 Insights nutrition intelligents**
4. Cartes de repas (breakfast, lunch, dinner, snack)
5. État vide / Loading / Erreur

---

## 🎯 Types d'Insights Détaillés

### 1. 🍽️ Repas tardifs → Sommeil fragmenté

**Conditions** :
- Dernier repas ≥ 20h
- ET sommeil fragmenté > 3 réveils

**Sévérité** : `warning` (orange)

**Confidence** : 0.75-0.95 (augmente avec l'heure du repas)

**Action** : "Termine ton dernier repas avant 19h30 pour améliorer ton sommeil."

---

### 2. 💪 Protéines → Récupération

**Conditions positives** :
- Protéines ≥ 80g
- ET récupération ≥ 70%

**Conditions warning** :
- Protéines < 60g
- ET récupération < 60%

**Sévérité** : `positive` (vert) ou `warning` (orange)

**Confidence** : 0.80 (positif), 0.65 (warning)

**Actions** :
- Positif : "Continue cet apport, il soutient bien ta récupération."
- Warning : "Vise 1.6-2g de protéines par kg de poids corporel."

---

### 3. 🍷 Alcool → HRV réduite

**Conditions** :
- Alcool ≥ 2 unités
- ET HRV réduite > 10% sous baseline

**Sévérité** : 
- `alert` (rouge) si ≥4 unités
- `warning` (orange) si 2-3 unités

**Confidence** : 0.85

**Actions** :
- Alert : "Évite l'alcool les 2-3 prochains jours pour récupération complète."
- Warning : "Limite à 1-2 verres maximum pour maintenir HRV optimale."

---

### 4. ☕ Caféine tardive → Sommeil affecté

**Conditions** :
- Caféine > 100mg
- Dernier café ≥ 16h
- ET qualité sommeil < 60%

**Sévérité** : `warning` (orange)

**Confidence** : 0.75

**Action** : "Coupe la caféine après 14h pour préserver ton sommeil."

---

### 5. 💧 Hydratation → Performance

**Conditions warning** :
- Activité intense > 500 kcal
- ET eau < 1500mL

**Conditions positives** :
- Activité intense > 500 kcal
- ET eau ≥ 2500mL

**Sévérité** : `warning` ou `positive`

**Confidence** : 0.70-0.75

**Actions** :
- Warning : "Vise 2-3L d'eau les jours d'entraînement intense."
- Positif : "Continue, c'est parfait pour ton niveau d'activité."

---

### 6. 🍞 Glucides → Niveau d'énergie

**Conditions** :
- Glucides < 100g
- ET énergie < 50%

**Sévérité** : `warning` (orange)

**Confidence** : 0.65

**Action** : "Ajoute glucides complexes (riz, pâtes, pain complet) pour restaurer énergie."

---

## 🎨 Design System

### Niveaux de sévérité

| Niveau | Couleur | Hex | Icône | Usage |
|--------|---------|-----|-------|-------|
| `alert` | Rouge | #FF3B30 | ⚠️ AlertCircle | Impact critique |
| `warning` | Orange | #FF9500 | ↘ TrendingDown | Impact modéré |
| `positive` | Vert | #00FF41 | ↗ TrendingUp | Pattern positif |
| `neutral` | Gris | #8E8E93 | ℹ️ Info | Information neutre |

### Badges de couleur

Chaque insight a :
- **Badge de sévérité** (haut droite) : Icône + fond coloré
- **Dots de couleur** : Guident le flow Observation → Conséquence → Action
  - Observation : Cyan (#00C7BE)
  - Conséquence : Couleur de sévérité
  - Action : Vert (#00FF41)

### Typographie

| Élément | Taille | Poids | Couleur |
|---------|--------|-------|---------|
| Titre | 16px | 700 | #FFFFFF |
| Confiance | 11px | 400 | #8E8E93 |
| Label flow | 11px | 600 | #8E8E93 |
| Valeur flow | 14px | 400 | #FFFFFF |
| Action | 14px | 600 | #00FF41 |
| Emoji | 28px | - | - |

---

## 📊 Flow de Données

```
┌─────────────────────────────────────────┐
│ Supabase Database                       │
├─────────────────────────────────────────┤
│ • food_logs (repas du jour)             │
│ • food_log_items (composition)          │
│ • biometrics (HRV, sommeil, etc.)       │
│ • daily_state (recovery, energy)        │
│ • user_baselines (HRV baseline)         │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ useNutritionHealthData()                │
│ Hook React Query                        │
├─────────────────────────────────────────┤
│ 1. Fetch food_logs → Calcul protéines  │
│ 2. Fetch biometrics → Extraction HRV   │
│ 3. Fetch daily_state → Récupération    │
│ 4. Fetch baselines → HRV baseline      │
│ 5. Agrégation finale                    │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ useNutritionInsights()                  │
│ Hook useMemo                            │
├─────────────────────────────────────────┤
│ 1. detectLateMeal()                     │
│ 2. detectProteinRecovery()              │
│ 3. detectAlcoholHRV()                   │
│ 4. detectCaffeineSleep()                │
│ 5. detectHydrationPerformance()         │
│ 6. detectCarbsEnergy()                  │
│ 7. Tri par sévérité                     │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ <NutritionInsightsList>                 │
│ Composant React                         │
├─────────────────────────────────────────┤
│ Map insights → <NutritionInsightCard>   │
│ Affichage dans Journal alimentaire      │
└─────────────────────────────────────────┘
```

---

## 🔍 Cas Limites Gérés

### 1. Données manquantes

Si une donnée clé manque, l'insight n'est pas généré :
```typescript
if (!nutritionData.lastMealTime || !healthData.sleepFragmentation) {
  return null; // Pas d'insight "repas tardifs"
}
```

### 2. Aucun pattern détecté

Si données OK mais pas de corrélation :
```typescript
// Alcool consommé mais HRV normale
if (alcohol >= 2 && hrvDrop <= 10) {
  return null; // Pas d'alerte
}

// UI
{nutritionInsights.hasData ? (
  <NutritionInsightsList insights={nutritionInsights.insights} />
) : null}
```

### 3. Données partielles

Le système génère uniquement les insights possibles :
```typescript
// Exemple: Seulement protéines + recovery disponibles
insights = [
  proteinRecoveryInsight,  // ✅ Généré
  // alcoholHRVInsight,    // ❌ Données alcool manquantes
  // caffeineSleepInsight, // ❌ Données caféine manquantes
];
```

### 4. Multiples insights

Plusieurs insights peuvent coexister et sont triés par sévérité :
```typescript
insights = [
  alcoholHRVInsight,          // alert (rouge)
  lateMealSleepInsight,       // warning (orange)
  proteinRecoveryInsight,     // positive (vert)
];
// Ordre: alert → warning → positive → neutral
```

---

## 🚀 Déploiement

### Checklist pré-déploiement

- [x] Hook `useNutritionInsights` créé
- [x] Hook `useNutritionHealthData` créé
- [x] Composant `NutritionInsightCard` créé
- [x] Intégration dans `journal.tsx`
- [x] Documentation technique complète
- [x] Vérification linter (0 erreur)
- [ ] Test manuel avec données réelles
- [ ] Validation sur device iOS
- [ ] Validation sur simulator Android
- [ ] Test avec données partielles
- [ ] Test avec aucune donnée
- [ ] Performance check (chargement < 1s)

### Commandes de validation

```bash
# Linter
cd mobile && npx eslint src/hooks/useNutrition*.ts src/components/NutritionInsight*.tsx

# TypeScript
cd mobile && npx tsc --noEmit

# Build
cd mobile && npx expo start
```

---

## 📈 Métriques de Succès

### KPIs à surveiller post-déploiement

| Métrique | Baseline | Cible (1 mois) |
|----------|----------|----------------|
| Insights générés par jour (moyenne) | 0 | 1-3 |
| % utilisateurs avec ≥1 insight/semaine | 0% | 70% |
| Actions suivies suite aux insights | - | 40% |
| NPS "utilité insights" | - | 8/10 |
| Temps sur écran Journal | 20s | 45s |

### Feedback attendu

- ✅ "Enfin je comprends l'impact de mon alimentation !"
- ✅ "Les conseils sont actionnables et personnalisés"
- ✅ "Le format Observation → Conséquence → Action est clair"
- ✅ "J'ai changé l'heure de mon dernier repas grâce à ça"

---

## 🔮 Évolutions Futures

### Phase 2 : Historique et trends (Q2 2026)

**Objectif** : Analyser les patterns sur plusieurs jours/semaines

**Exemples** :
- "3 repas tardifs cette semaine → sommeil dégradé de 12%"
- "Depuis que tu coupes la caféine à 14h (7 jours), sommeil +18%"
- "Corrélation forte: protéines >80g les jours sport → récupération +22%"

**Implémentation** :
- Nouveau hook `useLongitudinalInsights(userId, weeks: number)`
- Graphiques de corrélation
- Calcul de trends (amélioration/détérioration)

---

### Phase 3 : Recommandations proactives (Q3 2026)

**Objectif** : Prédire et prévenir plutôt que constater

**Exemples** :
- "Si tu manges tard ce soir, risque sommeil fragmenté: 75%"
- "Ton corps fonctionne mieux avec dernier repas entre 18h30-19h30"
- "Jours d'entraînement: vise 100g+ protéines pour récupération optimale"

**Implémentation** :
- Modèles ML simples (régression logistique)
- Recommandations timing personnalisées
- Notifications push préventives

---

### Phase 4 : Intelligence contextuelle (Q4 2026)

**Objectif** : Facteurs multiples et interactions

**Exemples** :
- "Alcool + repas tardif + stress → impact sommeil multiplié (×3)"
- "En voyage: hydratation critique, vise 3L+ eau"
- "Objectif perte de poids: déficit 300 kcal + protéines 1.8g/kg"

**Implémentation** :
- Intégration contexte (stress, voyage, objectifs)
- Détection interactions complexes
- Recommandations multi-facteurs

---

## 🧪 Tests de Validation

### Scénarios de test clés

| # | Scénario | Données | Insight attendu |
|---|----------|---------|-----------------|
| 1 | Repas tardif | Repas 21h + 5 réveils | 🍽️ Repas tardif → Sommeil fragmenté |
| 2 | Protéines optimales | 95g protéines + récup 82% | 💪 Excellente nutrition sportive |
| 3 | Protéines insuffisantes | 45g protéines + récup 52% | 🥩 Apport protéique insuffisant |
| 4 | Alcool modéré | 3 unités + HRV -15% | 🍷 Impact alcool → HRV réduite |
| 5 | Alcool élevé | 4+ unités + HRV -20% | 🍷 [ALERT] Impact alcool critique |
| 6 | Caféine tardive | Café 17h + sommeil 52% | ☕ Caféine tardive → Sommeil affecté |
| 7 | Hydratation faible | 1200mL + 620 kcal actives | 💧 Hydratation insuffisante |
| 8 | Hydratation optimale | 2800mL + 550 kcal actives | 💧 Hydratation optimale |
| 9 | Glucides faibles | 75g glucides + énergie 42% | 🍞 Glucides insuffisants |
| 10 | Données normales | Tout normal | Aucun insight (hasData = false) |
| 11 | Données partielles | Seulement protéines disponibles | 1 insight (protéines) |
| 12 | Aucune donnée | userId null | Aucun insight |

---

## 📚 Références

### Fichiers du projet
- `/mobile/src/hooks/useNutritionInsights.ts` - Moteur détection
- `/mobile/src/hooks/useNutritionHealthData.ts` - Agrégateur données
- `/mobile/src/components/NutritionInsightCard.tsx` - Composant UI
- `/mobile/app/(tabs)/journal.tsx` - Intégration journal
- `/mobile/docs/nutrition-intelligence.md` - Documentation technique

### Études scientifiques
- [Sleep and meal timing (2020)](https://pubmed.ncbi.nlm.nih.gov/31851909/)
- [Protein and recovery (2018)](https://pubmed.ncbi.nlm.nih.gov/29497353/)
- [Alcohol and HRV (2006)](https://pubmed.ncbi.nlm.nih.gov/16243846/)
- [Caffeine and sleep quality (2013)](https://pubmed.ncbi.nlm.nih.gov/24235903/)

---

**Version** : 1.0  
**Date d'implémentation** : 2026-01-30  
**Auteur** : Pulse Engineering Team  
**Status** : ✅ Implémenté, prêt pour tests manuels
