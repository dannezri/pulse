/**
 * Hook pour modifier la posologie d'un médicament à partir d'une date
 */

import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import Constants from 'expo-constants';
import { storage } from '../lib/storage';

interface UpdateDosageParams {
  medicationId: string;
  newDosage: string;
  newDosageUnit: string;
  newPillsPerIntake: number;
  effectiveDate: string;
}

export function useUpdateMedicationDosage() {
  const [isLoading, setIsLoading] = useState(false);
  const queryClient = useQueryClient();

  const updateDosage = async (params: UpdateDosageParams) => {
    setIsLoading(true);
    try {
      const userId = await storage.getUserId();
      if (!userId) {
        throw new Error('User ID not found');
      }

      const backendUrl = Constants.expoConfig?.extra?.backendUrl || 'http://localhost:9000';
      const url = `${backendUrl}/api/medications/${params.medicationId}/dosage`;

      console.log('[useUpdateMedicationDosage] 📝 Updating dosage:', {
        medicationId: params.medicationId,
        newDosage: params.newDosage,
        effectiveDate: params.effectiveDate,
      });

      const response = await fetch(url, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userId}`,
        },
        body: JSON.stringify({
          new_dosage: params.newDosage,
          new_dosage_unit: params.newDosageUnit,
          new_pills_per_intake: params.newPillsPerIntake,
          effective_date: params.effectiveDate,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('[useUpdateMedicationDosage] ❌ Error:', errorText);
        throw new Error(`Failed to update dosage: ${response.status}`);
      }

      const data = await response.json();
      console.log('[useUpdateMedicationDosage] ✅ Dosage updated:', data);

      // Invalider les caches
      queryClient.invalidateQueries({ queryKey: ['medications', userId] });
      queryClient.invalidateQueries({ queryKey: ['medication-history', userId] });
      queryClient.invalidateQueries({ queryKey: ['medications', 'analysis', userId] });
      queryClient.invalidateQueries({ queryKey: ['medications', 'comparative-analysis', userId] });

      return data;
    } catch (error) {
      console.error('[useUpdateMedicationDosage] ❌ Error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    updateDosage,
    isLoading,
  };
}
