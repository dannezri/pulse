/**
 * Energy Analysis Screen - Analyse détaillée de l'énergie
 * 
 * Page dédiée affichant:
 * - La courbe d'énergie intrajournalière
 * - Le raisonnement complet du calcul
 * - Les données sources (Oura, médicaments, conditions)
 * - L'impact de chaque facteur
 * - Les poids personnalisés ML
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Pressable,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { LineChart } from 'react-native-chart-kit';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '../src/hooks/useAuth';
import { useBriefData } from '../src/hooks/useBriefData';
import * as Haptics from 'expo-haptics';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

export default function EnergyAnalysisScreen() {
  const router = useRouter();
  const { userId } = useAuth();
  const { data: briefData, isLoading } = useBriefData(userId);
  const [showDebugMode, setShowDebugMode] = useState(false);

  const forecast = briefData?.intraday_energy_forecast;

  if (isLoading || !forecast) {
    return (
      <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#8B5CF6" />
          <Text style={styles.loadingText}>Analyse en cours...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Préparer les données pour le graphique
  const chartData = {
    labels: forecast.forecast_curve
      ?.filter((_, i) => i % 3 === 0) // Tous les 3 points
      .map((point: any) => {
        const time = new Date(point.time);
        return `${time.getHours()}h`;
      }) || [],
    datasets: [
      {
        data: forecast.forecast_curve
          ?.filter((_, i: number) => i % 3 === 0)
          .map((point: any) => point.value || 0) || [0],
        color: (opacity = 1) => `rgba(139, 92, 246, ${opacity})`,
        strokeWidth: 3,
      },
    ],
  };

  const currentEnergy = forecast.current_energy || 0;
  const influencers = forecast.influencers || [];
  const notes = forecast.notes || [];

  // Calculer les statistiques
  const positiveInfluencers = influencers.filter((inf: any) => inf.status === 'positive');
  const negativeInfluencers = influencers.filter((inf: any) => inf.status === 'negative');

  const totalPositive = positiveInfluencers.reduce((sum: number, inf: any) => {
    return sum + Math.abs(parseInt(inf.impact) || 0);
  }, 0);

  const totalNegative = negativeInfluencers.reduce((sum: number, inf: any) => {
    return sum + Math.abs(parseInt(inf.impact) || 0);
  }, 0);

  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      {/* Header */}
      <View style={styles.header}>
        <Pressable
          style={styles.backButton}
          onPress={() => {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            router.back();
          }}
        >
          <Text style={styles.backButtonText}>←</Text>
        </Pressable>
        <Text style={styles.headerTitle}>Analyse Énergétique</Text>
        <Pressable
          style={styles.debugButton}
          onPress={() => {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            setShowDebugMode(!showDebugMode);
          }}
        >
          <Text style={styles.debugButtonText}>{showDebugMode ? '✓' : '🔬'}</Text>
        </Pressable>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Score actuel */}
        <View style={styles.scoreCard}>
          <Text style={styles.scoreLabel}>Énergie actuelle</Text>
          <Text style={styles.scoreValue}>{Math.round(currentEnergy)}%</Text>
          <Text style={styles.scoreSubtitle}>
            {currentEnergy < 20 && 'Repos nécessaire'}
            {currentEnergy >= 20 && currentEnergy < 40 && 'Énergie basse'}
            {currentEnergy >= 40 && currentEnergy < 60 && 'Énergie modérée'}
            {currentEnergy >= 60 && currentEnergy < 80 && 'Bonne énergie'}
            {currentEnergy >= 80 && 'Énergie excellente'}
          </Text>
        </View>

        {/* Graphique */}
        <View style={styles.chartCard}>
          <Text style={styles.sectionTitle}>📈 Courbe prédictive</Text>
          <LineChart
            data={chartData}
            width={SCREEN_WIDTH - 48}
            height={220}
            chartConfig={{
              backgroundColor: '#1F1F1F',
              backgroundGradientFrom: '#1F1F1F',
              backgroundGradientTo: '#1F1F1F',
              decimalPlaces: 0,
              color: (opacity = 1) => `rgba(139, 92, 246, ${opacity})`,
              labelColor: (opacity = 1) => `rgba(156, 163, 175, ${opacity})`,
              style: {
                borderRadius: 16,
              },
              propsForDots: {
                r: '4',
                strokeWidth: '2',
                stroke: '#8B5CF6',
              },
            }}
            bezier
            style={styles.chart}
          />
          <Text style={styles.chartCaption}>
            Prédiction basée sur le modèle Pulse Energy Decay V2
          </Text>
        </View>

        {/* Balance des facteurs */}
        <View style={styles.balanceCard}>
          <Text style={styles.sectionTitle}>⚖️ Balance énergétique</Text>
          
          <View style={styles.balanceBar}>
            <View style={[styles.balancePositive, { flex: totalPositive }]}>
              <Text style={styles.balanceText}>+{totalPositive}</Text>
            </View>
            <View style={[styles.balanceNegative, { flex: totalNegative }]}>
              <Text style={styles.balanceText}>-{totalNegative}</Text>
            </View>
          </View>

          <View style={styles.balanceStats}>
            <View style={styles.balanceStat}>
              <Text style={styles.balanceStatLabel}>Facteurs positifs</Text>
              <Text style={[styles.balanceStatValue, { color: '#10B981' }]}>
                {positiveInfluencers.length}
              </Text>
            </View>
            <View style={styles.balanceStat}>
              <Text style={styles.balanceStatLabel}>Facteurs négatifs</Text>
              <Text style={[styles.balanceStatValue, { color: '#EF4444' }]}>
                {negativeInfluencers.length}
              </Text>
            </View>
          </View>
        </View>

        {/* Influencers détaillés */}
        <View style={styles.influencersCard}>
          <Text style={styles.sectionTitle}>🎯 Facteurs d'influence</Text>
          
          {positiveInfluencers.length > 0 && (
            <>
              <Text style={styles.influencerCategory}>Facteurs positifs</Text>
              {positiveInfluencers.map((inf: any, index: number) => (
                <View key={index} style={[styles.influencerItem, styles.influencerPositive]}>
                  <Text style={styles.influencerName}>{inf.name}</Text>
                  <Text style={[styles.influencerImpact, { color: '#10B981' }]}>
                    {inf.impact}
                  </Text>
                </View>
              ))}
            </>
          )}

          {negativeInfluencers.length > 0 && (
            <>
              <Text style={[styles.influencerCategory, { marginTop: 16 }]}>
                Facteurs négatifs
              </Text>
              {negativeInfluencers.map((inf: any, index: number) => (
                <View key={index} style={[styles.influencerItem, styles.influencerNegative]}>
                  <Text style={styles.influencerName}>{inf.name}</Text>
                  <Text style={[styles.influencerImpact, { color: '#EF4444' }]}>
                    {inf.impact}
                  </Text>
                </View>
              ))}
            </>
          )}
        </View>

        {/* Notes explicatives */}
        {notes.length > 0 && (
          <View style={styles.notesCard}>
            <Text style={styles.sectionTitle}>📝 Notes explicatives</Text>
            {notes.map((note: string, index: number) => (
              <View key={index} style={styles.noteItem}>
                <Text style={styles.noteBullet}>•</Text>
                <Text style={styles.noteText}>{note}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Mode Debug */}
        {showDebugMode && (
          <View style={styles.debugCard}>
            <Text style={styles.sectionTitle}>🔬 Mode Debug</Text>
            
            <View style={styles.debugSection}>
              <Text style={styles.debugLabel}>Type de modèle</Text>
              <Text style={styles.debugValue}>{forecast.type || 'N/A'}</Text>
            </View>

            <View style={styles.debugSection}>
              <Text style={styles.debugLabel}>Version</Text>
              <Text style={styles.debugValue}>{forecast.model_version || 'N/A'}</Text>
            </View>

            <View style={styles.debugSection}>
              <Text style={styles.debugLabel}>Date de génération</Text>
              <Text style={styles.debugValue}>
                {new Date(forecast.generated_at).toLocaleString('fr-FR')}
              </Text>
            </View>

            <View style={styles.debugSection}>
              <Text style={styles.debugLabel}>Points de données</Text>
              <Text style={styles.debugValue}>
                {forecast.forecast_curve?.length || 0}
              </Text>
            </View>

            <Pressable
              style={styles.jsonButton}
              onPress={() => {
                console.log('[Energy Analysis] Full forecast data:', JSON.stringify(forecast, null, 2));
                Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
              }}
            >
              <Text style={styles.jsonButtonText}>📋 Log JSON complet</Text>
            </Pressable>
          </View>
        )}

        {/* Footer explicatif */}
        <View style={styles.footerCard}>
          <Text style={styles.footerTitle}>🧠 Comment ça marche ?</Text>
          <Text style={styles.footerText}>
            Le modèle Pulse Energy Decay V2 combine vos données Oura (sommeil, récupération) 
            avec vos médicaments et conditions de santé pour prédire votre énergie tout au long de la journée.
          </Text>
          <Text style={[styles.footerText, { marginTop: 12 }]}>
            Chaque facteur a un impact mesuré scientifiquement, et le système apprend de vos feedbacks 
            pour s'adapter à VOTRE corps spécifiquement.
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#9CA3AF',
    fontSize: 16,
    marginTop: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1F1F1F',
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#1F1F1F',
    justifyContent: 'center',
    alignItems: 'center',
  },
  backButtonText: {
    color: '#FFFFFF',
    fontSize: 24,
    fontWeight: '600',
  },
  headerTitle: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
    flex: 1,
    textAlign: 'center',
  },
  debugButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#1F1F1F',
    justifyContent: 'center',
    alignItems: 'center',
  },
  debugButtonText: {
    fontSize: 20,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  scoreCard: {
    backgroundColor: '#1F1F1F',
    borderRadius: 20,
    padding: 24,
    alignItems: 'center',
    marginBottom: 20,
  },
  scoreLabel: {
    color: '#9CA3AF',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  scoreValue: {
    color: '#8B5CF6',
    fontSize: 64,
    fontWeight: '800',
    marginBottom: 8,
  },
  scoreSubtitle: {
    color: '#6B7280',
    fontSize: 16,
  },
  chartCard: {
    backgroundColor: '#1F1F1F',
    borderRadius: 20,
    padding: 20,
    marginBottom: 20,
  },
  sectionTitle: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 16,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  chartCaption: {
    color: '#6B7280',
    fontSize: 12,
    textAlign: 'center',
    marginTop: 8,
  },
  balanceCard: {
    backgroundColor: '#1F1F1F',
    borderRadius: 20,
    padding: 20,
    marginBottom: 20,
  },
  balanceBar: {
    flexDirection: 'row',
    height: 60,
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 16,
  },
  balancePositive: {
    backgroundColor: '#10B981',
    justifyContent: 'center',
    alignItems: 'center',
  },
  balanceNegative: {
    backgroundColor: '#EF4444',
    justifyContent: 'center',
    alignItems: 'center',
  },
  balanceText: {
    color: '#FFFFFF',
    fontSize: 20,
    fontWeight: '700',
  },
  balanceStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  balanceStat: {
    alignItems: 'center',
  },
  balanceStatLabel: {
    color: '#9CA3AF',
    fontSize: 12,
    marginBottom: 4,
  },
  balanceStatValue: {
    fontSize: 24,
    fontWeight: '700',
  },
  influencersCard: {
    backgroundColor: '#1F1F1F',
    borderRadius: 20,
    padding: 20,
    marginBottom: 20,
  },
  influencerCategory: {
    color: '#9CA3AF',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 12,
  },
  influencerItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    borderRadius: 12,
    marginBottom: 8,
  },
  influencerPositive: {
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    borderLeftWidth: 3,
    borderLeftColor: '#10B981',
  },
  influencerNegative: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    borderLeftWidth: 3,
    borderLeftColor: '#EF4444',
  },
  influencerName: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '500',
    flex: 1,
  },
  influencerImpact: {
    fontSize: 16,
    fontWeight: '700',
  },
  notesCard: {
    backgroundColor: '#1F1F1F',
    borderRadius: 20,
    padding: 20,
    marginBottom: 20,
  },
  noteItem: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  noteBullet: {
    color: '#8B5CF6',
    fontSize: 16,
    marginRight: 8,
    marginTop: 2,
  },
  noteText: {
    color: '#D1D5DB',
    fontSize: 14,
    lineHeight: 20,
    flex: 1,
  },
  debugCard: {
    backgroundColor: '#1F1F1F',
    borderRadius: 20,
    padding: 20,
    marginBottom: 20,
    borderWidth: 2,
    borderColor: '#8B5CF6',
  },
  debugSection: {
    marginBottom: 12,
  },
  debugLabel: {
    color: '#9CA3AF',
    fontSize: 12,
    marginBottom: 4,
  },
  debugValue: {
    color: '#FFFFFF',
    fontSize: 14,
    fontFamily: 'monospace',
  },
  jsonButton: {
    backgroundColor: '#8B5CF6',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 12,
  },
  jsonButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  footerCard: {
    backgroundColor: '#1F1F1F',
    borderRadius: 20,
    padding: 20,
  },
  footerTitle: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 12,
  },
  footerText: {
    color: '#9CA3AF',
    fontSize: 14,
    lineHeight: 20,
  },
});
