/**
 * Hook useTrendsSummary
 * 
 * Calcule automatiquement les tendances des métriques clés sur 30 jours
 * pour afficher un résumé rapide en haut de l'écran Tendances.
 * 
 * Métriques analysées (par ordre de priorité) :
 * - HRV (santé cardiovasculaire)
 * - Sommeil (récupération)
 * - Stress (bien-être mental)
 * - Fréquence cardiaque (santé cardiaque)
 * - Activité physique (mouvement)
 */

import { useMemo } from 'react';

export type TrendDirection = 'up' | 'down' | 'stable' | 'insufficient';

export interface MetricTrend {
  key: string;
  label: string;
  trend: TrendDirection;
  description: string;
  change: number; // Pourcentage de changement
  emoji: string;
}

export interface TrendsSummary {
  metrics: MetricTrend[];
  period: number; // Nombre de jours analysés
  hasData: boolean;
}

// Seuil de changement significatif (5%)
const SIGNIFICANCE_THRESHOLD = 0.05;

// Nombre minimum de points de données requis
const MIN_DATA_POINTS = 5;

/**
 * Calcule la tendance d'une métrique sur une période
 */
function calculateTrend(
  data: any[] | undefined,
  metricKey: string,
  label: string,
  emoji: string,
  isInverseInterpretation: boolean = false // Pour stress: baisse = positif
): MetricTrend {
  if (!data || data.length < MIN_DATA_POINTS) {
    return {
      key: metricKey,
      label,
      trend: 'insufficient',
      description: 'Données insuffisantes',
      change: 0,
      emoji,
    };
  }

  // Filtrer les valeurs invalides
  const values = data
    .map((d) => d?.value)
    .filter((v) => v != null && typeof v === 'number' && !isNaN(v) && isFinite(v));

  if (values.length < MIN_DATA_POINTS) {
    return {
      key: metricKey,
      label,
      trend: 'insufficient',
      description: 'Données insuffisantes',
      change: 0,
      emoji,
    };
  }

  // Comparer première moitié vs seconde moitié
  const midPoint = Math.floor(values.length / 2);
  const firstHalf = values.slice(0, midPoint);
  const secondHalf = values.slice(midPoint);

  const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
  const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;

  const diff = secondAvg - firstAvg;
  const changePercent = firstAvg > 0 ? (diff / firstAvg) * 100 : 0;

  // Déterminer la tendance
  let trend: TrendDirection;
  if (Math.abs(changePercent) < SIGNIFICANCE_THRESHOLD * 100) {
    trend = 'stable';
  } else if (changePercent > 0) {
    trend = 'up';
  } else {
    trend = 'down';
  }

  // Générer la description
  let description: string;
  
  if (trend === 'stable') {
    description = 'Stable';
  } else {
    const absChange = Math.abs(changePercent);
    const direction = trend === 'up' ? '↗' : '↘';
    
    // Interprétation selon le contexte
    let interpretation: 'amélioration' | 'baisse' | 'neutre';
    
    if (isInverseInterpretation) {
      // Pour stress: baisse = amélioration
      interpretation = trend === 'up' ? 'baisse' : 'amélioration';
    } else {
      // Pour la plupart des métriques: hausse = amélioration
      interpretation = trend === 'up' ? 'amélioration' : 'baisse';
    }
    
    description = `${direction} ${interpretation} (${absChange.toFixed(0)}%)`;
  }

  return {
    key: metricKey,
    label,
    trend,
    description,
    change: changePercent,
    emoji,
  };
}

/**
 * Hook principal - Analyse les tendances des métriques clés
 */
export function useTrendsSummary(
  metricsHistory: Record<string, any[]> | undefined
): TrendsSummary {
  return useMemo(() => {
    if (!metricsHistory) {
      return {
        metrics: [],
        period: 30,
        hasData: false,
      };
    }

    // Métriques clés à afficher (max 5 pour l'UI)
    const keyMetrics: MetricTrend[] = [];

    // 1. HRV (priorité haute)
    if (metricsHistory.hrv && metricsHistory.hrv.length >= MIN_DATA_POINTS) {
      keyMetrics.push(
        calculateTrend(metricsHistory.hrv, 'hrv', 'HRV', '💚', false)
      );
    }

    // 2. Sommeil (priorité haute)
    if (metricsHistory.sleep_duration && metricsHistory.sleep_duration.length >= MIN_DATA_POINTS) {
      keyMetrics.push(
        calculateTrend(metricsHistory.sleep_duration, 'sleep_duration', 'Sommeil', '🌙', false)
      );
    }

    // 3. Stress (priorité haute - interprétation inverse)
    if (metricsHistory.stress && metricsHistory.stress.length >= MIN_DATA_POINTS) {
      keyMetrics.push(
        calculateTrend(metricsHistory.stress, 'stress', 'Stress', '🧠', true)
      );
    }

    // 4. Fréquence cardiaque (priorité moyenne)
    if (metricsHistory.heart_rate && metricsHistory.heart_rate.length >= MIN_DATA_POINTS) {
      keyMetrics.push(
        calculateTrend(metricsHistory.heart_rate, 'heart_rate', 'Fréquence cardiaque', '❤️', false)
      );
    }

    // 5. Activité physique - Pas (priorité moyenne)
    if (metricsHistory.steps && metricsHistory.steps.length >= MIN_DATA_POINTS) {
      keyMetrics.push(
        calculateTrend(metricsHistory.steps, 'steps', 'Activité', '👟', false)
      );
    }

    // Limiter à 5 métriques max
    const topMetrics = keyMetrics.slice(0, 5);

    return {
      metrics: topMetrics,
      period: 30,
      hasData: topMetrics.length > 0,
    };
  }, [metricsHistory]);
}
