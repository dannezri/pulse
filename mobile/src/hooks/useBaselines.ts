import { useQuery } from '@tanstack/react-query';

interface Baseline {
  mean: number;
  std: number;
  weight: 1 | 2 | 3;
  count: number;
}

interface Baselines {
  hrv?: Baseline;
  heart_rate?: Baseline;
  body_temperature?: Baseline;
  sleep_duration?: Baseline;
  sleep?: Baseline;
  active_calories?: Baseline;
  stress?: Baseline;
  glucose?: Baseline;
  spo2?: Baseline;
  steps?: Baseline;
  calories?: Baseline;
  water?: Baseline;
  distance?: Baseline;
  floors_climbed?: Baseline;
  weight?: Baseline;
  respiratory_rate?: Baseline;
  caffeine?: Baseline;
}

interface BaselinesResponse {
  status: string;
  user_id: string;
  baselines: Baselines;
  lookback_days?: number;
  message?: string;
}

import { API_URL } from '../config/api';

async function fetchBaselines(userId: string | null): Promise<Baselines> {
  if (!userId) {
    return {};
  }

  console.log('[useBaselines] Fetching baselines for user:', userId);

  try {
    const response = await fetch(`${API_URL}/api/baselines/${userId}`);
    
    if (!response.ok) {
      console.error('[useBaselines] Error response:', response.status);
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data: BaselinesResponse = await response.json();
    
    console.log('[useBaselines] Fetched baselines:', Object.keys(data.baselines || {}).length, 'metrics');
    
    return data.baselines || {};
  } catch (error) {
    console.error('[useBaselines] Error fetching baselines:', error);
    throw error;
  }
}

export function useBaselines(userId: string | null) {
  return useQuery({
    queryKey: ['baselines', userId],
    queryFn: () => fetchBaselines(userId),
    enabled: !!userId,
    staleTime: 24 * 60 * 60 * 1000, // 24h cache (baselines changent lentement)
    refetchOnMount: false,
    refetchOnWindowFocus: false,
  });
}

export type { Baseline, Baselines };
