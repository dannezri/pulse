import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { TrendingUp, TrendingDown } from 'lucide-react-native';
import type { Anomaly } from '../services/ZScoreCalculator';

interface WhyPillsProps {
  anomalies: Anomaly[];
}

/**
 * Affiche les 3 principales raisons (anomalies) sous forme de pilules horizontales
 */
export function WhyPills({ anomalies }: WhyPillsProps) {
  if (anomalies.length === 0) {
    return null;
  }

  return (
    <View style={styles.container}>
      {anomalies.map((anomaly, index) => (
        <Pill key={`${anomaly.metric}-${index}`} anomaly={anomaly} />
      ))}
    </View>
  );
}

/**
 * Pilule individuelle affichant une anomalie
 */
function Pill({ anomaly }: { anomaly: Anomaly }) {
  const isAbove = anomaly.direction === 'above';
  const Icon = isAbove ? TrendingUp : TrendingDown;
  const iconColor = isAbove ? '#00FF41' : '#FF9500';

  // Formater la valeur selon la métrique
  const formattedValue = formatMetricValue(anomaly.metric, anomaly.value);
  const metricName = getMetricShortName(anomaly.metric);

  // Calculer le pourcentage de variation par rapport à la baseline
  const percentChange = anomaly.baseline.mean > 0
    ? ((anomaly.value - anomaly.baseline.mean) / anomaly.baseline.mean * 100)
    : 0;
  const percentText = isAbove 
    ? `+${Math.abs(percentChange).toFixed(0)}%`
    : `-${Math.abs(percentChange).toFixed(0)}%`;

  return (
    <View style={styles.pill}>
      <Icon size={16} color={iconColor} strokeWidth={2.5} />
      <View style={styles.pillContent}>
        <Text style={styles.pillMetric}>{metricName}</Text>
        <Text style={[styles.pillValue, { color: iconColor }]}>
          {percentText}
        </Text>
      </View>
      <Text style={styles.pillActualValue}>{formattedValue}</Text>
    </View>
  );
}

/**
 * Formater la valeur selon le type de métrique
 */
function formatMetricValue(metric: string, value: number): string {
  switch (metric) {
    case 'hrv':
      return `${Math.round(value)} ms`;
    case 'heart_rate':
    case 'hr':
      return `${Math.round(value)} bpm`;
    case 'spo2':
      return `${Math.round(value)}%`;
    case 'body_temperature':
      return `${value.toFixed(1)}°C`;
    case 'sleep_duration':
    case 'sleep':
      return `${(value / 3600).toFixed(1)}h`;
    case 'steps':
      return `${Math.round(value).toLocaleString('fr-FR')}`;
    case 'distance':
      return `${(value / 1000).toFixed(1)} km`;
    case 'calories':
    case 'active_calories':
      return `${Math.round(value)} kcal`;
    case 'water':
      return `${Math.round(value)} mL`;
    case 'caffeine':
      return `${Math.round(value)} mg`;
    case 'weight':
      return `${value.toFixed(1)} kg`;
    case 'glucose':
      return `${Math.round(value)} mg/dL`;
    case 'stress':
      return `${Math.round(value)}/100`;
    case 'respiratory_rate':
      return `${Math.round(value)} /min`;
    case 'floors_climbed':
      return `${Math.round(value)} étages`;
    default:
      return Math.round(value).toString();
  }
}

/**
 * Obtenir le nom court de la métrique pour l'affichage dans la pilule
 */
function getMetricShortName(metric: string): string {
  const names: Record<string, string> = {
    hrv: 'HRV',
    heart_rate: 'FC',
    hr: 'FC',
    body_temperature: 'Temp',
    sleep_duration: 'Sommeil',
    sleep: 'Sommeil',
    stress: 'Stress',
    glucose: 'Glycémie',
    spo2: 'SpO2',
    steps: 'Pas',
    calories: 'Calories',
    water: 'Eau',
    active_calories: 'Cal. actives',
    weight: 'Poids',
    respiratory_rate: 'Resp',
    caffeine: 'Caféine',
    distance: 'Distance',
    floors_climbed: 'Étages',
  };
  return names[metric] || metric;
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  pill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1C1C1E',
    borderRadius: 20,
    paddingVertical: 10,
    paddingHorizontal: 16,
    gap: 8,
    borderWidth: 1,
    borderColor: '#2C2C2E',
    minWidth: 140,
  },
  pillContent: {
    flex: 1,
  },
  pillMetric: {
    fontSize: 13,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 2,
  },
  pillValue: {
    fontSize: 15,
    fontWeight: '700',
  },
  pillActualValue: {
    fontSize: 12,
    color: '#8E8E93',
    fontWeight: '500',
  },
});
