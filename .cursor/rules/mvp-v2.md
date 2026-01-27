# Règles Cursor : MVP v2.0

## 📋 Checklist MVP v2.0

### Dépendances Expo/React Native
- ✅ **JAMAIS** `npm install <package>@latest` pour packages Expo/RN
- ✅ **TOUJOURS** `cd mobile && npx expo install <package>`
- ✅ Vérifier compatibilité Expo SDK 54 avant d'ajouter une dépendance
- ✅ Après chaque ajout de dépendance : `cd mobile && npx expo-doctor`

### Module Natif HealthKit
- ✅ **JAMAIS** utiliser `react-native-health` (incompatible Expo managed)
- ✅ Utiliser uniquement `mobile/pulse-healthkit` (module Expo natif Swift)
- ✅ Code natif : `mobile/pulse-healthkit/ios/` uniquement
- ✅ Wrapper JS : `mobile/src/modules/pulseHealthkit/` (pas de code natif)
- ✅ HealthKit : "best effort" - si catégorie indisponible, retourner [] sans crash

### Service Role Supabase
- ✅ **JAMAIS** utiliser Service Role côté mobile
- ✅ Mobile : utiliser Supabase client avec session user (JWT)
- ✅ Backend : Service Role OK pour webhooks/cron uniquement

### Architecture Mobile
- ✅ Routes `mobile/app/*` : orchestration minimale uniquement
- ✅ Logique métier : `mobile/src/hooks/` et `mobile/src/services/`
- ✅ UI pure : `mobile/src/components/` (pas de logique métier directe)
- ✅ Séparation claire : UI vs Business Logic

### Backend MVP v2.0
- ✅ Endpoints minimal : `/api/webhooks/vital`, `/api/cron/daily-insight`, `/api/insights/latest`
- ✅ Validation : Pydantic pour webhook Vital
- ✅ Mapping identity : Vital user_id → Supabase user_id via `external_identities`
- ✅ Idempotence : `source_event_id` unique pour éviter doublons
- ✅ JWT : Vérification via Supabase client (recommandé)
- ✅ Cron Secret : Header `X-Cron-Secret` pour protéger endpoint cron

### Node Version
- ✅ Respecter `engines.node >= 20.19.4` côté mobile
- ✅ Ne pas introduire de scripts nécessitant Node < 20

### Database
- ✅ Tables MVP : `biometrics`, `daily_context`, `insights`, `external_identities`
- ✅ RLS : Activé sur `daily_context` et `insights`
- ✅ Indexes : `(user_id, measured_at DESC)`, `(user_id, logged_at DESC)`, etc.

### Documentation
- ✅ Mettre à jour `ARCHITECTURE.md` et `MVP.md` si changement d'architecture
- ✅ Documenter les endpoints dans `backend/README.md`
- ✅ Documenter les catégories HealthKit disponibles/stubs

## 🚫 Interdictions

- ❌ `react-native-health` (incompatible Expo managed)
- ❌ Service Role Supabase côté mobile
- ❌ Logique métier dans composants UI
- ❌ Code natif dans `mobile/src/modules/` (uniquement dans `pulse-healthkit/`)
- ❌ Dépendances Expo/RN sans `npx expo install`
- ❌ Node < 20.19.4 pour scripts mobile

## ✅ Bonnes Pratiques

- ✅ HealthKit : retourner [] si catégorie indisponible (best effort)
- ✅ Simulateur iOS : message explicite "HealthKit indisponible sur simulateur"
- ✅ Webhook Vital : 202 Accepted si utilisateur non trouvé (webhook accepté mais non traité)
- ✅ Insights : retourner insight neutre si données insuffisantes
- ✅ Idempotence : utiliser `source_event_id` pour éviter doublons
- ✅ Validation : Pydantic pour payloads webhook
- ✅ JWT : vérifier via Supabase client (pas de vérification manuelle)
