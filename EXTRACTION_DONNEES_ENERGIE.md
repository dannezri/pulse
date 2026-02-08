# Extraction des Données de la Page Énergie

## 📊 Résumé de l'Extraction

**Date:** 3 février 2026, 21:15
**Utilisateur:** 966bee23-35a8-4235-8cde-d7479aa94f94 (Le Burnout imminent)
**Fichier de sortie:** `energy_data_export_20260203_211543.json` (32 KB, 1016 lignes)

---

## 🔍 Données Extraites

### 1. Brief Quotidien (API `/api/v1/generate-brief`)

Le brief contient **l'analyse complète de la journée** générée par le Wellness Coach IA :

#### 📈 Pulse Score: **35%** (État: Alert)
- **Statut:** Conflit métabolique détecté
- **Cache:** Données fraîches (force_refresh)
- **Timestamp:** 2026-02-03T20:15:42

#### 🎴 Cartes Brief (5)

1. **Le bilan du coach** (Verdict)
   - État: Alert
   - Pulse Score: 35%
   - Problème: HRV bas (42 ms vs baseline 65 ms), absence de repas, faible activité

2. **Votre météo intérieure** (Focus)
   - État: Alert  
   - Alerte sur substrat énergétique critique (glycogène bas)
   - Prévision: fatigue accrue, baisse concentration

3. **Le petit pas du jour** (Activity)
   - État: Optimal
   - Action: Nutrition immédiate (30g protéines + 50g glucides)
   - Objectif: 5000 pas minimum

4. **Votre corps en veille** (Activity)
   - État: Alert
   - Problème: Seulement 2000 pas aujourd'hui
   - Action: 3000 pas supplémentaires

5. **Carburant manquant** (Focus)
   - État: Alert
   - Problème: Aucun repas enregistré (0 kcal)
   - Action: Préparer repas équilibré

#### ⚡ Prévision Énergétique Intraday

**Courbe d'énergie prédictive** (48 points de 30 minutes):
- Type: `intraday_energy`
- Version modèle: `intraday_v1`
- Timezone: UTC
- Points: 48 valeurs de 7h00 à 23h00

**Exemple de points:**
```json
[
  {"t": "2026-02-03T07:00:00+01:00", "energy": 47},
  {"t": "2026-02-03T07:30:00+01:00", "energy": 47},
  {"t": "2026-02-03T08:00:00+01:00", "energy": 47},
  ...
]
```

**Influenceurs détectés** (1):
- Sommeil: Impact significatif sur l'énergie
- Notes: 1 note explicative sur le système

#### 💰 Utilisation IA
- Tokens prompt: 4826
- Tokens complétion: 705
- Total: 5531 tokens (GPT-4o)

---

### 2. Données Biométriques (Table `biometrics`)

**Total:** 25 enregistrements des 7 derniers jours

**Répartition par type:**
- **HRV** (Heart Rate Variability): 8 valeurs
- **HR** (Heart Rate): 8 valeurs
- **Steps** (Pas): 1 valeur
- **Sleep Duration**: 8 valeurs

**Format des données:**
```json
{
  "metric_type": "hrv",
  "value": 42.0,
  "recorded_at": "2026-01-25T21:37:06+00:00",
  "source": "oura",
  "raw_data": { ... }
}
```

---

### 3. Médicaments (Table `user_medications`)

**Statut:** ⚠️ Table existe mais colonne `active` devrait être `is_active`

**Données attendues:**
- Médicaments actifs de l'utilisateur
- Schedules de prise
- Impacts énergétiques

**Action nécessaire:** Corriger le schéma ou adapter la requête

---

### 4. Conditions de Santé (Table `user_conditions`)

**Statut:** ⚠️ Table existe mais structure non standard

**Données attendues:**
- Conditions de santé actives
- Codes ICD-11
- Impacts sur l'énergie

---

### 5. Feedbacks Utilisateur (Table `user_feedback`)

**Total:** 0 feedbacks

L'utilisateur n'a pas encore soumis de feedback sur ses prédictions d'énergie.

**Format attendu:**
```json
{
  "feedback_type": "energy_accuracy",
  "rating": 1-5,
  "comment": "...",
  "created_at": "..."
}
```

