import { useState } from 'react';
import { supabase } from '@/lib/supabase';
import { storage } from '@/lib/storage';

export interface EventTrackingResult {
  success: boolean;
  error?: string;
}

export function useEventTracking() {
  const [isLogging, setIsLogging] = useState(false);

  /**
   * Log un événement caféine
   * @param amount_mg Quantité de caféine en mg
   */
  const logCaffeine = async (amount_mg: number): Promise<EventTrackingResult> => {
    if (isLogging) return { success: false, error: 'Déjà en cours' };
    
    setIsLogging(true);
    try {
      const userId = await storage.getUserId();
      if (!userId) {
        return { success: false, error: 'Utilisateur non connecté' };
      }

      const { error } = await supabase
        .from('daily_context')
        .insert({
          user_id: userId,
          category: 'caffeine',
          details: { amount_mg, time: new Date().toISOString() },
          logged_at: new Date().toISOString(),
          source: 'manual'
        });

      if (error) {
        console.error('Error logging caffeine:', error);
        return { success: false, error: error.message };
      }

      return { success: true };
    } catch (error) {
      console.error('Exception logging caffeine:', error);
      return { success: false, error: String(error) };
    } finally {
      setIsLogging(false);
    }
  };

  /**
   * Log un événement alcool
   * @param units Nombre d'unités d'alcool
   * @param type Type d'alcool (vin, bière, etc.)
   */
  const logAlcohol = async (units: number, type: string): Promise<EventTrackingResult> => {
    if (isLogging) return { success: false, error: 'Déjà en cours' };
    
    setIsLogging(true);
    try {
      const userId = await storage.getUserId();
      if (!userId) {
        return { success: false, error: 'Utilisateur non connecté' };
      }

      const { error } = await supabase
        .from('daily_context')
        .insert({
          user_id: userId,
          category: 'alcohol',
          details: { units, type, time: new Date().toISOString() },
          logged_at: new Date().toISOString(),
          source: 'manual'
        });

      if (error) {
        console.error('Error logging alcohol:', error);
        return { success: false, error: error.message };
      }

      return { success: true };
    } catch (error) {
      console.error('Exception logging alcohol:', error);
      return { success: false, error: String(error) };
    } finally {
      setIsLogging(false);
    }
  };

  /**
   * Log un repas
   * @param time Heure du repas
   * @param size Taille du repas ('small', 'medium', 'large')
   */
  const logMeal = async (
    time: Date, 
    size: 'small' | 'medium' | 'large'
  ): Promise<EventTrackingResult> => {
    if (isLogging) return { success: false, error: 'Déjà en cours' };
    
    setIsLogging(true);
    try {
      const userId = await storage.getUserId();
      if (!userId) {
        return { success: false, error: 'Utilisateur non connecté' };
      }

      // Calculer si c'est un repas tardif (< 3h avant le coucher typique 23h)
      const mealHour = time.getHours();
      const late_meal = mealHour >= 20; // Après 20h = tardif

      const { error } = await supabase
        .from('daily_context')
        .insert({
          user_id: userId,
          category: 'meal',
          details: { time: time.toISOString(), size, late_meal },
          logged_at: time.toISOString(),
          source: 'manual'
        });

      if (error) {
        console.error('Error logging meal:', error);
        return { success: false, error: error.message };
      }

      return { success: true };
    } catch (error) {
      console.error('Exception logging meal:', error);
      return { success: false, error: String(error) };
    } finally {
      setIsLogging(false);
    }
  };

  /**
   * Log une session d'exercice
   * @param type Type d'exercice (course, vélo, musculation, etc.)
   * @param duration_minutes Durée en minutes
   * @param intensity Intensité ('light', 'moderate', 'intense')
   * @param calories Calories brûlées (optionnel)
   */
  const logExercise = async (
    type: string,
    duration_minutes: number,
    intensity: 'light' | 'moderate' | 'intense',
    calories?: number
  ): Promise<EventTrackingResult> => {
    if (isLogging) return { success: false, error: 'Déjà en cours' };
    
    setIsLogging(true);
    try {
      const userId = await storage.getUserId();
      if (!userId) {
        return { success: false, error: 'Utilisateur non connecté' };
      }

      const details: Record<string, any> = {
        type,
        duration_minutes,
        intensity,
        time: new Date().toISOString()
      };

      if (calories !== undefined) {
        details.calories = calories;
      }

      const { error } = await supabase
        .from('daily_context')
        .insert({
          user_id: userId,
          category: 'exercise',
          details,
          logged_at: new Date().toISOString(),
          source: 'manual'
        });

      if (error) {
        console.error('Error logging exercise:', error);
        return { success: false, error: error.message };
      }

      return { success: true };
    } catch (error) {
      console.error('Exception logging exercise:', error);
      return { success: false, error: String(error) };
    } finally {
      setIsLogging(false);
    }
  };

  return {
    logCaffeine,
    logAlcohol,
    logMeal,
    logExercise,
    isLogging
  };
}
