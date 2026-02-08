# Guide de Performance : biometrics & health_profiles

## 📋 Règle Fondamentale

### ⚠️ IMPORTANT : Ne JAMAIS requêter `biometrics` directement pour les lectures IA

**Utilisez TOUJOURS `health_profiles` pour les lectures IA.**

```python
# ❌ MAUVAIS : Lecture directe depuis biometrics
biometrics = supabase_client.get_today_biometrics(user_id)
# Ne pas utiliser pour générer des insights IA

# ✅ BON : Lecture depuis health_profiles
health_profile = supabase_client.get_latest_health_profile(user_id)
# Utiliser pour générer des insights IA
```

## 🏗️ Architecture de Performance

### Table `biometrics` : Stockage Haute Performance

**Rôle** : Stocker les données brutes des wearables (millions de lignes)

**Optimisations** :
- ✅ Index composite `(user_id, recorded_at DESC)`
- ✅ Index partiels par `metric_type` (HR, HRV, sleep, steps)
- ✅ Index pour baselines (7 derniers jours)
- ✅ Partitionnement par mois (optionnel, si > 10M lignes)

**Usage** :
- ✅ **Écriture** : Insertion de nouvelles données
- ✅ **Lecture** : Calcul de baselines (7 jours max)
- ✅ **Lecture** : Construction de `health_profiles`
- ❌ **NE PAS utiliser** : Lectures directes pour IA

### Table `health_profiles` : Cache pour IA

**Rôle** : Profils de santé normalisés (un par jour, ~365 lignes/an/utilisateur)

**Optimisations** :
- ✅ Index `(user_id, date DESC)`
- ✅ Contrainte unique `(user_id, date)`
- ✅ Format JSON normalisé prêt pour IA

**Usage** :
- ✅ **Lecture** : Génération d'insights IA
- ✅ **Lecture** : Affichage dans l'UI
- ✅ **Écriture** : Mise à jour quotidienne par worker

## 📊 Index Créés

### Index Composite Principal

```sql
CREATE INDEX idx_biometrics_user_date_optimized 
    ON biometrics(user_id, recorded_at DESC)
    WITH (fillfactor = 90);
```

**Usage** : Requêtes temporelles par utilisateur
**Performance** : O(log n) pour récupérer les données récentes

### Index Partiels par Metric Type

```sql
-- HR uniquement
CREATE INDEX idx_biometrics_hr_partial 
    ON biometrics(user_id, recorded_at DESC) 
    WHERE metric_type = 'hr';

-- HRV uniquement
CREATE INDEX idx_biometrics_hrv_partial 
    ON biometrics(user_id, recorded_at DESC) 
    WHERE metric_type = 'hrv';

-- Sleep (duration, score, quality)
CREATE INDEX idx_biometrics_sleep_partial 
    ON biometrics(user_id, recorded_at DESC) 
    WHERE metric_type IN ('sleep_duration', 'sleep_score', 'sleep_quality');

-- Steps
CREATE INDEX idx_biometrics_steps_partial 
    ON biometrics(user_id, recorded_at DESC) 
    WHERE metric_type = 'steps';
```

**Avantages** :
- **Taille réduite** : Index plus petits (seulement les lignes pertinentes)
- **Performance** : Requêtes plus rapides pour un type de métrique
- **Maintenance** : Moins de données à indexer

### Index pour Baselines

```sql
CREATE INDEX idx_biometrics_baseline_query 
    ON biometrics(user_id, metric_type, recorded_at DESC) 
    WHERE recorded_at >= CURRENT_DATE - INTERVAL '7 days';
```

**Usage** : Calcul des baselines (7 derniers jours uniquement)
**Performance** : Index partiel sur données récentes uniquement

## 🔄 Flux de Données

```
Webhook reçu
    ↓
Enregistrement brut → biometrics (INSERT rapide)
    ↓
Worker normalise → health_profiles (UPSERT quotidien)
    ↓
IA lit → health_profiles (SELECT rapide, 1 ligne/jour)
```

### Pourquoi ce flux ?

1. **biometrics** : Optimisé pour INSERT (millions de lignes)
2. **health_profiles** : Optimisé pour SELECT (peu de lignes, format normalisé)

## 📈 Performance Attendue

### Table `biometrics`

| Opération | Performance | Volume |
|-----------|------------|--------|
| INSERT | < 10ms | Millions de lignes |
| SELECT (7 jours) | < 50ms | ~1000 lignes |
| SELECT (30 jours) | < 200ms | ~5000 lignes |
| SELECT (1 an) | < 1s | ~50k lignes |

### Table `health_profiles`

| Opération | Performance | Volume |
|-----------|------------|--------|
| SELECT (dernier) | < 10ms | 1 ligne |
| SELECT (7 jours) | < 20ms | 7 lignes |
| SELECT (30 jours) | < 50ms | 30 lignes |
| UPSERT (quotidien) | < 100ms | 1 ligne |

