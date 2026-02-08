import { useQuery } from '@tanstack/react-query';
import { supabase } from '../lib/supabase';

interface MetricDataPoint {
  date: string;
  value: number;
  source?: string;
}

interface MetricsHistory {
  // Activity
  steps: MetricDataPoint[];
  distance: MetricDataPoint[];
  calories: MetricDataPoint[];
  active_calories: MetricDataPoint[];
  active_minutes: MetricDataPoint[];
  floors_climbed: MetricDataPoint[];
  vo2_max: MetricDataPoint[];
  
  // Vitals
  hrv: MetricDataPoint[];
  heart_rate: MetricDataPoint[];
  spo2: MetricDataPoint[];
  blood_pressure: MetricDataPoint[];
  glucose: MetricDataPoint[];
  respiratory_rate: MetricDataPoint[];
  
  // Body
  weight: MetricDataPoint[];
  body_fat: MetricDataPoint[];
  bmi: MetricDataPoint[];
  body_temperature: MetricDataPoint[];
  
  // Sleep
  sleep_duration: MetricDataPoint[];
  
  // Wellness
  stress: MetricDataPoint[];
  mindfulness: MetricDataPoint[];
  
  // Nutrition
  water: MetricDataPoint[];
  caffeine: MetricDataPoint[];
  carbs: MetricDataPoint[];
}

async function fetchMetricsHistory(
  userId: string | null,
  days?: number,
  specificDate?: Date
): Promise<MetricsHistory> {
  if (!userId) {
    return {
      steps: [], distance: [], calories: [], active_calories: [], active_minutes: [],
      floors_climbed: [], vo2_max: [],
      hrv: [], heart_rate: [], spo2: [], blood_pressure: [], glucose: [], respiratory_rate: [],
      weight: [], body_fat: [], bmi: [], body_temperature: [],
      sleep_duration: [],
      stress: [], mindfulness: [],
      water: [], caffeine: [], carbs: [],
    };
  }

  let startDate: Date;
  let endDate: Date;

  if (specificDate) {
    // Mode jour spécifique : récupérer les données pour ce jour uniquement
    startDate = new Date(specificDate);
    startDate.setHours(0, 0, 0, 0);
    endDate = new Date(specificDate);
    endDate.setHours(23, 59, 59, 999);
    console.log('[useMetricsHistory] Fetching metrics for specific day:', startDate.toISOString());
  } else {
    // Mode période : récupérer les données pour les X derniers jours
    const daysToFetch = days || 30;
    startDate = new Date();
    startDate.setDate(startDate.getDate() - daysToFetch);
    startDate.setHours(0, 0, 0, 0);
    endDate = new Date(); // Maintenant
    console.log('[useMetricsHistory] Fetching metrics from', startDate.toISOString(), 'to', endDate.toISOString());
  }

  // Fetch all biometrics for the period
  const { data: biometrics, error } = await supabase
    .from('biometrics')
    .select('metric_type, value, recorded_at, source')
    .eq('user_id', userId)
    .gte('recorded_at', startDate.toISOString())
    .lte('recorded_at', endDate.toISOString())
    .order('recorded_at', { ascending: true });

  if (error) {
    console.error('[useMetricsHistory] Error fetching metrics:', error);
    throw error;
  }

  console.log('[useMetricsHistory] Fetched', biometrics?.length, 'records');

  // Group by metric type and aggregate by date
  const groupedMetrics: MetricsHistory = {
    steps: [], distance: [], calories: [], active_calories: [], active_minutes: [],
    floors_climbed: [], vo2_max: [],
    hrv: [], heart_rate: [], spo2: [], blood_pressure: [], glucose: [], respiratory_rate: [],
    weight: [], body_fat: [], bmi: [], body_temperature: [],
    sleep_duration: [],
    stress: [], mindfulness: [],
    water: [], caffeine: [], carbs: [],
  };

  if (!biometrics) {
    return groupedMetrics;
  }

  // Pour un jour spécifique, garder toutes les mesures de la journée
  // Pour une période, garder une mesure par jour (la plus récente)
  if (specificDate) {
    // Mode jour : garder toutes les mesures
    biometrics.forEach((record) => {
      const metricType = record.metric_type;
      if (metricType in groupedMetrics) {
        (groupedMetrics as any)[metricType].push({
          date: record.recorded_at,
          value: record.value,
          source: record.source,
        });
      }
    });
  } else {
    // Mode période : une mesure par jour
    const dataByDateAndType: Record<string, Record<string, MetricDataPoint>> = {};

    biometrics.forEach((record) => {
      const date = new Date(record.recorded_at).toISOString().split('T')[0];
      const metricType = record.metric_type;

      if (!dataByDateAndType[date]) {
        dataByDateAndType[date] = {};
      }

      // Keep the latest value for this date and metric
      if (
        !dataByDateAndType[date][metricType] ||
        new Date(record.recorded_at) >
          new Date(dataByDateAndType[date][metricType].date)
      ) {
        dataByDateAndType[date][metricType] = {
          date: record.recorded_at,
          value: record.value,
          source: record.source,
        };
      }
    });

    // Convert to arrays
    Object.values(dataByDateAndType).forEach((dayData) => {
      Object.entries(dayData).forEach(([metricType, dataPoint]) => {
        if (metricType in groupedMetrics) {
          (groupedMetrics as any)[metricType].push(dataPoint);
        }
      });
    });
  }

  // Sort each array by date
  Object.keys(groupedMetrics).forEach((key) => {
    (groupedMetrics as any)[key].sort(
      (a: MetricDataPoint, b: MetricDataPoint) =>
        new Date(a.date).getTime() - new Date(b.date).getTime()
    );
  });

  console.log('[useMetricsHistory] Grouped metrics:', {
    steps: groupedMetrics.steps.length,
    hrv: groupedMetrics.hrv.length,
    heart_rate: groupedMetrics.heart_rate.length,
    sleep_duration: groupedMetrics.sleep_duration.length,
  });

  return groupedMetrics;
}

export function useMetricsHistory(
  userId: string | null, 
  days?: number,
  specificDate?: Date
) {
  return useQuery({
    queryKey: ['metricsHistory', userId, days, specificDate?.toISOString()],
    queryFn: () => fetchMetricsHistory(userId, days, specificDate),
    enabled: !!userId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 10 * 60 * 1000, // Refetch every 10 minutes
  });
}
