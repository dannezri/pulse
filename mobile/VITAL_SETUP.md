# Configuration Vital - Guide complet

Ce guide explique comment configurer Vital comme passerelle unifiée pour synchroniser les données de santé depuis diverses sources (Apple Health, Google Fit, Fitbit, Oura, Whoop, Strava, Garmin, etc.).

## 🎯 Vue d'ensemble

**Vital** est une API unifiée qui permet de connecter et synchroniser les données de santé depuis de nombreuses sources, sans avoir à implémenter chaque intégration individuellement.

### Architecture

```
Sources de données           Vital API              Backend Pulse         App Mobile
(Apple Health, Fitbit, etc.) → Webhooks → Endpoints Python → Supabase → React Native
```

### Avantages

- ✅ **Multi-sources** : Apple Health, Google Fit, Fitbit, Oura, Whoop, Strava, Garmin, etc.
- ✅ **Cross-platform** : iOS et Android via une seule API
- ✅ **Automatique** : Synchronisation via webhooks (pas de polling)
- ✅ **Sécurisé** : Clés API côté backend uniquement
- ✅ **Scalable** : Ajout de nouvelles sources sans modification du code

## 📋 Prérequis

1. **Compte Vital** : [https://tryvital.io](https://tryvital.io)
2. **Clés API Vital** : API Key, Region, Webhook Secret
3. **Backend Pulse** : En cours d'exécution (port 9000 par défaut)
4. **Supabase** : Base de données configurée

## 🚀 Configuration étape par étape

### 1. Créer un compte Vital

1. Aller sur [https://app.tryvital.io/signup](https://app.tryvital.io/signup)
2. Créer un compte (gratuit pour commencer)
3. Créer un nouveau projet

### 2. Récupérer les clés API

Dans le dashboard Vital :

1. Aller dans **Settings** → **API Keys**
2. Copier votre **API Key**
3. Noter votre **Region** (US ou EU)
4. Copier le **Webhook Secret** (pour valider les webhooks)

### 3. Configurer le backend

Ajouter dans `backend/.env` :

```env
# Vital API Configuration
VITAL_API_KEY=sk_us_xxxxxxxxxxxxx
VITAL_REGION=us
VITAL_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
VITAL_ENVIRONMENT=sandbox
```

**Notes** :
- Utiliser `sandbox` pour le développement
- Utiliser `production` pour la production
- Ne **jamais** commit le fichier `.env` dans git

### 4. Configurer les webhooks Vital

Dans le dashboard Vital :

1. Aller dans **Webhooks** → **Add Endpoint**
2. URL du webhook : `https://your-backend.com/api/webhooks/vital`
   - En développement local : utiliser [ngrok](https://ngrok.com) pour exposer votre backend
   - `ngrok http 9000` puis utiliser l'URL générée
3. Sélectionner les événements :
   - ✅ `daily.data.*.created` (sleep, activity, etc.)
   - ✅ `timeseries.data.*.created` (heart_rate, hrv, steps, etc.)
   - ✅ `connection.*.connected` (notifications de connexion)
4. Copier le **Signing Secret** (webhook secret)

### 5. Activer les providers

Dans le dashboard Vital, aller dans **Providers** et activer :

- ✅ **Apple Health** (iOS HealthKit)
- ✅ **Google Fit** (Android)
- ✅ **Fitbit**
- ✅ **Oura Ring**
- ✅ **Whoop**
- ✅ **Strava**
- ✅ **Garmin**
- ✅ Autres selon vos besoins

**Note** : Chaque provider peut nécessiter des credentials OAuth (client ID, secret). Suivre la documentation Vital pour chaque provider.

### 6. Configurer les types de données

Dans **Data Types**, sélectionner les données à synchroniser :

- ✅ **Sleep** : Durée, qualité, phases
- ✅ **Heart Rate** : Repos, max, zones
- ✅ **HRV** : Variabilité cardiaque
- ✅ **Steps** : Nombre de pas
- ✅ **Calories** : Dépense énergétique
- ✅ **Workouts** : Activités sportives
- ✅ **Body** : Poids, masse grasse, etc.

## 📱 Utilisation dans l'app mobile

### Premier lancement

1. L'utilisateur ouvre l'app Pulse
2. Il voit le bouton **"Connecter vos sources de données"** sur l'écran d'accueil
3. Il tape sur ce bouton → redirigé vers l'écran **Sources**
4. Il tape **"Configurer Vital"**
5. Le backend crée un utilisateur Vital pour lui

### Connexion d'une source

1. L'utilisateur tape **"+ Connecter une source"**
2. Le backend génère un **Vital Link Token** (JWT temporaire)
3. L'app ouvre le **Vital Link Widget** dans le navigateur
4. L'utilisateur sélectionne la source (ex: Fitbit)
5. Vital gère l'OAuth flow
6. Une fois connecté, l'utilisateur revient dans l'app
7. Il rafraîchit la liste → la source apparaît comme connectée ✅

### Synchronisation automatique

- Vital envoie des webhooks automatiquement (temps réel ou quotidien)
- Le backend reçoit et traite les webhooks via `/api/webhooks/vital`
- Les données sont insérées dans Supabase `biometrics`
- L'app affiche les données immédiatement

## 🧪 Tests

### Tester le backend

```bash
# 1. Créer un utilisateur Vital
curl -X POST http://localhost:9000/api/vital/create-user \
  -H "Authorization: Bearer <user_id>" \
  -H "Content-Type: application/json"

# 2. Générer un link token
curl -X POST http://localhost:9000/api/vital/link-token \
  -H "Authorization: Bearer <user_id>" \
  -H "Content-Type: application/json"

# 3. Récupérer les connexions
curl -X GET http://localhost:9000/api/vital/connections \
  -H "Authorization: Bearer <user_id>"

# 4. Simuler un webhook
curl -X POST http://localhost:9000/api/webhooks/vital \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "vital_user_id",
    "data": {
      "hr": [{"value": 72, "timestamp": "2024-01-15T10:00:00Z"}]
    }
  }'
```

### Tester l'app mobile

1. Lancer le backend : `cd backend && python api_server_mvp.py`
2. Lancer l'app : `cd mobile && npx expo start`
3. Naviguer vers l'onglet **Sources**
4. Configurer Vital
5. Connecter une source en sandbox (Apple Health en test)
6. Vérifier les données dans Supabase

## 🔐 Sécurité

### Bonnes pratiques

1. **Ne jamais exposer la clé API Vital côté client**
   - Toujours faire les appels via le backend
   - Le mobile ne connaît que l'URL du backend

2. **Valider les signatures webhook**
   - Le code backend valide déjà les signatures HMAC
   - Assure que les webhooks viennent bien de Vital

3. **Utiliser HTTPS en production**
   - Vital requiert HTTPS pour les webhooks
   - Utiliser un certificat SSL valide

4. **Stocker les secrets de manière sécurisée**
   - Utiliser des variables d'environnement
   - Ne jamais commit `.env` dans git
   - Utiliser un gestionnaire de secrets en production (AWS Secrets Manager, etc.)

## 🐛 Troubleshooting

### "Vital client not configured"

**Problème** : Le backend ne trouve pas les variables Vital.

**Solution** :
1. Vérifier que `backend/.env` contient `VITAL_API_KEY`
2. Redémarrer le backend : `python api_server_mvp.py`

### "Vital user not found"

**Problème** : L'utilisateur n'a pas de compte Vital.

**Solution** :
1. Dans l'app, aller dans **Sources**
2. Taper **"Configurer Vital"**
3. Le compte sera créé automatiquement

### "Cannot open Vital Link URL"

**Problème** : L'URL du widget ne s'ouvre pas.

**Solution** :
1. Vérifier que le backend est accessible
2. Vérifier la configuration `backendUrl` dans `mobile/app.json`
3. En local, utiliser l'IP de votre machine (pas `localhost`)

### Les webhooks ne sont pas reçus

**Problème** : Le backend ne reçoit pas les webhooks.

**Solution** :
1. Vérifier que l'URL du webhook est correcte dans Vital dashboard
2. En local, utiliser ngrok : `ngrok http 9000`
3. Vérifier les logs backend : `python api_server_mvp.py`
4. Tester manuellement : Dashboard Vital → Webhooks → **Send test event**

### "403 Forbidden" sur les webhooks

**Problème** : La signature webhook est invalide.

**Solution** :
1. Vérifier que `VITAL_WEBHOOK_SECRET` correspond au secret dans Vital dashboard
2. Redémarrer le backend après modification de `.env`

## 📚 Ressources

- **Documentation Vital** : [https://docs.tryvital.io](https://docs.tryvital.io)
- **Dashboard Vital** : [https://app.tryvital.io](https://app.tryvital.io)
- **Providers supportés** : [https://docs.tryvital.io/wearables/providers](https://docs.tryvital.io/wearables/providers)
- **API Reference** : [https://docs.tryvital.io/api-reference](https://docs.tryvital.io/api-reference)
- **Status Vital** : [https://status.tryvital.io](https://status.tryvital.io)

## ❓ Questions fréquentes

### Vital est-il gratuit ?

Vital propose un plan gratuit pour le développement et les petits projets. Voir la [tarification](https://tryvital.io/pricing) pour plus de détails.

### Combien de sources puis-je connecter ?

Autant que vous voulez ! Chaque utilisateur peut connecter plusieurs sources (ex: Apple Health + Fitbit + Oura).

### Les données sont-elles synchronisées en temps réel ?

Ça dépend du provider :
- **Apple Health** : Via webhooks (quasi temps réel si Vital Link est ouvert)
- **Fitbit** : Quotidien (limites API Fitbit)
- **Oura** : Quotidien
- **Whoop** : Temps réel

### Puis-je utiliser Vital sans le backend Pulse ?

Techniquement oui, mais ce n'est pas recommandé. Le backend :
- Sécurise les clés API
- Mappe les utilisateurs Vital <-> Supabase
- Gère l'idempotence des webhooks
- Normalise les données

## 🎉 Prochaines étapes

Une fois Vital configuré :

1. ✅ Connecter vos propres sources de test
2. ✅ Vérifier que les webhooks arrivent bien
3. ✅ Vérifier les données dans Supabase
4. ✅ Tester la synchronisation dans l'app mobile
5. ✅ Passer en production quand vous êtes prêt

Bon développement ! 🚀
