# 🗄️ Système de Cache Gemini - Documentation Complète

**Date**: 4 février 2026  
**Objectif**: Éviter les appels redondants à Gemini 3 Pro (payant + lent)

---

## 🎯 Pourquoi un Cache ?

### Problème Sans Cache

- **Coût** : Gemini 3 Pro coûte ~$0.03 par explication générée
- **Latence** : 30-60 secondes par appel (mode raisonnement)
- **Redondance** : Si les données n'ont pas changé, l'explication sera identique

### Exemple de Scénario Sans Cache

Un utilisateur consulte sa page Énergie 5 fois dans la journée :
- ❌ 5 appels à Gemini = **$0.15**
- ❌ 5 × 45 secondes = **3m 45s d'attente cumulée**
- ❌ Même explication générée 5 fois

### Avec le Cache ✅

- ✅ 1er appel : Génération Gemini ($0.03, 45s)
- ✅ 2-5ème appels : Cache instantané ($0, <100ms)
- ✅ **Économie** : $0.12 (80%) et 3 minutes d'attente

---

## 🏗️ Architecture du Cache

### Table Supabase : `gemini_explanations_cache`

```sql
CREATE TABLE gemini_explanations_cache (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    target_date DATE NOT NULL,
    data_hash TEXT NOT NULL,          -- Hash MD5 des données sources
    explanation JSONB NOT NULL,        -- Réponse complète de Gemini
    energy_score INTEGER,
    confidence INTEGER,
    label TEXT,
    generated_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,            -- Expiration après 24h
    UNIQUE(user_id, target_date, data_hash)
);
```

### Clé de Cache Composite

**`user_id` + `target_date` + `data_hash`**

- **`user_id`** : Isole les caches par utilisateur
- **`target_date`** : Une date = un cache
- **`data_hash`** : Hash MD5 des données sources (voir ci-dessous)

---

## 🔑 Calcul du Hash des Données

Le hash est calculé à partir de :

```python
{
    "energy_score": 0.36,
    "confidence": 0.27,
    "latent_states": {
        "recovery": 0.19,
        "sleep_debt": 1.0,
        "overtrain": 0.13,
        "infection_like": 0.0
    },
    "biometrics": {
        "hrv_night": 20,
        "rhr_night": 80,
        "sleep_score": 64,
        "readiness_score": 72,
        "activity_score": 55,
        "steps": 5303
    },
    "influencers_count": 8
}
```

**Si UNE seule de ces valeurs change, le hash change** → Cache invalidé

---

## 🔄 Flux de Fonctionnement

### 1. Requête Entrante

```
GET /api/energy/explain/{user_id}?date=2026-02-03
```

### 2. Récupération des Données

```python
energy_data = await _get_energy_calculation(...)
latent_states = await _get_latent_states(...)
forecast = await _get_intraday_forecast(...)
biometrics = await _get_biometrics(...)
```

### 3. Calcul du Hash

```python
data_hash = _compute_data_hash(energy_data, latent_states, forecast, biometrics)
# Résultat: "a3f7b9c2d1e4f6g8..."
```

### 4. Vérification du Cache

```python
cached = await _get_cached_explanation(user_id, target_date, data_hash)

if cached:
    # ✅ Cache HIT : Retour immédiat
    logger.info("🚀 Returning cached explanation (saved ~$0.03 + 30-60s)")
    return cached
```

### 5. Si Cache MISS

```python
# ❌ Cache MISS : Appel Gemini
logger.info("🧠 Cache miss, calling Gemini 3 Pro...")
explanation = await _generate_cards(prompt)

# Stocker dans le cache pour la prochaine fois
await _store_cached_explanation(user_id, target_date, data_hash, explanation)
```

---

## ⏰ Durée de Vie du Cache (TTL)

### Durée par Défaut : **24 heures**

```python
self.cache_ttl_hours = 24
```

### Expiration Automatique

```python
expires_at = NOW() + 24 hours
```

