/**
 * Hook useNutritionInsights
 * 
 * Moteur d'intelligence nutritionnelle qui corrèle automatiquement :
 * - Données alimentaires (timing, composition, quantité)
 * - Métriques de santé (HRV, sommeil, récupération)
 * 
 * Génère des insights automatiques :
 * - "Repas tardifs → sommeil fragmenté"
 * - "Bonne répartition protéines → récupération meilleure"
 * - "Excès alcool → HRV réduite"
 * 
 * Format : Nutrition → Conséquence → Action
 */

import { useMemo } from 'react';

// Types d'insights nutritionnels
export type InsightType = 
  | 'late_meal_sleep'         // Repas tardifs affectant sommeil
  | 'protein_recovery'        // Protéines et récupération
  | 'alcohol_hrv'             // Alcool et HRV
  | 'caffeine_sleep'          // Caféine et qualité sommeil
  | 'hydration_performance'   // Hydratation et performance
  | 'carbs_energy'            // Glucides et niveau d'énergie
  | 'meal_timing_recovery';   // Timing des repas et récupération

export type InsightSeverity = 'positive' | 'neutral' | 'warning' | 'alert';

export interface NutritionInsight {
  id: string;
  type: InsightType;
  severity: InsightSeverity;
  title: string;
  observation: string;        // Ce qui a été détecté
  consequence: string;         // Impact sur la santé
  action: string;              // Recommandation concrète
  emoji: string;
  confidence: number;          // 0-1 (fiabilité de la corrélation)
  metrics: {
    nutrition: any;            // Données nutrition concernées
    health: any;               // Métriques santé impactées
  };
}

export interface NutritionInsightsData {
  insights: NutritionInsight[];
  hasData: boolean;
  analysisDate: string;
}

/**
 * Données d'entrée pour l'analyse
 */
interface NutritionData {
  lastMealTime?: string;       // ISO timestamp du dernier repas
  proteinIntake?: number;      // Grammes de protéines (journée)
  alcoholUnits?: number;       // Unités d'alcool (journée)
  caffeineIntake?: number;     // mg de caféine (journée)
  caffeineLastTime?: string;   // Timestamp dernier café
  waterIntake?: number;        // mL d'eau (journée)
  carbsIntake?: number;        // g de glucides (journée)
  caloriesIntake?: number;     // kcal totales (journée)
}

interface HealthData {
  sleepQuality?: number;       // Score 0-100
  sleepDuration?: number;      // Heures
  sleepFragmentation?: number; // Nombre de réveils
  hrv?: number;                // ms
  hrvBaseline?: number;        // ms (baseline personnelle)
  recovery?: number;           // Score 0-100
  energyLevel?: number;        // Score 0-100 (subjectif ou calculé)
  activeCalories?: number;     // kcal
}

/**
 * Détecte si un repas est "tardif" (>20h)
 */
function detectLateMeal(nutritionData: NutritionData, healthData: HealthData): NutritionInsight | null {
  if (!nutritionData.lastMealTime || !healthData.sleepFragmentation) {
    return null;
  }

  const mealTime = new Date(nutritionData.lastMealTime);
  const mealHour = mealTime.getHours();

  // Repas après 20h ET sommeil fragmenté (>3 réveils)
  if (mealHour >= 20 && healthData.sleepFragmentation > 3) {
    const confidence = Math.min(0.75 + (mealHour - 20) * 0.05, 0.95);
    
    return {
      id: 'late_meal_sleep_' + mealTime.toISOString(),
      type: 'late_meal_sleep',
      severity: 'warning',
      title: 'Repas tardif détecté',
      observation: `Dernier repas à ${mealHour}h`,
      consequence: `Sommeil fragmenté (${healthData.sleepFragmentation} réveils)`,
      action: 'Termine ton dernier repas avant 19h30 pour améliorer ton sommeil.',
      emoji: '🍽️',
      confidence,
      metrics: {
        nutrition: { mealTime: mealHour },
        health: { fragmentation: healthData.sleepFragmentation },
      },
    };
  }

  return null;
}

/**
 * Analyse la relation protéines <-> récupération
 */
