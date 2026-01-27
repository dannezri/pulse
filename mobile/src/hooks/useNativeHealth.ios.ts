import { useState, useCallback, useEffect } from 'react';
import { Alert, Platform } from 'react-native';
import * as Device from 'expo-device';
import * as HealthKit from '@/src/modules/pulseHealthkit';

/**
 * Fonction helper pour vérifier si on est sur un simulateur
 */
function isSimulator(): boolean {
  return !Device.isDevice;
}

/**
 * Hook iOS pour HealthKit
 * Utilise le module natif pulse-healthkit pour lire les données HealthKit
 */
export function useNativeHealth() {
  const [isAuthorized, setIsAuthorized] = useState<boolean | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [lastSyncDate, setLastSyncDate] = useState<Date | null>(null);
  const [isAvailable, setIsAvailable] = useState<boolean | null>(null);

  // Vérifier la disponibilité au montage
  useEffect(() => {
    const checkAvailability = async () => {
      if (Platform.OS !== 'ios') {
        setIsAvailable(false);
        return;
      }
      
      // Vérifier si on est sur un simulateur
      const simulator = isSimulator();
      if (simulator) {
        setIsAvailable(false);
        setIsAuthorized(false);
        return;
      }
      
      try {
        // Vérifier si HealthKit est disponible sur cet appareil
        const available = await HealthKit.isAvailable();
        setIsAvailable(available);
        
        if (available) {
          // Note: On ne peut pas vérifier le statut d'autorisation sans demander les permissions
          // On laisse isAuthorized à null jusqu'à la première tentative de sync
        }
      } catch (error) {
        console.error('[useNativeHealth] Erreur lors de la vérification de disponibilité:', error);
        setIsAvailable(false);
      }
    };
    
    checkAvailability();
  }, []);

  const checkAuthorizationStatus = useCallback(async (): Promise<boolean> => {
    if (Platform.OS !== 'ios') {
      setIsAuthorized(false);
      return false;
    }
    
    const simulator = isSimulator();
    if (simulator) {
      setIsAuthorized(false);
      return false;
    }
    
    try {
      const available = await HealthKit.isAvailable();
      if (!available) {
        setIsAuthorized(false);
        return false;
      }
      
      // Note: HealthKit ne permet pas de vérifier le statut sans demander les permissions
      // On retourne true si HealthKit est disponible, mais le vrai statut sera connu lors de requestAuthorization
      return true;
    } catch (error) {
      console.error('[useNativeHealth] Erreur lors de la vérification du statut:', error);
      setIsAuthorized(false);
      return false;
    }
  }, []);

  const checkAvailability = useCallback(async (): Promise<boolean> => {
    if (Platform.OS !== 'ios') {
      return false;
    }
    
    const simulator = isSimulator();
    if (simulator) {
      return false;
    }
    
    try {
      return await HealthKit.isAvailable();
    } catch (error) {
      console.error('[useNativeHealth] Erreur lors de la vérification de disponibilité:', error);
      return false;
    }
  }, []);

  const authorizeHealthKit = useCallback(async (): Promise<boolean> => {
    if (Platform.OS !== 'ios') {
      Alert.alert(
        'Non disponible',
        'HealthKit est disponible uniquement sur iOS.',
        [{ text: 'OK' }]
      );
      return false;
    }
    
    const simulator = isSimulator();
    if (simulator) {
      Alert.alert(
        'Simulateur détecté',
        'HealthKit est indisponible sur simulateur, lance l\'app sur un iPhone réel.',
        [{ text: 'OK' }]
      );
      return false;
    }
    
    try {
      const authorized = await HealthKit.requestAuthorization();
      setIsAuthorized(authorized);
      
      if (!authorized) {
        Alert.alert(
          'Autorisation refusée',
          'Les permissions HealthKit sont nécessaires pour synchroniser vos données de santé.',
          [{ text: 'OK' }]
        );
      }
      
      return authorized;
    } catch (error: any) {
      console.error('[useNativeHealth] Erreur lors de la demande d\'autorisation:', error);
      Alert.alert(
        'Erreur',
        error?.message || 'Une erreur est survenue lors de la demande d\'autorisation HealthKit.',
        [{ text: 'OK' }]
      );
      setIsAuthorized(false);
      return false;
    }
  }, []);

  const syncHealthData = useCallback(async (): Promise<boolean> => {
    if (Platform.OS !== 'ios') {
      Alert.alert(
        'Non disponible',
        'HealthKit est disponible uniquement sur iOS.',
        [{ text: 'OK' }]
      );
      return false;
    }
    
    const simulator = isSimulator();
    if (simulator) {
      Alert.alert(
        'Simulateur détecté',
        'HealthKit est indisponible sur simulateur, lance l\'app sur un iPhone réel.',
        [{ text: 'OK' }]
      );
      return false;
    }
    
    try {
      // Vérifier la disponibilité
      const available = await HealthKit.isAvailable();
      if (!available) {
        Alert.alert(
          'Non disponible',
          'HealthKit n\'est pas disponible sur cet appareil.',
          [{ text: 'OK' }]
        );
        return false;
      }
      
      // Demander les autorisations si nécessaire
      const authorized = await HealthKit.requestAuthorization();
      if (!authorized) {
        setIsAuthorized(false);
        Alert.alert(
          'Autorisation requise',
          'Les permissions HealthKit sont nécessaires pour synchroniser vos données.',
          [{ text: 'OK' }]
        );
        return false;
      }
      
      setIsAuthorized(true);
      
      // Calculer la période (7 derniers jours)
      const now = new Date();
      const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      const fromISO = sevenDaysAgo.toISOString();
      const toISO = now.toISOString();
      
      // Lire les données en parallèle
      const [steps, heartRates] = await Promise.all([
        HealthKit.readSteps(fromISO, toISO),
        HealthKit.readHeartRate(fromISO, toISO),
      ]);
      
      // Log des résultats
      console.log(`[HealthKit Sync] Succès: ${steps.length} échantillons de pas, ${heartRates.length} échantillons de fréquence cardiaque`);
      
      if (steps.length > 0) {
        const totalSteps = steps.reduce((sum, sample) => sum + sample.count, 0);
        console.log(`[HealthKit Sync] Total pas sur 7 jours: ${totalSteps}`);
      }
      
      if (heartRates.length > 0) {
        const avgBpm = heartRates.reduce((sum, sample) => sum + sample.bpm, 0) / heartRates.length;
        console.log(`[HealthKit Sync] Fréquence cardiaque moyenne: ${avgBpm.toFixed(1)} bpm`);
      }
      
      // Mettre à jour la date de dernière synchronisation
      setLastSyncDate(new Date());
      
      // Afficher un message de succès
      Alert.alert(
        'Synchronisation réussie',
        `Données synchronisées: ${steps.length} échantillons de pas, ${heartRates.length} échantillons de fréquence cardiaque.`,
        [{ text: 'OK' }]
      );
      
      return true;
    } catch (error: any) {
      console.error('[useNativeHealth] Erreur lors de la synchronisation:', error);
      Alert.alert(
        'Erreur de synchronisation',
        error?.message || 'Une erreur est survenue lors de la synchronisation des données HealthKit.',
        [{ text: 'OK' }]
      );
      return false;
    }
  }, []);

  // Nouvelle API: sync() et isAvailable()
  const sync = useCallback(async (): Promise<void> => {
    setIsSyncing(true);
    try {
      await syncHealthData();
    } finally {
      setIsSyncing(false);
    }
  }, [syncHealthData]);

  const isAvailableAsync = useCallback(async (): Promise<boolean> => {
    return await checkAvailability();
  }, [checkAvailability]);

  return {
    isAuthorized,
    isSyncing,
    lastSyncDate,
    authorizeHealthKit,
    syncHealthData,
    checkAuthorizationStatus,
    // Nouvelle API
    sync,
    isAvailable: isAvailableAsync,
    isAvailableValue: isAvailable,
  };
}
