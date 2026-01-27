# Intégration du API Logger avec les Hooks Existants

## 🎯 Objectif

Ce guide montre comment intégrer le API Logger avec les hooks existants de l'application, notamment `useHealthData` qui utilise Supabase.

## 📦 Hooks actuels

L'application utilise actuellement :
- **`useHealthData`** : Récupère les données de santé via Supabase RPC
- **`useNativeHealth`** : Accède aux données natives (HealthKit)
- **`useAuth`** : Gère l'authentification

## 🔧 Stratégies d'intégration

### Option 1 : Wrapper Supabase (Recommandé pour le debugging)

Créer un wrapper pour logger les appels Supabase :

```typescript
// src/lib/supabase-logger.ts
import { supabase } from './supabase';
import { useApiLogger } from '../hooks/useApiLogger';

export async function supabaseRPC<T>(
  functionName: string,
  params?: Record<string, any>
): Promise<T | null> {
  const { addRequest, updateRequest } = useApiLogger.getState();
  
  const requestId = addRequest({
    method: 'POST',
    url: `Supabase RPC: ${functionName}`,
    status: 'pending',
    requestBody: params,
  });
  
  const startTime = Date.now();
  
  try {
    const { data, error, status, statusText } = await supabase.rpc(functionName, params);
    const duration = Date.now() - startTime;
    
    if (error) {
      updateRequest(requestId, {
        status: 'error',
        statusCode: status,
        duration,
        error: error.message || statusText,
      });
      throw error;
    }
    
    updateRequest(requestId, {
      status: 'success',
      statusCode: status || 200,
      duration,
      responseBody: data,
    });
    
    return data as T;
  } catch (error) {
    const duration = Date.now() - startTime;
    
    updateRequest(requestId, {
      status: 'error',
      duration,
      error: error instanceof Error ? error.message : 'Unknown error',
    });
    
    throw error;
  }
}
```

### Option 2 : Modifier useHealthData (Plus invasif)

Modifier directement `useHealthData` pour utiliser le wrapper :

```typescript
// src/hooks/useHealthData.ts
import { supabaseRPC } from '@/src/lib/supabase-logger';

// Au lieu de :
const { data, error } = await supabase.rpc('get_latest_insight', { p_user_id: userId });

// Utiliser :
const data = await supabaseRPC('get_latest_insight', { p_user_id: userId });
```

### Option 3 : Logger sélectivement (Minimal)

Logger uniquement certaines requêtes importantes :

```typescript
// src/hooks/useHealthData.ts
import { useApiLogger } from './useApiLogger';

const fetchLatestInsight = useCallback(async () => {
  setLoadingInsight(true);
  
  // Logger manuellement
  const { addRequest, updateRequest } = useApiLogger.getState();
  const requestId = addRequest({
    method: 'POST',
    url: 'Supabase: get_latest_insight',
    status: 'pending',
  });
  
  const startTime = Date.now();
  
  try {
    const userId = await storage.getUserId();
    const { data, error, status } = await supabase
      .rpc('get_latest_insight', { p_user_id: userId });
    
    const duration = Date.now() - startTime;
    
    if (error) {
      updateRequest(requestId, {
        status: 'error',
        statusCode: status,
        duration,
        error: error.message,
      });
      throw error;
    }
    
    updateRequest(requestId, {
      status: 'success',
      statusCode: status || 200,
      duration,
      responseBody: data,
    });
    
    setLatestInsight(data[0]);
  } catch (error) {
    // ...
  } finally {
    setLoadingInsight(false);
  }
}, []);
```

## 🎯 Recommandation

**Pour le développement et le debugging** :
- Utiliser **Option 1** (Wrapper Supabase)
- Créer `src/lib/supabase-logger.ts`
- Remplacer progressivement les appels Supabase dans les hooks

**Pour la production** :
- Garder le logger mais désactiver le logging Supabase (trop verbeux)
- Ou logger uniquement les erreurs

## 📝 Exemple complet d'intégration

### 1. Créer le wrapper Supabase

```typescript
// src/lib/supabase-logger.ts
import { supabase } from './supabase';
import { useApiLogger } from '../hooks/useApiLogger';

/**
 * Wrapper pour logger les appels Supabase RPC
 */
export async function supabaseRPC<T>(
  functionName: string,
  params?: Record<string, any>
): Promise<T | null> {
  const { addRequest, updateRequest } = useApiLogger.getState();
  
  const requestId = addRequest({
    method: 'POST',
    url: `Supabase RPC: ${functionName}`,
    status: 'pending',
    requestBody: params,
  });
  
  const startTime = Date.now();
  
  try {
    const { data, error, status, statusText } = await supabase.rpc(functionName, params);
    const duration = Date.now() - startTime;
    
    if (error) {
      updateRequest(requestId, {
        status: 'error',
        statusCode: status,
        duration,
        error: error.message || statusText,
      });
      throw error;
    }
    
    updateRequest(requestId, {
      status: 'success',
      statusCode: status || 200,
      duration,
      responseBody: data,
    });
    
    return data as T;
  } catch (error) {
    const duration = Date.now() - startTime;
    
    updateRequest(requestId, {
      status: 'error',
      duration,
      error: error instanceof Error ? error.message : 'Unknown error',
    });
    
    throw error;
  }
}

/**
 * Wrapper pour logger les requêtes Supabase SELECT
 */
export function supabaseSelect(tableName: string) {
  const { addRequest, updateRequest } = useApiLogger.getState();
  
  const requestId = addRequest({
    method: 'GET',
    url: `Supabase SELECT: ${tableName}`,
    status: 'pending',
  });
  
  const startTime = Date.now();
  
  return {
    async execute<T>() {
      try {
        const { data, error, status } = await supabase.from(tableName).select();
        const duration = Date.now() - startTime;
        
        if (error) {
          updateRequest(requestId, {
            status: 'error',
            statusCode: status,
            duration,
            error: error.message,
          });
          throw error;
        }
        
        updateRequest(requestId, {
          status: 'success',
          statusCode: status || 200,
          duration,
          responseBody: data,
        });
        
        return data as T;
      } catch (error) {
        const duration = Date.now() - startTime;
        
        updateRequest(requestId, {
          status: 'error',
          duration,
          error: error instanceof Error ? error.message : 'Unknown error',
        });
        
        throw error;
      }
    },
  };
}
```

