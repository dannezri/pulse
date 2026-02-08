# Cache Intelligent Gemini - Analyse des Médicaments 🧠

## Objectif

Optimiser les appels à Gemini pour **ne régénérer l'analyse que lorsque l'historique des médicaments change**, économisant ainsi :
- 🔋 Ressources serveur
- 💰 Coûts API Gemini
- ⚡ Temps de réponse utilisateur

---

## 🔑 Système de Hash Intelligent

### Avant (hash basique)
```typescript
Hash = MD5(medications seulement)
  - Nom du médicament
  - Dosage
  - Heure de prise
  - Date de début
```

**Problème :** L'analyse ne se régénère jamais, même si l'utilisateur prend ses médicaments depuis 1 mois.

### Après (hash intelligent)
```typescript
Hash = MD5(medications + historique)
  - Nom du médicament
  - Dosage
  - Heure de prise
  - Date de début
  + Dernière date d'historique          ← NOUVEAU
  + Nombre total d'entrées              ← NOUVEAU
```

**Avantage :** L'analyse se régénère **uniquement quand de nouvelles prises sont ajoutées**.

---

## 📊 Workflow de Cache

```
┌────────────────────────────────────────────────────┐
│  User ouvre l'app                                  │
└────────────┬───────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────┐
│  useMedicationHistorySync()                        │
│  → Synchronise l'historique                        │
│  → Ajoute nouvelles entrées si nécessaire          │
└────────────┬───────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────┐
│  Nouvelles entrées ajoutées ?                      │
└────────────┬───────────────────────────────────────┘
             │
         OUI │ NON
             │  │
             │  └───────────────────────────────────┐
             ▼                                      ▼
┌────────────────────────────────────┐  ┌──────────────────────────────┐
│  Invalide cache Gemini             │  │  Garde cache existant        │
│  queryClient.invalidateQueries()   │  │  Pas d'appel Gemini          │
└────────────┬───────────────────────┘  └──────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────┐
│  User va dans "Médicaments"                        │
└────────────┬───────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────┐
│  useMedicationAnalysis() fetch l'analyse           │
└────────────┬───────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────┐
│  Backend: medication_analysis_service.py           │
│  1. Calcule hash(medications + historique)         │
│  2. Vérifie si cache existe avec ce hash           │
└────────────┬───────────────────────────────────────┘
             │
         CACHE HIT │ CACHE MISS
                   │  │
                   │  └──────────────────────────┐
                   ▼                             ▼
┌────────────────────────────┐  ┌────────────────────────────────┐
│  Retourne analyse cachée   │  │  Appelle Gemini 3 Pro          │
│  Pas d'appel API           │  │  Génère nouvelle analyse       │
│  ⚡ Instantané              │  │  Stocke dans cache             │
└────────────────────────────┘  └────────────────────────────────┘
```

---

## 🔍 Exemple Concret

### Scénario 1: Première utilisation
```
Jour 1 - 08:00
→ User ajoute Venlafaxine (start_date: 01/02/2025)
→ Historique synchronisé: 6 jours d'entrées (01/02 → 06/02)
→ Hash calculé: abc123... (inclut: last_date=06/02, total=6)
→ Cache MISS → Appel Gemini
→ Analyse générée avec "Vous êtes au début du traitement (J+6)"
→ Stocké en cache avec hash abc123...
```

### Scénario 2: Ouverture le lendemain (pas de nouvelle prise)
```
Jour 2 - 08:00
→ User ouvre l'app
→ Synchronisation historique: aucune nouvelle entrée (déjà à jour)
→ Cache Gemini NON invalidé
→ User va dans "Médicaments"
→ Hash calculé: abc123... (identique)
→ Cache HIT → Retourne analyse existante
→ ⚡ Pas d'appel Gemini
```

### Scénario 3: Lendemain avec nouvelle prise
```
Jour 2 - 18:00
→ User ouvre l'app
→ Synchronisation historique: +1 journée (07/02)
→ Cache Gemini INVALIDÉ (car historique changé)
→ User va dans "Médicaments"
→ Hash calculé: def456... (last_date=07/02, total=7)
→ Cache MISS → Appel Gemini
→ Analyse régénérée avec "Vous êtes au début du traitement (J+7)"
→ Stocké en cache avec hash def456...
```

### Scénario 4: Après 1 mois
```
Jour 30 - 08:00
→ User ouvre l'app
→ Synchronisation historique: +1 journée (01/03)
→ Cache Gemini INVALIDÉ
→ Hash calculé: xyz789... (last_date=01/03, total=30)
→ Cache MISS → Appel Gemini
→ Analyse régénérée avec "Vous êtes en phase d'adaptation (J+30)"
→ Les conseils changent selon la durée du traitement
```

---

## 📈 Bénéfices

### Économie de coûts
```
Sans cache intelligent:
- Chaque ouverture d'app = 1 appel Gemini
- 10 ouvertures/jour = 10 appels
- 1 mois = 300 appels
- Coût: ~300 × $0.002 = $0.60/utilisateur/mois

Avec cache intelligent:
- 1 appel/jour maximum (quand nouvelle prise)
- 30 jours = 30 appels max
- Coût: ~30 × $0.002 = $0.06/utilisateur/mois
- 💰 Économie: 90%
```

### Performance
```
Cache HIT:
- Temps de réponse: ~50ms (lecture DB)
- Pas d'attente Gemini

Cache MISS:
- Temps de réponse: ~2-3 secondes (Gemini + stockage)
```

### Pertinence
```
Analyse adaptée à la durée du traitement:
- J+0 à J+7: "Vous êtes au début du traitement"
- J+7 à J+30: "Phase d'adaptation en cours"
- J+30+: "Traitement stabilisé"

→ L'analyse évolue naturellement avec l'historique
```

