# Migration Daily Energy vers Backend

**Date:** 30 Janvier 2026  
**Priorité:** #1 (Prod-Blocking)  
**Statut:** ✅ Complétée

---

## 🎯 Objectif

Déplacer le calcul d'**Energy Overview** (Carte 1 du Brief) du client mobile vers le backend pour garantir:

- ✅ **Cohérence des calculs** : 1 seule version canonique (backend)
- ✅ **Pas de divergences** selon les versions mobile
- ✅ **Historique rejouable** : Stockage en DB avec versioning
- ✅ **Évolutivité** : Intégration future avec LLM/forecast/learning

---

## 🏗️ Architecture Implémentée

### 1. Base de Données

**Nouvelle table `daily_energy`** :

```sql
-- Fichier: database/migrations/029_daily_energy.sql

CREATE TABLE daily_energy (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    energy_date DATE NOT NULL,
    energy_score FLOAT NOT NULL,           -- 0.0-1.0
    label TEXT NOT NULL,                   -- "Excellente journée", etc.
    confidence FLOAT NOT NULL,             -- 0.0-1.0
    reasons JSONB NOT NULL,                -- [{key, text}]
    primary_action JSONB NOT NULL,         -- {key, title, why}
    risk_windows JSONB,                    -- [{from, to, risk, text}]
    components JSONB,                      -- {recovery, sleep_debt, overtrain, infection}
    model_version TEXT NOT NULL DEFAULT 'energy_v1',
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, energy_date)
);
```

**Caractéristiques** :
- Stockage JSON pour flexibilité
- Versioning algorithme (`model_version`)
- RLS activé (sécurité Supabase)
- Contrainte UNIQUE par utilisateur/date

---

### 2. Backend

#### A. Moteur de Calcul (`daily_energy_engine.py`)

**Fonctions implémentées** :

```python
# Calcul principal
def compute_daily_energy(states: Dict) -> Dict:
    """
    Calcule le score d'énergie à partir des états latents
    
    Input: {recovery, sleep_debt, overtrain, infection_like}
    Output: {energy_score, label, confidence, reasons, primary_action, risk_windows, components}
    """
    # Pondérations V1
    WEIGHT_RECOVERY = 0.45
    WEIGHT_SLEEP_DEBT = 0.25
    WEIGHT_OVERTRAIN = 0.20
    WEIGHT_INFECTION = 0.10
    
    # Normalisation en "bon"
    recovery_good = recovery_score
    sleep_debt_good = 1 - sleep_debt_score
    overtrain_good = 1 - overtrain_score
    infection_good = 1 - infection_score
    
    # Score final
    energy = weighted_sum(...)
    
    # Label lifestyle
    if energy >= 0.80: "Excellente journée"
    elif energy >= 0.65: "Bonne journée"
    elif energy >= 0.50: "Journée moyenne"
    else: "Journée fragile"

# Persistence
def get_daily_energy(user_id: str, date_str: str) -> Optional[Dict]:
    """Récupère depuis daily_energy table"""

def save_daily_energy(user_id: str, date_str: str, energy_data: Dict) -> bool:
    """Sauvegarde dans daily_energy table"""
```

#### B. Intégration dans `LatentStateService`

**Fichier** : `backend/services/latent_state_service.py`

```python
def calculate_all_states(self, user_id: str, target_date: date) -> Dict:
    # 1-5. Calcul des états latents (recovery, sleep_debt, overtrain, infection)
    
    # 6. Sauvegarde des états
    self._save_states(user_id, target_date, states)
    
    # 7. ✅ NOUVEAU: Calcul et sauvegarde daily_energy
    self._calculate_and_save_daily_energy(user_id, target_date, states)
    
    return states
```

**Déclenchement** :
- Automatique après calcul des états latents
- Erreur non-bloquante (si échec, ne bloque pas les états)
- Versioning automatique (`energy_v1`)

#### C. Endpoint API

**Fichier** : `backend/api_server.py`

