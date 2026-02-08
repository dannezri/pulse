# FatSecret - Démarrage rapide (5 minutes)

## ⚡ Setup en 5 étapes

### 1. Configuration FatSecret API

1. Aller sur https://platform.fatsecret.com/api/
2. Créer une application
3. Noter votre **Consumer Key** et **Consumer Secret**

### 2. Variables d'environnement

Ajouter dans `backend/.env`:

```bash
FATSECRET_CONSUMER_KEY=your_consumer_key_here
FATSECRET_CONSUMER_SECRET=your_consumer_secret_here
```

### 3. Migration Supabase

Appliquer la migration:

```bash
# Via Supabase SQL Editor (copier/coller le contenu)
cat database/migrations/018_fatsecret_integration.sql
```

Ou via psql:

```bash
psql -h db.YOUR_PROJECT.supabase.co -U postgres -d postgres < database/migrations/018_fatsecret_integration.sql
```

### 4. Installer les dépendances

```bash
cd backend
pip install requests-oauthlib>=1.3.1
```

### 5. Connecter un utilisateur (test)

```bash
cd backend
python setup_fatsecret.py
```

Choisir option 1, entrer l'UUID de votre utilisateur test, suivre les instructions.

---

## 🧪 Test rapide

```bash
# 1. Connecter l'utilisateur (étape 5 ci-dessus)

# 2. Synchroniser les données
python sync_fatsecret_food_entries.py --days-back 7

# 3. Vérifier dans Supabase
# SELECT * FROM food_entries_raw LIMIT 10;
```

---

## 📱 Intégration Mobile (API)

### Flow complet

1. **Démarrer OAuth:**
```http
POST /api/fatsecret/connect/start
Authorization: Bearer <JWT>
```

2. **Ouvrir l'URL retournée dans le navigateur**

3. **Compléter OAuth:**
```http
POST /api/fatsecret/connect/complete
Authorization: Bearer <JWT>
{
  "request_token": "...",
  "request_token_secret": "...",
  "verifier": "CODE_FROM_FATSECRET"
}
```

4. **Vérifier le statut:**
```http
GET /api/fatsecret/status
Authorization: Bearer <JWT>
```

5. **Récupérer les entrées:**
```http
GET /api/fatsecret/food-entries?start_date=2026-01-20
Authorization: Bearer <JWT>
```

---

## 🔄 Automatisation (Cron)

### macOS/Linux - Crontab

```bash
crontab -e
```

Ajouter:
```
# Sync FatSecret daily at 5 AM
0 5 * * * cd /path/to/Pulse/backend && python sync_fatsecret_food_entries.py
```

---

## 🎯 Checklist de vérification

- [ ] Variables d'environnement configurées
- [ ] Migration SQL appliquée
- [ ] Dépendances installées (`requests-oauthlib`)
- [ ] Utilisateur test connecté (OAuth flow réussi)
- [ ] Données synchronisées (au moins 1 entrée dans `food_entries_raw`)
- [ ] API endpoints testés (start, complete, status, food-entries)
- [ ] Cron job configuré (optionnel)

---

## 🆘 Problèmes courants

**"Missing environment variables"**
→ Vérifier le fichier `.env` avec les variables FATSECRET_*

**"Invalid signature"**
→ Vérifier que les credentials sont corrects (copier/coller depuis FatSecret)

**"No food entries found"**
→ L'utilisateur doit avoir des données dans son compte FatSecret pour cette période

**"Request token already used"**
→ Recommencer le flow OAuth depuis le début (étape 1)

---

## 📚 Documentation complète

Pour plus de détails: `backend/FATSECRET_INTEGRATION.md`

---

**Prêt à démarrer ?** Suivez les 5 étapes ci-dessus ! 🚀
