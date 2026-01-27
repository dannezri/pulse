import { useState, useCallback } from 'react';
import { Alert, Platform } from 'react-native';

/**
 * Hook fallback pour web/dev
 * HealthKit n'est pas disponible sur cette plateforme
 * 
 * NOTE: L'app utilise maintenant Vital comme passerelle principale pour
 * synchroniser les données de santé (Apple Health, Fitbit, Oura, etc.).
 * 
 * HealthKit iOS natif (pulse-healthkit/) reste disponible pour une
 * synchronisation directe locale, mais Vital est recommandé car:
 * - Supporte de nombreuses sources (pas seulement Apple Health)
 * - Synchronisation automatique via webhooks
 * - Fonctionne sur iOS et Android
 * 
 * Les deux systèmes coexistent et sont complémentaires.
 */
export function useNativeHealth() {
  const [isAuthorized] = useState<boolean | null>(false);
  const [isSyncing] = useState(false);
  const [lastSyncDate] = useState<Date | null>(null);

  const checkAuthorizationStatus = useCallback(async (): Promise<boolean> => {
    console.log('HealthKit n\'est pas disponible sur cette plateforme');
    return false;
  }, []);

  const authorizeHealthKit = useCallback(async (): Promise<boolean> => {
    const message = Platform.OS === 'ios' 
      ? 'HealthKit n\'est disponible que sur iOS.'
      : 'HealthKit est disponible uniquement sur iOS.';
    Alert.alert('Non disponible', message, [{ text: 'OK' }]);
    return false;
  }, []);

  const syncHealthData = useCallback(async (): Promise<boolean> => {
    const message = Platform.OS === 'ios'
      ? 'HealthKit n\'est pas disponible sur cette plateforme.'
      : 'HealthKit est disponible uniquement sur iOS.';
    Alert.alert('Non disponible', message);
    return false;
  }, []);

  // Nouvelle API: sync() et isAvailable()
  const sync = useCallback(async (): Promise<void> => {
    await syncHealthData();
  }, [syncHealthData]);

  const isAvailable = useCallback(async (): Promise<boolean> => {
    // HealthKit n'est pas disponible sur cette plateforme
    return false;
  }, []);

  return {
    isAuthorized,
    isSyncing,
    lastSyncDate,
    authorizeHealthKit,
    syncHealthData,
    checkAuthorizationStatus,
    // Nouvelle API
    sync,
    isAvailable,
    isAvailableValue: false,
  };
}
