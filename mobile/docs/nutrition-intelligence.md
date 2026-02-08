#### Intelligence Nutritionnelle - Documentation

## Vue d'ensemble

Le système d'**Intelligence Nutritionnelle** corrèle automatiquement les données alimentaires avec les métriques de santé pour générer des insights actionnables.

**Format** : Nutrition → Conséquence → Action

### Objectif

Transformer le journal alimentaire d'un simple outil de tracking en **coach nutrition intelligent** qui :
- ✅ Détecte les patterns nutrition <-> santé
- ✅ Explique les conséquences sur le corps
- ✅ Propose des actions concrètes

---

## Types d'Insights

### 1. 🍽️ Repas tardifs → Sommeil fragmenté

**Détection** :
- Dernier repas après 20h
- ET sommeil fragmenté (>3 réveils)

**Exemple** :
```
🍽️ Repas tardif détecté
Observation: Dernier repas à 21h
Conséquence: Sommeil fragmenté (5 réveils)
Action: Termine ton dernier repas avant 19h30 pour améliorer ton sommeil.
```

**Algorithme** :
```typescript
if (mealHour >= 20 && sleepFragmentation > 3) {
  confidence = 0.75 + (mealHour - 20) * 0.05; // Max 0.95
  severity = 'warning';
}
```

---

### 2. 💪 Protéines → Récupération

**Détection (Positive)** :
- Apport protéique élevé (≥80g)
- ET bonne récupération (≥70%)

**Détection (Warning)** :
- Apport protéique faible (<60g)
- ET récupération limitée (<60%)

**Exemples** :

**Positif** :
```
💪 Excellente nutrition sportive
Observation: 95g de protéines
Conséquence: Récupération optimale (82%)
Action: Continue cet apport protéique, il soutient bien ta récupération.
```

**Warning** :
```
🥩 Apport protéique insuffisant
Observation: Seulement 45g de protéines
Conséquence: Récupération limitée (52%)
Action: Vise 1.6-2g de protéines par kg de poids corporel.
```

**Algorithme** :
```typescript
// Positif
if (protein >= 80 && recovery >= 70) {
  confidence = 0.80;
  severity = 'positive';
}

// Warning
if (protein < 60 && recovery < 60) {
  confidence = 0.65;
  severity = 'warning';
}
```

---

### 3. 🍷 Alcool → HRV réduite

**Détection** :
- Consommation d'alcool (≥2 unités)
- ET HRV réduite (>10% sous baseline)

**Exemple** :
```
🍷 Impact alcool détecté
Observation: 3 unités d'alcool hier
Conséquence: HRV réduite de 15% (42ms vs 50ms)
Action: Limite à 1-2 verres maximum si tu veux maintenir une HRV optimale.
```

**Sévérité** :
- ≥4 unités : `alert` (rouge)
- 2-3 unités : `warning` (orange)

**Algorithme** :
```typescript
const hrvDrop = ((baseline - hrv) / baseline) * 100;

if (alcohol >= 2 && hrvDrop > 10) {
  severity = alcohol >= 4 ? 'alert' : 'warning';
  confidence = 0.85;
}
```

---

### 4. ☕ Caféine tardive → Sommeil affecté

**Détection** :
- Caféine >100mg
- Dernier café après 16h
- ET qualité sommeil <60%

**Exemple** :
```
☕ Caféine tardive détectée
Observation: 240mg de caféine, dernier café à 17h
Conséquence: Qualité de sommeil réduite (52%)
Action: Coupe la caféine après 14h pour préserver ton sommeil.
```

**Algorithme** :
```typescript
const lastCaffeineHour = new Date(caffeineLastTime).getHours();

if (caffeine > 100 && lastCaffeineHour >= 16 && sleepQuality < 60) {
  confidence = 0.75;
  severity = 'warning';
}
```

---

### 5. 💧 Hydratation → Performance

**Détection (Warning)** :
- Activité intense (>500 kcal actives)
- ET hydratation faible (<1500mL)

**Détection (Positive)** :
- Activité intense (>500 kcal actives)
- ET bonne hydratation (≥2500mL)

**Exemples** :