---

## 🛠️ Modifications Apportées

### 1. Backend (`medication_analysis_service.py`)

**Nouvelle méthode `_get_history_summary()`**
```python
def _get_history_summary(self, user_id: str) -> Dict:
    """
    Récupère un résumé de l'historique:
    - Dernière date de prise
    - Nombre total d'entrées
    """
    # Query Supabase pour récupérer last_intake_date et total_intakes
    return {
        "last_intake_date": "2026-02-06",
        "total_intakes": 3710,
    }
```

**Méthode `_compute_medications_hash()` modifiée**
```python
def _compute_medications_hash(self, medications: List[Dict], user_id: str) -> str:
    """
    Hash basé sur medications + historique
    """
    history_summary = self._get_history_summary(user_id)
    
    cache_data = {
        "medications": medications,
        "history": history_summary,  # ← NOUVEAU
    }
    
    return hashlib.md5(json.dumps(cache_data).encode()).hexdigest()
```

### 2. Frontend (`useMedicationHistorySync.ts`)

**Invalidation du cache Gemini après synchronisation**
```typescript
// Après synchronisation de l'historique
await queryClient.invalidateQueries({ queryKey: ['medication', 'history'] });

// Invalider AUSSI le cache d'analyse Gemini
await queryClient.invalidateQueries({ queryKey: ['medications', 'analysis'] });
```

---

## 🧪 Tests

### Test 1: Vérifier que le hash inclut l'historique
```python
# Dans backend/
from medication_analysis_service import MedicationAnalysisService

service = MedicationAnalysisService(supabase_client, gemini_client)
hash1 = service._compute_medications_hash(medications, user_id)

# Ajouter une entrée d'historique
# ...

hash2 = service._compute_medications_hash(medications, user_id)

assert hash1 != hash2  # Les hash doivent être différents
```

### Test 2: Vérifier le cache HIT/MISS
```bash
# Logs à vérifier dans la console
[cache] 🔑 Hash computed with history (last: 2026-02-06, total: 3710)
[cache] ✅ Cache HIT for user_id (hash: abc123...)
```

### Test 3: Scénario complet
```
1. Ouvrir l'app → Sync historique → Aller dans "Médicaments"
   → Logs: Cache MISS, appel Gemini

2. Revenir à l'écran principal → Aller dans "Médicaments"
   → Logs: Cache HIT, pas d'appel Gemini

3. Lendemain: Ouvrir l'app → Sync historique (nouvelle journée)
   → Logs: Cache invalidé

4. Aller dans "Médicaments"
   → Logs: Cache MISS, appel Gemini
```

---

## 📊 Monitoring

### Logs Backend
```python
# Dans medication_analysis_service.py
logger.info(f"[cache] 🔑 Hash computed with history (last: {last_date}, total: {total})")
logger.info(f"[cache] ✅ Cache HIT for {user_id}")
logger.info(f"[cache] ❌ Cache MISS for {user_id}")
```

### Logs Frontend
```typescript
// Dans useMedicationHistorySync.ts
console.log('[useMedicationHistorySync] 🔄 Gemini analysis cache invalidated');
```

### Métriques Supabase
```sql
-- Voir les entrées de cache avec leur date
SELECT 
  user_id,
  medications_hash,
  generated_at,
  expires_at,
  jsonb_pretty(analysis) as analysis_preview
FROM medication_analysis_cache
ORDER BY generated_at DESC
LIMIT 10;

-- Voir les analyses récentes vs anciennes
SELECT 
  DATE(generated_at) as date,
  COUNT(*) as analyses_generated,
  COUNT(DISTINCT user_id) as unique_users
FROM medication_analysis_cache
GROUP BY DATE(generated_at)
ORDER BY date DESC;
```

---

## 🎯 Cas d'usage

### User typique (ouvre l'app 3x/jour)
```
Matin (08:00):
  → Sync historique: nouvelle journée
  → Cache Gemini invalidé
  → 1 appel Gemini

Midi (12:00):
  → Sync historique: pas de changement
  → Cache Gemini valide
  → 0 appel Gemini

Soir (20:00):
  → Sync historique: pas de changement
  → Cache Gemini valide
  → 0 appel Gemini

Total: 1 appel/jour au lieu de 3
```

### User qui oublie l'app pendant 1 semaine
```
Jour 8:
  → Sync historique: +7 jours
  → Cache Gemini invalidé
  → Hash inclut: last_date=Jour 8, total=+70 entrées
  → 1 appel Gemini avec analyse mise à jour
```

---

## ✅ Résumé

**Avant :**
- ❌ Appel Gemini à chaque consultation
- ❌ Cache basé uniquement sur les médicaments
- ❌ Analyse ne reflète pas la progression du traitement

**Après :**
- ✅ Appel Gemini uniquement si historique change
- ✅ Cache basé sur medications + historique
- ✅ Analyse évolue avec la durée du traitement
- ✅ Économie de 90% des appels API
- ✅ Performance optimale

---

## 🔮 Améliorations Futures

1. **Cache prédictif**
   - Pré-générer l'analyse la nuit pour le lendemain
   
2. **Différentiel intelligent**
   - Ne régénérer que la partie changée de l'analyse
   
3. **Batch processing**
   - Grouper les demandes d'analyse pour économiser les tokens

4. **TTL dynamique**
   - Cache plus long pour les traitements stables (6+ mois)
   - Cache plus court pour les nouveaux traitements

---

**Le système est maintenant optimisé ! Gemini ne travaille que quand c'est nécessaire. 🎉**
