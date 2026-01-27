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
  days: number = 30
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

  // Calculate start date
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);

  console.log('[useMetricsHistory] Fetching metrics from', startDate.toISOString());

  // Fetch all biometrics for the period
  const { data: biometrics, error } = await supabase
    .from('biometrics')
    .select('metric_type, value, recorded_at, source')
    .eq('user_id', userId)
    .gte('recorded_at', startDate.toISOString())
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

  // Group by date and metric_type, keeping the latest value for each day
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

export function useMetricsHistory(userId: string | null, days: number = 30) {
  return useQuery({
    queryKey: ['metricsHistory', userId, days],
    queryFn: () => fetchMetricsHistory(userId, days),
    enabled: !!userId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 10 * 60 * 1000, // Refetch every 10 minutes
  });
}
