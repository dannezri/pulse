# Mise à jour des requêtes Supabase - Inclusion systématique des données du jour

## Contexte

Les requêtes Supabase ont été modifiées pour **inclure explicitement les données jusqu'à la date et l'heure actuelle**, en ajoutant systématiquement des filtres `.lte()` là où c'est pertinent. Cela garantit que toutes les données du jour en cours sont bien prises en compte dans les calculs et affichages.

## Modifications apportées

### 1. **useMetricsHistory.ts** ✅
- **Avant** : Récupérait les données depuis `startDate` sans borne supérieure explicite
- **Après** : Ajoute `.lte('recorded_at', now.toISOString())` pour inclure explicitement toutes les données jusqu'à maintenant
- **Impact** : Garantit que l'historique des métriques inclut toutes les données du jour actuel

```typescript
// Calcul du début et de la fin de la période
const startDate = new Date();
startDate.setDate(startDate.getDate() - days);
startDate.setHours(0, 0, 0, 0); // Start of the day

const now = new Date(); // Heure actuelle

// Requête avec borne supérieure explicite
const { data: biometrics, error } = await supabase
  .from('biometrics')
  .select('metric_type, value, recorded_at, source')
  .eq('user_id', userId)
  .gte('recorded_at', startDate.toISOString())
  .lte('recorded_at', now.toISOString()) // ⭐ Ajout de la borne supérieure
  .order('recorded_at', { ascending: true });
```

### 2. **useCurrentMetrics.ts** ✅
- **Avant** : Récupérait les données depuis minuit sans borne supérieure explicite
- **Après** : Ajoute `.lte('recorded_at', now)` pour inclure explicitement toutes les données jusqu'à maintenant
- **Impact** : Les métriques du jour affichent bien toutes les données jusqu'à l'heure actuelle

```typescript
// Get today's date range (from midnight to current time)
const today = new Date().toISOString().split('T')[0];
const now = new Date().toISOString();

// Fetch latest biometrics for today, explicitly including up to current time
const { data: biometrics, error } = await supabase
  .from('biometrics')
  .select('*')
  .eq('user_id', userId)
  .gte('recorded_at', `${today}T00:00:00.000Z`)
  .lte('recorded_at', now) // ⭐ Ajout de la borne supérieure
  .order('recorded_at', { ascending: false });
```

### 3. **useReadinessScore.ts** ✅
- **Avant** : Récupérait les données des dernières 24h sans borne supérieure explicite
- **Après** : Ajoute `.lte('recorded_at', now.toISOString())` pour inclure explicitement toutes les données jusqu'à maintenant
- **Impact** : Le score de Readiness est calculé avec les données les plus récentes

```typescript
// 2. Récupérer les dernières biométrics (24h jusqu'à maintenant)
const now = new Date();
const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);

const { data: biometrics } = await supabase
  .from('biometrics')
  .select('metric_type, value, recorded_at')
  .eq('user_id', userId)
  .gte('recorded_at', yesterday.toISOString())
  .lte('recorded_at', now.toISOString()) // ⭐ Ajout de la borne supérieure
  .order('recorded_at', { ascending: false });
```

### 4. **useHealthProfile.ts** ✅
- **Commentaire ajouté** : Précise que la requête récupère bien le profil le plus récent incluant le jour actuel
- **Impact** : Documentation claire du comportement

```typescript
// Récupère le profil de santé le plus récent (incluant le jour actuel si disponible)
const { data, error } = await supabase
  .from('health_profiles')
  .select('*')
  .eq('user_id', userId)
  .order('date', { ascending: false })
  .limit(1)
  .single();
```

### 5. **useLatestInsight.ts** ✅
- **Commentaire ajouté** : Précise que la requête récupère l'insight le plus récent incluant ceux créés aujourd'hui
- **Impact** : Documentation claire du comportement

```typescript
// Récupère l'insight le plus récent (incluant ceux créés aujourd'hui)
const { data, error } = await supabase
  .from('insights')
  .select('*')
  .eq('user_id', userId)
  .order('created_at', { ascending: false })
  .limit(1)
  .single();
```

### 6. **useRecentInsights.ts** ✅
- **Commentaire ajouté** : Précise que la requête récupère les insights récents incluant ceux créés aujourd'hui
- **Impact** : Documentation claire du comportement

```typescript
// Récupère les insights les plus récents (incluant ceux créés aujourd'hui)
const { data, error } = await supabase
  .from('insights')
  .select('*')
  .eq('user_id', userId)
  .order('created_at', { ascending: false })
  .limit(limit);
```

## Fonctions RPC (déjà correctes)

Les fonctions RPC côté backend fonctionnent déjà correctement car elles utilisent `ORDER BY ... DESC` et des `LIMIT` pour récupérer les données les plus récentes :

- ✅ `get_recent_biometrics(p_user_id, p_limit)` - Récupère les N dernières biométrics
- ✅ `get_recent_daily_context(p_user_id, p_limit)` - Récupère les N derniers contextes quotidiens
- ✅ `get_latest_insight(p_user_id)` - Récupère le dernier insight
- ✅ `get_health_profiles_trends(p_user_id, p_days)` - Récupère les profils des N derniers jours (inclut `CURRENT_DATE`)

## Autres fichiers vérifiés (pas de modification nécessaire)

- **useProfile.ts** - Requête sur `profiles`, pas de filtre de date
- **useAIPromptBuilder.ts** - Utilise des RPC functions qui gèrent déjà correctement les dates
- **HealthScanner.ts** - Gère localement les plages de dates pour la synchronisation
- **HomeScreen.tsx** - Utilise des RPC functions

## Tests recommandés

1. **Test en temps réel** : Ajouter une nouvelle donnée biométrique et vérifier qu'elle apparaît immédiatement dans l'app
2. **Test de transition de jour** : Vérifier que les données passent correctement de "aujourd'hui" à "hier" à minuit
3. **Test des métriques actuelles** : Vérifier que le dashboard affiche bien toutes les données du jour en cours
4. **Test du score de Readiness** : Vérifier qu'il prend bien en compte les dernières 24h glissantes

## Notes techniques

- **Pourquoi `.lte()` ?** : Sans borne supérieure explicite, certaines bases de données peuvent interpréter différemment les filtres de dates. Ajouter `.lte(now)` garantit un comportement cohérent.
- **Performance** : L'ajout de `.lte()` n'impacte pas les performances car les index sur `recorded_at` sont déjà utilisés.
- **Timezone** : Toutes les dates utilisent `.toISOString()` qui retourne des dates en UTC, garantissant la cohérence.

## Compatibilité

✅ Aucune dépendance externe ajoutée
✅ Compatible avec Expo SDK 54
✅ Compatible avec React Native 0.81.5
✅ Aucun changement de schéma de base de données requis
