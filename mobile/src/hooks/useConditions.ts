/**
 * Hook pour gérer les conditions de santé (ICD-11)
 */

import { useState, useEffect, useCallback } from 'react';
import { storage } from '@/lib/storage';
import { API_URL } from '@/config/api';

export interface Condition {
  id: string;
  system: string;
  code: string;
  display: string;
  category?: string;
  severity?: 'mild' | 'moderate' | 'severe' | null;
  diagnosed?: boolean | null;
  noted_at: string;
}

export interface SearchResult {
  code: string;
  display: string;
  category: string;
  kind?: 'consumer' | 'icd11';
  _score?: number;
}

export interface ConsumerSuggestion {
  label: string;
  codes: string[];
  category: string;
  kind: 'consumer';
}

export interface SearchResponse {
  query: string;
  suggestions: ConsumerSuggestion[];
  results: SearchResult[];
  more_results: boolean;
}

export function useConditions() {
  const [conditions, setConditions] = useState<Condition[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Récupérer les conditions de l'utilisateur
  const fetchConditions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const userId = await storage.getUserId();
      if (!userId) {
        throw new Error('User ID not found');
      }

      const response = await fetch(`${API_URL}/api/profile/conditions`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${userId}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setConditions(data.conditions || []);
    } catch (err: any) {
      console.error('[useConditions] Error fetching conditions:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Rechercher des conditions dans ICD-11
  const searchConditions = async (query: string, lang: string = 'fr'): Promise<any> => {
    try {
      if (query.trim().length < 2) {
        return { suggestions: [], results: [], more_results: false };
      }

      const response = await fetch(
        `${API_URL}/api/terminology/icd11/search?q=${encodeURIComponent(query)}&lang=${lang}&consumer_friendly=true`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Retourner le format complet {suggestions, results, more_results}
      return {
        suggestions: data.suggestions || [],
        results: data.results || [],
        more_results: data.more_results || false
      };
    } catch (err: any) {
      console.error('[useConditions] Error searching conditions:', err);
      throw err;
    }
  };

  // Ajouter une condition (depuis suggestion consumer ou résultat ICD-11)
  const addCondition = async (
    item: SearchResult | ConsumerSuggestion,
    severity?: 'mild' | 'moderate' | 'severe',
    diagnosed?: boolean
  ): Promise<boolean> => {
    try {
      const userId = await storage.getUserId();
      if (!userId) {
        throw new Error('User ID not found');
      }

      // Si c'est une suggestion consumer avec plusieurs codes, prendre le premier
      const code = 'code' in item ? item.code : item.codes[0];
      const display = 'display' in item ? item.display : item.label;
      const category = item.category;

      // Vérification idempotente : si la condition existe déjà, ne pas réessayer
      const existingCondition = conditions.find(
        (c) => c.system === 'icd11' && c.code === code
      );
      if (existingCondition) {
        console.log('[useConditions] Condition already exists, skipping add:', code);
        return true; // Opération idempotente : succès sans modification
      }

      const response = await fetch(`${API_URL}/api/profile/conditions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${userId}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          system: 'icd11',
          code,
          display,
          category,
          severity,
          diagnosed,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Ajouter la nouvelle condition à la liste locale
      if (data.condition) {
        setConditions((prev) => [...prev, data.condition]);
      }

      return true;
    } catch (err: any) {
      console.error('[useConditions] Error adding condition:', err);
      setError(err.message);
      return false;
    }
  };

  // Supprimer une condition
  const deleteCondition = async (conditionId: string): Promise<boolean> => {
    try {
      const userId = await storage.getUserId();
      if (!userId) {
        throw new Error('User ID not found');
      }

      const response = await fetch(`${API_URL}/api/profile/conditions/${conditionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${userId}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Retirer la condition de la liste locale
      setConditions((prev) => prev.filter((c) => c.id !== conditionId));

      return true;
    } catch (err: any) {
      console.error('[useConditions] Error deleting condition:', err);
      setError(err.message);
      return false;
    }
  };

  // Charger les conditions au mount
  useEffect(() => {
    fetchConditions();
  }, [fetchConditions]);

  return {
    conditions,
    loading,
    error,
    fetchConditions,
    searchConditions,
    addCondition,
    deleteCondition,
  };
}
