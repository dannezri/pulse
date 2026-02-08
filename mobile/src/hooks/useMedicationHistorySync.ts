import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import { storage } from '@/lib/storage';

/**
 * Hook pour synchroniser automatiquement l'historique des médicaments
 * Se déclenche à chaque ouverture de l'app
 */
export function useMedicationHistorySync(userId?: string | null) {
  const queryClient = useQueryClient();
  const hasSyncedRef = useRef(false);

  useEffect(() => {
    // Synchroniser une seule fois par session
    if (hasSyncedRef.current) {
      console.log('[useMedicationHistorySync] ⏭️ Already synced this session');
      return;
    }

    const syncHistory = async () => {
      // Utiliser le userId passé en paramètre, sinon fallback sur storage
      const effectiveUserId = userId || storage.userId;

      if (!effectiveUserId) {
        console.log('[useMedicationHistorySync] ⚠️ No user ID, skipping sync');
        return;
      }

      console.log(`[useMedicationHistorySync] 🚀 Triggering sync for user: ${effectiveUserId}`);

      try {
        console.log('[useMedicationHistorySync] 🔄 Starting medication history sync...');
        const startTime = Date.now();

        // Appeler la fonction RPC Supabase pour générer l'historique
        const { data, error } = await supabase.rpc('auto_populate_medication_history', {
          p_user_id: effectiveUserId,
        });

        if (error) {
          console.error('[useMedicationHistorySync] ❌ Sync error:', error);
          throw error;
        }

        const duration = Date.now() - startTime;
        console.log(`[useMedicationHistorySync] ✅ Sync completed in ${duration}ms`);
        console.log(`[useMedicationHistorySync] 📊 Results:`, data);

        // Invalider le cache React Query pour rafraîchir l'historique
        await queryClient.invalidateQueries({ queryKey: ['medication', 'history'] });
        
        // Invalider aussi le cache d'analyse Gemini (car l'historique a changé)
        await queryClient.invalidateQueries({ queryKey: ['medications', 'analysis'] });

        // Marquer comme synchronisé pour cette session
        hasSyncedRef.current = true;

        console.log('[useMedicationHistorySync] 🎉 History synchronized successfully');
        console.log('[useMedicationHistorySync] 🔄 Gemini analysis cache invalidated (will regenerate on next fetch)');
      } catch (error) {
        console.error('[useMedicationHistorySync] ❌ Fatal error during sync:', error);
        // Ne pas bloquer l'app en cas d'erreur
        // L'utilisateur verra simplement l'historique déjà en cache
      }
    };

    // Lancer la synchronisation après un petit délai (pour ne pas ralentir le démarrage)
    const timeoutId = setTimeout(() => {
      syncHistory();
    }, 1000); // 1 seconde de délai

    return () => clearTimeout(timeoutId);
  }, [queryClient, userId]);
}

/**
 * Hook pour forcer une synchronisation manuelle
 * Utile pour un bouton "Rafraîchir" ou pull-to-refresh
 */
export function useManualMedicationSync() {
  const queryClient = useQueryClient();

  const syncHistory = async (): Promise<{ success: boolean; error?: string }> => {
    const userId = storage.userId;

    if (!userId) {
      return { success: false, error: 'No user ID' };
    }

    try {
      console.log('[useManualMedicationSync] 🔄 Manual sync triggered...');
      const startTime = Date.now();

      const { data, error } = await supabase.rpc('auto_populate_medication_history', {
        p_user_id: userId,
      });

      if (error) {
        throw error;
      }

      const duration = Date.now() - startTime;
      console.log(`[useManualMedicationSync] ✅ Sync completed in ${duration}ms`);
      console.log(`[useManualMedicationSync] 📊 Results:`, data);

      // Invalider le cache de l'historique
      await queryClient.invalidateQueries({ queryKey: ['medication', 'history'] });
      
      // Invalider aussi le cache d'analyse Gemini
      await queryClient.invalidateQueries({ queryKey: ['medications', 'analysis'] });

      return { success: true };
    } catch (error: any) {
      console.error('[useManualMedicationSync] ❌ Error:', error);
      return { success: false, error: error.message };
    }
  };

  return { syncHistory };
}
