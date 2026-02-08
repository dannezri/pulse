/**
 * MealCard - Card affichant un repas (meal type)
 * UI Pure : Affichage d'un repas avec ses items (Design Pulse)
 */

import React from 'react'
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native'
import { MEAL_LABELS, MEAL_ICONS, type MealType, type FoodLogWithNutrition } from '@/types/foodDiary'

interface MealCardProps {
  mealType: MealType
  meals: FoodLogWithNutrition[]
  onAddPress: () => void
  onMealPress?: (meal: FoodLogWithNutrition) => void
}

export const MealCard: React.FC<MealCardProps> = ({
  mealType,
  meals,
  onAddPress,
  onMealPress
}) => {
  const totalCalories = meals.reduce((sum, meal) => sum + meal.nutrition.calories, 0)
  
  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.icon}>{MEAL_ICONS[mealType]}</Text>
          <Text style={styles.mealType}>{MEAL_LABELS[mealType].toUpperCase()}</Text>
        </View>
        
        {totalCalories > 0 && (
          <Text style={styles.calories}>{Math.round(totalCalories)} kcal</Text>
        )}
      </View>
      
      {/* Meals */}
      {meals.length > 0 ? (
        <View style={styles.mealsContainer}>
          {meals.map((meal) => (
            <TouchableOpacity
              key={meal.id}
              style={styles.mealItem}
              onPress={() => onMealPress?.(meal)}
              activeOpacity={0.8}
            >
              {meal.items.map((item, idx) => (
                <View key={idx} style={styles.itemRow}>
                  <Text style={styles.itemName} numberOfLines={1}>
                    {item.name}
                  </Text>
                  <Text style={styles.itemQuantity}>
                    {item.quantity} {item.unit}
                  </Text>
                </View>
              ))}
              
              {meal.note && (
                <Text style={styles.note} numberOfLines={1}>
                  💬 {meal.note}
                </Text>
              )}
            </TouchableOpacity>
          ))}
        </View>
      ) : (
        <TouchableOpacity
          style={styles.emptyContainer}
          onPress={onAddPress}
          activeOpacity={0.8}
        >
          <Text style={styles.emptyText}>Ajouter un aliment</Text>
        </TouchableOpacity>
      )}
      
      {/* Add Button - only if meals exist */}
      {meals.length > 0 && (
        <TouchableOpacity
          style={styles.addButton}
          onPress={onAddPress}
          activeOpacity={0.8}
        >
          <Text style={styles.addButtonText}>+ Ajouter</Text>
        </TouchableOpacity>
      )}
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    marginHorizontal: 20,
    marginBottom: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center'
  },
  icon: {
    fontSize: 20,
    marginRight: 8
  },
  mealType: {
    fontSize: 14,
    fontWeight: '700',
    color: '#8E8E93',
    letterSpacing: 0.5
  },
  calories: {
    fontSize: 16,
    fontWeight: '700',
    color: '#00FF41'
  },
  mealsContainer: {
    marginBottom: 8
  },
  mealItem: {
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: '#2C2C2E'
  },
  itemRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6
  },
  itemName: {
    flex: 1,
    fontSize: 15,
    color: '#FFFFFF',
    fontWeight: '500',
    marginRight: 8
  },
  itemQuantity: {
    fontSize: 13,
    color: '#8E8E93',
    fontWeight: '500'
  },
  note: {
    fontSize: 12,
    color: '#8E8E93',
    marginTop: 4
  },
  emptyContainer: {
    paddingVertical: 16,
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#2C2C2E'
  },
  emptyText: {
    fontSize: 14,
    color: '#8E8E93',
    fontWeight: '500'
  },
  addButton: {
    marginTop: 8,
    paddingVertical: 12,
    backgroundColor: '#00FF41',
    borderRadius: 12,
    alignItems: 'center'
  },
  addButtonText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#000000'
  }
})
