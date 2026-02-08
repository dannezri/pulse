# ✅ Harmonisation Échelle Energy (0-1 → 0-100)

**Date:** 30 Janvier 2026  
**Statut:** ✅ Complété  
**Impact:** Cohérence API, Simplification Mobile

---

## 🎯 Problème Identifié

### Avant (Incohérent)

| Endpoint | Échelle | Exemple | Format |
|----------|---------|---------|--------|
| **Energy Overview** (`/api/energy/daily`) | 0-1 | `0.78` | Float |
| **Energy Forecast** (`/energy_forecast`) | 0-100 | `52` | Integer |

**Conséquences** :
- ❌ Confusion dans le code mobile (quand multiplier par 100 ?)
- ❌ Risque d'erreurs d'affichage
- ❌ Incohérence UX (78% vs 52)
- ❌ Code dupliqué de conversion

---

## ✅ Solution Implémentée

### Convention Unique : **0-100 dans l'API**

| Couche | Échelle | Raison |
|--------|---------|--------|
| **Base de Données** | 0-1 (float) | Précision scientifique, standard ML |
| **API (JSON)** | 0-100 (integer) | Lisibilité, intuitivité |
| **Mobile (UI)** | 0-100 (affichage direct) | Simplicité, pas de conversion |

**Principe** : La conversion 0-1 → 0-100 se fait **une seule fois, dans l'endpoint API**.

---

## 🔧 Modifications Apportées

### 1. Backend - API Endpoint

**Fichier** : `backend/api_server.py`

```python
@app.get("/api/energy/daily")
async def get_daily_energy_endpoint(...):
    """
    ✅ CONVENTION API : Scores en 0-100 (cohérence avec energy_forecast)
    """
    # Récupérer depuis DB (en 0-1)
    energy = get_daily_energy(user_id, date)
    
    # ✅ CONVERSION 0-1 → 0-100 pour l'API
    energy_api = {
        'energy_score': round(energy['energy_score'] * 100),  # 0.78 → 78
        'confidence': round(energy['confidence'] * 100),      # 0.82 → 82
        'components': {
            'recovery': round(energy['components']['recovery'] * 100),
            'sleep_debt': round(energy['components']['sleep_debt'] * 100),
            'overtrain': round(energy['components']['overtrain'] * 100),
            'infection': round(energy['components']['infection'] * 100),
        },
        # ... autres champs inchangés
    }
    
    return JSONResponse(content=energy_api, status_code=200)
```

**Changements** :
- ✅ `energy_score` : 0.78 → 78
- ✅ `confidence` : 0.82 → 82
- ✅ `components.*` : tous convertis en 0-100

### 2. Mobile - Interface TypeScript

**Fichier** : `mobile/src/hooks/useDailyEnergy.ts`

```typescript
export interface DailyEnergy {
  energy_score: number;        // ✅ 0-100 (depuis API, déjà converti)
  label: string;
  confidence: number;          // ✅ 0-100 (depuis API, déjà converti)
  reasons: EnergyReason[];
  primary_action: PrimaryAction;
  risk_windows: RiskWindow[];
  components: {                // ✅ 0-100 (depuis API, déjà convertis)
    recovery: number;
    sleep_debt: number;
    overtrain: number;
    infection: number;
  };
}
```

**Changements** :
- ✅ Commentaires mis à jour : `0-100` au lieu de `0-1`
- ✅ Plus besoin de conversion dans le mobile

### 3. Mobile - Hook d'Adaptation

**Fichier** : `mobile/src/hooks/useEnergyOverview.ts`

**Avant** :
```typescript
// ❌ Conversion dans le mobile
const score = Math.round(dailyEnergy.energy_score * 100);
```

**Après** :
```typescript
// ✅ Score déjà en 0-100 depuis l'API
const score = dailyEnergy.energy_score;
```

### 4. Mobile - Composant d'Affichage

**Fichier** : `mobile/src/components/DailyEnergyCard.tsx`

**Avant** :
```typescript
const scorePercent = Math.round(energy.energy_score * 100);
const confidencePercent = Math.round(energy.confidence * 100);
```

**Après** :
```typescript
const scorePercent = energy.energy_score; // ✅ Déjà en 0-100
const confidencePercent = energy.confidence; // ✅ Déjà en 0-100
```

### 5. Mobile - Helpers

**Fichier** : `mobile/src/hooks/useDailyEnergy.ts`

**Avant** :
```typescript
export const getEnergyEmoji = (score: number): string => {
  if (score >= 0.80) return '🌟';  // ❌ Échelle 0-1
  if (score >= 0.65) return '🟢';
  // ...
};
```

**Après** :
```typescript
export const getEnergyEmoji = (score: number): string => {
  if (score >= 80) return '🌟';  // ✅ Échelle 0-100
  if (score >= 65) return '🟢';
  // ...
};
```

---

## 📊 Comparaison Avant/Après

### Exemple Concret

