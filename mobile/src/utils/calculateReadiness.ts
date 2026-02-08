// Algorithme de Readiness inspiré d'Oura/Whoop
// HRV: 45%, Sleep: 40%, RHR: 15%

export interface ReadinessInput {
  currentHRV: number | null;
  baselineHRV: number | null;
  sleepMinutes: number | null;
  targetSleepMinutes: number;
  currentRHR: number | null;
  baselineRHR: number | null;
}

export interface ReadinessResult {
  totalScore: number;
  hrvScore: number;
  sleepScore: number;
  rhrScore: number;
  interpretation: 'ready' | 'vigilance' | 'recovery';
  interpretationText: string;
  color: string;
}

export function calculateReadiness(input: ReadinessInput): ReadinessResult {
  // HRV Score (45% max)
  let hrvScore = 0;
  if (input.currentHRV && input.baselineHRV) {
    const ratio = input.currentHRV / input.baselineHRV;
    hrvScore = Math.min(ratio * 45, 45);
  }

  // Sleep Score (40% max)
  let sleepScore = 0;
  if (input.sleepMinutes) {
    const ratio = input.sleepMinutes / input.targetSleepMinutes;
    sleepScore = Math.min(ratio * 40, 40);
  }

  // RHR Score (15% max, pénalité si > baseline)
  let rhrScore = 15;
  if (input.currentRHR && input.baselineRHR) {
    const diff = input.currentRHR - input.baselineRHR;
    if (diff > 0) {
      rhrScore = Math.max(15 - (diff * 3), 0);
    }
  }

  const totalScore = Math.round(hrvScore + sleepScore + rhrScore);

  // Interprétation
  let interpretation: 'ready' | 'vigilance' | 'recovery';
  let interpretationText: string;
  let color: string;

  if (totalScore > 85) {
    interpretation = 'ready';
    interpretationText = 'SYSTÈME PRÊT';
    color = '#34C759';
  } else if (totalScore >= 60) {
    interpretation = 'vigilance';
    interpretationText = 'VIGILANCE';
    color = '#FF9500';
  } else {
    interpretation = 'recovery';
    interpretationText = 'RÉCUPÉRATION REQUISE';
    color = '#FF3B30';
  }

  return {
    totalScore,
    hrvScore: Math.round(hrvScore),
    sleepScore: Math.round(sleepScore),
    rhrScore: Math.round(rhrScore),
    interpretation,
    interpretationText,
    color,
  };
}
