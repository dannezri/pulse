import { useQuery } from '@tanstack/react-query';
import { Anomaly, GlobalState } from './useAnomalyDetection';
import { API_URL } from '../config/api';

interface MainInsight {
  content: string;
  state: GlobalState;
  priority: number;
  anomalies_count?: number;
}

interface MainInsightResponse {
  status: string;
  insight: MainInsight;
}

async function fetchMainInsight(
  userId: string | null,
  anomalies: Anomaly[]
): Promise<MainInsight> {
  if (!userId) {
    return {
      content: "Connectez-vous pour voir votre état.",
      state: 'calm',
      priority: 1,
    };
  }

  // Si pas d'anomalies, retourner insight "calm" sans appeler le backend
  if (!anomalies || anomalies.length === 0) {
    return {
      content: "Votre corps est en parfaite homéostasie. Profitez de ce pic d'énergie.",
      state: 'calm',
      priority: 1,
      anomalies_count: 0,
    };
  }

  // Appeler le backend avec les top 3 anomalies
  console.log('[useMainInsight] Fetching insight for', anomalies.length, 'anomalies');

  try {
    const response = await fetch(`${API_URL}/api/insights/prioritized`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        anomalies: anomalies.slice(0, 3), // Top 3 seulement
      }),
    });

    if (!response.ok) {
      console.error('[useMainInsight] Error response:', response.status);
      // Fallback si erreur
      return {
        content: "Une anomalie a été détectée dans vos données. Consultez les détails.",
        state: 'warning',
        priority: 1,
      };
    }

    const data: MainInsightResponse = await response.json();
    
    console.log('[useMainInsight] Received insight:', data.insight.content.substring(0, 50) + '...');
    
    return data.insight;
  } catch (error) {
    console.error('[useMainInsight] Error fetching insight:', error);
    // Fallback si erreur réseau
    return {
      content: "Impossible de générer un insight. Vérifiez votre connexion.",
      state: 'calm',
      priority: 1,
    };
  }
}

/**
 * Hook pour récupérer l'insight principal basé sur les anomalies détectées
 * Appelle le backend uniquement si des anomalies sont présentes
 */
export function useMainInsight(
  userId: string | null,
  anomalies: Anomaly[]
) {
  // Créer une clé stable pour les anomalies (pour éviter les re-renders inutiles)
  const anomaliesKey = anomalies
    .map(a => `${a.metric}:${a.z_score.toFixed(1)}`)
    .join(',');

  return useQuery({
    queryKey: ['mainInsight', userId, anomaliesKey],
    queryFn: () => fetchMainInsight(userId, anomalies),
    enabled: !!userId,
    staleTime: 5 * 60 * 1000, // 5 minutes (les insights ne changent pas souvent)
    refetchOnMount: false,
    refetchOnWindowFocus: false,
  });
}

export type { MainInsight };
