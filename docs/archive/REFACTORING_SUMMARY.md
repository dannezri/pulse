# Résumé du Refactoring MVP v2.0

## 📋 Vue d'Ensemble

Refactoring complet pour appliquer le **Nouveau MVP v2.0** : Vital flux + Apple Health context + LLM correlation.

**Date** : 2024
**Version** : 2.0.0

---

## ✅ Fichiers Créés

### Backend
- `backend/api_server_mvp.py` : API FastAPI minimal (MVP v2.0)
- `backend/vital_webhook.py` : Gestionnaire webhook Vital (validation Pydantic, mapping identity, idempotence)
- `backend/jwt_auth.py` : Authentification JWT Supabase
- `backend/README.md` : Documentation backend minimal
- `backend/config.example.env` : Template configuration

### Mobile
- `mobile/src/services/HealthScanner.ts` : Service de synchronisation contexte Apple Health
- `mobile/scripts/check-deps.sh` : Script de vérification dépendances

### Database
- `database/migrations/009_mvp_context_and_insights.sql` : Migration MVP v2.0 (appliquée)

### Documentation
- `MVP.md` : Mis à jour pour MVP v2.0
- `ARCHITECTURE.md` : Mis à jour pour MVP v2.0
- `DEPLOYMENT.md` : Guide de déploiement complet
- `.cursor/rules/mvp-v2.md` : Règles Cursor pour MVP v2.0

---

## 📦 Fichiers Archivés (Legacy)

### Backend
- `backend/legacy/data_normalizer.py` : Normalisation avec baselines/anomalies (legacy)
- `backend/legacy/main.py` : DataPipeline Open Wearables (legacy)
- `backend/legacy/insight_generator.py` : Génération insights health_profiles (legacy)
- `backend/legacy/webhook_receiver.py` : Récepteur webhook Open Wearables (legacy)
- `backend/legacy/open_wearables_integration.py` : Client Open Wearables (legacy)
- `backend/legacy/workers/` : Workers Celery (legacy)

### Documentation
- `docs/legacy/DATA_QUALITY.md` : Documentation qualité données (legacy)
- `docs/legacy/PROFILE_VERSIONING.md` : Documentation versioning (legacy)
- `docs/legacy/NORMALIZATION_STRATEGY.md` : Documentation normalisation (legacy)

---

## 🔄 Fichiers Modifiés

### Backend
- `backend/correlation_engine.py` : Amélioré pour gérer données insuffisantes (insight neutre)
- `backend/api_server.py` : Conservé pour compatibilité (utiliser `api_server_mvp.py` pour MVP v2.0)

### Mobile
- `mobile/app/(tabs)/index.tsx` : Bouton "Synchroniser Contexte" ajouté
- `mobile/src/modules/pulseHealthkit/index.ts` : Fonctions readNutrition, readMedications, readSymptoms, readStool ajoutées
- `mobile/pulse-healthkit/ios/PulseHealthkitModule.swift` : Fonctions contexte HealthKit ajoutées

---

## 🗄️ Schéma Database

### Tables MVP v2.0

#### `biometrics`
- Colonnes : `user_id`, `metric_type`, `value`, `measured_at`, `source`, `source_event_id`, `metadata` (JSONB)
- Index : `(user_id, measured_at DESC)`, `(user_id, metric_type, measured_at DESC)`
- Idempotence : Contrainte unique `(user_id, source, source_event_id)`

#### `daily_context`
- Colonnes : `user_id`, `category`, `details` (JSONB), `logged_at`, `source`
- Index : `(user_id, logged_at DESC)`, `(user_id, category, logged_at DESC)`
- RLS : SELECT/INSERT pour `auth.uid() = user_id`

#### `insights`
- Colonnes : `user_id`, `content`, `correlation_type`, `priority`, `created_at`
- RLS : SELECT pour `auth.uid() = user_id`

#### `external_identities`
- Colonnes : `supabase_user_id`, `provider_system`, `external_user_id`, `metadata`, `is_active`
- Contrainte unique : `(supabase_user_id, provider_system, external_user_id)`

### Fonctions RPC

- `get_recent_biometrics(user_id, limit)` : Récupère N derniers biometrics
- `get_recent_daily_context(user_id, limit)` : Récupère N derniers daily_context
- `get_latest_insight(user_id)` : Récupère dernier insight

---

## 📡 Endpoints API

### POST `/api/webhooks/vital`
- **Rôle** : Reçoit webhooks Vital API (HR, HRV, Sleep)
- **Validation** : Pydantic schema
- **Mapping** : Vital user_id → Supabase user_id via `external_identities`
- **Idempotence** : `source_event_id` unique
- **Réponses** : 200 (succès), 202 (accepté mais user non trouvé), 400 (payload invalide)

