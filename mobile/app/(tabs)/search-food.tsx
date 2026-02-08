/**
 * SearchFoodScreen - Écran de recherche d'aliments
 * Orchestration : Recherche + sélection aliment
 */

import React, { useState, useCallback, useEffect } from 'react'
import {
  View,
  FlatList,
  StyleSheet,
  SafeAreaView,
  ActivityIndicator,
  Text,
  TouchableOpacity
} from 'react-native'
import { useRouter, useLocalSearchParams } from 'expo-router'
import { useFoodDiary } from '@/hooks/useFoodDiary'
import { SearchBar, FoodItem } from '@/components/foodDiary'
import type { Food, MealType } from '@/types/foodDiary'

export default function SearchFoodScreen() {
  const router = useRouter()
  const params = useLocalSearchParams<{ mealType: MealType }>()
  const { searchFoods, loading } = useFoodDiary()
  
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Food[]>([])
  const [searching, setSearching] = useState(false)

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (query.trim().length >= 2) {
        setSearching(true)
        const foods = await searchFoods(query)
        setResults(foods)
        setSearching(false)
      } else {
        setResults([])
      }
    }, 500) // Debounce 500ms

    return () => clearTimeout(timer)
  }, [query, searchFoods])

  // Handle food selection
  const handleFoodPress = useCallback((food: Food) => {
    router.push({
      pathname: '/(tabs)/food-details',
      params: {
        foodId: food.fs_food_id.toString(),
        foodName: food.name,
        mealType: params.mealType
      }
    })
  }, [router, params.mealType])

  // Render item
  const renderItem = useCallback(({ item }: { item: Food }) => (
    <FoodItem food={item} onPress={handleFoodPress} />
  ), [handleFoodPress])

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Text style={styles.backButton}>← Retour</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Rechercher un aliment</Text>
      </View>

      {/* Search Bar */}
      <SearchBar
        value={query}
        onChangeText={setQuery}
        loading={searching}
        autoFocus
      />

      {/* Results */}
      <FlatList
        data={results}
        renderItem={renderItem}
        keyExtractor={(item) => item.fs_food_id.toString()}
        contentContainerStyle={styles.listContent}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            {query.trim().length === 0 ? (
              <>
                <Text style={styles.emptyIcon}>🔍</Text>
                <Text style={styles.emptyText}>
                  Recherchez un aliment pour commencer
                </Text>
              </>
            ) : query.trim().length < 2 ? (
              <Text style={styles.emptyText}>
                Tapez au moins 2 caractères
              </Text>
            ) : searching ? (
              <ActivityIndicator size="large" color="#007AFF" />
            ) : (
              <>
                <Text style={styles.emptyIcon}>😕</Text>
                <Text style={styles.emptyText}>
                  Aucun résultat pour "{query}"
                </Text>
                <Text style={styles.emptyHint}>
                  Essayez un autre terme
                </Text>
              </>
            )}
          </View>
        }
      />
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
    color: '#007AFF',
    marginBottom: 8
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#000'
  },
  listContent: {
    flexGrow: 1
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
    paddingVertical: 60
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: 16
  },
  emptyText: {
    fontSize: 18,
    color: '#666',
    textAlign: 'center',
    marginBottom: 8
  },
  emptyHint: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center'
  }
})
