import { useQuery } from '@tanstack/react-query';
import { supabase } from '../lib/supabase';

interface HealthProfile {
  id: string;
  user_id: string;
  date: string;
  profile_data: {
    current_metrics: {
      hrv?: { latest_ms: number; average_ms: number };
      heart_rate?: { resting_bpm: number; average_bpm: number };
      sleep?: { duration_minutes: number; quality_score: number };
    };
    baselines: {
      hrv_baseline: number;
      hr_baseline: number;
      sleep_baseline: number;
    };
  };
  created_at: string;
}

async function fetchHealthProfile(userId: string | null): Promise<HealthProfile | null> {
  if (!userId) return null;

  // Récupère le profil de santé le plus récent (incluant le jour actuel si disponible)
  const { data, error } = await supabase
    .from('health_profiles')
    .select('*')
    .eq('user_id', userId)
    .order('date', { ascending: false })
    .limit(1)
    .single();

  if (error) {
    if (error.code === 'PGRST116') {
      // No rows returned
      return null;
    }
    console.error('Error fetching health profile:', error);
    throw error;
  }

  return data;
}

export function useHealthProfile(userId: string | null) {
  return useQuery({
    queryKey: ['healthProfile', userId],
    queryFn: () => fetchHealthProfile(userId),
    enabled: !!userId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}
