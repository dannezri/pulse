import { ZScoreCalculator } from '../ZScoreCalculator';
import type { Baselines } from '../../hooks/useBaselines';

describe('ZScoreCalculator', () => {
  let calculator: ZScoreCalculator;

  beforeEach(() => {
    calculator = new ZScoreCalculator();
  });

  describe('calculateZScore', () => {
    it('should calculate Z-Score correctly', () => {
      // Z = (value - mean) / std
      // (75 - 65) / 10 = 1.0
      expect(calculator.calculateZScore(75, 65, 10)).toBe(1.0);
    });

    it('should calculate negative Z-Score for values below mean', () => {
      // (55 - 65) / 10 = -1.0
      expect(calculator.calculateZScore(55, 65, 10)).toBe(-1.0);
    });

    it('should return 0 when value equals mean', () => {
      expect(calculator.calculateZScore(65, 65, 10)).toBe(0);
    });

    it('should return 0 when std is 0 (avoid division by zero)', () => {
      expect(calculator.calculateZScore(75, 65, 0)).toBe(0);
    });

    it('should handle decimal values correctly', () => {
      // (67.5 - 65.2) / 8.5 ≈ 0.27
      const result = calculator.calculateZScore(67.5, 65.2, 8.5);
      expect(result).toBeCloseTo(0.27, 2);
    });
  });

  describe('detectAnomalies', () => {
    const mockBaselines: Baselines = {
      hrv: { mean: 65, std: 10, weight: 3, count: 42 },
      heart_rate: { mean: 60, std: 5, weight: 3, count: 120 },
      steps: { mean: 8000, std: 1000, weight: 1, count: 30 },
      body_temperature: { mean: 36.5, std: 0.3, weight: 3, count: 20 },
    };

    it('should detect anomaly when Z > 2', () => {
      const currentMetrics = {
        hrv: 85, // Z = (85-65)/10 = 2.0 (borderline)
        hr: 72, // Z = (72-60)/5 = 2.4 (anomaly)
        steps: 8500, // Z = 0.5 (normal)
        distance: null,
        calories: null,
        active_calories: null,
        floors_climbed: null,
        spo2: null,
        glucose: null,
        respiratory_rate: null,
        weight: null,
        body_temperature: null,
        sleep: null,
        stress: null,
        water: null,
        caffeine: null,
      };

      const anomalies = calculator.detectAnomalies(currentMetrics, mockBaselines);
      
      // Should detect heart_rate anomaly (Z=2.4)
      expect(anomalies.length).toBeGreaterThan(0);
      expect(anomalies[0].metric).toBe('heart_rate');
      expect(anomalies[0].z_score).toBeCloseTo(2.4, 1);
      expect(anomalies[0].direction).toBe('above');
    });

    it('should detect anomaly when Z < -2', () => {
      const currentMetrics = {
        hrv: 45, // Z = (45-65)/10 = -2.0 (borderline)
        hr: 48, // Z = (48-60)/5 = -2.4 (anomaly)
        steps: null,
        distance: null,
        calories: null,
        active_calories: null,
        floors_climbed: null,
        spo2: null,
        glucose: null,
        respiratory_rate: null,
        weight: null,
        body_temperature: null,
        sleep: null,
        stress: null,
        water: null,
        caffeine: null,
      };

      const anomalies = calculator.detectAnomalies(currentMetrics, mockBaselines);
      
      // Should detect heart_rate anomaly (Z=-2.4)
      expect(anomalies.length).toBeGreaterThan(0);
      const hrAnomaly = anomalies.find(a => a.metric === 'heart_rate');
      expect(hrAnomaly).toBeDefined();
      expect(hrAnomaly?.direction).toBe('below');
    });

    it('should not detect anomaly when |Z| < 2', () => {
      const currentMetrics = {
        hrv: 70, // Z = 0.5 (normal)
        hr: 62, // Z = 0.4 (normal)
        steps: 8500, // Z = 0.5 (normal)
        distance: null,
        calories: null,
        active_calories: null,
        floors_climbed: null,
        spo2: null,
        glucose: null,
        respiratory_rate: null,
        weight: null,
        body_temperature: null,
        sleep: null,
        stress: null,
        water: null,
        caffeine: null,
      };

      const anomalies = calculator.detectAnomalies(currentMetrics, mockBaselines);
      
      expect(anomalies.length).toBe(0);
    });

    it('should calculate priority as |Z| × weight', () => {
      const currentMetrics = {
        hrv: 45, // Z = -2.0, weight = 3, priority = 6.0
        hr: 60,
        steps: null,
        distance: null,
        calories: null,
        active_calories: null,
        floors_climbed: null,
        spo2: null,
        glucose: null,
        respiratory_rate: null,
        weight: null,
        body_temperature: null,
        sleep: null,
        stress: null,
        water: null,
        caffeine: null,
      };

      const anomalies = calculator.detectAnomalies(currentMetrics, mockBaselines);
      
      const hrvAnomaly = anomalies.find(a => a.metric === 'hrv');
      expect(hrvAnomaly).toBeDefined();
      // Priority = |Z| × weight = 2.0 × 3 = 6.0
      expect(hrvAnomaly?.priority).toBeCloseTo(6.0, 1);
    });

    it('should sort anomalies by priority (descending)', () => {
      const currentMetrics = {
        hrv: 40, // Z = -2.5, weight = 3, priority = 7.5
        hr: 48, // Z = -2.4, weight = 3, priority = 7.2
        steps: 11000, // Z = 3.0, weight = 1, priority = 3.0
        distance: null,
        calories: null,
        active_calories: null,
        floors_climbed: null,
        spo2: null,
        glucose: null,
        respiratory_rate: null,
        weight: null,
        body_temperature: null,
        sleep: null,
        stress: null,
        water: null,
        caffeine: null,
      };

      const anomalies = calculator.detectAnomalies(currentMetrics, mockBaselines);
      
      // Should be sorted by priority: hrv (7.5) > heart_rate (7.2) > steps (3.0)
      expect(anomalies.length).toBe(3);
      expect(anomalies[0].metric).toBe('hrv');
      expect(anomalies[1].metric).toBe('heart_rate');
      expect(anomalies[2].metric).toBe('steps');
    });

    it('should handle null/undefined metrics gracefully', () => {
      const currentMetrics = {
        hrv: null,
        hr: undefined as any,
        steps: 12000, // Z = 4.0, anomaly
        distance: null,
        calories: null,
        active_calories: null,
        floors_climbed: null,
        spo2: null,
        glucose: null,
        respiratory_rate: null,
        weight: null,
        body_temperature: null,
        sleep: null,
        stress: null,
        water: null,
        caffeine: null,
      };

      const anomalies = calculator.detectAnomalies(currentMetrics, mockBaselines);
      
      // Should only detect steps anomaly
      expect(anomalies.length).toBe(1);
      expect(anomalies[0].metric).toBe('steps');
    });

    it('should handle metrics without baselines', () => {
      const currentMetrics = {
        hrv: 45, // Has baseline, anomaly
        hr: 60,
        steps: null,
        distance: null,
        calories: null,
        active_calories: null,
        floors_climbed: null,
        spo2: 95, // No baseline
        glucose: 100, // No baseline
        respiratory_rate: null,
        weight: null,
        body_temperature: null,
        sleep: null,
        stress: null,
        water: null,
        caffeine: null,
      };

      const anomalies = calculator.detectAnomalies(currentMetrics, mockBaselines);
      
      // Should only detect hrv (has baseline)
      expect(anomalies.find(a => a.metric === 'spo2')).toBeUndefined();
      expect(anomalies.find(a => a.metric === 'glucose')).toBeUndefined();
    });
  });

  describe('calculateGlobalState', () => {
    it('should return "calm" when no anomalies', () => {
      const state = calculator.calculateGlobalState([]);
      expect(state).toBe('calm');
    });

    it('should return "alert" when Z >= 3 and weight >= 3', () => {
      const anomalies = [
        {
          metric: 'hrv',
          value: 35,
          z_score: -3.0,
          weight: 3,
          priority: 9.0,
          direction: 'below' as const,
          baseline: { mean: 65, std: 10 },
        },
      ];

      const state = calculator.calculateGlobalState(anomalies);
      expect(state).toBe('alert');
    });

    it('should return "warning" when Z >= 2.5', () => {
      const anomalies = [
        {
          metric: 'hrv',
          value: 40,
          z_score: -2.5,
          weight: 3,
          priority: 7.5,
          direction: 'below' as const,
          baseline: { mean: 65, std: 10 },
        },
      ];

      const state = calculator.calculateGlobalState(anomalies);
      expect(state).toBe('warning');
    });

    it('should return "warning" when multiple anomalies', () => {
      const anomalies = [
        {
          metric: 'hrv',
          value: 53,
          z_score: -1.2,
          weight: 3,
          priority: 3.6,
          direction: 'below' as const,
          baseline: { mean: 65, std: 10 },
        },
        {
          metric: 'heart_rate',
          value: 70,
          z_score: 2.0,
          weight: 3,
          priority: 6.0,
          direction: 'above' as const,
          baseline: { mean: 60, std: 5 },
        },
      ];

      const state = calculator.calculateGlobalState(anomalies);
      expect(state).toBe('warning');
    });
  });

  describe('getTopAnomalies', () => {
    it('should return top N anomalies', () => {
      const anomalies = [
        {
          metric: 'hrv',
          value: 40,
          z_score: -2.5,
          weight: 3,
          priority: 7.5,
          direction: 'below' as const,
          baseline: { mean: 65, std: 10 },
        },
        {
          metric: 'heart_rate',
          value: 70,
          z_score: 2.0,
          weight: 3,
          priority: 6.0,
          direction: 'above' as const,
          baseline: { mean: 60, std: 5 },
        },
        {
          metric: 'steps',
          value: 12000,
          z_score: 4.0,
          weight: 1,
          priority: 4.0,
          direction: 'above' as const,
          baseline: { mean: 8000, std: 1000 },
        },
      ];

      const top2 = calculator.getTopAnomalies(anomalies, 2);
      
      expect(top2.length).toBe(2);
      expect(top2[0].metric).toBe('hrv');
      expect(top2[1].metric).toBe('heart_rate');
    });

    it('should return all anomalies if N > anomalies.length', () => {
      const anomalies = [
        {
          metric: 'hrv',
          value: 40,
          z_score: -2.5,
          weight: 3,
          priority: 7.5,
          direction: 'below' as const,
          baseline: { mean: 65, std: 10 },
        },
      ];

      const top5 = calculator.getTopAnomalies(anomalies, 5);
      
      expect(top5.length).toBe(1);
    });
  });
});
