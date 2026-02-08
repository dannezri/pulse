# 🔍 Dépannage : Analyses Gemini Non Affichées

## Problème

Les analyses Gemini ne s'affichent pas dans la section expandable des médicaments.

---

## ✅ Checklist de Diagnostic

### 1. Vérifier que le Backend est Démarré

```bash
# Vérifier que le processus tourne
ps aux | grep api_server.py

# Vérifier les logs
tail -f backend/backend.log

# Chercher cette ligne dans les logs :
# ✅ Medication Analysis Service initialized with Gemini 3 Pro
```

**Si le service n'est pas initialisé**, redémarrez le backend :

```bash
cd backend
# Arrêter le backend actuel
pkill -f api_server.py

# Redémarrer
python3 api_server.py
```

### 2. Vérifier que l'Endpoint API Fonctionne

```bash
cd backend

# Définir les variables
export USER_ID="votre-user-id"  # Trouvez-le dans Supabase
export JWT_TOKEN="votre-jwt"    # Générez-le avec get_jwt_token.py

# Tester l'endpoint
./test_medication_endpoint.sh
```

**Réponse attendue** :
```json
{
  "analyse_traitements": [
    {
      "nom": "Doliprane",
      "intro_explicative": "...",
      "impact_corps": "...",
      "impact_journee": "...",
      "observation": "..."
    }
  ],
  "_generated_at": "2026-02-04T...",
  "_medications_count": 1
}
```

**Si erreur 503** : Le service n'est pas initialisé
- Vérifier que `GOOGLE_API_KEY` est défini dans `.env`
- Redémarrer le backend

**Si erreur 401/403** : Problème d'authentification
- Vérifier que le JWT token est valide
- Régénérer un token avec `python3 get_jwt_token.py`

**Si `analyse_traitements` est vide** : L'utilisateur n'a pas de médicaments actifs
- Ajouter des médicaments via l'app mobile
- Ou vérifier dans Supabase : `SELECT * FROM user_medications WHERE user_id = 'xxx' AND is_active = true;`

### 3. Vérifier les Logs du Mobile

Dans Metro Bundler, cherchez ces logs :

```
[Medications] 🔍 Debug Analyses Gemini:
  - userId: xxx-xxx-xxx
  - analysisData: { analyse_traitements: [...] }
  - loadingAnalysis: false
  - Nombre d'analyses: 2
  - [0] Doliprane
  - [1] Venlafaxine LP
  - Médicaments actuels:
  - [0] Doliprane
  - [1] Venlafaxine LP
```

**Si `analysisData: undefined`** :
- L'API n'a pas été appelée ou a échoué
- Vérifier que `userId` est défini
- Vérifier les logs réseau dans React Native Debugger

**Si `analysisError` est présent** :
- Lire l'erreur pour identifier le problème
- Vérifier la connexion réseau
- Vérifier l'URL du backend dans `mobile/app.config.js`

**Si les noms ne matchent pas** :
- Problème de casse ou d'espaces
- Exemple : Backend retourne "Doliprane 500mg" mais l'app cherche "Doliprane"
- Solution : Ajuster la logique de matching

### 4. Vérifier le Matching des Noms

Les analyses sont matchées par nom de médicament. Si les noms ne correspondent pas exactement, l'analyse ne sera pas trouvée.

**Dans les logs, cherchez** :
```
[Medications] 🔎 Recherche analyse pour "Doliprane": ✅ Trouvée
[Medications] 🔎 Recherche analyse pour "Venlafaxine LP": ❌ Non trouvée
```

**Si "Non trouvée"**, c'est un problème de matching. Options :

**Option A : Améliorer le matching (recommandé)**

Modifier `medications.tsx` :

```typescript
const getMedicationAnalysis = (medicationName: string) => {
  if (!analysisData || !analysisData.analyse_traitements) {
    return null;
  }
  
  // Matching plus flexible
  const normalizedSearchName = medicationName.toLowerCase().trim();
  
  return analysisData.analyse_traitements.find((item) => {
    const normalizedItemName = item.nom.toLowerCase().trim();
    
    // Exact match
    if (normalizedItemName === normalizedSearchName) return true;
    
    // Partial match (contient)
    if (normalizedItemName.includes(normalizedSearchName)) return true;
    if (normalizedSearchName.includes(normalizedItemName)) return true;
    
    // Match sans dosage (ex: "Doliprane 500mg" vs "Doliprane")
    const itemNameWithoutDosage = normalizedItemName.replace(/\s*\d+\.?\d*\s*(mg|g|ml)/gi, '').trim();
    const searchNameWithoutDosage = normalizedSearchName.replace(/\s*\d+\.?\d*\s*(mg|g|ml)/gi, '').trim();
    
    if (itemNameWithoutDosage === searchNameWithoutDosage) return true;
    
    return false;
  }) || null;
};
```

**Option B : Ajuster le backend**

Modifier le service backend pour retourner le nom exact du médicament sans dosage.

### 5. Vérifier que la Section Gemini est Affichée

Dans `MedicationCard.tsx`, la section Gemini s'affiche uniquement si `analysis` est défini :

```typescript
{analysis && (
  <>
    {/* Intro Explicative */}
    <View style={[styles.expandedCard, styles.geminiCard]}>
      ...
    </View>
  </>
)}
```

**Debug dans MedicationCard** :

Ajoutez temporairement dans le composant :

