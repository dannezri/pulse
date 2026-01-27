/**
 * Hook useVital - Gestion des connexions Vital
 * 
 * Ce hook gère l'état des connexions aux sources de tracking via Vital.
 */

import { useState, useEffect, useCallback } from 'react';
import { vitalService, VitalProvider } from '../services/vitalService';

export interface UseVitalReturn {
  // État
  isVitalConfigured: boolean;
  connections: VitalProvider[];
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setupVital: () => Promise<void>;
  refreshConnections: () => Promise<void>;
  getLinkToken: () => Promise<string>;
  disconnectProvider: (providerSlug: string) => Promise<void>;
  
  // Compteurs
  connectedCount: number;
}

export function useVital(): UseVitalReturn {
  const [isVitalConfigured, setIsVitalConfigured] = useState<boolean>(false);
  const [connections, setConnections] = useState<VitalProvider[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Vérifie si l'utilisateur a déjà un compte Vital
   * et charge les connexions si disponibles
   */
  const checkVitalStatus = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const hasAccount = await vitalService.hasVitalAccount();
      setIsVitalConfigured(hasAccount);

      if (hasAccount) {
        // Charger les connexions
        const result = await vitalService.getConnections();
        setConnections(result.providers);
      } else {
        setConnections([]);
      }
    } catch (err) {
      console.error('[useVital] Error checking Vital status:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      setIsVitalConfigured(false);
      setConnections([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Configure Vital pour la première fois
   * Crée un utilisateur Vital si nécessaire
   */
  const setupVital = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      console.log('[useVital] Setting up Vital...');

      // Créer l'utilisateur Vital
      await vitalService.createVitalUser();

      // Marquer comme configuré
      setIsVitalConfigured(true);

      console.log('[useVital] Vital setup complete');
    } catch (err) {
      console.error('[useVital] Error setting up Vital:', err);
      setError(err instanceof Error ? err.message : 'Failed to setup Vital');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Rafraîchit la liste des connexions
   */
  const refreshConnections = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      console.log('[useVital] Refreshing connections...');

      const result = await vitalService.getConnections();
      setConnections(result.providers);

      console.log(`[useVital] ${result.providers.length} connections loaded`);
    } catch (err) {
      console.error('[useVital] Error refreshing connections:', err);
      setError(err instanceof Error ? err.message : 'Failed to load connections');
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Génère un token Vital Link pour connecter une nouvelle source
   * 
   * @returns Le token à utiliser pour ouvrir le Vital Link Widget
   */
  const getLinkToken = useCallback(async (): Promise<string> => {
    try {
      setIsLoading(true);
      setError(null);

      console.log('[useVital] Generating link token...');

      const result = await vitalService.generateLinkToken();

      if (result.status !== 'success' || !result.link_token) {
        throw new Error('Failed to generate link token');
      }

      console.log('[useVital] Link token generated');
      return result.link_token;
    } catch (err) {
      console.error('[useVital] Error generating link token:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate link token');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Déconnecte un provider spécifique
   * 
   * @param providerSlug - Slug du provider à déconnecter
   */
  const disconnectProvider = useCallback(async (providerSlug: string) => {
    try {
      setIsLoading(true);
      setError(null);

      console.log(`[useVital] Disconnecting provider: ${providerSlug}`);

      await vitalService.disconnectProvider(providerSlug);

      // Rafraîchir les connexions
      await refreshConnections();

      console.log(`[useVital] Provider ${providerSlug} disconnected`);
    } catch (err) {
      console.error('[useVital] Error disconnecting provider:', err);
      setError(err instanceof Error ? err.message : 'Failed to disconnect provider');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [refreshConnections]);

  /**
   * Nombre de sources connectées
   */
  const connectedCount = connections.filter(
    (conn) => conn.status === 'connected' || conn.status === 'active'
  ).length;

  /**
   * Vérifier le statut Vital au montage du composant
   */
  useEffect(() => {
    checkVitalStatus();
  }, [checkVitalStatus]);

  return {
    // État
    isVitalConfigured,
    connections,
    isLoading,
    error,
    
    // Actions
    setupVital,
    refreshConnections,
    getLinkToken,
    disconnectProvider,
    
    // Compteurs
    connectedCount,
  };
}
