/**
 * Food Diary Screen - Écran unifié pour le journal alimentaire
 * Intègre : Journal + Recherche + Détails en une seule navigation
 */

import { useState, useEffect } from 'react'
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
  SafeAreaView,
  StyleSheet,
} from 'react-native'
import { Search, Plus, Calendar, ChevronLeft } from 'lucide-react-native'
import { useFoodDiary } from '@/hooks/useFoodDiary'
import { MealCard, SearchBar, FoodItem, NutritionSummary } from '@/components/foodDiary'
import type { FoodDiary, Food, FoodDetails, MealType } from '@/types/foodDiary'

type ViewMode = 'journal' | 'search' | 'details'

export default function FoodDiaryScreen() {
  // État de navigation
  const [viewMode, setViewMode] = useState<ViewMode>('journal')
  const [selectedFood, setSelectedFood] = useState<Food | null>(null)
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0])
  
  // État de recherche
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<Food[]>([])
  
  // État des détails
  const [foodDetails, setFoodDetails] = useState<FoodDetails | null>(null)
  const [selectedServing, setSelectedServing] = useState(0)
  const [quantity, setQuantity] = useState('1')
  const [selectedMeal, setSelectedMeal] = useState<MealType>('lunch')
  
  // Hook Food Diary
  const {
    loading,
    error,
    searchFoods,
    getFoodDetails,
    addMealLog,
    getDiary,
  } = useFoodDiary()
  
  // État du journal
  const [diary, setDiary] = useState<FoodDiary | null>(null)

  // =====================================================
  // CHARGEMENT DU JOURNAL
  // =====================================================
  
  useEffect(() => {
    if (viewMode === 'journal') {
      loadDiary()
    }
  }, [selectedDate, viewMode])

  const loadDiary = async () => {
    const diaryData = await getDiary(selectedDate)
    setDiary(diaryData)
  }

  // =====================================================
  // RECHERCHE
  // =====================================================

  const handleSearch = async (query: string) => {
    setSearchQuery(query)
    if (query.trim().length < 2) {
      setSearchResults([])
      return
    }
    const results = await searchFoods(query)
    setSearchResults(results)
  }

  const handleFoodSelect = async (food: Food) => {
    setSelectedFood(food)
    setViewMode('details')
    const details = await getFoodDetails(food.fs_food_id)
    setFoodDetails(details)
    if (details?.servings && details.servings.length > 0) {
      setSelectedServing(0)
    }
  }

  // =====================================================
  // AJOUT AU JOURNAL
  // =====================================================

  const handleAddToLog = async () => {
    if (!foodDetails || !selectedFood) return

    const serving = foodDetails.servings[selectedServing]
    const qty = parseFloat(quantity) || 1

    const result = await addMealLog({
      logged_at: new Date().toISOString(),
      meal_type: selectedMeal,
      items: [
        {
          fs_food_id: selectedFood.fs_food_id,
          fs_serving_id: serving.serving_id,
          quantity: qty,
          name: selectedFood.name,
          unit: serving.serving_description,
        },
      ],
      source: 'search',
    })

    if (result) {
      Alert.alert('✅ Ajouté', `${selectedFood.name} ajouté à votre ${selectedMeal}`)
      // Retour au journal
      setViewMode('journal')
      setSelectedFood(null)
      setFoodDetails(null)
      loadDiary()
    }
  }

  // =====================================================
  // NAVIGATION
  // =====================================================

  const handleBack = () => {
    if (viewMode === 'details') {
      setViewMode('search')
      setFoodDetails(null)
      setSelectedFood(null)
    } else if (viewMode === 'search') {
      setViewMode('journal')
      setSearchQuery('')
      setSearchResults([])
    }
  }

  // =====================================================
  // RENDU CONDITIONNEL PAR MODE
  // =====================================================

  return (
    <SafeAreaView style={styles.container}>
      {/* Header minimaliste */}
      <View style={styles.header}>
        {viewMode !== 'journal' && (
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <ChevronLeft size={24} color="#00FF41" />
          </TouchableOpacity>
        )}
        
        <Text style={styles.headerTitle}>
          {viewMode === 'journal' && 'Nutrition'}
          {viewMode === 'search' && 'Rechercher'}
          {viewMode === 'details' && selectedFood?.name}
        </Text>
        
        {viewMode === 'journal' && (
          <TouchableOpacity
            onPress={() => setViewMode('search')}
            style={styles.addButton}
          >
            <Plus size={24} color="#00FF41" />
          </TouchableOpacity>
        )}
      </View>

      {/* MODE: JOURNAL */}
      {viewMode === 'journal' && (
        <ScrollView style={styles.content}>
          {/* Date */}
          <View style={styles.dateContainer}>
            <Text style={styles.dateText}>
              {new Date(selectedDate).toLocaleDateString('fr-FR', {
                weekday: 'long',
                day: 'numeric',
                month: 'long',
              })}
            </Text>
          </View>

          {/* Résumé nutritionnel */}
          {diary && diary.total_nutrition && (
            <NutritionSummary nutrition={diary.total_nutrition} />
          )}

          {/* Repas */}
          {diary && (
            <View>
              {(['breakfast', 'lunch', 'dinner', 'snack'] as MealType[]).map((mealType) => {
                const meals = diary.meals[mealType]
                return (
                  <MealCard
                    key={mealType}
                    mealType={mealType}
                    meals={meals}
                    onAddPress={() => {
                      setSelectedMeal(mealType)
                      setViewMode('search')
                    }}
                  />
                )
              })}
            </View>
          )}

          {loading && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#00FF41" />
            </View>
          )}
        </ScrollView>
      )}

      {/* MODE: RECHERCHE */}
      {viewMode === 'search' && (
        <View style={styles.searchContainer}>
          {/* Barre de recherche */}
          <View style={styles.searchBarContainer}>
            <SearchBar value={searchQuery} onChangeText={handleSearch} autoFocus />
          </View>

          {/* Résultats */}
          <ScrollView style={styles.content}>
            {loading && (
              <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#00FF41" />
              </View>
            )}
            {searchResults.map((food, index) => (
              <FoodItem
                key={`${food.fs_food_id}-${index}`}
                food={food}
                onPress={() => handleFoodSelect(food)}
              />
            ))}
            {searchQuery.length >= 2 && searchResults.length === 0 && !loading && (
              <Text style={styles.emptyText}>
                Aucun résultat pour "{searchQuery}"
              </Text>
            )}
          </ScrollView>
        </View>
      )}

      {/* MODE: DÉTAILS */}
      {viewMode === 'details' && foodDetails && selectedFood && (
        <ScrollView style={styles.content}>
          {/* Nom de l'aliment */}
          <View style={styles.detailsHeader}>
            <Text style={styles.foodName}>{selectedFood.name}</Text>
            {selectedFood.brand && (
              <Text style={styles.foodBrand}>{selectedFood.brand}</Text>
            )}
          </View>

          {/* Sélection du type de repas */}
          <View style={styles.section}>
            <Text style={styles.sectionLabel}>TYPE DE REPAS</Text>
            <View style={styles.mealTypeContainer}>
              {(['breakfast', 'lunch', 'dinner', 'snack'] as MealType[]).map((meal) => (
                <TouchableOpacity
                  key={meal}
                  onPress={() => setSelectedMeal(meal)}
                  style={[
                    styles.mealTypeButton,
                    selectedMeal === meal && styles.mealTypeButtonActive,
                  ]}
                  activeOpacity={0.8}
                >
                  <Text style={styles.mealTypeIcon}>
                    {{
                      breakfast: '🌅',
                      lunch: '☀️',
                      dinner: '🌙',
                      snack: '🍪',
                    }[meal]}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Sélection de la portion */}
          <View style={styles.section}>
            <Text style={styles.sectionLabel}>PORTION</Text>
            <View style={styles.servingContainer}>
              {foodDetails.servings.map((serving, index) => (
                <TouchableOpacity
                  key={index}
                  onPress={() => setSelectedServing(index)}
                  style={[
                    styles.servingItem,
                    selectedServing === index && styles.servingItemActive,
                  ]}
                  activeOpacity={0.8}
                >
                  <Text style={styles.servingDescription}>
                    {serving.serving_description}
                  </Text>
                  <Text style={styles.servingCalories}>
                    {serving.calories} kcal
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Quantité */}
          <View style={styles.section}>
            <Text style={styles.sectionLabel}>QUANTITÉ</Text>
            <TextInput
              value={quantity}
              onChangeText={setQuantity}
              keyboardType="numeric"
              style={styles.quantityInput}
              placeholder="1"
              placeholderTextColor="#666"
            />
          </View>

          {/* Bouton d'ajout */}
          <TouchableOpacity
            onPress={handleAddToLog}
            disabled={loading}
            style={styles.submitButton}
            activeOpacity={0.8}
          >
            <Text style={styles.submitButtonText}>
              {loading ? 'Ajout en cours...' : 'Ajouter au journal'}
            </Text>
          </TouchableOpacity>

          {error && (
            <Text style={styles.errorText}>{error}</Text>
          )}
        </ScrollView>
      )}
    </SafeAreaView>
  )
}

// =====================================================
// STYLES
// =====================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1C1C1E',
  },
  backButton: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFFFFF',
    flex: 1,
    textAlign: 'center',
  },
  addButton: {
    padding: 4,
  },
  content: {
    flex: 1,
  },
  dateContainer: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    alignItems: 'center',
  },
  dateText: {
    fontSize: 14,
    color: '#8E8E93',
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  loadingContainer: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  searchContainer: {
    flex: 1,
  },
  searchBarContainer: {
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  emptyText: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    paddingVertical: 40,
  },
  detailsHeader: {
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 24,
  },
  foodName: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  foodBrand: {
    fontSize: 16,
    color: '#8E8E93',
    fontWeight: '500',
  },
  section: {
    paddingHorizontal: 20,
    marginBottom: 24,
  },
  sectionLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#8E8E93',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  mealTypeContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  mealTypeButton: {
    flex: 1,
    paddingVertical: 16,
    backgroundColor: '#1C1C1E',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#2C2C2E',
    alignItems: 'center',
  },
  mealTypeButtonActive: {
    backgroundColor: '#00FF41',
    borderColor: '#00FF41',
  },
  mealTypeIcon: {
    fontSize: 24,
  },
  servingContainer: {
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#2C2C2E',
    overflow: 'hidden',
  },
  servingItem: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#2C2C2E',
  },
  servingItemActive: {
    backgroundColor: '#2C2C2E',
  },
  servingDescription: {
    fontSize: 15,
    color: '#FFFFFF',
    fontWeight: '500',
    marginBottom: 4,
  },
  servingCalories: {
    fontSize: 13,
    color: '#8E8E93',
  },
  quantityInput: {
    backgroundColor: '#1C1C1E',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#2C2C2E',
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: '#FFFFFF',
    fontWeight: '600',
  },
  submitButton: {
    marginHorizontal: 20,
    marginBottom: 32,
    paddingVertical: 16,
    backgroundColor: '#00FF41',
    borderRadius: 16,
    alignItems: 'center',
  },
  submitButtonText: {
    fontSize: 17,
    fontWeight: '700',
    color: '#000000',
  },
  errorText: {
    fontSize: 14,
    color: '#FF3B30',
    textAlign: 'center',
    marginTop: 16,
    marginBottom: 32,
  },
})
