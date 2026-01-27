/**
 * EXEMPLE D'UTILISATION DU API LOGGER
 * 
 * Ce fichier montre comment utiliser le logger API dans l'application.
 * Il n'est pas utilisé dans le code de production, c'est juste pour la documentation.
 */

import { api } from '../lib/api-client';
import { useApiLogger } from './useApiLogger';

// ============================================
// EXEMPLE 1: Utiliser le client API avec logging automatique
// ============================================

async function exampleFetchWithLogging() {
  try {
    // Toutes ces requêtes seront automatiquement loggées
    const data = await api.get('https://api.example.com/users');
    console.log('Users:', data);
    
    const newUser = await api.post('https://api.example.com/users', {
      name: 'John Doe',
      email: 'john@example.com',
    });
    console.log('Created user:', newUser);
    
    const updatedUser = await api.put(`https://api.example.com/users/${newUser.id}`, {
      name: 'Jane Doe',
    });
    console.log('Updated user:', updatedUser);
    
    await api.delete(`https://api.example.com/users/${newUser.id}`);
    console.log('User deleted');
  } catch (error) {
    console.error('Error:', error);
  }
}

// ============================================
// EXEMPLE 2: Utiliser le logger dans un composant React
// ============================================

import { View, Text, Button } from 'react-native';

function ExampleComponent() {
  const { requests, clearRequests } = useApiLogger();
  
  const handleFetch = async () => {
    // Cette requête sera automatiquement loggée
    await api.get('https://api.example.com/data');
  };
  
  return (
    <View>
      <Text>Total requests: {requests.length}</Text>
      <Button title="Fetch Data" onPress={handleFetch} />
      <Button title="Clear Logs" onPress={clearRequests} />
      
      {requests.map((req) => (
        <View key={req.id}>
          <Text>{req.method} {req.url}</Text>
          <Text>Status: {req.status}</Text>
        </View>
      ))}
    </View>
  );
}

// ============================================
// EXEMPLE 3: Logger manuellement une requête
// ============================================

async function exampleManualLogging() {
  const { addRequest, updateRequest } = useApiLogger.getState();
  
  // Créer un log de requête
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
    
    // Mettre à jour le log avec le succès
    updateRequest(requestId, {
      status: 'success',
      statusCode: response.status,
      duration,
      responseBody: data,
    });
    
    return data;
  } catch (error) {
    // Mettre à jour le log avec l'erreur
    updateRequest(requestId, {
      status: 'error',
      error: error instanceof Error ? error.message : 'Unknown error',
    });
    
    throw error;
  }
}

// ============================================
// EXEMPLE 4: Wrapper pour Supabase (optionnel)
// ============================================

import { supabase } from '../lib/supabase';

/**
 * Wrapper pour logger les requêtes Supabase
 * Note: Supabase utilise son propre système de requêtes,
 * donc on doit logger manuellement
 */
async function supabaseWithLogging<T>(
  operation: () => Promise<{ data: T | null; error: any }>,
  operationName: string
): Promise<T | null> {
  const { addRequest, updateRequest } = useApiLogger.getState();
  
  const requestId = addRequest({
    method: 'POST', // Supabase utilise généralement POST
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
        error: error.message || 'Supabase error',
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
    const duration = Date.now() - startTime;
    
    updateRequest(requestId, {
      status: 'error',
      duration,
      error: error instanceof Error ? error.message : 'Unknown error',
    });
    
    throw error;
  }
}

// Exemple d'utilisation avec Supabase
async function exampleSupabaseLogging() {
  const data = await supabaseWithLogging(
    () => supabase.rpc('get_latest_insight', { p_user_id: 'user-123' }),
    'get_latest_insight'
  );
  
  console.log('Insight:', data);
}

// ============================================
// EXEMPLE 5: Filtrer et analyser les logs
// ============================================

function analyzeApiLogs() {
  const { requests } = useApiLogger.getState();
  
  // Compter les requêtes par statut
  const statusCounts = requests.reduce((acc, req) => {
    acc[req.status] = (acc[req.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  console.log('Status counts:', statusCounts);
  
  // Calculer le temps moyen de réponse
  const successfulRequests = requests.filter(r => r.status === 'success' && r.duration);
  const avgDuration = successfulRequests.length > 0
    ? successfulRequests.reduce((sum, r) => sum + (r.duration || 0), 0) / successfulRequests.length
    : 0;
  
  console.log('Average duration:', avgDuration, 'ms');
  
  // Trouver les requêtes les plus lentes
  const slowestRequests = [...requests]
    .filter(r => r.duration)
    .sort((a, b) => (b.duration || 0) - (a.duration || 0))
    .slice(0, 5);
  
  console.log('Slowest requests:', slowestRequests);
  
  // Compter les erreurs par URL
  const errorsByUrl = requests
    .filter(r => r.status === 'error')
    .reduce((acc, req) => {
      acc[req.url] = (acc[req.url] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  
  console.log('Errors by URL:', errorsByUrl);
}

export {
  exampleFetchWithLogging,
  ExampleComponent,
  exampleManualLogging,
  supabaseWithLogging,
  exampleSupabaseLogging,
  analyzeApiLogs,
};
