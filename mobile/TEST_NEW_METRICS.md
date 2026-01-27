# 🧪 Guide de Test - Nouveaux Types de Métriques

## ✅ Modifications Effectuées

### Backend
- ✅ **52+ types** supportés via `vital_timeseries_types.py`
- ✅ Mapping universel automatique
- ✅ Déduplication pour tous les types

### Mobile
- ✅ **26 types** affichés dans l'interface
- ✅ Écran Tendances : 23 graphiques
- ✅ Écran Aujourd'hui : cartes dynamiques (affichées uniquement si données présentes)
- ✅ Hooks mis à jour : `useCurrentMetrics` + `useMetricsHistory`

---

## 📊 Types Affichés dans l'App

### Écran "Aujourd'hui" (Dashboard)
**Toujours affichées :**
- 🌙 Sommeil
- 💚 HRV
- 🧡 Rythme Cardiaque
- 🚶 Pas

**Affichées si données présentes :**
- 💧 Eau (hydratation)
- 🔥 Calories
- 🫁 SpO2 (oxygène)
- 💜 Glycémie
- ⚖️ Poids
- 🧠 Stress
- ☕ Caféine

### Écran "Tendances" (Graphiques Historiques)
**23 graphiques disponibles :**

#### Activity (6)
- Pas, Distance, Calories totales, Calories actives, Étages montés, VO2 Max

#### Vitals (6)
- HRV, Rythme cardiaque, SpO2, Pression artérielle, Glycémie, Fréquence respiratoire

#### Body (4)
- Poids, Masse grasse, IMC, Température corporelle

#### Sleep (1)
- Durée du sommeil

#### Wellness (2)
- Stress, Méditation

#### Nutrition (3)
- Eau, Caféine, Glucides

---

## 🧪 Scripts de Test

### 1. Test Glycémie (Glucose)

```bash
curl --request POST \
  --url http://192.168.0.23:9000/ \
  --header 'Content-Type: application/json' \
  --data '{
    "event_type": "timeseries.data.glucose.created",
    "user_id": "6306b303-069b-48b6-a257-c6324161a7c8",
    "client_user_id": "006b5096-1983-44ae-9fc5-a8431c9f40be",
    "team_id": "544014f4-69f7-480a-8670-a50542c6b135",
    "data": {
      "provider": "freestyle",
      "data": [
        {"timestamp": "2026-01-27T08:00:00Z", "value": 92, "unit": "mg/dL", "id": "glucose_1"},
        {"timestamp": "2026-01-27T12:00:00Z", "value": 105, "unit": "mg/dL", "id": "glucose_2"},
        {"timestamp": "2026-01-27T16:00:00Z", "value": 88, "unit": "mg/dL", "id": "glucose_3"}
      ]
    }
  }'
```

**Résultat attendu :**
- ✅ 3 points insérés dans `biometrics`
- ✅ Carte "Glycémie" visible sur écran Aujourd'hui
- ✅ Graphique "Glycémie" dans Tendances

---

### 2. Test Hydratation (Water)

```bash
curl --request POST \
  --url http://192.168.0.23:9000/ \
  --header 'Content-Type: application/json' \
  --data '{
    "event_type": "timeseries.data.water.created",
    "user_id": "6306b303-069b-48b6-a257-c6324161a7c8",
    "client_user_id": "006b5096-1983-44ae-9fc5-a8431c9f40be",
    "team_id": "544014f4-69f7-480a-8670-a50542c6b135",
    "data": {
      "provider": "apple_health",
      "data": [
        {"timestamp": "2026-01-27T08:00:00Z", "value": 250, "id": "water_1"},
        {"timestamp": "2026-01-27T12:00:00Z", "value": 500, "id": "water_2"},
        {"timestamp": "2026-01-27T18:00:00Z", "value": 300, "id": "water_3"}
      ]
    }
  }'
```

**Résultat attendu :**
- ✅ 3 points d'hydratation
- ✅ Total aujourd'hui : 1050 mL
- ✅ Carte "Eau" visible

---

### 3. Test Stress (Garmin)

```bash
curl --request POST \
  --url http://192.168.0.23:9000/ \
  --header 'Content-Type: application/json' \
  --data '{
    "event_type": "timeseries.data.stress_level.created",
    "user_id": "6306b303-069b-48b6-a257-c6324161a7c8",
    "client_user_id": "006b5096-1983-44ae-9fc5-a8431c9f40be",
    "team_id": "544014f4-69f7-480a-8670-a50542c6b135",
    "data": {
      "provider": "garmin",
      "data": [
        {"timestamp": "2026-01-27T09:00:00Z", "value": 35, "id": "stress_1"},
        {"timestamp": "2026-01-27T14:00:00Z", "value": 65, "id": "stress_2"},
        {"timestamp": "2026-01-27T20:00:00Z", "value": 25, "id": "stress_3"}
      ]
    }
  }'
```

**Résultat attendu :**
- ✅ 3 mesures de stress
- ✅ Graphique "Stress" dans Tendances
- ✅ Carte "Stress" si valeur > 0

---

### 4. Test Poids (Weight)

