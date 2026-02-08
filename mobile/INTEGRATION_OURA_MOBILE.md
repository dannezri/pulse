# Intégration Oura dans l'app mobile Pulse

Guide pour implémenter la connexion Oura dans l'application mobile React Native / Expo.

## 🎯 Objectif

Permettre aux utilisateurs de connecter leur compte Oura directement depuis l'application mobile pour synchroniser automatiquement leurs données de santé.

## 📋 Fonctionnalités à implémenter

### 1. Écran de connexion Oura

**Emplacement suggéré**: `app/(tabs)/settings/oura.tsx`

Fonctionnalités:
- ✅ Afficher le statut de connexion (connecté / non connecté)
- ✅ Formulaire pour entrer le token Oura
- ✅ Bouton "Connecter"
- ✅ Bouton "Déconnecter" (si déjà connecté)
- ✅ Bouton "Synchroniser maintenant"
- ✅ Affichage de la dernière synchronisation

### 2. Hook personnalisé

**Fichier**: `src/hooks/useOura.ts`

```typescript
import { useState, useEffect } from 'react';
import { useAuth } from './useAuth';

interface OuraStatus {
  connected: boolean;
  last_sync: string | null;
  has_readiness_data: boolean;
  connected_at: string | null;
}

export const useOura = () => {
  const { token } = useAuth();
  const [status, setStatus] = useState<OuraStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Récupérer le statut
  const fetchStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/oura/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Failed to fetch status');
      
      const data = await response.json();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Connecter Oura
  const connect = async (ouraToken: string) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/oura/connect`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ access_token: ouraToken })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to connect');
      }
      
      await fetchStatus(); // Refresh status
      setError(null);
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  // Déconnecter Oura
  const disconnect = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/oura/disconnect`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Failed to disconnect');
      
      await fetchStatus(); // Refresh status
      setError(null);
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  // Synchroniser les données
  const sync = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/oura/sync`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to sync');
      }
      
      await fetchStatus(); // Refresh status
      setError(null);
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchStatus();
    }
  }, [token]);

  return {
    status,
    loading,
    error,
    connect,
    disconnect,
    sync,
    refresh: fetchStatus
  };
};
```

### 3. Composant UI

**Fichier**: `app/(tabs)/settings/oura.tsx`

```tsx
import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ActivityIndicator, Alert } from 'react-native';
import { useOura } from '@/src/hooks/useOura';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

