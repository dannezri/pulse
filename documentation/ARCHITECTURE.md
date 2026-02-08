# Architecture Globale du Projet Pulse

## 📋 Vue d'Ensemble

**Pulse** est une plateforme de bio-feedback IA qui collecte et analyse les données biométriques et de contexte pour générer des insights personnalisés en temps réel.

**Nouveau MVP** :
- **Données de Flux** : Oura API (HR, HRV, Sleep) via webhook vers backend
- **Données de Contexte** : Apple Health (Nutrition, Médicaments, Symptômes, Selles) scannées localement sur iOS puis envoyées au backend
- **Insight** : Corrélation "contexte récent" vs "biométrie récente" via LLM (GPT-4o)

Le projet se compose de trois systèmes principaux :
1. **Backend Pulse** : API FastAPI pour webhooks, corrélation et génération d'insights
2. **Mobile (Expo)** : Application React Native pour scanner le contexte Apple Health
3. **Base de données Supabase** : Stockage des données utilisateur (biometrics, daily_context, insights)

---

## 🏗️ Architecture Générale

```
┌─────────────────────────────────────────────────────────────────┐
│                    MOBILE (Expo SDK 54)                          │
│  - Scan contexte Apple Health (Nutrition, Médicaments, etc.)   │
│  - Affichage insights                                           │
└────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      COUCHE API / SERVICES                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Backend Pulse (FastAPI)                                 │  │
│  │  - POST /api/webhooks/oura (HR, HRV, Sleep)             │  │
│  │  - POST /api/cron/daily-insight (génération quotidienne) │  │
│  │  - GET /api/insights/latest (pour mobile)                │  │
│  │  - Correlation Engine (biometrics + daily_context)       │  │
│  │  - LLM Client (GPT-4o)                                   │  │
│  └────────┬─────────────────────────────────────────────────┘  │
└───────────┼─────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      COUCHE DONNÉES                              │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │              Supabase (PostgreSQL)                       │    │
│  │  - profiles          - biometrics (HR, HRV, Sleep)       │    │
│  │  - daily_context     - insights                         │    │
│  │  - meals (legacy)    - auth.users                       │    │
│  └──────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SOURCES DE DONNÉES                             │
│  Oura API (webhook) │ Apple Health (scan local iOS)             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Composants Principaux

### 1. Backend Pulse (`/backend`)

**Rôle** : Réception des données, corrélation et génération d'insights

**Composants** :

- **`api_server.py`** : API FastAPI
  - `POST /api/webhooks/oura` : Reçoit les données Oura API (HR, HRV, Sleep)
  - `POST /api/cron/daily-insight` : Génération quotidienne d'insights (protégé par secret)
  - `GET /api/insights/latest` : Récupère le dernier insight pour le mobile

- **`correlation_engine.py`** : Moteur de corrélation simple
  - Récupère les 10 derniers `biometrics` et 10 derniers `daily_context`
  - Construit un prompt pour le LLM
  - Génère un insight corrélé

- **`llm_client.py`** : Client LLM (GPT-4o)
  - Abstraction pour appeler OpenAI
  - Gère les prompts système/utilisateur
  - Retourne JSON structuré

- **`supabase_client.py`** : Client Supabase
  - Insertion des `biometrics` (depuis webhook Oura)
  - Insertion des `daily_context` (depuis mobile)
  - Insertion des `insights` (générés par correlation_engine)

**Flux de traitement** :
```
Oura API (webhook)
    ↓
POST /api/webhooks/oura
    ↓
Insert dans biometrics (HR, HRV, Sleep)
    ↓
[Quotidien] POST /api/cron/daily-insight
    ↓
Correlation Engine (biometrics récents + daily_context récents)
    ↓
LLM (GPT-4o) → Insight
    ↓
Insert dans insights
    ↓
Mobile récupère via GET /api/insights/latest
```

---

### 2. Mobile (`/mobile`)

**Rôle** : Scanner le contexte Apple Health et afficher les insights

**Architecture** :
- **Expo SDK 54** : Framework React Native
- **Expo Router** : Routing basé sur le système de fichiers
- **Module natif** : `pulse-healthkit` (Swift) pour accéder à HealthKit

**Composants** :

- **`src/services/HealthScanner.ts`** : Service de synchronisation du contexte
  - Scanne les 6 dernières heures depuis Apple Health
  - Catégories : Nutrition (calories, carbs), Médicaments, Symptômes, Selles
  - Envoie vers Supabase table `daily_context` (source 'AppleHealth')
  - Affiche notification de succès

- **`src/modules/pulseHealthkit/`** : Wrapper JS pour le module natif
  - `readNutrition()` : Calories et glucides
  - `readMedications()` : Médicaments (si accessible)
  - `readSymptoms()` : Symptômes (si accessible)
  - `readStool()` : Selles (si accessible)

- **`pulse-healthkit/ios/`** : Module natif Swift
  - Accès HealthKit (lecture uniquement)
  - Gestion des permissions
  - Lecture des données de contexte

- **`app/(tabs)/index.tsx`** : Dashboard principal
  - Bouton "Synchroniser Contexte" (iOS uniquement)
  - Affichage des insights
  - Métriques de santé (HRV, Sleep, HR)

**Flux de synchronisation** :
```
Utilisateur clique "Synchroniser Contexte"
    ↓