```typescript
console.log('[MedicationCard]', medication.name, 'analysis:', analysis ? '✅ Présente' : '❌ Absente');
```

---

## 🚀 Solution Rapide

Si rien ne fonctionne, suivez ces étapes dans l'ordre :

### 1. Redémarrer le Backend

```bash
cd /Users/dannezri/Desktop/Pulse/backend

# Arrêter
pkill -f api_server.py

# Vérifier que GOOGLE_API_KEY est défini
echo $GOOGLE_API_KEY

# Si vide, l'ajouter
echo 'GOOGLE_API_KEY=AIzaSy...' >> .env

# Redémarrer
python3 api_server.py
```

### 2. Vérifier les Logs Backend

```bash
tail -f backend/backend.log | grep -i "medication\|gemini"
```

Cherchez :
```
✅ Medication Analysis Service initialized with Gemini 3 Pro
```

### 3. Tester Manuellement l'Endpoint

```bash
cd backend

# Trouver un user_id
psql $DATABASE_URL -c "SELECT id FROM profiles LIMIT 1;"

# Générer un JWT
python3 get_jwt_token.py

# Tester l'endpoint
export USER_ID="le-user-id"
export JWT_TOKEN="le-jwt-token"
./test_medication_endpoint.sh
```

### 4. Recharger l'App Mobile

```bash
# Dans le terminal Metro Bundler, appuyez sur 'r' pour reload
# Ou dans l'app, secouez l'appareil et appuyez sur "Reload"
```

### 5. Vérifier les Logs Mobile

Dans Metro Bundler, cherchez :
```
[Medications] 🔍 Debug Analyses Gemini:
```

---

## 📊 Scénarios Courants

### Scénario 1 : Backend Non Redémarré

**Symptômes** :
- Logs backend ne montrent pas "Medication Analysis Service initialized"
- Endpoint retourne 503 ou 500

**Solution** :
```bash
cd backend
pkill -f api_server.py
python3 api_server.py
```

### Scénario 2 : Pas de Médicaments Actifs

**Symptômes** :
- Endpoint retourne `"analyse_traitements": []`
- Message : "Aucun médicament actif à analyser"

**Solution** :
- Ajouter des médicaments via l'app mobile
- Ou vérifier dans Supabase que `is_active = true`

### Scénario 3 : Noms Ne Matchent Pas

**Symptômes** :
- Logs montrent "❌ Non trouvée" pour tous les médicaments
- Backend retourne "Doliprane 500mg" mais app cherche "Doliprane"

**Solution** :
- Utiliser le matching flexible (Option A ci-dessus)
- Ou ajuster les noms dans la base de données

### Scénario 4 : Erreur Réseau

**Symptômes** :
- `analysisError: Network request failed`
- Timeout

**Solution** :
- Vérifier que le backend tourne
- Vérifier l'URL dans `mobile/app.config.js`
- Si sur device physique, vérifier que device et backend sont sur le même réseau

### Scénario 5 : Cache Vide

**Symptômes** :
- Première génération prend 5-10 secondes
- Ensuite instantané

**Solution** :
- C'est normal ! Gemini met du temps la première fois
- Le cache se remplit automatiquement
- Les prochains appels seront instantanés (7 jours)

---

## 🔬 Debug Avancé

### Activer les Logs Complets

Dans `mobile/src/hooks/useMedicationAnalysis.ts` :

```typescript
async function fetchMedicationAnalysis(userId: string | null): Promise<MedicationAnalysis> {
  console.log('[useMedicationAnalysis] 📡 Fetching...');
  console.log('  - userId:', userId);
  console.log('  - backendUrl:', backendUrl);
  console.log('  - url:', url);
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  
  console.log('[useMedicationAnalysis] 📨 Response:');
  console.log('  - status:', response.status);
  console.log('  - statusText:', response.statusText);
  
  const data = await response.json();
  console.log('[useMedicationAnalysis] 📦 Data:', data);
  
  return data;
}
```

### Vérifier la Base de Données

```sql
-- Vérifier les médicaments de l'utilisateur
SELECT id, medication_name, is_active 
FROM user_medications 
WHERE user_id = 'votre-user-id';

-- Vérifier le cache
SELECT user_id, medications_hash, generated_at, expires_at
FROM medication_analysis_cache
WHERE user_id = 'votre-user-id';

-- Invalider le cache si nécessaire
DELETE FROM medication_analysis_cache
WHERE user_id = 'votre-user-id';
```

---

## ✅ Checklist Finale

Avant de demander de l'aide, vérifiez :

- [ ] Backend est démarré avec `python3 api_server.py`
- [ ] Logs backend montrent "✅ Medication Analysis Service initialized"
- [ ] `GOOGLE_API_KEY` est défini dans `.env`
- [ ] L'endpoint `/api/medications/analyze/:user_id` retourne 200
- [ ] La réponse JSON contient `analyse_traitements` avec des données
- [ ] L'app mobile peut se connecter au backend (même réseau)
- [ ] Les logs mobile montrent `analysisData` avec des données
- [ ] Les noms de médicaments matchent entre backend et app
- [ ] La section expandable est bien ouverte (cliquer sur la card)

---

**Si tout est vérifié et ça ne marche toujours pas**, partagez :
1. Les logs backend (dernières 50 lignes)
2. Les logs mobile (section Debug Analyses Gemini)
3. La réponse de `./test_medication_endpoint.sh`
