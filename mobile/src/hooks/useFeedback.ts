/**
 * useFeedback - Hook complet pour gérer le feedback utilisateur ML
 * 
 * Version 2.0 : Compatible avec FeedbackBottomSheet et standalone
 */

import { useState, useCallback } from 'react';
import { API_URL } from '../config/api';

interface FeedbackPayload {
  user_id: string;
  system_score: number;
  user_score: number;
  active_factors: {
    medications: string[];
    conditions: string[];
  };
}

interface FeedbackResponse {
  status: string;
  error: number;
  adjustments_count: number;
  adjustments: Array<{
    factor_type: string;
    factor_code: string;
    old_weight: number;
    new_weight: number;
    adjustment: number;
    confidence: number;
  }>;
}

interface UseFeedbackProps {
  userId?: string;
  currentEnergy?: number;
  systemScore?: number;
  hoursSinceWake?: number;
  activeFactors?: {
    medications?: any[];
    conditions?: any[];
  };
}

/**
 * Hook avec gestion complète du bottom sheet (pour Dashboard)
 */
export const useFeedback = (props?: UseFeedbackProps) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showFeedbackSheet, setShowFeedbackSheet] = useState(false);
  const [feedbackContext, setFeedbackContext] = useState<'low_energy_trigger' | 'energy_spike' | 'manual'>('manual');

  /**
   * Fonction de soumission standalone (pour usage direct)
   */
  const submitFeedback = useCallback(async (payload: FeedbackPayload): Promise<FeedbackResponse | null> => {
    setIsSubmitting(true);
    setError(null);

    try {
      console.log('[useFeedback] 📤 Envoi feedback:', payload);

      const response = await fetch(`${API_URL}/api/v1/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: FeedbackResponse = await response.json();

      console.log(
        '[useFeedback] ✅ Feedback envoyé:',
        `error=${data.error.toFixed(1)}%,`,
        `adjustments=${data.adjustments_count}`
      );

      if (data.adjustments_count > 0) {
        console.log('[useFeedback] 🎯 Ajustements ML appliqués:');
        data.adjustments.forEach((adj) => {
          console.log(
            `  - ${adj.factor_type}:${adj.factor_code}:`,
            `${adj.old_weight.toFixed(2)} → ${adj.new_weight.toFixed(2)}`,
            `(confidence=${adj.confidence.toFixed(2)})`
          );
        });
      }

      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue';
      console.error('[useFeedback] ❌ Erreur:', errorMessage);
      setError(errorMessage);
      return null;
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  /**
   * Handler pour FeedbackBottomSheet (compatibilité avec index.tsx)
   */
  const handleSubmitFeedback = useCallback(async (userScore: number) => {
    if (!props?.userId) {
      console.error('[useFeedback] ❌ userId manquant');
      return;
    }

    console.log('[useFeedback] 📝 handleSubmitFeedback appelé, userScore:', userScore);

    // Extraire les codes des facteurs actifs
    const medications = props.activeFactors?.medications?.map((m: any) => 
      typeof m === 'string' ? m : m.atc_code
    ) || [];
    
    const conditions = props.activeFactors?.conditions?.map((c: any) => 
      typeof c === 'string' ? c : c.icd11_code
    ) || [];

    const result = await submitFeedback({
      user_id: props.userId,
      system_score: props.systemScore || props.currentEnergy || 0,
      user_score: userScore,
      active_factors: {
        medications,
        conditions,
      },
    });

    if (result) {
      // Fermer le bottom sheet après succès
      setShowFeedbackSheet(false);
    }
  }, [props, submitFeedback]);

  /**
   * Ouvrir le feedback manuellement
   */
  const openFeedbackSheet = useCallback((context: 'low_energy_trigger' | 'energy_spike' | 'manual' = 'manual') => {
    setFeedbackContext(context);
    setShowFeedbackSheet(true);
  }, []);

  /**
   * Fermer le feedback
   */
  const closeFeedbackSheet = useCallback(() => {
    setShowFeedbackSheet(false);
  }, []);

  return {
    // Pour usage avec FeedbackBottomSheet (Dashboard)
    showFeedbackSheet,
    feedbackContext,
    handleSubmitFeedback,
    openFeedbackSheet,
    closeFeedbackSheet,
    
    // Pour usage standalone (energie.tsx)
    submitFeedback,
    isSubmitting,
    error,
  };
};