**Données en DB** :
```json
{
  "energy_score": 0.78,
  "confidence": 0.82,
  "components": {
    "recovery": 0.72,
    "sleep_debt": 0.65,
    "overtrain": 0.60,
    "infection": 0.75
  }
}
```

### Avant (Incohérent)

**API Response** :
```json
{
  "energy_score": 0.78,  // ❌ 0-1
  "confidence": 0.82,    // ❌ 0-1
  "components": {
    "recovery": 0.72,    // ❌ 0-1
    // ...
  }
}
```

**Mobile (conversion manuelle)** :
```typescript
const score = Math.round(energy.energy_score * 100);  // 78
const confidence = Math.round(energy.confidence * 100); // 82
```

### Après (Cohérent) ✅

**API Response** :
```json
{
  "energy_score": 78,    // ✅ 0-100
  "confidence": 82,      // ✅ 0-100
  "components": {
    "recovery": 72,      // ✅ 0-100
    "sleep_debt": 65,    // ✅ 0-100
    "overtrain": 60,     // ✅ 0-100
    "infection": 75      // ✅ 0-100
  }
}
```

**Mobile (affichage direct)** :
```typescript
const score = energy.energy_score;  // ✅ 78 directement
const confidence = energy.confidence; // ✅ 82 directement
```

---

## ✅ Avantages

| Avantage | Description |
|----------|-------------|
| **Cohérence API** | Tous les endpoints retournent 0-100 |
| **Simplicité Mobile** | Plus de conversion, affichage direct |
| **Moins d'Erreurs** | Plus de confusion sur l'échelle |
| **Code Plus Clair** | Intent explicite dans les commentaires |
| **Facilité Debug** | Valeurs lisibles (78 au lieu de 0.78) |
| **Précision DB** | Garder 0-1 en DB pour ML/calculs |

---

## 🔄 Cohérence Globale

### Tous les Endpoints Energy

| Endpoint | Score | Échelle | Statut |
|----------|-------|---------|--------|
| `GET /api/energy/daily` | `energy_score` | 0-100 | ✅ Harmonisé |
| `GET /api/energy/forecast` (via table) | `predicted_energy_score` | 0-100 | ✅ Déjà bon |
| `GET /api/energy/profile` (futur) | `traits.*.score` | 0-100 | ✅ À suivre |

### Convention Documentation

**Toujours spécifier l'échelle dans les commentaires** :

```typescript
// ✅ Bon
energy_score: number;  // 0-100 (integer)

// ❌ Mauvais
energy_score: number;  // Pas clair
```

---

## 🧪 Tests de Validation

### Backend

```python
# Test de conversion
def test_api_energy_conversion():
    # Simuler DB response (0-1)
    db_energy = {
        'energy_score': 0.78,
        'confidence': 0.82,
    }
    
    # Appeler l'endpoint
    response = client.get('/api/energy/daily', headers={'Authorization': f'Bearer {token}'})
    
    # Vérifier conversion (0-100)
    assert response.json()['energy_score'] == 78
    assert response.json()['confidence'] == 82
```

### Mobile

```typescript
// Test d'affichage direct
test('useEnergyOverview displays score without conversion', () => {
  const mockEnergy = {
    energy_score: 78,  // Déjà 0-100
    label: 'Bonne journée',
    // ...
  };
  
  const overview = adaptDailyEnergyToOverview(mockEnergy);
  
  expect(overview.score).toBe(78);  // Pas de * 100
});
```

---

## 📁 Fichiers Modifiés

### Backend
- ✅ `backend/api_server.py` (conversion dans endpoint)

### Mobile
- ✅ `mobile/src/hooks/useDailyEnergy.ts` (interface + helpers)
- ✅ `mobile/src/hooks/useEnergyOverview.ts` (suppression conversion)
- ✅ `mobile/src/components/DailyEnergyCard.tsx` (affichage direct)

### Documentation
- ✅ `ENERGY_SCORE_HARMONIZATION.md` (ce fichier)
- ⏳ `MOBILE_SCREENS_GUIDE.md` (à mettre à jour)
- ⏳ `DAILY_ENERGY_BACKEND_MIGRATION.md` (à mettre à jour)

---

## 🎯 Prochaines Étapes

1. ✅ Harmonisation Energy Overview et Forecast
2. ⏳ Tester avec données réelles
3. ⏳ Mettre à jour guides utilisateur
4. ⏳ Valider cohérence dans tous les composants
5. ⏳ Ajouter tests unitaires/intégration

---

## 📚 Références

- **Issue** : Incohérence échelle Energy (0-1) vs Forecast (0-100)
- **Décision** : Convention unique 0-100 dans l'API
- **Pattern** : Conversion unique dans l'endpoint backend
- **Justification** : Simplicité, cohérence, moins d'erreurs

---

**✅ L'harmonisation est complète. Tous les scores energy sont maintenant cohérents en 0-100 dans l'API.** 🚀
