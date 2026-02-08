/**
 * Types pour le Food Diary MVP
 * Architecture : Supabase (source de vérité) ↔ FatSecret (nutrition)
 */

// =====================================================
// FOOD SEARCH & DETAILS
// =====================================================

export interface Food {
  fs_food_id: number
  name: string
  brand: string | null
  description: string
  type: 'generic' | 'brand'
}

export interface FoodServing {
  serving_id: number
  serving_description: string
  metric_serving_amount?: string
  metric_serving_unit?: string
  calories?: string
  protein?: string
  carbohydrate?: string
  fat?: string
  fiber?: string
}

export interface FoodDetails {
  food_id: number
  name: string
  brand: string | null
  servings: FoodServing[]
  raw: any
}

// =====================================================
// FOOD LOG (REPAS)
// =====================================================

export type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack'

export interface FoodLogItem {
  id?: string
  food_log_id?: string
  name: string
  quantity: number
  unit: string
  fs_food_id?: number
  fs_serving_id?: number
  nutrition?: NutritionData
  raw?: any
  created_at?: string
}

export interface FoodLog {
  id: string
  user_id: string
  logged_at: string
  meal_type: MealType
  source: 'search' | 'manual' | 'photo' | 'import'
  note?: string
  context?: Record<string, any>
  items: FoodLogItem[]
  photos?: FoodPhoto[]
  fs_sync_status: 'pending' | 'synced' | 'error' | 'skipped'
  created_at: string
  updated_at: string
}

export interface NutritionData {
  calories: number
  protein: number
  carbohydrate: number
  fat: number
  fiber?: number
}

// =====================================================
// FOOD DIARY (JOURNAL)
// =====================================================

export interface FoodDiary {
  date: string
  meals: {
    breakfast: FoodLogWithNutrition[]
    lunch: FoodLogWithNutrition[]
    dinner: FoodLogWithNutrition[]
    snack: FoodLogWithNutrition[]
  }
  total_nutrition: NutritionData
  source: 'cache' | 'fatsecret'
}

export interface FoodLogWithNutrition extends FoodLog {
  nutrition: NutritionData
}

// =====================================================
// PHOTO
// =====================================================

export interface FoodPhoto {
  id: string
  food_log_id: string
  user_id: string
  storage_path: string
  storage_bucket: string
  taken_at: string
  file_size_bytes?: number
  mime_type?: string
  analysis?: any
  analysis_status: 'pending' | 'success' | 'failed' | 'skipped'
  confidence?: number
  created_at: string
}

// =====================================================
// API REQUESTS / RESPONSES
// =====================================================

export interface SearchFoodsResponse {
  foods: Food[]
}

export interface CreateFoodLogRequest {
  logged_at: string
  meal_type: MealType
  items: {
    name: string
    fs_food_id?: number
    fs_serving_id?: number
    quantity: number
    unit?: string
    nutrition?: NutritionData
    raw?: any
  }[]
  note?: string
  context?: Record<string, any>
  source?: 'search' | 'manual' | 'photo' | 'import'
}

export interface CreateFoodLogResponse {
  food_log_id: string
  items_count: number
  fs_sync_status: 'pending' | 'synced' | 'error' | 'skipped'
  fs_entry_ids: number[]
}

export interface UploadPhotoResponse {
  photo_id: string
  storage_path: string
  public_url: string
  file_size_bytes: number
  analysis_status: string
  analysis?: any
}

// =====================================================
// UI STATE
// =====================================================

export interface FoodSearchState {
  query: string
  results: Food[]
  loading: boolean
  error: string | null
}

export interface AddMealState {
  meal_type: MealType
  logged_at: Date
  items: FoodLogItem[]
  note: string
  context: Record<string, any>
  submitting: boolean
  error: string | null
}

// =====================================================
// MEAL LABELS (i18n-ready)
// =====================================================

export const MEAL_LABELS: Record<MealType, string> = {
  breakfast: 'Petit-déjeuner',
  lunch: 'Déjeuner',
  dinner: 'Dîner',
  snack: 'Snack'
}

export const MEAL_ICONS: Record<MealType, string> = {
  breakfast: '🌅',
  lunch: '🌞',
  dinner: '🌙',
  snack: '🍪'
}

// =====================================================
// HELPERS
// =====================================================

/**
 * Formate les macros pour affichage
 */
export const formatNutrition = (nutrition: NutritionData): string => {
  return `${Math.round(nutrition.calories)} kcal • P: ${nutrition.protein.toFixed(1)}g • C: ${nutrition.carbohydrate.toFixed(1)}g • F: ${nutrition.fat.toFixed(1)}g`
}

/**
 * Formate une date pour l'API (ISO 8601)
 */
export const formatDateForAPI = (date: Date): string => {
  return date.toISOString()
}

/**
 * Formate une date pour affichage (format local)
 */
export const formatDateForDisplay = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('fr-FR', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

/**
 * Calcule la nutrition totale d'une liste d'items
 */
export const calculateTotalNutrition = (items: FoodLogItem[]): NutritionData => {
  return items.reduce(
    (total, item) => {
      const nutrition = item.nutrition || { calories: 0, protein: 0, carbohydrate: 0, fat: 0 }
      return {
        calories: total.calories + nutrition.calories,
        protein: total.protein + nutrition.protein,
        carbohydrate: total.carbohydrate + nutrition.carbohydrate,
        fat: total.fat + nutrition.fat,
        fiber: (total.fiber || 0) + (nutrition.fiber || 0)
      }
    },
    { calories: 0, protein: 0, carbohydrate: 0, fat: 0, fiber: 0 }
  )
}
