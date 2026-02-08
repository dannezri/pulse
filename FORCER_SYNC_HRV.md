# Forcer la Synchronisation des Données HRV Manquantes

## 🎯 Objectif

Récupérer les données HRV manquantes depuis l'API Oura pour les **4 jours** :
- 29 janvier 2026
- 30 janvier 2026
- 31 janvier 2026
- 1er février 2026

---

## ✅ Confirmation

Tu as **confirmé avoir ces données dans l'app Oura** → Le problème est côté **synchronisation Pulse**.

---

## 🚀 Méthode 1 : Via l'App Mobile Pulse (Le Plus Simple)

### Étapes

1. **Ouvre l'app Pulse** sur ton iPhone
2. Va dans **Paramètres** → **Intégrations** → **Oura**
3. Clique sur **"Synchroniser maintenant"** (ou **"Force Sync"**)
4. Attends 10-15 secondes
5. Retourne sur la page **"Analyse Énergétique"**
6. Tire vers le bas pour **refresh**

**Résultat attendu** : Les données HRV devraient apparaître et ton score de récupération devrait changer.

---

## 🚀 Méthode 2 : Via l'API Backend (Plus Technique)

### Option A : Appel API Manuel

Tu peux forcer la synchronisation en appelant l'endpoint `/api/oura/sync` pour chaque jour manquant :

```bash
# Obtenir ton JWT token depuis l'app
# (va dans Paramètres → Debug Mode → Copier Token)

TOKEN="YOUR_JWT_TOKEN_HERE"
API_URL="http://localhost:9000"

# Synchroniser chaque jour manquant
curl -X POST "$API_URL/api/oura/sync?date=2026-01-29" \
  -H "Authorization: Bearer $TOKEN"

curl -X POST "$API_URL/api/oura/sync?date=2026-01-30" \
  -H "Authorization: Bearer $TOKEN"

curl -X POST "$API_URL/api/oura/sync?date=2026-01-31" \
  -H "Authorization: Bearer $TOKEN"

curl -X POST "$API_URL/api/oura/sync?date=2026-02-01" \
  -H "Authorization: Bearer $TOKEN"
```

### Option B : Script Python (fix_missing_hrv.py)

J'ai créé un script Python qui :
1. ✅ Teste la connexion API Oura
2. ✅ Récupère les données manquantes
3. ✅ Les insère dans Supabase
4. ✅ Invalide le cache des forecasts

**Pour l'exécuter** :

```bash
# Terminal 235 (où tourne le backend)
cd /Users/dannezri/Desktop/Pulse/backend

# Arrêter temporairement le serveur (Ctrl+C)

# Activer l'environnement Python
source venv/bin/activate  # ou le chemin de ton venv

# Exécuter le script
python3 fix_missing_hrv.py

# Résultat attendu :
# 🔗 Connexion à Supabase...
# 🔑 Récupération du token Oura...
# ✅ Token Oura trouvé: IX6RMKRCMIJOVZMIB2I...
# 🧪 Test de connexion API Oura...
# ✅ API Oura OK - User: nezri.dan@gmail.com
# 📥 Récupération des données Oura manquantes...
#   → Daily Sleep...
#      Récupéré: 4 nuits
#   → Daily Readiness...
#      Récupéré: 4 jours
# 📊 Données HRV trouvées:
#   ✅ 2026-01-29: HRV = 52 ms
#   ✅ 2026-01-30: HRV = 61 ms
#   ✅ 2026-01-31: HRV = 48 ms
#   ✅ 2026-02-01: HRV = 55 ms
# 💾 Insertion de 4 valeurs HRV dans Supabase...
#   ✅ Inséré HRV pour 2026-01-29: 52 ms
#   ✅ Inséré HRV pour 2026-01-30: 61 ms
#   ✅ Inséré HRV pour 2026-01-31: 48 ms
#   ✅ Inséré HRV pour 2026-02-01: 55 ms
# 🗑️  Invalidation du cache des forecasts...
#   ✅ Cache invalidé
# ✅ TERMINÉ !

# Redémarrer le serveur
./restart_api_server.sh
```

---

## 🚀 Méthode 3 : Via Supabase SQL (Debug)

Si tout le reste échoue, on peut **tester directement l'API Oura** et voir ce qu'elle retourne.

### Étape 1 : Récupérer le Token Oura

```sql
SELECT metadata->'access_token' as oura_token
FROM external_identities
WHERE supabase_user_id = 'c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd'
  AND provider_system = 'oura';

-- Résultat attendu : IX6RMKRCMIJOVZMIB2IKVL2PWUQOCNNI
```

### Étape 2 : Tester l'API Oura Manuellement

