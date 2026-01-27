import { useQuery } from '@tanstack/react-query';
import { supabase } from '../lib/supabase';

interface Profile {
  id: string;
  full_name: string | null;
  health_goal: string | null;
  baseline_hrv: number | null;
  baseline_resting_hr: number | null;
  open_wearables_user_id: string | null;
  created_at: string;
  updated_at: string;
}

async function fetchProfile(userId: string | null): Promise<Profile | null> {
  if (!userId) return null;

  const { data, error } = await supabase
    .from('profiles')
    .select('id, full_name, health_goal, baseline_hrv, baseline_resting_hr, open_wearables_user_id, created_at, updated_at')
    .eq('id', userId)
    .single();

  if (error) {
    // PGRST116 = no rows returned, which can happen due to RLS policies
    if (error.code === 'PGRST116') {
      console.log('No profile found for user (might be RLS issue):', userId);
      return null;
    }
    console.error('Error fetching profile:', error);
    throw error;
  }

  return data;
}

export function useProfile(userId: string | null) {
  return useQuery({
    queryKey: ['profile', userId],
    queryFn: () => fetchProfile(userId),
    enabled: !!userId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
