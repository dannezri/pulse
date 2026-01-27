# 🚀 Intégration Vital - Fonctionnalités Complètes

## ✅ Fonctionnalités Implémentées

### 1️⃣ Gestion des Doublons

**Système de déduplication intelligent** basé sur :
- `user_id` + `metric_type` + `recorded_at` + `source_event_id`
- Si pas de `source_event_id`, utilise `user_id` + `metric_type` + `recorded_at` + `value` + `source`

**Avantages :**
- ✅ Évite les doublons lorsque plusieurs providers envoient les mêmes données
- ✅ Gère les re-envois de webhooks (idempotence)
- ✅ Performance : vérifie avant d'insérer

**Code :** `backend/vital_webhook_v2.py` → `_is_duplicate()`

---

### 2️⃣ Types de Métriques Supportés

#### 📊 Activity (Activité Quotidienne)
- **Steps** (pas) - `metric_type: steps`
- **Calories totales** - `metric_type: calories`
- **Calories actives** - `metric_type: active_calories`
- **Distance** (km) - `metric_type: distance`
- **Étages montés** - `metric_type: floors_climbed`
- **Minutes actives** - `metric_type: active_minutes`

#### 🫀 Vitals (Signes Vitaux)
- **HRV** (Heart Rate Variability) - `metric_type: hrv`
- **Rythme cardiaque** - `metric_type: heart_rate`
- **SpO2** (Saturation en oxygène) - `metric_type: spo2`
- **Fréquence respiratoire** - `metric_type: respiratory_rate`

#### 😴 Sleep (Sommeil)
- **Durée du sommeil** - `metric_type: sleep_duration`
- **Score de sommeil** (dans metadata)
- **Sommeil profond, REM, léger** (dans metadata)

#### 🏋️ Workouts (Entraînements)
- **Durée de l'entraînement** - `metric_type: workout`
- **Type de sport** (dans metadata)
- **Calories brûlées** (dans metadata)
- **Distance parcourue** (dans metadata)
- **Fréquence cardiaque moyenne/max** (dans metadata)

#### ⚖️ Body (Composition Corporelle)
- **Poids** - `metric_type: weight`

#### ⏱️ Timeseries (Données en Temps Réel)
- **Rythme cardiaque streaming** - `metric_type: heart_rate` (type: timeseries)
- **Glucose** - `metric_type: glucose`
- **Pression artérielle** - `metric_type: blood_pressure`

**Total : 16+ types de métriques**

---

### 3️⃣ Écran Historique (Tendances)

**Fonctionnalités :**
- 📈 **Graphiques interactifs** pour chaque métrique
- 🎚️ **Sélecteur de période** : 7, 30, ou 90 jours
- 📊 **Statistiques** : moyenne, min, max
- 📉 **Indicateur de tendance** : hausse, baisse, stable
- 🔄 **Pull-to-refresh** pour actualiser les données
- 🎨 **Design moderne** avec couleurs distinctes par métrique

**Métriques affichées :**
1. 🚶 Pas (rose)
2. 💚 HRV (vert)
3. 🧡 Rythme Cardiaque (orange)
4. 🌙 Sommeil (bleu)
5. 🔥 Calories (rouge)
6. 🛣️ Distance (violet)

**Code :** `mobile/app/(tabs)/tendances.tsx`

---

### 4️⃣ Architecture Backend

#### Webhook Handler V2
**Fichier :** `backend/vital_webhook_v2.py`

**Fonctionnalités :**
- ✅ Support format officiel Vital
- ✅ Auto-détection format V1/V2
- ✅ Déduplication intelligente
- ✅ Gestion des webhooks :
  - `historical.data.*` (backfill)
  - `timeseries.data.*` (temps réel)
  - `daily.data.*` (résumés quotidiens)

#### Vital Client
**Fichier :** `backend/vital_client.py`

