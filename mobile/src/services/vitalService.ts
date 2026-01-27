/**
 * Service Vital - Gestion des connexions aux sources de tracking
 * 
 * Ce service communique avec le backend Pulse qui gère l'API Vital.
 * Pas de SDK direct (n'existe pas pour React Native).
 */

import Constants from 'expo-constants';
import { storage } from '../lib/storage';

const BACKEND_URL = Constants.expoConfig?.extra?.backendUrl || 'http://localhost:9000';

export interface VitalProvider {
  name: string;
  slug: string;
  status: string;
  created_at?: string;
  last_sync_at?: string;
}

export interface VitalConnection {
  status: 'success' | 'error';
  providers: VitalProvider[];
}

export interface VitalLinkToken {
  status: 'success' | 'error';
  link_token: string;
  expires_at?: string;
}

export interface VitalUserResponse {
  status: 'success' | 'error';
  vital_user_id: string;
  client_user_id: string;
  message?: string;
}

/**
 * Service Vital pour gérer les connexions sources de tracking
 */
class VitalService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = BACKEND_URL;
  }

  /**
   * Récupère le JWT token depuis le storage local
   */
  private async getAuthToken(): Promise<string | null> {
    // Dans le MVP actuel, on n'a pas de JWT token car l'auth est basique
    // Pour l'instant, on utilise juste le userId
    // TODO: Implémenter proper JWT auth
    const userId = await storage.getUserId();
    return userId;
  }

  /**
   * Fait un appel API avec authentification
   */
  private async apiCall<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = await this.getAuthToken();

    if (!token) {
      throw new Error('User not authenticated');
    }

    // Pour l'instant, on passe le user_id dans le header Authorization
    // comme Bearer token temporaire (à remplacer par proper JWT)
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    };

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `API call failed: ${response.status}`
      );
    }

    return response.json();
  }

  /**
   * Crée un utilisateur Vital
   * 
   * Doit être appelé une seule fois par utilisateur.
   * Si l'utilisateur existe déjà, retourne l'utilisateur existant.
   */
  async createVitalUser(): Promise<VitalUserResponse> {
    try {
      console.log('[VitalService] Creating Vital user...');
      const response = await this.apiCall<VitalUserResponse>(
        '/api/vital/create-user',
        {
          method: 'POST',
        }
      );

      console.log('[VitalService] Vital user created:', response.vital_user_id);
      return response;
    } catch (error) {
      console.error('[VitalService] Error creating Vital user:', error);
      throw error;
    }
  }

  /**
   * Génère un token Vital Link pour connecter des sources
   * 
   * Ce token est utilisé pour ouvrir le Vital Link Widget (WebView).
   * Le token expire après un certain temps.
   */
  async generateLinkToken(): Promise<VitalLinkToken> {
    try {
      console.log('[VitalService] Generating Vital Link token...');
      const response = await this.apiCall<VitalLinkToken>(
        '/api/vital/link-token',
        {
          method: 'POST',
        }
      );

      console.log('[VitalService] Link token generated');
      return response;
    } catch (error) {
      console.error('[VitalService] Error generating link token:', error);
      throw error;
    }
  }

  /**
   * Récupère les sources connectées pour l'utilisateur
   * 
   * Retourne la liste des providers (Apple Health, Fitbit, etc.)
   * avec leur statut de connexion.
   */
  async getConnections(): Promise<VitalConnection> {
    try {
      // console.log('[VitalService] Fetching connections...');
      const response = await this.apiCall<VitalConnection>(
        '/api/vital/connections',
        {
          method: 'GET',
        }
      );

      console.log(
        `[VitalService] Retrieved ${response.providers.length} connections`
      );
      return response;
    } catch (error: any) {
      // Vital n'est pas encore implémenté côté backend
      // Retourner un objet vide au lieu de crasher
      if (error?.message?.includes('Not Found') || error?.message?.includes('404')) {
        // console.log('[VitalService] Vital API not yet implemented');
        throw new Error('Vital API not implemented');
      }
      console.error('[VitalService] Error fetching connections:', error);
      throw error;
    }
  }

  /**
   * Déconnecte une source spécifique
   * 
   * @param providerSlug - Slug du provider (ex: "apple_health", "fitbit")
   */
  async disconnectProvider(providerSlug: string): Promise<void> {
    try {
      console.log(`[VitalService] Disconnecting provider: ${providerSlug}...`);
      await this.apiCall(`/api/vital/connections/${providerSlug}`, {
        method: 'DELETE',
      });

      console.log(`[VitalService] Provider ${providerSlug} disconnected`);
    } catch (error) {
      console.error('[VitalService] Error disconnecting provider:', error);
      throw error;
    }
  }

  /**
   * Construit l'URL du Vital Link Widget
   * 
   * @param linkToken - Token généré par generateLinkToken()
   * @returns URL complète du widget à ouvrir dans une WebView
   */
  getVitalLinkUrl(linkToken: string): string {
    const region = Constants.expoConfig?.extra?.vitalRegion || 'us';
    const environment =
      Constants.expoConfig?.extra?.vitalEnvironment || 'sandbox';

    // URL du widget Vital Link selon l'environnement
    if (environment === 'sandbox') {
      return `https://link.sandbox.tryvital.io/?token=${linkToken}&region=${region}`;
    } else {
      return `https://link.tryvital.io/?token=${linkToken}&region=${region}`;
    }
  }

  /**
   * Vérifie si l'utilisateur a déjà un compte Vital
   * 
   * Tente de récupérer les connexions. Si ça échoue avec 404,
   * l'utilisateur n'existe pas côté Vital.
   */
  async hasVitalAccount(): Promise<boolean> {
    try {
      await this.getConnections();
      return true;
    } catch (error: any) {
      if (error.message?.includes('Vital API not implemented') || 
          error.message?.includes('404') || 
          error.message?.includes('not found') || 
          error.message?.includes('Not Found')) {
        return false;
      }
      // Autre erreur (network, etc.) - on considère que le compte n'existe pas
      return false;
    }
  }
}

// Export singleton
export const vitalService = new VitalService();