```bash
curl --request POST \
  --url http://192.168.0.23:9000/ \
  --header 'Content-Type: application/json' \
  --data '{
    "event_type": "timeseries.data.weight.created",
    "user_id": "6306b303-069b-48b6-a257-c6324161a7c8",
    "client_user_id": "006b5096-1983-44ae-9fc5-a8431c9f40be",
    "team_id": "544014f4-69f7-480a-8670-a50542c6b135",
    "data": {
      "provider": "withings",
      "data": [
        {"timestamp": "2026-01-20T07:00:00Z", "value": 75.2, "id": "weight_1"},
        {"timestamp": "2026-01-22T07:00:00Z", "value": 74.8, "id": "weight_2"},
        {"timestamp": "2026-01-24T07:00:00Z", "value": 75.0, "id": "weight_3"},
        {"timestamp": "2026-01-27T07:00:00Z", "value": 74.5, "id": "weight_4"}
      ]
    }
  }'
```

**Résultat attendu :**
- ✅ 4 mesures de poids
- ✅ Graphique dans Tendances avec tendance (↘️ baisse)
- ✅ Carte "Poids" : 74.5 kg

---

### 5. Test SpO2 (Saturation Oxygène)

```bash
curl --request POST \
  --url http://192.168.0.23:9000/ \
  --header 'Content-Type: application/json' \
  --data '{
    "event_type": "timeseries.data.blood_oxygen.created",
    "user_id": "6306b303-069b-48b6-a257-c6324161a7c8",
    "client_user_id": "006b5096-1983-44ae-9fc5-a8431c9f40be",
    "team_id": "544014f4-69f7-480a-8670-a50542c6b135",
    "data": {
      "provider": "apple_health",
      "data": [
        {"timestamp": "2026-01-27T22:00:00Z", "value": 97, "id": "spo2_1"},
        {"timestamp": "2026-01-27T23:00:00Z", "value": 96, "id": "spo2_2"}
      ]
    }
  }'
```

**Résultat attendu :**
- ✅ 2 mesures SpO2
- ✅ Carte "SpO2" : 96%

---

### 6. Test Caféine

```bash
curl --request POST \
  --url http://192.168.0.23:9000/ \
  --header 'Content-Type: application/json' \
  --data '{
    "event_type": "timeseries.data.caffeine.created",
    "user_id": "6306b303-069b-48b6-a257-c6324161a7c8",
    "client_user_id": "006b5096-1983-44ae-9fc5-a8431c9f40be",
    "team_id": "544014f4-69f7-480a-8670-a50542c6b135",
    "data": {
      "provider": "apple_health",
      "data": [
        {"timestamp": "2026-01-27T08:00:00Z", "value": 95, "id": "caffeine_1"},
        {"timestamp": "2026-01-27T14:00:00Z", "value": 80, "id": "caffeine_2"}
      ]
    }
  }'
```

**Résultat attendu :**
- ✅ 2 mesures de caféine
- ✅ Total : 175 mg
- ✅ Carte "Caféine" visible

---

## 🔍 Vérification dans la Base de Données

```sql
-- Voir tous les types de métriques par utilisateur
SELECT 
  metric_type,
  COUNT(*) as count,
  MIN(recorded_at) as first,
  MAX(recorded_at) as last,
  metadata->>'unit' as unit,
  metadata->>'category' as category
FROM biometrics
WHERE user_id = '006b5096-1983-44ae-9fc5-a8431c9f40be'
GROUP BY metric_type, metadata->>'unit', metadata->>'category'
ORDER BY category, metric_type;
```

---

## 📱 Test dans l'App Mobile

### 1. Écran "Aujourd'hui"
1. **Ouvrir l'app**
2. **Pull-to-refresh** (glisser vers le bas)
3. **Vérifier** :
   - Cartes de base : Sommeil, HRV, HR, Pas
   - Nouvelles cartes (si données) : Eau, Glucose, SpO2, Poids, Stress, Caféine

### 2. Écran "Tendances"
1. **Aller dans l'onglet Tendances**
2. **Sélectionner période** : 7J, 30J, 90J
3. **Scroll vers le bas**
4. **Vérifier** :
   - Graphiques pour chaque type avec données
   - Statistiques : Moyenne, Min/Max
   - Indicateur de tendance (↗️↘️➖)

### 3. Écran "Sources"
1. **Aller dans l'onglet Sources**
2. **Vérifier** :
   - Nombre de sources connectées
   - Fitbit, Oura affichés

---

## ✅ Checklist Complète

- [ ] Backend redémarré avec nouveaux types
- [ ] Test glucose → données insérées
- [ ] Test water → carte visible
- [ ] Test stress → graphique affiché
- [ ] Test weight → tendance calculée
- [ ] Test SpO2 → pourcentage affiché
- [ ] Test caféine → valeur cumulée
- [ ] App rechargée (`r` dans Expo)
- [ ] Écran Aujourd'hui affiche nouvelles cartes
- [ ] Écran Tendances affiche 10+ graphiques
- [ ] Pull-to-refresh fonctionne
- [ ] Sélecteur de période fonctionne (7J/30J/90J)

---

**Date** : 27 janvier 2026  
**Version** : 2.1.0  
**Status** : ✅ Ready to Test
