# Feature: Énergie – Reste de la journée (Intraday Energy Forecast)

## Vue d'ensemble

Cette feature ajoute une nouvelle card dans l'écran Brief de Pulse qui affiche une **courbe d'énergie prédictive** de maintenant jusqu'à la fin de la journée, avec les événements du calendrier superposés et les fenêtres de risque (creux d'énergie).

**Objectif UX:**
- Donner une vision claire de l'évolution de l'énergie dans la journée
- Identifier les moments critiques (creux) et les événements coûteux
- Aider l'utilisateur à planifier ses tâches selon son niveau d'énergie prévu

---

## Architecture

### Backend

#### 1. Migration DB: `030_intraday_energy_forecast.sql`

Crée la table `intraday_energy_forecast` pour stocker les prévisions intraday:

```sql
CREATE TABLE intraday_energy_forecast (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES profiles(id),
    forecast_date DATE NOT NULL,
    timezone TEXT NOT NULL DEFAULT 'UTC',
    generated_at TIMESTAMPTZ NOT NULL,
    points JSONB NOT NULL,        -- Courbe d'énergie (points toutes les 30 min)
    windows JSONB,                -- Fenêtres de risque (creux)
    events JSONB,                 -- Événements calendrier avec impact
    notes JSONB,                  -- Notes explicatives
    model_version TEXT NOT NULL DEFAULT 'intraday_v1',
    confidence FLOAT NOT NULL DEFAULT 0.5,
    UNIQUE(user_id, forecast_date)
);
```

**Helper function:**
```sql
CREATE FUNCTION get_intraday_forecast(p_user_id UUID, p_date DATE)
RETURNS TABLE (...);
```

#### 2. Service: `intraday_energy_service.py`

**Fonctions principales:**

- `classify_event_type(event)` → Classifie un événement calendrier (meeting, sport, travel, focus, social, other)
- `estimate_event_impact(event, event_type, tags, base_energy, recovery, sleep_debt)` → Estime l'impact d'un événement sur l'énergie (-20 à +10)
- `generate_intraday_curve(user_id, target_date, base_energy, recovery, sleep_debt, overtrain, events)` → Génère la courbe d'énergie (points toutes les 30 min)
- `generate_risk_windows_intraday(points, events)` → Détecte les creux d'énergie (< 70 pendant > 1h)
- `generate_notes_intraday(base_energy, recovery, sleep_debt, events, windows)` → Génère des notes explicatives (max 3)
- `generate_intraday_forecast(user_id, target_date)` → Génère la prévision complète
- `save_intraday_forecast(user_id, forecast)` → Sauvegarde en DB
- `get_intraday_forecast(user_id, target_date)` → Récupère depuis DB

**Heuristiques V1 (MVP):**

1. **Base:** Score `daily_energy` du jour (0-100)
2. **Décroissance naturelle:** Énergie plus haute le matin, baisse progressive l'après-midi
3. **Modulation selon états latents:**
   - `sleep_debt > 0.6` → Creux plus tôt dans la journée
   - `recovery < 0.5` → Amplitude du creux plus forte
   - `overtrain > 0.7` → Énergie globalement réduite
4. **Impact événements:**
   - **Meeting:** -5 à -12 selon durée et importance
   - **Sport:** -8 immédiat, puis +5 rebound après 1h
   - **Travel:** -6 selon durée
   - **Focus:** -4 selon durée
   - **Social:** -2 (faible coût)
5. **Détection creux:** Énergie < 70 pendant > 1h

#### 3. Endpoint: `GET /api/energy/intraday`

