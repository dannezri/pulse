/**
 * FoodItem - Item aliment dans les résultats de recherche (Design Pulse)
 * UI Pure : Affichage + événement onPress
 */

import React from 'react'
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native'
import { ChevronRight } from 'lucide-react-native'
import type { Food } from '@/types/foodDiary'

interface FoodItemProps {
  food: Food
  onPress: (food: Food) => void
}

export const FoodItem: React.FC<FoodItemProps> = ({ food, onPress }) => {
  return (
    <TouchableOpacity
      style={styles.container}
      onPress={() => onPress(food)}
      activeOpacity={0.8}
    >
      <View style={styles.content}>
        <Text style={styles.name} numberOfLines={2}>
          {food.name}
        </Text>
        
        {food.brand && (
          <Text style={styles.brand} numberOfLines={1}>
            {food.brand}
          </Text>
        )}
        
        {food.description && (
          <Text style={styles.description} numberOfLines={2}>
            {food.description}
          </Text>
        )}
      </View>
      
      <View style={styles.arrow}>
        <ChevronRight size={20} color="#8E8E93" />
      </View>
    </TouchableOpacity>
  )
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1C1C1E',
    marginHorizontal: 20,
    marginBottom: 12,
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#2C2C2E'
  },
  content: {
    flex: 1,
    marginRight: 12
  },
  name: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 4
  },
  brand: {
    fontSize: 13,
    color: '#8E8E93',
    fontWeight: '500',
    marginBottom: 4
  },
  description: {
    fontSize: 12,
    color: '#666666',
    lineHeight: 16
  },
  arrow: {
    width: 24,
    height: 24,
    alignItems: 'center',
    justifyContent: 'center'
  }
})
