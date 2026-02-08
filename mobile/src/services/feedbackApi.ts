/**
 * Feedback API Service
 * 
 * Gère l'envoi des feedbacks utilisateurs vers le backend (ML adaptatif)
 */

import { API_URL } from '../config/api';

export interface FeedbackPayload {
  user_id: string;
  system_score: number; // 0-100
  user_score: number; // 0-100
  active_factors: {
    medications?: Array<{
      atc_code: string;
      name: string;
      impact: number;
      weight?: number;
    }>;
    conditions?: Array<{
      icd11_code: string;
      name: string;
      decay_rate: number;
      malus: number;
      weight?: number;
    }>;
  };
  energy_at_feedback: number;
  hours_since_wake: number;
  feedback_context: 'low_energy_trigger' | 'energy_spike' | 'manual';
}

export interface FeedbackResponse {
  feedback_id: string;
  unprocessed_count: number;
  optimization_triggered: boolean;
  optimization_result?: {
    status: string;
    feedback_count: number;
    adjustments?: Array<{
      factor: string;
      name: string;
      old_weight: number;
      new_weight: number;
      change: number;
    }>;
  };
}

/**
 * Envoie un feedback utilisateur au backend
 */
export async function submitFeedback(payload: FeedbackPayload): Promise<FeedbackResponse> {
  try {
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

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('[FeedbackAPI] Error submitting feedback:', error);
    throw error;
  }
}

/**
 * Extrait les facteurs actifs d'un forecast
 */
export function extractActiveFactors(forecast: any) {
  return {
    medications: forecast?.influencers
      ?.filter((inf: any) => inf.name.startsWith('💊'))
      ?.map((inf: any) => ({
        name: inf.name.replace('💊 ', ''),
        impact: parseInt(inf.impact) || 0,
      })) || [],
    conditions: forecast?.influencers
      ?.filter((inf: any) => inf.name.includes('Dépression') || inf.name.includes('TDAH'))
      ?.map((inf: any) => ({
        name: inf.name.replace(/^[😔🧠⚡] /, ''),
        impact: parseInt(inf.impact) || 0,
      })) || [],
  };
}
