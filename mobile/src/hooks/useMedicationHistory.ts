import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import { storage } from '@/lib/storage';
import { useAuth } from '@/hooks/useAuth';
import React from 'react';

export interface MedicationIntake {
  id: string;
  user_id: string;
  medication_id: string;
  taken_at: string;
  intake_date: string;
  intake_time?: string;
  scheduled_time?: string;
  was_on_time: boolean;
  pills_taken: number;
  status: 'taken' | 'skipped' | 'late' | 'early';
  notes?: string;
  created_at: string;
  updated_at: string;
  
  // Relations (jointure)
  medication?: {
    id: string;
    medication_name: string;
    dosage: number;
    dosage_unit: string;
  };
}

export interface DailyIntakeSummary {
  date: string;
  intakes: MedicationIntake[];
  totalIntakes: number;
  takenCount: number;
  skippedCount: number;
}

/**
 * Hook pour récupérer l'historique des prises de médicaments
 */
export function useMedicationHistory() {
  const { userId } = useAuth();

  return useQuery({
    queryKey: ['medication', 'history', userId],
    queryFn: async () => {
      if (!userId) {
        console.log('[useMedicationHistory] ℹ️ No user ID, skipping fetch');
        return [];
      }

      console.log('[useMedicationHistory] 🔄 Fetching medication intake history...');
      console.log('[useMedicationHistory] 👤 UserId:', userId);

      // Utiliser la fonction RPC qui bypass RLS
      const { data, error } = await supabase.rpc('get_medication_history', {
        p_user_id: userId
      });

      if (error) {
        console.error('[useMedicationHistory] ❌ Error fetching history:', error);
        console.error('[useMedicationHistory] 📋 Error details:', JSON.stringify(error, null, 2));
        throw error;
      }

      console.log(`[useMedicationHistory] ✅ Fetched ${data?.length || 0} intake records`);
      if (data && data.length > 0) {
        console.log('[useMedicationHistory] 📊 Sample data:', data[0]);
      }
      
      // Transformer les données RPC en format attendu (avec objet medication imbriqué)
      const transformedData: MedicationIntake[] = (data || []).map((item: any) => ({
        id: item.id,
        user_id: item.user_id,
        medication_id: item.medication_id,
        taken_at: item.taken_at,
        intake_date: item.intake_date,
        intake_time: item.intake_time,
        scheduled_time: item.scheduled_time,
        was_on_time: item.was_on_time,
        pills_taken: item.pills_taken,
        status: item.status,
        notes: item.notes,
        created_at: item.created_at,
        updated_at: item.updated_at,
        medication: {
          id: item.medication_id,
          medication_name: item.medication_name,
          dosage: item.dosage,
          dosage_unit: item.dosage_unit,
        },
      }));
      
      return transformedData;
    },
    enabled: !!userId,
    staleTime: 1000 * 60, // 1 minute
  });
}

/**
 * Hook pour récupérer l'historique groupé par jour
 */
export function useMedicationHistoryByDay() {
  const { data: intakes, ...rest } = useMedicationHistory();

  // Grouper les prises par jour
  const groupedByDay: DailyIntakeSummary[] = React.useMemo(() => {
    if (!intakes || intakes.length === 0) return [];

    const grouped = new Map<string, MedicationIntake[]>();

    for (const intake of intakes) {
      const date = intake.intake_date;
      if (!grouped.has(date)) {
        grouped.set(date, []);
      }
      grouped.get(date)!.push(intake);
    }

    return Array.from(grouped.entries()).map(([date, intakes]) => ({
      date,
      intakes,
      totalIntakes: intakes.length,
      takenCount: intakes.filter(i => i.status === 'taken').length,
      skippedCount: intakes.filter(i => i.status === 'skipped').length,
    }));
  }, [intakes]);

  return {
    data: groupedByDay,
    ...rest,
  };
}

/**
 * Hook pour enregistrer une prise de médicament
 */
