/**
 * JournalScreen - Écran principal du journal alimentaire
 * Orchestration : Utilise useFoodDiary + composants UI
 */

import React, { useState, useEffect, useCallback } from 'react'
import {
  View,
  Text,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  Alert
} from 'react-native'
import { useRouter } from 'expo-router'
import { useAuth } from '@/hooks/useAuth'
import { useFoodDiary } from '@/hooks/useFoodDiary'
import { useNutritionHealthData } from '@/hooks/useNutritionHealthData'
import { useNutritionInsights } from '@/hooks/useNutritionInsights'
import { MealCard, NutritionSummary } from '@/components/foodDiary'
import { NutritionInsightsList } from '@/components/NutritionInsightCard'
import type { FoodDiary as FoodDiaryType, MealType } from '@/types/foodDiary'

export default function JournalScreen() {
  const router = useRouter()
  const { userId } = useAuth()
  const { getDiary, loading, error } = useFoodDiary()
  
  const [diary, setDiary] = useState<FoodDiaryType | null>(null)
  const [selectedDate, setSelectedDate] = useState<Date>(new Date())
  const [refreshing, setRefreshing] = useState(false)

  // Récupérer les données nutrition + santé pour les insights
  const { data: nutritionHealthData, isLoading: insightsLoading } = useNutritionHealthData(userId, selectedDate)
  
  // Calculer les insights nutritionnels
  const nutritionInsights = useNutritionInsights(
    nutritionHealthData?.nutrition,
    nutritionHealthData?.health
  )

  // Charger le journal
  const loadDiary = useCallback(async (forceSync: boolean = false) => {
    try {
      const result = await getDiary(selectedDate, forceSync)
      if (result) {
        setDiary(result)
      }
    } catch (err) {
      console.error('[JournalScreen] Load error:', err)
      Alert.alert('Erreur', 'Impossible de charger le journal')
    }
  }, [selectedDate, getDiary])

  // Initial load
  useEffect(() => {
    loadDiary()
  }, [loadDiary])

  // Pull to refresh
  const onRefresh = useCallback(async () => {
    setRefreshing(true)
    await loadDiary(true) // Force sync FatSecret
    setRefreshing(false)
  }, [loadDiary])

  // Navigation vers recherche
  const handleAddMeal = useCallback((mealType: MealType) => {
    router.push({
      pathname: '/(tabs)/search-food',
      params: { mealType }
    })
  }, [router])

  // Format date
  const formatDate = (date: Date) => {
    return date.toLocaleDateString('fr-FR', {
      weekday: 'long',
      day: 'numeric',
      month: 'long'
    })
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Journal</Text>
        <Text style={styles.headerDate}>{formatDate(selectedDate)}</Text>
      </View>

      {/* Content */}
      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Total Nutrition */}
        {diary && diary.total_nutrition.calories > 0 && (
          <NutritionSummary nutrition={diary.total_nutrition} />
        )}

        {/* Nutrition Insights - Affichage intelligent */}
        {!insightsLoading && nutritionInsights.hasData && (
          <NutritionInsightsList insights={nutritionInsights.insights} />
        )}

        {/* Meals */}
        {diary && (
          <>
            <MealCard
              mealType="breakfast"
              meals={diary.meals.breakfast}
              onAddPress={() => handleAddMeal('breakfast')}
            />
            
            <MealCard
              mealType="lunch"
              meals={diary.meals.lunch}
              onAddPress={() => handleAddMeal('lunch')}
            />
            
            <MealCard
              mealType="dinner"
              meals={diary.meals.dinner}
              onAddPress={() => handleAddMeal('dinner')}
            />
            
            <MealCard
              mealType="snack"
              meals={diary.meals.snack}
              onAddPress={() => handleAddMeal('snack')}
            />
          </>
        )}

        {/* Loading */}
        {loading && !diary && (
          <View style={styles.loadingContainer}>
            <Text style={styles.loadingText}>Chargement...</Text>
          </View>
        )}

        {/* Error */}
        {error && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{error}</Text>
            <TouchableOpacity
              style={styles.retryButton}
              onPress={() => loadDiary()}
            >
              <Text style={styles.retryButtonText}>Réessayer</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Empty state */}
        {!loading && !error && diary && diary.total_nutrition.calories === 0 && (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>🍽️</Text>
            <Text style={styles.emptyTitle}>Aucun repas aujourd'hui</Text>
            <Text style={styles.emptyText}>
              Commencez par ajouter votre premier repas
            </Text>
          </View>
        )}

        {/* Spacer */}
        <View style={{ height: 40 }} />
      </ScrollView>
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
    paddingVertical: 16,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0'
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#000',
    marginBottom: 4
  },
  headerDate: {
    fontSize: 15,
    color: '#666',
    textTransform: 'capitalize'
  },
  content: {
    flex: 1
  },
  loadingContainer: {
    paddingVertical: 40,
    alignItems: 'center'
  },
  loadingText: {
    fontSize: 16,
    color: '#999'
  },
  errorContainer: {
    paddingVertical: 40,
    paddingHorizontal: 20,
    alignItems: 'center'
  },
  errorText: {
    fontSize: 16,
    color: '#FF3B30',
    textAlign: 'center',
    marginBottom: 16
  },
  retryButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: '#007AFF',
    borderRadius: 8
  },
  retryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFF'
  },
  emptyContainer: {
    paddingVertical: 60,
    paddingHorizontal: 40,
    alignItems: 'center'
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: 16
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#000',
    marginBottom: 8
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
    textAlign: 'center'
  }
})
