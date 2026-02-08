/**
 * Hook useFoodDiary
 * Logique métier pour le journal alimentaire
 * 
 * Architecture:
 * - Gère les appels API vers le backend Food Diary
 * - Récupère automatiquement le JWT token depuis Supabase Auth
 * - Gère le cache et l'état local
 * - Pas de logique UI (UI pure dans les composants)
 */

import { useState, useCallback, useEffect } from 'react'
import { supabase } from '@/lib/supabase'
import { storage } from '@/lib/storage'
import { API_URL } from '@/config/api'
import type {
  Food,
  FoodDetails,
  FoodDiary,
  CreateFoodLogRequest,
  CreateFoodLogResponse,
  MealType,
  UploadPhotoResponse
} from '@/types/foodDiary'

// =====================================================
// HOOK
// =====================================================

export const useFoodDiary = () => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isReady, setIsReady] = useState(false)

  /**
   * Récupère l'UUID utilisateur depuis le storage local
   * (compatibilité avec le système d'auth custom de l'app)
   */
  const getAuthToken = useCallback(async (): Promise<string> => {
    const userId = await storage.getUserId()
    
    if (!userId) {
      throw new Error('Non authentifié')
    }
    
    return userId
  }, [])

  /**
   * Helper pour faire des requêtes API authentifiées
   */
  const fetchAPI = useCallback(async <T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> => {
    const token = await getAuthToken()
    
    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }
    
    return response.json()
  }, [getAuthToken])

  // =====================================================
  // PROVISIONING PROFIL FATSECRET
  // =====================================================

  /**
   * Créé automatiquement un profil FatSecret si absent
   * (Transparent pour l'utilisateur, appelé automatiquement)
   */
  const provisionFatSecretProfile = useCallback(async (): Promise<boolean> => {
    try {
      setError(null)
      
      const result = await fetchAPI<{ status: string; fatsecret_profile: string }>(
        '/api/food-diary/provision',
        { method: 'POST' }
      )
      
      return result.fatsecret_profile === 'active'
    } catch (err) {
      console.error('[useFoodDiary] Provisioning error:', err)
      setError(err instanceof Error ? err.message : 'Erreur provisioning')
      return false
    }
  }, [fetchAPI])

  // =====================================================
  // RECHERCHE D'ALIMENTS
  // =====================================================

  /**
   * Recherche d'aliments dans la base FatSecret
   */
  const searchFoods = useCallback(async (
    query: string,
    page: number = 0
  ): Promise<Food[]> => {
    if (!query.trim()) {
      return []
    }
    
    try {
      setLoading(true)
      setError(null)
      
      const result = await fetchAPI<{ foods: Food[] }>(
        `/api/foods/search?q=${encodeURIComponent(query)}&page=${page}`
      )
      
      return result.foods || []
    } catch (err) {
      console.error('[useFoodDiary] Search error:', err)
      setError(err instanceof Error ? err.message : 'Erreur recherche')
      return []
    } finally {
      setLoading(false)
    }
  }, [fetchAPI])

  /**
   * Récupère les détails d'un aliment (servings + nutrition)
   */
  const getFoodDetails = useCallback(async (
    foodId: number
  ): Promise<FoodDetails | null> => {
    try {
      setLoading(true)
      setError(null)
      
      const result = await fetchAPI<FoodDetails>(`/api/foods/${foodId}`)
      
      return result
    } catch (err) {
      console.error('[useFoodDiary] Get food details error:', err)
      setError(err instanceof Error ? err.message : 'Erreur détails aliment')
      return null
    } finally {
      setLoading(false)
    }
  }, [fetchAPI])

  // =====================================================
  // AJOUTER UN REPAS
  // =====================================================

  /**
   * Ajoute un repas au journal
   */
  const addMealLog = useCallback(async (
    request: CreateFoodLogRequest
  ): Promise<CreateFoodLogResponse | null> => {
    try {
      setLoading(true)
      setError(null)
      
      // Ensure provisioning (transparent)
      await provisionFatSecretProfile()
      
      const result = await fetchAPI<CreateFoodLogResponse>(
        '/api/food-logs',
        {
          method: 'POST',
          body: JSON.stringify(request)
        }
      )
      
      return result
    } catch (err) {
      console.error('[useFoodDiary] Add meal error:', err)
      setError(err instanceof Error ? err.message : 'Erreur ajout repas')
      return null
    } finally {
      setLoading(false)
    }
  }, [fetchAPI, provisionFatSecretProfile])

  /**
   * Helper: Ajoute un repas simple (1 item)
   */
  const addSimpleMeal = useCallback(async (
    mealType: MealType,
    foodId: number,
    servingId: number,
    quantity: number,
    foodName: string,
    nutrition: { calories: number; protein: number; carbohydrate: number; fat: number }
  ): Promise<boolean> => {
    const result = await addMealLog({
      logged_at: new Date().toISOString(),
      meal_type: mealType,
      items: [
        {
          name: foodName,
          fs_food_id: foodId,
          fs_serving_id: servingId,
          quantity,
          unit: 'serving',
          nutrition
        }
      ],
      source: 'search'
    })
    
    return result !== null
  }, [addMealLog])

  // =====================================================
  // CONSULTER LE JOURNAL
  // =====================================================

  /**
   * Récupère le journal alimentaire d'une date
   */
  const getDiary = useCallback(async (
    date: Date | string,
    forceSync: boolean = false
  ): Promise<FoodDiary | null> => {
    try {
      setLoading(true)
      setError(null)
      
      // Gérer string (YYYY-MM-DD) ou Date
      const dateStr = typeof date === 'string' 
        ? date 
        : date.toISOString().split('T')[0]
      
      const result = await fetchAPI<FoodDiary>(
        `/api/food-diary?date_str=${dateStr}&force_sync=${forceSync}`
      )
      
      return result
    } catch (err) {
      console.error('[useFoodDiary] Get diary error:', err)
      setError(err instanceof Error ? err.message : 'Erreur récupération journal')
      return null
    } finally {
      setLoading(false)
    }
  }, [fetchAPI])

  /**
   * Récupère le journal du jour
   */
  const getTodayDiary = useCallback(async (): Promise<FoodDiary | null> => {
    return getDiary(new Date())
  }, [getDiary])

  // =====================================================
  // UPLOAD PHOTO
  // =====================================================

  /**
   * Upload une photo de repas
   */
  const uploadPhoto = useCallback(async (
    foodLogId: string,
    uri: string,
    mimeType: string = 'image/jpeg',
    analyze: boolean = false
  ): Promise<UploadPhotoResponse | null> => {
    try {
      setLoading(true)
      setError(null)
      
      const token = await getAuthToken()
      
      // Créer FormData
      const formData = new FormData()
      
      // Extraire filename depuis URI
      const filename = uri.split('/').pop() || 'photo.jpg'
      
      // Ajouter le fichier
      formData.append('file', {
        uri,
        name: filename,
        type: mimeType
      } as any)
      
      // Ajouter analyze flag
      formData.append('analyze', analyze.toString())
      
      const response = await fetch(
        `${API_URL}/api/food-logs/${foodLogId}/photo`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
            // Ne pas définir Content-Type, laisse le navigateur gérer multipart/form-data
          },
          body: formData
        }
      )
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }
      
      return response.json()
    } catch (err) {
      console.error('[useFoodDiary] Upload photo error:', err)
      setError(err instanceof Error ? err.message : 'Erreur upload photo')
      return null
    } finally {
      setLoading(false)
    }
  }, [getAuthToken])

  // =====================================================
  // RETURN
  // =====================================================

  return {
    // State
    loading,
    error,
    
    // Provisioning
    provisionFatSecretProfile,
    
    // Search
    searchFoods,
    getFoodDetails,
    
    // Add meal
    addMealLog,
    addSimpleMeal,
    
    // Diary
    getDiary,
    getTodayDiary,
    
    // Photo
    uploadPhoto,
    
    // Helpers
    clearError: () => setError(null)
  }
}

// =====================================================
// EXPORT DEFAULT
// =====================================================

export default useFoodDiary
