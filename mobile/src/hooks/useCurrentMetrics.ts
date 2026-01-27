import { useQuery } from '@tanstack/react-query';
import { supabase } from '../lib/supabase';

interface CurrentMetrics {
  // Activity
  steps: number | null;
  distance: number | null;
  calories: number | null;
  active_calories: number | null;
  floors_climbed: number | null;
  
  // Vitals
  hrv: number | null;
  hr: number | null;
  spo2: number | null;
  glucose: number | null;
  respiratory_rate: number | null;
  
  // Body
  weight: number | null;
  body_temperature: number | null;
  
  // Sleep
  sleep: {
    duration: number;
    score: number;
  } | null;
  
  // Wellness
  stress: number | null;
  
  // Nutrition
  water: number | null;
  caffeine: number | null;
}

async function fetchCurrentMetrics(userId: string | null): Promise<CurrentMetrics> {
  if (!userId) {
    return {
      steps: null, distance: null, calories: null, active_calories: null, floors_climbed: null,
      hrv: null, hr: null, spo2: null, glucose: null, respiratory_rate: null,
      weight: null, body_temperature: null,
      sleep: null,
      stress: null,
      water: null, caffeine: null,
    };
  }

  // Get today's date
  const today = new Date().toISOString().split('T')[0];

  console.log('[useCurrentMetrics] Fetching metrics for date:', today);

  // Fetch latest biometrics for today
  const { data: biometrics, error } = await supabase
    .from('biometrics')
    .select('*')
    .eq('user_id', userId)
    .gte('recorded_at', `${today}T00:00:00.000Z`)
    .order('recorded_at', { ascending: false });

  if (error) {
    console.error('[useCurrentMetrics] Error fetching current metrics:', error);
    throw error;
  }

  console.log('[useCurrentMetrics] Fetched biometrics:', biometrics?.length, 'records');

  // Helper to find latest value for a metric type
  const getValue = (type: string) => biometrics?.find((b) => b.metric_type === type)?.value || null;

  return {
    // Activity
    steps: getValue('steps'),
    distance: getValue('distance'),
    calories: getValue('calories'),
    active_calories: getValue('active_calories'),
    floors_climbed: getValue('floors_climbed'),
    
    // Vitals
    hrv: getValue('hrv'),
    hr: getValue('heart_rate'),
    spo2: getValue('spo2'),
    glucose: getValue('glucose'),
    respiratory_rate: getValue('respiratory_rate'),
    
    // Body
    weight: getValue('weight'),
    body_temperature: getValue('body_temperature'),
    
    // Sleep
    sleep: (() => {
      const sleepData = biometrics?.find((b) => b.metric_type === 'sleep' || b.metric_type === 'sleep_duration');
      return sleepData ? {
        duration: sleepData.value || 0,
        score: sleepData.metadata?.quality_score || sleepData.metadata?.sleep_score || 0,
      } : null;
    })(),
    
    // Wellness
    stress: getValue('stress'),
    
    // Nutrition
    water: getValue('water'),
    caffeine: getValue('caffeine'),
  };
}

export function useCurrentMetrics(userId: string | null) {
  return useQuery({
    queryKey: ['currentMetrics', userId],
    queryFn: () => fetchCurrentMetrics(userId),
    enabled: !!userId,
    staleTime: 1 * 60 * 1000, // 1 minute
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });
}
