# Synchronisation Automatique à l'Ouverture de l'App 🚀

## Vue d'ensemble

L'historique des médicaments se synchronise **automatiquement à chaque ouverture de l'app**, garantissant que les données sont toujours à jour sans intervention de l'utilisateur.

---

## 🎯 Comment ça fonctionne

### 1. À l'ouverture de l'app
```
User ouvre l'app
    ↓
App se charge (1 seconde de délai)
    ↓
useMedicationHistorySync() se déclenche
    ↓
Appel RPC Supabase: auto_populate_medication_history(userId)
    ↓
Génération des entrées manquantes dans medication_intake_history
    ↓
Invalidation du cache React Query
    ↓
Historique rafraîchi automatiquement dans l'UI
```

### 2. Pull-to-refresh dans l'onglet Historique
```
User tire vers le bas dans "Historique"
    ↓
useManualMedicationSync() se déclenche
    ↓
Synchronisation forcée
    ↓
Recharge des données
    ↓
Historique mis à jour
```

---

## 📁 Fichiers modifiés

### 1. Hook de synchronisation
**`mobile/src/hooks/useMedicationHistorySync.ts`**
- `useMedicationHistorySync()` : Synchronisation automatique au démarrage
- `useManualMedicationSync()` : Synchronisation manuelle (pull-to-refresh)

**Caractéristiques :**
- ✅ Une seule synchronisation par session (via `useRef`)
- ✅ Délai de 1 seconde pour ne pas ralentir le démarrage
- ✅ Gestion d'erreur silencieuse (n'empêche pas l'app de se lancer)
- ✅ Invalidation du cache React Query après synchronisation

### 2. Layout principal
**`mobile/app/_layout.tsx`**
- Ajout de `useMedicationHistorySync()` dans `AppContent`
- Se déclenche dès que le QueryClient est prêt

### 3. Onglet Historique
**`mobile/src/components/MedicationHistoryTab.tsx`**
- Ajout du `RefreshControl` pour pull-to-refresh
- Intégration de `useManualMedicationSync()`

---

## 🔄 Cycle de vie

### Premier lancement de l'app
```
1. App démarre
2. QueryClient s'initialise
3. useMedicationHistorySync() attend 1 seconde
4. Appel à auto_populate_medication_history()
5. Génération de TOUT l'historique (depuis start_date)
6. Cache invalidé
7. Historique affiché dans l'UI
```

### Lancements suivants (même session)
```
1. App démarre
2. useMedicationHistorySync() détecte qu'il a déjà synchronisé (useRef)
3. Aucun appel réseau
4. Historique chargé depuis le cache React Query
```

### Nouvelle session (app fermée puis rouverte)
```
1. App démarre
2. useRef est réinitialisé
3. useMedicationHistorySync() se déclenche à nouveau
4. Génère les entrées manquantes (nouvelles dates)
5. Cache invalidé
6. Historique mis à jour
```

---

## ⚡ Optimisations

### 1. Délai de démarrage (1 seconde)
```typescript
setTimeout(() => {
  syncHistory();
}, 1000);
```

**Pourquoi ?**
- Évite de ralentir le chargement initial de l'app
- Laisse l'UI s'afficher d'abord
- La synchronisation se fait en arrière-plan

### 2. Une seule synchronisation par session
```typescript
const hasSyncedRef = useRef(false);

if (hasSyncedRef.current) {
  return; // Skip si déjà synchronisé
}

// Après synchronisation réussie
hasSyncedRef.current = true;
```

**Pourquoi ?**
- Évite les appels réseau inutiles
- Navigation rapide entre écrans
- Économise les ressources

### 3. Gestion d'erreur silencieuse
```typescript
try {
  await syncHistory();
} catch (error) {
  console.error('Sync error:', error);
  // N'empêche pas l'app de fonctionner
}
```

**Pourquoi ?**
- L'app reste fonctionnelle même si la synchronisation échoue
- L'utilisateur voit l'historique en cache
- Peut réessayer avec pull-to-refresh

---

## 📊 Monitoring

### Logs dans la console mobile

**Synchronisation réussie :**
```
[useMedicationHistorySync] 🔄 Starting medication history sync...
[useMedicationHistorySync] ✅ Sync completed in 320ms
[useMedicationHistorySync] 📊 Results: [...]
[useMedicationHistorySync] 🎉 History synchronized successfully
```

**Déjà synchronisé cette session :**
```
[useMedicationHistorySync] ⏭️ Already synced this session
```

**Erreur :**
```
[useMedicationHistorySync] ❌ Sync error: [error details]
```

### Vérifier dans Supabase

**Voir les dernières entrées générées :**
```sql
SELECT 
  intake_date,
  COUNT(*) as entries_count
FROM medication_intake_history
WHERE user_id = 'YOUR_USER_ID'
GROUP BY intake_date
ORDER BY intake_date DESC
LIMIT 10;
```

---

## 🧪 Tests

### Test 1: Première ouverture
1. Désinstaller l'app (ou clear storage)
2. Réinstaller et ouvrir
3. Attendre 2 secondes
4. Aller dans "Historique"
5. ✅ L'historique est rempli depuis la date de début

