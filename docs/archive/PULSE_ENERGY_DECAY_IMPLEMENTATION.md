# 🎯 Implémentation du Modèle "Pulse Energy Decay"

## Vue d'ensemble

Évolution de la carte "Énergie – reste de la journée" d'un modèle heuristique V1 vers un modèle mathématique précis basé sur la pharmacocinétique, la biométrie Oura et les conditions de santé.

---

## 📊 Formule Mathématique

$$E(t) = (S_{base} \times R_{oura}) - D(t) + \sum M_{adj}(t)$$

Où :
- **$E_0$** : Capital de départ = `readiness_score` (Oura) - Malus HRV
- **$D(t)$** : Décroissance circadienne (-4% ou -7% par heure + creux post-lunch)
- **$M_{adj}(t)$** : Modificateurs pharmacocinétiques (médicaments)

---

## 🗂️ PHASE 1 : Fondations Données (DB)

### ✅ Migration 031 créée

Fichier : `database/migrations/031_pulse_energy_decay_model.sql`

**Nouvelles structures** :
- **Table `health_profiles`** : `current_metrics`, `anomalies`
- **Extension `profiles`** : `medications`, `conditions`, `chronotype`
- **Extension `intraday_energy_forecast`** : `influencers`, `calculation_model`
- **Fonctions helpers** : `get_today_health_profile()`, `get_active_medications()`, `get_health_conditions()`

### 🔧 Application

```bash
# Via MCP Supabase
mcp_supabase-pulse_apply_migration \
  --name="pulse_energy_decay_model" \
  --query="$(cat database/migrations/031_pulse_energy_decay_model.sql)"
```

---

## 🧮 PHASE 2 : Service Backend (Modèle Mathématique)

### Nouveau fichier : `backend/pulse_energy_decay_service.py`

**Responsabilités** :
1. **Récupération données** :
   - `readiness_score` depuis Oura
   - Anomalies HRV (Z-Score < -1.5)
   - Médicaments avec pharmacocinétique
   - Conditions de santé

2. **Calcul Capital $E_0$** :
   ```python
   E0 = readiness_score
   if hrv_z_score < -1.5:
       E0 -= 15
   ```

3. **Décroissance Circadienne $D(t)$** :
   ```python
   decay_rate = 0.07 if 'fatigue_chronique' in conditions else 0.04
   hours_since_wake = (t - wake_time).hours
   decay = E0 * decay_rate * hours_since_wake
   
   # Creux post-lunch
   if wake_time + 7h <= t <= wake_time + 9h:
       decay += 10
   ```

4. **Pharmacocinétique $M_{adj}(t)$** :
   ```python
   for med in medications:
       time_since_dose = t - med['time']
       if med['type'] == 'stimulant':
           peak = 1h  # +15% pic
           duration = 4h
           impact = calculate_bell_curve(time_since_dose, peak, duration, +15)
       elif med['type'] == 'sedatif':
           peak = 2h  # -20% pic
           duration = 6h
           impact = calculate_bell_curve(time_since_dose, peak, duration, -20)
   ```

5. **Génération forecast_curve** :
   ```python
   forecast_curve = []
   for hour in range(16):  # 16h de prévision
       t = now + timedelta(hours=hour)
       energy = E0 - D(t) + sum(M_adj(t))
       energy = max(0, min(100, energy))
       forecast_curve.append({
           "time": t.strftime("%H:%M"),
           "value": energy,
           "event": detect_event(t)
       })
   ```

6. **Génération influencers** :
   ```python
   influencers = [
       {"name": "Sommeil", "impact": f"+{readiness_score}", "status": "positive"},
       {"name": "HRV", "impact": f"{hrv_impact:+d}", "status": status},
       {"name": "Médicament", "impact": f"+{med_boost}", "status": "positive"},
       ...
   ]
   ```

### Structure JSON de sortie

