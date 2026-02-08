import { useMutation } from '@tanstack/react-query';
import { API_URL } from '../config/api';
import { CalendarEvent } from './useCalendarEvents';

/**
 * Résultat de l'analyse IA d'un événement
 */
export interface AnalysisResult {
  status: 'success' | 'error';
  insight: string;
  cached: boolean;
  analyzed_at: string;
  biometrics_ref_at: string;
  message?: string; // En cas d'erreur
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

/**
 * Appelle l'API backend pour analyser un événement
 * 
 * @param userId UUID de l'utilisateur
 * @param event Événement du calendrier
 * @param forceRefresh Si true, ignore le cache et force une nouvelle analyse
 * @returns Résultat de l'analyse avec le texte Markdown
 */
async function analyzeEvent(
  userId: string,
  event: CalendarEvent,
  forceRefresh: boolean = false
): Promise<AnalysisResult> {
  const response = await fetch(`${API_URL}/api/v1/analyze-event`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: userId,
      event: {
        title: event.title,
        start: event.startDate.toISOString(),
        end: event.endDate.toISOString(),
        location: event.location || undefined,
        notes: event.notes || undefined,
      },
      force_refresh: forceRefresh,
    }),
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
  }
  
  const data = await response.json();
  return data;
}

/**
 * Hook pour analyser un événement du calendrier avec l'IA
 * 
 * Utilise un système de cache intelligent :
 * - Si les données biométriques n'ont pas changé → Cache (instantané)
 * - Si nouvelles données → Appel OpenAI (quelques secondes)
 * 
 * @param userId UUID de l'utilisateur (null si non connecté)
 * @param event Événement à analyser (null si non sélectionné)
 * @returns Mutation React Query avec data, isLoading, error, mutate
 * 
 * @example
 * const { mutate, data, isLoading, error } = useEventAnalysis(userId, event);
 * 
 * // Lancer l'analyse (auto ou manuel)
 * useEffect(() => {
 *   mutate({ forceRefresh: false });
 * }, []);
 * 
 * // Forcer une nouvelle analyse
 * <Button onPress={() => mutate({ forceRefresh: true })} />
 */
export function useEventAnalysis(userId: string | null, event: CalendarEvent | null) {
  return useMutation({
    mutationKey: ['eventAnalysis', userId, event?.id],
    mutationFn: ({ forceRefresh = false }: { forceRefresh?: boolean }) => {
      if (!userId || !event) {
        throw new Error('userId and event are required');
      }
      return analyzeEvent(userId, event, forceRefresh);
    },
    onSuccess: (data) => {
      console.log(`[useEventAnalysis] ${data.cached ? '✅ Cache hit' : '🔄 Fresh analysis'}`);
      if (data.usage) {
        console.log(`[useEventAnalysis] Tokens: ${data.usage.total_tokens}`);
      }
    },
    onError: (error: Error) => {
      console.error('[useEventAnalysis] Error:', error.message);
    },
  });
}
