# Séparation UI / Métier

- `src/components`: UI pure (props in, render out). Pas d'accès Supabase direct.
- `src/hooks`: logique métier (Supabase, transforms, validation, sync).
- `app/`: orchestration minimale (loading/error/navigation).
- `src/modules`: wrappers JS uniquement (requireNativeModule), jamais de natif.
- `pulse-healthkit/`: natif Expo Modules uniquement.
