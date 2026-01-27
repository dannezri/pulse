/**
 * Pulse HealthKit Module - JavaScript Wrapper
 * Wrapper JS pur qui réexporte le module natif pulse-healthkit
 * 
 * Règle : Ce fichier ne contient QUE du code JavaScript/TypeScript.
 * Tout le code natif (Swift/Kotlin) est dans pulse-healthkit/
 */

import { requireNativeModule } from 'expo-modules-core';

// Import du module natif depuis pulse-healthkit/
// En mode dev (Expo Go), le module natif n'est pas disponible
let PulseHealthkitModule: any = null;
try {
  PulseHealthkitModule = requireNativeModule('PulseHealthkit');
} catch (error) {
  console.warn('⚠️ Module natif PulseHealthkit non disponible (normal en mode Expo Go)');
  // Mock pour le développement
  PulseHealthkitModule = {
    isAvailable: () => Promise.resolve(false),
    requestAuthorization: () => Promise.resolve(false),
    readSteps: () => Promise.resolve([]),
    readHeartRate: () => Promise.resolve([]),
    readNutrition: () => Promise.resolve([]),
    readMedications: () => Promise.resolve([]),
    readSymptoms: () => Promise.resolve([]),
    readStool: () => Promise.resolve([]),
  };
}

/**
 * Vérifie si HealthKit est disponible sur cet appareil
 * @returns Promise<boolean> true si HealthKit est disponible
 */
export async function isAvailable(): Promise<boolean> {
  return await PulseHealthkitModule.isAvailable();
}

/**
 * Demande les autorisations HealthKit (lecture uniquement)
 * @returns Promise<boolean> true si les permissions sont accordées
 */
export async function requestAuthorization(): Promise<boolean> {
  return await PulseHealthkitModule.requestAuthorization();
}

/**
 * Lit les données de pas (steps) sur une période donnée
 * @param fromISO Date de début au format ISO 8601
 * @param toISO Date de fin au format ISO 8601
 * @returns Promise<StepsSample[]> Tableau d'échantillons de pas
 */
export async function readSteps(fromISO: string, toISO: string): Promise<StepsSample[]> {
  return await PulseHealthkitModule.readSteps(fromISO, toISO);
}

/**
 * Lit les données de fréquence cardiaque sur une période donnée
 * @param fromISO Date de début au format ISO 8601
 * @param toISO Date de fin au format ISO 8601
 * @returns Promise<HeartRateSample[]> Tableau d'échantillons de fréquence cardiaque
 */
export async function readHeartRate(fromISO: string, toISO: string): Promise<HeartRateSample[]> {
  return await PulseHealthkitModule.readHeartRate(fromISO, toISO);
}

/**
 * Type pour un échantillon de pas
 */
export interface StepsSample {
  start: string;  // ISO 8601
  end: string;    // ISO 8601
  count: number;
}

/**
 * Type pour un échantillon de fréquence cardiaque
 */
export interface HeartRateSample {
  time: string;   // ISO 8601
  bpm: number;
}

/**
 * Lit les données de nutrition (calories, glucides) sur une période donnée
 * @param fromISO Date de début au format ISO 8601
 * @param toISO Date de fin au format ISO 8601
 * @returns Promise<NutritionSample[]> Tableau d'échantillons de nutrition
 */
export async function readNutrition(fromISO: string, toISO: string): Promise<NutritionSample[]> {
  return await PulseHealthkitModule.readNutrition(fromISO, toISO);
}

/**
 * Lit les données de médicaments sur une période donnée
 * @param fromISO Date de début au format ISO 8601
 * @param toISO Date de fin au format ISO 8601
 * @returns Promise<MedicationSample[]> Tableau d'échantillons de médicaments
 */
export async function readMedications(fromISO: string, toISO: string): Promise<MedicationSample[]> {
  return await PulseHealthkitModule.readMedications(fromISO, toISO);
}

/**
 * Lit les données de symptômes sur une période donnée
 * @param fromISO Date de début au format ISO 8601
 * @param toISO Date de fin au format ISO 8601
 * @returns Promise<SymptomSample[]> Tableau d'échantillons de symptômes
 */
export async function readSymptoms(fromISO: string, toISO: string): Promise<SymptomSample[]> {
  return await PulseHealthkitModule.readSymptoms(fromISO, toISO);
}

/**
 * Lit les données de selles sur une période donnée
 * @param fromISO Date de début au format ISO 8601
 * @param toISO Date de fin au format ISO 8601
 * @returns Promise<StoolSample[]> Tableau d'échantillons de selles
 */
export async function readStool(fromISO: string, toISO: string): Promise<StoolSample[]> {
  return await PulseHealthkitModule.readStool(fromISO, toISO);
}

/**
 * Type pour un échantillon de nutrition
 */
export interface NutritionSample {
  type: 'calories' | 'carbs';
  value: number;
  logged_at: string;  // ISO 8601
}

/**
 * Type pour un échantillon de médicament
 */
export interface MedicationSample {
  logged_at: string;  // ISO 8601
  value: number;
}

/**
 * Type pour un échantillon de symptôme
 */
export interface SymptomSample {
  logged_at: string;  // ISO 8601
  value: number;
}

/**
 * Type pour un échantillon de selles
 */
export interface StoolSample {
  logged_at: string;  // ISO 8601
  value: number;
}

export default PulseHealthkitModule;
