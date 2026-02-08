# FatSecret Integration - Guide Complet

## 📋 Vue d'ensemble

Cette intégration permet de récupérer les données alimentaires (Food Diary / Food Entries) depuis FatSecret et de les stocker dans Supabase.

**Architecture:**
- OAuth 1.0a (3-legged) pour l'authentification utilisateur
- Endpoints API FastAPI pour le flow OAuth depuis l'app mobile
- Script de synchronisation automatique (cron/job)
- Tables Supabase pour stocker les tokens et les entrées alimentaires

---

## 🔐 Configuration FatSecret

### 1. Créer une application FatSecret

1. Aller sur https://platform.fatsecret.com/api/
2. Créer une nouvelle application
3. Obtenir vos credentials:
   - **Consumer Key**
   - **Consumer Secret**

### 2. Variables d'environnement

Ajouter dans votre fichier `.env`:

```bash
# FatSecret API Credentials
FATSECRET_CONSUMER_KEY=your_consumer_key_here
FATSECRET_CONSUMER_SECRET=your_consumer_secret_here
```

---

## 📊 Schéma de base de données

### Migration SQL

La migration `018_fatsecret_integration.sql` crée deux tables:

#### Table `fatsecret_connections`

Stocke les tokens OAuth pour chaque utilisateur:

```sql
CREATE TABLE fatsecret_connections (
  user_id UUID PRIMARY KEY REFERENCES profiles(id),
  oauth_token TEXT NOT NULL,
  oauth_token_secret TEXT NOT NULL,
  connected_at TIMESTAMPTZ DEFAULT NOW(),
  last_synced_date DATE NULL,
  is_active BOOLEAN DEFAULT TRUE,
  metadata JSONB DEFAULT '{}'
);
```

#### Table `food_entries_raw`

Stocke les entrées alimentaires brutes:

```sql
CREATE TABLE food_entries_raw (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES profiles(id),
  fatsecret_food_entry_id BIGINT NOT NULL,
  entry_date DATE NOT NULL,
  meal TEXT NOT NULL, -- breakfast/lunch/dinner/other
  description TEXT,
  food_id BIGINT,
  serving_id BIGINT,
  number_of_units NUMERIC,
  raw JSONB NOT NULL,
  inserted_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, fatsecret_food_entry_id)
);
```

### Appliquer la migration

```bash
# Se connecter à Supabase et exécuter la migration
psql -h db.YOUR_PROJECT.supabase.co -U postgres -d postgres < database/migrations/018_fatsecret_integration.sql
```

Ou via l'interface Supabase SQL Editor.

---

## 🚀 Installation

### 1. Installer les dépendances

```bash
cd backend
pip install -r requirements.txt
```

Packages clés:
- `requests-oauthlib>=1.3.1` - OAuth 1.0a pour FatSecret
- `supabase>=2.0.0` - Client Supabase
- `fastapi>=0.104.0` - API Server

### 2. Vérifier la configuration

```bash
python -c "from fatsecret_client import get_fatsecret_client; print('✓ FatSecret client OK')"
```

---

## 🔄 Flow OAuth - Connecter un utilisateur

### Option A: Depuis l'app mobile (Recommandé)

L'app mobile utilise les endpoints API pour gérer le flow OAuth:

#### 1. Démarrer le flow OAuth

```http
POST /api/fatsecret/connect/start
Authorization: Bearer <JWT_TOKEN>
```

Réponse:
```json
{
  "status": "success",
  "auth_url": "https://authentication.fatsecret.com/oauth/authorize?oauth_token=...",
  "request_token": "...",
  "request_token_secret": "..."
}
```

#### 2. L'utilisateur ouvre `auth_url` dans le navigateur

- Se connecte avec son compte FatSecret
- Autorise l'application
- Obtient un code de vérification (verifier)

#### 3. Compléter le flow OAuth

```http
POST /api/fatsecret/connect/complete
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "request_token": "...",
  "request_token_secret": "...",
  "verifier": "CODE_FROM_FATSECRET"
}
```

Réponse:
```json
{
  "status": "success",
  "message": "FatSecret connected successfully"
}
```

### Option B: Script en ligne de commande

Pour tester ou connecter des utilisateurs manuellement:

```bash
cd backend
python setup_fatsecret.py
```

Le script vous guide étape par étape:
1. Choisir "Connecter un nouvel utilisateur"
2. Entrer l'UUID de l'utilisateur Supabase
3. Ouvrir l'URL d'autorisation dans le navigateur
4. Entrer le code de vérification obtenu

---

## 📡 Endpoints API disponibles

### 1. Vérifier le statut de connexion

```http
GET /api/fatsecret/status
Authorization: Bearer <JWT_TOKEN>
```

Réponse:
```json
{
  "connected": true,
  "connected_at": "2026-01-29T10:30:00Z",
  "last_synced_date": "2026-01-29"
}
```

### 2. Récupérer les entrées alimentaires

