/**
 * Hook pour récupérer l'impact énergétique des médicaments
 * Réutilise les données du forecast énergétique existant
 */

import { useMemo } from 'react';
import { useBriefData } from './useBriefData';
import { Medication } from './useMedications';

export interface MedicationImpact {
  medicationId: string;
  medicationName: string;
  impact: number; // Impact énergétique (positif ou négatif)
  impactText: string; // Texte formaté (ex: "+5%", "-12%")
  status: 'positive' | 'negative' | 'neutral';
  description?: string;
  atcCode?: string;
}

interface UseMedicationImpactsResult {
  impacts: Map<string, MedicationImpact>;
  loading: boolean;
  getMedicationImpact: (medication: Medication) => MedicationImpact | null;
  getTotalImpact: () => number;
}

export function useMedicationImpacts(userId: string | null): UseMedicationImpactsResult {
  const { data: briefData, isLoading } = useBriefData(userId);

  // Construire la map des impacts depuis le forecast
  const impacts = useMemo(() => {
    const impactsMap = new Map<string, MedicationImpact>();

    if (!briefData?.intraday_energy_forecast?.influencers) {
      return impactsMap;
    }

    const influencers = briefData.intraday_energy_forecast.influencers;

    // Filtrer les influencers de type médicament
    influencers.forEach((influencer: any) => {
      if (influencer.category === 'medication' || influencer.type === 'medication') {
        const name = influencer.name || influencer.title || '';
        
        // Extraire la valeur d'impact (peut être "±X%" ou un nombre)
        let impactValue = 0;
        let impactText = '0%';

        if (typeof influencer.impact === 'string') {
          const match = influencer.impact.match(/([+-]?\d+(?:\.\d+)?)/);
          if (match) {
            impactValue = parseFloat(match[1]);
            impactText = influencer.impact;
          }
        } else if (typeof influencer.impact === 'number') {
          impactValue = influencer.impact;
          impactText = `${impactValue > 0 ? '+' : ''}${impactValue.toFixed(1)}%`;
        }

        // Déterminer le statut
        let status: 'positive' | 'negative' | 'neutral' = 'neutral';
        if (impactValue > 2) {
          status = 'positive';
        } else if (impactValue < -2) {
          status = 'negative';
        }

        const impact: MedicationImpact = {
          medicationId: influencer.id || name.toLowerCase().replace(/\s+/g, '-'),
          medicationName: name,
          impact: impactValue,
          impactText,
          status: influencer.status || status,
          description: influencer.text || influencer.description,
          atcCode: influencer.atc_code,
        };

        // Utiliser le nom du médicament comme clé
        impactsMap.set(name.toLowerCase(), impact);
      }
    });

    return impactsMap;
  }, [briefData]);

  // Fonction pour obtenir l'impact d'un médicament spécifique
  const getMedicationImpact = (medication: Medication): MedicationImpact | null => {
    const key = medication.name.toLowerCase();
    return impacts.get(key) || null;
  };

  // Fonction pour calculer l'impact total
  const getTotalImpact = (): number => {
    let total = 0;
    impacts.forEach((impact) => {
      total += impact.impact;
    });
    return total;
  };

  return {
    impacts,
    loading: isLoading,
    getMedicationImpact,
    getTotalImpact,
  };
}
