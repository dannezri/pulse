/**
 * Types pour Baselines Robustes (Median/IQR)
 * 
 * MISE À JOUR v2: Migration de mean/std vers median/IQR
 */

export interface RobustBaseline {
  // Statistiques robustes (principal)
  median: number;
  iqr: number;       // Interquartile Range
  p25: number;       // Percentile 25 (Q1)
  p75: number;       // Percentile 75 (Q3)
  
  // Statistiques classiques (optionnel, pour graphiques)
  mean?: number;
  std?: number;
  
  // Métadonnées
  sample_count: number;
  confidence: 'low' | 'medium' | 'high';
  calculated_at: string;
  model_version: string;
}

export interface RobustBaselines {
  [metric: string]: RobustBaseline;
}

export interface Anomaly {
  metric: string;
  value: number;
  z_score_robust: number;  // Z-Score robuste (IQR-based)
  weight: number;
  priority: number;
  direction: 'above' | 'below';
  baseline: {
    median: number;
    iqr: number;
    p25: number;
    p75: number;
  };
}

export interface GlobalState {
  state: 'calm' | 'warning' | 'alert';
  anomalies: Anomaly[];
  timestamp: string;
}

// Types pour compatibilité backwards (legacy)
export interface LegacyBaseline {
  mean: number;
  std: number;
  sample_count: number;
  confidence: string;
}

export interface LegacyBaselines {
  [metric: string]: LegacyBaseline;
}

// Helpers de conversion
export function robustToLegacy(robust: RobustBaseline): LegacyBaseline {
  return {
    mean: robust.mean ?? robust.median,
    std: robust.std ?? (robust.iqr / 1.349), // IQR → sigma équivalent
    sample_count: robust.sample_count,
    confidence: robust.confidence
  };
}

export function legacyToRobust(legacy: LegacyBaseline): RobustBaseline {
  // Approximation pour migration
  const median = legacy.mean;
  const iqr = legacy.std * 1.349; // sigma → IQR équivalent
  
  return {
    median,
    iqr,
    p25: median - (0.675 * legacy.std),  // Q1 ≈ mean - 0.675σ
    p75: median + (0.675 * legacy.std),  // Q3 ≈ mean + 0.675σ
    mean: legacy.mean,
    std: legacy.std,
    sample_count: legacy.sample_count,
    confidence: legacy.confidence as 'low' | 'medium' | 'high',
    calculated_at: new Date().toISOString(),
    model_version: 'legacy_migration'
  };
}
