/**
 * HealthScanner - Service pour scanner et synchroniser les données de contexte depuis Apple Health
 * 
 * Rôle: Récupère les données de contexte (Nutrition, Médicaments, Symptômes, Selles) des 6 dernières heures
 * depuis HealthKit et les envoie au backend dans la table daily_context
 */

import { Platform, Alert } from 'react-native';
import * as Device from 'expo-device';
import * as HealthKit from '@/src/modules/pulseHealthkit';
import { supabase } from '@/src/lib/supabase';
import { storage } from '@/src/lib/storage';
import * as SecureStore from 'expo-secure-store';
import type { Medication } from '../hooks/useMedications';

/**
 * Vérifie si on est sur un simulateur
 */
function isSimulator(): boolean {
  return !Device.isDevice;
}

/**
 * Charge les médicaments saisis manuellement dans la période donnée
 */
async function loadManualMedications(fromISO: string, toISO: string): Promise<Medication[]> {
  try {
    const STORAGE_KEY = '@pulse_medications';
    const stored = await SecureStore.getItemAsync(STORAGE_KEY);
    
    if (!stored) {
      return [];
    }
    
    const allMedications: Medication[] = JSON.parse(stored);
    const from = new Date(fromISO).getTime();
    const to = new Date(toISO).getTime();
    
    // Filtrer par période
    return allMedications.filter(med => {
      const takenTime = new Date(med.takenAt).getTime();
      return takenTime >= from && takenTime <= to;
    });
  } catch (error) {
    console.error('[HealthScanner] Erreur chargement médicaments manuels:', error);
    return [];
  }
}

/**
 * Interface pour une entrée de contexte
 */
export interface ContextEntry {
  category: 'nutrition' | 'medication' | 'symptoms' | 'stool';
  details: Record<string, any>;
  logged_at: string;  // ISO 8601
}

/**
 * Résultat de la synchronisation
 */
export interface SyncResult {
  success: boolean;
  message: string;
  entriesCount: number;
}

/**
 * Scanne et synchronise les données de contexte des 6 dernières heures
 * 
 * @returns Promise<SyncResult> Résultat de la synchronisation
 */
