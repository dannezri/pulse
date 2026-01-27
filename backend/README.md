# Backend Pulse MVP v2.0

API FastAPI minimal pour le Nouveau MVP : Vital flux + Apple Health context + LLM correlation

## 🏗️ Architecture

```
backend/
├── api_server_mvp.py      # API FastAPI minimal (MVP v2.0)
├── vital_webhook.py        # Gestionnaire webhook Vital (validation, mapping identity, idempotence)
├── correlation_engine.py   # Moteur de corrélation (biometrics + daily_context → insight)
├── llm_client.py          # Client LLM (GPT-4o)
├── jwt_auth.py            # Authentification JWT Supabase
├── supabase_client.py     # Client Supabase (service role)
└── requirements.txt       # Dépendances Python
```

## 🚀 Démarrage Local

### 1. Installation

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configuration

Créer un fichier `.env` à partir de `config.example.env` :

```bash
cp config.example.env .env
```

Variables d'environnement requises :

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key  # Pour JWT verification

# OpenAI
OPENAI_API_KEY=sk-...

# Cron Secret
CRON_SECRET=your-secret-for-cron-endpoint

# Vital API Configuration
VITAL_API_KEY=your_vital_api_key
VITAL_REGION=us  # ou eu
VITAL_WEBHOOK_SECRET=your_webhook_secret
VITAL_ENVIRONMENT=sandbox  # ou production

# Port (optionnel, défaut: 9000)
PORT=9000
```

### 3. Lancer le serveur

```bash
python api_server_mvp.py
```

Le serveur démarre sur `http://0.0.0.0:9000`

## 📡 Endpoints

### POST `/api/webhooks/vital`

Reçoit les webhooks Vital API (HR, HRV, Sleep)

**Format** :
```json
{
  "user_id": "vital_user_id",
  "event_id": "optional_event_id_for_idempotence",
  "data": {
    "hr": [{"value": 72, "timestamp": "2024-01-15T10:00:00Z"}],
    "hrv": [{"value": 65, "timestamp": "2024-01-15T10:00:00Z"}],
    "sleep": {"duration_seconds": 28800, "start_time": "2024-01-15T22:00:00Z"}
  }
}
```

**Processus** :
1. Valide le payload (Pydantic)
2. Mappe Vital `user_id` → Supabase `user_id` via `external_identities`
3. Insère dans `biometrics` avec idempotence (`source_event_id`)

**Réponses** :
- `200` : Succès
- `202` : Accepté mais utilisateur non trouvé (webhook accepté mais non traité)
- `400` : Payload invalide

### POST `/api/cron/daily-insight`

Génère les insights quotidiens (appelé par cron externe)

**Protection** : Header `X-Cron-Secret` (doit correspondre à `CRON_SECRET`)

**Format** :
```json
{
  "user_id": "uuid"
}
```

**Processus** :
1. Vérifie le secret
2. Génère un insight en corrélant :
   - 10 derniers `biometrics` (HR/HRV/Sleep)
   - 10 derniers `daily_context` (nutrition/medication/symptoms/stool)
3. Appelle LLM (GPT-4o) via `correlation_engine`
4. Insère dans `insights`

**Réponses** :
- `200` : Insight généré
- `401` : Secret invalide
- `400` : `user_id` manquant

### GET `/api/insights/latest`

Récupère le dernier insight pour l'utilisateur authentifié

**Protection** : JWT Supabase (header `Authorization: Bearer <token>`)

**Processus** :
1. Vérifie le token JWT
2. Extrait `user_id` depuis le token
3. Récupère le dernier insight via RPC

**Réponses** :
- `200` : Insight trouvé
- `401` : Token invalide ou manquant
- `404` : Aucun insight trouvé

## 🔗 Endpoints Vital

### POST `/api/vital/create-user`

Crée un utilisateur Vital et enregistre l'identité externe

**Protection** : JWT Supabase (header `Authorization: Bearer <token>`)

**Processus** :
1. Vérifie le token JWT et extrait `user_id`
2. Crée l'utilisateur Vital via l'API
3. Enregistre l'identité dans `external_identities` (provider_system="vital")

**Réponses** :
- `200` : Utilisateur créé avec `vital_user_id`
- `401` : Token invalide ou manquant
- `503` : Vital client non configuré

**Exemple** :
```bash
curl -X POST http://localhost:9000/api/vital/create-user \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json"
```

### POST `/api/vital/link-token`

