RÈGLES DÉPENDANCES / NATIF (Expo SDK 54)
- Toute dépendance RN/Expo doit être installée via `cd mobile && npx expo install <pkg>`.
- Interdit: `npm i <pkg>@latest` (risque incompatibilité Expo).
- Interdit: `react-native-health` (nécessite config native hors Expo managed).
- Natif iOS/Android uniquement dans `mobile/pulse-healthkit/`.
- `mobile/src/modules/*` = wrappers TS/JS uniquement, pas de Swift/Kotlin.
- Mobile n’utilise jamais SUPABASE_SERVICE_KEY.
