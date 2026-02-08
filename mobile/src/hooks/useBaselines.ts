import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import { storage } from '@/lib/storage';
import Constants from 'expo-constants';

// ============================================
// TYPES (Structure standardisée JSONB)
// ============================================

export interface BaselineData {
  value: number;
  unit: string;
  normal_range: {
    min: number;
    max: number;
  };
  trend: {
    slope_per_week: number;
    direction: 'up' | 'down' | 'flat';
  };
  details: Record<string, any>; // Spécifique à chaque type de baseline
}

export interface Baseline {
  baseline_type: string;
  baseline_data: BaselineData;
  calculated_at: string;
  confidence: number;
  sample_size: number;
  model_version: string;
  window_start: string | null;
  window_end: string | null;
  status: 'ok' | 'insufficient_data' | 'error';
  error_message: string | null;
}

export interface UseBaselinesResult {
  baselines: Baseline[] | undefined;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<UseQueryResult<Baseline[], Error>>;
  triggerRecalculation: () => Promise<boolean>;
}

// ============================================
// HOOK useBaselines
// ============================================

export function useBaselines(userId: string | null): UseBaselinesResult {
  // Fetch baselines via RPC function
  const { data, isLoading, error, refetch } = useQuery<Baseline[], Error>({
    queryKey: ['baselines', userId],
    queryFn: async () => {
      console.log('[useBaselines] Fetching baselines for user:', userId);
      
      if (!userId) {
        console.log('[useBaselines] No user ID provided');
        throw new Error('User ID is required');
      }

      const { data, error } = await supabase.rpc('get_user_baselines', {
        p_user_id: userId,
      });

      if (error) {
        console.error('[useBaselines] RPC error:', error);
        throw error;
      }

      console.log('[useBaselines] Received data:', data);
      return (data as Baseline[]) || [];
    },
    enabled: !!userId,
    staleTime: 24 * 60 * 60 * 1000, // 24h - Les baselines ne changent qu'une fois par jour (cron)
    gcTime: 7 * 24 * 60 * 60 * 1000, // 7 jours de cache (anciennement cacheTime)
    refetchOnMount: 'always', // Toujours refetch au mount pour s'assurer d'avoir les données
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
