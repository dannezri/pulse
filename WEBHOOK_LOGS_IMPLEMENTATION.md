# 📊 Implémentation des Logs de Webhooks Vital

## ✅ Résumé

Une page stylisée a été créée pour afficher tous les webhooks **reçus par le backend** depuis Vital API, avec logging automatique dans Supabase.

## 🎯 Fonctionnalités

### Backend
- ✅ Table `webhook_logs` dans Supabase pour stocker tous les webhooks
- ✅ Logger automatique dans `/api/webhooks/vital`
- ✅ Endpoint `/api/webhooks/logs` pour récupérer les logs d'un utilisateur
- ✅ Endpoint `/api/webhooks/logs/all` pour récupérer tous les logs (admin)
- ✅ RLS (Row Level Security) pour la sécurité des données

### Mobile
- ✅ Page "Webhooks" dans l'onglet navigation
- ✅ Affichage en temps réel des webhooks reçus
- ✅ Stats (succès, erreurs, temps moyen, total)
- ✅ Filtres par type (ALL, HISTORICAL, TIMESERIES, DAILY)
- ✅ Détails expandables (payload, response, etc.)
- ✅ Rafraîchissement automatique toutes les 10 secondes
- ✅ Pull-to-refresh manuel

## 📦 Fichiers créés/modifiés

### Backend

#### Nouveaux fichiers
1. **`database/migrations/012_add_webhook_logs.sql`**
   - Table `webhook_logs` avec tous les champs nécessaires
   - Index pour performances
   - RLS policies
   - Fonctions RPC : `get_user_webhook_logs`, `get_all_webhook_logs`

2. **`backend/webhook_logger.py`**
   - Classe `WebhookLogger` pour logger les webhooks
   - Méthodes : `log_webhook`, `update_webhook_log`, `log_webhook_complete`
   - Fonctions helper : `get_user_webhook_logs`, `get_all_webhook_logs`

#### Fichiers modifiés
3. **`backend/api_server_mvp.py`**
   - Import de `WebhookLogger`
   - Modification de `/api/webhooks/vital` pour logger automatiquement
   - Ajout de `/api/webhooks/logs` (récupérer logs utilisateur)
   - Ajout de `/api/webhooks/logs/all` (récupérer tous les logs)

### Mobile

#### Nouveaux fichiers
4. **`mobile/src/components/WebhookCard.tsx`**
   - Composant pour afficher un webhook
   - Icônes selon le type d'événement
   - Couleurs selon le statut
   - Détails expandables

#### Fichiers modifiés
5. **`mobile/app/(tabs)/requests.tsx`**
   - Complètement réécrit pour afficher les webhooks backend
   - Utilise `useQuery` pour récupérer les webhooks
   - Rafraîchissement automatique toutes les 10s
   - Filtres par type d'événement

6. **`mobile/app/(tabs)/_layout.tsx`**
   - Changé le titre de "Requêtes" à "Webhooks"

## 🗄️ Structure de la table `webhook_logs`

```sql
CREATE TABLE webhook_logs (
    id UUID PRIMARY KEY,
    endpoint TEXT NOT NULL,                    -- Ex: /api/webhooks/vital
    method TEXT NOT NULL DEFAULT 'POST',
    event_type TEXT,                           -- Ex: historical.data.water.created
    user_id TEXT,                              -- Vital user_id
    client_user_id UUID REFERENCES profiles(id), -- Supabase user_id
    payload JSONB NOT NULL,                    -- Payload complet
    status_code INT NOT NULL DEFAULT 200,
    response_message TEXT,
    duration_ms INT,                           -- Durée de traitement
    error TEXT,
    headers JSONB,
    received_at TIMESTAMPTZ NOT NULL,
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL
);
```

## 🔄 Flux de données

### 1. Réception d'un webhook

```
Vital API
  ↓
POST /api/webhooks/vital
  ↓
webhook_logger.log_webhook() → Supabase (webhook_logs)
  ↓
vital_handler_v2.process_webhook()
  ↓
webhook_logger.update_webhook_log() → Supabase (update status/duration)
  ↓
Response 200/400/500
```

### 2. Affichage dans l'app mobile

```
Mobile App
  ↓
useQuery → GET /api/webhooks/logs?user_id=xxx
  ↓
Supabase RPC get_user_webhook_logs()
  ↓
Retourne les webhooks de l'utilisateur
  ↓
WebhookCard (affichage)
```

## 🎨 Design

### Couleurs par type d'événement
- **HISTORICAL** : `#00BFFF` (bleu ciel) - Données historiques
- **TIMESERIES** : `#00FF41` (vert néon) - Données en temps réel
- **DAILY** : `#FFD700` (or) - Données quotidiennes

### Couleurs par statut
- **2xx (Succès)** : `#00FF41` (vert néon)
- **4xx (Client Error)** : `#FFD700` (or)
- **5xx (Server Error)** : `#FF4444` (rouge)

### Icônes
- **HISTORICAL** : 💾 Database
- **TIMESERIES** : 📊 Activity
- **DAILY** : ⚡ Zap
- **Success** : ✅ CheckCircle
- **Error** : ❌ XCircle

## 🚀 Utilisation

### Backend