**Warning** :
```
💧 Hydratation insuffisante
Observation: Seulement 1200mL d'eau
Conséquence: Activité intense (620 kcal brûlées)
Action: Vise 2-3L d'eau par jour les jours d'entraînement intense.
```

**Positif** :
```
💧 Hydratation optimale
Observation: 2.8L d'eau
Conséquence: Soutien optimal de ta performance
Action: Continue cette hydratation, c'est parfait pour ton niveau d'activité.
```

**Algorithme** :
```typescript
// Warning
if (activeCalories > 500 && water < 1500) {
  confidence = 0.70;
  severity = 'warning';
}

// Positif
if (activeCalories > 500 && water >= 2500) {
  confidence = 0.75;
  severity = 'positive';
}
```

---

### 6. 🍞 Glucides → Niveau d'énergie

**Détection** :
- Apport glucides faible (<100g)
- ET niveau d'énergie bas (<50%)

**Exemple** :
```
🍞 Glucides insuffisants
Observation: Seulement 75g de glucides
Conséquence: Niveau d'énergie bas (42%)
Action: Ajoute des glucides complexes (riz, pâtes, pain complet).
```

**Algorithme** :
```typescript
if (carbs < 100 && energy < 50) {
  confidence = 0.65;
  severity = 'warning';
}
```

---

## Architecture Technique

### Fichiers

| Fichier | Responsabilité |
|---------|----------------|
| `useNutritionInsights.ts` | Moteur de détection des corrélations |
| `useNutritionHealthData.ts` | Agrégation données nutrition + santé |
| `NutritionInsightCard.tsx` | Composant UI pour afficher insights |
| `journal.tsx` | Intégration dans le journal alimentaire |

### Flow de données

```
┌─────────────────────────────────────────┐
│ Supabase                                │
│ ├─ food_logs                            │
│ ├─ food_log_items                       │
│ ├─ biometrics (HRV, sommeil, etc.)     │
│ ├─ daily_state (recovery, energy)       │
│ └─ user_baselines (HRV baseline)        │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ useNutritionHealthData()                │
│ Agrège nutrition + santé                │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ useNutritionInsights()                  │
│ Détecte corrélations                    │
│ Génère insights actionnables            │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ <NutritionInsightsList>                 │
│ Affiche insights dans le Journal        │
└─────────────────────────────────────────┘
```

### Sources de données

**Nutrition** :
```typescript
{
  lastMealTime?: string;       // ISO timestamp
  proteinIntake?: number;      // grammes
  alcoholUnits?: number;       // unités standard
  caffeineIntake?: number;     // mg
  caffeineLastTime?: string;   // ISO timestamp
  waterIntake?: number;        // mL
  carbsIntake?: number;        // grammes
  caloriesIntake?: number;     // kcal
}
```

**Santé** :
```typescript
{
  sleepQuality?: number;       // 0-100
  sleepDuration?: number;      // heures
  sleepFragmentation?: number; // nombre de réveils
  hrv?: number;                // ms
  hrvBaseline?: number;        // ms (médiane perso)
  recovery?: number;           // 0-100
  energyLevel?: number;        // 0-100
  activeCalories?: number;     // kcal
}
```

---

## Niveaux de Sévérité