### Test 2: Ouverture suivante (même session)
1. Aller sur un autre écran
2. Revenir à l'écran d'accueil
3. Vérifier les logs
4. ✅ "Already synced this session"

### Test 3: Nouvelle session
1. Fermer complètement l'app (swipe)
2. Rouvrir l'app
3. Attendre 2 secondes
4. ✅ Nouvelle synchronisation lancée

### Test 4: Pull-to-refresh
1. Aller dans "Historique"
2. Tirer vers le bas
3. ✅ Spinner de rafraîchissement
4. ✅ Historique mis à jour

### Test 5: Hors ligne
1. Activer le mode avion
2. Ouvrir l'app
3. ✅ L'app se lance normalement
4. ✅ Historique chargé depuis le cache
5. ✅ Pas de blocage

---

## 🔧 Configuration

### Changer le délai de synchronisation

Par défaut : **1 seconde**

Pour changer (par exemple 500ms) :
```typescript
// Dans useMedicationHistorySync.ts
setTimeout(() => {
  syncHistory();
}, 500); // ← Modifier ici
```

### Désactiver la synchronisation automatique

Pour désactiver temporairement (debug) :
```typescript
// Dans _layout.tsx
function AppContent() {
  // useMedicationHistorySync(); // ← Commenter cette ligne
  
  return <Stack />;
}
```

### Forcer la synchronisation à chaque navigation

Pour synchroniser à chaque changement d'écran :
```typescript
// Dans useMedicationHistorySync.ts
// Supprimer la logique de hasSyncedRef
```

---

## 🆚 Comparaison avec le Cron Job

| Critère | Cron Job (Quotidien) | Sync à l'ouverture |
|---------|---------------------|-------------------|
| **Fraîcheur** | Données d'hier | Données en temps réel |
| **Consommation serveur** | Faible (1x/jour) | Moyenne (à chaque ouverture) |
| **Utilisateur inactif** | ✅ Historique généré | ❌ Pas de génération |
| **Latence au démarrage** | Aucune | +1 seconde |
| **Fiabilité** | ✅ Garanti | Dépend de l'ouverture |
| **Complexité** | Simple (SQL) | Moyenne (Hook React) |

---

## 💡 Recommandations

### Option hybride (recommandée)
Combiner les deux approches :
1. **Sync à l'ouverture** : Données toujours fraîches
2. **Cron backup** : Génère l'historique même si l'app n'est pas ouverte

**Configuration :**
```sql
-- Cron quotidien à 00:00 UTC (backup)
SELECT cron.schedule(
  'daily_medication_history_sync_backup',
  '0 0 * * *',
  'SELECT daily_medication_sync();'
);
```

### Gestion des utilisateurs inactifs
Pour les utilisateurs qui n'ouvrent pas l'app pendant longtemps :
- Le cron backup génère l'historique
- Quand ils ouvrent l'app, elle synchronise les jours manquants

---

## 🐛 Dépannage

### "Sync prend trop de temps au démarrage"
**Solution :** Augmenter le délai initial
```typescript
setTimeout(() => {
  syncHistory();
}, 2000); // 2 secondes au lieu de 1
```

### "L'historique ne se rafraîchit pas"
**Vérifier :**
1. Les logs dans la console
2. Que `userId` existe dans storage
3. Que la fonction RPC fonctionne manuellement
4. Que React Query invalidation fonctionne

**Test manuel :**
```typescript
// Dans l'app
import { supabase } from '@/lib/supabase';

const testSync = async () => {
  const { data, error } = await supabase.rpc('auto_populate_medication_history', {
    p_user_id: 'YOUR_USER_ID',
  });
  console.log('Result:', data, error);
};
```

### "Sync échoue à chaque fois"
**Causes possibles :**
1. Problème de connexion réseau
2. Fonction SQL manquante/erreur
3. Permissions RLS incorrectes
4. userId incorrect

**Vérifier dans Supabase SQL Editor :**
```sql
-- Tester la fonction directement
SELECT * FROM auto_populate_medication_history('YOUR_USER_ID');
```

---

## ✅ Checklist de Vérification

- [ ] Hook `useMedicationHistorySync` intégré dans `_layout.tsx`
- [ ] Pull-to-refresh fonctionne dans l'onglet Historique
- [ ] Logs apparaissent dans la console mobile
- [ ] Historique se remplit à l'ouverture de l'app
- [ ] Pas de régression sur les performances
- [ ] Gestion d'erreur silencieuse fonctionne
- [ ] Cron job désactivé (ou configuré en backup)

---

## 🎉 Résultat

**À partir de maintenant :**
- ✅ Chaque ouverture de l'app synchronise l'historique
- ✅ Pull-to-refresh disponible pour synchronisation manuelle
- ✅ Données toujours à jour
- ✅ Aucune action requise de l'utilisateur
- ✅ Performance optimale (délai + cache)

**L'utilisateur voit :**
- Son historique complet dès l'ouverture
- Aucun délai perceptible
- Possibilité de rafraîchir manuellement

---

**Tout est prêt ! 🚀**
