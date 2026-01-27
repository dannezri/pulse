# Architecture Asynchrone : Découplage Webhook / Normalisation

## 📋 Vue d'Ensemble

Le système utilise maintenant un pattern asynchrone pour découpler la **réception des webhooks** de la **normalisation des données**. Cela permet :

- ✅ **Réponse rapide** : L'endpoint webhook répond en < 100ms
- ✅ **Résilience** : Les pics de trafic sont gérés par la queue
- ✅ **Scalabilité** : Les workers peuvent être mis à l'échelle indépendamment
- ✅ **Débogage** : Les webhooks bruts sont stockés pour analyse

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Open Wearables                            │
│              (envoie webhook)                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Endpoint Webhook (FastAPI)                      │
│  POST /api/webhooks/wearables                                │
│                                                              │
│  1. Valide signature                                         │
│  2. Enregistre brut → webhook_events                        │
│  3. Push job → Redis/Celery                                  │
│  4. Répond 200 OK (rapide)                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Redis Queue                                │
│              (Queue: normalization)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Worker Celery                                   │
│  workers.normalization_worker.normalize_webhook_data        │
│                                                              │
│  1. Récupère webhook_event depuis DB                        │
│  2. Sauvegarde données brutes → biometrics                 │
│  3. Normalise les données                                    │
│  4. Calcule baselines                                        │
│  5. Crée/mise à jour health_profile                         │
│  6. Marque webhook_event comme "completed"                  │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Composants

### 1. Webhook Receiver (`webhook_receiver.py`)

**Rôle** : Recevoir les webhooks rapidement

**Responsabilités** :
- Valider la signature (si fournie)
- Enregistrer le payload brut dans `webhook_events`
- Pousser un job dans la queue Celery
- Répondre 200 OK rapidement

**Temps de réponse** : < 100ms

### 2. Job Queue (`job_queue.py`)

**Rôle** : Gérer la queue de jobs avec Celery + Redis

**Configuration** :
- Broker : Redis
- Queue : `normalization`
- Serialization : JSON
- Timeout : 5 minutes max par tâche

### 3. Normalization Worker (`workers/normalization_worker.py`)

**Rôle** : Traiter les webhooks en arrière-plan

**Tâche Celery** : `normalize_webhook_data`

**Processus** :
1. Récupère le `webhook_event` depuis la DB
2. Sauvegarde les données brutes dans `biometrics` (avec idempotence)
3. Récupère les données du jour + historiques
4. Normalise les données
5. Calcule les baselines
6. Crée/mise à jour le `health_profile`
7. Marque le `webhook_event` comme "completed"

### 4. Table `webhook_events`

Stocke les webhooks bruts pour :
- Traçabilité
- Reprocessing en cas d'erreur
- Débogage

**Colonnes** :
- `id` : UUID
- `user_id` : UUID Supabase
- `open_wearables_user_id` : ID Open Wearables
- `payload` : JSONB (payload brut)
- `signature` : Signature du webhook
- `status` : `pending`, `processing`, `completed`, `failed`
- `error_message` : Message d'erreur si échec
- `processed_at` : Timestamp de traitement
- `created_at` : Timestamp de réception

## 🚀 Déploiement

### Prérequis

1. **Redis** : Broker pour Celery
   ```bash
   # Docker
   docker run -d -p 6379:6379 redis:7-alpine
   
   # Ou utiliser un service Redis cloud (Upstash, Redis Cloud, etc.)
   ```

2. **Variables d'environnement** :
   ```env
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   # Ou
   REDIS_URL=redis://localhost:6379/0
   ```

### Démarrage

#### 1. API Server (réception webhooks)

```bash
cd backend
python api_server.py
```

L'API écoute sur le port configuré (défaut: 9000) et reçoit les webhooks.

#### 2. Worker Celery (traitement)

```bash
cd backend
python start_worker.py
```

Ou directement avec Celery :

```bash
celery -A job_queue.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --queue=normalization
```

### Déploiement Serverless

Pour un déploiement serverless (Vercel, AWS Lambda, etc.) :

#### Option 1 : Worker séparé

- **API** : Déployée en serverless (Vercel, Lambda)
- **Worker** : Déployé sur un serveur dédié ou un service géré (Railway, Render, etc.)

#### Option 2 : Queue externe

- Utiliser une queue externe (AWS SQS, Google Cloud Tasks, etc.)
- Adapter `job_queue.py` pour utiliser ces services

#### Option 3 : Worker serverless

- Utiliser AWS Lambda avec Celery (via SQS)
- Ou Google Cloud Functions avec Cloud Tasks

## 📊 Monitoring

### Vérifier les webhooks en attente

```sql
SELECT status, COUNT(*) 
FROM webhook_events 
GROUP BY status;
```

### Vérifier les webhooks échoués

```sql
SELECT id, user_id, error_message, created_at 
FROM webhook_events 
WHERE status = 'failed' 
ORDER BY created_at DESC 
LIMIT 10;
```

### Vérifier le statut des workers

```bash
# Avec Flower (monitoring Celery)
pip install flower
celery -A job_queue.celery_app flower
```

## 🔄 Reprocessing

En cas d'erreur, vous pouvez reprocesser un webhook :

```python
from job_queue import push_normalization_job

# Reprocesser un webhook_event
push_normalization_job(
    webhook_event_id="uuid-du-webhook",
    user_id="uuid-supabase",
    open_wearables_user_id="open-wearables-id"
)
```

## ⚙️ Configuration

### Concurrency

Ajuster le nombre de workers en parallèle :

```python
# Dans start_worker.py
celery_app.worker_main([
    "worker",
    "--concurrency=4",  # 4 workers en parallèle
    ...
])
```

### Timeouts

Ajuster les timeouts dans `job_queue.py` :

```python
task_time_limit=300,  # 5 minutes max
task_soft_time_limit=240,  # 4 minutes soft limit
```

### Retry Policy

Ajouter une politique de retry dans le worker :

```python
@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60}
)
def normalize_webhook_data(self, ...):
    ...
```

## 🧪 Tests

### Test local

1. Démarrer Redis : `docker run -d -p 6379:6379 redis:7-alpine`
2. Démarrer l'API : `python api_server.py`
3. Démarrer le worker : `python start_worker.py`
4. Envoyer un webhook de test :

```bash
curl -X POST http://localhost:9000/api/webhooks/wearables \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-id",
    "data": {
      "hr": [{"value": 72, "timestamp": "2024-01-15T10:00:00Z"}]
    }
  }'
```

5. Vérifier que le job est traité :

```sql
SELECT * FROM webhook_events ORDER BY created_at DESC LIMIT 1;
```

## 📈 Performance

### Métriques attendues

- **Endpoint webhook** : < 100ms (réponse 200)
- **Worker** : 1-5 secondes par webhook (selon volume de données)
- **Throughput** : 10-100 webhooks/seconde (selon configuration)

### Optimisations

1. **Batch processing** : Traiter plusieurs webhooks en batch
2. **Caching** : Mettre en cache les baselines
3. **Indexes** : Vérifier les index sur `webhook_events` et `biometrics`

## 🔐 Sécurité

- **Signature validation** : Validée avant enregistrement
- **RLS** : Les utilisateurs ne voient que leurs propres webhooks
- **Service role** : Utilisé pour les insertions depuis le worker

---

*Document créé le : 2024*
*Migration : 004_add_webhook_queue.sql*
