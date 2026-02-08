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

async function fetchRecentInsights(
  userId: string | null,
  limit: number = 5
): Promise<Insight[]> {
  if (!userId) return [];

  // Récupère les insights les plus récents (incluant ceux créés aujourd'hui)
  const { data, error } = await supabase
    .from('insights')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
    .limit(limit);

  if (error) {
    console.error('Error fetching recent insights:', error);
    throw error;
  }

  return data || [];
}

export function useRecentInsights(userId: string | null, limit: number = 5) {
  return useQuery({
    queryKey: ['recentInsights', userId, limit],
    queryFn: () => fetchRecentInsights(userId, limit),
    enabled: !!userId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}