HealthScanner.syncLast6Hours()
    ↓
pulse-healthkit (Swift) → HealthKit
    ↓
Transforme en entrées daily_context
    ↓
POST vers Supabase (table daily_context)
    ↓
Notification : "Contexte synchronisé. Pulse analyse vos données…"
```

---

### 3. Base de Données Supabase (`/database`)

**Rôle** : Stockage centralisé des données utilisateur

**Tables principales** :

#### `profiles`
- Informations utilisateur et réglages
- Objectifs santé (`health_goal`)
- Lien avec `auth.users`

#### `biometrics`
- Données de flux (HR, HRV, Sleep) depuis Oura API
- Colonnes : `user_id`, `metric_type`, `value`, `measured_at`, `source`, `metadata` (JSONB)
- Index : `(user_id, measured_at DESC)`, `(user_id, metric_type, measured_at DESC)`

#### `daily_context`
- Données de contexte (Nutrition, Médicaments, Symptômes, Selles) depuis Apple Health
- Colonnes : `user_id`, `category`, `details` (JSONB), `logged_at`, `source`
- Index : `(user_id, logged_at DESC)`, `(user_id, category, logged_at DESC)`

#### `insights`
- Insights générés par corrélation
- Colonnes : `user_id`, `content`, `correlation_type`, `priority`, `created_at`
- Index : `(user_id, created_at DESC)`

**Sécurité** :
- Row Level Security (RLS) activé sur toutes les tables
- Utilisateurs ne voient que leurs propres données
- Service role pour insertions via webhooks/mobile

**Fonctions RPC** :
- `get_recent_biometrics(user_id, limit)` : Récupère les N derniers biometrics
- `get_recent_daily_context(user_id, limit)` : Récupère les N derniers daily_context
- `get_latest_insight(user_id)` : Récupère le dernier insight

---

## 🔄 Flux de Données

### Flux Principal : Génération d'Insight Quotidien

```
1. Oura API envoie webhook (HR, HRV, Sleep)
   POST /api/webhooks/oura
   ↓
2. Backend insère dans biometrics
   ↓
3. [Quotidien] Cron externe appelle
   POST /api/cron/daily-insight (avec secret)
   ↓
4. Correlation Engine :
   - Récupère 10 derniers biometrics
   - Récupère 10 derniers daily_context
   - Construit prompt pour LLM
   ↓
5. LLM (GPT-4o) génère insight
   ↓
6. Backend insère dans insights
   ↓
7. Mobile récupère via GET /api/insights/latest
```

### Flux Mobile : Synchronisation du Contexte

```
1. Utilisateur clique "Synchroniser Contexte" (iOS)
   ↓
2. HealthScanner.syncLast6Hours()
   ↓
3. Module natif pulse-healthkit lit HealthKit :
   - Nutrition (calories, carbs)
   - Médicaments (si accessible)
   - Symptômes (si accessible)
   - Selles (si accessible)
   ↓
4. Transforme en entrées daily_context
   ↓
5. POST vers Supabase (table daily_context)
   ↓
