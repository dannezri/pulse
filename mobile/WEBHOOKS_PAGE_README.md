# 📊 Page Webhooks Vital - Guide Rapide

## ✅ Implémentation Complète

Une page stylisée a été créée pour afficher tous les **webhooks reçus par le backend** depuis Vital API, avec logging automatique dans Supabase.

## 🚀 Accès rapide

### Dans l'application
1. Lancez l'app : `npm start` (depuis `/mobile`)
2. Allez dans l'onglet **"Webhooks"** (icône 📊 Activity)
3. Les webhooks apparaîtront automatiquement

### Navigation
```
┌─────┬─────────┬────────────┬─────────┬───────────┬────────┐
│Pulse│ Sources │Médicaments │Webhooks │Historique │ Profil │
│ 🏠  │   🔗    │     💊     │   📊    │    📜     │   👤   │
└─────┴─────────┴────────────┴─────────┴───────────┴────────┘
                               ↑ Affiche les webhooks Vital reçus
```

## 🎨 Fonctionnalités

### 1. Affichage des webhooks
- ✅ Tous les webhooks Vital reçus par le backend
- ✅ Icônes selon le type d'événement (HISTORICAL, TIMESERIES, DAILY)
- ✅ Couleurs selon le statut (succès, erreur)
- ✅ Détails expandables (payload complet, response, etc.)

### 2. Stats en temps réel
- ✅ Nombre de succès (vert)
- ✅ Nombre d'erreurs (rouge)
- ✅ Temps moyen de traitement (bleu)
- ✅ Total de webhooks (or)

### 3. Filtres
- ✅ Filtrer par type d'événement (ALL, HISTORICAL, TIMESERIES, DAILY)
- ✅ Rafraîchissement automatique toutes les 10 secondes
- ✅ Pull-to-refresh manuel

## 📦 Fichiers créés

### Backend
```
backend/
├── webhook_logger.py                      # Logger pour les webhooks
└── api_server_mvp.py                      # (modifié) Logging automatique

database/migrations/
└── 012_add_webhook_logs.sql               # Table webhook_logs
```

### Mobile
```
mobile/
├── src/components/
│   └── WebhookCard.tsx                    # Composant UI pour un webhook
└── app/(tabs)/
    ├── requests.tsx                       # (réécrit) Page webhooks
    └── _layout.tsx                        # (modifié) Titre "Webhooks"
```

## 🗄️ Backend

### 1. Appliquer la migration

```bash
# Dans Supabase SQL Editor
# Exécuter: database/migrations/012_add_webhook_logs.sql
```

### 2. Démarrer le serveur

```bash
cd backend
python api_server_mvp.py
```

Le logging est **automatique**. Chaque webhook reçu sur `/api/webhooks/vital` sera loggé dans Supabase.

### 3. Endpoints

#### POST /api/webhooks/vital
Reçoit les webhooks Vital et les log automatiquement.

#### GET /api/webhooks/logs
Récupère les webhooks d'un utilisateur.
- Query: `user_id`, `limit`
- Header: `Authorization: Bearer <token>`

#### GET /api/webhooks/logs/all
Récupère tous les webhooks (admin).

## 📱 Mobile

### Récupération des webhooks

L'app utilise `useQuery` pour récupérer les webhooks depuis le backend :

```typescript
const { data, isLoading, error, refetch } = useQuery({
  queryKey: ['webhooks'],
  queryFn: async () => {
    const userId = await storage.getUserId();
    const token = await storage.getAccessToken();
    
    const response = await fetch(
      `${API_URL}/api/webhooks/logs?user_id=${userId}&limit=100`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    );
    
    const result = await response.json();
    return result.logs;
  },
  refetchInterval: 10000, // Rafraîchir toutes les 10 secondes
});
```

## 🎨 Design

### Couleurs par type d'événement
- **HISTORICAL** : 🔵 Bleu ciel (`#00BFFF`) - Données historiques
- **TIMESERIES** : 🟢 Vert néon (`#00FF41`) - Données en temps réel
- **DAILY** : 🟡 Or (`#FFD700`) - Données quotidiennes

### Couleurs par statut
- **2xx (Succès)** : 🟢 Vert néon (`#00FF41`)
- **4xx (Client Error)** : 🟡 Or (`#FFD700`)
- **5xx (Server Error)** : 🔴 Rouge (`#FF4444`)

### Icônes
- **HISTORICAL** : 💾 Database
- **TIMESERIES** : 📊 Activity
- **DAILY** : ⚡ Zap
- **Success** : ✅ CheckCircle
- **Error** : ❌ XCircle

