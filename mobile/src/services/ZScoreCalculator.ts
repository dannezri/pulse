import { Baselines } from '../hooks/useBaselines';

interface CurrentMetrics {
  // Activity
  steps: number | null;
  distance: number | null;
  calories: number | null;
  active_calories: number | null;
  floors_climbed: number | null;
  
  // Vitals
  hrv: number | null;
  hr: number | null;
  spo2: number | null;
  glucose: number | null;
  respiratory_rate: number | null;
  
  // Body
  weight: number | null;
  body_temperature: number | null;
  
  // Sleep
  sleep: {
    duration: number;
    score: number;
  } | null;
  
  // Wellness
  stress: number | null;
  
  // Nutrition
  water: number | null;
  caffeine: number | null;
}

export interface Anomaly {
  metric: string;
  value: number;
  z_score: number;
  weight: number;
  priority: number; // |z_score| × weight
  direction: 'above' | 'below';
  baseline: {
    mean: number;
    std: number;
  };
}

export type GlobalState = 'calm' | 'warning' | 'alert';

export class ZScoreCalculator {
  /**
   * Calcule le Z-Score : Z = (valeur - μ) / σ
   */
  calculateZScore(value: number, mean: number, std: number): number {
    if (std === 0) {
      return 0;
    }
    return (value - mean) / std;
  }

  /**
   * Détecte les anomalies en calculant les Z-Scores pour toutes les métriques
   * Filtre : garde uniquement |Z| > 2
   * Retourne le top 3 des anomalies triées par priorité décroissante
   */
  detectAnomalies(
    currentMetrics: CurrentMetrics,
    baselines: Baselines
  ): Anomaly[] {
    const anomalies: Anomaly[] = [];

    // Mapper les métriques plates
    const metricsMap: Record<string, number | null> = {
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
    };

    // Ajouter sleep_duration si disponible
    if (currentMetrics.sleep?.duration) {
      metricsMap['sleep_duration'] = currentMetrics.sleep.duration;
      metricsMap['sleep'] = currentMetrics.sleep.duration;
    }

    // Calculer Z-Score pour chaque métrique
    for (const [metricKey, value] of Object.entries(metricsMap)) {
      if (value === null || value === undefined) {
        continue;
      }

      const baseline = baselines[metricKey as keyof Baselines];
      if (!baseline) {
        continue;
      }

      const { mean, std, weight } = baseline;

      // Éviter division par zéro
      if (std === 0) {
        continue;
      }

      const zScore = this.calculateZScore(value, mean, std);

      // Filtrer : garder uniquement |Z| > 2
      if (Math.abs(zScore) > 2) {
        const priority = Math.abs(zScore) * weight;
        const direction: 'above' | 'below' = zScore > 0 ? 'above' : 'below';

        anomalies.push({
          metric: metricKey,
          value: Math.round(value * 100) / 100, // Arrondir à 2 décimales
          z_score: Math.round(zScore * 100) / 100,
          weight,
          priority: Math.round(priority * 100) / 100,
          direction,
          baseline: {
            mean: Math.round(mean * 100) / 100,
            std: Math.round(std * 100) / 100,
          },
        });
      }
    }

    // Trier par priorité décroissante
    anomalies.sort((a, b) => b.priority - a.priority);

    console.log('[ZScoreCalculator] Detected', anomalies.length, 'anomalies');
    if (anomalies.length > 0) {
      console.log('[ZScoreCalculator] Top 3:', anomalies.slice(0, 3));
    }

    return anomalies;
  }

  /**
   * Détermine l'état global (calm, warning, alert) basé sur les anomalies
   */
  calculateGlobalState(anomalies: Anomaly[]): GlobalState {
    if (anomalies.length === 0) {
      return 'calm';
    }

    // Récupérer la pire anomalie (première car triée par priorité)
    const worstAnomaly = anomalies[0];
    const maxZScore = Math.abs(worstAnomaly.z_score);
    const maxWeight = worstAnomaly.weight;

    // Alert : Z >= 3 et weight >= 3 (critères critiques très anormaux)
    if (maxZScore >= 3 && maxWeight >= 3) {
      return 'alert';
    }

    // Warning : Z >= 2.5 ou plusieurs anomalies avec weight >= 2
    if (maxZScore >= 2.5 || anomalies.length >= 2) {
      return 'warning';
    }

    // Sinon, warning léger
    return 'warning';
  }

  /**
   * Retourne les top N anomalies
   */
  getTopAnomalies(anomalies: Anomaly[], topN: number = 3): Anomaly[] {
    return anomalies.slice(0, topN);
  }
}

// Export singleton pour réutilisation
export const zScoreCalculator = new ZScoreCalculator();