```http
GET /api/fatsecret/food-entries?start_date=2026-01-20&end_date=2026-01-29
Authorization: Bearer <JWT_TOKEN>
```

Réponse:
```json
{
  "status": "success",
  "entries": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "fatsecret_food_entry_id": 123456789,
      "entry_date": "2026-01-29",
      "meal": "breakfast",
      "description": "Oatmeal with berries",
      "food_id": 12345,
      "serving_id": 67890,
      "number_of_units": 1.0,
      "raw": { ... },
      "inserted_at": "2026-01-29T11:00:00Z"
    }
  ]
}
```

### 3. Déconnecter FatSecret

```http
DELETE /api/fatsecret/disconnect
Authorization: Bearer <JWT_TOKEN>
```

Réponse:
```json
{
  "status": "success",
  "message": "FatSecret disconnected"
}
```

---

## 🔄 Synchronisation automatique

### Script de synchronisation

Le script `sync_fatsecret_food_entries.py` synchronise les données pour tous les utilisateurs connectés:

```bash
cd backend

# Synchroniser les 7 derniers jours (défaut)
python sync_fatsecret_food_entries.py

# Synchroniser les 30 derniers jours
python sync_fatsecret_food_entries.py --days-back 30

# Synchroniser un utilisateur spécifique
python sync_fatsecret_food_entries.py --user-id "c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd"
```

### Configuration d'un Cron Job

Pour automatiser la synchronisation quotidienne:

#### Linux/macOS - Crontab

```bash
crontab -e
```

Ajouter:
```cron
# Sync FatSecret tous les jours à 5h du matin
0 5 * * * cd /path/to/Pulse/backend && /path/to/python sync_fatsecret_food_entries.py >> /tmp/fatsecret_sync.log 2>&1
```

#### macOS - Launchd (Recommandé)

Créer `~/Library/LaunchAgents/com.pulse.fatsecret-sync.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.pulse.fatsecret-sync</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/python</string>
        <string>/path/to/Pulse/backend/sync_fatsecret_food_entries.py</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/path/to/Pulse/backend</string>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>5</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    
    <key>StandardOutPath</key>
    <string>/tmp/fatsecret_sync.log</string>
    
    <key>StandardErrorPath</key>
    <string>/tmp/fatsecret_sync_error.log</string>
</dict>
</plist>
```

Charger:
```bash
launchctl load ~/Library/LaunchAgents/com.pulse.fatsecret-sync.plist
```

---

## 🧪 Tests et validation

### 1. Tester le client FatSecret

```bash
cd backend
python -c "
from fatsecret_client import get_fatsecret_client
import datetime as dt

# Avec les tokens d'un utilisateur
client = get_fatsecret_client(
    oauth_token='YOUR_TOKEN',
    oauth_token_secret='YOUR_SECRET'
)

# Récupérer les entrées d'aujourd'hui
data = client.get_food_entries_for_date(dt.date.today())
print(data)
"
```

### 2. Vérifier les données dans Supabase

```sql
-- Voir les connexions actives
SELECT user_id, connected_at, last_synced_date 
FROM fatsecret_connections 
WHERE is_active = true;

-- Voir les entrées alimentaires récentes
SELECT user_id, entry_date, meal, description, inserted_at
FROM food_entries_raw
ORDER BY entry_date DESC, inserted_at DESC
LIMIT 20;

-- Statistiques par utilisateur
SELECT 
  user_id,
  COUNT(*) as total_entries,
  MIN(entry_date) as first_entry,
  MAX(entry_date) as last_entry
FROM food_entries_raw
GROUP BY user_id;
```

### 3. Tester les endpoints API

```bash
# Démarrer le serveur API
cd backend
python api_server.py

# Dans un autre terminal
# Obtenir un JWT token (voir jwt_auth.py ou get_jwt_token.py)
JWT_TOKEN="your_jwt_token_here"

# Vérifier le statut
curl -X GET http://localhost:9000/api/fatsecret/status \
  -H "Authorization: Bearer $JWT_TOKEN"

# Récupérer les entrées
curl -X GET "http://localhost:9000/api/fatsecret/food-entries?start_date=2026-01-20" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

## 📝 Points clés de l'API FatSecret

### Format de date spécial

FatSecret utilise un format de date spécifique: **nombre de jours depuis le 1er janvier 1970**.

Le client le gère automatiquement:

```python
from fatsecret_client import FatSecretClient
import datetime as dt

# Convertir une date en jours depuis epoch
days = FatSecretClient.date_to_days_since_epoch(dt.date(2026, 1, 29))
# days = 20481

