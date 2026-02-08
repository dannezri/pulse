import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  TouchableOpacity,
  Platform,
} from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { useAuth } from '../../src/hooks/useAuth';
import { useMetricsHistory } from '../../src/hooks/useMetricsHistory';
import { useTrendsSummary } from '../../src/hooks/useTrendsSummary';
import { useQueryClient } from '@tanstack/react-query';
import { TrendingUp, TrendingDown, Minus, Activity, Heart, Moon, Footprints, Flame, Route, Wind, Droplets, Scale, Brain, Coffee, Apple, TrendingUpIcon, Calendar } from 'lucide-react-native';
import { LifeLineChart } from '../../src/components/LifeLineChart';
import { TrendsSummaryCard } from '../../src/components/TrendsSummaryCard';

type MetricType = 
  | 'steps' | 'distance' | 'calories' | 'active_calories' | 'floors_climbed' | 'vo2_max'
  | 'hrv' | 'heart_rate' | 'spo2' | 'blood_pressure' | 'glucose' | 'respiratory_rate'
  | 'weight' | 'body_fat' | 'bmi' | 'body_temperature'
  | 'sleep_duration'
  | 'stress' | 'mindfulness'
  | 'water' | 'caffeine' | 'carbs';

interface MetricConfig {
  key: MetricType;
  title: string;
  icon: React.ReactNode;
  color: string;
  unit: string;
  formatter: (value: number) => string;
}

const METRIC_CONFIGS: MetricConfig[] = [
  // Activity
  {
    key: 'steps',
    title: 'Pas',
    icon: <Footprints size={18} color="#00FF41" />,
    color: '#00FF41',
    unit: 'pas',
    formatter: (v) => Math.round(v).toLocaleString('fr-FR'),
  },
  {
    key: 'distance',
    title: 'Distance',
    icon: <Route size={18} color="#5856D6" />,
    color: '#5856D6',
    unit: 'km',
    formatter: (v) => v.toFixed(1),
  },
  {
    key: 'calories',
    title: 'Calories Totales',
    icon: <Flame size={18} color="#FF3B30" />,
    color: '#FF3B30',
    unit: 'kcal',
    formatter: (v) => Math.round(v).toString(),
  },
  {
    key: 'active_calories',
    title: 'Calories Actives',
    icon: <Flame size={18} color="#FF6B35" />,
    color: '#FF6B35',
    unit: 'kcal',
    formatter: (v) => Math.round(v).toString(),
  },
  {
    key: 'floors_climbed',
    title: 'Étages Montés',
    icon: <TrendingUpIcon size={18} color="#AF52DE" />,
    color: '#AF52DE',
    unit: 'étages',
    formatter: (v) => Math.round(v).toString(),
  },
  {
    key: 'vo2_max',
    title: 'VO2 Max',
    icon: <Wind size={18} color="#32ADE6" />,
    color: '#32ADE6',
    unit: 'mL/kg/min',
    formatter: (v) => v.toFixed(1),
  },
  
  // Vitals
  {
    key: 'hrv',
    title: 'HRV',
    icon: <Activity size={18} color="#00FF41" />,
    color: '#00FF41',
    unit: 'ms',
    formatter: (v) => Math.round(v).toString(),
  },
  {
    key: 'heart_rate',
    title: 'Rythme Cardiaque',
    icon: <Heart size={18} color="#FF9500" />,
    color: '#FF9500',
    unit: 'bpm',
    formatter: (v) => Math.round(v).toString(),
  },
  {
    key: 'spo2',
    title: 'Saturation O2',
    icon: <Wind size={18} color="#00C7BE" />,
    color: '#00C7BE',
    unit: '%',
    formatter: (v) => Math.round(v).toString(),
  },
  {
    key: 'blood_pressure',
    title: 'Pression Artérielle',
    icon: <Heart size={18} color="#FF375F" />,
    color: '#FF375F',
    unit: 'mmHg',
    formatter: (v) => Math.round(v).toString(),
  },
  {
    key: 'glucose',
    title: 'Glycémie',
    icon: <Droplets size={18} color="#BF5AF2" />,
    color: '#BF5AF2',
    unit: 'mg/dL',
    formatter: (v) => Math.round(v).toString(),
  },
  {
    key: 'respiratory_rate',
    title: 'Fréquence Respiratoire',
    icon: <Wind size={18} color="#64D2FF" />,
    color: '#64D2FF',
    unit: 'bpm',
    formatter: (v) => Math.round(v).toString(),
  },
  
  // Body
  {
    key: 'weight',
    title: 'Poids',
    icon: <Scale size={18} color="#FF9F0A" />,
    color: '#FF9F0A',
    unit: 'kg',
    formatter: (v) => v.toFixed(1),
  },
  {
    key: 'body_fat',
    title: 'Masse Grasse',
    icon: <Scale size={18} color="#FFD60A" />,
    color: '#FFD60A',
    unit: '%',
    formatter: (v) => v.toFixed(1),
  },
  {
    key: 'bmi',
    title: 'IMC',
    icon: <Scale size={18} color="#FFCC00" />,
    color: '#FFCC00',
    unit: 'kg/m²',
    formatter: (v) => v.toFixed(1),
  },
  {
    key: 'body_temperature',
    title: 'Température Corporelle',
    icon: <Activity size={18} color="#FF453A" />,
    color: '#FF453A',
    unit: '°C',
    formatter: (v) => v.toFixed(1),
  },
  
  // Sleep
  {
    key: 'sleep_duration',
    title: 'Sommeil',
    icon: <Moon size={18} color="#0066FF" />,
    color: '#0066FF',
    unit: 'h',
    formatter: (v) => (v / 3600).toFixed(1),
  },
  
  // Wellness
  {
    key: 'stress',
    title: 'Niveau de Stress',
    icon: <Brain size={18} color="#FF2D55" />,
    color: '#FF2D55',
    unit: 'score',
    formatter: (v) => Math.round(v).toString(),
  },
  {
    key: 'mindfulness',
    title: 'Méditation',
    icon: <Brain size={18} color="#30D158" />,
    color: '#30D158',
    unit: 'min',
    formatter: (v) => Math.round(v).toString(),
  },
  
  // Nutrition
  {
    key: 'water',
    title: 'Hydratation',
    icon: <Droplets size={18} color="#00C7BE" />,
    color: '#00C7BE',
    unit: 'mL',
    formatter: (v) => Math.round(v).toString(),
  },
  {
    key: 'caffeine',
    title: 'Caféine',
    icon: <Coffee size={18} color="#8B4513" />,
    color: '#8B4513',
    unit: 'mg',
    formatter: (v) => Math.round(v).toString(),
  },
  {
    key: 'carbs',
    title: 'Glucides',
    icon: <Apple size={18} color="#FFD60A" />,
    color: '#FFD60A',
    unit: 'g',
    formatter: (v) => Math.round(v).toString(),
  },
];

