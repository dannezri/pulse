/**
 * Calculateur de Z-Score Robuste (Median/IQR)
 * 
 * Implémente la détection d'anomalies avec statistiques robustes
 * pour remplacer l'ancienne méthode mean/std
 */

import { RobustBaseline, RobustBaselines, Anomaly, GlobalState } from '../types/baselines';

// Constante IQR → Sigma pour distribution normale
const IQR_TO_SIGMA = 1.349;

// Seuil par défaut pour anomalie
const DEFAULT_THRESHOLD = 2.0;

// Poids par métrique (priorité)
const METRIC_WEIGHTS: Record<string, number> = {
  // Poids 3 (Critique)
  hrv: 3,
  heart_rate: 3,
  body_temperature: 3,
  sleep_duration: 3,
  sleep: 3,
  
  // Poids 2 (Important)
  active_calories: 2,
  stress: 2,
  glucose: 2,
  spo2: 2,
  
  // Poids 1 (Info)
  steps: 1,
  calories: 1,
  water: 1,
  distance: 1,
  floors_climbed: 1,
  weight: 1,
  respiratory_rate: 1,
  caffeine: 1,
};

export interface CurrentMetrics {
  [metric: string]: number;
}

export class RobustZScoreCalculator {
  /**
   * Calcule Z-Score ROBUSTE
   * 
   * Z_robust = (x - median) / (IQR / 1.349)
   * 
   * Le diviseur 1.349 convertit IQR en équivalent sigma
   * pour rendre Z_robust comparable au Z classique.
   */
  calculateZScoreRobust(
    value: number,
    median: number,
    iqr: number
  ): number {
    if (iqr === 0) {
      console.warn('IQR is 0, cannot calculate z-score');
      return 0;
    }
    
    const sigmaEquivalent = iqr / IQR_TO_SIGMA;
    return (value - median) / sigmaEquivalent;
  }
  
  /**
   * Détermine si une valeur est une anomalie
   */
  isAnomaly(
    value: number,
    baseline: RobustBaseline,
    threshold: number = DEFAULT_THRESHOLD
  ): boolean {
    const z = this.calculateZScoreRobust(value, baseline.median, baseline.iqr);
    return Math.abs(z) > threshold;
  }
  
  /**
   * Détermine la direction d'une anomalie
   */
  getAnomalyDirection(
    value: number,
    baseline: RobustBaseline,
    threshold: number = DEFAULT_THRESHOLD
  ): 'above' | 'below' | 'normal' {
    const z = this.calculateZScoreRobust(value, baseline.median, baseline.iqr);
    
    if (z > threshold) return 'above';
    if (z < -threshold) return 'below';
    return 'normal';
  }
  
  /**
   * Détecte toutes les anomalies
   */
  detectAnomalies(
    currentMetrics: CurrentMetrics,
    baselines: RobustBaselines,
    threshold: number = DEFAULT_THRESHOLD
  ): Anomaly[] {
    const anomalies: Anomaly[] = [];
    
    for (const [metric, value] of Object.entries(currentMetrics)) {
      const baseline = baselines[metric];
      
      if (!baseline) {
        console.warn(`No baseline found for metric: ${metric}`);
        continue;
      }
      
      const z = this.calculateZScoreRobust(value, baseline.median, baseline.iqr);
      
      // Filtrer: garder uniquement |Z| > threshold
      if (Math.abs(z) > threshold) {
        const weight = METRIC_WEIGHTS[metric] ?? 1;
        const priority = Math.abs(z) * weight;
        const direction = z > 0 ? 'above' : 'below';
        
        anomalies.push({
          metric,
          value: Math.round(value * 100) / 100,
          z_score_robust: Math.round(z * 100) / 100,
          weight,
          priority: Math.round(priority * 100) / 100,
          direction,
          baseline: {
            median: baseline.median,
            iqr: baseline.iqr,
            p25: baseline.p25,
            p75: baseline.p75,
          },
        });
      }
    }
    
    // Trier par priorité décroissante
    anomalies.sort((a, b) => b.priority - a.priority);
    
    return anomalies;
  }
  
  /**
   * Calcule l'état global basé sur les anomalies détectées
   */
  calculateGlobalState(anomalies: Anomaly[]): GlobalState['state'] {
    if (anomalies.length === 0) {
      return 'calm';
    }
    
    // Compter anomalies critiques (weight = 3)
    const criticalCount = anomalies.filter(a => a.weight === 3).length;
    
    // Compter anomalies importantes (weight = 2)
    const importantCount = anomalies.filter(a => a.weight === 2).length;
    
    // Règles de décision
    if (criticalCount >= 2 || (criticalCount >= 1 && importantCount >= 2)) {
      return 'alert';
    }
    
    if (criticalCount >= 1 || importantCount >= 2) {
      return 'warning';
    }
    
    return 'calm';
  }
  
  /**
   * Calcule l'état global complet
   */
  calculateGlobalStateComplete(
    currentMetrics: CurrentMetrics,
    baselines: RobustBaselines
  ): GlobalState {
    const anomalies = this.detectAnomalies(currentMetrics, baselines);
    const state = this.calculateGlobalState(anomalies);
    
    return {
      state,
      anomalies,
      timestamp: new Date().toISOString(),
    };
  }
  
  /**
   * Retourne les top N anomalies
   */
  getTopAnomalies(
    currentMetrics: CurrentMetrics,
    baselines: RobustBaselines,
    topN: number = 3
  ): Anomaly[] {
    const anomalies = this.detectAnomalies(currentMetrics, baselines);
    return anomalies.slice(0, topN);
  }
  
  /**
   * Calcule le percentile d'une valeur
   */
  calculatePercentile(value: number, baseline: RobustBaseline): number {
    // Approximation simple
    if (value <= baseline.p25) {
      return 25 * (value / baseline.p25);
    } else if (value >= baseline.p75) {
      return 75 + 25 * ((value - baseline.p75) / (baseline.p75 * 0.5));
    } else if (value <= baseline.median) {
      // Entre P25 et médiane
      return 25 + 25 * ((value - baseline.p25) / (baseline.median - baseline.p25));
    } else {
      // Entre médiane et P75
      return 50 + 25 * ((value - baseline.median) / (baseline.p75 - baseline.median));
    }
  }
}

// Export singleton
export const robustZScoreCalculator = new RobustZScoreCalculator();

// Export pour tests
export { IQR_TO_SIGMA, DEFAULT_THRESHOLD, METRIC_WEIGHTS };