export function useRecordMedicationIntake() {
  const queryClient = useQueryClient();
  const userId = storage.userId;

  return useMutation({
    mutationFn: async (params: {
      medicationId: string;
      takenAt?: Date;
      scheduledTime?: string;
      pillsTaken?: number;
      status?: 'taken' | 'skipped' | 'late' | 'early';
      notes?: string;
    }) => {
      if (!userId) {
        throw new Error('User ID is required');
      }

      const takenAt = params.takenAt || new Date();
      const intakeDate = takenAt.toISOString().split('T')[0];
      const intakeTime = takenAt.toTimeString().split(' ')[0].substring(0, 5);

      const { data, error } = await supabase
        .from('medication_intake_history')
        .insert({
          user_id: userId,
          medication_id: params.medicationId,
          taken_at: takenAt.toISOString(),
          intake_date: intakeDate,
          intake_time: intakeTime,
          scheduled_time: params.scheduledTime,
          pills_taken: params.pillsTaken || 1,
          status: params.status || 'taken',
          notes: params.notes,
          was_on_time: params.scheduledTime 
            ? Math.abs(parseTime(intakeTime) - parseTime(params.scheduledTime)) <= 60 // 1h de marge
            : true,
        })
        .select()
        .single();

      if (error) {
        console.error('[useRecordMedicationIntake] ❌ Error recording intake:', error);
        throw error;
      }

      console.log('[useRecordMedicationIntake] ✅ Intake recorded:', data);
      return data;
    },
    onSuccess: () => {
      // Invalider le cache pour rafraîchir l'historique
      queryClient.invalidateQueries({ queryKey: ['medication', 'history'] });
    },
  });
}

/**
 * Hook pour marquer un médicament comme pris aujourd'hui
 */
export function useMarkAsTaken() {
  const recordIntake = useRecordMedicationIntake();

  return {
    markAsTaken: (medicationId: string, scheduledTime?: string) => {
      return recordIntake.mutateAsync({
        medicationId,
        scheduledTime,
        status: 'taken',
      });
    },
    isLoading: recordIntake.isPending,
    error: recordIntake.error,
  };
}

/**
 * Hook pour mettre à jour une prise d'historique
 */
export function useUpdateMedicationIntake() {
  const queryClient = useQueryClient();
  const { userId } = useAuth();

  return useMutation({
    mutationFn: async (params: {
      intakeId: string;
      takenAt?: Date;
      intakeTime?: string;
      pillsTaken?: number;
      status?: 'taken' | 'skipped' | 'late' | 'early';
      notes?: string;
    }) => {
      if (!userId) {
        throw new Error('User ID is required');
      }

      console.log('[useUpdateMedicationIntake] 🔄 Updating intake:', params.intakeId);

      const { data, error } = await supabase.rpc('update_medication_intake', {
        p_intake_id: params.intakeId,
        p_user_id: userId,
        p_taken_at: params.takenAt?.toISOString(),
        p_intake_time: params.intakeTime,
        p_pills_taken: params.pillsTaken,
        p_status: params.status,
        p_notes: params.notes,
      });

      if (error) {
        console.error('[useUpdateMedicationIntake] ❌ Error:', error);
        throw error;
      }

      console.log('[useUpdateMedicationIntake] ✅ Intake updated successfully');
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['medication', 'history'] });
    },
  });
}

/**
 * Hook pour supprimer une prise d'historique
 */
export function useDeleteMedicationIntake() {
  const queryClient = useQueryClient();
  const { userId } = useAuth();

  return useMutation({
    mutationFn: async (intakeId: string) => {
      if (!userId) {
        throw new Error('User ID is required');
      }

      console.log('[useDeleteMedicationIntake] 🗑️ Deleting intake:', intakeId);

      const { data, error } = await supabase.rpc('delete_medication_intake', {
        p_intake_id: intakeId,
        p_user_id: userId,
      });

      if (error) {
        console.error('[useDeleteMedicationIntake] ❌ Error:', error);
        throw error;
      }

      console.log('[useDeleteMedicationIntake] ✅ Intake deleted successfully');
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['medication', 'history'] });
    },
  });
}

// Helper pour comparer les heures (en minutes depuis minuit)
function parseTime(time: string): number {
  const [hours, minutes] = time.split(':').map(Number);
  return hours * 60 + minutes;
}
