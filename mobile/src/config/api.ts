/**
 * Configuration API dynamique
 * Détecte automatiquement si on est sur device ou simulateur
 */

import Constants from 'expo-constants';
import { Platform } from 'react-native';

/**
 * Retourne l'URL de l'API backend en fonction de l'environnement
 */
export function getApiUrl(): string {
  // 1. Si défini dans .env, l'utiliser (priorité)
  if (process.env.EXPO_PUBLIC_API_URL) {
    return process.env.EXPO_PUBLIC_API_URL;
  }

  // 2. Sinon, détecter automatiquement
  const isSimulator = Constants.isDevice === false;
  
  if (Platform.OS === 'ios') {
    // Sur simulateur iOS, localhost fonctionne
    if (isSimulator) {
      return 'http://localhost:9000';
    }
    // Sur device iOS, utiliser l'IP locale du Mac
    // ✅ IP automatiquement détectée: 192.168.0.23
    return 'http://192.168.0.23:9000';
  }
  
  if (Platform.OS === 'android') {
    // Sur Android, 10.0.2.2 = localhost de l'hôte
    if (isSimulator) {
      return 'http://10.0.2.2:9000';
    }
    // Sur device Android, utiliser l'IP locale
    // ✅ IP automatiquement détectée: 192.168.0.23
    return 'http://192.168.0.23:9000';
  }
  
  // Fallback
  return 'http://localhost:9000';
}

export const API_URL = getApiUrl();

console.log('[API Config] Using API URL:', API_URL);