export default function OuraSettingsScreen() {
  const { status, loading, error, connect, disconnect, sync } = useOura();
  const [ouraToken, setOuraToken] = useState('');

  const handleConnect = async () => {
    if (!ouraToken.trim()) {
      Alert.alert('Erreur', 'Veuillez entrer votre token Oura');
      return;
    }

    const success = await connect(ouraToken);
    
    if (success) {
      Alert.alert('Succès', 'Votre compte Oura a été connecté avec succès');
      setOuraToken('');
    } else {
      Alert.alert('Erreur', error || 'Impossible de connecter votre compte Oura');
    }
  };

  const handleDisconnect = () => {
    Alert.alert(
      'Déconnecter Oura',
      'Êtes-vous sûr de vouloir déconnecter votre compte Oura ?',
      [
        { text: 'Annuler', style: 'cancel' },
        {
          text: 'Déconnecter',
          style: 'destructive',
          onPress: async () => {
            const success = await disconnect();
            if (success) {
              Alert.alert('Succès', 'Votre compte Oura a été déconnecté');
            }
          }
        }
      ]
    );
  };

  const handleSync = async () => {
    const success = await sync();
    if (success) {
      Alert.alert('Succès', 'Synchronisation terminée');
    } else {
      Alert.alert('Erreur', error || 'Échec de la synchronisation');
    }
  };

  if (loading && !status) {
    return (
      <View className="flex-1 items-center justify-center">
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <View className="flex-1 bg-white p-4">
      <Text className="text-2xl font-bold mb-4">Connexion Oura</Text>

      {status?.connected ? (
        // Compte connecté
        <View>
          <View className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
            <Text className="text-green-800 font-semibold mb-2">
              ✅ Compte Oura connecté
            </Text>
            {status.last_sync && (
              <Text className="text-green-600 text-sm">
                Dernière synchronisation:{' '}
                {format(new Date(status.last_sync), 'dd MMMM yyyy à HH:mm', { locale: fr })}
              </Text>
            )}
            {status.has_readiness_data && (
              <Text className="text-green-600 text-sm mt-1">
                ✓ Données Readiness disponibles
              </Text>
            )}
          </View>

          <TouchableOpacity
            onPress={handleSync}
            disabled={loading}
            className="bg-blue-500 rounded-lg p-4 mb-3"
          >
            {loading ? (
              <ActivityIndicator color="white" />
            ) : (
              <Text className="text-white text-center font-semibold">
                Synchroniser maintenant
              </Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            onPress={handleDisconnect}
            disabled={loading}
            className="bg-red-500 rounded-lg p-4"
          >
            <Text className="text-white text-center font-semibold">
              Déconnecter
            </Text>
          </TouchableOpacity>
        </View>
      ) : (
        // Compte non connecté
        <View>
          <Text className="text-gray-600 mb-4">
            Connectez votre compte Oura pour synchroniser automatiquement vos données de santé.
          </Text>

          <View className="mb-4">
            <Text className="text-sm font-semibold mb-2">Token Oura</Text>
            <TextInput
              value={ouraToken}
              onChangeText={setOuraToken}
              placeholder="Entrez votre token Oura"
              className="border border-gray-300 rounded-lg p-3"
              autoCapitalize="none"
              autoCorrect={false}
            />
            <Text className="text-xs text-gray-500 mt-2">
              Obtenez votre token sur{' '}
              <Text className="text-blue-500">cloud.ouraring.com</Text>
            </Text>
          </View>

          <TouchableOpacity
            onPress={handleConnect}
            disabled={loading}
            className="bg-blue-500 rounded-lg p-4"
          >
            {loading ? (
              <ActivityIndicator color="white" />
            ) : (
              <Text className="text-white text-center font-semibold">
                Connecter
              </Text>
            )}
          </TouchableOpacity>

          {error && (
            <View className="bg-red-50 border border-red-200 rounded-lg p-3 mt-4">
              <Text className="text-red-800">{error}</Text>
            </View>
          )}

          {/* Instructions */}
          <View className="mt-6 bg-gray-50 rounded-lg p-4">
            <Text className="font-semibold mb-2">Comment obtenir votre token ?</Text>
            <Text className="text-sm text-gray-600 mb-1">
              1. Allez sur cloud.ouraring.com
            </Text>
            <Text className="text-sm text-gray-600 mb-1">
              2. Connectez-vous avec votre compte Oura
            </Text>
            <Text className="text-sm text-gray-600 mb-1">
              3. Allez dans "Personal Access Tokens"
            </Text>
            <Text className="text-sm text-gray-600 mb-1">
              4. Créez un nouveau token
            </Text>
            <Text className="text-sm text-gray-600">
              5. Copiez le token et collez-le ci-dessus
            </Text>
          </View>
        </View>
      )}
    </View>
  );
}
```

### 4. Navigation

Ajouter un lien vers l'écran Oura dans les paramètres:

**Fichier**: `app/(tabs)/settings/index.tsx`

```tsx
<TouchableOpacity
  onPress={() => router.push('/settings/oura')}
  className="flex-row items-center justify-between p-4 border-b border-gray-200"
>
  <View className="flex-row items-center">
    <Text className="text-2xl mr-3">💍</Text>
    <View>
      <Text className="font-semibold">Oura Ring</Text>
      <Text className="text-sm text-gray-500">
        Connecter votre compte Oura
      </Text>
    </View>
  </View>
  <Text className="text-gray-400">›</Text>
</TouchableOpacity>
```

## 🔄 Synchronisation automatique

### Option 1: Synchronisation au lancement de l'app

**Fichier**: `app/_layout.tsx`

```tsx
useEffect(() => {
  const syncOuraData = async () => {
    try {
      const response = await fetch(`${API_URL}/api/oura/sync`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        console.log('Oura data synced successfully');
      }
    } catch (error) {
      console.error('Failed to sync Oura data:', error);
    }
  };

  if (token) {
    syncOuraData();
  }
}, [token]);
```

### Option 2: Synchronisation périodique (toutes les heures)

```tsx
import * as BackgroundFetch from 'expo-background-fetch';
import * as TaskManager from 'expo-task-manager';

const OURA_SYNC_TASK = 'oura-sync-task';

TaskManager.defineTask(OURA_SYNC_TASK, async () => {
  try {
    const token = await getAuthToken(); // Récupérer le token stocké
    
    const response = await fetch(`${API_URL}/api/oura/sync`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    return response.ok
      ? BackgroundFetch.BackgroundFetchResult.NewData
      : BackgroundFetch.BackgroundFetchResult.Failed;
  } catch (error) {
    return BackgroundFetch.BackgroundFetchResult.Failed;
  }
});

// Enregistrer la tâche
await BackgroundFetch.registerTaskAsync(OURA_SYNC_TASK, {
  minimumInterval: 60 * 60, // 1 heure
  stopOnTerminate: false,
  startOnBoot: true,
});
```

## 🎨 Améliorations UI

### Badge de statut Oura

Afficher un badge sur l'écran d'accueil si Oura est connecté:

```tsx
{status?.connected && (
  <View className="bg-purple-100 rounded-full px-3 py-1 flex-row items-center">
    <Text className="text-purple-800 text-xs font-semibold">💍 Oura</Text>
  </View>
)}
```

### Indicateur de synchronisation

Afficher un indicateur pendant la synchronisation:

```tsx
{syncing && (
  <View className="absolute top-0 left-0 right-0 bg-blue-500 p-2">
    <Text className="text-white text-center text-sm">
      Synchronisation Oura en cours...
    </Text>
  </View>
)}
```

## 🧪 Tests

### Test manuel

1. Aller dans Paramètres → Oura Ring
2. Entrer un token Oura valide
3. Cliquer sur "Connecter"
4. Vérifier que le statut passe à "Connecté"
5. Cliquer sur "Synchroniser maintenant"
6. Vérifier que les données sont bien synchronisées

### Test avec un token invalide

1. Entrer un token invalide
2. Vérifier qu'un message d'erreur s'affiche
3. Vérifier que le compte n'est pas connecté

## 📝 Notes importantes

- **Sécurité**: Ne jamais logger le token Oura en clair
- **UX**: Afficher des messages clairs en cas d'erreur
- **Performance**: Ne pas synchroniser trop souvent (max 1x/heure)
- **Offline**: Gérer le cas où l'utilisateur n'a pas de connexion

## 🔗 Ressources

- Documentation API: `backend/OURA_API_ENDPOINTS.md`
- Documentation migration: `OURA_TOKEN_MIGRATION_COMPLETE.md`
- Oura Cloud: https://cloud.ouraring.com/

---

**Date de création**: 4 février 2026  
**Statut**: 📝 À implémenter
