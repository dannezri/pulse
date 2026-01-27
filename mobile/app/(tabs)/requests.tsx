/**
 * Page d'affichage de tous les webhooks reçus par le backend
 */

import { View, Text, ScrollView, Pressable, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Activity, Webhook, Database, Zap } from 'lucide-react-native';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { API_URL } from '../../src/config/api';
import { storage } from '../../src/lib/storage';
import { WebhookCard } from '../../src/components/WebhookCard';
import type { WebhookLog } from '../../src/components/WebhookCard';

export default function WebhooksScreen() {
  const [filterType, setFilterType] = useState<string>('ALL');
  
  // Récupérer les webhooks depuis le backend
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['webhooks'],
    queryFn: async () => {
      const userId = await storage.getUserId();
      
      if (!userId) {
        throw new Error('User not authenticated');
      }
      
      const response = await fetch(`${API_URL}/api/webhooks/logs?user_id=${userId}&limit=100`);
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to fetch webhooks: ${errorText}`);
      }
      
      const result = await response.json();
      return result.logs as WebhookLog[];
    },
    refetchInterval: 10000, // Rafraîchir toutes les 10 secondes
  });
  
  const webhooks = data || [];
  
  // Filtrer les webhooks
  const filteredWebhooks = webhooks.filter((webhook) => {
    if (filterType === 'ALL') return true;
    if (filterType === 'HISTORICAL') return webhook.event_type?.includes('historical');
    if (filterType === 'TIMESERIES') return webhook.event_type?.includes('timeseries');
    if (filterType === 'DAILY') return webhook.event_type?.includes('daily');
    return true;
  });
  
  // Stats
  const stats = {
    total: webhooks.length,
    success: webhooks.filter(w => w.status_code >= 200 && w.status_code < 300).length,
    error: webhooks.filter(w => w.status_code >= 400).length,
    avgDuration: webhooks.filter(w => w.duration_ms).length > 0
      ? Math.round(
          webhooks.filter(w => w.duration_ms).reduce((acc, w) => acc + (w.duration_ms || 0), 0) /
          webhooks.filter(w => w.duration_ms).length
        )
      : 0,
  };
  
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#000000' }}>
      {/* Header */}
      <View style={{ padding: 20, paddingBottom: 16 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
            <View
              style={{
                width: 48,
                height: 48,
                borderRadius: 16,
                backgroundColor: '#00FF4115',
                justifyContent: 'center',
                alignItems: 'center',
              }}
            >
              <Webhook size={24} color="#00FF41" />
            </View>
            <View>
              <Text style={{ color: '#FFFFFF', fontSize: 24, fontWeight: '700' }}>
                Webhooks Vital
              </Text>
              <Text style={{ color: '#666', fontSize: 14, marginTop: 2 }}>
                {filteredWebhooks.length} webhook{filteredWebhooks.length > 1 ? 's' : ''}
              </Text>
            </View>
          </View>
        </View>
      </View>
      
      {/* Stats Cards */}
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ paddingHorizontal: 20, gap: 12, paddingBottom: 16 }}
      >
        <View
          style={{
            backgroundColor: '#0a0a0a',
            borderRadius: 12,
            padding: 16,
            borderWidth: 1,
            borderColor: '#00FF4130',
            minWidth: 120,
          }}
        >
          <Text style={{ color: '#00FF41', fontSize: 28, fontWeight: '700' }}>
            {stats.success}
          </Text>
          <Text style={{ color: '#666', fontSize: 13, marginTop: 4 }}>
            Succès
          </Text>
        </View>
        
        <View
          style={{
            backgroundColor: '#0a0a0a',
            borderRadius: 12,
            padding: 16,
            borderWidth: 1,
            borderColor: '#FF444430',
            minWidth: 120,
          }}
        >
          <Text style={{ color: '#FF4444', fontSize: 28, fontWeight: '700' }}>
            {stats.error}
          </Text>
          <Text style={{ color: '#666', fontSize: 13, marginTop: 4 }}>
            Erreurs
          </Text>
        </View>
        
        <View
          style={{
            backgroundColor: '#0a0a0a',
            borderRadius: 12,
            padding: 16,
            borderWidth: 1,
            borderColor: '#00BFFF30',
            minWidth: 120,
          }}
        >
          <View style={{ flexDirection: 'row', alignItems: 'baseline', gap: 4 }}>
            <Text style={{ color: '#00BFFF', fontSize: 28, fontWeight: '700' }}>
              {stats.avgDuration}
            </Text>
            <Text style={{ color: '#00BFFF', fontSize: 16 }}>ms</Text>
          </View>
          <Text style={{ color: '#666', fontSize: 13, marginTop: 4 }}>
            Temps moyen
          </Text>
        </View>
        
        <View
          style={{
            backgroundColor: '#0a0a0a',
            borderRadius: 12,
            padding: 16,
            borderWidth: 1,
            borderColor: '#FFD70030',
            minWidth: 120,
          }}
        >
          <Text style={{ color: '#FFD700', fontSize: 28, fontWeight: '700' }}>
            {stats.total}
          </Text>
          <Text style={{ color: '#666', fontSize: 13, marginTop: 4 }}>
            Total
          </Text>
        </View>
      </ScrollView>
      
      {/* Filtres */}
      <View style={{ paddingHorizontal: 20, paddingBottom: 12 }}>
        <View style={{ flexDirection: 'row', gap: 8, flexWrap: 'wrap' }}>
          {(['ALL', 'HISTORICAL', 'TIMESERIES', 'DAILY'] as const).map((type) => {
            const icons = {
              ALL: Activity,
              HISTORICAL: Database,
              TIMESERIES: Activity,
              DAILY: Zap,
            };
            const Icon = icons[type];
            
            return (
              <Pressable
                key={type}
                onPress={() => setFilterType(type)}
                style={{
                  flexDirection: 'row',
                  alignItems: 'center',
                  gap: 6,
                  paddingHorizontal: 12,
                  paddingVertical: 6,
                  borderRadius: 8,
                  backgroundColor: filterType === type ? '#00FF4115' : '#0a0a0a',
                  borderWidth: 1,
                  borderColor: filterType === type ? '#00FF41' : '#1a1a1a',
                }}
              >
                <Icon size={14} color={filterType === type ? '#00FF41' : '#666'} />
                <Text
                  style={{
                    color: filterType === type ? '#00FF41' : '#666',
                    fontSize: 12,
                    fontWeight: '600',
                  }}
                >
                  {type}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </View>
      
      {/* Liste des webhooks */}
      <ScrollView
        contentContainerStyle={{
          padding: 20,
          paddingTop: 8,
        }}
        refreshControl={
          <RefreshControl
            refreshing={isLoading}
            onRefresh={refetch}
            tintColor="#00FF41"
          />
        }
      >
        {isLoading && webhooks.length === 0 ? (
          <View
            style={{
              flex: 1,
              justifyContent: 'center',
              alignItems: 'center',
              paddingVertical: 60,
            }}
          >
            <View
              style={{
                width: 80,
                height: 80,
                borderRadius: 20,
                backgroundColor: '#0a0a0a',
                justifyContent: 'center',
                alignItems: 'center',
                marginBottom: 16,
              }}
            >
              <Webhook size={36} color="#00FF41" />
            </View>
            <Text style={{ color: '#666', fontSize: 16, textAlign: 'center' }}>
              Chargement des webhooks...
            </Text>
          </View>
        ) : error ? (
          <View
            style={{
              flex: 1,
              justifyContent: 'center',
              alignItems: 'center',
              paddingVertical: 60,
            }}
          >
            <View
              style={{
                width: 80,
                height: 80,
                borderRadius: 20,
                backgroundColor: '#0a0a0a',
                justifyContent: 'center',
                alignItems: 'center',
                marginBottom: 16,
              }}
            >
              <Webhook size={36} color="#FF4444" />
            </View>
            <Text style={{ color: '#FF4444', fontSize: 16, textAlign: 'center', marginBottom: 8 }}>
              Erreur de chargement
            </Text>
            <Text style={{ color: '#666', fontSize: 13, textAlign: 'center', paddingHorizontal: 40 }}>
              {error instanceof Error ? error.message : 'Une erreur est survenue'}
            </Text>
          </View>
        ) : filteredWebhooks.length === 0 ? (
          <View
            style={{
              flex: 1,
              justifyContent: 'center',
              alignItems: 'center',
              paddingVertical: 60,
            }}
          >
            <View
              style={{
                width: 80,
                height: 80,
                borderRadius: 20,
                backgroundColor: '#0a0a0a',
                justifyContent: 'center',
                alignItems: 'center',
                marginBottom: 16,
              }}
            >
              <Webhook size={36} color="#333" />
            </View>
            <Text style={{ color: '#666', fontSize: 16, textAlign: 'center' }}>
              {webhooks.length === 0 
                ? "Aucun webhook reçu"
                : "Aucun webhook ne correspond aux filtres"}
            </Text>
            {webhooks.length === 0 && (
              <Text style={{ color: '#444', fontSize: 13, textAlign: 'center', marginTop: 8, paddingHorizontal: 40 }}>
                Les webhooks Vital apparaîtront ici automatiquement
              </Text>
            )}
          </View>
        ) : (
          filteredWebhooks.map((webhook) => (
            <WebhookCard key={webhook.id} webhook={webhook} />
          ))
        )}
      </ScrollView>
    </SafeAreaView>
  );
}
