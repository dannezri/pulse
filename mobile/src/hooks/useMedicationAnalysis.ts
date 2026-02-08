/**
 * Hook pour récupérer l'analyse Gemini des médicaments
 * Génère des explications détaillées et vulgarisées pour chaque médicament
 */

import { useQuery } from '@tanstack/react-query';
import Constants from 'expo-constants';
import { storage } from '../lib/storage';

/**
 * Interface pour un effet horaire (pour graphique)
 */
export interface HourlyEffect {
  heure: string; // Format "HH:00" (ex: "14:00")
  concentration: number; // 0-100
  efficacite: number; // 0-100
  effets_secondaires: number; // 0-100
  description: string;
}

export interface MedicationAnalysisItem {
  nom: string;
  intro_explicative: string;
  impact_corps: string;
  impact_journee: string;
  observation: string;
  label_concentration?: string; // Label adaptatif (ex: "Niveau sanguin")
  label_efficacite?: string; // Label adaptatif (ex: "Effet anxiolytique")
  label_effets_secondaires?: string; // Label adaptatif (ex: "Nausées/fatigue")
  heure_prise?: string; // Heure de prise (ex: "23:00")
  effets_horaires?: HourlyEffect[]; // Profil horaire sur 24h
}

export interface MedicationAnalysis {
  analyse_traitements: MedicationAnalysisItem[];
  _generated_at?: string;
  _medications_count?: number;
  _cost?: number;
  message?: string;
  error?: string;
}

interface UseMedicationAnalysisOptions {
  userId: string | null;
  enabled?: boolean;
}

async function fetchMedicationAnalysis(userId: string | null): Promise<MedicationAnalysis> {
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
  const url = `${backendUrl}/api/medications/analyze/${userId}`;
  
  console.log('[useMedicationAnalysis] 📡 Fetching analysis from:', url);

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${storedUserId}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('[useMedicationAnalysis] ❌ Error response:', errorText);
    throw new Error(`Failed to fetch medication analysis: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  console.log('[useMedicationAnalysis] ✅ Analysis received:', {
    medications_count: data.analyse_traitements?.length || 0,
    cost: data._cost,
    generated_at: data._generated_at,
  });

  return data;
}

/**
 * Hook pour récupérer l'analyse Gemini des médicaments
 * 
 * @example
 * ```tsx
 * const { data, isLoading, error, refetch } = useMedicationAnalysis({
 *   userId: 'user-123',
 *   enabled: true
 * });
 * 
 * if (isLoading) return <LoadingSkeleton />;
 * if (error) return <ErrorView message={error.message} />;
 * 
 * return <MedicationAnalysisView analyses={data.analyse_traitements} />;
 * ```
 */
export function useMedicationAnalysis({
  userId,
  enabled = true,
}: UseMedicationAnalysisOptions) {
  return useQuery<MedicationAnalysis, Error>({
    // Version 2: avec effets horaires
    queryKey: ['medications', 'analysis', 'v2', userId],
    queryFn: () => fetchMedicationAnalysis(userId),
    enabled: enabled && !!userId,
    staleTime: 0, // Force refetch (pour debug - remettre à 7j plus tard)
    gcTime: 1000 * 60 * 60 * 24 * 7, // 7 jours
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
}

/**
 * Hook helper pour obtenir l'analyse d'un médicament spécifique par son nom
 */
export function useMedicationAnalysisForMedication(
  userId: string | null,
  medicationName: string
): MedicationAnalysisItem | null {
  const { data } = useMedicationAnalysis({ userId });

  if (!data || !data.analyse_traitements) {
    return null;
  }

  // Recherche insensible à la casse
  const analysis = data.analyse_traitements.find(
    (item) => item.nom.toLowerCase() === medicationName.toLowerCase()
  );

  return analysis || null;
}