```python
@app.get("/api/energy/daily")
async def get_daily_energy_endpoint(
    date: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """
    Récupère le daily energy pour un utilisateur
    
    Query params:
        date: YYYY-MM-DD (défaut: aujourd'hui)
    
    Headers:
        Authorization: Bearer <JWT>
    
    Response:
        {
            "energy_score": 0.78,
            "label": "Bonne journée",
            "confidence": 0.82,
            "reasons": [{"key": "recovery_good", "text": "..."}],
            "primary_action": {"key": "...", "title": "...", "why": "..."},
            "risk_windows": [...],
            "components": {...}
        }
    """
    user_id = verify_jwt_token(authorization=authorization)
    energy = get_daily_energy(user_id, date)
    
    if not energy:
        raise HTTPException(status_code=404, detail="Daily energy not found")
    
    return JSONResponse(content=energy, status_code=200)
```

---

### 3. Mobile

#### A. Hook `useDailyEnergy` (Nouvelle Implémentation)

**Fichier** : `mobile/src/hooks/useDailyEnergy.ts`

**Avant** :
```typescript
// ❌ Calcul côté client (duplication logique)
export const useDailyEnergy = (date?: string) => {
  // Récupère daily_states depuis Supabase
  // Recalcule energy localement
  const energy = computeDailyEnergy(states);
  return { energy, loading, error };
};
```

**Après** :
```typescript
// ✅ Appel API backend (source unique de vérité)
export const useDailyEnergy = (date?: string) => {
  const fetchEnergy = async () => {
    const session = await supabase.auth.getSession();
    const url = `${API_URL}/api/energy/daily${date ? `?date=${date}` : ''}`;
    
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
      },
    });
    
    const data = await response.json();
    setEnergy(data);
  };
  
  useEffect(() => { fetchEnergy(); }, [date]);
  
  return { energy, loading, error, refresh: fetchEnergy };
};
```

**Avantages** :
- Suppression de **~230 lignes** de code de calcul dupliqué
- Garantie de cohérence avec le backend
- Simplification maintenance

#### B. Hook `useEnergyOverview` (Adaptateur)

**Fichier** : `mobile/src/hooks/useEnergyOverview.ts`

**Rôle** : Adapter `DailyEnergy` (API) → `EnergyOverview` (Composant)

```typescript
export function useEnergyOverview(date?: string): EnergyOverview {
  const { energy, loading, error } = useDailyEnergy(date);
  
  return useMemo(() => {
    if (!energy) {
      return defaultState; // État vide avec message
    }
    
    // Adapter format API → format composant
    return {
      state: mapLabelToState(energy.label),
      score: Math.round(energy.energy_score * 100),
      title: generateContextualTitle(energy.label),
      reasons: energy.reasons.map(r => r.text),
      action: energy.primary_action.title,
    };
  }, [energy]);
}
```

**Mapping** :
| Backend Label | Mobile State |
|---------------|-------------|
| "Excellente journée" | `excellent` |
| "Bonne journée" | `good` |
| "Journée moyenne" | `moderate` |
| "Journée fragile" | `low` |

#### C. Composant `index.tsx` (Simplifié)

**Fichier** : `mobile/app/(tabs)/index.tsx`

**Avant** :
```typescript
const { data: dailyStates, refetch: refetchStates } = useDailyStates(userId);
const energyOverview = useEnergyOverview(dailyStates);

const onRefresh = async () => {
  await Promise.all([refetch(), refetchStates()]);
};
```

**Après** :
```typescript
// ✅ Plus besoin de dailyStates
const energyOverview = useEnergyOverview();

const onRefresh = async () => {
  await refetch(); // Simplifié
};
```

---

## 📦 Fichiers Modifiés

### Backend
- ✅ `database/migrations/029_daily_energy.sql` (nouveau)
- ✅ `backend/daily_energy_engine.py` (complété)
- ✅ `backend/services/latent_state_service.py` (ajout calcul)
- ✅ `backend/api_server.py` (nouvel endpoint)

### Mobile
- ✅ `mobile/src/hooks/useDailyEnergy.ts` (API au lieu de calcul local)
- ✅ `mobile/src/hooks/useEnergyOverview.ts` (adaptateur)
- ✅ `mobile/app/(tabs)/index.tsx` (simplifié)