export async function syncLast6Hours(): Promise<SyncResult> {
  console.log('[HealthScanner] ========== DÉBUT DE LA SYNCHRONISATION ==========');
  
  // Vérifier la plateforme
  if (Platform.OS !== 'ios') {
    console.log('[HealthScanner] ❌ Plateforme non supportée:', Platform.OS);
    return {
      success: false,
      message: 'HealthKit est disponible uniquement sur iOS',
      entriesCount: 0
    };
  }
  
  console.log('[HealthScanner] ✅ Plateforme: iOS');
  
  // Vérifier si on est sur un simulateur
  if (isSimulator()) {
    console.log('[HealthScanner] ❌ Simulateur détecté');
    Alert.alert(
      'Simulateur détecté',
      'Apple Health/HealthKit est indisponible sur simulateur. Lance l\'app sur un iPhone réel.',
      [{ text: 'OK' }]
    );
    return {
      success: false,
      message: 'HealthKit indisponible sur simulateur',
      entriesCount: 0
    };
  }
  
  console.log('[HealthScanner] ✅ Device physique détecté');
  
  try {
    // Vérifier la disponibilité
    console.log('[HealthScanner] Vérification de la disponibilité HealthKit...');
    const available = await HealthKit.isAvailable();
    console.log('[HealthScanner] HealthKit disponible:', available);
    
    if (!available) {
      console.log('[HealthScanner] ❌ HealthKit non disponible');
      return {
        success: false,
        message: 'HealthKit n\'est pas disponible sur cet appareil',
        entriesCount: 0
      };
    }
    
    // Demander les autorisations
    console.log('[HealthScanner] Demande d\'autorisation HealthKit...');
    const authorized = await HealthKit.requestAuthorization();
    console.log('[HealthScanner] Autorisation accordée:', authorized);
    
    if (!authorized) {
      console.log('[HealthScanner] ❌ Autorisation refusée');
      Alert.alert(
        'Autorisation requise',
        'Les permissions HealthKit sont nécessaires pour synchroniser vos données de contexte.',
        [{ text: 'OK' }]
      );
      return {
        success: false,
        message: 'Autorisation HealthKit refusée',
        entriesCount: 0
      };
    }
    
    console.log('[HealthScanner] ✅ Autorisations OK, lecture des données...');
    
    // Calculer la période (6 dernières heures)
    const now = new Date();
    const sixHoursAgo = new Date(now.getTime() - 6 * 60 * 60 * 1000);
    const fromISO = sixHoursAgo.toISOString();
    const toISO = now.toISOString();
    
    // Lire les données en parallèle
    console.log('[HealthScanner] Lecture des données de contexte de', sixHoursAgo.toLocaleString(), 'à', now.toLocaleString());
    const [nutrition, medications, symptoms, stool] = await Promise.all([
      HealthKit.readNutrition(fromISO, toISO).catch(() => []),
      HealthKit.readMedications(fromISO, toISO).catch(() => []),
      HealthKit.readSymptoms(fromISO, toISO).catch(() => []),
      HealthKit.readStool(fromISO, toISO).catch(() => [])
    ]);
    
    console.log('[HealthScanner] Données récupérées de HealthKit:', {
      nutrition: nutrition.length,
      medications: medications.length,
      symptoms: symptoms.length,
      stool: stool.length
    });
    
    // Charger les médicaments saisis manuellement
    const manualMedications = await loadManualMedications(fromISO, toISO);
    console.log('[HealthScanner] Médicaments saisis manuellement:', manualMedications.length);
    
    // Transformer en entrées de contexte
    const entries: ContextEntry[] = [];
    
    // Nutrition
    if (nutrition && nutrition.length > 0) {
      // Grouper par date/heure
      const nutritionByTime = new Map<string, { calories?: number; carbs?: number }>();
      
      for (const item of nutrition) {
        const loggedAt = item.logged_at;
        if (!nutritionByTime.has(loggedAt)) {
          nutritionByTime.set(loggedAt, {});
        }
        const entry = nutritionByTime.get(loggedAt)!;
        if (item.type === 'calories') {
          entry.calories = item.value;
        } else if (item.type === 'carbs') {
          entry.carbs = item.value;
        }
      }
      
      // Créer les entrées
      for (const [loggedAt, details] of nutritionByTime.entries()) {
        entries.push({
          category: 'nutrition',
          details,
          logged_at: loggedAt
        });
      }
    }
    
    // Médicaments HealthKit
    if (medications && medications.length > 0) {
      console.log('[HealthScanner] 💊 Traitement des médicaments HealthKit:', medications.length);
      for (const med of medications) {
        const details: Record<string, any> = {
          name: med.name || 'Médicament inconnu',
          source: 'HealthKit'
        };
        
        // Ajouter les métadonnées si disponibles
        if (med.metadata) {
          details.metadata = med.metadata;
        }
        
        entries.push({
          category: 'medication',
          details,
          logged_at: med.logged_at
        });
      }
    }
    
    // Médicaments saisis manuellement dans Pulse
    if (manualMedications.length > 0) {
      console.log('[HealthScanner] 💊 Traitement des médicaments manuels:', manualMedications.length);
      for (const med of manualMedications) {
        const details: Record<string, any> = {
          name: med.name,
          source: 'Manual'
        };
        
        if (med.dosage) details.dosage = med.dosage;
        if (med.unit) details.unit = med.unit;
        if (med.frequency) details.frequency = med.frequency;
        if (med.notes) details.notes = med.notes;
        
        entries.push({
          category: 'medication',
          details,
          logged_at: med.takenAt
        });
      }
    }
    
    // Symptômes
    if (symptoms && symptoms.length > 0) {
      for (const symptom of symptoms) {
        entries.push({
          category: 'symptoms',
          details: { value: symptom.value },
          logged_at: symptom.logged_at
        });
      }
    }
    
    // Selles
    if (stool && stool.length > 0) {
      for (const stoolItem of stool) {
        entries.push({
          category: 'stool',
          details: { value: stoolItem.value },
          logged_at: stoolItem.logged_at
        });
      }
    }
    
    // Envoyer au backend
    console.log('[HealthScanner] Total d\'entrées à synchroniser:', entries.length);
    
    const userId = await storage.getUserId();
    console.log('[HealthScanner] User ID:', userId ? 'OK' : 'MANQUANT');
    
    if (!userId) {
      console.log('[HealthScanner] ❌ Utilisateur non connecté');
      return {
        success: false,
        message: 'Utilisateur non connecté',
        entriesCount: 0
      };
    }
    
    // Insérer dans daily_context
    if (entries.length > 0) {
      console.log('[HealthScanner] Insertion dans Supabase...');
      const { error } = await supabase
        .from('daily_context')
        .insert(
          entries.map(entry => ({
            user_id: userId,
            category: entry.category,
            details: entry.details,
            logged_at: entry.logged_at,
            source: 'AppleHealth'
          }))
        );
      
      if (error) {
        console.error('[HealthScanner] ❌ Erreur d\'insertion:', error);
        return {
          success: false,
          message: `Erreur lors de l'insertion: ${error.message}`,
          entriesCount: 0
        };
      }
      console.log('[HealthScanner] ✅ Données insérées dans Supabase');
    }
    
    // Afficher un message de succès
    let message = '';
    if (entries.length > 0) {
      const nutritionCount = entries.filter(e => e.category === 'nutrition').length;
      const medicationCount = entries.filter(e => e.category === 'medication').length;
      const parts = [];
      if (nutritionCount > 0) parts.push(`${nutritionCount} nutrition`);
      if (medicationCount > 0) parts.push(`${medicationCount} médicament(s)`);
      message = `Contexte synchronisé: ${parts.join(', ')}. Pulse analyse vos données…`;
    } else {
      message = 'Aucune donnée trouvée dans les 6 dernières heures.\n\nAjoutez des données dans l\'app Santé ou loggez vos médicaments dans l\'onglet 💊 Médicaments.';
    }
    
    console.log('[HealthScanner] ========== SYNCHRONISATION TERMINÉE ==========');
    console.log('[HealthScanner] Message:', message);
    
    Alert.alert('Synchronisation réussie', message, [{ text: 'OK' }]);
    
    return {
      success: true,
      message,
      entriesCount: entries.length
    };
    
  } catch (error: any) {
    console.error('[HealthScanner] Erreur lors de la synchronisation:', error);
    Alert.alert(
      'Erreur de synchronisation',
      error?.message || 'Une erreur est survenue lors de la synchronisation des données HealthKit.',
      [{ text: 'OK' }]
    );
    return {
      success: false,
      message: error?.message || 'Erreur inconnue',
      entriesCount: 0
    };
  }
}
