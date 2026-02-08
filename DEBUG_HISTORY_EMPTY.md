# Debug : Historique Vide dans l'App Mobile

## Situation
- ✅ Données existent en base (3 710 entrées)
- ❌ L'app mobile affiche un historique vide

---

## Causes Possibles

### 1. App pas rechargée (90% des cas)
**Symptôme :** Le nouveau code n'est pas chargé  
**Solution :** Fermer complètement l'app et la rouvrir

### 2. UserId différent
**Symptôme :** L'app utilise un userId différent de celui en base  
**Solution :** Vérifier le userId dans les logs

### 3. RLS bloque la lecture
**Symptôme :** Erreur 403 ou permissions denied  
**Solution :** Vérifier que auth.uid() = user_id

### 4. Hook non déclenché
**Symptôme :** Pas de logs de synchronisation  
**Solution :** Vérifier que useMedicationHistorySync est bien appelé

---

## Checklist de Debug

### Étape 1 : Vérifier les données en base
```sql
-- Dans Supabase SQL Editor
SELECT 
  COUNT(*) as entries,
  MIN(intake_date) as first_date,
  MAX(intake_date) as last_date
FROM medication_intake_history
WHERE user_id = 'YOUR_USER_ID';
```

**Résultat attendu :** entries > 0

---

### Étape 2 : Redémarrer l'app
```bash
1. Fermer COMPLÈTEMENT l'app (swipe)
2. Rouvrir
3. Attendre 2-3 secondes
4. Aller dans "Historique"
```

---

### Étape 3 : Vérifier les logs React Native

**Ouvrir la console :**
- iOS Simulator : CMD + D → "Show Inspector"
- Android : Secouer → "Debug"

**Logs à chercher :**
```
[useMedicationHistorySync] 🔄 Starting medication history sync...
[useMedicationHistorySync] ✅ Sync completed in Xms
[useMedicationHistory] 🔄 Fetching medication intake history...
[useMedicationHistory] ✅ Fetched X intake records
```

**Si vous voyez :**
```
[useMedicationHistory] ✅ Fetched 0 intake records
```
→ Problème de query ou de userId

---

### Étape 4 : Vérifier l'userId

**Dans les logs, chercher :**
```
userId: bee9a055-9b10-47d7-b91d-d7f6081a63f1
```

**Si différent, vérifier dans le code :**
```typescript
// Dans mobile/src/lib/storage.ts
import { storage } from '@/lib/storage';
console.log('Current userId:', storage.userId);
```

---

### Étape 5 : Tester la query manuellement

**Dans le code de l'app, ajouter temporairement :**
```typescript
// Dans MedicationHistoryTab.tsx
useEffect(() => {
  const testQuery = async () => {
    const { data, error } = await supabase
      .from('medication_intake_history')
      .select('*')
      .eq('user_id', storage.userId)
      .limit(5);
    
    console.log('Test query result:', data);
    console.log('Test query error:', error);
  };
  
  testQuery();
}, []);
```

**Résultat attendu :**
- data contient des objets
- error = null

**Si error :**
- `Row level security` → Problème RLS
- `No rows` → UserId incorrect

---

### Étape 6 : Forcer la synchronisation

**Pull-to-refresh dans l'onglet Historique :**
```
1. Aller dans "Historique"
2. Tirer vers le bas
3. Attendre que le spinner disparaisse
4. Vérifier si les données apparaissent
```

---

## Solutions par Symptôme

### "Aucun historique" affiché
```typescript
// Problème : Hook ne retourne rien
// Vérifier dans useMedicationHistoryByDay.ts

const { data: intakes } = useMedicationHistory();
console.log('Intakes from hook:', intakes);

// Si intakes est [] ou undefined, problème de query
```

### "Loading..." infini
```typescript
// Problème : isLoading ne passe jamais à false
// Vérifier dans useMedicationHistory.ts

const { isLoading, error } = useMedicationHistory();
console.log('Loading state:', isLoading);
console.log('Error:', error);

// Si isLoading = true toujours, problème réseau ou timeout
```

### Erreur "Not authenticated"
```typescript
// Problème : Pas de token valide
// Vérifier l'authentification

import { storage } from '@/lib/storage';
console.log('UserId:', storage.userId);
console.log('Token:', storage.getAccessToken?.());

// Si userId = null, l'utilisateur n'est pas connecté
```

---

## Commandes de Vérification

### Vérifier Supabase
```sql
-- Nombre d'entrées par utilisateur
SELECT 
  user_id,
  COUNT(*) as entries
FROM medication_intake_history
GROUP BY user_id;

-- Voir un échantillon
SELECT *
FROM medication_intake_history
WHERE user_id = 'YOUR_USER_ID'
ORDER BY intake_date DESC
LIMIT 10;
```

### Vérifier RLS
```sql
-- Tester la policy SELECT en tant qu'utilisateur
SET request.jwt.claims.sub TO 'bee9a055-9b10-47d7-b91d-d7f6081a63f1';

SELECT COUNT(*)
FROM medication_intake_history;

-- Résultat attendu : > 0
```

---

## Résolution Définitive

Si rien ne fonctionne après toutes ces étapes :

### 1. Vérifier que le hook est bien intégré
```typescript
// Dans mobile/app/_layout.tsx
function AppContent() {
  useMedicationHistorySync(); // ← Doit être présent
  return <Stack />;
}
```

### 2. Vérifier que le composant est utilisé
```typescript
// Dans mobile/app/medications.tsx
import { MedicationHistoryTab } from '@/components/MedicationHistoryTab';

// Dans le render
{activeTab === 'history' && <MedicationHistoryTab />}
```

### 3. Rebuild l'app mobile
```bash
cd /Users/dannezri/Desktop/Pulse/mobile

# Nettoyer
rm -rf node_modules
npm install

# Rebuild
npx expo start --clear
```

---

## Logs Utiles

### Backend (Supabase)
- Logs des fonctions Edge
- Logs des RPC calls
- Logs des queries

### Frontend (React Native)
```
[useMedicationHistorySync] 🔄 Starting...
[useMedicationHistorySync] ✅ Sync completed
[useMedicationHistory] 🔄 Fetching...
[useMedicationHistory] ✅ Fetched X records
[MedicationHistoryTab] ℹ️ No user ID
[MedicationHistoryTab] ✅ Fetched X days
```

---

## Contact Support

Si le problème persiste après ces vérifications, fournir :
1. Les logs complets de la console mobile
2. Une capture d'écran de l'onglet Historique
3. Le résultat de la query SQL ci-dessus
4. La version de l'app (commit hash)

---

**Note :** Dans 90% des cas, un simple redémarrage de l'app résout le problème.
