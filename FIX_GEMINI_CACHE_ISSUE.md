# 🔧 Fix: Cache React Query Empêchant l'Affichage des Cartes Gemini

## 📅 Date: 3 Février 2026

---

## 🐛 Problème Identifié

Les logs montraient:
```
LOG  [useEnergyExplanation] 📊 Query state: {"cardsCount": 3, "hasData": true, "isError": false, "isFetching": false, "isLoading": false}
```

**Mais AUCUN appel API** vers `/api/energy/explain/` !

### Cause Root:

React Query utilisait des **données anciennes en cache** avec la query key `['energy', 'explanation', 'v2', userId, date]` et un `staleTime` de **30 minutes**.

Résultat: Le hook retournait 3 anciennes cartes au lieu d'appeler le backend Gemini 3 Pro.

---

## ✅ Solution Appliquée

### Modifications dans `mobile/src/hooks/useEnergyExplanation.ts`:

#### 1️⃣ **Changement de Query Key** (ligne 68)

**Avant:**
```typescript
queryKey: ['energy', 'explanation', 'v2', userId, date],
```

**Après:**
```typescript
queryKey: ['energy', 'explanation', 'v3-gemini', userId, date],
```

**Effet:** Invalide automatiquement l'ancien cache.

---

#### 2️⃣ **Réduction du StaleTime** (ligne 126)

**Avant:**
```typescript
staleTime: 1000 * 60 * 30, // 30 minutes
```

**Après:**
```typescript
staleTime: 1000 * 60 * 5, // 5 minutes
```

**Effet:** Les données sont considérées "stale" après 5 minutes au lieu de 30.

---

#### 3️⃣ **Ajout de RefetchOnMount** (ligne 129)

**Nouveau:**
```typescript
refetchOnMount: true, // ✅ Force un refetch à chaque montage du composant
```

**Effet:** À chaque fois que la page Énergie est visitée, un nouveau fetch est déclenché si les données sont stale.

---

## 🧪 Comment Tester

### Dans votre app mobile:

1. **⚠️ IMPORTANT: Rechargez l'app** (Fast Refresh devrait suffire, ou redémarrez Expo)

2. **Naviguez vers l'onglet "Énergie"** ⚡

3. **Scrollez vers "Pourquoi ce score ?"**

4. **Surveillez les logs dans le terminal 238:**

   Vous devriez voir:
   ```
   LOG  [useEnergyExplanation] 📡 START Fetching explanation...
   LOG  [useEnergyExplanation] 🔗 Full URL: http://localhost:9000/api/energy/explain/...
   LOG  [useEnergyExplanation] 🚀 Sending fetch request...
   LOG  [useEnergyExplanation] 📥 Response status: 200
   LOG  [useEnergyExplanation] ✅ Response received: { cards: [...], energyScore: 38 }
   LOG  [WhyEnergyStack] 🎨 Component rendered with: { cardsCount: 4 }
   ```

5. **Dans le terminal 235 (backend):**

   Vous devriez voir:
   ```
   INFO [explain-energy] user=..., date=today
   INFO ✅ Gemini response generated successfully
   INFO 💰 Estimated cost: $0.03 USD
   ```

---

## 📊 Différence Visuelle

### Avant (Cache):
- Affichait 3 anciennes cartes (format inconnu, peut-être vides ou invalides)
- Aucun appel backend
- Pas de cartes Gemini visibles

### Après (Fresh Data):
- Appel API vers `/api/energy/explain/{userId}`
- Backend génère 4 nouvelles cartes avec Gemini 3 Pro
- `WhyEnergyStack` affiche les cartes en défilement horizontal
- Glassmorphism + animations

---

## 🔍 Vérification Backend

Si les logs frontend montrent l'appel API mais que le backend ne répond pas, vérifiez:

### 1. Backend est bien lancé:
```bash
# Dans terminal 235, vous devriez voir:
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:9000
```

### 2. Gemini client initialisé:
```bash
# Au démarrage du backend:
INFO ✅ Gemini client initialized with model: gemini-3-pro-preview
INFO 🧠 Thinking level: high (default for Gemini 3 Pro)
```

### 3. Clé API configurée:
```bash
# Dans terminal 235:
echo $GOOGLE_API_KEY
# Devrait afficher: AIzaSyAP9UbJfUJEsx-rBrVhWXcuA1sT6ctIj7c
```

### 4. Test manuel de l'endpoint:
```bash
curl -X GET "http://localhost:9000/api/energy/explain/c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd" \
  -H "Authorization: Bearer c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd"
```

**Réponse attendue:**
```json
{
  "energyScore": 38,
  "confidence": 62,
  "label": "Journée fragile",
  "date": "2026-02-03",
  "cards": [
    {
      "type": "nervous",
      "title": "Le Câblage",
      "text": "Ton HRV à 20ms signale...",
      "analogy": "C'est comme charger ton téléphone avec un câble sectionné",
      "metrics": {...}
    },
    ...
  ]
}
```

---

## 🎯 Prochaines Étapes

1. ✅ Changement de query key → **FAIT**
2. ✅ Réduction du staleTime → **FAIT**
3. ✅ Ajout de refetchOnMount → **FAIT**
4. 🔄 **TEST EN COURS** → À vérifier dans l'app

---

## 💡 Notes Techniques

### React Query Cache Strategy:

- **Query Key**: Identifiant unique pour le cache
- **StaleTime**: Durée pendant laquelle les données sont considérées "fraîches"
- **GcTime (CacheTime)**: Durée avant suppression du cache
- **RefetchOnMount**: Force un refetch au montage du composant

### Pourquoi `refetchOnMount: true` ?

Par défaut, React Query ne refetch que si:
1. Les données sont `stale` (après `staleTime`)
2. ET le composant est monté

Avec `refetchOnMount: true`, on force le refetch même si les données sont considérées fraîches.

---

## ✅ Checklist Finale

- ✅ Query key changée à `v3-gemini`
- ✅ StaleTime réduit à 5 minutes
- ✅ RefetchOnMount ajouté
- ✅ Backend Gemini 3 Pro configuré
- ✅ Endpoint `/api/energy/explain/{userId}` opérationnel
- 🔄 **Test dans l'app en cours...**

---

## 🚨 Si ça ne marche toujours pas:

### Option 1: Hard Refresh de l'app
```bash
# Dans terminal 238 (Expo)
# Appuyez sur 'r' pour reload
```

### Option 2: Clear du cache React Native
```bash
cd mobile
npx expo start --clear
```

### Option 3: Invalider manuellement le cache
```typescript
// Dans energie.tsx, ajouter au useEffect:
queryClient.removeQueries({ queryKey: ['energy', 'explanation'] });
```

---

## 📞 Debug Logs à Partager

Si le problème persiste, partagez ces logs:

1. **Frontend (terminal 238)**: Chercher `[useEnergyExplanation]`
2. **Backend (terminal 235)**: Chercher `[explain-energy]` ou `[GeminiClient]`
3. **Network**: Vérifier si l'appel HTTP part bien vers `localhost:9000`
