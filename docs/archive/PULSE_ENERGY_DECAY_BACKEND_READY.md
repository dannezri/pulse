# ✅ Pulse Energy Decay Backend - Implémentation Complète

**Date** : 31 Janvier 2026  
**Status** : 🟢 Prêt pour test

---

## 📦 Fichiers Créés

### 1. Service Principal
**`backend/pulse_energy_decay_service.py`** (570 lignes)
- ✅ Classe `PulseEnergyDecayService` complète
- ✅ Calcul E0 (readiness_score - malus HRV)
- ✅ Décroissance circadienne (-4% ou -7% par heure)
- ✅ Creux post-lunch (7h-9h après réveil, -10 points)
- ✅ Pharmacocinétique des médicaments (courbes de Gauss)
  - Stimulants : Pic T+1h, durée 4h, +15%
  - Sédatifs : Pic T+2h, durée 6h, -20%
- ✅ Génération `influencers` (Sommeil, HRV, Médicaments, Conditions)
- ✅ Détection risk windows
- ✅ Génération notes explicatives
- ✅ Sauvegarde dans `intraday_energy_forecast`

### 2. Intégrations API
**`backend/api_server.py`** (modifié)
- ✅ Endpoint `/api/energy/intraday` avec paramètre `model`
  - `model=auto` : Auto-select (Pulse Energy Decay si Oura, sinon heuristique)
  - `model=pulse_energy_decay` : Force V2
  - `model=heuristic` : Force V1
- ✅ Fallback gracieux vers V1 si V2 échoue

**`backend/services/ai_service.py`** (modifié)
- ✅ Auto-select dans `/api/brief`
- ✅ Vérification `readiness_score` avant d'utiliser V2
- ✅ Fallback vers V1 si pas de données Oura

### 3. Script de Test
**`backend/test_pulse_energy_decay.py`**
- Script autonome pour tester le service
- Affiche : courbe, influencers, risk windows, notes

---

## 🗄️ Données en DB

### Profil Utilisateur Test
**User ID** : `c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd`

```sql
-- Médicaments (profiles.medications)
[
  {"name": "Caféine", "time": "08:30", "type": "stimulant", "dose": "200mg"},
  {"name": "Magnésium", "time": "22:00", "type": "sedatif", "dose": "400mg"}
]

-- Conditions (profiles.conditions)
["fatigue_chronique"]

-- Chronotype
"morning"

-- Health Profile (health_profiles.current_metrics)
{
  "readiness_score": 72,
  "hrv_ms": 45,
  "resting_hr": 65,
  "sleep_score": 78,
  "activity_score": 65
}

-- Anomalies (health_profiles.anomalies)
[
  {
    "type": "hrv_drop",
    "severity": "medium",
    "z_score": -1.8,
    "detected_at": "2026-01-31T08:00:00Z"
  }
]
```

---

## 🧮 Exemple de Calcul

### Capital de Départ (E0)
```
E0 = readiness_score - malus_HRV
E0 = 72 - 15  (car z_score = -1.8 < -1.5)
E0 = 57
```

### Décroissance (D)
```
decay_rate = 0.07  (car "fatigue_chronique")
Après 8h : E = 57 - (57 * 0.07 * 8) = 57 - 31.92 = 25.08
```

### Creux Post-Lunch
```
Si t = wake_time + 8h (14h) :
  E = E - 10 * sin(progress * π)
  E ≈ 15  (creux maximal vers 14h-16h)
```

### Impact Médicaments
```
Caféine à 08:30 :
  - Pic à 09:30 (+15%)
  - Décroissance gaussienne jusqu'à 12:30

Magnésium à 22:00 :
  - Pic à 00:00 (-20%)
  - Endormissement facilité
```

### Influencers Générés
```json
[
  {"name": "Sommeil (Readiness)", "impact": "+2", "status": "neutral"},
  {"name": "HRV Anomaly", "impact": "-15", "status": "negative"},
  {"name": "Médicament (Caféine)", "impact": "+15", "status": "positive"},
  {"name": "Condition (Fatigue)", "impact": "-24", "status": "negative"}
]
```

---

## 🧪 Tests à Effectuer

### Test 1 : Endpoint Direct
```bash
curl -X GET "http://localhost:9000/api/energy/intraday?model=pulse_energy_decay&force_refresh=true" \
  -H "Authorization: Bearer c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd"
```

