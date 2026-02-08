/**
 * Hook useNutritionHealthData
 * 
 * Agrège les données nutrition + santé nécessaires
 * pour alimenter le moteur d'insights nutritionnels.
 * 
 * Sources :
 * - Nutrition : food_logs, food_diary (Supabase)
 * - Santé : biometrics, daily_state (Supabase)
 */

import { useQuery } from '@tanstack/react-query';
import { supabase } from '../lib/supabase';

interface NutritionHealthDataResult {
  nutrition: {
    lastMealTime?: string;
    proteinIntake?: number;
    alcoholUnits?: number;
    caffeineIntake?: number;
    caffeineLastTime?: string;
    waterIntake?: number;
    carbsIntake?: number;
    caloriesIntake?: number;
  };
  health: {
    sleepQuality?: number;
    sleepDuration?: number;
    sleepFragmentation?: number;
    hrv?: number;
    hrvBaseline?: number;
    recovery?: number;
    energyLevel?: number;
    activeCalories?: number;
  };
}

async function fetchNutritionHealthData(
  userId: string | null,
  date: Date
): Promise<NutritionHealthDataResult> {
  if (!userId) {
    return { nutrition: {}, health: {} };
  }

  const dateStr = date.toISOString().split('T')[0];
  const yesterday = new Date(date);
  yesterday.setDate(yesterday.getDate() - 1);
  const yesterdayStr = yesterday.toISOString().split('T')[0];

  try {
    // 1. Récupérer les données nutritionnelles du jour
    const { data: foodLogs, error: foodError } = await supabase
      .from('food_logs')
      .select(`
        *,
        food_log_items(*)
      `)
      .eq('user_id', userId)
      .eq('log_date', dateStr);

    if (foodError) {
      console.error('[useNutritionHealthData] Food logs error:', foodError);
    }

    // Calculer les totaux nutrition
    let lastMealTime: string | undefined;
    let proteinIntake = 0;
    let carbsIntake = 0;
    let caloriesIntake = 0;
    let alcoholUnits = 0; // À implémenter si trackable
    let caffeineIntake = 0; // À implémenter si trackable
    let caffeineLastTime: string | undefined;
    let waterIntake = 0; // À implémenter si trackable

    if (foodLogs && foodLogs.length > 0) {
      // Trouver l'heure du dernier repas
      const sortedLogs = [...foodLogs].sort((a, b) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      lastMealTime = sortedLogs[0]?.created_at;

      // Sommer les macros
      foodLogs.forEach((log: any) => {
        if (log.total_protein) proteinIntake += log.total_protein;
        if (log.total_carbs) carbsIntake += log.total_carbs;
        if (log.total_calories) caloriesIntake += log.total_calories;
      });
    }

    // 2. Récupérer les données biométriques (HRV, sommeil, etc.)
    const { data: biometrics, error: bioError } = await supabase
      .from('biometrics')
      .select('*')
      .eq('user_id', userId)
      .eq('date', dateStr)
      .order('timestamp', { ascending: false })
      .limit(50);

    if (bioError) {
      console.error('[useNutritionHealthData] Biometrics error:', bioError);
    }

    // Extraire les métriques de santé
    let hrv: number | undefined;
    let sleepDuration: number | undefined;
    let sleepQuality: number | undefined;
    let sleepFragmentation: number | undefined;
    let activeCalories: number | undefined;

    if (biometrics && biometrics.length > 0) {
      // HRV (moyenne du jour)
      const hrvValues = biometrics
        .filter((b: any) => b.metric_type === 'hrv' && b.value != null)
        .map((b: any) => b.value);
      if (hrvValues.length > 0) {
        hrv = hrvValues.reduce((a: number, b: number) => a + b, 0) / hrvValues.length;
      }

      // Sommeil (chercher la nuit précédente aussi)
      const sleepMetric = biometrics.find((b: any) => b.metric_type === 'sleep_duration');
      if (sleepMetric) {
        sleepDuration = sleepMetric.value / 3600; // Convertir secondes en heures
        sleepQuality = sleepMetric.metadata?.sleep_score || 
                       sleepMetric.metadata?.quality || 
                       undefined;
        sleepFragmentation = sleepMetric.metadata?.wake_count || 
                             sleepMetric.metadata?.fragmentation ||
                             undefined;
      }

      // Calories actives
      const activeCalMetric = biometrics.find((b: any) => b.metric_type === 'active_calories');
      if (activeCalMetric) {
        activeCalories = activeCalMetric.value;
      }
    }

    // 3. Récupérer les baselines pour HRV
    const { data: baselines, error: baselineError } = await supabase
      .from('user_baselines')
      .select('*')
      .eq('user_id', userId)
      .eq('metric_type', 'hrv')
      .order('calculated_at', { ascending: false })
      .limit(1);

    if (baselineError) {
      console.error('[useNutritionHealthData] Baselines error:', baselineError);
    }

    const hrvBaseline = baselines && baselines.length > 0 
      ? baselines[0].median 
      : undefined;

    // 4. Récupérer les états quotidiens (recovery, energy)
    const { data: dailyStates, error: statesError } = await supabase
      .from('daily_state')
      .select('*')
      .eq('user_id', userId)
      .eq('state_date', dateStr);

    if (statesError) {
      console.error('[useNutritionHealthData] Daily states error:', statesError);
    }

    let recovery: number | undefined;
    if (dailyStates && dailyStates.length > 0) {
      const recoveryState = dailyStates.find((s: any) => s.state_type === 'recovery');
      if (recoveryState) {
        recovery = recoveryState.smoothed_score * 100; // Convertir 0-1 en 0-100
      }
    }

    // 5. Niveau d'énergie (approximation depuis recovery ou depuis un tracker)
    const energyLevel = recovery; // Pour l'instant, on utilise recovery comme proxy

    return {
      nutrition: {
        lastMealTime,
        proteinIntake,
        alcoholUnits, // TODO: Implémenter tracking alcool
        caffeineIntake, // TODO: Implémenter tracking caféine
        caffeineLastTime,
        waterIntake, // TODO: Implémenter tracking eau
        carbsIntake,
        caloriesIntake,
      },
      health: {
        sleepQuality,
        sleepDuration,
        sleepFragmentation,
        hrv,
        hrvBaseline,
        recovery,
        energyLevel,
        activeCalories,
      },
    };
  } catch (error) {
    console.error('[useNutritionHealthData] Unexpected error:', error);
    return { nutrition: {}, health: {} };
  }
}

export function useNutritionHealthData(userId: string | null, date: Date = new Date()) {
  return useQuery({
    queryKey: ['nutritionHealthData', userId, date.toISOString().split('T')[0]],
    queryFn: () => fetchNutritionHealthData(userId, date),
    enabled: !!userId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });
}
