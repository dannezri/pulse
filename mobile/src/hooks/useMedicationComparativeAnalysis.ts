/**
 * Hook pour récupérer l'analyse comparative détaillée des traitements avec Gemini
 * Analyse les changements (ajouts, arrêts, modifications) et génère une synthèse complète
 */

import { useQuery } from '@tanstack/react-query';
import Constants from 'expo-constants';
import { storage } from '../lib/storage';

export interface ComparativeAnalysisData {
  analysis_text: string;
  has_changes: boolean;
  medications_count: number;
  new_medications: number;
  stopped_medications: number;
  modified_medications: number;
  _generated_at?: string;
}

interface UseComparativeAnalysisOptions {
  userId: string | null;
  enabled?: boolean;
}

async function fetchComparativeAnalysis(userId: string | null): Promise<ComparativeAnalysisData> {
  if (!userId) {
    throw new Error('User ID is required');
  }

  // Récupérer le userId stocké pour l'auth (utilisé comme token)
  const storedUserId = await storage.getUserId();
  if (!storedUserId) {
    throw new Error('User ID not found in storage');
  }

  // Récupérer l'URL du backend
  const backendUrl = Constants.expoConfig?.extra?.backendUrl || 'http://localhost:9000';

  // Construire l'URL
  const url = `${backendUrl}/api/medications/comparative-analysis/${userId}`;
  
  console.log('[useComparativeAnalysis] 📡 Fetching from:', url);

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${storedUserId}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('[useComparativeAnalysis] ❌ Error response:', errorText);
    throw new Error(`Failed to fetch comparative analysis: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  console.log('[useComparativeAnalysis] ✅ Analysis received:', {
    has_changes: data.has_changes,
    medications_count: data.medications_count,
    new: data.new_medications,
    stopped: data.stopped_medications,
  });

  return data;
}

/**
 * Hook pour récupérer l'analyse comparative détaillée des médicaments
 * 
 * @example
 * ```tsx
 * const { data, isLoading, error } = useMedicationComparativeAnalysis({
 *   userId: 'user-123',
 *   enabled: true
 * });
 * 
 * if (isLoading) return <LoadingSkeleton />;
 * if (error) return <ErrorView message={error.message} />;
 * 
 * return <Text>{data.analysis_text}</Text>;
 * ```
 */
export function useMedicationComparativeAnalysis({
  userId,
  enabled = true,
}: UseComparativeAnalysisOptions) {
  return useQuery<ComparativeAnalysisData, Error>({
    queryKey: ['medications', 'comparative-analysis', userId],
    queryFn: () => fetchComparativeAnalysis(userId),
    enabled: enabled && !!userId,
    staleTime: 1000 * 60 * 60 * 24, // 24 heures (l'analyse change peu)
    gcTime: 1000 * 60 * 60 * 24 * 7, // 7 jours
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
}
