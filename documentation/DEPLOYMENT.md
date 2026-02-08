# Guide de Déploiement - MVP v2.0

## 📋 Vue d'Ensemble

Ce guide explique comment déployer et configurer le Nouveau MVP v2.0 :
- Backend FastAPI (webhooks Oura, génération insights)
- Mobile Expo (synchronisation contexte Apple Health)
- Base de données Supabase (migrations)

---

## 🗄️ Base de Données (Supabase)

### 1. Appliquer les Migrations

Les migrations sont dans `database/migrations/`. Appliquer dans l'ordre :

```bash
# Via Supabase Dashboard SQL Editor ou MCP
# Migration 009 : MVP v2.0
database/migrations/009_mvp_context_and_insights.sql
```

**Tables créées/mises à jour** :
- `daily_context` (nouvelle)
- `insights` (colonnes `correlation_type`, `content` ajoutées)
- `biometrics` (colonnes `metadata`, `measured_at` ajoutées)
- `external_identities` (déjà existante, utilisée pour mapping Oura)

**Fonctions RPC créées** :
- `get_recent_biometrics(user_id, limit)`
- `get_recent_daily_context(user_id, limit)`
- `get_latest_insight(user_id)`

### 2. Vérifier RLS

Les politiques RLS sont activées dans la migration. Vérifier dans Supabase Dashboard :
- `daily_context` : SELECT/INSERT pour `auth.uid() = user_id`
- `insights` : SELECT pour `auth.uid() = user_id`
- `biometrics` : INSERT via service role (backend), SELECT via policies si besoin

---

## 🚀 Backend (FastAPI)

### 1. Configuration

Créer un fichier `.env` dans `backend/` :

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# Cron Secret
CRON_SECRET=your-secret-here

# Port
PORT=9000
```

### 2. Installation

```bash
cd backend
pip install -r requirements.txt
```

### 3. Lancer Localement

```bash
python api_server_mvp.py
```

Le serveur démarre sur `http://0.0.0.0:9000`

### 4. Déploiement Production

**Options** :
- **Vercel** : `vercel deploy` (détecte FastAPI automatiquement)
- **Railway** : Connecter repo GitHub, Railway détecte Python
- **Render** : Créer Web Service, pointer vers `api_server_mvp.py`
- **AWS Lambda** : Utiliser Mangum adapter
- **Docker** : Créer `Dockerfile` (voir exemple ci-dessous)

**Variables d'environnement** : Configurer dans le dashboard du provider.

### 5. Configurer Webhook Oura

Dans le dashboard Oura API :
1. Aller dans "Webhooks"
2. Ajouter webhook : `https://your-api.com/api/webhooks/oura`
3. Sélectionner les événements : HR, HRV, Sleep
4. Tester le webhook

**Important** : S'assurer que `external_identities` contient les mappings :
```sql
INSERT INTO external_identities (supabase_user_id, provider_system, external_user_id, is_active)
VALUES ('supabase-uuid', 'oura', 'oura-user-id', true);
```

### 6. Configurer Cron Quotidien

**Option A : GitHub Actions** (gratuit)

Créer `.github/workflows/daily-insight.yml` :
```yaml
name: Daily Insight Generation

on:
  schedule:
    - cron: '0 8 * * *'  # 8h UTC chaque jour
  workflow_dispatch:  # Permet déclenchement manuel

jobs:
  generate-insights:
    runs-on: ubuntu-latest
    steps:
      - name: Generate Daily Insights
        run: |
          curl -X POST ${{ secrets.API_URL }}/api/cron/daily-insight \
            -H "Content-Type: application/json" \
            -H "X-Cron-Secret: ${{ secrets.CRON_SECRET }}" \
            -d '{"user_id": "user-uuid"}'
```

**Option B : Vercel Cron** (si backend sur Vercel)

Créer `vercel.json` :
```json
{
  "crons": [{
    "path": "/api/cron/daily-insight",
    "schedule": "0 8 * * *"
  }]
}
```

**Option C : Cron Externe** (EasyCron, cron-job.org, etc.)

Configurer une requête HTTP :
- URL : `https://your-api.com/api/cron/daily-insight`
- Method : POST
- Headers : `X-Cron-Secret: your-secret`
- Body : `{"user_id": "uuid"}`
- Schedule : Quotidien à 8h UTC

---

## 📱 Mobile (Expo)

### 1. Prérequis

- Node.js >= 20.19.4
- Expo CLI : `npm install -g expo-cli`
- iOS : Xcode (pour build natif)
- Android : Android Studio (optionnel pour MVP)

