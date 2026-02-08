/**
 * Hook pour gérer les médicaments
 * Stratégie offline-first : stockage local + synchronisation Supabase
 */

import { useState, useEffect } from 'react';
import * as SecureStore from 'expo-secure-store';
import { supabase } from '../lib/supabase';
import { storage } from '../lib/storage';
import { enrichMedication } from '../services/MedicationEnrichment';

export interface Medication {
  id: string;
  name: string;
  dosage?: string;
  unit?: string;
  pillsPerIntake?: number; // Nombre de comprimés par prise (peut être 0.5, 1, 1.5, 2...)
  frequency?: string; // Texte descriptif (rétro-compatibilité)
  intakeTimes?: string[]; // Heures de prise dans la journée (format "HH:mm")
  dailyFrequency?: number; // Nombre de prises par jour (1-6)
  isRecurring?: boolean; // true = traitement récurrent, false = prise ponctuelle
  notes?: string;
  takenAt: string; // ISO 8601
  createdAt: string;
  updatedAt?: string; // Pour la synchronisation
  syncedAt?: string; // Dernière synchro réussie
  endDate?: string; // Date de fin du traitement (ISO 8601)
  isActive?: boolean; // true = actif, false = terminé
  // Enrichissement automatique
  atcCode?: string; // Code ATC (ex: N06AB06)
  activeSubstance?: string; // Substance active (DCI)
  laboratory?: string; // Laboratoire
  form?: string; // Forme pharmaceutique
  enrichmentSource?: 'local_cache' | 'bdpm_api' | 'gpt4o' | 'manual'; // Source de l'enrichissement
}

const STORAGE_KEY_PREFIX = 'pulse_medications_';

// Options de sécurité pour le Keychain iOS
const KEYCHAIN_OPTIONS: SecureStore.SecureStoreOptions = {
  keychainAccessible: SecureStore.AFTER_FIRST_UNLOCK_THIS_DEVICE_ONLY,
};

// Générer la clé de stockage spécifique à l'utilisateur
const getStorageKey = (userId: string | null): string => {
  if (!userId) return `${STORAGE_KEY_PREFIX}anonymous`;
  return `${STORAGE_KEY_PREFIX}${userId}`;
};