Après 24h, le cache est considéré comme expiré :
- ✅ Nouvelles données biométriques probablement disponibles
- ✅ Nouvelle journée = nouveau calcul d'énergie
- ✅ Le cache sera automatiquement recréé

### Nettoyage Automatique (Cron)

```sql
-- Fonction SQL pour nettoyer les caches expirés
CREATE OR REPLACE FUNCTION cleanup_expired_gemini_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM gemini_explanations_cache
    WHERE expires_at < NOW();
END;
$$;
```

À exécuter quotidiennement via cron :
```bash
0 3 * * * psql $DATABASE_URL -c "SELECT cleanup_expired_gemini_cache();"
```

---

## 🔧 Configuration du Cache

### Activer/Désactiver

```python
class EnergyExplainService:
    def __init__(self, ...):
        self.cache_enabled = True  # False pour désactiver
        self.cache_ttl_hours = 24  # Durée de vie en heures
```

### Cas où le Cache est Désactivé

```python
if not self.cache_enabled:
    return None  # Bypass cache
```

---

## 📊 Logs et Monitoring

### Cache HIT (Succès)

```
[cache] ✅ Cache HIT for user123 on 2026-02-03 (hash: a3f7b9c2...)
[cache] 📅 Generated at: 2026-02-03T08:30:00Z
[generate_explanation] 🚀 Returning cached explanation (saved ~$0.03 + 30-60s)
```

### Cache MISS (Échec)

```
[cache] ❌ Cache MISS for user123 on 2026-02-03
[generate_explanation] 🧠 Cache miss, calling Gemini 3 Pro...
[generate_explanation] 🔑 Data hash: a3f7b9c2d1e4f6g8...
[cache] 💾 Stored in cache for user123 on 2026-02-03 (hash: a3f7b9c2...)
[cache] ⏰ Expires at: 2026-02-04T08:30:00Z
```

### Stockage Réussi

```
[cache] 💾 Stored in cache for user123 on 2026-02-03 (hash: a3f7b9c2...)
[cache] ⏰ Expires at: 2026-02-04T08:30:00Z
```

---

## 🚀 Installation

### 1. Appliquer la Migration SQL

**Option A : Via Supabase Dashboard**

1. Aller sur `https://supabase.com/dashboard/project/<votre-projet>/editor`
2. Ouvrir l'onglet **SQL Editor**
3. Copier le contenu de `/database/migrations/20260204_create_gemini_cache.sql`
4. Exécuter la query

**Option B : Via Supabase CLI**

```bash
cd /Users/dannezri/Desktop/Pulse
supabase db push --db-url <votre-database-url>
```

### 2. Vérifier que la Table Existe

```sql
SELECT * FROM gemini_explanations_cache LIMIT 1;
```

### 3. Redémarrer le Backend

```bash
cd /Users/dannezri/Desktop/Pulse
./restart_api_server.sh
```

---

## 🧪 Test du Cache

### Script de Test

```bash
cd /Users/dannezri/Desktop/Pulse/backend
python3 test_gemini_cache.py
```

### Commandes SQL pour Inspecter

```sql
-- Voir tous les caches
SELECT 
    user_id, 
    target_date, 
    energy_score, 
    confidence,
    generated_at,
    expires_at
FROM gemini_explanations_cache
ORDER BY generated_at DESC;

-- Compter les caches par utilisateur
SELECT 
    user_id, 
    COUNT(*) as cache_count
FROM gemini_explanations_cache
GROUP BY user_id;

-- Voir les caches expirés
SELECT * FROM gemini_explanations_cache
WHERE expires_at < NOW();

-- Nettoyer manuellement les caches expirés
DELETE FROM gemini_explanations_cache
WHERE expires_at < NOW();
```

---

## 💡 Cas d'Usage

### Cas 1 : Utilisateur Consulte sa Page Plusieurs Fois

**Scénario** : Dan ouvre sa page Énergie 3 fois le même jour