**Paramètres:**
- `date` (optionnel): Date au format YYYY-MM-DD (défaut: aujourd'hui)
- `force_refresh` (optionnel): Si True, recalcule même si cache existe

**Réponse:**
```json
{
  "type": "intraday_energy",
  "date": "2026-01-30",
  "generated_at": "2026-01-30T09:12:00Z",
  "model_version": "intraday_v1",
  "timezone": "UTC",
  "points": [
    {"t": "2026-01-30T09:15:00Z", "energy": 78},
    {"t": "2026-01-30T09:45:00Z", "energy": 80}
  ],
  "windows": [
    {"from": "16:00", "to": "18:00", "kind": "dip", "label": "Creux probable"}
  ],
  "events": [
    {
      "id": "evt_123",
      "start": "2026-01-30T14:00:00Z",
      "end": "2026-01-30T15:00:00Z",
      "title": "Réunion client",
      "impact": -8,
      "confidence": 0.65,
      "tags": ["work", "high_focus"]
    }
  ],
  "notes": [
    "Creux attendu en fin d'après-midi",
    "Réunion à 14h pourrait être plus coûteuse que prévu"
  ],
  "confidence": 0.75
}
```

#### 4. Intégration dans `/api/brief`

Le service `ai_service.py` a été modifié pour inclure automatiquement `intraday_energy_forecast` dans la réponse du Brief:

```python
# Dans generate_brief()
intraday_forecast = get_intraday_forecast(user_id, today)
if not intraday_forecast:
    intraday_forecast = generate_intraday_forecast(user_id, today)
    if intraday_forecast:
        save_intraday_forecast(user_id, intraday_forecast)

return {
    "status": "success",
    "cards": [...],
    "pulseScore": 58,
    "intraday_energy_forecast": intraday_forecast  # ✅ Nouveau champ
}
```

---

### Mobile

#### 1. Composant: `IntradayEnergyCurveCard.tsx`

**Fonctionnalités:**
- Affiche une courbe d'énergie avec `react-native-svg` (compatible Expo SDK 54)
- Superpose les événements du calendrier (ligne verticale + marker)
- Affiche les fenêtres de risque (creux)
- Liste horizontale scrollable des événements
- Tap sur un événement → Bottom sheet avec détails (titre, heure, impact, tags)
- Notes explicatives en bas de carte

**Props:**
```typescript
interface IntradayEnergyCurveCardProps {
  forecast: IntradayForecast | null;
}
```

**Rendu:**
- Courbe lissée (Bézier cubique) avec couleur selon énergie moyenne (vert > 70, orange 50-70, rouge < 50)
- Point "maintenant" (premier point) avec cercle
- Ticks de temps (heures) sur l'axe X
- Événements avec ligne verticale + marker coloré selon impact

#### 2. Intégration dans `BriefStack.tsx`

La card `IntradayEnergyCurveCard` est insérée **après** la card "Énergie aujourd'hui" et **avant** la card "Prédiction demain":

1. **Card 1:** Énergie aujourd'hui (`EnergyOverviewCard`)
2. **Card 2:** Énergie – reste de la journée (`IntradayEnergyCurveCard`) ← **NOUVEAU**
3. **Card 3:** Prédiction demain (`EnergyForecastCard`)
4. **Cards 4+:** Cartes Brief détaillées

**Props ajoutées:**
```typescript
interface BriefStackProps {
  intradayForecast?: IntradayForecast | null;  // ✅ Nouveau
}
```

#### 3. Intégration dans `index.tsx`

Le composant `HomeScreen` passe `intradayForecast` depuis `briefData`:

```typescript
<BriefStack
  cards={briefData?.cards || []}
  pulseScore={briefData?.pulseScore || 0}
  energyOverview={energyOverview}
  intradayForecast={(briefData as any)?.intraday_energy_forecast || null}
  loading={briefLoading}
  onRefresh={onRefresh}
  refreshing={refreshing}
/>
```

---

## Structure JSON complète

### Intraday Forecast

```json
{
  "type": "intraday_energy",
  "date": "2026-01-30",
  "generated_at": "2026-01-30T09:12:00Z",
  "model_version": "intraday_v1",
  "timezone": "UTC",
  "points": [
    {"t": "2026-01-30T09:00:00Z", "energy": 78},
    {"t": "2026-01-30T09:30:00Z", "energy": 80},
    {"t": "2026-01-30T10:00:00Z", "energy": 79},
    {"t": "2026-01-30T10:30:00Z", "energy": 77},
    {"t": "2026-01-30T11:00:00Z", "energy": 75},
    {"t": "2026-01-30T11:30:00Z", "energy": 74},
    {"t": "2026-01-30T12:00:00Z", "energy": 72},
    {"t": "2026-01-30T12:30:00Z", "energy": 70},
    {"t": "2026-01-30T13:00:00Z", "energy": 68},
    {"t": "2026-01-30T13:30:00Z", "energy": 66},
    {"t": "2026-01-30T14:00:00Z", "energy": 58},
    {"t": "2026-01-30T14:30:00Z", "energy": 56},
    {"t": "2026-01-30T15:00:00Z", "energy": 60},
    {"t": "2026-01-30T15:30:00Z", "energy": 62},
    {"t": "2026-01-30T16:00:00Z", "energy": 64},
    {"t": "2026-01-30T16:30:00Z", "energy": 66},
    {"t": "2026-01-30T17:00:00Z", "energy": 68},
    {"t": "2026-01-30T17:30:00Z", "energy": 65},
    {"t": "2026-01-30T18:00:00Z", "energy": 63},
    {"t": "2026-01-30T18:30:00Z", "energy": 60},
    {"t": "2026-01-30T19:00:00Z", "energy": 58}
  ],
  "windows": [
    {
      "from": "13:30",
      "to": "15:30",
      "kind": "dip",
      "label": "Creux important - éviter tâches complexes"
    }
  ],
  "events": [
    {
      "id": "evt_123",
      "start": "2026-01-30T14:00:00Z",
      "end": "2026-01-30T15:00:00Z",
      "title": "Réunion client importante",
      "impact": -12,
      "confidence": 0.75,
      "tags": ["meeting", "high_focus", "high_stress"]
    },
    {
      "id": "evt_456",
      "start": "2026-01-30T17:30:00Z",
      "end": "2026-01-30T18:30:00Z",
      "title": "Sport - Course",
      "impact": -8,
      "confidence": 0.80,
      "tags": ["sport", "physical"]
    }
  ],
  "notes": [
    "Creux attendu en fin d'après-midi",
    "Réunion à 14h pourrait être plus coûteuse que prévu",
    "Ta récupération est faible, ménage-toi"
  ],
  "confidence": 0.72
}
```

---

## Règles heuristiques V1 (détaillées)

### 1. Classification des événements

**Keywords par catégorie:**

| Type | Keywords | Tags |
|------|----------|------|
| **Meeting** | réunion, meeting, call, visio, conf, présentation, rdv | `meeting`, `moderate_focus` ou `high_focus` + `high_stress` si "client", "important", "stratégique" |
| **Sport** | sport, gym, course, running, yoga, fitness, training, entraînement | `sport`, `physical` |
| **Travel** | vol, flight, train, avion, déplacement, voyage, trajet | `travel`, `logistics` |
| **Focus** | focus, deep work, coding, dev, écriture, rédaction, projet | `focus`, `deep_work` |
| **Social** | dîner, déjeuner, lunch, dinner, apéro, café, social | `social`, `low_stress` |
| **Other** | (défaut) | `other` |

### 2. Impact des événements

**Formule:**
```python
impact = base_impact * duration_factor * tags_factor * user_state_factor
```

**Base impacts:**
- Meeting: -5
- Sport: -8
- Travel: -6
- Focus: -4
- Social: -2
- Other: -3

**Duration factor:**
- < 30 min: ×0.7
- 30-60 min: ×1.0
- 1-2h: ×1.2
- > 2h: ×1.5

**Tags factor:**
- `high_stress` ou `high_focus`: ×1.3
- `low_stress`: ×0.7

**User state factor:**
- `recovery < 0.5`: ×1.2
- `sleep_debt > 0.6`: ×1.15

**Cas spécial (Sport):**
- Impact négatif immédiat pendant l'événement
- Rebound positif +5 pendant 1h après la fin

### 3. Décroissance naturelle

**Time factor par heure:**
- 00h-12h (matin): ×1.0
- 12h-15h (début après-midi): ×0.95
- 15h-18h (fin après-midi): ×0.85
- 18h-21h (soirée): ×0.80
- 21h-00h (nuit): ×0.70

**Modulation selon états latents:**
- `sleep_debt > 0.6` → Creux plus tôt (time_factor ×0.90 après 14h)
- `recovery < 0.5` → Amplitude creux plus forte (time_factor ×0.92 après 15h)
- `overtrain > 0.7` → Énergie globalement réduite (time_factor ×0.95)

### 4. Détection des creux

**Critères:**
- Énergie < 70 pendant au moins 1h consécutive
- Label selon sévérité:
  - Énergie < 50: "Creux important - éviter tâches complexes"
  - Énergie < 60: "Creux modéré - privilégier tâches simples"
  - Énergie < 70: "Baisse d'énergie légère"

### 5. Génération des notes

**Priorité (max 3 notes):**
1. Énergie de base faible (< 60) ou excellente (> 80)
2. Creux prévu (si windows non vide)
3. Événement à risque (impact < -10)
4. Récupération faible (< 0.5)
5. Dette de sommeil élevée (> 0.6)

---

## Tests

### Backend: `test_intraday_energy.py`

**Couverture:**
- ✅ Classification des événements (meeting, sport, travel, focus, social, other)
- ✅ Estimation de l'impact (durée, tags, états utilisateur)
- ✅ Génération de la courbe (décroissance, modulation)
- ✅ Détection des creux (durée > 1h, sévérité)
- ✅ Génération des notes (max 3, priorité)
- ✅ Génération complète (intégration)

**Lancer les tests:**
```bash
cd backend
pytest tests/test_intraday_energy.py -v
```

---

## Déploiement

### 1. Appliquer la migration DB

```bash
# Via Supabase CLI
supabase db push

# Ou manuellement
psql $DATABASE_URL < database/migrations/030_intraday_energy_forecast.sql
```

### 2. Redémarrer le backend

```bash
cd backend
./restart_api_server.sh
```

### 3. Tester l'endpoint

```bash
curl -X GET "http://localhost:9000/api/energy/intraday?date=2026-01-30" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### 4. Rebuild mobile

```bash
cd mobile
npx expo start --clear
```

---

## Limitations et améliorations futures

### Limitations V1

1. **Pas de table `calendar_events`:** Pour l'instant, le service tente de récupérer les événements depuis une table `calendar_events` qui n'existe pas encore. Il faudra soit:
   - Créer cette table et la peupler via une intégration calendrier (Google Calendar, Apple Calendar)
   - Utiliser une API externe (ex: Expo Calendar)

2. **Timezone hardcodé:** Actuellement en UTC. Il faudra récupérer le timezone de l'utilisateur depuis son profil.

3. **Heuristiques simples:** Les impacts sont estimés avec des règles simples. Une V2 pourrait utiliser du ML pour apprendre les impacts réels.

4. **Pas de feedback utilisateur:** Impossible de savoir si les prédictions sont justes. Une V2 pourrait demander un feedback en fin de journée.

### Améliorations futures (V2)

1. **Intégration calendrier native:**
   - Sync automatique avec Google Calendar / Apple Calendar
   - Détection automatique du type d'événement via ML

2. **Apprentissage personnalisé:**
   - Apprendre les impacts réels des événements pour chaque utilisateur
   - Adapter les heuristiques selon le chronotype

3. **Prédiction dynamique:**
   - Recalculer la courbe en temps réel si un événement est ajouté/modifié
   - Push notification si un creux est détecté pendant un événement important

4. **Suggestions proactives:**
   - "Décale ta réunion de 16h à 11h pour éviter le creux"
   - "Prends une pause de 15 min avant ta réunion importante"

5. **Feedback loop:**
   - Demander en fin de journée: "Comment était ton énergie à 16h?"
   - Utiliser les réponses pour améliorer les prédictions

---

## Fichiers créés/modifiés

### Backend
- ✅ `database/migrations/030_intraday_energy_forecast.sql` (nouveau)
- ✅ `backend/intraday_energy_service.py` (nouveau)
- ✅ `backend/api_server.py` (modifié: ajout endpoint `/api/energy/intraday`)
- ✅ `backend/services/ai_service.py` (modifié: intégration dans `/api/brief`)
- ✅ `backend/tests/test_intraday_energy.py` (nouveau)

### Mobile
- ✅ `mobile/src/components/IntradayEnergyCurveCard.tsx` (nouveau)
- ✅ `mobile/src/components/BriefStack.tsx` (modifié: ajout card intraday)
- ✅ `mobile/app/(tabs)/index.tsx` (modifié: passage prop `intradayForecast`)

### Documentation
- ✅ `INTRADAY_ENERGY_FEATURE.md` (ce fichier)

---

## Résumé

Cette feature ajoute une **courbe d'énergie prédictive intraday** dans l'écran Brief de Pulse, permettant aux utilisateurs de visualiser leur énergie prévue pour le reste de la journée, avec les événements du calendrier et les creux d'énergie.

**Valeur ajoutée:**
- ✅ Vision claire de l'évolution de l'énergie dans la journée
- ✅ Identification des moments critiques (creux)
- ✅ Aide à la planification des tâches selon l'énergie prévue
- ✅ Intégration transparente dans le Brief existant

**Architecture:**
- ✅ Backend: Service Python avec heuristiques V1 simples et explicables
- ✅ Mobile: Composant React Native avec courbe SVG et interactions
- ✅ Tests: Couverture complète des fonctions critiques
- ✅ Documentation: Structure JSON + règles heuristiques détaillées

**Prêt pour production:** Oui, avec les limitations V1 mentionnées ci-dessus.