#### Appliquer la migration
```bash
cd database/migrations
# Exécuter 012_add_webhook_logs.sql dans Supabase
```

#### Démarrer le serveur
```bash
cd backend
python api_server_mvp.py
```

Le logging est automatique. Chaque webhook reçu sur `/api/webhooks/vital` sera loggé.

### Mobile

#### Accéder à la page
1. Lancez l'app : `npm start` (depuis `/mobile`)
2. Allez dans l'onglet **"Webhooks"** (icône 📊 Activity)
3. Les webhooks apparaîtront automatiquement

#### Tester
1. Connectez un provider Vital (Fitbit, Oura, etc.)
2. Vital enverra des webhooks au backend
3. Les webhooks apparaîtront dans l'app mobile en temps réel

## 📊 Endpoints Backend

### 1. POST /api/webhooks/vital
Reçoit les webhooks Vital et les log automatiquement.

**Exemple de payload :**
```json
{
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
```

### 2. GET /api/webhooks/logs
Récupère les webhooks d'un utilisateur.

**Query params :**
- `user_id` : UUID utilisateur (optionnel si JWT fourni)
- `limit` : Nombre maximum de logs (default: 50)

**Headers :**
- `Authorization: Bearer <token>` (JWT Supabase)

**Exemple de réponse :**
```json
{
  "status": "success",
  "count": 10,
  "logs": [
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
      "payload": { ... }
    }
  ]
}
```

### 3. GET /api/webhooks/logs/all
Récupère tous les webhooks (admin only).

**Query params :**
- `limit` : Nombre maximum de logs (default: 100)

**Note :** Cet endpoint devrait être protégé par une authentification admin en production.

## 🔒 Sécurité

### RLS (Row Level Security)
- ✅ Les utilisateurs peuvent voir uniquement leurs propres webhooks
- ✅ Le service role peut tout faire (pour le backend)

### Policies
```sql
-- Users can view their own webhook logs
CREATE POLICY "Users can view their own webhook logs"
    ON webhook_logs
    FOR SELECT
    USING (client_user_id = auth.uid());

-- Service role can insert webhook logs
CREATE POLICY "Service role can insert webhook logs"
    ON webhook_logs
    FOR INSERT
    WITH CHECK (true);
```

## 📈 Performances

### Index
- ✅ `idx_webhook_logs_endpoint` : Sur `endpoint`
- ✅ `idx_webhook_logs_event_type` : Sur `event_type`
- ✅ `idx_webhook_logs_client_user_id` : Sur `client_user_id`
- ✅ `idx_webhook_logs_received_at` : Sur `received_at DESC`
- ✅ `idx_webhook_logs_status_code` : Sur `status_code`
- ✅ `idx_webhook_logs_user_time` : Composite sur `(client_user_id, received_at DESC)`

### Optimisations mobile
- ✅ Rafraîchissement automatique toutes les 10 secondes (configurable)
- ✅ Limite de 100 webhooks par requête
- ✅ Cache React Query
- ✅ Pull-to-refresh manuel

## 🧪 Test

### 1. Tester le logging backend

```bash
# Envoyer un webhook de test
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

### 2. Vérifier dans Supabase

```sql
SELECT * FROM webhook_logs ORDER BY received_at DESC LIMIT 10;
```

### 3. Vérifier dans l'app mobile

1. Ouvrez l'app
2. Allez dans l'onglet "Webhooks"
3. Le webhook devrait apparaître

## 💡 Conseils

### Développement
- ✅ Utilisez les logs pour débugger les problèmes de webhooks
- ✅ Vérifiez les temps de réponse pour optimiser les performances
- ✅ Filtrez par type pour trouver rapidement un webhook spécifique

### Production
- ⚠️ Ajoutez une authentification admin pour `/api/webhooks/logs/all`
- ⚠️ Considérez un système de nettoyage automatique des vieux logs (>30 jours)
- ⚠️ Monitorez les erreurs (status_code >= 400)

## 🔗 Liens utiles

- [Vital API Webhooks Documentation](https://docs.tryvital.io/wearables/webhooks)
- [Supabase RLS Documentation](https://supabase.com/docs/guides/auth/row-level-security)
- [React Query Documentation](https://tanstack.com/query/latest)

## ❓ Questions fréquentes

### Les webhooks sont-ils stockés indéfiniment ?
Oui, actuellement. Considérez un système de nettoyage automatique en production.

### Puis-je voir les webhooks d'autres utilisateurs ?
Non, grâce au RLS. Chaque utilisateur ne voit que ses propres webhooks.

### Comment tester sans Vital ?
Utilisez `curl` pour envoyer des webhooks de test (voir section Test).

### Les webhooks sont-ils rafraîchis automatiquement ?
Oui, toutes les 10 secondes. Vous pouvez aussi tirer pour rafraîchir manuellement.

## 🎉 Résultat

Une page professionnelle et stylisée qui permet de :
- 📊 Monitorer tous les webhooks Vital reçus en temps réel
- 🔍 Débugger les problèmes de webhooks facilement
- ⚡ Analyser les performances (temps de traitement)
- 🎨 Interface cohérente avec le thème Dark Zen de l'app
- 🚀 Prêt à l'emploi, logging automatique

---

**Bon développement ! 🚀**
