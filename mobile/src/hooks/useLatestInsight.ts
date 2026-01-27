import { useQuery } from '@tanstack/react-query';
import { supabase } from '../lib/supabase';

interface Insight {
  id: string;
  user_id: string;
  instruction_text: string;
  content: string | null;
  category: string | null;
  priority: number;
  is_read: boolean;
  created_at: string;
  correlation_type: string | null;
}

async function fetchLatestInsight(userId: string | null): Promise<Insight | null> {
  if (!userId) return null;

  const { data, error } = await supabase
    .from('insights')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
    .limit(1)
    .single();

  if (error) {
    if (error.code === 'PGRST116') {
      // No rows returned
      return null;
    }
    console.error('Error fetching latest insight:', error);
    throw error;
  }

  return data;
}

export function useLatestInsight(userId: string | null) {
  return useQuery({
    queryKey: ['latestInsight', userId],
    queryFn: () => fetchLatestInsight(userId),
    enabled: !!userId,
    staleTime: 1 * 60 * 1000, // 1 minute
  });
}
