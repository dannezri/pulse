# Infrastructure de Données - Bio-Feedback IA

Ce document décrit l'infrastructure complète pour l'ingestion, la normalisation et le stockage des données biométriques.

## 📁 Structure du Projet

```
Pulse/
├── database/
│   ├── schema.sql              # Schéma complet de la base de données
│   └── migrations/             # Migrations versionnées
├── backend/
│   ├── open_wearables_integration.py  # Client Open Wearables Ingestion Engine
│   ├── data_normalizer.py            # Système de normalisation
│   ├── supabase_client.py             # Client Supabase
│   ├── webhook_handler.py             # Handler webhooks Open Wearables
│   ├── main.py                        # Pipeline principal
│   ├── api_server.py                  # API FastAPI
│   ├── requirements.txt               # Dépendances Python
│   └── config.example.env             # Template de configuration
├── MVP.md                      # Cahier des charges MVP
├── BBD_docs.md                 # Documentation base de données
└── INFRASTRUCTURE.md           # Ce fichier
```

## 🗄️ Base de Données (Supabase)

### Installation

1. Créer un projet Supabase
2. Exécuter le script SQL dans l'éditeur SQL de Supabase :
   ```sql
   -- Copier/coller le contenu de database/schema.sql
   ```

### Tables Principales

#### `profiles`
Stocke les informations utilisateur et les réglages :
- `id` : UUID (référence auth.users)
- `health_goal` : Objectif santé ('energy', 'sleep', 'weight', 'focus')
- `baseline_hrv` : Baseline HRV habituelle
- `baseline_resting_hr` : Rythme cardiaque au repos habituel
- `open_wearables_user_id` : ID utilisateur Open Wearables

#### `biometrics`
Stocke toutes les mesures brutes des wearables :
- `metric_type` : Type de métrique ('hr', 'hrv', 'sleep_duration', 'steps', etc.)
- `value` : Valeur numérique
- `recorded_at` : Timestamp de la mesure
- `raw_data` : JSON brut (pour analyse future)
- `source` : Source des données ('open_wearables', 'apple_health', 'garmin', etc.)

#### `health_profiles`
Cache les profils de santé normalisés (un par jour) :
- `profile_data` : JSON du profil complet normalisé
- `date` : Date du profil

#### `insights` & `meals`
Tables pour les insights IA et le journal alimentaire (voir BBD_docs.md)

### Sécurité (RLS)

Toutes les tables ont Row Level Security activé :
- Les utilisateurs ne peuvent voir que leurs propres données
- Le service role peut insérer des données via les webhooks

## 🔌 Intégration Open Wearables Ingestion Engine

### Configuration

1. Lancer l'instance Open Wearables (auto-hébergé) :
   ```bash
   cd open-wearables
   docker-compose up -d
   ```

2. Configurer Ngrok pour exposer l'instance (production) :
   ```bash
   ngrok http 8080
   # Utiliser l'URL fournie : https://mckenzie-endarterial-tomi.ngrok-free.dev
   ```