Génère un token Vital Link pour connecter des sources

**Protection** : JWT Supabase (header `Authorization: Bearer <token>`)

**Processus** :
1. Vérifie le token JWT et extrait `user_id`
2. Récupère le `vital_user_id` depuis `external_identities`
3. Génère un link token via l'API Vital

**Réponses** :
- `200` : Token généré avec `link_token` et `expires_at`
- `401` : Token invalide ou manquant
- `404` : Utilisateur Vital non trouvé
- `503` : Vital client non configuré

**Exemple** :
```bash
curl -X POST http://localhost:9000/api/vital/link-token \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json"
```

### GET `/api/vital/connections`

Liste les sources connectées pour l'utilisateur

**Protection** : JWT Supabase (header `Authorization: Bearer <token>`)

**Processus** :
1. Vérifie le token JWT et extrait `user_id`
2. Récupère le `vital_user_id` depuis `external_identities`
3. Liste les connexions via l'API Vital

**Réponses** :
- `200` : Liste des providers connectés
  ```json
  {
    "status": "success",
    "providers": [
      {
        "name": "Apple Health",
        "slug": "apple_health",
        "status": "connected",
        "created_at": "2024-01-15T10:00:00Z",
        "last_sync_at": "2024-01-15T12:00:00Z"
      }
    ]
  }
  ```
- `401` : Token invalide ou manquant
- `404` : Utilisateur Vital non trouvé
- `503` : Vital client non configuré

**Exemple** :
```bash
curl -X GET http://localhost:9000/api/vital/connections \
  -H "Authorization: Bearer <jwt>"
```

### DELETE `/api/vital/connections/{provider_slug}`

Déconnecte une source pour l'utilisateur

**Protection** : JWT Supabase (header `Authorization: Bearer <token>`)

**Args** :
- `provider_slug` : Slug du provider (ex: "apple_health", "fitbit")

**Réponses** :
- `200` : Provider déconnecté
- `401` : Token invalide ou manquant
- `404` : Utilisateur Vital non trouvé
- `503` : Vital client non configuré

**Exemple** :
```bash
curl -X DELETE http://localhost:9000/api/vital/connections/fitbit \
  -H "Authorization: Bearer <jwt>"
```

## 🔧 Configuration Cron

Pour générer les insights quotidiennement, configurer un cron externe (ex: GitHub Actions, Vercel Cron, etc.) :

```bash
# Exemple avec curl
curl -X POST https://your-api.com/api/cron/daily-insight \
  -H "Content-Type: application/json" \
  -H "X-Cron-Secret: your-secret" \
  -d '{"user_id": "uuid"}'
```

## 📝 Notes

- **Idempotence** : Les webhooks Vital utilisent `source_event_id` pour éviter les doublons
- **Mapping Identity** : Vital `user_id` doit être présent dans `external_identities` avec `provider_system="vital"`
- **JWT** : Les tokens Supabase sont vérifiés via le client Supabase (recommandé)
- **Vital Configuration** : Voir [`mobile/VITAL_SETUP.md`](../mobile/VITAL_SETUP.md) pour la configuration complète

## 🧪 Tests

```bash
# Test webhook Vital
curl -X POST http://localhost:9000/api/webhooks/vital \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "vital_user_123",
    "data": {
      "hr": [{"value": 72, "timestamp": "2024-01-15T10:00:00Z"}]
    }
  }'

# Test cron (nécessite CRON_SECRET)
curl -X POST http://localhost:9000/api/cron/daily-insight \
  -H "Content-Type: application/json" \
  -H "X-Cron-Secret: your-secret" \
  -d '{"user_id": "uuid"}'

# Test insights latest (nécessite JWT)
curl -X GET http://localhost:9000/api/insights/latest \
  -H "Authorization: Bearer <supabase-jwt-token>"

# Test Vital endpoints
# 1. Créer un utilisateur Vital
curl -X POST http://localhost:9000/api/vital/create-user \
  -H "Authorization: Bearer <jwt>"

# 2. Générer un link token
curl -X POST http://localhost:9000/api/vital/link-token \
  -H "Authorization: Bearer <jwt>"

# 3. Récupérer les connexions
curl -X GET http://localhost:9000/api/vital/connections \
  -H "Authorization: Bearer <jwt>"

# 4. Déconnecter un provider
curl -X DELETE http://localhost:9000/api/vital/connections/fitbit \
  -H "Authorization: Bearer <jwt>"
```
