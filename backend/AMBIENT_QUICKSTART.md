# Ambient Concierge API - Guide de Démarrage Rapide

## Prérequis

- Python 3.9+
- Compte Supabase
- Clé API OpenAI (pour la génération d'insights)

## Installation

```bash
cd backend

# Installer les dépendances
pip3 install fastapi uvicorn python-dotenv supabase openai
```

## Configuration

### Option 1 : Variables d'environnement (Recommandé)

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_KEY="your-service-key"
export OPENAI_API_KEY="sk-..."
```

### Option 2 : Fichier .env

Créer un fichier `.env` dans `/backend` :

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
OPENAI_API_KEY=sk-...
```

## Démarrage

```bash
python3 api_server_ambient.py
```

Le serveur démarre sur `http://localhost:9000` (ou premier port disponible).

## Endpoints Disponibles

### GET `/`
Health check

```bash
curl http://localhost:9000/
```

### GET `/api/baselines/{user_id}`
Récupère les baselines (μ, σ) pour un utilisateur

```bash
curl http://localhost:9000/api/baselines/user-uuid-here
```

Response :
```json
{
  "status": "success",
  "user_id": "user-uuid",
  "baselines": {
    "hrv": {
      "mean": 65.2,
      "std": 8.5,
      "weight": 3,
      "count": 42
    },
    "heart_rate": {
      "mean": 60.0,
      "std": 5.0,
      "weight": 3,
      "count": 120
    }
  },
  "lookback_days": 14
}
```

### POST `/api/insights/prioritized`
Génère un insight "Concierge" basé sur les anomalies

```bash
curl -X POST http://localhost:9000/api/insights/prioritized \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-uuid",
    "anomalies": [
      {
        "metric": "hrv",
        "value": 45.2,
        "z_score": -2.35,
        "weight": 3,
        "direction": "below",
        "baseline": {"mean": 65.2, "std": 8.5}
      }
    ]
  }'
```

Response :
```json
{
  "status": "success",
  "insight": {
    "content": "HRV bas détectée. Priorisez le repos et évitez le stress.",
    "state": "warning",
    "priority": 1,
    "anomalies_count": 1
  }
}
```

### GET `/api/insights/latest?user_id={user_id}`
Récupère le dernier insight d'un utilisateur

```bash
curl "http://localhost:9000/api/insights/latest?user_id=user-uuid"
```

## Mode Développement

Pour le développement sans Supabase configuré, vous pouvez :

1. Utiliser un mock Supabase (à implémenter)
2. Configurer un projet Supabase gratuit sur [supabase.com](https://supabase.com)
3. Utiliser la base de données de test

## Troubleshooting

### Erreur : `supabase_url is required`

Vérifiez que les variables d'environnement sont bien définies :

```bash
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_KEY
```

### Erreur : `Operation not permitted: .env`

Le fichier `.env` n'est pas accessible. Utilisez les variables d'environnement système à la place.

### Port déjà utilisé

Le serveur trouve automatiquement un port libre. Si le port 9000 est occupé, il essaiera 9001, 9002, etc.

## Architecture

```
Mobile App
    ↓
GET /api/baselines/{user_id}
    ↓
PriorityEngine.calculate_baselines()
    ↓
Supabase (biometrics table)
    ↓
Return {mean, std, weight}
    ↓
Mobile calcule Z-Scores
    ↓
POST /api/insights/prioritized
    ↓
LLMClient.generate_insight()
    ↓
OpenAI GPT-4
    ↓
Return insight + save to DB
```

## Logs

Les logs sont affichés dans la console :

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:9000
```

## Production

Pour la production, utilisez Gunicorn ou un service managé :

```bash
gunicorn api_server_ambient:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:9000
```

## Support

Pour toute question, consultez la documentation complète dans `AMBIENT_CONCIERGE.md`.