6. Notification : "Contexte synchronisé. Pulse analyse vos données…"
```

---

## 🛠️ Technologies Utilisées

### Backend Pulse
- **Python 3.11+**
- **FastAPI** : Framework API REST
- **Supabase Python Client** : Client pour base de données
- **OpenAI** : Client LLM (GPT-4o)
- **Python-dotenv** : Gestion des variables d'environnement

### Mobile
- **Expo SDK 54** : Framework React Native
- **Expo Router 6** : Routing basé sur le système de fichiers
- **React 19.1.0** : Bibliothèque UI
- **React Native 0.81.5** : Framework mobile
- **TypeScript** : Langage de programmation
- **pulse-healthkit** : Module Expo natif (Swift) pour HealthKit

### Infrastructure
- **Supabase** : Backend-as-a-Service
  - PostgreSQL (base de données)
  - Auth (authentification)
  - Row Level Security (sécurité)

---

## 📁 Structure du Projet

```
Pulse/
├── backend/                          # Backend Pulse
│   ├── api_server.py                 # API FastAPI
│   ├── correlation_engine.py         # Moteur de corrélation
│   ├── llm_client.py                 # Client LLM (GPT-4o)
│   ├── supabase_client.py            # Client Supabase
│   ├── requirements.txt              # Dépendances Python
│   └── config.example.env            # Template config
│
├── database/                         # Schémas et migrations
│   ├── schema.sql                    # Schéma complet
│   └── migrations/                   # Migrations versionnées
│       ├── 001_initial_schema.sql
│       ├── ...
│       └── 009_mvp_context_and_insights.sql  # Nouveau MVP
│
├── mobile/                           # Application mobile (Expo)
│   ├── app/                          # Routes Expo Router
│   │   └── (tabs)/
│   │       └── index.tsx             # Dashboard principal
│   ├── src/
│   │   ├── services/
│   │   │   └── HealthScanner.ts     # Service de synchronisation contexte
│   │   ├── modules/
│   │   │   └── pulseHealthkit/      # Wrapper JS pour module natif
│   │   ├── hooks/                   # Hooks React (logique métier)
│   │   └── components/               # Composants UI
│   ├── pulse-healthkit/             # Module Expo natif
│   │   ├── ios/                     # Code Swift
│   │   │   └── PulseHealthkitModule.swift
│   │   └── src/                     # Code TypeScript
│   └── package.json                 # Dépendances Expo
│
├── docs/
│   └── legacy/                      # Documentation legacy
│       ├── DATA_QUALITY.md
│       ├── PROFILE_VERSIONING.md
│       └── NORMALIZATION_STRATEGY.md
│
├── ARCHITECTURE.md                   # Ce document
└── MVP.md                            # Cahier des charges MVP
```

---

## 🔐 Sécurité

### Authentification
- **Supabase Auth** : Gestion des utilisateurs et sessions
- **API Keys** : Authentification pour appels API (Oura, OpenAI)

### Protection des Données
- **Row Level Security (RLS)** : Isolation des données par utilisateur
- **Service Role** : Accès privilégié pour webhooks uniquement
- **HTTPS** : Communication sécurisée (production)
- **Secret Header** : Protection endpoint cron (`X-Cron-Secret`)

### Validation
- **Validation des schémas** : Contrôle des formats de données
- **Idempotence** : `source_event_id` empêche les doublons (biometrics)

---

## 🚀 Déploiement

### Backend Pulse

#### API Server
- **Local** : `python api_server.py`
- **Serverless** : Vercel, AWS Lambda, Google Cloud Functions
- **Docker** : Containerisation possible

#### Configuration Requise
- **Variables d'environnement** : Voir `config.example.env`
  - `SUPABASE_URL` : URL Supabase
  - `SUPABASE_SERVICE_KEY` : Clé service Supabase
  - `OPENAI_API_KEY` : Clé API OpenAI
  - `CRON_SECRET` : Secret pour endpoint cron

### Mobile
- **Local** : `cd mobile && npm start`
- **iOS** : `cd mobile && npm run ios` (nécessite Xcode)
- **Android** : `cd mobile && npm run android` (nécessite Android Studio)

### Base de Données
- **Supabase Cloud** : Hébergement géré
- **Migrations** : Appliquer dans l'ordre (001 → 009)

---

## 📊 Format des Données

### Biometrics (Oura API)
```json
{
  "user_id": "uuid",
  "metric_type": "hr" | "hrv" | "sleep_duration",
  "value": 72.0,
  "measured_at": "2024-01-15T10:00:00Z",
  "source": "oura",
  "metadata": {}
}
```

### Daily Context (Apple Health)
```json
{
  "user_id": "uuid",
  "category": "nutrition" | "medication" | "symptoms" | "stool",
  "details": {
    "calories": 2000,
    "carbs": 250
  },
  "logged_at": "2024-01-15T12:00:00Z",
  "source": "AppleHealth"
}
```

### Insights (Générés)
```json
{
  "user_id": "uuid",
  "content": "HRV basse après repas riche en glucides → Réduire les glucides le soir",
  "correlation_type": "nutrition_hrv",
  "priority": 1,
  "created_at": "2024-01-15T14:00:00Z"
}
```

---

## 🔮 Évolutions Futures

### Court Terme
- Android Health Connect (remplacer stub)
- Notifications push pour nouveaux insights
- Amélioration du prompt LLM (plus de contexte)

### Moyen Terme
- Support de nouveaux providers (Garmin, Oura, etc.)
- Historique des insights
- Feedback utilisateur sur insights

### Long Terme
- Apprentissage automatique pour personnalisation
- Prédictions basées sur tendances
- Intégration avec services de santé

---

## 📚 Documentation Complémentaire

### Documentation Principale
- **MVP.md** : Cahier des charges et user stories
- **mobile/ARCHITECTURE.md** : Architecture détaillée du mobile
- **database/migrations/** : Migrations SQL

### Documentation Legacy
- **docs/legacy/** : Documentation de l'ancienne architecture (health_profiles, baselines, anomalies)

---

## 🤝 Points d'Intégration

### Pour Ajouter un Nouveau Provider de Données de Flux
1. Configurer webhook dans le provider
2. Créer un endpoint `POST /api/webhooks/{provider}` pour le format du provider
3. Insérer dans `biometrics` avec `source` approprié

### Pour Ajouter une Nouvelle Catégorie de Contexte
1. Ajouter fonction dans `pulse-healthkit/ios/PulseHealthkitModule.swift`
2. Mettre à jour `HealthScanner.ts` pour lire la nouvelle catégorie
3. Le backend utilisera automatiquement les nouvelles données dans la corrélation

### Pour Générer des Insights
1. Le cron quotidien appelle `POST /api/cron/daily-insight`
2. `CorrelationEngine` récupère les données récentes
3. LLM génère l'insight
4. Mobile récupère via `GET /api/insights/latest`

---

*Document généré le : 2024*
*Version : 2.0 (Nouveau MVP)*
