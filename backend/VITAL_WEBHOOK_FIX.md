# Fix Webhook Vital - 27 janvier 2026

## Problème

Les webhooks Vital retournaient 404 Not Found :

```
POST /api/webhooks/vital HTTP/1.1
Host: mckenzie-endarterial-tomi.ngrok-free.dev
404 Not Found
```

## Cause

Le serveur `api_server_ambient.py` qui était en cours d'exécution ne contenait pas l'endpoint `/api/webhooks/vital`. Cet endpoint existait uniquement dans `api_server.py` (qui ne pouvait pas démarrer à cause de dépendances manquantes sur `open_wearables_integration`).

## Solution

Ajout de l'endpoint `/api/webhooks/vital` à `api_server_ambient.py` avec :

1. **Support des event types Vital** :
   - `daily.data.steps.updated` → `steps`
   - `daily.data.distance.updated` → `distance`
   - `daily.data.calories.updated` → `calories`
   - `timeseries.heartrate.updated` → `hr`
   - `timeseries.hrv.updated` → `hrv`
   - `daily.data.sleep.updated` → `sleep_duration`

2. **Parsing correct des timestamps** :
   - Conversion des timestamps ISO 8601 en objets `datetime`
   - Support des formats avec timezone (`+00:00`)

3. **Idempotence** :
   - Utilisation de `source_event_id` unique : `vital_{metric_type}_{timestamp}_{value}`
   - Prévention des doublons via contrainte unique en base

4. **Extraction du user_id** :
   - Utilisation de `client_user_id` du payload Vital (notre UUID utilisateur)
   - Pas de `user_id` Vital (qui est l'ID interne de Vital)

## Format du webhook Vital

```json
{
  "event_type": "daily.data.steps.updated",
  "client_user_id": "006b5096-1983-44ae-9fc5-a8431c9f40be",
  "user_id": "6306b303-069b-48b6-a257-c6324161a7c8",
  "data": {
    "data": [
      {
        "value": 7639,
        "timestamp": "2026-01-26T00:00:00+00:00",
        "start": "2026-01-26T00:00:00+00:00",
        "end": "2026-01-27T00:00:00+00:00",
        "unit": "count"
      }
    ],
    "provider": {
      "name": "Oura",
      "slug": "oura"
    },
    "source": {
      "device_id": "...",
      "type": "ring"
    }
  }
}
```

## Test

```bash
curl -X POST http://localhost:9000/api/webhooks/vital \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "daily.data.steps.updated",
    "client_user_id": "006b5096-1983-44ae-9fc5-a8431c9f40be",
    "data": {
      "data": [
        {
          "value": 7639,
          "timestamp": "2026-01-26T00:00:00+00:00"
        }
      ]
    }
  }'
```

**Résultat attendu** :
```json
{
  "status": "success",
  "message": "Inserted 1 data points",
  "metric_type": "steps"
}
```

## Logs

```
INFO:__main__:Received Vital webhook: daily.data.steps.updated
INFO:httpx:HTTP Request: GET .../biometrics?select=id&user_id=eq...&source=eq.vital&source_event_id=eq... "HTTP/2 200 OK"
INFO:httpx:HTTP Request: POST .../biometrics "HTTP/2 201 Created"
INFO:__main__:Inserted 1 data points for user 006b5096-1983-44ae-9fc5-a8431c9f40be
INFO:     127.0.0.1:62718 - "POST /api/webhooks/vital HTTP/1.1" 200 OK
```

## Configuration Vital

L'URL webhook à configurer dans Vital Dashboard :
```
https://mckenzie-endarterial-tomi.ngrok-free.dev/api/webhooks/vital
```

## Prochaines étapes

- [ ] Ajouter la validation de signature Svix (headers `Svix-Signature`, `Svix-Timestamp`)
- [ ] Ajouter plus d'event types (activity, workout, body, nutrition)
- [ ] Gérer les webhooks de type `timeseries.*` (données continues)
- [ ] Ajouter des métriques de monitoring (taux de succès, latence)
