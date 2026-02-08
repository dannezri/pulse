/**
 * HourlyEffectChart - Graphique en barres des effets horaires d'un médicament
 * Affiche concentration, efficacité et effets secondaires sur 24h
 */

import React, { useState, useRef, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, Dimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { HourlyEffect } from '../hooks/useMedicationAnalysis';

interface HourlyEffectChartProps {
  data: HourlyEffect[];
  intakeTimes?: string[]; // Heures de prise (ex: ["23:00"])
  labelConcentration?: string; // Label adaptatif (ex: "Niveau sanguin")
  labelEfficacite?: string; // Label adaptatif (ex: "Effet anxiolytique")
  labelEffetsSecondaires?: string; // Label adaptatif (ex: "Nausées/fatigue")
}

const CHART_HEIGHT = 200;
const BAR_WIDTH = 32;
const SCREEN_WIDTH = Dimensions.get('window').width;

export function HourlyEffectChart({ 
  data, 
  intakeTimes = [],
  labelConcentration = "Concentration",
  labelEfficacite = "Efficacité",
  labelEffetsSecondaires = "Effets 2nd",
}: HourlyEffectChartProps) {
  const [selectedHour, setSelectedHour] = useState<HourlyEffect | null>(null);
  const scrollViewRef = useRef<ScrollView>(null);

  if (!data || data.length === 0) {
    return null;
  }

  // Obtenir l'heure actuelle complète (avec minutes)
  const getCurrentTime = () => {
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes();
    return { hours, minutes, totalMinutes: hours * 60 + minutes };
  };

  const currentTime = getCurrentTime();

  // Trouver l'heure la plus proche de l'heure actuelle dans les données
  const findClosestHour = () => {
    if (!data || data.length === 0) return null;

    let closestHour = data[0].heure;
    let minDifference = Infinity;

    data.forEach(hourData => {
      const [hourStr] = hourData.heure.split(':');
      const dataHour = parseInt(hourStr, 10);
      const dataMinutes = dataHour * 60; // Convertir en minutes totales
      
      const difference = Math.abs(currentTime.totalMinutes - dataMinutes);
      
      if (difference < minDifference) {
        minDifference = difference;
        closestHour = hourData.heure;
      }
    });

    return closestHour;
  };

  const closestHour = findClosestHour();

  // Normaliser les heures de prise pour comparaison (format "HH:00")
  const normalizedIntakeTimes = intakeTimes.map(time => {
    const [hour] = time.split(':');
    return `${hour.padStart(2, '0')}:00`;
  });

  const isIntakeHour = (hour: string) => normalizedIntakeTimes.includes(hour);
  const isCurrentHour = (hour: string) => hour === closestHour;

  // Centrer automatiquement le scroll sur l'heure la plus proche
  useEffect(() => {
    if (scrollViewRef.current && closestHour) {
      // Trouver l'index de l'heure la plus proche
      const closestIndex = data.findIndex(item => item.heure === closestHour);
      
      if (closestIndex !== -1) {
        // Calculer la position x de l'élément
        const barGroupWidth = BAR_WIDTH + 8; // largeur d'un groupe de barres + gap
        const elementX = closestIndex * barGroupWidth;
        
        // Centrer l'élément dans la vue
        const screenCenter = SCREEN_WIDTH / 2;
        const scrollX = elementX - screenCenter + (barGroupWidth / 2);
        
        // Petit délai pour s'assurer que le composant est bien monté
        setTimeout(() => {
          scrollViewRef.current?.scrollTo({ 
            x: Math.max(0, scrollX), 
            animated: true 
          });
        }, 100);
      }
    }
  }, [closestHour, data]);

  return (
    <View style={styles.container}>
      {/* Légende avec labels adaptatifs */}
      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: '#5E5CE6' }]} />
          <Text style={styles.legendText}>{labelConcentration}</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: '#34C759' }]} />
          <Text style={styles.legendText}>{labelEfficacite}</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: '#FF9500' }]} />
          <Text style={styles.legendText}>{labelEffetsSecondaires}</Text>
        </View>
      </View>

      {/* Graphique scrollable */}
      <ScrollView 
        ref={scrollViewRef}
        horizontal 
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.chartContainer}
      >
        {data.map((hourData, index) => {
          const isIntake = isIntakeHour(hourData.heure);
          const isCurrent = isCurrentHour(hourData.heure);
          const isSelected = selectedHour?.heure === hourData.heure;
          
          // Facteur de réduction pour les heures non-actuelles (0.75 = 75% de la hauteur)
          const heightFactor = isCurrent ? 1 : 0.75;
          // Opacité réduite pour les heures non-actuelles
          const baseOpacity = isCurrent ? (isSelected ? 1 : 0.9) : (isSelected ? 0.85 : 0.5);
          
          return (
            <View key={index} style={styles.barGroup}>
              {/* Indicateur de prise */}
              {isIntake && (
                <View style={styles.intakeIndicator}>
                  <Text style={styles.intakeText}>💊</Text>
                </View>
              )}

              {/* Indicateur heure actuelle */}
              {isCurrent && (
                <View style={styles.currentIndicator}>
                  <Text style={styles.currentText}>•</Text>
                </View>
              )}

              {/* Barres empilées */}
              <View style={styles.barsContainer}>
                {/* Concentration (bleu) */}
                <View style={styles.barWrapper}>
                  <LinearGradient
                    colors={['#5E5CE6', '#4A4AC8']}
                    style={[
                      styles.bar,
                      { 
                        height: (hourData.concentration / 100) * CHART_HEIGHT * heightFactor,
                        opacity: baseOpacity,
                      }
                    ]}
                  />
                </View>

                {/* Efficacité (vert) */}
                <View style={styles.barWrapper}>
                  <LinearGradient
                    colors={['#34C759', '#2BA84A']}
                    style={[
                      styles.bar,
                      { 
                        height: (hourData.efficacite / 100) * CHART_HEIGHT * heightFactor,
                        opacity: baseOpacity,
                      }
                    ]}
                  />
                </View>

                {/* Effets secondaires (orange) */}
                <View style={styles.barWrapper}>
                  <LinearGradient
                    colors={['#FF9500', '#CC7700']}
                    style={[
                      styles.bar,
                      { 
                        height: (hourData.effets_secondaires / 100) * CHART_HEIGHT * heightFactor,
                        opacity: baseOpacity,
                      }
                    ]}
                  />
                </View>
              </View>

              {/* Heure */}
              <Text style={[
                styles.hourLabel,
                isIntake && styles.hourLabelIntake,
                isCurrent && styles.hourLabelCurrent,
                isSelected && styles.hourLabelSelected,
              ]}>
                {hourData.heure.split(':')[0]}h
              </Text>
            </View>
          );
        })}
      </ScrollView>

      {/* Description de l'heure sélectionnée */}
      {selectedHour && (
        <View style={styles.descriptionCard}>
          <Text style={styles.descriptionTime}>{selectedHour.heure}</Text>
          <Text style={styles.descriptionText}>{selectedHour.description}</Text>
          <View style={styles.descriptionStats}>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>{labelConcentration}</Text>
              <Text style={[styles.statValue, { color: '#5E5CE6' }]}>
                {selectedHour.concentration}%
              </Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>{labelEfficacite}</Text>
              <Text style={[styles.statValue, { color: '#34C759' }]}>
                {selectedHour.efficacite}%
              </Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>{labelEffetsSecondaires}</Text>
              <Text style={[styles.statValue, { color: '#FF9500' }]}>
                {selectedHour.effets_secondaires}%
              </Text>
            </View>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginVertical: 16,
  },
  legend: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 16,
    marginBottom: 16,
    paddingHorizontal: 16,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  legendText: {
    fontSize: 12,
    color: '#8E8E93',
    fontWeight: '500',
  },
  chartContainer: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    gap: 8,
  },
  barGroup: {
    alignItems: 'center',
    width: BAR_WIDTH + 8,
  },
  intakeIndicator: {
    position: 'absolute',
    top: -20,
    zIndex: 10,
  },
  intakeText: {
    fontSize: 16,
  },
  currentIndicator: {
    position: 'absolute',
    top: -32,
    zIndex: 11,
  },
  currentText: {
    fontSize: 24,
    color: '#5E5CE6',
    fontWeight: '900',
  },
  barsContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    height: CHART_HEIGHT,
    gap: 2,
  },
  barWrapper: {
    width: 8,
    height: CHART_HEIGHT,
    justifyContent: 'flex-end',
  },
  bar: {
    width: 8,
    borderRadius: 4,
  },
  hourLabel: {
    fontSize: 10,
    color: '#6E6E73',
    marginTop: 6,
    fontWeight: '500',
  },
  hourLabelIntake: {
    color: '#5E5CE6',
    fontWeight: '700',
  },
  hourLabelCurrent: {
    color: '#5E5CE6',
    fontWeight: '900',
    fontSize: 12,
  },
  hourLabelSelected: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  descriptionCard: {
    marginTop: 16,
    padding: 16,
    backgroundColor: 'rgba(28, 28, 30, 0.8)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  descriptionTime: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  descriptionText: {
    fontSize: 14,
    color: '#EBEBF5',
    lineHeight: 20,
    marginBottom: 12,
  },
  descriptionStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#2C2C2E',
  },
  statItem: {
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 11,
    color: '#8E8E93',
    marginBottom: 4,
  },
  statValue: {
    fontSize: 18,
    fontWeight: '700',
  },
});
