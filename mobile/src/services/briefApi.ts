/**
 * Service API pour le Brief quotidien
 * Appelle le backend Wellness Coach pour générer les cartes Brief
 */

import { API_URL } from '../config/api';

export interface BriefApiResponse {
  status: 'success' | 'error';
  cards: Array<{
    id: string;
    type: 'verdict' | 'critical' | 'focus' | 'agenda' | 'activity' | 'empty';
    title: string;
    content: string; // Markdown
    state: 'optimal' | 'warning' | 'alert' | 'neutral';
    iconName: string;
    badge?: number;
    priority: number;
    actionButton?: {
      label: string;
      action: string;
    };
  }>;
  pulseScore: number;
  cached: boolean;
  analyzed_at: string;
  biometrics_ref_at?: string;
  intraday_energy_forecast?: {
    type: string;
    date: string;
    generated_at: string;
    model_version: string;
    timezone: string;
    points: Array<{ t: string; energy: number }>;
    windows: Array<{ from: string; to: string; kind: string; label: string }>;
    events: Array<{
      id: string;
      start: string;
      end: string;
      title: string;
      impact: number;
      confidence: number;
      tags: string[];
    }>;
    notes: string[];
    confidence: number;
  };
  message?: string; // En cas d'erreur
}

/**
 * Génère le Brief quotidien via l'API backend
 * 
 * @param userId - UUID de l'utilisateur
 * @param forceRefresh - Si true, force un nouveau calcul même si cache valide
 * @returns Promise avec les cartes Brief et métadonnées
 */
export async function generateBrief(
  userId: string,
  forceRefresh: boolean = false
): Promise<BriefApiResponse> {
  try {
    const response = await fetch(`${API_URL}/api/v1/generate-brief`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        force_refresh: forceRefresh,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error ${response.status}: ${errorText}`);
    }

    const data = await response.json();
    
    // Valider la structure de la réponse
    if (!data.cards || !Array.isArray(data.cards)) {
      throw new Error('Invalid API response: missing cards array');
    }

    return data;
  } catch (error) {
    console.error('Error generating brief:', error);
    throw error;
  }
}
