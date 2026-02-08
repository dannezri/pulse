/**
 * Hook useEnergyProfile
 * 
 * Récupère le profil énergétique personnel de l'utilisateur
 * - Patterns appris sur le long terme (60-90 jours d'historique)
 * - Traits personnels validés par le système de machine learning
 * 
 * Exemples de traits:
 * - "Tu récupères mieux avec 7h45 de sommeil"
 * - "Café après 16h dégrade ton sommeil"
 * - "Sport tardif réduit HRV"
 */

import { useQuery } from '@tanstack/react-query';
import { supabase } from '../lib/supabase';

export type TraitCategory = 'sleep' | 'nutrition' | 'exercise' | 'recovery' | 'stress' | 'timing';

export interface EnergyProfileTrait {
  id: string;
  trait_type: string;
  category: TraitCategory;
  title: string;
  description: string;
  value_numeric?: number;
  value_text?: string;
  confidence: number; // 0-1
  support_data: {
    sample_size: number;
    average_recovery?: number;
    other_average?: number;
    improvement?: string;
    analyzed_days?: number;
    p_value?: number;
    [key: string]: any;
  };
  discovered_at: string;
  last_validated: string;
  data_points_count: number;
}

export interface EnergyProfile {
  traits: EnergyProfileTrait[];
  hasData: boolean;
  traitsByCategory: Record<TraitCategory, EnergyProfileTrait[]>;
  highConfidenceTraits: EnergyProfileTrait[]; // confidence >= 0.80
}

async function fetchEnergyProfile(userId: string | null): Promise<EnergyProfile> {
  if (!userId) {
    return {
      traits: [],
      hasData: false,
      traitsByCategory: {
        sleep: [],
        nutrition: [],
        exercise: [],
        recovery: [],
        stress: [],
        timing: [],
      },
      highConfidenceTraits: [],
    };
  }

  try {
    // Appeler la RPC function
    const { data, error } = await supabase
      .rpc('get_user_energy_profile', { p_user_id: userId });

    if (error) {
      console.error('[useEnergyProfile] Error fetching profile:', error);
      return {
        traits: [],
        hasData: false,
        traitsByCategory: {
          sleep: [],
          nutrition: [],
          exercise: [],
          recovery: [],
          stress: [],
          timing: [],
        },
        highConfidenceTraits: [],
      };
    }

    const traits: EnergyProfileTrait[] = data || [];

    // Grouper par catégorie
    const traitsByCategory: Record<TraitCategory, EnergyProfileTrait[]> = {
      sleep: [],
      nutrition: [],
      exercise: [],
      recovery: [],
      stress: [],
      timing: [],
    };

    traits.forEach(trait => {
      if (trait.category in traitsByCategory) {
        traitsByCategory[trait.category as TraitCategory].push(trait);
      }
    });

    // Filtrer les traits haute confiance (>= 80%)
    const highConfidenceTraits = traits.filter(t => t.confidence >= 0.80);

    return {
      traits,
      hasData: traits.length > 0,
      traitsByCategory,
      highConfidenceTraits,
    };
  } catch (err) {
    console.error('[useEnergyProfile] Unexpected error:', err);
    return {
      traits: [],
      hasData: false,
      traitsByCategory: {
        sleep: [],
        nutrition: [],
        exercise: [],
        recovery: [],
        stress: [],
        timing: [],
      },
      highConfidenceTraits: [],
    };
  }
}

export function useEnergyProfile(userId: string | null) {
  return useQuery({
    queryKey: ['energyProfile', userId],
    queryFn: () => fetchEnergyProfile(userId),
    enabled: !!userId,
    staleTime: 24 * 60 * 60 * 1000, // 24 heures (profile stable)
    retry: 1,
  });
}
