# Setup Guide - Interface Ambient Concierge

## 🎯 Vue d'ensemble

L'interface "Ambient Concierge" transforme Pulse en une expérience minimaliste qui ne communique que l'essentiel. Ce guide vous aide à démarrer rapidement.

## 📦 Prérequis

### Backend
- Python 3.9+
- Compte Supabase (gratuit : [supabase.com](https://supabase.com))
- Clé API OpenAI (pour générer les insights)

### Mobile
- Node.js >= 20.19.4
- Expo CLI
- iOS Simulator ou device iOS (pour HealthKit)

## 🚀 Démarrage Rapide

### 1. Configuration Backend

```bash
cd backend

# Installer les dépendances
pip3 install fastapi uvicorn python-dotenv supabase openai

# Configurer les variables d'environnement
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_KEY="your-service-role-key"
export OPENAI_API_KEY="sk-..."

# Démarrer le serveur
python3 api_server_ambient.py
```

Le serveur démarre sur `http://localhost:9000`.

### 2. Configuration Mobile

```bash
cd mobile

# Installer les dépendances (UNIQUEMENT avec expo install !)
npm install

# Configurer l'URL de l'API
# Créer un fichier .env à la racine de mobile/
echo "EXPO_PUBLIC_API_URL=http://localhost:9000" > .env

# Démarrer l'app
npm start
```

## 🔧 Configuration Détaillée

### Backend : Variables d'environnement

Créer un fichier `backend/.env` :

```bash
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGc...  # Clé "service_role" (pas "anon" !)

# OpenAI pour génération d'insights
OPENAI_API_KEY=sk-...

# Optional
PORT=9000
```

**⚠️ Important** : Utilisez la clé `service_role` de Supabase, pas la clé `anon`.

### Mobile : Configuration

Créer un fichier `mobile/.env` :

```bash
# Backend API
EXPO_PUBLIC_API_URL=http://localhost:9000  # Développement
# EXPO_PUBLIC_API_URL=https://api.pulse.app  # Production

# Supabase (pour authentification mobile)
EXPO_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...  # Clé "anon" ici
```

## 🗄️ Setup Base de Données

### 1. Créer un projet Supabase

1. Aller sur [supabase.com](https://supabase.com)
2. Créer un nouveau projet
3. Noter l'URL et les clés API

### 2. Exécuter les migrations

```bash
cd database

# Les migrations sont dans database/migrations/
# Exécutez-les dans l'ordre dans l'éditeur SQL de Supabase
```

Migrations essentielles pour Ambient Concierge :
- `001_initial_schema.sql` - Structure de base
- `002_fix_schema.sql` - Corrections
- `003_add_idempotence.sql` - Éviter les doublons

### 3. Créer un utilisateur de test

```bash
cd backend
python3 create_test_auth_user.py
```

## 📱 Test de l'Interface

### 1. Vérifier le backend

```bash
# Health check
curl http://localhost:9000/

# Test baselines (remplacer USER_ID)
curl http://localhost:9000/api/baselines/00000000-0000-0000-0000-000000000000
```

### 2. Lancer l'app mobile

```bash
cd mobile
npm start

# Puis appuyer sur :
# - 'i' pour iOS Simulator
# - 'a' pour Android Emulator
# - Scan QR code pour device physique
```

### 3. Générer des données de test

Pour voir l'interface en action, vous avez besoin de données. Options :

**A. Utiliser HealthKit (iOS uniquement, device réel)** :
1. Autoriser l'accès HealthKit dans l'app
2. Synchroniser vos données réelles

**B. Insérer des données de test manuellement** :

```sql
-- Dans l'éditeur SQL de Supabase
INSERT INTO biometrics (user_id, metric_type, value, recorded_at, source)
VALUES
  ('YOUR_USER_ID', 'hrv', 65, NOW(), 'test'),
  ('YOUR_USER_ID', 'heart_rate', 60, NOW(), 'test'),
  ('YOUR_USER_ID', 'steps', 8000, NOW(), 'test');
```

## 🎨 Voir l'Interface en Action

Une fois les données insérées :

1. **Accueil** : Vous verrez le PulseOrb (sphère animée)
   - Vert = Tout va bien
   - Orange = Attention
   - Rouge = Alerte

2. **Insight** : Une carte avec un conseil personnalisé si anomalie détectée

3. **Détails** : Appuyer sur la carte pour voir les détails (Z-Scores, baselines, etc.)

## 🔍 Débogage

### Backend ne démarre pas

```bash
# Vérifier les variables d'environnement
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_KEY

# Vérifier les dépendances
pip3 list | grep -E "fastapi|uvicorn|supabase|openai"
```

### Mobile ne se connecte pas au backend

```bash
# Vérifier que le backend tourne
curl http://localhost:9000/

# Sur iOS Simulator, utiliser l'IP locale au lieu de localhost
# Trouver votre IP locale :
ifconfig | grep "inet " | grep -v 127.0.0.1

# Puis dans mobile/.env :
EXPO_PUBLIC_API_URL=http://192.168.1.XXX:9000
```

### Pas de données affichées

1. Vérifier que l'utilisateur est authentifié
2. Vérifier qu'il y a des données dans la table `biometrics`
3. Vérifier les logs du backend
4. Vérifier les logs de Metro (terminal mobile)

## 📊 Architecture Simplifiée

```
┌─────────────┐
│  Mobile App │
└──────┬──────┘
       │
       │ 1. GET /api/baselines/{user_id}
       ↓
┌─────────────────┐
│ Backend Python  │───→ Calcule μ, σ sur 14 jours
└──────┬──────────┘
       │
       │ Retourne baselines
       ↓
┌─────────────┐
│  Mobile App │───→ Calcule Z-Scores en temps réel
└──────┬──────┘
       │
       │ 2. POST /api/insights/prioritized (si anomalies)
       ↓
┌─────────────────┐
│ Backend + LLM   │───→ Génère insight "Concierge"
└──────┬──────────┘
       │
       │ Retourne insight
       ↓
┌─────────────┐
│ PulseOrb +  │
│ InsightCard │
└─────────────┘
```

## 🎓 Prochaines Étapes

1. **Lire la documentation complète** : `mobile/AMBIENT_CONCIERGE.md`
2. **Tester avec des données réelles** : Connecter HealthKit ou Vital
3. **Personnaliser les poids** : Modifier `backend/priority_engine.py`
4. **Ajuster les seuils** : Z-Score > 2 par défaut, modifiable
5. **Améliorer les prompts LLM** : Voir `backend/api_server_ambient.py`

## 💡 Tips

- **Performance** : Les baselines sont cachées 24h côté mobile
- **Coûts LLM** : Les insights ne sont générés que si anomalies (économise des tokens)
- **Tests** : Utilisez `mobile/src/services/__tests__/ZScoreCalculator.test.ts`
- **Production** : Utilisez Gunicorn pour le backend, pas `uvicorn` directement

## 🐛 Problèmes Connus

1. **Simulateur iOS** : HealthKit ne fonctionne pas, utilisez un device réel
2. **Permissions .env** : Si erreur de permission, utilisez les variables d'environnement système
3. **Première utilisation** : Il faut au moins 3-5 jours de données pour des baselines fiables

## 📞 Support

- 📖 Documentation : `mobile/AMBIENT_CONCIERGE.md`
- 🔧 Quickstart Backend : `backend/AMBIENT_QUICKSTART.md`
- 🏗️ Architecture : `mobile/ARCHITECTURE.md`
- 🧪 Tests : `npm test` dans `mobile/`

---

**Prêt à tester ?** Lancez le backend, lancez l'app, et profitez de votre nouveau concierge de santé ! 🚀
