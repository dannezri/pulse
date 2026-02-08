/**
 * Types TypeScript pour le système Pulse Brief
 * 
 * Ces types définissent la structure des données utilisées pour afficher
 * les cartes de briefing avec le score Pulse révolutionnaire.
 */

export interface BriefCard {
  id: string;
  type: 'verdict' | 'critical' | 'focus' | 'agenda' | 'activity' | 'empty';
  title: string;
  content: string;
  state: 'optimal' | 'warning' | 'alert' | 'neutral';
  iconName: string;
  badge?: number;
  badgeUnit?: string; // Unité du badge (par défaut "%", peut être "pas", "kcal", etc.)
  priority: number; // Score de pertinence (pour le tri)
  metadata?: any;
  headerText?: string; // Texte optionnel en haut de la carte (ex: date et prénom)
  actionButton?: {
    label: string;
    onPress: () => void;
  };
}

export interface BriefData {
  pulseScore: number; // Score calculé par calculatePulseScore (0-100)
  state: 'optimal' | 'warning' | 'alert' | 'neutral';
  weakestMetric: string; // Nom de la métrique la plus faible
  weakestMetricImpact: number; // Impact négatif en % (de calculatePulseScore)
  cards: BriefCard[];
  lastUpdated: Date;
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
}

export interface MetricWithRelevance {
  name: string;
  value: number;
  baseline: number | null;
  relevanceScore: number; // Écart normalisé
  state: 'ok' | 'warning' | 'critical';
}

// Types pour calculatePulseScore
export interface PulseMetrics {
  hrv: number;
  hrvBaseline: number;
  sleepTiming: number; // Score 0-100 (Oura contributors.timing)
  sleepDeep: number;   // Score 0-100 (Oura contributors.deep_sleep)
  rhr: number;
  rhrBaseline: number;
}

export interface PulseScoreResult {
  score: number;
  state: 'optimal' | 'warning' | 'alert';
  color: string;
  weakestMetric: {
    name: string;
    value: number;
    impact: number; // Pourcentage d'impact négatif (100 - score)
  };
}