3. Variables d'environnement requises :
   - `OPEN_WEARABLES_BASE_URL` : URL de base (http://localhost:8080 en local, ou URL Ngrok)
   - `OPEN_WEARABLES_API_KEY` : Clé API (optionnelle)
   - `WEBHOOK_URL` : URL où Open Wearables enverra les données (http://host.docker.internal:8000/api/webhooks/wearables)

### Fonctionnalités

Le module `open_wearables_integration.py` permet de :
- Récupérer les données de sommeil
- Récupérer les données de fréquence cardiaque (HR)
- Récupérer les données HRV (Variabilité de la Fréquence Cardiaque)
- Récupérer les données d'activité (pas, distance, calories)
- Vérifier les signatures des webhooks (optionnel)

### Webhooks

Open Wearables peut envoyer des données en temps réel via webhooks :
- Configurer l'URL dans Open Wearables : `http://host.docker.internal:8000/api/webhooks/wearables`
- Format des données : `{"user_id": "...", "data": {"hr": [...], "hrv": [...], "sleep": {...}, "steps": [...]}}`

## 🔄 Système de Normalisation

### Objectif

Transformer les données **unifiées** d'Open Wearables en **"Profil de Santé JSON"** standardisé et lisible par l'IA.

### Séparation des Responsabilités

**Open Wearables** (Ingestion Engine) :
- ✅ Unifie les structures JSON (formats providers → format commun)
- ✅ Normalise les timestamps (ISO 8601)
- ✅ Mappe les champs (ex: "heartRate" → "hr")
- ❌ Ne calcule PAS les baselines, anomalies, contexte

**Pulse** (DataNormalizer) :
- ✅ Transforme en métriques santé (logique santé centralisée)
- ✅ Conversion en unités standard (bpm, ms, minutes)
- ✅ Agrégats (moyennes, min, max, resting)
- ✅ Calcul des baselines avec fallback (7j → 14j → 30j)
- ✅ Détection d'anomalies avec confiance
- ✅ Construction du contexte (heure, jour, tendances)
- ✅ Qualité des données (low/medium/high)

**Règle d'or** : La logique "santé" vit **uniquement** dans Pulse.

### Processus

1. **Réception** : Format unifié Open Wearables (déjà normalisé structurellement)
2. **Transformation** : Conversion en unités standard (bpm, ms, minutes)
3. **Agrégation** : Moyennes, min, max, resting
4. **Calcul des Baselines** : Moyenne glissante sur 7 jours (avec fallback 14j/30j)
5. **Détection d'Anomalies** : Comparaison avec les baselines (avec confiance)
6. **Construction du Contexte** : Heure, jour, tendances
7. **Évaluation Qualité** : Qualité globale des données (low/medium/high)

### Format du Profil de Santé JSON

```json
{
  "timestamp": "2024-01-15T14:30:00",
  "user_goal": "energy",
  "current_metrics": {
    "sleep": {
      "duration_minutes": 420,
      "quality_score": 85,
      "deep_sleep_minutes": 120,
      "rem_sleep_minutes": 90
    },
    "heart_rate": {
      "average_bpm": 72,
      "resting_bpm": 58,
      "max_bpm": 145
    },
    "hrv": {
      "average_ms": 65,
      "latest_ms": 62
    },
    "activity": {
      "steps": 8500,
      "distance_meters": 6500,
      "calories_kcal": 2100
    }
  },
  "baselines": {
    "hrv_baseline": 68,
    "hr_baseline": 60,
    "sleep_baseline": 450
  },
  "anomalies": [
    {
      "type": "hrv_drop",
      "severity": "medium",
      "current": 62,
      "baseline": 68,
      "drop_percentage": 8.82
    }
  ],
  "context": {
    "current_time": "14:30",
    "day_of_week": "Monday",
    "time_of_day": "afternoon",
    "trends": {
      "hrv": "declining",
      "sleep": "stable"
    }
  }
}
```

## 🚀 Déploiement

### Backend Python

1. **Installation locale** :
   ```bash
   cd backend
   pip install -r requirements.txt
   cp config.example.env .env
   # Éditer .env avec vos clés
   ```

2. **Test du pipeline** :
   ```bash
   python main.py
   ```

3. **Lancer l'API** :
   ```bash
   python api_server.py
   ```

### Déploiement Serverless (Recommandé)

#### Vercel
```bash
vercel --prod
```

#### AWS Lambda
Utiliser Serverless Framework ou AWS SAM

#### Google Cloud Functions
```bash
gcloud functions deploy open-wearables-webhook --runtime python311 --trigger-http
```

## 📊 Flux de Données

```
┌─────────────┐
│   Wearable  │ (Apple Health, Garmin, Oura)
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  Open Wearables     │ (Ingestion Engine - Auto-hébergé)
│  http://localhost:8080│
└──────┬──────────────┘
       │
       ├─── Webhook ───► [webhook_handler.py]
       │                      │
       │                      ▼
       │              [data_normalizer.py]
       │                      │
       │                      ▼
       └─── API Call ──► [main.py] ──► [supabase_client.py]
                                        │
                                        ▼
                                   ┌──────────┐
                                   │ Supabase │
                                   └──────────┘
                                        │
                                        ▼
                              [health_profiles table]
                                        │
                                        ▼
                              ┌─────────────────┐
                              │  Profil JSON    │
                              │  pour l'IA      │
                              └─────────────────┘
```

## ✅ Checklist de Mise en Place

- [ ] Créer le projet Supabase
- [ ] Exécuter `database/schema.sql`
- [ ] Lancer l'instance Open Wearables (Docker)
- [ ] Configurer Ngrok pour exposer Open Wearables (production)
- [ ] Configurer les variables d'environnement
- [ ] Configurer les webhooks Open Wearables
- [ ] Tester la synchronisation manuelle
- [ ] Déployer l'API backend
- [ ] Tester avec un utilisateur réel
- [ ] Vérifier que les profils de santé sont créés

## 🔗 Prochaines Étapes

Une fois l'infrastructure de données en place :

1. **Intégration IA** : Utiliser les profils de santé pour générer des insights
2. **Frontend React Native** : Afficher les données et insights
3. **Notifications Push** : Système de triggers basé sur les anomalies
4. **Analyse de Repas** : Intégration Vision API pour les photos

## 📚 Documentation Supplémentaire

- [Open Wearables Documentation](https://github.com/open-wearables/open-wearables)
- [Supabase Documentation](https://supabase.com/docs)
- Voir `backend/README.md` pour plus de détails techniques