## 🚀 Partitionnement (Optionnel)

### Quand partitionner ?

- **< 10M lignes** : Index suffisent
- **> 10M lignes** : Considérer le partitionnement
- **> 100M lignes** : Partitionnement recommandé

### Partitionnement par Mois

```sql
-- Créer une partition mensuelle
SELECT create_biometrics_partition('2024-01-01');

-- Créer les partitions futures (3 mois)
SELECT create_future_biometrics_partitions();
```

**Avantages** :
- **Performance** : Requêtes limitées à une partition
- **Maintenance** : VACUUM/ANALYZE par partition
- **Archivage** : Suppression facile des anciennes partitions

**Inconvénients** :
- **Complexité** : Migration nécessaire
- **Maintenance** : Création automatique des partitions futures

## 🛠️ Maintenance

### VACUUM et ANALYZE

```sql
-- Analyser les statistiques
SELECT * FROM analyze_biometrics_stats();

-- Maintenance des partitions récentes
SELECT maintain_biometrics_partitions();
```

### Monitoring

```sql
-- Taille de la table
SELECT 
    pg_size_pretty(pg_total_relation_size('biometrics')) as total_size,
    pg_size_pretty(pg_relation_size('biometrics')) as table_size,
    pg_size_pretty(pg_indexes_size('biometrics')) as indexes_size;

-- Nombre de lignes
SELECT COUNT(*) FROM biometrics;

-- Distribution par metric_type
SELECT metric_type, COUNT(*) 
FROM biometrics 
GROUP BY metric_type 
ORDER BY COUNT(*) DESC;
```

## 📝 Bonnes Pratiques

### 1. Toujours utiliser health_profiles pour IA

```python
# ✅ CORRECT
def generate_insight(user_id: str):
    profile = supabase_client.get_latest_health_profile(user_id)
    # Utiliser profile pour générer l'insight
    return create_insight(profile)
```

### 2. Limiter les requêtes biometrics

```python
# ✅ CORRECT : Seulement pour calculer baselines
def calculate_baseline(user_id: str):
    # 7 jours max
    data = supabase_client.get_historical_biometrics(user_id, days=7)
    return compute_baseline(data)

# ❌ INCORRECT : Lecture complète pour IA
def generate_insight(user_id: str):
    # Ne pas faire ça !
    all_data = supabase_client.get_historical_biometrics(user_id, days=365)
    return create_insight(all_data)  # Trop lent !
```

### 3. Utiliser les index partiels

```python
# ✅ CORRECT : Requête qui utilise l'index partiel
# (Le code utilise automatiquement l'index si metric_type est filtré)
data = supabase_client.client.table("biometrics").select("*").eq(
    "user_id", user_id
).eq("metric_type", "hr").gte(
    "recorded_at", start_date
).execute()
```

### 4. Mettre à jour health_profiles quotidiennement

```python
# ✅ CORRECT : Worker met à jour health_profiles chaque jour
def update_daily_profile(user_id: str):
    # Récupère les données du jour depuis biometrics
    today_data = supabase_client.get_today_biometrics(user_id)
    
    # Normalise et crée le profil
    profile = normalizer.create_health_profile(today_data, ...)
    
    # Sauvegarde dans health_profiles (1 ligne/jour)
    supabase_client.save_health_profile(user_id, profile)
```

## 🔍 Vérification des Performances

### Requête lente ? Vérifier :

1. **Index utilisé ?**
   ```sql
   EXPLAIN ANALYZE 
   SELECT * FROM biometrics 
   WHERE user_id = '...' 
   ORDER BY recorded_at DESC 
   LIMIT 100;
   ```

2. **Index partiel utilisé ?**
   ```sql
   EXPLAIN ANALYZE 
   SELECT * FROM biometrics 
   WHERE user_id = '...' 
   AND metric_type = 'hr'
   ORDER BY recorded_at DESC;
   ```

3. **health_profiles utilisé pour IA ?**
   ```python
   # Vérifier que le code utilise get_latest_health_profile()
   # et non get_today_biometrics() ou get_historical_biometrics()
   ```

## 📊 Métriques de Performance

### Objectifs

- **INSERT biometrics** : < 10ms
- **SELECT health_profiles (dernier)** : < 10ms
- **SELECT biometrics (7 jours)** : < 50ms
- **UPSERT health_profiles** : < 100ms

### Alertes

Si les performances dépassent ces seuils :
1. Vérifier les index (sont-ils utilisés ?)
2. Vérifier la taille de la table
3. Considérer le partitionnement si > 10M lignes
4. Vérifier que health_profiles est utilisé pour IA

---

*Document créé le : 2024*
*Migration : 006_optimize_biometrics_performance.sql*