```json
{
  "type": "pulse_energy_decay",
  "date": "2026-01-31",
  "generated_at": "2026-01-31T08:15:00Z",
  "model_version": "pulse_energy_decay_v1",
  "calculation_model": "pulse_energy_decay_v1",
  
  "current_energy": 72,
  
  "forecast_curve": [
    {"time": "08:00", "value": 92, "event": "Wake up"},
    {"time": "09:00", "value": 95, "event": "Medication: L-Thyroxin"},
    {"time": "14:00", "value": 55, "event": "Circadian Dip"},
    {"time": "22:00", "value": 15, "event": "Sleep Ready"}
  ],
  
  "influencers": [
    {"name": "Sommeil (Readiness)", "impact": "+85", "status": "positive"},
    {"name": "HRV Anomaly", "impact": "-15", "status": "negative"},
    {"name": "Médicament (Stimulant)", "impact": "+12", "status": "positive"},
    {"name": "Condition (Fatigue)", "impact": "-18", "status": "negative"}
  ],
  
  "points": [...],  // Ancien format pour compatibilité
  "windows": [...],
  "events": [...],
  "notes": [
    "💊 Pic médicament à 09h (+15%)",
    "📉 Creux circadien vers 14h-16h",
    "⚠️ Anomalie HRV détectée ce matin"
  ],
  
  "confidence": 0.85
}
```

---

## 🎨 PHASE 3 : Frontend Mobile (Affichage Enrichi)

### Modifications `IntradayEnergyCurveCard.tsx`

1. **Afficher `influencers`** :
   ```tsx
   {/* Section Influencers */}
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

2. **Markers d'événements sur la courbe** :
   ```tsx
   {/* Événements importants */}
   {forecast.forecast_curve
     .filter(point => point.event && point.event !== '')
     .map((point, i) => {
       const x = calculateX(point.time);
       const y = calculateY(point.value);
       return (
         <React.Fragment key={i}>
           <Circle cx={x} cy={y} r="6" fill="#FF9500" />
           <SvgText x={x} y={y - 15} fill="#FF9500" fontSize="10" textAnchor="middle">
             {getEventIcon(point.event)}
           </SvgText>
         </React.Fragment>
       );
     })}
   ```

3. **Gradient de courbe dynamique** :
   ```tsx
   <Defs>
     <LinearGradient id="energyGradient" x1="0" y1="0" x2="1" y2="0">
       {forecast.forecast_curve.map((point, i) => (
         <Stop
           key={i}
           offset={i / (forecast.forecast_curve.length - 1)}
           stopColor={point.value > 50 ? '#32D74B' : '#FF9500'}
         />
       ))}
     </LinearGradient>
   </Defs>
   <Path d={curvePath} stroke="url(#energyGradient)" strokeWidth="4" />
   ```

---

## 🧪 PHASE 4 : Tests & Validation

### Tests Backend

Fichier : `backend/tests/test_pulse_energy_decay.py`

```python
def test_capital_depart_avec_hrv_anomaly():
    """Vérifie le malus de -15 si Z-Score HRV < -1.5"""
    result = calculate_E0(readiness=85, hrv_z_score=-2.0)
    assert result == 70  # 85 - 15

def test_decay_fatigue_chronique():
    """Vérifie le taux de décroissance augmenté"""
    result = calculate_decay(E0=100, hours=5, conditions=['fatigue_chronique'])
    assert result == 35  # 100 * 0.07 * 5

def test_pharmacocinetique_stimulant():
    """Vérifie le pic à T+1h pour stimulant"""
    med = {"name": "Caféine", "time": "08:00", "type": "stimulant"}
    impact_at_9h = calculate_medication_impact(med, time="09:00")
    assert impact_at_9h == 15  # Pic à +15%
```

### Tests d'Intégration

```bash
# Scénario complet
curl -X GET "http://localhost:9000/api/energy/intraday?date=2026-01-31&model=pulse_energy_decay" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

## 📈 PHASE 5 : Migration Progressive

### Stratégie de Rollout

1. **Dual-Mode** : Garder `intraday_energy_service.py` (V1) et créer `pulse_energy_decay_service.py` (V2)