## 🧪 Test

### 1. Envoyer un webhook de test

```bash
curl -X POST http://localhost:9000/api/webhooks/vital \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "historical.data.water.created",
    "user_id": "vital_user_id",
    "client_user_id": "your-supabase-uuid",
    "team_id": "team_id",
    "data": {
      "provider": "fitbit",
      "start_date": "2025-12-29T00:00:00+00:00",
      "end_date": "2026-01-27T23:59:59+00:00",
      "is_final": true
    }
  }'
```

### 2. Vérifier dans l'app

1. Ouvrez l'app mobile
2. Allez dans l'onglet "Webhooks"
3. Le webhook devrait apparaître dans les 10 secondes (ou tirez pour rafraîchir)

### 3. Vérifier dans Supabase

```sql
SELECT * FROM webhook_logs ORDER BY received_at DESC LIMIT 10;
```

## 📊 Exemple de webhook

```json
{
  "id": "uuid",
  "endpoint": "/api/webhooks/vital",
  "method": "POST",
  "event_type": "historical.data.water.created",
  "status_code": 200,
  "response_message": "Webhook processed",
  "duration_ms": 123,
  "error": null,
  "received_at": "2026-01-27T10:00:00Z",
  "processed_at": "2026-01-27T10:00:00.123Z",
  "payload": {
    "event_type": "historical.data.water.created",
    "user_id": "vital_user_id",
    "client_user_id": "supabase_uuid",
    "team_id": "team_id",
    "data": {
      "provider": "fitbit",
      "start_date": "2025-12-29T00:00:00+00:00",
      "end_date": "2026-01-27T23:59:59+00:00",
      "is_final": true
    }
  }
}
```

## 🔒 Sécurité

### RLS (Row Level Security)
- ✅ Les utilisateurs peuvent voir uniquement leurs propres webhooks
- ✅ Le service role peut tout faire (pour le backend)

### Authentification
- ✅ JWT Supabase requis pour `/api/webhooks/logs`
- ✅ Pas d'authentification pour `/api/webhooks/vital` (webhook public)

## 📈 Performances

### Backend
- ✅ Index sur `endpoint`, `event_type`, `client_user_id`, `received_at`, `status_code`
- ✅ Index composite sur `(client_user_id, received_at DESC)`

### Mobile
- ✅ Rafraîchissement automatique toutes les 10 secondes
- ✅ Limite de 100 webhooks par requête
- ✅ Cache React Query
- ✅ Pull-to-refresh manuel

## 💡 Conseils

### Développement
- ✅ Utilisez les logs pour débugger les problèmes de webhooks
- ✅ Vérifiez les temps de traitement pour optimiser les performances
- ✅ Filtrez par type pour trouver rapidement un webhook spécifique

### Production
- ⚠️ Ajoutez une authentification admin pour `/api/webhooks/logs/all`
- ⚠️ Considérez un système de nettoyage automatique des vieux logs (>30 jours)
- ⚠️ Monitorez les erreurs (status_code >= 400)

## 📚 Documentation

- **[WEBHOOK_LOGS_IMPLEMENTATION.md](../WEBHOOK_LOGS_IMPLEMENTATION.md)** : Documentation complète
- **[Vital API Webhooks](https://docs.tryvital.io/wearables/webhooks)** : Documentation Vital

## ❓ Questions fréquentes

### Les webhooks sont-ils stockés indéfiniment ?
Oui, actuellement. Considérez un système de nettoyage automatique en production.

### Puis-je voir les webhooks d'autres utilisateurs ?
Non, grâce au RLS. Chaque utilisateur ne voit que ses propres webhooks.

### Comment tester sans Vital ?
Utilisez `curl` pour envoyer des webhooks de test (voir section Test).

### Les webhooks sont-ils rafraîchis automatiquement ?
Oui, toutes les 10 secondes. Vous pouvez aussi tirer pour rafraîchir manuellement.

### Quelle est la différence avec la page "Requêtes" originale ?
- **Ancienne page** : Requêtes **sortantes** de l'app mobile (fetch, API calls)
- **Nouvelle page** : Webhooks **entrants** reçus par le backend depuis Vital

## 🎉 Résultat

Une page professionnelle et stylisée qui permet de :
- 📊 Monitorer tous les webhooks Vital reçus en temps réel
- 🔍 Débugger les problèmes de webhooks facilement
- ⚡ Analyser les performances (temps de traitement)
- 🎨 Interface cohérente avec le thème Dark Zen de l'app
- 🚀 Prêt à l'emploi, logging automatique

---

**Bon développement ! 🚀**
