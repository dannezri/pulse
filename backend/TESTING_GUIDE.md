# Guide de Test - Simulation et Vérification du Flux Complet

Ce guide explique comment simuler une action et vérifier que tout le chemin fonctionne correctement dans le système Bio-Feedback IA.

## 📋 Vue d'ensemble du flux

```
Open Wearables Webhook
    ↓
Webhook Handler (webhook_handler.py)
    ↓
Traitement des données (sleep, HR, HRV, steps)
    ↓
Sauvegarde dans Supabase (biometrics table)
    ↓
Normalisation des données (data_normalizer.py)
    ↓
Calcul des baselines
    ↓
Création du profil de santé
    ↓
Sauvegarde du profil (health_profiles table)
```

## 🧪 Méthodes de test

### 1. Test complet du flux (Recommandé)

Ce test vérifie tout le chemin de bout en bout, de la réception du webhook jusqu'à la création du profil de santé.

```bash
cd backend
python test_webhook_flow.py
```

**Ce que fait ce script :**
- ✅ Vérifie la configuration (variables d'environnement)
- ✅ Initialise tous les clients (Open Wearables, Supabase, Normalizer)
- ✅ Vérifie que l'utilisateur existe dans Supabase
- ✅ Crée un payload de webhook de test avec des données réalistes
- ✅ Traite le webhook via le handler
- ✅ Vérifie que les biométriques sont sauvegardées dans Supabase
- ✅ Vérifie que le profil de santé est créé correctement

**Prérequis :**
- Fichier `.env` configuré avec :
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_KEY`
  - `OPEN_WEARABLES_BASE_URL` (optionnel, par défaut: http://localhost:8080)
  - `OPEN_WEARABLES_API_KEY` (optionnel)

**Exemple d'utilisation :**
```bash
$ python test_webhook_flow.py

════════════════════════════════════════════════════════════
TEST COMPLET DU FLUX WEBHOOK
════════════════════════════════════════════════════════════

═══ Étape 0: Vérification de la configuration ═══
✅ Configuration chargée

Entrez l'ID utilisateur Open Wearables à tester: user-123

═══ Étape 1: Initialisation des clients ═══
✅ Clients initialisés

═══ Étape 2: Vérification de l'utilisateur ═══
✅ Utilisateur trouvé: 550e8400-e29b-41d4-a716-446655440000

═══ Étape 3: Création du payload de test ═══
✅ Payload de test créé

═══ Étape 4: Traitement du webhook ═══
✅ Webhook traité avec succès

═══ Étape 5: Vérification des biométriques sauvegardées ═══
✅ Données biométriques trouvées: 5 types de métriques

═══ Étape 6: Vérification du profil de santé ═══
✅ Profil de santé trouvé

✅ TEST RÉUSSI - Tous les composants fonctionnent correctement
```

### 2. Test des composants individuels

Pour tester uniquement la logique de normalisation sans Supabase :

```bash
python test_webhook_flow.py --components
```

### 3. Test via l'API HTTP

Cette méthode simule un appel webhook externe comme si Open Wearables envoyait réellement les données.

**Étape 1 : Démarrer l'API**
```bash
python api_server.py
```

L'API démarre sur `http://localhost:9000` (ou un port libre).

**Étape 2 : Tester le webhook**
```bash
# Dans un autre terminal
python test_api_endpoint.py webhook
```

**Étape 3 : Tester la synchronisation manuelle**
```bash
python test_api_endpoint.py sync
```

**Étape 4 : Récupérer le profil de santé**
```bash
python test_api_endpoint.py profile
```

### 4. Test manuel avec curl

Vous pouvez aussi tester directement avec `curl` :

```bash
# Test du webhook
curl -X POST http://localhost:9000/api/webhooks/wearables \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "timestamp": "2024-01-15T10:00:00Z",
    "data": {
      "sleep": {
        "duration_seconds": 28800,
        "score": 85
      },
      "hr": [{"value": 65, "timestamp": "2024-01-15T07:00:00Z"}],
      "hrv": [{"value": 45, "timestamp": "2024-01-15T07:00:00Z"}],
      "steps": [{"value": 5000, "timestamp": "2024-01-15T14:00:00Z"}]
    }
  }'

# Test de synchronisation
curl -X POST http://localhost:9000/sync/user-123

# Récupération du profil de santé
curl http://localhost:9000/health-profile/{supabase_user_id}
```

## 🔍 Vérification manuelle dans Supabase

Après avoir exécuté les tests, vous pouvez vérifier directement dans Supabase :

### 1. Vérifier les biométriques

```sql
-- Voir toutes les biométriques d'aujourd'hui pour un utilisateur
SELECT 
  metric_type,
  value,
  recorded_at,
  source,
  raw_data
FROM biometrics
WHERE user_id = 'votre-user-id'
  AND DATE(recorded_at) = CURRENT_DATE
ORDER BY recorded_at DESC;
```

### 2. Vérifier le profil de santé

```sql
-- Voir le dernier profil de santé
SELECT 
  user_id,
  date,
  profile_data
FROM health_profiles
WHERE user_id = 'votre-user-id'
ORDER BY date DESC
LIMIT 1;
```

### 3. Vérifier le mapping utilisateur

```sql
-- Vérifier que l'utilisateur est bien mappé
SELECT 
  id,
  open_wearables_user_id,
  health_goal,
  baseline_hrv,
  baseline_resting_hr
FROM profiles
WHERE open_wearables_user_id = 'user-123';
```

## 🐛 Débogage

### Problème : "User not found"

**Cause :** L'utilisateur n'existe pas dans la table `profiles` avec le bon `open_wearables_user_id`.

**Solution :**
1. Vérifiez que l'utilisateur existe dans Supabase
2. Vérifiez que le champ `open_wearables_user_id` est correctement rempli

```sql
-- Créer ou mettre à jour un utilisateur de test
INSERT INTO profiles (id, open_wearables_user_id, health_goal)
VALUES (
  gen_random_uuid(),
  'user-123',
  'energy'
)
ON CONFLICT (open_wearables_user_id) DO UPDATE
SET health_goal = EXCLUDED.health_goal;
```

### Problème : "Missing required environment variables"

**Cause :** Les variables d'environnement ne sont pas configurées.

**Solution :**
1. Créez un fichier `.env` dans le dossier `backend/`
2. Ajoutez les variables nécessaires :

```env
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_SERVICE_KEY=votre-service-key
OPEN_WEARABLES_BASE_URL=http://localhost:8080
OPEN_WEARABLES_API_KEY=votre-api-key (optionnel)
```

### Problème : "Error inserting biometric"

**Cause :** Problème de connexion à Supabase ou structure de table incorrecte.

**Solution :**
1. Vérifiez que Supabase est accessible
2. Vérifiez que la table `biometrics` existe et a la bonne structure
3. Vérifiez les logs pour plus de détails

### Problème : Les données ne sont pas normalisées correctement

**Cause :** Format des données d'entrée différent de celui attendu.

**Solution :**
1. Vérifiez le format du payload dans les logs
2. Ajustez le format dans `create_test_webhook_payload()` si nécessaire
3. Vérifiez que `data_normalizer.py` gère bien tous les cas

## 📊 Structure des données de test

Le script de test génère des données réalistes :

- **Sommeil :** 8 heures avec score de qualité 85
- **Fréquence cardiaque :** 3 points de mesure (65, 72, 68 bpm)
- **HRV :** 2 points de mesure (45, 48 ms)
- **Pas :** 3 points de mesure (2500, 5000, 8500 pas)

Vous pouvez modifier ces valeurs dans `test_webhook_flow.py` pour tester différents scénarios.

## ✅ Checklist de vérification

Avant de considérer que tout fonctionne :

- [ ] Le webhook est reçu et parsé correctement
- [ ] Les données sont sauvegardées dans `biometrics`
- [ ] Les données sont normalisées correctement
- [ ] Les baselines sont calculées (si données historiques disponibles)
- [ ] Le profil de santé est créé avec toutes les sections :
  - [ ] `current_metrics`
  - [ ] `baselines`
  - [ ] `anomalies` (si détectées)
  - [ ] `context`
- [ ] Le profil de santé est sauvegardé dans `health_profiles`

## 🚀 Prochaines étapes

Une fois que les tests passent :

1. **Intégration avec Open Wearables réel :** Configurez les webhooks dans Open Wearables pour pointer vers votre endpoint
2. **Monitoring :** Ajoutez des logs et métriques pour surveiller le système en production
3. **Tests d'intégration :** Créez des tests automatisés pour CI/CD
4. **Tests de charge :** Testez le système avec de nombreux webhooks simultanés

## 📝 Notes

- Les tests utilisent des données de test, pas de vraies données utilisateur
- Les timestamps sont générés dynamiquement (aujourd'hui/hier)
- Les tests ne modifient pas les données existantes, ils ajoutent de nouvelles entrées
- Pour nettoyer les données de test, supprimez-les manuellement dans Supabase