---

### 6. Profil Énergétique Personnalisé

**Statut:** ⚠️ Table `user_energy_profiles` n'existe pas

**Attendu:** Poids ML personnalisés par utilisateur pour améliorer les prédictions

---

## 📦 Structure du Fichier JSON Exporté

```json
{
  "user_id": "UUID",
  "extracted_at": "ISO8601",
  "brief": {
    "cards": [...],
    "pulseScore": 35,
    "intraday_energy_forecast": {
      "points": [...],
      "influencers": [...],
      "notes": [...]
    }
  },
  "biometrics": {
    "all": [...],
    "by_type": {
      "hrv": [...],
      "hr": [...],
      "steps": [...],
      "sleep_duration": [...]
    }
  },
  "medications": [],
  "conditions": [],
  "feedbacks": [],
  "energy_profile": null
}
```

---

## 🛠️ Script d'Extraction

**Fichier:** `backend/extract_energy_data.py`

**Fonctionnalités:**
- ✅ Récupération user_id depuis la table `profiles`
- ✅ Appel API `/api/v1/generate-brief` avec `force_refresh=true`
- ✅ Récupération biométriques (200 derniers enregistrements)
- ✅ Récupération médicaments (avec gestion d'erreur)
- ✅ Récupération conditions (avec gestion d'erreur)
- ✅ Récupération feedbacks (20 derniers)
- ✅ Récupération profil énergétique (avec gestion d'erreur)
- ✅ Export JSON formaté avec timestamp

**Usage:**
```bash
cd backend
python3 extract_energy_data.py
```

---

## 🎯 Données Clés pour la Page Énergie

### Affichage Principal

1. **Score Actuel:** 35% (tiré de `brief.pulseScore`)
2. **État:** Alert (tiré de `brief.cards[0].state`)
3. **Courbe Prédictive:** 48 points sur la journée (tiré de `brief.intraday_energy_forecast.points`)

### Facteurs d'Influence

**Positifs:** _(aucun dans l'export actuel)_

**Négatifs:**
- Sommeil de qualité insuffisante
- HRV bas (42 ms vs 65 ms baseline)
- Absence de nutrition (0 kcal)
- Activité faible (2000 pas)

### Balance Énergétique

- **Facteurs positifs:** 0
- **Facteurs négatifs:** 1 influenceur explicite
- **Impact total négatif:** Significatif (Pulse Score à 35%)

### Notes Explicatives

1. Le système nerveux est perturbé par l'absence de repas et la faible activité

### Mode Debug

- **Type modèle:** intraday_energy
- **Version:** intraday_v1
- **Date génération:** 2026-02-03T20:15:04
- **Timezone:** UTC
- **Points de données:** 48

---

## 🔧 Améliorations Possibles

### Schéma Base de Données

1. **user_medications:** Renommer `active` → `is_active`
2. **user_conditions:** Standardiser la colonne d'état
3. **user_energy_profiles:** Créer la table pour les poids ML personnalisés

### Données Manquantes

1. **Health Connect (Android):** Pas encore implémenté
2. **Feedbacks:** Système de collecte à activer
3. **Profils personnalisés:** Système ML à finaliser

### API

1. **Cache intelligent:** Actuellement désactivé (`force_refresh=true`)
2. **Metadata enrichie:** Ajouter plus de contexte sur les calculs
3. **Historique:** Sauvegarder les prédictions passées pour comparaison

---

## 📞 Contact & Support

**Script créé le:** 2026-02-03
**Dernier run:** 2026-02-03 21:15:43
**Fichier de sortie:** `/Users/dannezri/Desktop/Pulse/energy_data_export_20260203_211543.json`

Pour réexécuter l'extraction:
```bash
cd /Users/dannezri/Desktop/Pulse/backend
python3 extract_energy_data.py
```

---

## 🎓 Documentation Liée

- `mobile/app/energy-analysis.tsx` - Code React Native de la page
- `mobile/src/hooks/useBriefData.ts` - Hook de récupération des données
- `mobile/src/services/briefApi.ts` - Service API
- `backend/intraday_energy_service.py` - Service de prédiction
- `backend/api_server.py` - Endpoint `/api/v1/generate-brief`