**Résultat attendu** :
```json
{
  "type": "pulse_energy_decay",
  "date": "2026-01-31",
  "current_energy": 57,
  "calculation_model": "pulse_energy_decay_v1",
  "forecast_curve": [
    {"time": "...", "value": 57, "event": ""},
    {"time": "...", "value": 70, "event": "Medication: Caféine"},
    {"time": "...", "value": 15, "event": "Circadian Dip"}
  ],
  "influencers": [
    {"name": "Sommeil (Readiness)", "impact": "+2", "status": "neutral"},
    {"name": "HRV Anomaly", "impact": "-15", "status": "negative"}
  ],
  "windows": [
    {"from": "14:00", "to": "16:00", "kind": "dip", "label": "Creux probable"}
  ],
  "notes": [
    "⚠️ Anomalie HRV détectée ce matin (Z-Score: -1.8)",
    "💊 Pic Caféine vers 09:30 (+15%)",
    "📉 Creux circadien prévu 14:00-16:00"
  ],
  "confidence": 0.9
}
```

### Test 2 : Auto-Select
```bash
curl -X GET "http://localhost:9000/api/energy/intraday?model=auto" \
  -H "Authorization: Bearer c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd"
```

**Résultat attendu** : Pulse Energy Decay V2 (car readiness_score présent)

### Test 3 : Brief Complet
```bash
curl -X GET "http://localhost:9000/api/brief?force_refresh=true" \
  -H "Authorization: Bearer c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd"
```

**Résultat attendu** :
```json
{
  "status": "success",
  "cards": [...],
  "pulseScore": 65,
  "intraday_energy_forecast": {
    "type": "pulse_energy_decay",
    "current_energy": 57,
    "influencers": [...]
  }
}
```

### Test 4 : Script Python
```bash
cd /Users/dannezri/Desktop/Pulse/backend
python3 test_pulse_energy_decay.py
```

---

## 📱 Affichage Mobile

### Modifications Requises (IntradayEnergyCurveCard.tsx)

1. **Afficher `influencers`** :
```tsx
{forecast.influencers && (
  <View style={styles.influencersSection}>
    <Text style={styles.sectionTitle}>FACTEURS CLÉS</Text>
    {forecast.influencers.map((inf, i) => (
      <View key={i} style={styles.influencerRow}>
        <Text style={styles.influencerName}>{inf.name}</Text>
        <Text style={[styles.influencerImpact, {
          color: inf.status === 'positive' ? '#34C759' : '#FF3B30'
        }]}>
          {inf.impact}
        </Text>
      </View>
    ))}
  </View>
)}
```

2. **Afficher `forecast_curve` au lieu de `points`** :
```tsx
const dataPoints = forecast.forecast_curve || 
                   forecast.points.map(p => ({ time: p.t, value: p.energy, event: '' }));
```

3. **Markers d'événements** :
```tsx
{dataPoints
  .filter(point => point.event && point.event !== '')
  .map((point, i) => (
    <Circle
      key={i}
      cx={calculateX(point.time)}
      cy={calculateY(point.value)}
      r="6"
      fill="#FF9500"
    />
  ))}
```

---

## 🎯 Prochaines Étapes

### Immédiat
1. ✅ Migration DB appliquée
2. ✅ Service backend créé
3. ✅ Intégrations API complètes
4. 🔲 **Tester l'endpoint** (curl ou Postman)
5. 🔲 **Afficher influencers sur mobile**

### Court Terme
- Intégrer vraie API Oura (au lieu de données simulées)
- Ajouter chronotype detection (morning/evening person)
- Affiner les coefficients pharmacocinétiques

### Moyen Terme
- A/B Testing V1 vs V2
- Feedback utilisateurs sur précision
- ML pour affiner les paramètres (decay_rate, medication impacts)

---

## 🐛 Debugging

### Logs à Vérifier
```python
logger.info(f"[PulseEnergyDecay] E0 calculated: {E0}")
logger.info(f"[Intraday] Auto-select: advanced (has_readiness=True)")
```

### Erreurs Possibles

1. **`readiness_score` = 0** → Fallback V1
   - Solution : Insérer `health_profiles` avec `current_metrics.readiness_score`

2. **Z-Score HRV manquant** → Pas de malus
   - Solution : Insérer `anomalies` avec `z_score`

3. **Médicaments mal parsés** → Impact = 0
   - Solution : Vérifier format JSON `[{"name": "...", "time": "HH:MM", "type": "stimulant"}]`

---

**✅ Le backend est prêt ! Il ne reste plus qu'à tester et afficher les `influencers` sur mobile.**
