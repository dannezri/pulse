/**
 * Pulse HealthKit Module - JavaScript Wrapper
 * Wrapper JS pur qui réexporte le module natif pulse-healthkit
 * 
 * Règle : Ce fichier ne contient QUE du code JavaScript/TypeScript.
 * Tout le code natif (Swift/Kotlin) est dans pulse-healthkit/
 */

import { requireNativeModule } from 'expo-modules-core';

// Import du module natif depuis pulse-healthkit/
const PulseHealthkitModule = requireNativeModule('PulseHealthkit');

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

export default PulseHealthkitModule;