export function useMedications() {
  const [medications, setMedications] = useState<Medication[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  // Charger les médicaments (local + Supabase)
  useEffect(() => {
    loadMedications();
  }, []);

  /**
   * Récupérer l'ID utilisateur courant (depuis le stockage local)
   */
  const getCurrentUserId = async (): Promise<string | null> => {
    try {
      const userId = await storage.getUserId();
      return userId;
    } catch (error) {
      console.error('[useMedications] Erreur getUserId:', error);
      return null;
    }
  };

  /**
   * Charger depuis Supabase (table user_medications)
   */
  const loadFromSupabase = async (userId: string): Promise<Medication[]> => {
    try {
      console.log(`[useMedications] 📡 Requête Supabase pour user_id=${userId}`);
      const { data, error } = await supabase
        .from('user_medications')
        .select('*')
        .eq('user_id', userId)
        .eq('is_active', true)
        .order('start_date', { ascending: false });

      if (error) {
        console.error('[useMedications] ❌ Erreur Supabase:', error);
        return [];
      }

      console.log(`[useMedications] 📥 Supabase a retourné ${data?.length || 0} médicaments`);

      // Transformer le format Supabase vers notre format local
      const medications = (data || []).map((item: any) => ({
        id: item.id,
        name: item.medication_name,
        dosage: item.dosage ? String(item.dosage) : undefined,
        unit: item.dosage_unit,
        pillsPerIntake: item.pills_per_intake,
        frequency: undefined, // Calculé à partir de intake_times et daily_frequency
        intakeTimes: Array.isArray(item.intake_times) ? item.intake_times : [],
        dailyFrequency: item.daily_frequency || 1,
        isRecurring: item.is_recurring !== undefined ? item.is_recurring : true, // Par défaut récurrent pour rétro-compatibilité
        notes: item.notes,
        takenAt: item.start_date ? new Date(item.start_date).toISOString() : new Date().toISOString(),
        createdAt: item.created_at,
        updatedAt: item.updated_at,
        syncedAt: new Date().toISOString(),
        endDate: item.end_date ? new Date(item.end_date).toISOString() : undefined,
        isActive: item.is_active !== undefined ? item.is_active : true,
        // Enrichissement
        atcCode: item.atc_code,
        activeSubstance: item.active_substance,
        laboratory: item.laboratory,
        form: item.form,
        enrichmentSource: item.atc_code ? 'local_cache' : undefined,
      }));
      
      if (medications.length > 0) {
        console.log(`[useMedications] 💊 Premiers médicaments:`, medications.slice(0, 2).map(m => m.name));
      }
      
      return medications;
    } catch (error) {
      console.error('[useMedications] Exception Supabase:', error);
      return [];
    }
  };

  /**
   * Charger médicaments (local + merge avec Supabase)
   */
  const loadMedications = async () => {
    try {
      // 1. Récupérer l'userId d'abord
      const userId = await getCurrentUserId();
      const storageKey = getStorageKey(userId);
      
      // 2. Charger depuis le local (cache spécifique à cet utilisateur)
      const stored = await SecureStore.getItemAsync(storageKey, KEYCHAIN_OPTIONS);
      let localMeds: Medication[] = [];
      
      if (stored) {
        try {
          localMeds = JSON.parse(stored);
          console.log(`[useMedications] 📦 ${localMeds.length} médicaments en cache local pour userId=${userId}`);
        } catch (e) {
          console.warn('[useMedications] Cache local corrompu, ignoré');
        }
      } else {
        console.log(`[useMedications] 📦 Aucun cache local pour userId=${userId}`);
      }

      // Afficher immédiatement les données locales
      const sorted = localMeds.sort((a: Medication, b: Medication) => 
        new Date(b.takenAt).getTime() - new Date(a.takenAt).getTime()
      );
      setMedications(sorted);
      setLoading(false);

      // 3. Synchroniser avec Supabase en arrière-plan
      if (userId) {
        console.log('[useMedications] 🔄 Synchronisation avec Supabase...');
        const supabaseMeds = await loadFromSupabase(userId);
        
        // Merger : Supabase écrase toujours le local (source de vérité)
        const mergedMeds = mergeMedications(localMeds, supabaseMeds);
        
        // Toujours mettre à jour si Supabase a des données
        if (supabaseMeds.length > 0) {
          console.log(`[useMedications] ✅ Sync: ${supabaseMeds.length} médicaments depuis Supabase`);
          console.log(`[useMedications] 💊 Premiers médicaments: ${JSON.stringify(supabaseMeds.slice(0, 2).map(m => m.name))}`);
          await SecureStore.setItemAsync(storageKey, JSON.stringify(mergedMeds), KEYCHAIN_OPTIONS);
          
          const sortedMerged = mergedMeds.sort((a, b) => 
            new Date(b.takenAt).getTime() - new Date(a.takenAt).getTime()
          );
          setMedications(sortedMerged);
        }
      }
    } catch (error) {
      console.error('[useMedications] Erreur chargement:', error);
      setLoading(false);
    }
  };

  /**
   * Merger les médicaments locaux et Supabase
   * RÈGLE : Supabase est la source de vérité et écrase le local
   */
  const mergeMedications = (local: Medication[], remote: Medication[]): Medication[] => {
    // Si Supabase a des données, elles écrasent le local
    if (remote.length > 0) {
      console.log(`[useMedications] 🔄 Supabase écrase le cache local (${remote.length} médicaments)`);
      return remote;
    }
    
    // Sinon, garder le local (mode offline)
    console.log(`[useMedications] 📦 Pas de données Supabase, conservation du cache local`);
    return local;
  };

  const saveMedications = async (meds: Medication[]) => {
    try {
      const userId = await getCurrentUserId();
      const storageKey = getStorageKey(userId);
      await SecureStore.setItemAsync(storageKey, JSON.stringify(meds), KEYCHAIN_OPTIONS);
      setMedications(meds);
    } catch (error) {
      console.error('[useMedications] Erreur sauvegarde:', error);
      throw error;
    }
  };

  /**
   * Synchroniser un médicament vers Supabase (table user_medications)
   */
  const syncToSupabase = async (medication: Medication, operation: 'insert' | 'update' | 'delete') => {
    try {
      const userId = await getCurrentUserId();
      if (!userId) {
        console.warn('[useMedications] Pas d\'utilisateur connecté, sync ignorée');
        return;
      }

      setSyncing(true);

      if (operation === 'delete') {
        // Soft delete : mettre is_active à false
        const { error } = await supabase
          .from('user_medications')
          .update({ is_active: false, updated_at: new Date().toISOString() })
          .eq('id', medication.id)
          .eq('user_id', userId);

        if (error) {
          console.error('[useMedications] Erreur delete Supabase:', error);
        } else {
          console.log('[useMedications] ✅ Médicament supprimé de Supabase');
        }
        return;
      }

      // Convertir takenAt (ISO timestamp) en start_date (date only)
      const startDate = medication.takenAt ? new Date(medication.takenAt).toISOString().split('T')[0] : new Date().toISOString().split('T')[0];

      // Format pour Supabase (snake_case et noms de colonnes corrects)
      const supabaseData = {
        id: medication.id,
        user_id: userId,
        medication_name: medication.name,
        dosage: medication.dosage ? parseFloat(medication.dosage) : null,
        dosage_unit: medication.unit,
        pills_per_intake: medication.pillsPerIntake || 1,
        intake_times: medication.intakeTimes || [],
        daily_frequency: medication.dailyFrequency || 1,
        is_recurring: medication.isRecurring !== undefined ? medication.isRecurring : true, // Par défaut récurrent pour rétro-compatibilité
        notes: medication.notes,
        start_date: startDate,
        is_active: true,
        created_at: medication.createdAt,
        updated_at: new Date().toISOString(),
        // Enrichissement automatique
        atc_code: medication.atcCode,
        active_substance: medication.activeSubstance,
        laboratory: medication.laboratory,
        form: medication.form,
      };

      if (operation === 'insert') {
        const { error } = await supabase
          .from('user_medications')
          .insert(supabaseData);

        if (error) {
          console.error('[useMedications] Erreur insert Supabase:', error);
        } else {
          console.log('[useMedications] ✅ Médicament ajouté à Supabase');
        }
      } else if (operation === 'update') {
        const { error } = await supabase
          .from('user_medications')
          .update(supabaseData)
          .eq('id', medication.id)
          .eq('user_id', userId);

        if (error) {
          console.error('[useMedications] Erreur update Supabase:', error);
        } else {
          console.log('[useMedications] ✅ Médicament mis à jour dans Supabase');
        }
      }
    } catch (error) {
      console.error('[useMedications] Exception sync Supabase:', error);
    } finally {
      setSyncing(false);
    }
  };

  const addMedication = async (medication: Omit<Medication, 'id' | 'createdAt'>) => {
    // Générer un UUID v4 compatible Supabase
    const uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });

    const newMed: Medication = {
      ...medication,
      id: uuid,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    // 1. Sauvegarder localement d'abord (rapide - expérience utilisateur)
    const updated = [newMed, ...medications];
    await saveMedications(updated);

    // 2. Enrichissement automatique en arrière-plan (non-bloquant)
    enrichMedication(medication.name, medication.dosage, medication.unit)
      .then(enrichmentResult => {
        if (enrichmentResult.success) {
          console.log('[useMedications] ✅ Enrichissement réussi:', enrichmentResult);
          
          // Mettre à jour le médicament avec les données enrichies
          const enrichedMed: Medication = {
            ...newMed,
            atcCode: enrichmentResult.atc_code,
            activeSubstance: enrichmentResult.active_substance,
            laboratory: enrichmentResult.laboratory,
            form: enrichmentResult.form,
            enrichmentSource: enrichmentResult.source,
            updatedAt: new Date().toISOString(),
          };

          // Mettre à jour localement
          const updatedWithEnrichment = medications.map(m => 
            m.id === uuid ? enrichedMed : m
          );
          if (updatedWithEnrichment.find(m => m.id === uuid)) {
            saveMedications(updatedWithEnrichment);
          } else {
            // Le médicament vient d'être ajouté, mettre à jour la liste
            const enrichedList = [enrichedMed, ...medications.filter(m => m.id !== uuid)];
            saveMedications(enrichedList);
          }

          // Synchroniser avec Supabase (avec enrichissement)
          syncToSupabase(enrichedMed, 'insert').catch(err => {
            console.error('[useMedications] Sync enrichie échouée:', err);
          });
        } else {
          console.warn('[useMedications] ⚠️ Enrichissement échoué, sync sans ATC');
          
          // Synchroniser quand même sans enrichissement
          syncToSupabase(newMed, 'insert').catch(err => {
            console.error('[useMedications] Sync en arrière-plan échouée:', err);
          });
        }
      })
      .catch(err => {
        console.error('[useMedications] Erreur enrichissement:', err);
        
        // Fallback : sync sans enrichissement
        syncToSupabase(newMed, 'insert').catch(syncErr => {
          console.error('[useMedications] Sync fallback échouée:', syncErr);
        });
      });

    return newMed;
  };

  const updateMedication = async (id: string, updates: Partial<Medication>) => {
    // 1. Mettre à jour localement d'abord
    const updatedMeds = medications.map(med => 
      med.id === id ? { 
        ...med, 
        ...updates,
        updatedAt: new Date().toISOString() 
      } : med
    );
    await saveMedications(updatedMeds);

    // 2. Synchroniser avec Supabase en arrière-plan
    const updatedMed = updatedMeds.find(m => m.id === id);
    if (updatedMed) {
      syncToSupabase(updatedMed, 'update').catch(err => {
        console.error('[useMedications] Sync update échouée:', err);
      });
    }
  };

  const deleteMedication = async (id: string) => {
    // Trouver le médicament avant de le supprimer (pour Supabase)
    const medToDelete = medications.find(med => med.id === id);

    // 1. Supprimer localement d'abord
    const updated = medications.filter(med => med.id !== id);
    await saveMedications(updated);

    // 2. Synchroniser avec Supabase en arrière-plan
    if (medToDelete) {
      syncToSupabase(medToDelete, 'delete').catch(err => {
        console.error('[useMedications] Sync delete échouée:', err);
      });
    }
  };

  // Récupérer les médicaments dans une plage de dates (pour sync)
  const getMedicationsInRange = (fromISO: string, toISO: string): Medication[] => {
    const from = new Date(fromISO).getTime();
    const to = new Date(toISO).getTime();
    
    return medications.filter(med => {
      const takenTime = new Date(med.takenAt).getTime();
      return takenTime >= from && takenTime <= to;
    });
  };

  // Récupérer les médicaments du jour
  const getTodayMedications = (): Medication[] => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    return getMedicationsInRange(today.toISOString(), tomorrow.toISOString());
  };

  return {
    medications,
    loading,
    syncing,
    addMedication,
    updateMedication,
    deleteMedication,
    getMedicationsInRange,
    getTodayMedications,
    reload: loadMedications,
  };
}