2. **Flag Feature** :
   ```python
   use_advanced_model = user.has_oura_data and user.has_medications
   
   if use_advanced_model:
       return PulseEnergyDecayService().generate()
   else:
       return IntradayEnergyService().generate()  # Fallback V1
   ```

3. **A/B Testing** :
   - 20% users → V2 (Pulse Energy Decay)
   - 80% users → V1 (Heuristique)
   - Mesurer : précision, engagement, feedback

4. **Rollout 100%** après validation

---

## 🎓 Bénéfices Clients (Wellness Coach)

### Pour le Client Final

1. **Transparence Totale** :
   > "Ce n'est pas une intuition, c'est ta courbe de pharmacocinétique croisée avec ta récupération Oura."

2. **Prédiction Actionnable** :
   - Voit le pic de caféine à 9h (+15%)
   - Anticipe le creux à 14h-16h
   - Planifie réunion importante à 10h (pic d'énergie)

3. **Adhérence Protocole** :
   - Oublie de noter un médicament → Courbe ne correspond pas au ressenti
   - Encourage màj profil en temps réel

4. **Sécurité** :
   - Anomalie HRV → Courbe "écrasée" dès le matin
   - Validation visuelle du conseil de repos

### Pour le Wellness Coach

1. **Crédibilité Scientifique** :
   - Formule mathématique publiable
   - Références pharmacocinétiques

2. **Diagnostic Rapide** :
   - Voit immédiatement si problème = HRV / Sommeil / Médicament
   - `influencers` = dashboard en un coup d'œil

3. **Suivi Précis** :
   - Compare courbe prédite vs réalité (via check-ins)
   - Ajuste dosages/horaires médicaments

---

## 🚀 Next Steps

### Priorité 1 (Cette Semaine)
- [x] Créer migration SQL `031_pulse_energy_decay_model.sql`
- [ ] Appliquer migration via MCP
- [ ] Créer structure `backend/pulse_energy_decay_service.py`
- [ ] Implémenter fonction `calculate_E0()`

### Priorité 2 (Semaine Prochaine)
- [ ] Implémenter `calculate_decay()`
- [ ] Implémenter `calculate_medication_impact()`
- [ ] Génération `forecast_curve` complète
- [ ] Tests unitaires

### Priorité 3 (Dans 2 Semaines)
- [ ] Intégration Oura API (`readiness_score`)
- [ ] UI Mobile : Affichage `influencers`
- [ ] UI Mobile : Markers événements
- [ ] Tests d'intégration

---

## 📝 Notes Techniques

### Dépendances Requises

```python
# backend/requirements.txt
numpy>=1.24.0  # Pour courbes de Bézier et calculs matriciels
scipy>=1.10.0  # Pour fonctions pharmacocinétiques (bell curves)
```

### Configuration Oura

```bash
# .env
OURA_API_KEY=your_oura_api_key
OURA_API_URL=https://api.ouraring.com/v2
```

### Exemple de Profil Utilisateur Enrichi

```sql
-- Profil complet pour tester le modèle
UPDATE profiles
SET 
    medications = '[
        {"name": "L-Thyroxin", "time": "08:00", "type": "stimulant", "dose": "50mcg"},
        {"name": "Magnésium", "time": "22:00", "type": "sédatif", "dose": "400mg"}
    ]'::jsonb,
    conditions = '["fatigue_chronique"]'::jsonb,
    chronotype = 'morning'
WHERE id = 'c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd';

INSERT INTO health_profiles (user_id, profile_date, current_metrics, anomalies)
VALUES (
    'c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd',
    CURRENT_DATE,
    '{"readiness_score": 85, "hrv_ms": 65, "resting_hr": 58, "sleep_score": 82}'::jsonb,
    '[{"type": "hrv_drop", "severity": "high", "z_score": -2.3}]'::jsonb
);
```

---

**Auteur** : Claude  
**Date** : 31 Janvier 2026  
**Version** : 1.0  
**Status** : 🟡 Migration créée, implémentation en attente