| Niveau | Couleur | Icône | Usage |
|--------|---------|-------|-------|
| `alert` | Rouge (#FF3B30) | ⚠️ AlertCircle | Impact critique (ex: alcool élevé + HRV très basse) |
| `warning` | Orange (#FF9500) | ↘ TrendingDown | Impact modéré nécessitant attention |
| `positive` | Vert (#00FF41) | ↗ TrendingUp | Pattern positif à maintenir |
| `neutral` | Gris (#8E8E93) | ℹ️ Info | Information sans impact majeur |

---

## Confidence Score

Chaque insight inclut un **score de confiance** (0-1) indiquant la fiabilité de la corrélation :

| Confidence | Interprétation |
|------------|----------------|
| 0.85-1.0 | Corrélation forte, bien documentée scientifiquement |
| 0.70-0.84 | Corrélation probable, pattern cohérent |
| 0.60-0.69 | Corrélation possible, suggérée par les données |
| <0.60 | Hypothèse, à valider avec plus de données |

**Exemples** :
- Alcool → HRV : `0.85` (très documenté)
- Protéines → Récupération : `0.80` (bien établi)
- Caféine tardive → Sommeil : `0.75` (prouvé)
- Repas tardifs → Sommeil : `0.75-0.90` (augmente avec l'heure)
- Glucides → Énergie : `0.65` (indicatif)

---

## Interface Utilisateur

### Mode complet (Journal alimentaire)

```
┌──────────────────────────────────────────┐
│ 🍷 Impact alcool détecté           [⚠️]  │
│ Fiabilité: 85%                           │
│                                          │
│ • OBSERVATION                            │
│   3 unités d'alcool hier                 │
│        ↓                                 │
│ • CONSÉQUENCE                            │
│   HRV réduite de 15% (42ms vs 50ms)      │
│        ↓                                 │
│ • ACTION                                 │
│   Limite à 1-2 verres maximum si tu      │
│   veux maintenir une HRV optimale.       │
└──────────────────────────────────────────┘
```

**Caractéristiques** :
- Flow vertical clair
- Labels explicites (Observation / Conséquence / Action)
- Dots de couleur pour guider l'œil
- Badge de sévérité en haut à droite
- Score de confiance affiché

### Mode compact (Brief quotidien - optionnel)

```
┌──────────────────────────────────────────┐
│ 🍷 Impact alcool détecté                 │
│ 3 unités hier → HRV -15%                 │
│ 💡 Limite à 1-2 verres maximum           │
└──────────────────────────────────────────┘
```

**Caractéristiques** :
- Une ligne titre
- Une ligne observation → conséquence
- Une ligne action (avec icône ampoule)
- Bordure gauche colorée selon sévérité

---

## Implémentation

### Hook `useNutritionInsights`

**Signature** :
```typescript
function useNutritionInsights(
  nutritionData: NutritionData | undefined,
  healthData: HealthData | undefined
): NutritionInsightsData
```

**Retour** :
```typescript
interface NutritionInsightsData {
  insights: NutritionInsight[];  // Liste des insights détectés
  hasData: boolean;               // Au moins 1 insight trouvé
  analysisDate: string;           // ISO timestamp
}
```

**Logique** :
1. Appelle chaque fonction de détection
2. Filtre les `null` (pas de pattern détecté)
3. Trie par sévérité (alert → warning → positive → neutral)
4. Retourne la liste consolidée

### Hook `useNutritionHealthData`

**Signature** :
```typescript
function useNutritionHealthData(
  userId: string | null,
  date: Date = new Date()
): UseQueryResult<NutritionHealthDataResult>
```

**Opérations** :
1. Récupère `food_logs` + `food_log_items` du jour
2. Calcule totaux nutrition (protéines, glucides, calories)
3. Récupère `biometrics` (HRV, sommeil, calories actives)
4. Récupère `user_baselines` pour HRV baseline
5. Récupère `daily_state` pour recovery/energy
6. Agrège tout dans un objet unifié

**Caching** : 5 minutes via React Query

---

## Cas Limites Gérés

### 1. Données manquantes

Si certaines données ne sont pas disponibles, l'insight n'est pas généré :

```typescript
if (!nutritionData.lastMealTime || !healthData.sleepFragmentation) {
  return null; // Pas d'insight "repas tardifs"
}
```

### 2. Données partielles

Le système génère uniquement les insights pour lesquels il a les données nécessaires :

```typescript
// Exemple: Seulement protéines et recovery disponibles
insights = [
  proteinRecoveryInsight,  // ✅ Généré
  // alcoholHRVInsight,    // ❌ Pas de données alcool
  // caffeineSleepInsight, // ❌ Pas de données caféine
];
```

### 3. Aucun pattern détecté

Si les données sont disponibles mais aucun pattern n'est détecté :

```typescript
// HRV normale malgré alcool
if (alcohol >= 2 && hrvDrop <= 10) {
  return null; // Pas d'insight négatif
}

// Affichage UI
{nutritionInsights.hasData ? (
  <NutritionInsightsList insights={nutritionInsights.insights} />
) : (
  <Text>Aucun pattern notable aujourd'hui 👍</Text>
)}
```

---

## Évolutions Futures

### Phase 2 : Historique et trends (Q2 2026)

- **Tendances multi-jours** : "3 repas tardifs cette semaine → sommeil dégradé"
- **Analyse longitudinale** : "Depuis que tu coupes la caféine à 14h, ton sommeil s'est amélioré de 18%"
- **Graphiques de corrélation** : Visualiser la relation repas tardifs <-> qualité sommeil

### Phase 3 : Recommandations proactives (Q3 2026)

- **Prédictions** : "Si tu manges tard ce soir, risque de sommeil fragmenté à 75%"
- **Timing optimal** : "Meilleure fenêtre pour dernier repas: 18h30-19h30"
- **Plans personnalisés** : "Ton corps réagit mieux avec 100g+ de protéines les jours d'entraînement"

### Phase 4 : Intelligence contextuelle (Q4 2026)

- **Facteurs externes** : Stress, voyage, maladie
- **Interactions complexes** : Alcool + repas tardif + stress → impact multiplié
- **Recommandations adaptatives** : Ajuster selon objectifs (performance, perte de poids, santé)

---

## Tests de Validation

### Scénarios de test

| Scénario | Nutrition | Santé | Insight attendu |
|----------|-----------|-------|-----------------|
| **Repas tardif** | Repas 21h | 5 réveils | ⚠️ Repas tardif → Sommeil fragmenté |
| **Protéines + récup** | 95g protéines | Récup 82% | ✅ Excellente nutrition sportive |
| **Alcool + HRV** | 3 unités | HRV -15% | ⚠️ Impact alcool → HRV réduite |
| **Caféine tardive** | Café 17h, 240mg | Sommeil 52% | ⚠️ Caféine tardive → Sommeil affecté |
| **Hydratation faible** | 1200mL | 620 kcal actives | ⚠️ Hydratation insuffisante |
| **Glucides faibles** | 75g glucides | Énergie 42% | ⚠️ Glucides → Énergie basse |
| **Aucun pattern** | Normal | Normal | Aucun insight (hasData = false) |

### Tests unitaires recommandés

```typescript
describe('useNutritionInsights', () => {
  it('should detect late meal impact', () => {
    const nutrition = { lastMealTime: '2026-01-30T21:00:00Z' };
    const health = { sleepFragmentation: 5 };
    const result = useNutritionInsights(nutrition, health);
    
    expect(result.insights[0].type).toBe('late_meal_sleep');
    expect(result.insights[0].severity).toBe('warning');
  });

  it('should detect positive protein-recovery correlation', () => {
    const nutrition = { proteinIntake: 95 };
    const health = { recovery: 82 };
    const result = useNutritionInsights(nutrition, health);
    
    expect(result.insights[0].type).toBe('protein_recovery');
    expect(result.insights[0].severity).toBe('positive');
  });

  it('should return empty when no patterns detected', () => {
    const nutrition = { proteinIntake: 70 };
    const health = { recovery: 65 };
    const result = useNutritionInsights(nutrition, health);
    
    expect(result.hasData).toBe(false);
    expect(result.insights).toHaveLength(0);
  });
});
```

---

## Références

### Fichiers du projet
- `/mobile/src/hooks/useNutritionInsights.ts` - Moteur de détection
- `/mobile/src/hooks/useNutritionHealthData.ts` - Agrégation données
- `/mobile/src/components/NutritionInsightCard.tsx` - Composant UI
- `/mobile/app/(tabs)/journal.tsx` - Intégration journal

### Documentation scientifique
- [Sleep and meal timing](https://pubmed.ncbi.nlm.nih.gov/31851909/)
- [Protein and recovery](https://pubmed.ncbi.nlm.nih.gov/29497353/)
- [Alcohol and HRV](https://pubmed.ncbi.nlm.nih.gov/16243846/)
- [Caffeine and sleep](https://pubmed.ncbi.nlm.nih.gov/24235903/)

---

**Version** : 1.0  
**Date** : 2026-01-30  
**Auteur** : Pulse Engineering Team  
**Status** : ✅ Implémenté