# Convertir des jours depuis epoch en date
date = FatSecretClient.days_since_epoch_to_date(20481)
# date = 2026-01-29
```

### Types de repas (meal)

Les valeurs possibles pour le champ `meal`:
- `breakfast` - Petit-déjeuner
- `lunch` - Déjeuner
- `dinner` - Dîner
- `snack` - Collation
- `other` - Autre

### Structure de réponse API

Réponse typique de `food-entries/v1`:

```json
{
  "food_entries": {
    "food_entry": [
      {
        "food_entry_id": "123456789",
        "food_id": "12345",
        "serving_id": "67890",
        "food_entry_description": "Oatmeal with berries",
        "meal": "breakfast",
        "date_int": "20481",
        "number_of_units": "1.0"
      }
    ]
  }
}
```

Note: Si une seule entrée, `food_entry` est un objet (pas un tableau).

---

## 🔧 Troubleshooting

### Erreur "Invalid signature"

**Cause:** OAuth 1.0a est très strict sur les signatures.

**Solutions:**
1. Vérifier l'heure système du serveur (doit être synchronisée)
2. S'assurer que les credentials (consumer key/secret) sont corrects
3. Utiliser `requests-oauthlib` (géré automatiquement par le client)
4. Éviter les proxies qui modifient les requêtes

### "Request token already used"

**Cause:** Un request token ne peut être utilisé qu'une seule fois.

**Solution:** Recommencer le flow OAuth depuis le début (étape 1).

### "Token expired"

**Cause:** Le token d'accès FatSecret a expiré.

**Solution:** L'utilisateur doit se reconnecter (flow OAuth complet).

### "No food entries found"

**Cause:** L'utilisateur n'a pas d'entrées pour cette date, ou la date est invalide.

**Solutions:**
1. Vérifier que la date est valide (format YYYY-MM-DD)
2. Vérifier que l'utilisateur a bien des données dans FatSecret pour cette période
3. Vérifier le format de date (jours depuis epoch pour l'API FatSecret)

---

## 📊 Architecture des données

### Flow de données

```
┌─────────────┐
│  App Mobile │
│   (React    │
│   Native)   │
└──────┬──────┘
       │ POST /api/fatsecret/connect/start
       ↓
┌─────────────┐
│ API Server  │ ← Consumer Key/Secret
│  (FastAPI)  │
└──────┬──────┘
       │ OAuth 1.0a Flow
       ↓
┌─────────────┐
│  FatSecret  │
│     API     │
└──────┬──────┘
       │ Access Token + Secret
       ↓
┌─────────────┐
│  Supabase   │
│ fatsecret_  │
│ connections │
└─────────────┘

       ↓ (Cron Job)
       
┌─────────────┐
│   Sync      │ ← OAuth Tokens
│   Script    │
└──────┬──────┘
       │ GET food-entries/v1
       ↓
┌─────────────┐
│  FatSecret  │
│     API     │
└──────┬──────┘
       │ Food Entries JSON
       ↓
┌─────────────┐
│  Supabase   │
│ food_       │
│ entries_raw │
└─────────────┘
```

### Stratégie de stockage

1. **Connexions OAuth** (`fatsecret_connections`)
   - Stocke les tokens d'accès de manière sécurisée
   - Un utilisateur = une connexion
   - RLS activée (l'utilisateur ne voit que sa connexion)

2. **Entrées alimentaires** (`food_entries_raw`)
   - Stocke les données brutes JSON complètes
   - Upsert basé sur `(user_id, fatsecret_food_entry_id)`
   - Permet de normaliser/enrichir plus tard sans perdre de données
   - Index sur `(user_id, entry_date)` pour les requêtes rapides

---

## 🎯 Prochaines étapes

### Phase 1: MVP (Actuel) ✅
- [x] Tables Supabase
- [x] Client FatSecret (OAuth 1.0a)
- [x] Script de synchronisation
- [x] Endpoints API
- [x] Documentation

### Phase 2: Enrichissement
- [ ] Table normalisée `food_entries` (calories, macros, etc.)
- [ ] Analyse nutritionnelle automatique
- [ ] Détection de patterns alimentaires
- [ ] Corrélations avec les métriques de santé (sommeil, activité)

### Phase 3: Interface Mobile
- [ ] Écran "Alimentation" dans l'app
- [ ] Bouton "Connecter FatSecret"
- [ ] Affichage des repas récents
- [ ] Statistiques nutritionnelles

### Phase 4: Intelligence
- [ ] Recommandations alimentaires basées sur les données de santé
- [ ] Détection d'allergies/intolérances potentielles
- [ ] Suggestions de timing de repas (en lien avec sommeil/activité)
- [ ] Insights IA sur l'alimentation

---

## 📚 Ressources

- **Documentation FatSecret API:** https://platform.fatsecret.com/api/
- **OAuth 1.0a RFC:** https://tools.ietf.org/html/rfc5849
- **Supabase Docs:** https://supabase.com/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com/

---

## 🆘 Support

Pour toute question ou problème:
1. Vérifier les logs: `/tmp/fatsecret_sync.log`
2. Vérifier la configuration (`.env`, credentials)
3. Consulter cette documentation
4. Vérifier les tables Supabase (données présentes ?)

---

**Dernière mise à jour:** 2026-01-29
**Version:** 1.0.0 (MVP)
