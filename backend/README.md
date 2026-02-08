# Backend Pulse MVP v2.0

API FastAPI minimal pour le Nouveau MVP : Vital flux + Apple Health context + LLM correlation

## 🏗️ Architecture

```
backend/
├── api_server_mvp.py      # API FastAPI minimal (MVP v2.0)
├── vital_webhook.py        # Gestionnaire webhook Vital (validation, mapping identity, idempotence)
├── correlation_engine.py   # Moteur de corrélation (biometrics + daily_context → insight)
├── llm_client.py          # Client LLM (GPT-4o)
├── gemini_client.py       # Client Gemini avec mode thinking (nouveau)
├── explain_service.py     # Service d'explication énergétique (utilise Gemini)
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

# OpenAI (utilisé par correlation_engine, wellness_coach)
OPENAI_API_KEY=sk-...

# Google Gemini (utilisé par explain_service pour "Pourquoi ce score ?")
GOOGLE_API_KEY=your-google-api-key
GEMINI_MODEL=gemini-2.0-flash-thinking-exp-01-21  # Optionnel

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

- **JWT** : Les tokens Supabase sont vérifiés via le client Supabase (recommandé)
- **Idempotence** : Les webhooks utilisent des identifiants uniques pour éviter les doublons

## 🧪 Tests

```bash
# Test cron (nécessite CRON_SECRET)
curl -X POST http://localhost:9000/api/cron/daily-insight \
  -H "Content-Type: application/json" \
  -H "X-Cron-Secret: your-secret" \
  -d '{"user_id": "uuid"}'

# Test insights latest (nécessite JWT)
curl -X GET http://localhost:9000/api/insights/latest \
  -H "Authorization: Bearer <supabase-jwt-token>"
```