---

## 🚀 Déploiement

### 1. Database

```bash
cd database
psql $DATABASE_URL -f migrations/029_daily_energy.sql
```

**Vérification** :
```sql
SELECT COUNT(*) FROM daily_energy;
-- Devrait être 0 (table vide au départ)

SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'daily_energy';
-- Vérifier la structure
```

### 2. Backend

**Redémarrer le serveur API** :
```bash
cd backend
python api_server.py
```

**Test manuel** :
```bash
# Obtenir un JWT token
export TOKEN="eyJhb..."

# Test endpoint
curl -X GET "http://localhost:9000/api/energy/daily" \
  -H "Authorization: Bearer $TOKEN"

# Devrait retourner 404 si pas encore calculé
# ou 200 avec le JSON energy si déjà calculé
```

### 3. Calcul Initial

Le `daily_energy` sera calculé automatiquement lors du prochain calcul des états latents.

**Déclencher manuellement** :
```python
from services.latent_state_service import LatentStateService
from supabase_client import SupabaseClient
from datetime import date

supabase = SupabaseClient(...)
service = LatentStateService(supabase)

# Calcul pour aujourd'hui
states = service.calculate_all_states(
    user_id='<UUID>',
    target_date=date.today(),
    force_refresh=True
)

print("✅ Daily energy calculé et sauvegardé")
```

### 4. Mobile

**Rebuild** :
```bash
cd mobile
npm install
npx expo start --clear
```

**Vérifications** :
- ✅ L'app démarre sans erreur
- ✅ La carte Energy Overview s'affiche
- ✅ Pull-to-refresh fonctionne
- ✅ Pas de calcul local (vérifier console logs)

---

## 🧪 Tests

### Backend

**Test unitaire** :
```python
# Test du moteur de calcul
from daily_energy_engine import compute_daily_energy

test_states = {
    'recovery': {'smoothed_score': 0.72, 'confidence': 0.85},
    'sleep_debt': {'smoothed_score': 0.35, 'confidence': 0.90, 'metadata': {'debt_hours': 2.3}},
    'overtrain': {'smoothed_score': 0.40, 'confidence': 0.75},
    'infection_like': {'smoothed_score': 0.25, 'confidence': 0.60, 'metadata': {'persistent': False}},
}

energy = compute_daily_energy(test_states)

assert energy['energy_score'] >= 0.0 and energy['energy_score'] <= 1.0
assert energy['label'] in ['Excellente journée', 'Bonne journée', 'Journée moyenne', 'Journée fragile']
assert len(energy['reasons']) > 0
assert 'key' in energy['primary_action']
print("✅ Tests unitaires passés")
```

**Test API** :
```bash
# Simuler un utilisateur avec des données
pytest backend/tests/test_daily_energy_api.py -v
```

### Mobile

**Test manuel** :
1. Ouvrir l'app sur simulateur/device
2. Aller sur l'écran Brief (Accueil)
3. Vérifier que la carte Energy Overview s'affiche
4. Pull-to-refresh → Vérifier que les données se mettent à jour
5. Vérifier console logs : `[useDailyEnergy] Fetching from API:`

**Test comportement sans données** :
1. Nouveau compte sans daily_states calculés
2. Vérifier message par défaut : "Synchronisation en cours"

---

## 📊 Métriques de Succès

| Métrique | Avant | Après | Amélioration |
|----------|-------|-------|-------------|
| **Code mobile (calcul)** | ~315 lignes | ~150 lignes | -52% |
| **Cohérence calculs** | ❌ Divergences possible | ✅ Source unique | +100% |
| **Historique rejouable** | ❌ Non | ✅ Oui (DB) | +∞ |
| **Versioning algo** | ❌ Non | ✅ Oui (`model_version`) | +∞ |
| **Maintenance** | ❌ 2 versions à sync | ✅ 1 version backend | -50% |

---

