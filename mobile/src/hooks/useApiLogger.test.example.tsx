/**
 * EXEMPLE DE TEST VISUEL POUR LE API LOGGER
 * 
 * Ce composant peut être ajouté temporairement à une page pour tester le logger.
 * Il génère des requêtes de test pour voir comment elles apparaissent dans la page Requêtes.
 */

import { View, Text, Pressable, ScrollView } from 'react-native';
import { api } from '../lib/api-client';
import { useApiLogger } from './useApiLogger';

export function ApiLoggerTestPanel() {
  const { requests, clearRequests } = useApiLogger();
  
  // Générer des requêtes de test
  const testRequests = async () => {
    try {
      // Test GET (succès)
      await api.get('https://jsonplaceholder.typicode.com/posts/1');
      
      // Test POST (succès)
      await api.post('https://jsonplaceholder.typicode.com/posts', {
        title: 'Test Post',
        body: 'This is a test',
        userId: 1,
      });
      
      // Test PUT (succès)
      await api.put('https://jsonplaceholder.typicode.com/posts/1', {
        id: 1,
        title: 'Updated Title',
        body: 'Updated body',
        userId: 1,
      });
      
      // Test DELETE (succès)
      await api.delete('https://jsonplaceholder.typicode.com/posts/1');
      
      // Test GET (erreur 404)
      try {
        await api.get('https://jsonplaceholder.typicode.com/posts/999999');
      } catch (error) {
        console.log('Expected error:', error);
      }
      
      // Test POST (erreur - URL invalide)
      try {
        await api.post('https://invalid-url-that-does-not-exist.com/api', {
          data: 'test',
        });
      } catch (error) {
        console.log('Expected error:', error);
      }
      
      console.log('✅ Test requests completed!');
    } catch (error) {
      console.error('❌ Test failed:', error);
    }
  };
  
  return (
    <View style={{ padding: 20, backgroundColor: '#0a0a0a', borderRadius: 16 }}>
      <Text style={{ color: '#00FF41', fontSize: 18, fontWeight: '700', marginBottom: 16 }}>
        🧪 API Logger Test Panel
      </Text>
      
      <View style={{ gap: 12 }}>
        <Pressable
          onPress={testRequests}
          style={{
            backgroundColor: '#00FF4115',
            borderWidth: 1,
            borderColor: '#00FF41',
            borderRadius: 12,
            padding: 16,
            alignItems: 'center',
          }}
        >
          <Text style={{ color: '#00FF41', fontSize: 14, fontWeight: '600' }}>
            🚀 Générer des requêtes de test
          </Text>
        </Pressable>
        
        <Pressable
          onPress={clearRequests}
          style={{
            backgroundColor: '#FF444415',
            borderWidth: 1,
            borderColor: '#FF4444',
            borderRadius: 12,
            padding: 16,
            alignItems: 'center',
          }}
        >
          <Text style={{ color: '#FF4444', fontSize: 14, fontWeight: '600' }}>
            🗑️ Effacer tous les logs
          </Text>
        </Pressable>
      </View>
      
      <View style={{ marginTop: 16, paddingTop: 16, borderTopWidth: 1, borderTopColor: '#1a1a1a' }}>
        <Text style={{ color: '#666', fontSize: 13, marginBottom: 8 }}>
          📊 Stats actuelles :
        </Text>
        <View style={{ flexDirection: 'row', gap: 16 }}>
          <View>
            <Text style={{ color: '#00FF41', fontSize: 20, fontWeight: '700' }}>
              {requests.filter(r => r.status === 'success').length}
            </Text>
            <Text style={{ color: '#666', fontSize: 11 }}>Succès</Text>
          </View>
          <View>
            <Text style={{ color: '#FF4444', fontSize: 20, fontWeight: '700' }}>
              {requests.filter(r => r.status === 'error').length}
            </Text>
            <Text style={{ color: '#666', fontSize: 11 }}>Erreurs</Text>
          </View>
          <View>
            <Text style={{ color: '#FFD700', fontSize: 20, fontWeight: '700' }}>
              {requests.filter(r => r.status === 'pending').length}
            </Text>
            <Text style={{ color: '#666', fontSize: 11 }}>En cours</Text>
          </View>
          <View>
            <Text style={{ color: '#00BFFF', fontSize: 20, fontWeight: '700' }}>
              {requests.length}
            </Text>
            <Text style={{ color: '#666', fontSize: 11 }}>Total</Text>
          </View>
        </View>
      </View>
      
      <View style={{ marginTop: 16, paddingTop: 16, borderTopWidth: 1, borderTopColor: '#1a1a1a' }}>
        <Text style={{ color: '#666', fontSize: 11, lineHeight: 16 }}>
          💡 Après avoir cliqué sur "Générer des requêtes de test", allez dans l'onglet "Requêtes" pour voir les résultats.
        </Text>
      </View>
    </View>
  );
}

/**
 * COMMENT UTILISER CE TEST PANEL
 * 
 * 1. Importez le composant dans une page de test :
 * 
 * import { ApiLoggerTestPanel } from '@/src/hooks/useApiLogger.test.example';
 * 
 * 2. Ajoutez-le à votre page :
 * 
 * export default function TestScreen() {
 *   return (
 *     <ScrollView style={{ flex: 1, backgroundColor: '#000' }}>
 *       <SafeAreaView>
 *         <View style={{ padding: 20 }}>
 *           <ApiLoggerTestPanel />
 *         </View>
 *       </SafeAreaView>
 *     </ScrollView>
 *   );
 * }
 * 
 * 3. Cliquez sur "Générer des requêtes de test"
 * 
 * 4. Allez dans l'onglet "Requêtes" pour voir les résultats
 * 
 * 5. Vous devriez voir :
 *    - 4 requêtes réussies (GET, POST, PUT, DELETE)
 *    - 2 requêtes en erreur (404 et URL invalide)
 */
