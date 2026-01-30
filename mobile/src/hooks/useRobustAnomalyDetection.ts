/**
 * Hook pour détecter les anomalies avec statistiques ROBUSTES (median/IQR)
 * 
 * NOUVEAU: Remplace useAnomalyDetection avec Z-Score robuste
 */

import { useMemo } from 'react';
import { useCurrentMetrics } from './useCurrentMetrics';
import { useRobustBaselines, hasValidBaselines } from './useRobustBaselines';
import { 
  robustZScoreCalculator, 
  type CurrentMetrics as RobustCurrentMetrics 
} from '../services/RobustZScoreCalculator';
import { Anomaly, GlobalState } from '../types/baselines';

interface RobustAnomalyDetectionResult {
  anomalies: Anomaly[];
  state: GlobalState['state'];
  isLoading: boolean;
  error: Error | null;
  hasValidData: boolean;
  dataStatus: 'none' | 'insufficient' | 'partial' | 'complete';
}

/**
 * Hook principal pour détection d'anomalies ROBUSTE
 * 
 * Combine:
 * - Métriques actuelles (useCurrentMetrics)
 * - Baselines robustes (useRobustBaselines)
 * - Z-Score robuste (RobustZScoreCalculator)
 * 
 * Gère automatiquement:
 * - États de chargement
 * - Erreurs
 * - Données manquantes ou insuffisantes
 */
export function useRobustAnomalyDetection(userId: string | null): RobustAnomalyDetectionResult {
  const { data: currentMetrics, isLoading: metricsLoading, error: metricsError } = useCurrentMetrics(userId);
  const { baselines, loading: baselinesLoading, error: baselinesError } = useRobustBaselines(userId);

  const result = useMemo(() => {
    // Si en cours de chargement
    if (metricsLoading || baselinesLoading) {
      return {
        anomalies: [],
        state: 'calm' as const,
        isLoading: true,
        error: null,
        hasValidData: false,
        dataStatus: 'none' as const
      };
    }

    // Si erreur
    if (metricsError || baselinesError) {
      console.error('[useRobustAnomalyDetection] Error:', metricsError || baselinesError);
      return {
        anomalies: [],
        state: 'calm' as const,
        isLoading: false,
        error: (metricsError || baselinesError) as Error,
        hasValidData: false,
        dataStatus: 'none' as const
      };
    }

    // Vérifier validité des baselines
    const validBaselines = hasValidBaselines(baselines);
    
    // Si pas de données ou baselines insuffisantes
    if (!currentMetrics || !baselines || !validBaselines) {
      console.log('[useRobustAnomalyDetection] Insufficient data');
      
      // Déterminer statut précis
      let dataStatus: 'none' | 'insufficient' | 'partial' | 'complete' = 'none';
      if (baselines && Object.keys(baselines).length > 0) {
        const validCount = Object.values(baselines).filter(
          b => b.sample_count >= 10 && b.confidence !== 'low'
        ).length;
        const totalCount = Object.keys(baselines).length;
        
        if (validCount === 0) {
          dataStatus = 'insufficient';
        } else if (validCount < totalCount / 2) {
          dataStatus = 'partial';
        } else {
          dataStatus = 'complete';
        }
      }
      
      return {
        anomalies: [],
        state: 'calm' as const,
        isLoading: false,
        error: null,
        hasValidData: false,
        dataStatus
      };
    }

    // Convertir currentMetrics au format attendu par RobustZScoreCalculator
    const metricsForDetection: RobustCurrentMetrics = {
      steps: currentMetrics.steps,
      distance: currentMetrics.distance,
      calories: currentMetrics.calories,
      active_calories: currentMetrics.active_calories,
      floors_climbed: currentMetrics.floors_climbed,
      hrv: currentMetrics.hrv,
      heart_rate: currentMetrics.hr,
      spo2: currentMetrics.spo2,
      glucose: currentMetrics.glucose,
      respiratory_rate: currentMetrics.respiratory_rate,
      weight: currentMetrics.weight,
      body_temperature: currentMetrics.body_temperature,
      stress: currentMetrics.stress,
      water: currentMetrics.water,
      caffeine: currentMetrics.caffeine,
      sleep_duration: currentMetrics.sleep?.duration ?? null
    };

    // Détecter les anomalies avec Z-Score ROBUSTE
    const anomalies = robustZScoreCalculator.detectAnomalies(
      metricsForDetection,
      baselines
    );
    
    // Calculer l'état global
    const state = robustZScoreCalculator.calculateGlobalState(anomalies);

    console.log('[useRobustAnomalyDetection] State:', state, 'Anomalies:', anomalies.length);
    if (anomalies.length > 0) {
      console.log('[useRobustAnomalyDetection] Top anomalies:', anomalies.slice(0, 3));
    }

    return {
      anomalies,
      state,
      isLoading: false,
      error: null,
      hasValidData: true,
      dataStatus: 'complete' as const
    };
  }, [currentMetrics, baselines, metricsLoading, baselinesLoading, metricsError, baselinesError]);

  return result;
}

// Export types pour compatibilité
export type { Anomaly, RobustAnomalyDetectionResult };
export type { GlobalState } from '../types/baselines';
