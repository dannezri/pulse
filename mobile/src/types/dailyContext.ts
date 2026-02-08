// Types robustes pour le JSONB de daily_context
export interface NutritionDetails {
  calories?: number;
  carbs?: number;
  protein?: number;
  fat?: number;
  meal_type?: string;
  description?: string;
  [key: string]: any; // Flexibilité pour champs inconnus
}

export interface MedicationDetails {
  name?: string;
  dosage?: string;
  time?: string;
  [key: string]: any;
}

export interface SymptomDetails {
  description?: string;
  severity?: number;
  duration?: string;
  [key: string]: any;
}

export type DailyContextDetails = NutritionDetails | MedicationDetails | SymptomDetails | Record<string, any>;

export interface DailyContextRow {
  id: string;
  category: 'nutrition' | 'medication' | 'symptoms' | 'stool';
  details: DailyContextDetails;
  logged_at: string;
  source: string;
  created_at: string;
}

// Type guards
export function isNutritionDetails(details: any): details is NutritionDetails {
  return typeof details === 'object' && details !== null;
}

export function isMedicationDetails(details: any): details is MedicationDetails {
  return typeof details === 'object' && details !== null && 'name' in details;
}

export function isSymptomDetails(details: any): details is SymptomDetails {
  return typeof details === 'object' && details !== null && 'description' in details;
}

// Helper pour extraire description de façon safe
export function getDetailsDescription(details: DailyContextDetails): string {
  if (isSymptomDetails(details) && details.description) {
    return details.description;
  }
  if (isMedicationDetails(details) && details.name) {
    return details.name;
  }
  // Fallback: JSON.stringify
  return JSON.stringify(details);
}
