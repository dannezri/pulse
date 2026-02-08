/**
 * FoodDetailsScreen - Écran des détails d'un aliment
 * Orchestration : Portion picker + ajout au journal
 */

import React, { useState, useCallback, useEffect } from 'react'
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  ActivityIndicator,
  Alert
} from 'react-native'
import { useRouter, useLocalSearchParams } from 'expo-router'
import { Picker } from '@react-native-picker/picker'
import { useFoodDiary } from '@/hooks/useFoodDiary'
import type { FoodDetails, FoodServing, MealType } from '@/types/foodDiary'

export default function FoodDetailsScreen() {
  const router = useRouter()
  const params = useLocalSearchParams<{
    foodId: string
    foodName: string
    mealType: MealType
  }>()
  
  const { getFoodDetails, addSimpleMeal, loading } = useFoodDiary()
  
  const [details, setDetails] = useState<FoodDetails | null>(null)
  const [selectedServing, setSelectedServing] = useState<FoodServing | null>(null)
  const [quantity, setQuantity] = useState(1)
  const [submitting, setSubmitting] = useState(false)

  // Load food details
  useEffect(() => {
    const load = async () => {
      const result = await getFoodDetails(parseInt(params.foodId))
      if (result) {
        setDetails(result)
        if (result.servings.length > 0) {
          setSelectedServing(result.servings[0])
        }
      }
    }
    load()
  }, [params.foodId, getFoodDetails])

  // Add to diary
  const handleAddToDiary = useCallback(async () => {
    if (!selectedServing || !details) return
    
    setSubmitting(true)
    
    try {
      // Calculate nutrition
      const nutrition = {
        calories: parseFloat(selectedServing.calories || '0') * quantity,
        protein: parseFloat(selectedServing.protein || '0') * quantity,
        carbohydrate: parseFloat(selectedServing.carbohydrate || '0') * quantity,
        fat: parseFloat(selectedServing.fat || '0') * quantity
      }
      
      const success = await addSimpleMeal(
        params.mealType,
        parseInt(params.foodId),
        selectedServing.serving_id,
        quantity,
        params.foodName,
        nutrition
      )
      
      if (success) {
        Alert.alert('Succès', 'Repas ajouté au journal', [
          {
            text: 'OK',
            onPress: () => router.push('/(tabs)/journal')
          }
        ])
      } else {
        Alert.alert('Erreur', 'Impossible d\'ajouter le repas')
      }
    } catch (err) {
      Alert.alert('Erreur', 'Une erreur s\'est produite')
    } finally {
      setSubmitting(false)
    }
  }, [selectedServing, details, quantity, params, addSimpleMeal, router])

  // Calculate total nutrition
  const getTotalNutrition = () => {
    if (!selectedServing) return null
    
    return {
      calories: parseFloat(selectedServing.calories || '0') * quantity,
      protein: parseFloat(selectedServing.protein || '0') * quantity,
      carbohydrate: parseFloat(selectedServing.carbohydrate || '0') * quantity,
      fat: parseFloat(selectedServing.fat || '0') * quantity
    }
  }

  const totalNutrition = getTotalNutrition()

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Text style={styles.backButton}>← Retour</Text>
        </TouchableOpacity>
      </View>

      {loading && !details ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
        </View>
      ) : details ? (
        <ScrollView style={styles.content}>
          {/* Food Info */}
          <View style={styles.section}>
            <Text style={styles.foodName}>{details.name}</Text>
            {details.brand && (
              <Text style={styles.foodBrand}>{details.brand}</Text>
            )}
          </View>

          {/* Serving Picker */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Portion</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={selectedServing?.serving_id}
                onValueChange={(value) => {
                  const serving = details.servings.find(s => s.serving_id === value)
                  if (serving) setSelectedServing(serving)
                }}
              >
                {details.servings.map((serving) => (
                  <Picker.Item
                    key={serving.serving_id}
                    label={serving.serving_description}
                    value={serving.serving_id}
                  />
                ))}
              </Picker>
            </View>
          </View>

          {/* Quantity */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Quantité</Text>
            <View style={styles.quantityContainer}>
              <TouchableOpacity
                style={styles.quantityButton}
                onPress={() => setQuantity(Math.max(0.5, quantity - 0.5))}
              >
                <Text style={styles.quantityButtonText}>−</Text>
              </TouchableOpacity>
              
              <Text style={styles.quantityValue}>{quantity.toFixed(1)}</Text>
              
              <TouchableOpacity
                style={styles.quantityButton}
                onPress={() => setQuantity(quantity + 0.5)}
              >
                <Text style={styles.quantityButtonText}>+</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Nutrition */}
          {totalNutrition && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Information nutritionnelle</Text>
              <View style={styles.nutritionCard}>
                <View style={styles.nutritionRow}>
                  <Text style={styles.nutritionLabel}>Calories</Text>
                  <Text style={styles.nutritionValue}>
                    {Math.round(totalNutrition.calories)} kcal
                  </Text>
                </View>
                <View style={styles.nutritionRow}>
                  <Text style={styles.nutritionLabel}>Protéines</Text>
                  <Text style={styles.nutritionValue}>
                    {totalNutrition.protein.toFixed(1)}g
                  </Text>
                </View>
                <View style={styles.nutritionRow}>
                  <Text style={styles.nutritionLabel}>Glucides</Text>
                  <Text style={styles.nutritionValue}>
                    {totalNutrition.carbohydrate.toFixed(1)}g
                  </Text>
                </View>
                <View style={styles.nutritionRow}>
                  <Text style={styles.nutritionLabel}>Lipides</Text>
                  <Text style={styles.nutritionValue}>
                    {totalNutrition.fat.toFixed(1)}g
                  </Text>
                </View>
              </View>
            </View>
          )}

          {/* Spacer */}
          <View style={{ height: 100 }} />
        </ScrollView>
      ) : (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>Impossible de charger les détails</Text>
        </View>
      )}

      {/* Add Button */}
      {details && (
        <View style={styles.footer}>
          <TouchableOpacity
            style={[styles.addButton, submitting && styles.addButtonDisabled]}
            onPress={handleAddToDiary}
            disabled={submitting}
          >
            {submitting ? (
              <ActivityIndicator color="#FFF" />
            ) : (
              <Text style={styles.addButtonText}>Ajouter au journal</Text>
            )}
          </TouchableOpacity>
        </View>
      )}
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F8F8'
  },
  header: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0'
  },
  backButton: {
    fontSize: 16,
    color: '#007AFF'
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center'
  },
  content: {
    flex: 1
  },
  section: {
    backgroundColor: '#FFF',
    marginTop: 16,
    padding: 20
  },
  foodName: {
    fontSize: 24,
    fontWeight: '700',
    color: '#000',
    marginBottom: 4
  },
  foodBrand: {
    fontSize: 16,
    color: '#666'
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 12
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#E0E0E0',
    borderRadius: 8,
    overflow: 'hidden'
  },
  quantityContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center'
  },
  quantityButton: {
    width: 60,
    height: 60,
    backgroundColor: '#007AFF',
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center'
  },
  quantityButtonText: {
    fontSize: 32,
    fontWeight: '300',
    color: '#FFF'
  },
  quantityValue: {
    fontSize: 32,
    fontWeight: '600',
    color: '#000',
    marginHorizontal: 40
  },
  nutritionCard: {
    backgroundColor: '#F8F8F8',
    borderRadius: 12,
    padding: 16
  },
  nutritionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0'
  },
  nutritionLabel: {
    fontSize: 16,
    color: '#666'
  },
  nutritionValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000'
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center'
  },
  errorText: {
    fontSize: 16,
    color: '#999'
  },
  footer: {
    padding: 20,
    backgroundColor: '#FFF',
    borderTopWidth: 1,
    borderTopColor: '#F0F0F0'
  },
  addButton: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center'
  },
  addButtonDisabled: {
    opacity: 0.5
  },
  addButtonText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFF'
  }
})
