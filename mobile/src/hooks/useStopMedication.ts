/**
 * Hook pour terminer un traitement médicamenteux
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';

interface StopMedicationParams {
  medicationId: string;
  endDate: string; // Format ISO 8601 ou 'YYYY-MM-DD'
}

export function useStopMedication() {
  const queryClient = useQueryClient();

  const stopMedication = useMutation({
    mutationFn: async ({ medicationId, endDate }: StopMedicationParams) => {
      console.log(`[useStopMedication] 🛑 Arrêt du médicament ${medicationId} à la date ${endDate}`);

      // Convertir endDate en format DATE si nécessaire
      const endDateFormatted = endDate.split('T')[0]; // Garder seulement YYYY-MM-DD

      // 1. Supprimer l'historique des prises à partir de la date de fin
      console.log(`[useStopMedication] 🗑️ Suppression de l'historique à partir du ${endDateFormatted}`);
      const { error: deleteError } = await supabase
        .from('medication_intake_history')
        .delete()
        .eq('medication_id', medicationId)
        .gte('intake_date', endDateFormatted);

      if (deleteError) {
        console.error('[useStopMedication] ⚠️ Erreur lors de la suppression de l\'historique:', deleteError);
        // On continue quand même pour marquer le médicament comme arrêté
      } else {
        console.log('[useStopMedication] ✅ Historique nettoyé');
      }

      // 2. Marquer le médicament comme inactif avec la date de fin
      const { data, error } = await supabase
        .from('user_medications')
        .update({
          end_date: endDateFormatted,
          is_active: false,
          updated_at: new Date().toISOString(),
        })
        .eq('id', medicationId)
        .select()
        .single();

      if (error) {
        console.error('[useStopMedication] ❌ Erreur Supabase:', error);
        throw new Error(error.message || 'Impossible de terminer le traitement');
      }

      console.log('[useStopMedication] ✅ Médicament arrêté avec succès');
      return data;
    },
    onSuccess: () => {
      // Invalider les caches pour forcer le rechargement
      queryClient.invalidateQueries({ queryKey: ['medications'] });
      queryClient.invalidateQueries({ queryKey: ['medicationHistory'] });
      queryClient.invalidateQueries({ queryKey: ['medication', 'history'] });
    },
  });

  return {
    stopMedication: stopMedication.mutateAsync,
    isLoading: stopMedication.isPending,
    error: stopMedication.error,
  };
}
