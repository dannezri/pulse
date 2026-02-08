# 🛠 Cahier des Charges : Le MVP v2.0 "Bio-Feedback IA"

## 📋 Vue d'Ensemble

**Nouveau MVP v2.0** : Corrélation simple entre données de flux (Oura API) et données de contexte (Apple Health) pour générer des insights personnalisés via LLM.

### Architecture Simplifiée

- **Données de Flux** : Oura API (HR, HRV, Sleep) → webhook → `biometrics`
- **Données de Contexte** : Apple Health (Nutrition, Médicaments, Symptômes, Selles) → scan local iOS → `daily_context`
- **Insight** : Corrélation "contexte récent" vs "biométrie récente" → LLM (GPT-4o) → `insights`

---

## Étape 1 : Flux de Données & Ingestion

### US 1 : En tant qu'utilisateur, je veux que mes données Oura (HR, HRV, Sleep) remontent automatiquement dans Pulse.

**Description** : Webhook Oura API vers backend FastAPI.

**Critères d'acceptation** :
- Oura API envoie un webhook avec `user_id` et données (HR, HRV, Sleep)
- Backend mappe `user_id` Oura → `user_id` Supabase via `external_identities`
- Données insérées dans `biometrics` avec idempotence (`source_event_id`)
- Si utilisateur non trouvé : webhook accepté (202) mais non traité

**Note technique** :
- Endpoint : `POST /api/webhooks/oura`
- Validation : Pydantic schema
- Idempotence : `source_event_id` unique par événement

### US 2 : En tant qu'utilisateur iOS, je veux synchroniser mon contexte Apple Health (Nutrition, Médicaments, Symptômes) en un clic.

**Description** : Scan local iOS via module natif `pulse-healthkit`, insertion dans `daily_context`.

**Critères d'acceptation** :
- Bouton "Synchroniser Contexte" visible uniquement sur iOS (device réel)
- Scan des 6 dernières heures depuis HealthKit
- Catégories : Nutrition (calories, carbs), Médicaments, Symptômes, Selles
- Insertion dans `daily_context` via Supabase client (avec session user, donc RLS)
- Notification : "Contexte synchronisé. Pulse analyse vos données…"
- Si simulateur : message "HealthKit indisponible sur simulateur"
- Si catégorie indisponible : retourner [] sans crash (best effort)

**Note technique** :
- Service : `mobile/src/services/HealthScanner.ts`
- Module natif : `mobile/pulse-healthkit` (Swift)
- Insertion : Supabase client avec session user (pas service role)

---

## Étape 2 : L'Intelligence Décisionnelle

### US 3 : En tant que système, je veux générer un insight quotidien en corrélant le contexte récent avec les biométriques récentes.

**Description** : Moteur de corrélation simple qui lit les 10 derniers `biometrics` et 10 derniers `daily_context`, puis appelle LLM.

**Critères d'acceptation** :
- Endpoint : `POST /api/cron/daily-insight` (protégé par `X-Cron-Secret`)
- Récupère 10 derniers `biometrics` (HR, HRV, Sleep)
- Récupère 10 derniers `daily_context` (nutrition, medication, symptoms, stool)
- Construit prompt concis pour LLM
- Appelle GPT-4o via `llm_client` (réponse JSON structurée)
- Insère dans `insights` avec `correlation_type` et `priority`
- Si données insuffisantes : retourne insight neutre "pas assez de données"

**Format LLM** :
```json
{
  "content": "HRV basse après repas riche en glucides → Réduire les glucides le soir",
  "correlation_type": "nutrition_hrv",
  "priority": 1
}
```

**Note technique** :
- Prompt système : instructions pour générer insights concis (< 150 caractères)
- Prompt utilisateur : données récentes formatées
- Garde-fous : si < 3 biometrics ET < 3 context → insight neutre

### US 4 : En tant qu'utilisateur mobile, je veux voir mon dernier insight généré.

**Description** : Endpoint protégé par JWT qui retourne le dernier insight.

**Critères d'acceptation** :
- Endpoint : `GET /api/insights/latest` (protégé par JWT Supabase)
- Vérifie token JWT, extrait `user_id`
- Récupère dernier insight via RPC `get_latest_insight`
- Mobile affiche l'insight dans le dashboard

**Note technique** :
- Authentification : Header `Authorization: Bearer <supabase-jwt-token>`
- Vérification : Via Supabase client (recommandé)

---

## Étape 3 : Interaction & Engagement

### US 5 : En tant qu'utilisateur, je veux recevoir une notification après synchronisation du contexte.

**Description** : Notification/toast après synchronisation réussie.

**Critères d'acceptation** :
- Après sync contexte : "Contexte synchronisé. Pulse analyse vos données…"
- Affichage du nombre d'entrées synchronisées
- Gestion des erreurs avec messages clairs

---

## 📊 Schéma de Données

### `biometrics`
- `user_id` (UUID)
- `metric_type` (hr, hrv, sleep_duration)
- `value` (FLOAT)
- `measured_at` (TIMESTAMP)
- `source` (oura, apple_health, etc.)
- `source_event_id` (TEXT, unique pour idempotence)
- `metadata` (JSONB)

### `daily_context`
- `user_id` (UUID)
- `category` (nutrition, medication, symptoms, stool)
- `details` (JSONB, ex: {"calories": 2000, "carbs": 250})
- `logged_at` (TIMESTAMP, date d'enregistrement dans HealthKit)
- `source` (AppleHealth, manual, etc.)

### `insights`
- `user_id` (UUID)
- `content` (TEXT, texte de l'insight)
- `correlation_type` (nutrition_hrv, medication_sleep, etc.)
- `priority` (1: Normal, 2: Urgent)
- `created_at` (TIMESTAMP)

### `external_identities`
- `supabase_user_id` (UUID)
- `provider_system` (oura, apple_health, etc.)
- `external_user_id` (TEXT, ID dans le système externe)
- Contrainte unique : `(supabase_user_id, provider_system, external_user_id)`

---

## 🔐 Sécurité

- **RLS** : Activé sur `daily_context` et `insights` (users ne voient que leurs données)
- **Service Role** : Utilisé uniquement côté backend (webhooks, cron)
- **JWT** : Vérification côté backend pour `/api/insights/latest`
- **Cron Secret** : Header `X-Cron-Secret` pour protéger `/api/cron/daily-insight`

---

## 🚀 Déploiement

### Backend
1. Configurer variables d'environnement (`.env`)
2. Lancer `python api_server_mvp.py`
3. Configurer cron externe pour `/api/cron/daily-insight`

### Mobile
1. `cd mobile && npm install`
2. `npx expo-doctor` (vérifier compatibilité)
3. Tester sur device iOS réel (HealthKit indisponible sur simulateur)

### Oura Webhook
1. Configurer webhook dans Oura API dashboard
2. URL : `https://your-api.com/api/webhooks/oura`
3. S'assurer que `external_identities` contient les mappings Oura → Supabase

---

*Version : 2.0.0*
*Date : 2024*
