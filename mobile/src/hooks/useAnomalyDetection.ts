import { useMemo } from 'react';
import { useCurrentMetrics } from './useCurrentMetrics';
import { useBaselines } from './useBaselines';
import { zScoreCalculator, Anomaly, GlobalState } from '../services/ZScoreCalculator';

interface AnomalyDetectionResult {
  anomalies: Anomaly[];
  state: GlobalState;
  isLoading: boolean;
  error: Error | null;
}

/**
 * Hook pour détecter les anomalies physiologiques en temps réel
 * Combine les métriques actuelles avec les baselines pour calculer les Z-Scores
 */
export function useAnomalyDetection(userId: string | null): AnomalyDetectionResult {
  const { data: currentMetrics, isLoading: metricsLoading, error: metricsError } = useCurrentMetrics(userId);
  const { data: baselines, isLoading: baselinesLoading, error: baselinesError } = useBaselines(userId);

  const result = useMemo(() => {
    // Si en cours de chargement
    if (metricsLoading || baselinesLoading) {
      return {
        anomalies: [],
        state: 'calm' as GlobalState,
        isLoading: true,
        error: null,
      };
    }

    // Si erreur
    if (metricsError || baselinesError) {
      return {
        anomalies: [],
        state: 'calm' as GlobalState,
        isLoading: false,
        error: (metricsError || baselinesError) as Error,
      };
    }

    // Si pas de données
    if (!currentMetrics || !baselines) {
      return {
        anomalies: [],
        state: 'calm' as GlobalState,
        isLoading: false,
        error: null,
      };
    }

    // Détecter les anomalies
    const anomalies = zScoreCalculator.detectAnomalies(currentMetrics, baselines);
    
    // Calculer l'état global
    const state = zScoreCalculator.calculateGlobalState(anomalies);

    console.log('[useAnomalyDetection] State:', state, 'Anomalies:', anomalies.length);

    return {
      anomalies,
      state,
      isLoading: false,
      error: null,
    };
  }, [currentMetrics, baselines, metricsLoading, baselinesLoading, metricsError, baselinesError]);

  return result;
}

export type { Anomaly, GlobalState };
