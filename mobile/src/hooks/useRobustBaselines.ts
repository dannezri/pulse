/**
 * Hook pour récupérer les baselines ROBUSTES (median/IQR)
 * 
 * NOUVEAU: Remplace l'ancien useBaselines en utilisant la nouvelle table user_baselines
 * avec statistiques robustes (median/IQR au lieu de mean/std)
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import { storage } from '@/lib/storage';
import Constants from 'expo-constants';
import { RobustBaseline, RobustBaselines } from '../types/baselines';

export interface UseRobustBaselinesResult {
  baselines: RobustBaselines | undefined;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<UseQueryResult<RobustBaselines, Error>>;
  triggerRecalculation: () => Promise<boolean>;
}

/**
 * Hook principal pour les baselines robustes
 */
export function useRobustBaselines(userId: string | null): UseRobustBaselinesResult {
  // Fetch baselines via nouvelle RPC function
  const { data, isLoading, error, refetch } = useQuery<RobustBaselines, Error>({
    queryKey: ['baselines-robust', userId],
    queryFn: async () => {
      console.log('[useRobustBaselines] Fetching baselines for user:', userId);
      
      if (!userId) {
        console.log('[useRobustBaselines] No user ID provided');
        throw new Error('User ID is required');
      }

      // Appeler la nouvelle RPC function
      const { data, error } = await supabase.rpc('get_user_baselines_robust', {
        p_user_id: userId,
        p_model_version: 'baseline_v2_robust'  // Version actuelle
      });

      if (error) {
        console.error('[useRobustBaselines] RPC error:', error);
        throw error;
      }

      console.log('[useRobustBaselines] Received data:', data);
      
      // Transformer le tableau en objet {metric: baseline}
      const baselines: RobustBaselines = {};
      
      if (Array.isArray(data)) {
        for (const row of data) {
          baselines[row.baseline_type] = {
            median: row.median,
            iqr: row.iqr,
            p25: row.p25,
            p75: row.p75,
            mean: row.mean ?? undefined,
            std: row.std ?? undefined,
            sample_count: row.sample_count,
            confidence: row.confidence as 'low' | 'medium' | 'high',
            calculated_at: row.calculated_at,
            model_version: 'baseline_v2_robust'
          };
        }
      }
      
      console.log('[useRobustBaselines] Transformed baselines:', Object.keys(baselines));
      return baselines;
    },
    enabled: !!userId,
    staleTime: 24 * 60 * 60 * 1000, // 24h - Les baselines ne changent qu'une fois par jour (cron)
    gcTime: 7 * 24 * 60 * 60 * 1000, // 7 jours de cache
    refetchOnMount: 'always', // Toujours refetch au mount
    refetchOnWindowFocus: false, // Ne pas refetch au focus
  });

  /**
   * Déclenche un recalcul manuel des baselines
   * Appelle l'endpoint backend protégé par JWT utilisateur
   */
  const triggerRecalculation = async (): Promise<boolean> => {
    if (!userId) {
      console.error('No user ID, cannot trigger recalculation');
      return false;
    }

    try {
      // Récupérer le token d'authentification
      const token = await storage.getAccessToken();
      if (!token) {
        console.error('No access token found');
        return false;
      }

      // Récupérer l'URL du backend depuis la config
      const backendUrl = Constants.expoConfig?.extra?.backendUrl || 'http://localhost:9000';

      // Appeler l'endpoint
      const response = await fetch(`${backendUrl}/api/baselines/calculate/${userId}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Failed to trigger recalculation:', response.status, errorText);
        return false;
      }

      console.log('[useRobustBaselines] Recalculation triggered successfully');

      // Invalider le cache et refetch
      await refetch();

      return true;
    } catch (error) {
      console.error('Error triggering recalculation:', error);
      return false;
    }
  };

  return {
    baselines: data,
    loading: isLoading,
    error: error,
    refetch: refetch as any,
    triggerRecalculation,
  };
}

/**
 * Hook helper pour récupérer une baseline spécifique
 */
export function useRobustBaseline(
  userId: string | null,
  metric: string
): RobustBaseline | undefined {
  const { baselines } = useRobustBaselines(userId);
  return baselines?.[metric];
}

/**
 * Hook helper pour récupérer plusieurs baselines
 */
export function useRobustBaselinesMultiple(
  userId: string | null,
  metrics: string[]
): Partial<RobustBaselines> {
  const { baselines } = useRobustBaselines(userId);
  
  if (!baselines) return {};
  
  const result: Partial<RobustBaselines> = {};
  for (const metric of metrics) {
    if (baselines[metric]) {
      result[metric] = baselines[metric];
    }
  }
  
  return result;
}