### 2. Installation

```bash
cd mobile
npm install
```

### 3. Configuration

Créer `mobile/.env` (optionnel, ou utiliser `app.json` pour config) :
```env
EXPO_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

### 4. Vérifier Dépendances

```bash
cd mobile
./scripts/check-deps.sh
# ou
npx expo-doctor
```

### 5. Lancer en Développement

```bash
# iOS (simulateur - HealthKit indisponible)
npm run ios

# iOS (device réel - requis pour HealthKit)
npm run ios -- --device

# Android
npm run android
```

### 6. Build Production

**iOS** :
```bash
cd mobile
eas build --platform ios
```

**Android** :
```bash
cd mobile
eas build --platform android
```

### 7. Configuration HealthKit (iOS)

Le module `pulse-healthkit` configure automatiquement :
- Capability HealthKit (via `app.plugin.js`)
- `NSHealthShareUsageDescription` dans Info.plist

**Important** : Ne pas activer "Verifiable Health Records" (incompatible personal team).

---

## 🧪 Tests

### Test Webhook Oura

```bash
curl -X POST http://localhost:9000/api/webhooks/oura \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "oura_user_123",
    "event_id": "test_event_001",
    "data": {
      "hr": [{"value": 72, "timestamp": "2024-01-15T10:00:00Z"}],
      "hrv": [{"value": 65, "timestamp": "2024-01-15T10:00:00Z"}],
      "sleep": {"duration_seconds": 28800, "start_time": "2024-01-15T22:00:00Z"}
    }
  }'
```

**Réponse attendue** :
- `200` : Succès (données insérées)
- `202` : Accepté mais utilisateur non trouvé (webhook accepté mais non traité)
- `400` : Payload invalide

### Test Cron Insight

```bash
curl -X POST http://localhost:9000/api/cron/daily-insight \
  -H "Content-Type: application/json" \
  -H "X-Cron-Secret: your-secret" \
  -d '{"user_id": "uuid"}'
```

**Réponse attendue** :
- `200` : Insight généré
- `401` : Secret invalide
- `400` : user_id manquant

### Test Insights Latest (JWT)

```bash
# Obtenir un token JWT depuis Supabase Auth
TOKEN="your-supabase-jwt-token"

curl -X GET http://localhost:9000/api/insights/latest \
  -H "Authorization: Bearer $TOKEN"
```

**Réponse attendue** :
- `200` : Insight trouvé
- `401` : Token invalide
- `404` : Aucun insight trouvé

### Test Mobile (iOS Device)

1. Lancer l'app sur device iOS réel
2. Cliquer "Synchroniser Contexte"
3. Autoriser HealthKit si demandé
4. Vérifier notification : "Contexte synchronisé. Pulse analyse vos données…"
5. Vérifier dans Supabase : données dans `daily_context`

---

## 🔍 Vérifications Post-Déploiement

### Backend
- [ ] Endpoint `/` retourne `{"status": "ok"}`
- [ ] Webhook Oura accepte les payloads valides
- [ ] Cron génère des insights (vérifier dans `insights` table)
- [ ] JWT fonctionne pour `/api/insights/latest`

### Database
- [ ] Table `daily_context` existe avec RLS
- [ ] Table `insights` a colonnes `correlation_type` et `content`
- [ ] Table `biometrics` a colonnes `metadata` et `measured_at`
- [ ] Fonctions RPC `get_recent_*` fonctionnent

### Mobile
- [ ] `npx expo-doctor` passe
- [ ] Bouton "Synchroniser Contexte" visible sur iOS device
- [ ] HealthKit permissions demandées correctement
- [ ] Données insérées dans `daily_context` après sync

---

## 📝 Notes Importantes

### HealthKit sur Simulateur
- HealthKit est **indisponible** sur simulateur iOS
- Tester uniquement sur device iOS réel
- L'app affiche un message explicite si simulateur détecté

### Mapping Identity Oura
- Oura `user_id` doit être présent dans `external_identities` avec `provider_system="oura"`
- Si absent : webhook accepté (202) mais non traité
- Créer le mapping lors de la connexion Oura dans l'app

### Idempotence
- Les webhooks Oura utilisent `source_event_id` pour éviter doublons
- Si `event_id` fourni : utilisé comme `source_event_id`
- Sinon : généré automatiquement (hash du payload)

### Données Insuffisantes
- Si < 3 biometrics ET < 3 context : insight neutre retourné
- Message : "Pas assez de données pour générer un insight"

---

*Version : 2.0.0*
*Dernière mise à jour : 2024*
