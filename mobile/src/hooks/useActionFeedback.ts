/**
 * useActionFeedback - Hook pour gérer le feedback utilisateur sur les recommandations
 * 
 * Permet à l'utilisateur d'indiquer s'il a suivi ou ignoré une recommandation,
 * alimentant ainsi le système d'apprentissage personnalisé.
 */

import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';

export interface ActionLog {
  id: string;
  user_id: string;
  action_date: string;              // ISO date
  recommendation_type: string;      // Ex: "sleep_earlier", "skip_workout"
  recommendation_text: string;
  context: any;                     // JSONB
  followed: boolean | null;         // null = pas encore de feedback
  user_feedback: string | null;
  feedback_at: string | null;
  created_at: string;
}

interface UseActionFeedbackReturn {
  todayAction: ActionLog | null;
  loading: boolean;
  error: string | null;
  submitFeedback: (followed: boolean, userFeedback?: string) => Promise<boolean>;
  hasGivenFeedback: boolean;
}

/**
 * Hook pour gérer le feedback de l'action quotidienne
 */
export const useActionFeedback = (): UseActionFeedbackReturn => {
  const [todayAction, setTodayAction] = useState<ActionLog | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Récupérer l'action d'aujourd'hui (ou d'hier si matin)
  const fetchTodayAction = async () => {
    try {
      setLoading(true);
      setError(null);

      const { data: { user }, error: userError } = await supabase.auth.getUser();

      if (userError || !user) {
        throw new Error('User not authenticated');
      }

      // Date cible : hier soir (car on demande le feedback le lendemain matin)
      const now = new Date();
      const targetDate = new Date(now);
      
      // Si avant 12h, on demande feedback pour hier
      // Si après 12h, on peut demander feedback pour aujourd'hui
      if (now.getHours() < 12) {
        targetDate.setDate(targetDate.getDate() - 1);
      }
      
      const actionDate = targetDate.toISOString().split('T')[0];

      // Récupérer l'action log pour cette date
      const { data, error: fetchError } = await supabase
        .from('user_action_logs')
        .select('*')
        .eq('user_id', user.id)
        .eq('action_date', actionDate)
        .order('created_at', { ascending: false })
        .limit(1);

      if (fetchError) {
        throw fetchError;
      }

      if (data && data.length > 0) {
        setTodayAction(data[0]);
      } else {
        setTodayAction(null);
      }

    } catch (err) {
      console.error('[useActionFeedback] Error fetching action:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      setTodayAction(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTodayAction();
  }, []);

  // Soumettre le feedback
  const submitFeedback = async (followed: boolean, userFeedback?: string): Promise<boolean> => {
    if (!todayAction) {
      console.error('[useActionFeedback] No action to provide feedback for');
      return false;
    }

    try {
      const { data: { user }, error: userError } = await supabase.auth.getUser();

      if (userError || !user) {
        throw new Error('User not authenticated');
      }

      // Appeler la RPC function pour enregistrer le feedback
      const { data, error: rpcError } = await supabase.rpc(
        'record_action_feedback',
        {
          p_user_id: user.id,
          p_action_date: todayAction.action_date,
          p_recommendation_type: todayAction.recommendation_type,
          p_followed: followed,
          p_user_feedback: userFeedback || null
        }
      );

      if (rpcError) {
        throw rpcError;
      }

      // Mettre à jour l'état local
      setTodayAction({
        ...todayAction,
        followed,
        user_feedback: userFeedback || null,
        feedback_at: new Date().toISOString()
      });

      return true;

    } catch (err) {
      console.error('[useActionFeedback] Error submitting feedback:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      return false;
    }
  };

  const hasGivenFeedback = todayAction?.followed !== null;

  return {
    todayAction,
    loading,
    error,
    submitFeedback,
    hasGivenFeedback,
  };
};

/**
 * Hook pour récupérer les stats d'apprentissage utilisateur
 */
export const useLearningStats = () => {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const { data: { user }, error: userError } = await supabase.auth.getUser();

        if (userError || !user) return;

        const { data, error } = await supabase.rpc(
          'get_user_learning_stats',
          { p_user_id: user.id }
        );

        if (error) throw error;

        if (data && data.length > 0) {
          setStats(data[0]);
        }

      } catch (err) {
        console.error('[useLearningStats] Error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  return { stats, loading };
};

/**
 * Helper: Traduire le type de recommandation en français
 */
export const translateRecommendationType = (type: string): string => {
  const translations: Record<string, string> = {
    'sleep_earlier': 'Se coucher plus tôt',
    'skip_workout': 'Sauter l\'entraînement',
    'reduce_caffeine': 'Réduire la caféine',
    'increase_protein': 'Augmenter les protéines',
    'rest_day': 'Journée de repos',
    'light_activity': 'Activité légère',
    'hydrate_more': 'S\'hydrater davantage',
  };
  
  return translations[type] || type;
};