### POST `/api/cron/daily-insight`
- **Rôle** : Génère insights quotidiens
- **Protection** : Header `X-Cron-Secret`
- **Processus** : Corrèle 10 derniers biometrics + 10 derniers daily_context → LLM → insights
- **Réponses** : 200 (insight généré), 401 (secret invalide), 400 (user_id manquant)

### GET `/api/insights/latest`
- **Rôle** : Récupère dernier insight utilisateur
- **Protection** : JWT Supabase (header `Authorization: Bearer <token>`)
- **Réponses** : 200 (insight trouvé), 401 (token invalide), 404 (aucun insight)

---

## 📱 Mobile

### Service HealthScanner
- **Fichier** : `mobile/src/services/HealthScanner.ts`
- **Fonction** : `syncLast6Hours()` : Scanne contexte Apple Health des 6 dernières heures
- **Catégories** : Nutrition (calories, carbs), Médicaments, Symptômes, Selles
- **Insertion** : Supabase client avec session user (RLS)
- **Best Effort** : Retourne [] si catégorie indisponible (pas de crash)

### Module Natif iOS
- **Fichier** : `mobile/pulse-healthkit/ios/PulseHealthkitModule.swift`
- **Fonctions** :
  - `readNutrition(fromISO, toISO)` : Calories et glucides
  - `readMedications(fromISO, toISO)` : Médicaments (stub si indisponible)
  - `readSymptoms(fromISO, toISO)` : Symptômes (stub si indisponible)
  - `readStool(fromISO, toISO)` : Selles (stub si indisponible)

### UI
- **Bouton** : "Synchroniser Contexte" (iOS uniquement, device réel)
- **Messages** :
  - Simulateur : "HealthKit indisponible sur simulateur"
  - Android : "HealthKit disponible uniquement sur iOS"
  - Succès : "Contexte synchronisé. Pulse analyse vos données…"

---

## 🔐 Sécurité

### RLS (Row Level Security)
- `daily_context` : SELECT/INSERT pour `auth.uid() = user_id`
- `insights` : SELECT pour `auth.uid() = user_id`
- `biometrics` : INSERT via service role (backend), SELECT via policies

### Authentification
- **JWT** : Vérification via Supabase client (recommandé)
- **Cron Secret** : Header `X-Cron-Secret` pour protéger endpoint cron
- **Service Role** : Utilisé uniquement côté backend (webhooks, cron)

### Idempotence
- **Webhook Vital** : `source_event_id` unique par événement
- **Contrainte unique** : `(user_id, source, source_event_id)` sur `biometrics`

---

## 🧪 Tests

### Test Webhook Vital
```bash
curl -X POST http://localhost:9000/api/webhooks/vital \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "vital_user_123",
    "event_id": "test_event_001",
    "data": {
      "hr": [{"value": 72, "timestamp": "2024-01-15T10:00:00Z"}]
    }
  }'
```

### Test Cron Insight
```bash
curl -X POST http://localhost:9000/api/cron/daily-insight \
  -H "Content-Type: application/json" \
  -H "X-Cron-Secret: your-secret" \
  -d '{"user_id": "uuid"}'
```

### Test Insights Latest
```bash
curl -X GET http://localhost:9000/api/insights/latest \
  -H "Authorization: Bearer <supabase-jwt-token>"
```

### Test Mobile
1. Lancer sur device iOS réel
2. Cliquer "Synchroniser Contexte"
3. Vérifier notification et données dans `daily_context`

---

## 📝 Notes Importantes

### HealthKit
- **Simulateur** : HealthKit indisponible (message explicite)
- **Best Effort** : Catégories indisponibles retournent [] sans crash
- **Permissions** : Demandées automatiquement via module natif

### Mapping Identity
- **Vital** : `user_id` Vital doit être dans `external_identities` avec `provider_system="vital"`
- **Si absent** : Webhook accepté (202) mais non traité

### Données Insuffisantes
- **Si < 3 biometrics ET < 3 context** : Insight neutre retourné
- **Message** : "Pas assez de données pour générer un insight"

### Dépendances
- **Expo/RN** : Toujours utiliser `cd mobile && npx expo install <package>`
- **Node** : Respecter `engines.node >= 20.19.4`
- **Vérification** : `cd mobile && npx expo-doctor`

---

## 🚀 Prochaines Étapes

1. **Configurer Vital Webhook** : Ajouter webhook dans dashboard Vital
2. **Configurer Cron** : Mettre en place cron quotidien pour génération insights
3. **Tester sur Device iOS** : Vérifier synchronisation contexte
4. **Vérifier Insights** : S'assurer que les insights sont générés correctement

---

*Version : 2.0.0*
*Date : 2024*