```
1er appel (08:00) : Cache MISS → Génération Gemini ($0.03, 45s)
2ème appel (12:00) : Cache HIT → Instantané ($0, 50ms)
3ème appel (18:00) : Cache HIT → Instantané ($0, 50ms)
```

**Économie** : $0.06 + 1m 30s

### Cas 2 : Données Changent (Nouvelle Sync Oura)

**Scénario** : Dan synchronise sa bague Oura à 14:00

```
Appel à 10:00 : Cache HIT (hash: a3f7b9c2...)
Sync Oura à 14:00 : HRV change de 20 → 25ms
Appel à 15:00 : Cache MISS (hash: e8d4b1c6... ≠ a3f7b9c2...)
                → Nouvelle génération Gemini avec nouvelles données
```

**✅ Le cache détecte automatiquement le changement de données**

### Cas 3 : Cache Expire (24h)

**Scénario** : Cache créé hier à 20:00

```
Aujourd'hui 19:00 : Cache HIT (valide jusqu'à 20:00)
Aujourd'hui 21:00 : Cache MISS (expiré)
                    → Nouvelle génération avec données du jour
```

---

## 📈 Métriques et Analytics

### Taux de Cache Hit

```sql
-- Calculer le taux de hit sur les 7 derniers jours
WITH cache_stats AS (
    SELECT 
        COUNT(*) FILTER (WHERE generated_at > NOW() - INTERVAL '7 days') as hits,
        -- Les misses seraient comptés par les logs backend
        0 as misses  -- À implémenter avec un compteur
    FROM gemini_explanations_cache
)
SELECT 
    hits,
    misses,
    ROUND(hits::numeric / (hits + misses) * 100, 2) as hit_rate_pct
FROM cache_stats;
```

### Économies Réalisées

```sql
-- Estimation des économies sur 30 jours
SELECT 
    COUNT(*) as cache_hits,
    COUNT(*) * 0.03 as dollars_saved,
    COUNT(*) * 45 / 60 as hours_saved
FROM gemini_explanations_cache
WHERE generated_at > NOW() - INTERVAL '30 days';
```

---

## ⚠️ Limitations

### 1. Espace de Stockage

Chaque explication = ~5-10 KB de JSON
- 1000 caches = ~5-10 MB
- Négligeable pour Supabase

### 2. Invalidation Manuelle

Si vous modifiez les données manuellement dans Supabase :
```sql
DELETE FROM gemini_explanations_cache
WHERE user_id = '<user_id>' AND target_date = '2026-02-03';
```

### 3. Hash Collision (Très Rare)

Probabilité de collision MD5 : ~1 / 2^128 = négligeable

---

## 🔮 Améliorations Futures

### 1. Cache Analytics Dashboard

Ajouter des métriques dans l'API :
```json
{
    "cache_hit": true,
    "generated_at": "2026-02-03T08:30:00Z",
    "cached_for": "4h 30m"
}
```

### 2. Cache Warming

Pré-générer les explications la nuit pour tous les utilisateurs :
```python
async def warm_cache_for_all_users():
    users = get_all_users()
    for user in users:
        await generate_explanation(user.id)
```

### 3. Cache Par Niveau de Détail

Permettre différents niveaux de cache :
- `brief` : Explication courte
- `detailed` : Explication complète
- `with_recommendations` : Avec conseils actionnables

---

## ✅ Résumé

| Critère | Sans Cache | Avec Cache |
|---------|-----------|-----------|
| **1er appel** | $0.03, 45s | $0.03, 45s |
| **2ème appel** | $0.03, 45s | $0, 50ms ✅ |
| **3ème appel** | $0.03, 45s | $0, 50ms ✅ |
| **Total (3 appels)** | **$0.09, 2m 15s** | **$0.03, 46s** |
| **Économie** | - | **67% coût, 66% temps** |

---

**Prochaine action** : Appliquer la migration SQL et redémarrer le backend ! 🚀
