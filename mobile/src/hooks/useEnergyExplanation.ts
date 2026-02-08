/**
 * Hook pour récupérer l'explication narrative du score d'énergie (Why-Stack)
 * Utilise React Query pour la gestion du cache et des états de chargement
 */

import { useQuery } from '@tanstack/react-query';
import { storage } from '@/lib/storage';
import { API_URL } from '@/config/api';

export interface EnergyMetric {
  label: string;
  value: number;
  unit: string;
}

export interface EnergyCard {
  type: 'nervous' | 'chemistry' | 'load';
  title: string;
  text: string;
  analogy: string;
  metrics?: {
    primary?: EnergyMetric;
    secondary?: EnergyMetric;
  };
}

export interface EnergyExplanation {
  energyScore: number;
  confidence: number;
  label: string;
  date: string;
  cards: EnergyCard[];
  error?: string;
}

interface UseEnergyExplanationOptions {
  userId: string;
  date?: string; // Format YYYY-MM-DD
  enabled?: boolean;
}

/**
 * Hook pour récupérer l'explication du score d'énergie
 * 
 * @example
 * ```tsx
 * const { data, isLoading, error, refetch } = useEnergyExplanation({
 *   userId: 'user-123',
 *   date: '2026-02-01'
 * });
 * 
 * if (isLoading) return <LoadingSkeleton />;
 * if (error) return <ErrorView message={error.message} />;
 * 
 * return <WhyEnergyStack cards={data.cards} />;
 * ```
 */
export function useEnergyExplanation({
  userId,
  date,
  enabled = true,
}: UseEnergyExplanationOptions) {
  console.log('[useEnergyExplanation] 🎯 Hook called with:', { userId, date, enabled });
  console.log('[useEnergyExplanation] 🔧 Enabled check:', { enabled, hasUserId: !!userId, finalEnabled: enabled && !!userId });
  
  const query = useQuery<EnergyExplanation, Error>({
    // ✅ Version v4 avec Gemini 3 Pro RAW TEXT - force un nouveau fetch
    queryKey: ['energy', 'explanation', 'v4-raw-text', userId, date],
    queryFn: async () => {
      console.log('[useEnergyExplanation] 🚨🚨🚨 QUERY FN CALLED - FETCHING FROM API 🚨🚨🚨');
      console.log('[useEnergyExplanation] 📡 START Fetching explanation...');
      console.log('[useEnergyExplanation] 🔑 Query key:', ['energy', 'explanation', 'v4-raw-text', userId, date]);
      
      // Récupérer le userId pour l'auth
      const storedUserId = await storage.getUserId();
      console.log('[useEnergyExplanation] 🔑 StoredUserId:', storedUserId);
      
      if (!storedUserId) {
        console.error('[useEnergyExplanation] ❌ No stored userId found');
        throw new Error('User ID not found');
      }
      
      // Construire l'URL
      const params = new URLSearchParams();
      if (date) {
        params.append('date', date);
      }

      const url = `${API_URL}/api/energy/explain/${userId}${params.toString() ? `?${params.toString()}` : ''}`;
      console.log('[useEnergyExplanation] 🔗 Full URL:', url);
      
      try {
        console.log('[useEnergyExplanation] 🚀 Sending fetch request...');
        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${storedUserId}`,
            'Content-Type': 'application/json',
          },
        });
        
        console.log('[useEnergyExplanation] 📥 Response status:', response.status);
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error('[useEnergyExplanation] ❌ HTTP error:', response.status, errorText);
          throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        const data: EnergyExplanation = await response.json();
        console.log('[useEnergyExplanation] ✅ Response received:', JSON.stringify(data, null, 2));
        console.log('[useEnergyExplanation] 📊 Cards count:', data.cards?.length || 0);
        
        // ✅ Même si data.error existe, on retourne les données
        // Car "Données insuffisantes" est une réponse valide avec des cartes à afficher
        if (data.error) {
          console.warn('[useEnergyExplanation] ⚠️ Response contains error field:', data.error);
          console.log('[useEnergyExplanation] 📦 But returning data anyway (has cards)');
        }

        return data;
      } catch (error) {
        console.error('[useEnergyExplanation] ❌ Fetch error:', error);
        throw error;
      }
    },
    enabled: enabled && !!userId,
    staleTime: 0, // Pas de cache - toujours fetch à nouveau
    gcTime: 0, // Pas de cache (garbage collection immédiate)
    retry: 2,
    refetchOnMount: 'always', // ✅ Force un refetch à chaque montage du composant
  });

  // Log l'état de la query
  console.log('[useEnergyExplanation] 📊 Query state:', {
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    isError: query.isError,
    hasData: !!query.data,
    cardsCount: query.data?.cards?.length || 0
  });

  return query;
}

/**
 * Retourne l'icône appropriée selon le type de carte
 */
export function getCardIcon(type: EnergyCard['type']): string {
  switch (type) {
    case 'nervous':
      return '⚡️';
    case 'chemistry':
      return '💊';
    case 'load':
      return '🎒';
    default:
      return '💡';
  }
}

/**
 * Retourne la couleur de thème selon le type de carte
 */
export function getCardColor(type: EnergyCard['type']): {
  border: string;
  background: string;
  accent: string;
} {
  switch (type) {
    case 'nervous':
      return {
        border: 'rgba(255, 69, 58, 0.3)', // Rouge SF Symbols
        background: 'rgba(255, 69, 58, 0.1)',
        accent: '#FF453A',
      };
    case 'chemistry':
      return {
        border: 'rgba(255, 159, 10, 0.3)', // Orange SF Symbols
        background: 'rgba(255, 159, 10, 0.1)',
        accent: '#FF9F0A',
      };
    case 'load':
      return {
        border: 'rgba(255, 214, 10, 0.3)', // Jaune SF Symbols
        background: 'rgba(255, 214, 10, 0.1)',
        accent: '#FFD60A',
      };
    default:
      return {
        border: 'rgba(100, 100, 100, 0.3)',
        background: 'rgba(100, 100, 100, 0.1)',
        accent: '#888888',
      };
  }
}

/**
 * Formatte une métrique pour l'affichage
 */
export function formatMetric(metric: EnergyMetric): string {
  return `${metric.value}${metric.unit}`;
}
