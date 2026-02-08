import { useQuery } from '@tanstack/react-query';
import { supabase } from '../lib/supabase';
import { calculateReadiness, ReadinessResult } from '../utils/calculateReadiness';

async function fetchReadinessScore(userId: string | null): Promise<ReadinessResult | null> {
  if (!userId) return null;

  // 1. Récupérer le profil (baselines + target_sleep_minutes)
  const { data: profile } = await supabase
    .from('profiles')
    .select('baseline_hrv, baseline_resting_hr, target_sleep_minutes')
    .eq('id', userId)
    .single();

  if (!profile) return null;

  // 2. Récupérer les dernières biométrics (24h jusqu'à maintenant)
  const now = new Date();
  const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);

  const { data: biometrics } = await supabase
    .from('biometrics')
    .select('metric_type, value, recorded_at')
    .eq('user_id', userId)
    .gte('recorded_at', yesterday.toISOString())
    .lte('recorded_at', now.toISOString()) // Explicitly include up to current time
    .order('recorded_at', { ascending: false });

  // 3. Extraire les valeurs actuelles
  // Note: Oura stocke 'hr' pas 'heart_rate', et HRV n'est pas toujours disponible
  const currentHRV = biometrics?.find(b => b.metric_type === 'hrv')?.value || null;
  const currentRHR = biometrics?.find(b => b.metric_type === 'hr' || b.metric_type === 'heart_rate')?.value || null;
  const sleepMinutes = biometrics?.find(b => b.metric_type === 'sleep_duration' || b.metric_type === 'sleep')?.value || null;

  // 4. Calculer le score
  return calculateReadiness({
    currentHRV,
    baselineHRV: profile.baseline_hrv,
    sleepMinutes,
    targetSleepMinutes: profile.target_sleep_minutes || 480,
    currentRHR,
    baselineRHR: profile.baseline_resting_hr,
  });
}

export function useReadinessScore(userId: string | null) {
  return useQuery({
    queryKey: ['readinessScore', userId],
    queryFn: () => fetchReadinessScore(userId),
    enabled: !!userId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
