# Résumé Automatique des Tendances - Documentation

## Vue d'ensemble

Le **Résumé Automatique des Tendances** affiche un aperçu visuel instantané des tendances des métriques clés sur 30 jours en haut de l'écran Tendances, avant les graphiques détaillés.

### Objectif

Transformer un écran analytique complexe en une **expérience lifestyle** :
- ✅ Compréhension en 3 secondes
- ✅ Moins besoin d'analyser les graphiques
- ✅ UX instantanée et accessible

## Format d'affichage

```
┌─────────────────────────────────────────┐
│ 📊 Résumé sur 30 jours                  │
│ Tendances automatiques des métriques clés│
│                                          │
│ 💚 HRV          ↗ amélioration (12%)    │
│ 🌙 Sommeil      → Stable                │
│ 🧠 Stress       ↘ baisse (8%)           │
│ ❤️ Fréq. card.  ↗ amélioration (5%)    │
│ 👟 Activité     ↗ amélioration (18%)   │
│                                          │
│ Scrollez pour voir les graphiques ↓     │
└─────────────────────────────────────────┘
```

### Symboles de tendance

| Symbole | Signification | Couleur | Condition |
|---------|---------------|---------|-----------|
| ↗ | Amélioration | Vert (#00FF41) | Changement > +5% |
| ↘ | Baisse | Rouge (#FF3B30) | Changement < -5% |
| → | Stable | Gris (#8E8E93) | Changement entre -5% et +5% |
| ⚠️ | Données insuffisantes | Gris sombre (#48484A) | < 5 points de données |

## Métriques analysées

Les métriques sont affichées par **ordre de priorité santé** :

### 1. 💚 HRV (Haute priorité)
- **Indicateur** : Santé cardiovasculaire et récupération
- **Interprétation** : Hausse = amélioration
- **Source** : `metricsHistory.hrv`

### 2. 🌙 Sommeil (Haute priorité)
- **Indicateur** : Qualité de la récupération
- **Interprétation** : Hausse = amélioration
- **Source** : `metricsHistory.sleep_duration`

### 3. 🧠 Stress (Haute priorité)
- **Indicateur** : Bien-être mental
- **Interprétation** : **Inverse** - Baisse = amélioration ✨
- **Source** : `metricsHistory.stress`

### 4. ❤️ Fréquence cardiaque (Priorité moyenne)
- **Indicateur** : Santé cardiaque
- **Interprétation** : Hausse = amélioration (contexte dépendant)
- **Source** : `metricsHistory.heart_rate`

### 5. 👟 Activité (Priorité moyenne)
- **Indicateur** : Mouvement quotidien
- **Interprétation** : Hausse = amélioration
- **Source** : `metricsHistory.steps`

**Note** : Maximum 5 métriques affichées simultanément pour éviter la surcharge cognitive.

## Algorithme de calcul

### Méthode de comparaison

Pour chaque métrique, l'algorithme compare la **première moitié** vs la **seconde moitié** de la période :

```typescript
// Exemple avec 30 jours de données
const midPoint = 15;
const firstHalf = values[0...14];   // Jours 1-15
const secondHalf = values[15...29]; // Jours 16-30

const firstAvg = moyenne(firstHalf);
const secondAvg = moyenne(secondHalf);

const changePercent = ((secondAvg - firstAvg) / firstAvg) * 100;
```

### Seuils de détection

| Changement | Tendance | Description |
|------------|----------|-------------|
| > +5% | ↗ Up | Amélioration significative |
| -5% à +5% | → Stable | Variations normales |
| < -5% | ↘ Down | Baisse significative |

**Justification** : Un seuil de 5% filtre le bruit quotidien tout en détectant les changements réels sur 30 jours.

### Données insuffisantes

**Minimum requis** : 5 points de données sur 30 jours

Si < 5 points :
```
⚠️ Métrique → Données insuffisantes
```

## Implémentation technique

### Architecture

```
┌─────────────────────────────────────┐
│   tendances.tsx (Screen)            │
│                                     │
│   ┌──────────────────────────┐    │
│   │ useTrendsSummary()       │    │
│   │ ↓                        │    │
│   │ Analyse metricsHistory   │    │
│   │ ↓                        │    │
│   │ Retourne TrendsSummary   │    │
│   └──────────────────────────┘    │
│                ↓                   │
│   ┌──────────────────────────┐    │
│   │ <TrendsSummaryCard>      │    │
│   │ Affiche le résumé        │    │
│   └──────────────────────────┘    │
│                                     │
│   [Graphiques détaillés...]        │
└─────────────────────────────────────┘
```

### Fichiers

#### 1. Hook : `useTrendsSummary.ts`

**Localisation** : `/mobile/src/hooks/useTrendsSummary.ts`

**Interface** :
```typescript
export interface MetricTrend {
  key: string;          // 'hrv', 'sleep_duration', etc.
  label: string;        // 'HRV', 'Sommeil', etc.
  trend: TrendDirection; // 'up', 'down', 'stable', 'insufficient'
  description: string;  // 'amélioration (12%)', 'Stable', etc.
  change: number;       // Pourcentage de changement
  emoji: string;        // '💚', '🌙', etc.
}

export interface TrendsSummary {
  metrics: MetricTrend[];
  period: number;       // Toujours 30 jours
  hasData: boolean;     // Au moins 1 métrique valide
}

function useTrendsSummary(
  metricsHistory: Record<string, any[]> | undefined
): TrendsSummary
```

**Logique clé** :
- Filtre les valeurs invalides (null, NaN, Infinity)
- Calcule la moyenne de chaque moitié
- Détermine la tendance avec seuil 5%
- Applique l'interprétation inverse pour le stress
- Limite à 5 métriques max

#### 2. Composant : `TrendsSummaryCard.tsx`

**Localisation** : `/mobile/src/components/TrendsSummaryCard.tsx`

**Props** :
```typescript
interface TrendsSummaryCardProps {
  summary: TrendsSummary;
}
```

**Rendu** :
- Header avec titre et période
- Grid de métriques (emoji + label + badge tendance)
- Footer avec hint de scroll
- État vide si aucune donnée

**Style** :
- Card dark (#1C1C1E) avec halo subtle
- Badges colorés selon tendance
- Séparateurs entre métriques
- Responsive et compact

#### 3. Intégration : `tendances.tsx`

**Modifications** :
```typescript
// Import
import { useTrendsSummary } from '../../src/hooks/useTrendsSummary';
import { TrendsSummaryCard } from '../../src/components/TrendsSummaryCard';

// Dans le composant
const trendsSummary = useTrendsSummary(metricsHistory);

// Dans le JSX (après les filtres, avant les graphiques)
{viewMode === 'period' && selectedPeriod === 30 && (
  <TrendsSummaryCard summary={trendsSummary} />
)}
```

**Condition d'affichage** :
- Uniquement en mode "Période"
- Uniquement pour période de 30 jours
- Masqué en mode "Jour" ou pour 7J/90J

## Comportement UX

### Affichage conditionnel

| Mode | Période | Résumé affiché ? |
|------|---------|------------------|
| Période | 7 jours | ❌ Non (période trop courte) |
| Période | 30 jours | ✅ Oui |
| Période | 90 jours | ❌ Non (trop long pour "tendance récente") |
| Jour | N/A | ❌ Non (vue ponctuelle) |

**Justification** : Le résumé est pertinent uniquement sur 30 jours, période standard pour détecter des tendances réelles sans être trop ancien.

### États possibles

#### 1. État nominal (données suffisantes)
```
📊 Résumé sur 30 jours
Tendances automatiques des métriques clés

💚 HRV          ↗ amélioration (12%)
🌙 Sommeil      → Stable
🧠 Stress       ↘ amélioration (8%)
❤️ Fréq. card.  ↗ amélioration (5%)
👟 Activité     ↗ amélioration (18%)

Scrollez pour voir les graphiques détaillés ↓
```

#### 2. État vide (pas assez de données)
```
📊 Résumé sur 30 jours

Collectez plus de données pour voir
vos tendances automatiques
```

#### 3. État partiel (certaines métriques insuffisantes)
```
📊 Résumé sur 30 jours
Tendances automatiques des métriques clés

💚 HRV          ↗ amélioration (12%)
🌙 Sommeil      → Stable

Scrollez pour voir les graphiques détaillés ↓
```

### Animations (potentielles évolutions)

- Fade in progressif de chaque métrique
- Pulse léger sur les badges de tendance
- Shimmer pendant le chargement

## Cas limites gérés

### 1. Données manquantes
```typescript
if (!data || data.length < MIN_DATA_POINTS) {
  return {
    trend: 'insufficient',
    description: 'Données insuffisantes',
  };
}
```

### 2. Valeurs invalides
```typescript
const values = data
  .map(d => d?.value)
  .filter(v => v != null && typeof v === 'number' && !isNaN(v) && isFinite(v));
```

### 3. Division par zéro
```typescript
const changePercent = firstAvg > 0 ? (diff / firstAvg) * 100 : 0;
```

### 4. Métriques mixtes (certaines valides, d'autres non)
Le hook retourne uniquement les métriques valides, le composant s'adapte au nombre.

## Tests de validation

### Scénarios de test

| Scénario | HRV | Sommeil | Stress | Résultat attendu |
|----------|-----|---------|--------|------------------|
| **Amélioration globale** | +15% | +8% | -12% | 3 flèches ↗ vertes |
| **Détérioration globale** | -10% | -6% | +15% | 3 flèches ↘ rouges |
| **Stabilité** | +2% | -3% | +1% | 3 flèches → grises |
| **Données partielles** | +12% | 2 points | +8% | HRV ↗, Sommeil ⚠️, Stress ↗ |
| **Aucune donnée** | 0 pts | 0 pts | 0 pts | État vide |

### Tests unitaires recommandés

```typescript
describe('useTrendsSummary', () => {
  it('should detect upward trend for >5% increase', () => {
    const data = generateMockData(30, { trend: 'up', change: 10 });
    const result = useTrendsSummary({ hrv: data });
    expect(result.metrics[0].trend).toBe('up');
  });

  it('should apply inverse interpretation for stress', () => {
    const data = generateMockData(30, { trend: 'down', change: -10 });
    const result = useTrendsSummary({ stress: data });
    expect(result.metrics[0].description).toContain('amélioration');
  });

  it('should return insufficient for <5 data points', () => {
    const data = generateMockData(3, { trend: 'up', change: 10 });
    const result = useTrendsSummary({ hrv: data });
    expect(result.metrics[0].trend).toBe('insufficient');
  });
});
```

## Évolutions futures

### Phase 2 : Intelligence contextuelle
- **Comparaison aux baselines personnelles** : "HRV à +15% de ta normale"
- **Détection de patterns** : "Ton sommeil baisse chaque lundi"
- **Corrélations** : "Stress ↗ quand Activité ↘"

### Phase 3 : Recommandations proactives
- **Actions suggérées** : "↗ HRV → Bon moment pour sport intense"
- **Alertes précoces** : "⚠️ Sommeil ↘ 3 semaines consécutives → Action requise"

### Phase 4 : Personnalisation UI
- **Choix des métriques** : L'utilisateur sélectionne les 5 métriques à suivre
- **Seuils personnalisés** : Ajuster le seuil de 5% selon préférence

## Avantages produit

### 1. **Réduction de la charge cognitive**
Au lieu d'analyser 15+ graphiques, l'utilisateur voit **5 lignes résumées**.

### 2. **Compréhension instantanée**
Format universel : emoji + flèche + pourcentage = **langage visuel clair**.

### 3. **Lifestyle vs analytique**
L'utilisateur casual comprend aussi bien que l'utilisateur expert.

### 4. **Encouragement comportemental**
Voir "↗ amélioration (12%)" renforce la motivation à maintenir les bonnes habitudes.

### 5. **Point d'entrée vers détails**
Le résumé attire l'attention sur les métriques importantes, puis l'utilisateur peut scroller pour les graphiques.

## Références

- **Backend** : N/A (calcul client-side uniquement)
- **Mobile** :
  - `/mobile/src/hooks/useTrendsSummary.ts` - Logique de calcul
  - `/mobile/src/components/TrendsSummaryCard.tsx` - Affichage
  - `/mobile/app/(tabs)/tendances.tsx` - Intégration
  - `/mobile/src/hooks/useMetricsHistory.ts` - Source de données

---

**Version** : 1.0  
**Date** : 2026-01-30  
**Auteur** : Pulse Engineering Team
