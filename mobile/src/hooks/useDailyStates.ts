/**
 * Hook useDailyStates
 * 
 * Récupère les états quotidiens (daily_state) depuis Supabase:
 * - recovery
 * - sleep_debt
 * - overtrain
 * - infection_like
 */

import { useQuery } from '@tanstack/react-query';
import { supabase } from '../lib/supabase';

interface DailyState {
  id: string;
  user_id: string;
  state_type: string;
  state_date: string;
  score: number;
  smoothed_score: number;
  confidence: number;
  top_factors: any[];
  metadata: any;
  model_version: string;
}

interface DailyStatesData {
  recovery?: DailyState;
  sleep_debt?: DailyState;
  overtrain?: DailyState;
  infection_like?: DailyState;
}

async function fetchDailyStates(userId: string | null): Promise<DailyStatesData> {
  if (!userId) {
    console.log('[useDailyStates] No userId provided');
    return {};
  }

  try {
    const today = new Date().toISOString().split('T')[0]; // Format: YYYY-MM-DD

    const { data, error } = await supabase
      .from('daily_state')
      .select('*')
      .eq('user_id', userId)
      .eq('state_date', today);

    if (error) {
      console.error('[useDailyStates] Error fetching daily states:', error);
      return {};
    }

    if (!data || data.length === 0) {
      console.log('[useDailyStates] No daily states found for today');
      return {};
    }

    // Mapper les états par type
    const statesMap: DailyStatesData = {};
    
    for (const state of data) {
      if (state.state_type === 'recovery') {
        statesMap.recovery = state;
      } else if (state.state_type === 'sleep_debt') {
        statesMap.sleep_debt = state;
      } else if (state.state_type === 'overtrain') {
        statesMap.overtrain = state;
      } else if (state.state_type === 'infection_like') {
        statesMap.infection_like = state;
      }
    }

    return statesMap;
  } catch (err) {
    console.error('[useDailyStates] Unexpected error:', err);
    return {};
  }
}

export function useDailyStates(userId: string | null) {
  return useQuery<DailyStatesData, Error>({
    queryKey: ['dailyStates', userId],
    queryFn: () => fetchDailyStates(userId),
    enabled: !!userId,
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 2,
  });
}
