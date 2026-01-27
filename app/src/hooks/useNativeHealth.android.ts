import { useState, useCallback } from 'react';
import { Alert } from 'react-native';

/**
 * Hook Android pour Health Connect
 * Stub pour l'instant - Health Connect sera implémenté dans une phase ultérieure
 */
export function useNativeHealth() {
  const [isAuthorized] = useState<boolean | null>(false);
  const [isSyncing] = useState(false);
  const [lastSyncDate] = useState<Date | null>(null);

  const checkAuthorizationStatus = useCallback(async (): Promise<boolean> => {
    console.log('[Android] Health Connect - bientôt disponible');
    return false;
  }, []);

  const authorizeHealthKit = useCallback(async (): Promise<boolean> => {
    Alert.alert(
      'Bientôt disponible',
      'L\'intégration Health Connect Android sera disponible prochainement. Pour l\'instant, HealthKit iOS est pris en charge.',
      [{ text: 'OK' }]
    );
    return false;
  }, []);

  const syncHealthData = useCallback(async (): Promise<boolean> => {
    Alert.alert(
      'Bientôt disponible',
      'L\'intégration Health Connect Android sera disponible prochainement. Pour l\'instant, HealthKit iOS est pris en charge.'
    );
    return false;
  }, []);

  // Nouvelle API: sync() et isAvailable()
  const sync = useCallback(async (): Promise<void> => {
    console.log('[Android] Health Connect - bientôt disponible');
    await syncHealthData();
  }, [syncHealthData]);

  const isAvailable = useCallback(async (): Promise<boolean> => {
    // Health Connect n'est pas encore implémenté
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