function detectProteinRecovery(nutritionData: NutritionData, healthData: HealthData): NutritionInsight | null {
  if (!nutritionData.proteinIntake || !healthData.recovery) {
    return null;
  }

  const protein = nutritionData.proteinIntake;
  const recovery = healthData.recovery;

  // Bonne répartition protéines (>1.6g/kg) ET bonne récupération (>70)
  // Approximation: 80g+ de protéines pour un adulte moyen
  if (protein >= 80 && recovery >= 70) {
    return {
      id: 'protein_recovery_positive',
      type: 'protein_recovery',
      severity: 'positive',
      title: 'Excellente nutrition sportive',
      observation: `${Math.round(protein)}g de protéines`,
      consequence: `Récupération optimale (${Math.round(recovery)}%)`,
      action: 'Continue cet apport protéique, il soutient bien ta récupération.',
      emoji: '💪',
      confidence: 0.80,
      metrics: {
        nutrition: { protein },
        health: { recovery },
      },
    };
  }

  // Apport protéique faible (<60g) ET récupération moyenne/faible (<60)
  if (protein < 60 && recovery < 60) {
    return {
      id: 'protein_recovery_low',
      type: 'protein_recovery',
      severity: 'warning',
      title: 'Apport protéique insuffisant',
      observation: `Seulement ${Math.round(protein)}g de protéines`,
      consequence: `Récupération limitée (${Math.round(recovery)}%)`,
      action: 'Vise 1.6-2g de protéines par kg de poids corporel pour optimiser ta récupération.',
      emoji: '🥩',
      confidence: 0.65,
      metrics: {
        nutrition: { protein },
        health: { recovery },
      },
    };
  }

  return null;
}

/**
 * Détecte l'impact de l'alcool sur la HRV
 */
function detectAlcoholHRV(nutritionData: NutritionData, healthData: HealthData): NutritionInsight | null {
  if (!nutritionData.alcoholUnits || !healthData.hrv || !healthData.hrvBaseline) {
    return null;
  }

  const alcohol = nutritionData.alcoholUnits;
  const hrv = healthData.hrv;
  const baseline = healthData.hrvBaseline;
  const hrvDrop = ((baseline - hrv) / baseline) * 100;

  // Consommation d'alcool (>2 unités) ET HRV réduite (>10% sous baseline)
  if (alcohol >= 2 && hrvDrop > 10) {
    const severity: InsightSeverity = alcohol >= 4 ? 'alert' : 'warning';
    
    return {
      id: 'alcohol_hrv_impact',
      type: 'alcohol_hrv',
      severity,
      title: 'Impact alcool détecté',
      observation: `${alcohol} unités d'alcool hier`,
      consequence: `HRV réduite de ${Math.round(hrvDrop)}% (${Math.round(hrv)}ms vs ${Math.round(baseline)}ms)`,
      action: alcohol >= 4 
        ? 'Évite l\'alcool les 2-3 prochains jours pour permettre une récupération complète.'
        : 'Limite à 1-2 verres maximum si tu veux maintenir une HRV optimale.',
      emoji: '🍷',
      confidence: 0.85,
      metrics: {
        nutrition: { alcoholUnits: alcohol },
        health: { hrv, hrvBaseline: baseline, hrvDrop },
      },
    };
  }

  return null;
}

/**
 * Analyse l'impact de la caféine sur le sommeil
 */
function detectCaffeineSleep(nutritionData: NutritionData, healthData: HealthData): NutritionInsight | null {
  if (!nutritionData.caffeineIntake || !nutritionData.caffeineLastTime || !healthData.sleepQuality) {
    return null;
  }

  const caffeine = nutritionData.caffeineIntake;
  const lastCaffeineTime = new Date(nutritionData.caffeineLastTime);
  const lastCaffeineHour = lastCaffeineTime.getHours();
  const sleepQuality = healthData.sleepQuality;

  // Caféine tardive (>16h) ET mauvaise qualité de sommeil (<60)
  if (caffeine > 100 && lastCaffeineHour >= 16 && sleepQuality < 60) {
    return {
      id: 'caffeine_sleep_impact',
      type: 'caffeine_sleep',
      severity: 'warning',
      title: 'Caféine tardive détectée',
      observation: `${Math.round(caffeine)}mg de caféine, dernier café à ${lastCaffeineHour}h`,
      consequence: `Qualité de sommeil réduite (${Math.round(sleepQuality)}%)`,
      action: 'Coupe la caféine après 14h pour préserver ton sommeil.',
      emoji: '☕',
      confidence: 0.75,
      metrics: {
        nutrition: { caffeine, lastCaffeineHour },
        health: { sleepQuality },
      },
    };
  }

  return null;
}

