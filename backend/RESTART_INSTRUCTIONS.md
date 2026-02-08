# ⚠️ IMPORTANT : Démarrer le bon serveur backend

## Problème Actuel

Vous avez démarré `api_server_ambient.py` qui **ne contient pas** le endpoint `/api/v1/analyze-event`.

Le endpoint se trouve dans `api_server.py` (la version complète).

## Solution : Redémarrer avec le bon serveur

### 1. Arrêter le serveur actuel

Dans le terminal où tourne `api_server_ambient.py` :
```bash
# Appuyer sur CTRL+C
```

### 2. Démarrer le bon serveur

```bash
cd /Users/dannezri/Desktop/Pulse/backend
python3 api_server.py
```

## Vérification

Après le démarrage, vous devriez voir dans les logs :

```
🚀 Démarrage du serveur Bio-Feedback IA sur http://0.0.0.0:9000
📡 Endpoint webhook: http://localhost:9000/api/webhooks/wearables
```

Et le endpoint `/api/v1/analyze-event` sera disponible.

## Différences entre les deux serveurs

### `api_server.py` (UTILISER CELUI-CI)
- ✅ Tous les endpoints incluant `/api/v1/analyze-event`
- ✅ Smart Cache pour l'analyse IA
- ✅ Service AIAnalysisService
- ✅ Support complet LLM

### `api_server_ambient.py` (Ancien)
- ❌ Pas de `/api/v1/analyze-event`
- ❌ Version simplifiée pour Ambient Concierge
- ❌ Pas de Smart Cache

## Test rapide après redémarrage

```bash
curl -X POST http://localhost:9000/api/v1/analyze-event \
  -H "Content-Type: application/json" \
  -d '{"user_id": "006b5096-1983-44ae-9fc5-a8431c9f40be", "event": {"title": "Test", "start": "2026-01-28T14:00:00Z", "end": "2026-01-28T15:00:00Z"}}'
```

Si ça retourne un JSON avec "status": "success", c'est bon ! 🎉
