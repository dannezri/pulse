/**
 * Tests unitaires pour useTrendsSummary
 * Validation de l'algorithme de détection automatique des tendances
 */

import { renderHook } from '@testing-library/react-hooks';
import { useTrendsSummary } from '../useTrendsSummary';

// Helper pour générer des données de test
function generateMockData(
  days: number,
  options: {
    startValue: number;
    trend: 'up' | 'down' | 'stable';
    changePercent?: number; // Pourcentage de changement total
  }
): any[] {
  const { startValue, trend, changePercent = 10 } = options;
  const data: any[] = [];
  
  const totalChange = (startValue * changePercent) / 100;
  const dailyChange = totalChange / days;

  for (let i = 0; i < days; i++) {
    let value = startValue;
    
    if (trend === 'up') {
      value = startValue + (dailyChange * i);
    } else if (trend === 'down') {
      value = startValue - (dailyChange * i);
    }
    // stable: valeur constante

    data.push({
      date: `2026-01-${String(i + 1).padStart(2, '0')}`,
      value: value + (Math.random() * 0.5 - 0.25), // Petit bruit aléatoire
    });
  }

  return data;
}

describe('useTrendsSummary - Détection des tendances', () => {
  describe('Tendance à la hausse (up)', () => {
    it('devrait détecter une amélioration HRV de +12%', () => {
      const mockData = {
        hrv: generateMockData(30, { startValue: 50, trend: 'up', changePercent: 12 }),
      };

      const { result } = renderHook(() => useTrendsSummary(mockData));

      expect(result.current.metrics).toHaveLength(1);
      expect(result.current.metrics[0].key).toBe('hrv');
      expect(result.current.metrics[0].trend).toBe('up');
      expect(result.current.metrics[0].description).toContain('amélioration');
    });

    it('devrait détecter une hausse significative avec +6%', () => {
      const mockData = {
        heart_rate: generateMockData(30, { startValue: 60, trend: 'up', changePercent: 6 }),
      };

      const { result } = renderHook(() => useTrendsSummary(mockData));

      expect(result.current.metrics[0].trend).toBe('up');
    });
  });

  describe('Tendance à la baisse (down)', () => {
    it('devrait détecter une baisse du sommeil de -8%', () => {
      const mockData = {
        sleep_duration: generateMockData(30, { startValue: 28800, trend: 'down', changePercent: 8 }),
      };

      const { result } = renderHook(() => useTrendsSummary(mockData));

      expect(result.current.metrics[0].key).toBe('sleep_duration');
      expect(result.current.metrics[0].trend).toBe('down');
      expect(result.current.metrics[0].description).toContain('baisse');
    });

    it('devrait détecter une baisse significative avec -6%', () => {
      const mockData = {
        steps: generateMockData(30, { startValue: 8000, trend: 'down', changePercent: 6 }),
      };

      const { result } = renderHook(() => useTrendsSummary(mockData));

      expect(result.current.metrics[0].trend).toBe('down');
    });
  });

  describe('Tendance stable', () => {
    it('devrait détecter une stabilité avec +2% (sous seuil)', () => {
      const mockData = {
        hrv: generateMockData(30, { startValue: 50, trend: 'up', changePercent: 2 }),
      };

      const { result } = renderHook(() => useTrendsSummary(mockData));

      expect(result.current.metrics[0].trend).toBe('stable');
      expect(result.current.metrics[0].description).toContain('Stable');
    });

    it('devrait détecter une stabilité avec -3% (sous seuil)', () => {
      const mockData = {
        hrv: generateMockData(30, { startValue: 50, trend: 'down', changePercent: 3 }),
      };

      const { result } = renderHook(() => useTrendsSummary(mockData));

      expect(result.current.metrics[0].trend).toBe('stable');
    });

    it('devrait détecter une parfaite stabilité (0%)', () => {
      const mockData = {
        hrv: generateMockData(30, { startValue: 50, trend: 'stable', changePercent: 0 }),
      };

      const { result } = renderHook(() => useTrendsSummary(mockData));

      expect(result.current.metrics[0].trend).toBe('stable');
    });
  });

  describe('Interprétation inverse pour le stress', () => {
    it('devrait interpréter une baisse du stress comme amélioration', () => {
      const mockData = {
        stress: generateMockData(30, { startValue: 60, trend: 'down', changePercent: 10 }),
      };

      const { result } = renderHook(() => useTrendsSummary(mockData));

      const stressMetric = result.current.metrics.find(m => m.key === 'stress');
      expect(stressMetric?.trend).toBe('down');
      expect(stressMetric?.description).toContain('amélioration');
    });

    it('devrait interpréter une hausse du stress comme baisse', () => {
      const mockData = {
        stress: generateMockData(30, { startValue: 40, trend: 'up', changePercent: 12 }),
      };

      const { result } = renderHook(() => useTrendsSummary(mockData));

      const stressMetric = result.current.metrics.find(m => m.key === 'stress');
      expect(stressMetric?.trend).toBe('up');
      expect(stressMetric?.description).toContain('baisse');
    });
  });

  describe('Données insuffisantes', () => {
    it('devrait retourner insufficient pour <5 points de données', () => {
      const mockData = {
        hrv: generateMockData(3, { startValue: 50, trend: 'up', changePercent: 10 }),
      };

      const { result } = renderHook(() => useTrendsSummary(mockData));

      expect(result.current.metrics[0].trend).toBe('insufficient');
      expect(result.current.metrics[0].description).toBe('Données insuffisantes');
    });

    it('devrait ignorer les métriques avec données insuffisantes', () => {
      const mockData = {
        hrv: generateMockData(30, { startValue: 50, trend: 'up', changePercent: 10 }),
        sleep_duration: generateMockData(2, { startValue: 28800, trend: 'up', changePercent: 10 }),
      };

      const { result } = renderHook(() => useTrendsSummary(mockData));

      // Seulement HRV devrait être présente
      expect(result.current.metrics).toHaveLength(1);
      expect(result.current.metrics[0].key).toBe('hrv');
    });

    it('devrait retourner hasData=false si aucune métrique valide', () => {
      const mockData = {
        hrv: generateMockData(2, { startValue: 50, trend: 'up', changePercent: 10 }),
        sleep_duration: generateMockData(1, { startValue: 28800, trend: 'up', changePercent: 10 }),
      };

      const { result } = renderHook(() => useTrendsSummary(mockData));

      expect(result.current.hasData).toBe(false);
      expect(result.current.metrics).toHaveLength(0);
    });
  });

  describe('Cas limites', () => {
    it('devrait gérer undefined metricsHistory', () => {
      const { result } = renderHook(() => useTrendsSummary(undefined));

      expect(result.current.hasData).toBe(false);
      expect(result.current.metrics).toHaveLength(0);
      expect(result.current.period).toBe(30);
    });

    it('devrait gérer un objet vide', () => {
      const { result } = renderHook(() => useTrendsSummary({}));

      expect(result.current.hasData).toBe(false);
      expect(result.current.metrics).toHaveLength(0);
    });

    it('devrait filtrer les valeurs null/NaN/Infinity', () => {
      const mockData = {
        hrv: [
          { date: '2026-01-01', value: 50 },
          { date: '2026-01-02', value: null },
          { date: '2026-01-03', value: NaN },
          { date: '2026-01-04', value: Infinity },
          { date: '2026-01-05', value: 52 },
          { date: '2026-01-06', value: 53 },
          { date: '2026-01-07', value: 54 },
          { date: '2026-01-08', value: 55 },
          { date: '2026-01-09', value: 56 },
        ],
      };

      const { result } = renderHook(() => useTrendsSummary(mockData));

      // Devrait avoir 6 valeurs valides (>= 5 minimum requis)
      expect(result.current.metrics[0].trend).not.toBe('insufficient');
    });

    it('devrait gérer division par zéro dans le calcul du pourcentage', () => {
      const mockData = {
        hrv: [
          { date: '2026-01-01', value: 0 },
          { date: '2026-01-02', value: 0 },
          { date: '2026-01-03', value: 0 },
          { date: '2026-01-04', value: 10 },
          { date: '2026-01-05', value: 10 },
          { date: '2026-01-06', value: 10 },
        ],
      };

      const { result } = renderHook(() => useTrendsSummary(mockData));

      // Ne devrait pas crash, devrait retourner stable ou up
      expect(result.current.metrics[0]).toBeDefined();
      expect(['up', 'stable']).toContain(result.current.metrics[0].trend);
    });
  });

  describe('Ordre de priorité des métriques', () => {
    it('devrait afficher les métriques dans l\'ordre de priorité', () => {
      const mockData = {
        hrv: generateMockData(30, { startValue: 50, trend: 'up', changePercent: 10 }),
        sleep_duration: generateMockData(30, { startValue: 28800, trend: 'up', changePercent: 8 }),
        stress: generateMockData(30, { startValue: 50, trend: 'down', changePercent: 6 }),
        heart_rate: generateMockData(30, { startValue: 60, trend: 'up', changePercent: 5 }),
        steps: generateMockData(30, { startValue: 8000, trend: 'up', changePercent: 12 }),
      };

      const { result } = renderHook(() => useTrendsSummary(mockData));

      expect(result.current.metrics).toHaveLength(5);
      
      // Ordre attendu: HRV, Sommeil, Stress, Heart Rate, Steps
      expect(result.current.metrics[0].key).toBe('hrv');
      expect(result.current.metrics[1].key).toBe('sleep_duration');
      expect(result.current.metrics[2].key).toBe('stress');
      expect(result.current.metrics[3].key).toBe('heart_rate');
      expect(result.current.metrics[4].key).toBe('steps');
    });

    it('devrait limiter à 5 métriques max même si plus disponibles', () => {
      const mockData = {
        hrv: generateMockData(30, { startValue: 50, trend: 'up', changePercent: 10 }),
        sleep_duration: generateMockData(30, { startValue: 28800, trend: 'up', changePercent: 8 }),
        stress: generateMockData(30, { startValue: 50, trend: 'down', changePercent: 6 }),
        heart_rate: generateMockData(30, { startValue: 60, trend: 'up', changePercent: 5 }),
        steps: generateMockData(30, { startValue: 8000, trend: 'up', changePercent: 12 }),
        weight: generateMockData(30, { startValue: 75, trend: 'down', changePercent: 2 }), // 6ème métrique
      };

      const { result } = renderHook(() => useTrendsSummary(mockData));

      expect(result.current.metrics).toHaveLength(5);
      // Weight ne devrait pas apparaître (priorité basse)
      expect(result.current.metrics.every(m => m.key !== 'weight')).toBe(true);
    });
  });

  describe('Calcul du pourcentage de changement', () => {
    it('devrait calculer correctement le pourcentage de changement', () => {
      // HRV: 50 → 60 = +20%
      const mockData = {
        hrv: generateMockData(30, { startValue: 50, trend: 'up', changePercent: 20 }),
      };

      const { result } = renderHook(() => useTrendsSummary(mockData));

      const hrvMetric = result.current.metrics[0];
      expect(hrvMetric.change).toBeGreaterThan(15); // ~20% avec bruit
      expect(hrvMetric.change).toBeLessThan(25);
    });
  });

  describe('Labels et emojis', () => {
    it('devrait assigner les bons labels et emojis', () => {
      const mockData = {
        hrv: generateMockData(30, { startValue: 50, trend: 'up', changePercent: 10 }),
        sleep_duration: generateMockData(30, { startValue: 28800, trend: 'up', changePercent: 8 }),
        stress: generateMockData(30, { startValue: 50, trend: 'down', changePercent: 6 }),
      };

      const { result } = renderHook(() => useTrendsSummary(mockData));

      expect(result.current.metrics[0]).toMatchObject({
        key: 'hrv',
        label: 'HRV',
        emoji: '💚',
      });

      expect(result.current.metrics[1]).toMatchObject({
        key: 'sleep_duration',
        label: 'Sommeil',
        emoji: '🌙',
      });

      expect(result.current.metrics[2]).toMatchObject({
        key: 'stress',
        label: 'Stress',
        emoji: '🧠',
      });
    });
  });
});
