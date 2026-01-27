/**
 * Hook pour gérer les médicaments
 * Stockage local avec SecureStore + synchronisation backend
 */

import { useState, useEffect } from 'react';
import * as SecureStore from 'expo-secure-store';

export interface Medication {
  id: string;
  name: string;
  dosage?: string;
  unit?: string;
  frequency?: string;
  notes?: string;
  takenAt: string; // ISO 8601
  createdAt: string;
}

const STORAGE_KEY = 'pulse_medications';

export function useMedications() {
  const [medications, setMedications] = useState<Medication[]>([]);
  const [loading, setLoading] = useState(true);

  // Charger les médicaments depuis AsyncStorage
  useEffect(() => {
    loadMedications();
  }, []);

  const loadMedications = async () => {
    try {
      const stored = await SecureStore.getItemAsync(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        // Trier par date de prise (plus récent en premier)
        const sorted = parsed.sort((a: Medication, b: Medication) => 
          new Date(b.takenAt).getTime() - new Date(a.takenAt).getTime()
        );
        setMedications(sorted);
      }
    } catch (error) {
      console.error('[useMedications] Erreur chargement:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveMedications = async (meds: Medication[]) => {
    try {
      await SecureStore.setItemAsync(STORAGE_KEY, JSON.stringify(meds));
      setMedications(meds);
    } catch (error) {
      console.error('[useMedications] Erreur sauvegarde:', error);
      throw error;
    }
  };

  const addMedication = async (medication: Omit<Medication, 'id' | 'createdAt'>) => {
    const newMed: Medication = {
      ...medication,
      id: `med_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      createdAt: new Date().toISOString(),
    };

    const updated = [newMed, ...medications];
    await saveMedications(updated);
    return newMed;
  };

  const updateMedication = async (id: string, updates: Partial<Medication>) => {
    const updated = medications.map(med => 
      med.id === id ? { ...med, ...updates } : med
    );
    await saveMedications(updated);
  };

  const deleteMedication = async (id: string) => {
    const updated = medications.filter(med => med.id !== id);
    await saveMedications(updated);
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
    addMedication,
    updateMedication,
    deleteMedication,
    getMedicationsInRange,
    getTodayMedications,
    reload: loadMedications,
  };
}