/**
 * Analyse l'hydratation et la performance
 */
function detectHydrationPerformance(nutritionData: NutritionData, healthData: HealthData): NutritionInsight | null {
  if (!nutritionData.waterIntake || !healthData.activeCalories) {
    return null;
  }

  const water = nutritionData.waterIntake;
  const activeCalories = healthData.activeCalories;

  // Activité élevée (>500 kcal actives) mais hydratation faible (<1500mL)
  if (activeCalories > 500 && water < 1500) {
    return {
      id: 'hydration_performance_low',
      type: 'hydration_performance',
      severity: 'warning',
      title: 'Hydratation insuffisante',
      observation: `Seulement ${Math.round(water)}mL d'eau`,
      consequence: `Activité intense (${Math.round(activeCalories)} kcal brûlées)`,
      action: 'Vise 2-3L d\'eau par jour les jours d\'entraînement intense.',
      emoji: '💧',
      confidence: 0.70,
      metrics: {
        nutrition: { water },
        health: { activeCalories },
      },
    };
  }

  // Bonne hydratation (>2500mL) ET activité élevée
  if (activeCalories > 500 && water >= 2500) {
    return {
      id: 'hydration_performance_good',
      type: 'hydration_performance',
      severity: 'positive',
      title: 'Hydratation optimale',
      observation: `${Math.round(water / 1000)}L d'eau`,
      consequence: 'Soutien optimal de ta performance',
      action: 'Continue cette hydratation, c\'est parfait pour ton niveau d\'activité.',
      emoji: '💧',
      confidence: 0.75,
      metrics: {
        nutrition: { water },
        health: { activeCalories },
      },
    };
  }

  return null;
}

/**
 * Analyse glucides et niveau d'énergie
 */
function detectCarbsEnergy(nutritionData: NutritionData, healthData: HealthData): NutritionInsight | null {
  if (!nutritionData.carbsIntake || !healthData.energyLevel) {
    return null;
  }

  const carbs = nutritionData.carbsIntake;
  const energy = healthData.energyLevel;

  // Faible apport glucides (<100g) ET faible énergie (<50)
  if (carbs < 100 && energy < 50) {
    return {
      id: 'carbs_energy_low',
      type: 'carbs_energy',
      severity: 'warning',
      title: 'Glucides insuffisants',
      observation: `Seulement ${Math.round(carbs)}g de glucides`,
      consequence: `Niveau d'énergie bas (${Math.round(energy)}%)`,
      action: 'Ajoute des glucides complexes (riz, pâtes, pain complet) pour restaurer ton énergie.',
      emoji: '🍞',
      confidence: 0.65,
      metrics: {
        nutrition: { carbs },
        health: { energy },
      },
    };
  }

  return null;
}

/**
 * Hook principal - Génère les insights nutritionnels
 */
export function useNutritionInsights(
  nutritionData: NutritionData | undefined,
  healthData: HealthData | undefined
): NutritionInsightsData {
  return useMemo(() => {
    if (!nutritionData || !healthData) {
      return {
        insights: [],
        hasData: false,
        analysisDate: new Date().toISOString(),
      };
    }

    const insights: NutritionInsight[] = [];

    // Analyser chaque dimension
    const lateMeal = detectLateMeal(nutritionData, healthData);
    if (lateMeal) insights.push(lateMeal);

    const proteinRecovery = detectProteinRecovery(nutritionData, healthData);
    if (proteinRecovery) insights.push(proteinRecovery);

    const alcoholHRV = detectAlcoholHRV(nutritionData, healthData);
    if (alcoholHRV) insights.push(alcoholHRV);

    const caffeineSleep = detectCaffeineSleep(nutritionData, healthData);
    if (caffeineSleep) insights.push(caffeineSleep);

    const hydrationPerf = detectHydrationPerformance(nutritionData, healthData);
    if (hydrationPerf) insights.push(hydrationPerf);

    const carbsEnergy = detectCarbsEnergy(nutritionData, healthData);
    if (carbsEnergy) insights.push(carbsEnergy);

    // Trier par sévérité (alerts first, puis warnings, positives, neutral)
    const severityOrder = { alert: 0, warning: 1, neutral: 2, positive: 3 };
    insights.sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]);

    return {
      insights,
      hasData: insights.length > 0,
      analysisDate: new Date().toISOString(),
    };
  }, [nutritionData, healthData]);
}
