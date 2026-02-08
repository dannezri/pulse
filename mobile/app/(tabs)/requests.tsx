/**
 * Page d'affichage de toutes les nouvelles données Supabase (biometrics, insights, meals)
 */

import { View, Text, ScrollView, Pressable, RefreshControl, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Activity, Heart, Lightbulb, Utensils, Filter } from 'lucide-react-native';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { API_URL } from '../../src/config/api';
import { storage } from '../../src/lib/storage';
import { DataEntryCard } from '../../src/components/DataEntryCard';
import type { DataEntry } from '../../src/components/DataEntryCard';

export default function DataScreen() {
  const [filterType, setFilterType] = useState<string>('ALL');
  
  // Récupérer les données depuis le backend
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['recent-data'],
    queryFn: async () => {
      const userId = await storage.getUserId();
      
      if (!userId) {
        throw new Error('User not authenticated');
      }
      
      const response = await fetch(`${API_URL}/api/data/recent?user_id=${userId}&limit=100`);
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to fetch data: ${errorText}`);
      }
      
      const result = await response.json();
      return result.entries as DataEntry[];
    },
    refetchInterval: 10000, // Rafraîchir toutes les 10 secondes
  });
  
  const entries = data || [];
  
  // Filtrer les données
  const filteredEntries = entries.filter((entry) => {
    if (filterType === 'ALL') return true;
    if (filterType === 'BIOMETRIC') return entry.type === 'biometric';
    if (filterType === 'INSIGHT') return entry.type === 'insight';
    if (filterType === 'MEAL') return entry.type === 'meal';
    return true;
  });
  
  // Stats
  const stats = {
    total: entries.length,
    biometrics: entries.filter(e => e.type === 'biometric').length,
    insights: entries.filter(e => e.type === 'insight').length,
    meals: entries.filter(e => e.type === 'meal').length,
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
              <Activity size={24} color="#00FF41" />
            </View>
            <View>
              <Text style={{ color: '#FFFFFF', fontSize: 24, fontWeight: '700' }}>
                Nouvelles Données
              </Text>
              <Text style={{ color: '#666', fontSize: 14, marginTop: 2 }}>
                {filteredEntries.length} entrée{filteredEntries.length > 1 ? 's' : ''}
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
            borderColor: '#00BFFF30',
            minWidth: 120,
          }}
        >
          <Text style={{ color: '#00BFFF', fontSize: 28, fontWeight: '700' }}>
            {stats.biometrics}
          </Text>
          <Text style={{ color: '#666', fontSize: 13, marginTop: 4 }}>
            Biométrie
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
            {stats.insights}
          </Text>
          <Text style={{ color: '#666', fontSize: 13, marginTop: 4 }}>
            Insights
          </Text>
        </View>
        
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
            {stats.meals}
          </Text>
          <Text style={{ color: '#666', fontSize: 13, marginTop: 4 }}>
            Repas
          </Text>
        </View>
        
        <View
          style={{
            backgroundColor: '#0a0a0a',
            borderRadius: 12,
            padding: 16,
            borderWidth: 1,
            borderColor: '#88888830',
            minWidth: 120,
          }}
        >
          <Text style={{ color: '#888', fontSize: 28, fontWeight: '700' }}>
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
          {(['ALL', 'BIOMETRIC', 'INSIGHT', 'MEAL'] as const).map((type) => {
            const icons = {
              ALL: Filter,
              BIOMETRIC: Heart,
              INSIGHT: Lightbulb,
              MEAL: Utensils,
            };
            const Icon = icons[type];
            const labels = {
              ALL: 'Tout',
              BIOMETRIC: 'Biométrie',
              INSIGHT: 'Insights',
              MEAL: 'Repas',
            };
            
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
                  {labels[type]}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </View>
      
      {/* Liste des données */}
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
        {isLoading && entries.length === 0 ? (
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
              <ActivityIndicator size="large" color="#00FF41" />
            </View>
            <Text style={{ color: '#666', fontSize: 16, textAlign: 'center' }}>
              Chargement des données...
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
              <Activity size={36} color="#FF4444" />
            </View>
            <Text style={{ color: '#FF4444', fontSize: 16, textAlign: 'center', fontWeight: '600' }}>
              Erreur de chargement
            </Text>
            <Text style={{ color: '#666', fontSize: 14, textAlign: 'center', marginTop: 8, paddingHorizontal: 40 }}>
              {error instanceof Error ? error.message : 'Erreur inconnue'}
            </Text>
          </View>
        ) : filteredEntries.length === 0 ? (
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
              <Activity size={36} color="#333" />
            </View>
            <Text style={{ color: '#666', fontSize: 16, textAlign: 'center' }}>
              {entries.length === 0 
                ? "Aucune donnée disponible"
                : "Aucune donnée ne correspond aux filtres"}
            </Text>
            {entries.length === 0 && (
              <Text style={{ color: '#444', fontSize: 13, textAlign: 'center', marginTop: 8, paddingHorizontal: 40 }}>
                Les nouvelles données apparaîtront ici automatiquement
              </Text>
            )}
          </View>
        ) : (
          filteredEntries.map((entry) => (
            <DataEntryCard key={`${entry.type}-${entry.id}`} entry={entry} />
          ))
        )}
      </ScrollView>
    </SafeAreaView>
  );
}
