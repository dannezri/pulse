# API Logger - Monitoring des Requêtes

## Vue d'ensemble

Le **API Logger** est un système de monitoring intégré qui capture et affiche toutes les requêtes API effectuées par l'application mobile Pulse. Il permet de :

- 📊 Visualiser toutes les requêtes en temps réel
- 🔍 Débugger les problèmes d'API
- ⚡ Analyser les performances (temps de réponse)
- 🎯 Filtrer par méthode HTTP (GET, POST, PUT, DELETE)
- 📱 Interface stylisée avec icônes selon le type de requête

## Architecture

### Composants

```
src/hooks/useApiLogger.ts          # Hook Zustand pour gérer l'état des logs
src/lib/api-client.ts              # Client API avec logging automatique
src/components/RequestCard.tsx     # Composant UI pour afficher une requête
app/(tabs)/requests.tsx            # Page de visualisation des requêtes
```

### Flux de données

```
API Request
  ↓
api-client.ts (wrapper fetch)
  ↓
useApiLogger (Zustand store)
  ↓
RequestCard (UI)
  ↓
requests.tsx (page)
```

## Utilisation

### 1. Utiliser le client API avec logging automatique

Le moyen le plus simple est d'utiliser le client API fourni :

```typescript
import { api } from '@/src/lib/api-client';

// GET request
const users = await api.get('https://api.example.com/users');

// POST request
const newUser = await api.post('https://api.example.com/users', {
  name: 'John Doe',
  email: 'john@example.com',
});

// PUT request
const updatedUser = await api.put(`https://api.example.com/users/${id}`, {
  name: 'Jane Doe',
});

// DELETE request
await api.delete(`https://api.example.com/users/${id}`);
```

Toutes ces requêtes seront **automatiquement loggées** et apparaîtront dans la page "Requêtes".

### 2. Logger manuellement une requête

Si vous utilisez `fetch` directement ou une autre bibliothèque :

```typescript
import { useApiLogger } from '@/src/hooks/useApiLogger';

const { addRequest, updateRequest } = useApiLogger.getState();

// Créer un log
const requestId = addRequest({
  method: 'GET',
  url: 'https://api.example.com/data',
  status: 'pending',
});

try {
  const startTime = Date.now();
  const response = await fetch('https://api.example.com/data');
  const data = await response.json();
  const duration = Date.now() - startTime;
  
  // Mettre à jour avec succès
  updateRequest(requestId, {
    status: 'success',
    statusCode: response.status,
    duration,
    responseBody: data,
  });
} catch (error) {
  // Mettre à jour avec erreur
  updateRequest(requestId, {
    status: 'error',
    error: error.message,
  });
}
```

### 3. Accéder aux logs dans un composant

```typescript
import { useApiLogger } from '@/src/hooks/useApiLogger';

function MyComponent() {
  const { requests, clearRequests } = useApiLogger();
  
  return (
    <View>
      <Text>Total: {requests.length} requêtes</Text>
      <Button title="Clear" onPress={clearRequests} />
    </View>
  );
}
```

## Interface utilisateur

### Page Requêtes (`app/(tabs)/requests.tsx`)

La page affiche :

1. **Header** : Titre + bouton pour effacer les logs
2. **Stats Cards** : 
   - Nombre de succès (vert)
   - Nombre d'erreurs (rouge)
   - Requêtes en cours (jaune)
   - Temps moyen de réponse (bleu)
3. **Filtres** : Par méthode HTTP (ALL, GET, POST, PUT, DELETE)
4. **Liste des requêtes** : Cartes expandables avec détails

### RequestCard (`src/components/RequestCard.tsx`)

Chaque carte affiche :

- **Icône de méthode** : 
  - 👁️ Eye (GET)
  - ⬆️ Upload (POST)
  - ✏️ Edit (PUT/PATCH)
  - 🗑️ Trash (DELETE)
- **Icône de statut** :
  - ⏳ Loader (pending)
  - ✅ CheckCircle (success)
  - ❌ XCircle (error)
- **Informations** :
  - Méthode HTTP + Code de statut
  - URL (path)
  - Timestamp relatif
  - Durée de la requête
  - Message d'erreur (si applicable)
- **Détails expandables** :
  - URL complète
  - Request body (JSON)
  - Response body (JSON)

## Couleurs

Les couleurs sont cohérentes avec le thème Dark Zen de l'application :

| Type | Couleur | Usage |
|------|---------|-------|
| GET | `#00BFFF` (bleu ciel) | Lecture |
| POST | `#00FF41` (vert néon) | Création |
| PUT | `#FFD700` (or) | Mise à jour complète |
| PATCH | `#FFA500` (orange) | Mise à jour partielle |
| DELETE | `#FF4444` (rouge) | Suppression |
| Success | `#00FF41` (vert néon) | Requête réussie |
| Error | `#FF4444` (rouge) | Requête échouée |
| Pending | `#FFD700` (or) | En cours |

