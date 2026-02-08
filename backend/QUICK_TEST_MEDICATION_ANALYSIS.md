# 🧪 Test Rapide : Analyse de Médicaments avec Gemini

## ⚠️ Prérequis

Le script de test a besoin de 3 variables d'environnement :

1. **SUPABASE_URL** : URL de votre projet Supabase
2. **SUPABASE_SERVICE_KEY** : Clé service role de Supabase
3. **GOOGLE_API_KEY** : Clé API Google pour Gemini 3 Pro

---

## 🚀 Configuration Rapide

### Option 1 : Fichier .env (Recommandé)

```bash
cd backend

# Copier le template
cp config.example.env .env

# Éditer le fichier .env avec vos vraies valeurs
# Vous devez au minimum définir :
# - SUPABASE_URL
# - SUPABASE_SERVICE_KEY
# - GOOGLE_API_KEY (ajoutez cette ligne si elle n'existe pas)

# Exemple :
cat >> .env << 'EOF'
GOOGLE_API_KEY=AIzaSy...votre_clé_google
EOF
```

### Option 2 : Variables d'environnement temporaires

```bash
cd backend

# Exporter les variables pour cette session
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_KEY="eyJhbGc..."
export GOOGLE_API_KEY="AIzaSy..."
```

---

## 🧪 Lancer le Test

### Test avec Données Mockées (Sans User ID)

```bash
cd backend
python3 test_medication_analysis.py

# Quand demandé "Enter user_id", appuyez simplement sur Enter
# Le script utilisera des données mockées pour tester Gemini
```

**Ce que vous verrez** :
```
🧪 TEST: Medication Analysis Service with Gemini 3 Pro
============================================================

📦 Initializing clients...
✅ Supabase client initialized
✅ Gemini client initialized
✅ Medication Analysis Service initialized

🔑 User ID required for testing
Enter user_id (or press Enter to use test data): [APPUYEZ SUR ENTER]

⚠️  No user_id provided, using mock data for prompt testing...

📝 Building prompt with mock data...

============================================================
SYSTEM PROMPT:
============================================================
Tu es un expert en pharmacologie vulgarisée et un coach bien-être...

============================================================
USER PROMPT:
============================================================
Médicaments à analyser :

- Doliprane 500.0mg, 08:00, 20:00, début J+14
- Venlafaxine LP 37.5mg, 11:00, début J+2

...

🧠 Calling Gemini 3 Pro with mock data...
✅ Gemini response received

============================================================
PARSED ANALYSIS:
============================================================
{
  "analyse_traitements": [
    {
      "nom": "Doliprane",
      "intro_explicative": "Antalgique et antipyrétique...",
      "impact_corps": "Agit sur le système nerveux central...",
      "impact_journee": "Effet ressenti environ 30 minutes...",
      "observation": "Après 14 jours, usage régulier..."
    },
    ...
  ]
}

💰 Estimated cost: $0.0089 USD
✅ Test completed successfully!
```

### Test avec un Vrai User ID

```bash
cd backend
python3 test_medication_analysis.py

# Quand demandé, entrez un user_id valide de votre base de données
# Le script récupérera les vrais médicaments de cet utilisateur
```

**Exemple** :
```
Enter user_id (or press Enter to use test data): 12345678-1234-1234-1234-123456789abc

🔍 Analyzing medications for user: 12345678-1234-1234-1234-123456789abc

🧠 Calling Medication Analysis Service...
✅ Analysis generated successfully!

============================================================
ANALYSIS RESULT:
============================================================
{
  "analyse_traitements": [
    {
      "nom": "Sertraline",
      "intro_explicative": "Antidépresseur ISRS...",
      ...
    }
  ],
  "_generated_at": "2026-02-04T15:30:00Z",
  "_medications_count": 1,
  "_cost": 0.0067
}

💰 Cost: $0.0067 USD
📊 Medications analyzed: 1
📅 Generated at: 2026-02-04T15:30:00Z

✅ Test completed successfully!
```

---

## 🔍 Trouver un User ID

Si vous ne connaissez pas de user_id, vous pouvez en trouver un dans Supabase :

```bash
# Via psql
psql $DATABASE_URL -c "SELECT id, full_name FROM profiles LIMIT 5;"

# Ou via le dashboard Supabase :
# 1. Aller sur https://supabase.com/dashboard
# 2. Sélectionner votre projet
# 3. Aller dans "Table Editor" > "profiles"
# 4. Copier un "id" (UUID)
```

---

## 🐛 Dépannage

### Erreur : "supabase_url is required"

**Cause** : Les variables d'environnement ne sont pas définies.

**Solution** :
```bash
# Vérifier si les variables sont définies
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_KEY
echo $GOOGLE_API_KEY

# Si vides, les exporter ou créer un fichier .env
```

### Erreur : "GOOGLE_API_KEY must be set"

**Cause** : La clé API Google n'est pas définie.

**Solution** :
```bash
# Ajouter dans .env
echo 'GOOGLE_API_KEY=AIzaSy...votre_clé' >> backend/.env

# Ou exporter
export GOOGLE_API_KEY="AIzaSy...votre_clé"
```

### Erreur : "No active medications found"

**Cause** : L'utilisateur n'a pas de médicaments actifs dans la base.

**Solution** :
- Utiliser le mode mock (appuyez sur Enter sans entrer de user_id)
- Ou ajouter des médicaments via l'app mobile
- Ou insérer manuellement dans Supabase :

```sql
INSERT INTO user_medications (
  user_id,
  medication_name,
  dosage,
  dosage_unit,
  start_date,
  is_active
) VALUES (
  'votre-user-id',
  'Doliprane',
  500,
  'mg',
  CURRENT_DATE,
  true
);
```

### Erreur : "Invalid JSON from Gemini"

**Cause** : Gemini a retourné du texte non-JSON (rare).

**Solution** :
- Réessayer (Gemini est parfois instable)
- Vérifier les logs pour voir la réponse brute
- Le service a un fallback gracieux

---

## 📊 Interpréter les Résultats

### Coût

Le coût affiché est une estimation basée sur :
- **Input tokens** : Prompt + données médicaments
- **Output tokens** : Réponse JSON de Gemini
- **Tarif Gemini 3 Pro** : $2/1M tokens (input), $12/1M tokens (output)

**Coût typique** :
- 1-2 médicaments : ~$0.006
- 3-5 médicaments : ~$0.012
- 6-10 médicaments : ~$0.020

### Cache

Si vous relancez le test avec le même user_id :
```
[cache] ✅ Cache HIT for user-123 (hash: 1a2b3c4d...)
🚀 Returning cached analysis (saved ~$0.03 + 30-60s)
```

Le cache est valide **7 jours** et s'invalide si les médicaments changent.

---

## ✅ Succès !

Si vous voyez :
```
✅ Test completed successfully!
💰 Estimated cost: $0.0089 USD
```

Alors le service fonctionne parfaitement ! 🎉

Vous pouvez maintenant tester dans l'app mobile :
```bash
cd mobile
npx expo start

# Dans l'app :
# 1. Aller sur "Médicaments"
# 2. Cliquer sur une card
# 3. Cliquer sur "Analyse complète ▼"
```

---

## 📚 Documentation Complète

Pour plus de détails, voir :
- `MEDICATION_GEMINI_INTEGRATION_COMPLETE.md` - Guide complet
- `mobile/MEDICATION_GEMINI_ANALYSIS.md` - Architecture détaillée