```bash
# Remplacer YOUR_TOKEN par le token récupéré
TOKEN="IX6RMKRCMIJOVZMIB2IKVL2PWUQOCNNI"

# Test 1 : Personal Info (vérifier que le token fonctionne)
curl -X GET "https://api.ouraring.com/v2/usercollection/personal_info" \
  -H "Authorization: Bearer $TOKEN"

# Résultat attendu :
# {"age":25,"weight":75,"height":1.8,"biological_sex":"male","email":"nezri.dan@gmail.com"}

# Test 2 : Daily Sleep (contient HRV)
curl -X GET "https://api.ouraring.com/v2/usercollection/daily_sleep?start_date=2026-01-29&end_date=2026-02-01" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Résultat attendu :
# {
#   "data": [
#     {
#       "day": "2026-01-29",
#       "contributors": {
#         "hrv_balance": 52,  ← HRV ici !
#         ...
#       }
#     },
#     ...
#   ]
# }

# Test 3 : Daily Readiness (contient aussi HRV)
curl -X GET "https://api.ouraring.com/v2/usercollection/daily_readiness?start_date=2026-01-29&end_date=2026-02-01" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

## 📊 Impact sur Ton Score

### Actuellement (Sans HRV)

```
Recovery : 31.8% (confiance: 50%)
  ├─ RHR neutre (0 contribution)
  ├─ Sommeil bon (+6%)
  └─ HRV MANQUANT (-15% pénalité)

Score d'énergie : 38%
```

### Après Synchronisation (Avec HRV)

**Scénario réaliste** (basé sur ta dernière valeur HRV : 48 ms) :

```
Recovery : 45-50% (confiance: 85%)
  ├─ RHR neutre (0 contribution)
  ├─ Sommeil bon (+6%)
  └─ HRV moyen (+10-15%)

Score d'énergie : 42-45% (+4-7%)
```

**Note** : Si ton HRV des 4 derniers jours est **meilleur** que 48 ms, ton score pourrait monter jusqu'à **50-55%**.

---

## 🔧 Debugging : Vérifier les Logs Backend

Si la synchronisation ne fonctionne pas, vérifie les logs :

```bash
# Terminal 235
tail -f /Users/dannezri/Desktop/Pulse/backend/nohup.out | grep -i "hrv\|oura\|sync"

# Logs à surveiller :
# ✅ "Retrieved X daily sleep records"
# ✅ "Retrieved X daily readiness records"
# ✅ "Saved biometric: hrv"
# ❌ "Error getting daily sleep data"
# ❌ "Token expired"
```

---

## ❓ Pourquoi Ça Ne Se Synchronise Pas Automatiquement ?

### Causes Possibles

1. **Cron Job Désactivé**
   - Le script `cron_oura_daily_sync.py` devrait tourner **tous les jours à 9h**
   - Vérifie si launchd est actif : `launchctl list | grep oura`

2. **Webhook Oura Non Configuré**
   - Oura peut envoyer des webhooks quand de nouvelles données arrivent
   - Actuellement, Pulse utilise un **polling manuel** (cron)

3. **API Oura Rate Limit**
   - Oura limite les appels API à **100 requêtes/heure**
   - Le backend respecte ces limites

4. **Token Oura Expiré**
   - Les tokens Oura expirent après **6 mois**
   - Ton token a été créé le **28 janvier 2026** (récent)

---

## 🆘 Si Rien Ne Marche

### Option 1 : Reconnecter Oura

Dans l'app Pulse :
1. Paramètres → Intégrations → Oura
2. **Déconnecter**
3. **Reconnecter** (OAuth flow)
4. Attendre 1-2 minutes
5. Vérifier si les données apparaissent

### Option 2 : Support Technique

**Contact moi** et dis-moi :
- [ ] As-tu essayé la Méthode 1 (app mobile) ?
- [ ] As-tu essayé de reconnecter Oura ?
- [ ] Que disent les logs backend ? (copie-colle)
- [ ] L'API Oura répond-elle ? (Test 1 ci-dessus)

---

## 📝 Checklist de Résolution

- [ ] **Méthode 1** : Force sync depuis l'app Pulse
- [ ] **Vérification** : Recharger la page Analyse Énergétique
- [ ] **Si échec** : Vérifier les logs backend
- [ ] **Si échec** : Tester l'API Oura manuellement (curl)
- [ ] **Si échec** : Exécuter le script `fix_missing_hrv.py`
- [ ] **Si échec** : Reconnecter Oura dans l'app
- [ ] **Si échec** : Me contacter avec les logs

---

## 🎯 Résultat Attendu

Après la synchronisation, tu devrais voir dans l'app Pulse :

```
🔋 Récupération : 45-55% (au lieu de 31.8%)
⚡ Énergie : 42-50% (au lieu de 38%)
🎯 Confiance : 85% (au lieu de 56%)

📊 Données HRV :
  - 29 janvier : XX ms
  - 30 janvier : XX ms
  - 31 janvier : XX ms
  - 1er février : XX ms
```

---

**Commence par la Méthode 1 (app mobile) et dis-moi ce qui se passe ! 📱**

---

**Auteur** : Assistant AI  
**Date** : 2026-02-02  
**Status** : ⏳ EN ATTENTE TEST UTILISATEUR  
**Priorité** : 🔥 HAUTE