## Performances

- **Limite de stockage** : 100 dernières requêtes (pour éviter les fuites mémoire)
- **State management** : Zustand (léger et performant)
- **Pas de persistence** : Les logs sont perdus au redémarrage de l'app

## Exemples avancés

### Wrapper pour Supabase

Pour logger les requêtes Supabase :

```typescript
import { supabase } from '@/src/lib/supabase';
import { useApiLogger } from '@/src/hooks/useApiLogger';

async function supabaseWithLogging<T>(
  operation: () => Promise<{ data: T | null; error: any }>,
  operationName: string
): Promise<T | null> {
  const { addRequest, updateRequest } = useApiLogger.getState();
  
  const requestId = addRequest({
    method: 'POST',
    url: `Supabase RPC: ${operationName}`,
    status: 'pending',
  });
  
  const startTime = Date.now();
  
  try {
    const { data, error } = await operation();
    const duration = Date.now() - startTime;
    
    if (error) {
      updateRequest(requestId, {
        status: 'error',
        duration,
        error: error.message,
      });
      throw error;
    }
    
    updateRequest(requestId, {
      status: 'success',
      statusCode: 200,
      duration,
      responseBody: data,
    });
    
    return data;
  } catch (error) {
    throw error;
  }
}

// Usage
const data = await supabaseWithLogging(
  () => supabase.rpc('get_latest_insight', { p_user_id: userId }),
  'get_latest_insight'
);
```

### Analyser les performances

```typescript
import { useApiLogger } from '@/src/hooks/useApiLogger';

function analyzePerformance() {
  const { requests } = useApiLogger.getState();
  
  // Temps moyen
  const avgDuration = requests
    .filter(r => r.duration)
    .reduce((sum, r) => sum + (r.duration || 0), 0) / requests.length;
  
  // Requêtes les plus lentes
  const slowest = [...requests]
    .filter(r => r.duration)
    .sort((a, b) => (b.duration || 0) - (a.duration || 0))
    .slice(0, 5);
  
  // Taux d'erreur
  const errorRate = requests.filter(r => r.status === 'error').length / requests.length;
  
  return { avgDuration, slowest, errorRate };
}
```

## Dépendances

- **zustand** : State management (installé via `npx expo install zustand`)
- **lucide-react-native** : Icônes (déjà présent)

## Compatibilité

- ✅ iOS
- ✅ Android
- ✅ Expo SDK 54
- ✅ React Native 0.81.5

## Limitations

1. **Pas de persistence** : Les logs sont perdus au redémarrage
2. **Limite de 100 requêtes** : Pour éviter les problèmes de mémoire
3. **Supabase non auto-loggé** : Nécessite un wrapper manuel
4. **Pas d'export** : Impossible d'exporter les logs (feature future)

## Roadmap

- [ ] Persistence des logs (AsyncStorage)
- [ ] Export des logs (JSON, CSV)
- [ ] Recherche dans les logs
- [ ] Graphiques de performances
- [ ] Notifications pour les erreurs
- [ ] Replay de requêtes
- [ ] Comparaison de requêtes

## Voir aussi

- [useApiLogger.example.ts](../src/hooks/useApiLogger.example.ts) : Exemples d'utilisation
- [api-client.ts](../src/lib/api-client.ts) : Client API avec logging
- [RequestCard.tsx](../src/components/RequestCard.tsx) : Composant UI
