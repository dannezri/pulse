/**
 * Algorithme Révolutionnaire Pulse Score
 * 
 * Cet algorithme contredit intelligemment les scores optimistes des wearables
 * en se focalisant sur les vulnérabilités réelles.
 * 
 * Exemple: Avec HRV stable, Timing 23, Deep Sleep 54:
 * - Oura affiche 87% (READY)
 * - Pulse calcule ~68% (WARNING)
 * Cette "honnêteté biologique" crée la confiance.
 */

import { PulseMetrics, PulseScoreResult } from '../types/brief';

export function calculatePulseScore(metrics: PulseMetrics): PulseScoreResult {
  // 1. Calcul du HRV Score (40% du total)
  // On compare le HRV actuel à la baseline. 
  // Un ratio de 1 = 100% de la part allouée (40 points).
  const hrvRatio = metrics.hrv / metrics.hrvBaseline;
  const hrvPart = Math.min(hrvRatio * 40, 40);

  // 2. Calcul du Timing Score (30% du total)
  // C'est le point faible critique (23/100 dans le rapport actuel).
  const timingPart = (metrics.sleepTiming / 100) * 30;

  // 3. Calcul du Deep Sleep Score (20% du total)
  const deepPart = (metrics.sleepDeep / 100) * 20;

  // 4. Calcul du RHR Score (10% du total)
  // On pénalise si le RHR est plus haut que la baseline.
  let rhrPart = 10;
  const rhrDiff = metrics.rhr - metrics.rhrBaseline;
  if (rhrDiff > 0) {
    rhrPart = Math.max(10 - (rhrDiff * 2), 0); // -2 points par battement d'écart
  }

  // Score Total
  const totalScore = Math.round(hrvPart + timingPart + deepPart + rhrPart);

  // 5. Identification de la métrique la plus faible pour le diagnostic
  const components = [
    { name: 'HRV', score: (hrvPart / 40) * 100, value: metrics.hrv },
    { name: 'Timing', score: metrics.sleepTiming, value: metrics.sleepTiming },
    { name: 'Sommeil Profond', score: metrics.sleepDeep, value: metrics.sleepDeep },
    { name: 'Repos Cardiaque', score: (rhrPart / 10) * 100, value: metrics.rhr }
  ];

  const weakest = components.reduce((prev, curr) => 
    (prev.score < curr.score) ? prev : curr
  );

  // 6. Détermination de l'état
  let state: 'optimal' | 'warning' | 'alert' = 'optimal';
  let color = '#34C759'; // Vert

  if (totalScore < 50 || metrics.sleepTiming < 30) {
    state = 'alert';
    color = '#FF3B30'; // Rouge
  } else if (totalScore < 75 || weakest.score < 50) {
    state = 'warning';
    color = '#FF9500'; // Orange
  }

  return {
    score: totalScore,
    state,
    color,
    weakestMetric: {
      name: weakest.name,
      value: weakest.value,
      impact: Math.round(100 - weakest.score)
    }
  };
}