### 2. Utiliser dans useHealthData

```typescript
// src/hooks/useHealthData.ts
import { supabaseRPC } from '@/src/lib/supabase-logger';

// Avant :
const { data, error } = await supabase.rpc('get_latest_insight', { p_user_id: userId });

// Après :
const data = await supabaseRPC<Insight[]>('get_latest_insight', { p_user_id: userId });
```

### 3. Exemple complet de fetchLatestInsight

```typescript
const fetchLatestInsight = useCallback(async () => {
  setLoadingInsight(true);
  try {
    const userId = await storage.getUserId();
    if (!userId) {
      console.log('No user ID found, skipping insight fetch');
      setLatestInsight(null);
      setLoadingInsight(false);
      return;
    }

    console.log('Fetching latest insight for user:', userId);
    
    // Utiliser le wrapper avec logging
    const data = await supabaseRPC<Insight[]>('get_latest_insight', { 
      p_user_id: userId 
    });

    console.log('Latest insight data:', data);
    const insight = Array.isArray(data) && data.length > 0 ? data[0] : null;
    console.log('Latest insight count:', insight ? 1 : 0);
    setLatestInsight(insight);
  } catch (error) {
    console.error('Exception fetching latest insight:', error);
    setLatestInsight(null);
  } finally {
    setLoadingInsight(false);
  }
}, []);
```

## 🔄 Migration progressive

### Étape 1 : Créer le wrapper
```bash
# Créer src/lib/supabase-logger.ts
```

### Étape 2 : Tester avec une fonction
```typescript
// Remplacer un seul appel RPC pour tester
const data = await supabaseRPC('get_latest_insight', { p_user_id: userId });
```

### Étape 3 : Vérifier dans l'onglet Requêtes
- Aller dans l'onglet "Requêtes"
- Vérifier que l'appel apparaît
- Vérifier les détails (durée, params, réponse)

### Étape 4 : Migrer progressivement
- Remplacer les autres appels RPC
- Tester chaque modification

## 🎛️ Configuration avancée

### Désactiver le logging en production

```typescript
// src/lib/supabase-logger.ts
const IS_DEV = __DEV__; // ou process.env.NODE_ENV === 'development'

export async function supabaseRPC<T>(
  functionName: string,
  params?: Record<string, any>
): Promise<T | null> {
  // Si pas en dev, ne pas logger
  if (!IS_DEV) {
    const { data, error } = await supabase.rpc(functionName, params);
    if (error) throw error;
    return data as T;
  }
  
  // Sinon, logger normalement
  // ... code de logging ...
}
```

### Logger uniquement les erreurs

```typescript
export async function supabaseRPC<T>(
  functionName: string,
  params?: Record<string, any>
): Promise<T | null> {
  const startTime = Date.now();
  
  try {
    const { data, error, status } = await supabase.rpc(functionName, params);
    
    if (error) {
      // Logger uniquement les erreurs
      const { addRequest } = useApiLogger.getState();
      addRequest({
        method: 'POST',
        url: `Supabase RPC: ${functionName}`,
        status: 'error',
        statusCode: status,
        duration: Date.now() - startTime,
        error: error.message,
        requestBody: params,
      });
      
      throw error;
    }
    
    return data as T;
  } catch (error) {
    // Logger les exceptions réseau
    const { addRequest } = useApiLogger.getState();
    addRequest({
      method: 'POST',
      url: `Supabase RPC: ${functionName}`,
      status: 'error',
      duration: Date.now() - startTime,
      error: error instanceof Error ? error.message : 'Unknown error',
      requestBody: params,
    });
    
    throw error;
  }
}
```

## 📊 Bénéfices

### Pour le développement
- ✅ Voir toutes les requêtes Supabase en temps réel
- ✅ Débugger les problèmes d'API facilement
- ✅ Mesurer les performances (temps de réponse)
- ✅ Voir les paramètres et réponses

### Pour le debugging
- ✅ Identifier les requêtes lentes
- ✅ Voir les erreurs en un coup d'œil
- ✅ Comparer les temps de réponse
- ✅ Tracer les appels API

## ⚠️ Limitations

1. **Performance** : Logger toutes les requêtes peut impacter les performances
2. **Mémoire** : Limite de 100 requêtes pour éviter les fuites
3. **Verbosité** : Peut être trop verbeux en production

## 💡 Conseils

1. **Utiliser en développement** : Activer le logging uniquement en dev
2. **Logger sélectivement** : Logger uniquement les requêtes importantes
3. **Logger les erreurs** : Toujours logger les erreurs, même en prod
4. **Désactiver en prod** : Désactiver le logging en production (ou logger uniquement les erreurs)

## 🔗 Voir aussi

- [api-logger.md](./api-logger.md) : Documentation complète
- [api-logger-visual-guide.md](./api-logger-visual-guide.md) : Guide visuel
- [useApiLogger.example.ts](../src/hooks/useApiLogger.example.ts) : Exemples d'utilisation