type ViewMode = 'period' | 'day';

export default function TendancesScreen() {
  const { userId } = useAuth();
  const [viewMode, setViewMode] = useState<ViewMode>('period');
  const [selectedPeriod, setSelectedPeriod] = useState<7 | 30 | 90>(30);
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [showDatePicker, setShowDatePicker] = useState(false);
  
  const { data: metricsHistory, isLoading, error } = useMetricsHistory(
    userId, 
    viewMode === 'period' ? selectedPeriod : undefined,
    viewMode === 'day' ? selectedDate : undefined
  );
  
  // Calcul du résumé automatique des tendances (toujours sur 30J)
  const trendsSummary = useTrendsSummary(metricsHistory);
  
  const queryClient = useQueryClient();
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = async () => {
    setRefreshing(true);
    await queryClient.invalidateQueries({ queryKey: ['metricsHistory'] });
    setRefreshing(false);
  };

  const calculateStats = (data: any[]) => {
    if (!data || data.length === 0) {
      return { average: 0, min: 0, max: 0, trend: 'stable' as const, count: 0 };
    }

    // Filtrer les valeurs invalides
    const values = data
      .map((d) => d?.value)
      .filter((v) => v != null && typeof v === 'number' && !isNaN(v) && isFinite(v));
    
    if (values.length === 0) {
      return { average: 0, min: 0, max: 0, trend: 'stable' as const, count: 0 };
    }

    const average = values.reduce((a, b) => a + b, 0) / values.length;
    const min = Math.min(...values);
    const max = Math.max(...values);

    // Pour un jour unique, pas de tendance
    if (viewMode === 'day' || values.length === 1) {
      return { average, min, max, trend: 'stable' as const, count: values.length };
    }

    // Calculate trend (compare first half vs second half)
    const midPoint = Math.floor(values.length / 2);
    const firstHalf = values.slice(0, midPoint);
    const secondHalf = values.slice(midPoint);

    const firstAvg = firstHalf.length > 0 ? firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length : 0;
    const secondAvg = secondHalf.length > 0 ? secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length : 0;

    const diff = secondAvg - firstAvg;
    const trend = firstAvg > 0 && (diff > firstAvg * 0.05 ? 'up' : diff < -firstAvg * 0.05 ? 'down' : 'stable') || 'stable';

    return { average, min, max, trend, count: values.length };
  };

  const renderMetricCard = (config: MetricConfig) => {
    const data = metricsHistory?.[config.key] || [];
    const stats = calculateStats(data);

    if (data.length === 0) {
      return null;
    }

    const TrendIcon =
      stats.trend === 'up' ? TrendingUp : stats.trend === 'down' ? TrendingDown : Minus;
    const trendColor = stats.trend === 'up' ? '#00FF41' : stats.trend === 'down' ? '#FF3B30' : '#8E8E93';

    return (
      <View key={config.key} style={styles.metricCard}>
        <View style={styles.metricHeader}>
          <View style={styles.metricTitleRow}>
            {config.icon}
            <Text style={styles.metricTitle}>{config.title}</Text>
          </View>
          <View style={styles.trendBadge}>
            <TrendIcon size={14} color={trendColor} />
          </View>
        </View>

        <View style={styles.statsRow}>
          {viewMode === 'day' ? (
            <>
              <View style={styles.statItem}>
                <Text style={styles.statLabel}>Mesures</Text>
                <Text style={styles.statValue}>
                  {stats.count} <Text style={styles.statUnit}>enregistrement{stats.count > 1 ? 's' : ''}</Text>
                </Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statLabel}>Plage</Text>
                <Text style={styles.statValue}>
                  {config.formatter(stats.min)} - {config.formatter(stats.max)}
                </Text>
              </View>
            </>
          ) : (
            <>
              <View style={styles.statItem}>
                <Text style={styles.statLabel}>Moyenne</Text>
                <Text style={styles.statValue}>
                  {config.formatter(stats.average)} <Text style={styles.statUnit}>{config.unit}</Text>
                </Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statLabel}>Min / Max</Text>
                <Text style={styles.statValue}>
                  {config.formatter(stats.min)} / {config.formatter(stats.max)}
                </Text>
              </View>
            </>
          )}
        </View>

        <View style={styles.chartContainer}>
          <LifeLineChart
            data={data}
            baseline={stats.average}
            color={config.color}
            title={config.title}
            unit={config.unit}
          />
        </View>

        <Text style={styles.dataInfo}>
          {viewMode === 'period' 
            ? `${data.length} point${data.length > 1 ? 's' : ''} • ${selectedPeriod} derniers jours`
            : `${data.length} mesure${data.length > 1 ? 's' : ''} • ${selectedDate.toLocaleDateString('fr-FR')}`
          }
        </Text>
      </View>
    );
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#34C759" />
        <Text style={styles.loadingText}>Chargement de l'historique...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>Erreur lors du chargement</Text>
        <TouchableOpacity onPress={onRefresh} style={styles.retryButton}>
          <Text style={styles.retryButtonText}>Réessayer</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.contentContainer}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#34C759" />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Tendances</Text>
        <Text style={styles.subtitle}>Historique de vos métriques</Text>
      </View>

      {/* View Mode Selector */}
      <View style={styles.modeSelector}>
        <TouchableOpacity
          style={[
            styles.modeButton,
            viewMode === 'period' && styles.modeButtonActive,
          ]}
          onPress={() => setViewMode('period')}
        >
          <TrendingUpIcon size={16} color={viewMode === 'period' ? '#FFFFFF' : '#8E8E93'} />
          <Text
            style={[
              styles.modeButtonText,
              viewMode === 'period' && styles.modeButtonTextActive,
            ]}
          >
            Période
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[
            styles.modeButton,
            viewMode === 'day' && styles.modeButtonActive,
          ]}
          onPress={() => setViewMode('day')}
        >
          <Calendar size={16} color={viewMode === 'day' ? '#FFFFFF' : '#8E8E93'} />
          <Text
            style={[
              styles.modeButtonText,
              viewMode === 'day' && styles.modeButtonTextActive,
            ]}
          >
            Jour
          </Text>
        </TouchableOpacity>
      </View>

      {/* Period Selector (only shown in period mode) */}
      {viewMode === 'period' && (
        <View style={styles.periodSelector}>
          {[7, 30, 90].map((period) => (
            <TouchableOpacity
              key={period}
              style={[
                styles.periodButton,
                selectedPeriod === period && styles.periodButtonActive,
              ]}
              onPress={() => setSelectedPeriod(period as 7 | 30 | 90)}
            >
              <Text
                style={[
                  styles.periodButtonText,
                  selectedPeriod === period && styles.periodButtonTextActive,
                ]}
              >
                {period}J
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Date Picker (only shown in day mode) */}
      {viewMode === 'day' && (
        <View style={styles.datePickerContainer}>
          <TouchableOpacity
            style={styles.datePickerButton}
            onPress={() => setShowDatePicker(true)}
          >
            <Calendar size={18} color="#34C759" />
            <Text style={styles.datePickerText}>
              {selectedDate.toLocaleDateString('fr-FR', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}
            </Text>
          </TouchableOpacity>
          {showDatePicker && (
            <DateTimePicker
              value={selectedDate}
              mode="date"
              display={Platform.OS === 'ios' ? 'compact' : 'default'}
              onChange={(event, date) => {
                // Sur Android, fermer immédiatement
                if (Platform.OS === 'android') {
                  setShowDatePicker(false);
                }
                
                // Si l'utilisateur a sélectionné une date (pas cancel)
                if (event.type === 'set' && date) {
                  setSelectedDate(date);
                  // Sur iOS, fermer après sélection
                  if (Platform.OS === 'ios') {
                    setShowDatePicker(false);
                  }
                } else if (event.type === 'dismissed') {
                  // Fermer si l'utilisateur annule
                  setShowDatePicker(false);
                }
              }}
              maximumDate={new Date()}
              locale="fr-FR"
            />
          )}
        </View>
      )}

      {/* Trends Summary Card (only shown in period mode with 30 days) */}
      {viewMode === 'period' && selectedPeriod === 30 && (
        <TrendsSummaryCard summary={trendsSummary} />
      )}

      {/* Metrics Cards */}
      <View style={styles.metricsContainer}>
        {METRIC_CONFIGS.map((config) => renderMetricCard(config))}
      </View>

      {/* Empty State */}
      {METRIC_CONFIGS.every((config) => !metricsHistory?.[config.key]?.length) && (
        <View style={styles.emptyState}>
          <Text style={styles.emptyIcon}>📊</Text>
          <Text style={styles.emptyTitle}>Aucune donnée disponible</Text>
          <Text style={styles.emptyText}>
            Synchronisez vos données de santé pour voir vos tendances
          </Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  contentContainer: {
    padding: 20,
    paddingTop: 60,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000000',
  },
  loadingText: {
    color: '#8E8E93',
    marginTop: 16,
    fontSize: 14,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000000',
    padding: 20,
  },
  errorText: {
    color: '#FF3B30',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 16,
  },
  retryButton: {
    backgroundColor: '#1C1C1E',
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 24,
  },
  retryButtonText: {
    color: '#34C759',
    fontSize: 14,
    fontWeight: '600',
  },
  header: {
    marginBottom: 24,
  },
  title: {
    fontSize: 32,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#8E8E93',
  },
  modeSelector: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
  },
  modeButton: {
    flex: 1,
    backgroundColor: '#1C1C1E',
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  modeButtonActive: {
    backgroundColor: '#34C759',
    borderColor: '#34C759',
  },
  modeButtonText: {
    color: '#8E8E93',
    fontSize: 14,
    fontWeight: '600',
  },
  modeButtonTextActive: {
    color: '#FFFFFF',
  },
  datePickerContainer: {
    marginBottom: 24,
  },
  datePickerButton: {
    backgroundColor: '#1C1C1E',
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  datePickerText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
    textTransform: 'capitalize',
    flex: 1,
  },
  periodSelector: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 24,
  },
  periodButton: {
    flex: 1,
    backgroundColor: '#1C1C1E',
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  periodButtonActive: {
    backgroundColor: '#34C759',
    borderColor: '#34C759',
  },
  periodButtonText: {
    color: '#8E8E93',
    fontSize: 14,
    fontWeight: '600',
  },
  periodButtonTextActive: {
    color: '#FFFFFF',
  },
  metricsContainer: {
    gap: 16,
  },
  metricCard: {
    backgroundColor: '#1C1C1E',
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  metricHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  metricTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  metricTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  trendBadge: {
    backgroundColor: '#2C2C2E',
    borderRadius: 8,
    padding: 6,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 16,
    marginBottom: 16,
  },
  statItem: {
    flex: 1,
  },
  statLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 4,
  },
  statValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  statUnit: {
    fontSize: 12,
    fontWeight: '400',
    color: '#8E8E93',
  },
  chartContainer: {
    marginVertical: 16,
    alignItems: 'center',
  },
  dataInfo: {
    fontSize: 11,
    color: '#8E8E93',
    textAlign: 'center',
    marginTop: 8,
  },
  emptyState: {
    backgroundColor: '#1C1C1E',
    borderRadius: 20,
    padding: 40,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2C2C2E',
    marginTop: 20,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 8,
    textAlign: 'center',
  },
  emptyText: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 20,
  },
});
