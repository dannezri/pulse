# Backend Legacy - Archivé

Ce dossier contient le code legacy de l'ancienne architecture (health_profiles, baselines, anomalies, normalizer, Open Wearables).

## Fichiers Archivés

- `data_normalizer.py` : Normalisation avec baselines, anomalies, versioning (legacy)
- `main.py` : DataPipeline avec Open Wearables (legacy)
- `insight_generator.py` : Génération insights basée sur health_profiles (legacy)
- `webhook_receiver.py` : Récepteur webhook Open Wearables (legacy)
- `open_wearables_integration.py` : Client Open Wearables (legacy)
- `workers/` : Workers Celery pour normalisation (legacy)

## Nouveau MVP v2.0

Le nouveau MVP utilise :
- `api_server_mvp.py` : API minimal (Vital webhook, cron insight, insights latest)
- `vital_webhook.py` : Gestionnaire webhook Vital (validation, mapping identity, idempotence)
- `correlation_engine.py` : Corrélation simple (biometrics + daily_context → insight)
- `llm_client.py` : Client LLM (GPT-4o)

**Tables utilisées** :
- `biometrics` : Données de flux (HR, HRV, Sleep) depuis Vital
- `daily_context` : Données de contexte (Nutrition, Médicaments, Symptômes) depuis Apple Health
- `insights` : Insights générés par corrélation

**Tables legacy** (conservées mais non utilisées) :
- `health_profiles` : Profils de santé normalisés (legacy)
- `meals` : Journal alimentaire via IA Vision (legacy)