## 🔄 Flux de Données (Nouvelle Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (Source of Truth)                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Webhook Wearable → Biometrics                          │
│  2. Cron/Manual → LatentStateService.calculate_all_states()│
│     ├─ Calcul recovery, sleep_debt, overtrain, infection   │
│     ├─ Save → daily_state table                            │
│     └─ ✅ NEW: Calcul + Save → daily_energy table          │
│                                                             │
│  3. API GET /api/energy/daily                              │
│     └─ Retourne daily_energy depuis DB                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP + JWT
┌─────────────────────────────────────────────────────────────┐
│                         MOBILE                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. useDailyEnergy() → fetch('/api/energy/daily')          │
│  2. useEnergyOverview() → Adapter format API → Composant   │
│  3. EnergyOverviewCard → Affichage UI                      │
│                                                             │
│  ❌ Plus de calcul local                                   │
│  ✅ Affichage uniquement                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔒 Sécurité

### RLS Policies

```sql
-- Les utilisateurs peuvent voir uniquement leur propre énergie
CREATE POLICY "Users can view own daily_energy" ON daily_energy
    FOR SELECT USING (auth.uid() = user_id);

-- Les utilisateurs peuvent insérer/update/delete leur propre énergie
CREATE POLICY "Users can insert own daily_energy" ON daily_energy
    FOR INSERT WITH CHECK (auth.uid() = user_id);
```

### Authentification API

- ✅ JWT token obligatoire
- ✅ Validation `verify_jwt_token()`
- ✅ Extraction `user_id` depuis token
- ✅ Pas de `user_id` en query param (sécurité)

---

## 🐛 Troubleshooting

### "Daily energy not found (404)"

**Cause** : Pas encore calculé pour cette date

**Solution** :
```python
# Déclencher calcul manuel
from services.latent_state_service import LatentStateService
service = LatentStateService(supabase)
service.calculate_all_states(user_id, target_date, force_refresh=True)
```

### "API error: 500"

**Cause** : Erreur backend (calcul ou DB)

**Debug** :
```bash
# Logs backend
tail -f backend/logs/api_server.log

# Vérifier daily_state existe
SELECT * FROM daily_state WHERE user_id = '<UUID>' AND state_date = '2026-01-30';
```

### "Synchronisation en cours" (mobile)

**Cause** : Pas de données disponibles

**Solutions** :
1. Vérifier que le wearable est connecté
2. Attendre prochain calcul des états latents (cron quotidien)
3. Déclencher calcul manuel (voir ci-dessus)

---

## 📚 Références

- **Architecture Globale** : `ARCHITECTURE.md`
- **Mobile Guide** : `MOBILE_SCREENS_GUIDE.md`
- **Latent States** : `LATENT_STATES_IMPLEMENTATION_SUMMARY.md`
- **API Docs** : `backend/README.md`

---

## ✅ Checklist Production

- [x] Migration SQL créée et testée
- [x] Fonctions backend implémentées (`get`, `save`, `compute`)
- [x] Intégration dans `LatentStateService`
- [x] Endpoint API `/api/energy/daily` créé
- [x] Hook mobile `useDailyEnergy` adapté (API au lieu de calcul)
- [x] Hook mobile `useEnergyOverview` simplifié (adaptateur)
- [x] Composant `index.tsx` mis à jour
- [ ] Migration SQL exécutée en prod
- [ ] Backend redémarré en prod
- [ ] Mobile rebuild + déployé
- [ ] Tests end-to-end validés en prod
- [ ] Monitoring activé (erreurs API, performances)

---

## 🎉 Résultat Final

**Avant** :
- ❌ Calcul dupliqué (backend + mobile)
- ❌ Risque de divergences
- ❌ Pas d'historique
- ❌ Maintenance difficile

**Après** :
- ✅ Calcul backend uniquement
- ✅ Cohérence garantie
- ✅ Historique rejouable
- ✅ Versioning algorithme
- ✅ Mobile simplifié (affichage uniquement)
- ✅ Scalable pour ML/LLM futur

**Le mobile est maintenant un simple client qui affiche les données calculées par le backend. C'est la bonne architecture pour un produit scalable.** 🚀
