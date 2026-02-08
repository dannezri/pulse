/**
 * Hook Métier: Récupération des Données Brief via API Wellness Coach
 * 
 * Ce hook appelle le backend qui:
 * - Récupère toutes les métriques biométriques
 * - Calcule le Score Pulse
 * - Génère les cartes Brief via l'IA (GPT-4o)
 * - Utilise un cache intelligent pour optimiser les coûts
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { BriefData, BriefCard } from '../types/brief';
import { generateBrief } from '../services/briefApi';
import { generateEmptyState } from '../utils/briefTemplates';
import { useRouter } from 'expo-router';
import { useState } from 'react';

/**
 * Mappe les actions de l'API vers les routes de l'application
 */
function handleAction(action: string, router: any) {
  const actionMap: Record<string, string> = {
    'view_details': '/profile',
    'connect_sources': '/connections',
    'start_activity': '/connections', // TODO: créer une page d'activité
    'view_calendar': '/requests', // Temporaire: utiliser la page webhooks
  };
  
  const route = actionMap[action];
  if (route) {
    router.push(route as any);
  } else {
    console.warn(`Unknown action: ${action}`);
  }
}

/**
 * Récupère les données du Brief via l'API backend
 */
async function fetchBriefData(userId: string | null, router: any, forceRefresh: boolean = false): Promise<BriefData> {
  if (!userId) {
    return {
      pulseScore: 0,
      state: 'neutral',
      weakestMetric: 'N/A',
      weakestMetricImpact: 0,
      cards: [generateEmptyState(false, () => router.push('/connections' as any))],
      lastUpdated: new Date(),
    };
  }

  try {
    console.log('[fetchBriefData] 📡 Appel API generateBrief, forceRefresh:', forceRefresh);
    // Appel à l'API backend Wellness Coach
    const response = await generateBrief(userId, forceRefresh);
    console.log('[fetchBriefData] ✅ Réponse reçue, has_intraday:', !!response.intraday_energy_forecast);
    
    // Transformer la réponse API en BriefCard[]
    const cards: BriefCard[] = response.cards.map((apiCard) => ({
      ...apiCard,
      actionButton: apiCard.actionButton ? {
        label: apiCard.actionButton.label,
        onPress: () => handleAction(apiCard.actionButton!.action, router),
      } : undefined,
    }));

    return {
      pulseScore: response.pulseScore,
      state: cards[0]?.state || 'neutral',
      weakestMetric: 'N/A', // L'IA ne retourne pas cette info directement
      weakestMetricImpact: 0,
      cards,
      lastUpdated: new Date(response.analyzed_at),
      intraday_energy_forecast: response.intraday_energy_forecast,
    };
  } catch (error) {
    console.error('Error fetching Brief from API:', error);
    
    // Fallback: retourner une carte d'erreur
    return {
      pulseScore: 0,
      state: 'neutral',
      weakestMetric: 'N/A',
      weakestMetricImpact: 0,
      cards: [{
        id: 'error',
        type: 'empty',
        title: 'Erreur de connexion',
        content: 'Impossible de charger le Brief. Vérifiez votre connexion et réessayez.',
        state: 'neutral',
        iconName: 'AlertTriangle',
        priority: 0,
        actionButton: {
          label: 'Réessayer',
          onPress: () => window.location.reload(),
        },
      }],
      lastUpdated: new Date(),
    };
  }
}

export function useBriefData(userId: string | null) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [forceRefreshFlag, setForceRefreshFlag] = useState(0);
  
  const query = useQuery<BriefData, Error>({
    queryKey: ['briefData', userId, forceRefreshFlag],
    queryFn: () => fetchBriefData(userId, router, forceRefreshFlag > 0),
    enabled: !!userId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2, // Réessayer 2 fois en cas d'erreur
  });
  
  // Fonction de refetch avec force_refresh
  const refetchWithForce = async () => {
    console.log('[useBriefData] 🔄 Force refresh demandé');
    // Incrémente le flag pour forcer un nouveau fetch avec force_refresh=true
    setForceRefreshFlag(prev => {
      const newFlag = prev + 1;
      console.log('[useBriefData] 📊 ForceRefreshFlag:', prev, '->', newFlag);
      return newFlag;
    });
  };
  
  // Remplacer refetch par une version qui force le refresh backend
  return {
    ...query,
    refetch: refetchWithForce,
  };
}
