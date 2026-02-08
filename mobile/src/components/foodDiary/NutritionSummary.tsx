/**
 * NutritionSummary - Résumé nutritionnel (macros)
 * UI Pure : Affichage des macros (Design Pulse)
 */

import React from 'react'
import { View, Text, StyleSheet } from 'react-native'
import type { NutritionData } from '@/types/foodDiary'

interface NutritionSummaryProps {
  nutrition: NutritionData
  showDetails?: boolean
}

export const NutritionSummary: React.FC<NutritionSummaryProps> = ({
  nutrition,
  showDetails = true
}) => {
  return (
    <View style={styles.container}>
      {/* Calories principales */}
      <View style={styles.mainMetric}>
        <Text style={styles.caloriesValue}>{Math.round(nutrition.calories)}</Text>
        <Text style={styles.caloriesLabel}>kcal</Text>
      </View>
      
      {/* Macros */}
      {showDetails && (
        <View style={styles.macrosContainer}>
          <View style={styles.macroItem}>
            <Text style={styles.macroValue}>{nutrition.protein.toFixed(1)}</Text>
            <Text style={styles.macroLabel}>PROTÉINES</Text>
          </View>
          
          <View style={styles.macroItem}>
            <Text style={styles.macroValue}>{nutrition.carbohydrate.toFixed(1)}</Text>
            <Text style={styles.macroLabel}>GLUCIDES</Text>
          </View>
          
          <View style={styles.macroItem}>
            <Text style={styles.macroValue}>{nutrition.fat.toFixed(1)}</Text>
            <Text style={styles.macroLabel}>LIPIDES</Text>
          </View>
        </View>
      )}
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#1C1C1E',
    borderRadius: 20,
    padding: 24,
    marginHorizontal: 20,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  mainMetric: {
    flexDirection: 'row',
    alignItems: 'baseline',
    justifyContent: 'center',
    marginBottom: 20
  },
  caloriesValue: {
    fontSize: 56,
    fontWeight: '700',
    color: '#00FF41',
    letterSpacing: -2
  },
  caloriesLabel: {
    fontSize: 18,
    fontWeight: '600',
    color: '#8E8E93',
    marginLeft: 8
  },
  macrosContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 20,
    borderTopWidth: 1,
    borderTopColor: '#2C2C2E'
  },
  macroItem: {
    alignItems: 'center',
    flex: 1
  },
  macroValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4
  },
  macroLabel: {
    fontSize: 10,
    color: '#8E8E93',
    fontWeight: '600',
    letterSpacing: 0.5
  }
})