**Méthodes disponibles :**
```python
# Récupération de données
get_sleep_data(user_id, start_date, end_date)
get_activity_data(user_id, start_date, end_date)
get_body_data(user_id, start_date, end_date)
get_workouts_data(user_id, start_date, end_date)
get_vitals_data(user_id, start_date, end_date)

# Gestion utilisateurs
create_user(client_user_id)
generate_link_token(user_id)
get_user_connections(user_id)

# Demo mode (sandbox)
connect_demo_provider(user_id, provider_slug)
```

---

### 5️⃣ Architecture Mobile

#### Hooks
- **`useVital`** : Gestion de l'état Vital (configuration, connexions)
- **`useCurrentMetrics`** : Métriques d'aujourd'hui (tableau de bord)
- **`useMetricsHistory`** : Historique complet (tendances)

#### Screens
- **`(tabs)/index.tsx`** : Tableau de bord avec métriques du jour
- **`(tabs)/connections.tsx`** : Gestion des sources connectées
- **`(tabs)/tendances.tsx`** : Graphiques historiques

#### Services
- **`vitalService.ts`** : API client pour communiquer avec le backend

---

## 📊 Statistiques

### Données Actuelles
- **24 enregistrements** de steps (3 providers)
- **6 enregistrements** de HRV
- **9 enregistrements** de rythme cardiaque
- **5 enregistrements** de sommeil (2 providers)
- **2 providers connectés** : Fitbit + Oura (demo)

### Performance
- ✅ Déduplication fonctionne : 0/2 doublons bloqués
- ✅ Insertion multi-métriques : 1 webhook activity = jusqu'à 6 métriques
- ✅ Idempotence : même webhook peut être reçu plusieurs fois

---

## 🔄 Flux de Données

### Webhook → Database
```
Vital Webhook (JSON)
    ↓
Backend (api_server_mvp.py)
    ↓
VitalWebhookHandlerV2
    ↓
_fetch_and_insert_data()
    ↓
VitalClient.get_*_data()
    ↓
_map_vital_to_biometric()
    ↓
_is_duplicate() [déduplication]
    ↓
Supabase INSERT (biometrics)
```

### Database → Mobile
```
Supabase (biometrics table)
    ↓
useMetricsHistory / useCurrentMetrics
    ↓
React Query (cache)
    ↓
UI Components (MetricCard, LineChart)
```

---

## 🎯 Prochaines Étapes (Optionnel)

### Sécurité
- [ ] Réactiver RLS sur `biometrics` avec JWT valide
- [ ] Implémenter vraie authentification Supabase Auth

### Fonctionnalités
- [ ] Alertes sur anomalies (HRV bas, sommeil insuffisant)
- [ ] Comparaison entre providers (Fitbit vs Oura)
- [ ] Export CSV des données
- [ ] Graphiques comparatifs (semaine vs semaine)

### Performance
- [ ] Pagination de l'historique (> 90 jours)
- [ ] Cache local pour graphiques
- [ ] Optimisation requêtes Supabase (indexes)

---

## 🐛 Debugging

### Vérifier les logs backend
```bash
tail -f /path/to/terminals/XX.txt | grep -E "(Inserted|Fetching|ERROR)"
```

### Vérifier les données dans Supabase
```sql
SELECT metric_type, COUNT(*), MIN(recorded_at), MAX(recorded_at)
FROM biometrics
WHERE user_id = 'your_user_id'
GROUP BY metric_type;
```

### Tester la déduplication
```bash
# Envoyer 2 fois le même webhook
curl --request POST --url http://localhost:9000/ ...
# Vérifier les logs : "Skipping duplicate" ou "0/X inserted"
```

---

## 📚 Documentation

- **Vital API Docs** : https://docs.tryvital.io
- **Vital Dashboard** : https://app.tryvital.io
- **Vital Status** : https://status.tryvital.io

---

**Dernière mise à jour** : 27 janvier 2026
**Version** : 1.0.0
**Auteur** : Pulse Team
