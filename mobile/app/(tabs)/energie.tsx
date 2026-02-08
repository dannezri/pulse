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

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Pressable,
  Dimensions,
  Alert,
  Linking,
  Share,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { BarChart } from 'react-native-gifted-charts';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '../../src/hooks/useAuth';
import { useBriefData } from '../../src/hooks/useBriefData';
import { useFeedback } from '../../src/hooks/useFeedback';
import { useEnergyExplanation } from '../../src/hooks/useEnergyExplanation';
import { supabase } from '../../src/lib/supabase';
import * as Haptics from 'expo-haptics';
import { FeedbackSlider } from '../../src/components/FeedbackSlider';
import { useQueryClient } from '@tanstack/react-query';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// Helper pour rendre le texte Markdown avec styles
const renderMarkdownText = (text: string, styles: any) => {
  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];
  
  lines.forEach((line, lineIndex) => {
    // Titres (##, ###)
    if (line.startsWith('###')) {
      const title = line.replace(/^###\s*/, '');
      elements.push(
        <Text key={`h3-${lineIndex}`} style={styles.geminiSubtitle}>
          {parseInlineMarkdown(title, styles)}
        </Text>
      );
    } else if (line.startsWith('##')) {
      const title = line.replace(/^##\s*/, '');
      elements.push(
        <Text key={`h2-${lineIndex}`} style={styles.geminiTitle}>
          {parseInlineMarkdown(title, styles)}
        </Text>
      );
    }
    // Listes à puces (*, -)
    else if (line.match(/^\s*[\*\-]\s+/)) {
      const content = line.replace(/^\s*[\*\-]\s+/, '');
      elements.push(
        <View key={`li-${lineIndex}`} style={styles.geminiBulletItem}>
          <Text style={styles.geminiBulletPoint}>•</Text>
          <Text style={styles.geminiBulletText}>
            {parseInlineMarkdown(content, styles)}
          </Text>
        </View>
      );
    }
    // Ligne vide (paragraphe)
    else if (line.trim() === '') {
      elements.push(<View key={`space-${lineIndex}`} style={{ height: 12 }} />);
    }
    // Texte normal
    else if (line.trim() !== '') {
      elements.push(
        <Text key={`p-${lineIndex}`} style={styles.geminiRawText}>
          {parseInlineMarkdown(line, styles)}
        </Text>
      );
    }
  });
  
  return <>{elements}</>;
};

// Parser le Markdown inline (**gras**, emojis)
const parseInlineMarkdown = (text: string, styles: any): React.ReactNode[] => {
  const parts: React.ReactNode[] = [];
  let currentIndex = 0;
  
  // Regex pour détecter **texte en gras**
  const boldRegex = /\*\*(.+?)\*\*/g;
  let match;
  
  while ((match = boldRegex.exec(text)) !== null) {
    // Ajouter le texte avant le gras
    if (match.index > currentIndex) {
      parts.push(text.substring(currentIndex, match.index));
    }
    
    // Ajouter le texte en gras
    parts.push(
      <Text key={`bold-${match.index}`} style={styles.geminiBold}>
        {match[1]}
      </Text>
    );
    
    currentIndex = match.index + match[0].length;
  }
  
  // Ajouter le reste du texte
  if (currentIndex < text.length) {
    parts.push(text.substring(currentIndex));
  }
  
  return parts;
};

export default function EnergyAnalysisScreen() {
  const { userId } = useAuth();
  const { data: briefData, isLoading, refetch } = useBriefData(userId);
  const { submitFeedback } = useFeedback();
  const queryClient = useQueryClient();
  
  const { data: energyExplanation, isLoading: isLoadingExplanation, error: explanationError, refetch: refetchExplanation } = useEnergyExplanation({
    userId: userId || '',
    enabled: !!userId,
  });
  const [showDebugMode, setShowDebugMode] = useState(false);

  // 🔧 Force refetch when userId is available (to get fresh data after backend fix)
  useEffect(() => {
    if (userId && refetchExplanation) {
      console.log('[EnergyAnalysis] 🔄 Forcing fresh fetch of energy explanation...');
      // Invalider TOUTES les queries d'explication (y compris les anciennes versions)
      queryClient.invalidateQueries({ queryKey: ['energy', 'explanation'] });
      // Force refetch pour ignorer le cache
      setTimeout(() => {
        refetchExplanation();
      }, 100);
    }
  }, [userId, queryClient, refetchExplanation]);

  // Debug: Log energyExplanation changes
  useEffect(() => {
    console.log('[EnergyAnalysis] 🎯 energyExplanation:', {
      hasData: !!energyExplanation,
      isLoading: isLoadingExplanation,
      hasError: !!explanationError,
      error: explanationError?.message,
      cardsCount: energyExplanation?.cards?.length || 0,
      score: energyExplanation?.energyScore,
    });
    if (explanationError) {
      console.error('[EnergyAnalysis] ❌ Explanation error:', explanationError);
    }
  }, [energyExplanation, isLoadingExplanation, explanationError]);
  const [wakeTime, setWakeTime] = useState<number | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const [selectedBarIndex, setSelectedBarIndex] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<'today' | 'week'>('today');
  const feedbackShownRef = useRef(false); // Track si le feedback a déjà été montré dans cette session

  const forecast = briefData?.intraday_energy_forecast;

  // Debug: Afficher toutes les données reçues
  useEffect(() => {
    if (briefData) {
      console.log('[EnergyAnalysis] Full briefData:', JSON.stringify(briefData, null, 2));
      console.log('[EnergyAnalysis] Has forecast:', !!forecast);
      if (forecast) {
        console.log('[EnergyAnalysis] Forecast keys:', Object.keys(forecast));
        console.log('[EnergyAnalysis] Forecast type:', forecast.type);
        console.log('[EnergyAnalysis] Current energy:', forecast.current_energy);
        console.log('[EnergyAnalysis] Forecast curve length:', forecast.forecast_curve?.length);
        console.log('[EnergyAnalysis] Points length:', forecast.points?.length);
      }
    }
  }, [briefData, forecast]);

  // Afficher le FeedbackSlider après 15 secondes (UNE SEULE FOIS par session)
  useEffect(() => {
    // Ne montrer qu'une seule fois par session
    if (feedbackShownRef.current || !forecast) {
      return;
    }

    const timer = setTimeout(() => {
      if (!feedbackShownRef.current && !showFeedback) {
        console.log('[EnergyAnalysis] 💬 Affichage du FeedbackSlider (une seule fois)');
        setShowFeedback(true);
        feedbackShownRef.current = true; // Marquer comme montré
      }
    }, 15000); // 15 secondes

    return () => clearTimeout(timer);
  }, []); // ✅ Array vide = s'exécute UNE SEULE FOIS au montage

  // Réinitialiser la sélection de barre quand les données changent
  useEffect(() => {
    setSelectedBarIndex(null);
  }, [briefData]);

  // Récupérer l'heure de réveil depuis les données de sommeil
  useEffect(() => {
    if (!userId) return;
    
    const fetchWakeTime = async () => {
      const { data: biometrics } = await supabase
        .from('biometrics')
        .select('metadata')
        .eq('user_id', userId)
        .eq('metric_type', 'sleep_duration')
        .order('recorded_at', { ascending: false })
        .limit(1)
        .single();

      if (biometrics?.metadata?.bedtime_end) {
        const bedtimeEnd = new Date(biometrics.metadata.bedtime_end);
        setWakeTime(bedtimeEnd.getHours());
      } else {
        // Heure de réveil par défaut si non disponible
        setWakeTime(7);
      }
    };

    fetchWakeTime();
  }, [userId]);

  if (isLoading || !forecast) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#8B5CF6" />
          <Text style={styles.loadingText}>Analyse en cours...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Préparer les données pour le graphique - filtrer à partir de l'heure de réveil
  // Essayer forecast_curve ou points selon ce qui est disponible
  const allPoints = forecast.forecast_curve || forecast.points || [];
  const wakeHour = wakeTime !== null ? wakeTime : 7; // Par défaut 7h si non disponible
  
  console.log('[EnergyAnalysis] Total points:', allPoints.length, 'Wake hour:', wakeHour);
  console.log('[EnergyAnalysis] First point sample:', allPoints[0]);
  
  // Si aucune donnée, créer des données par défaut
  let chartData = [];
  // Utiliser 50% comme minimum si pulseScore est trop bas (< 30)
  const pulseScoreFallback = Math.max(briefData?.pulseScore ?? 50, 40);
  
  if (allPoints.length === 0) {
    // Générer des points par défaut de l'heure de réveil à 23h
    for (let hour = wakeHour; hour < 24; hour++) {
      chartData.push({
        value: pulseScoreFallback,
        label: `${hour}h`,
      });
    }
    console.log('[EnergyAnalysis] No forecast data, using pulseScore points:', pulseScoreFallback);
  } else {
    // Filtrer et mapper les vraies données
    const rawChartData = allPoints
      .filter((point: any) => {
        // Supporter les deux formats: point.time ou point.t
        const timeStr = point.time || point.t;
        if (!timeStr) return false;
        const pointTime = new Date(timeStr);
        const pointHour = pointTime.getHours();
        // Garder les points entre l'heure de réveil et 23h59
        return pointHour >= wakeHour && pointHour < 24;
      })
      .filter((_: any, i: number) => i % 2 === 0) // Prendre un point sur deux pour éviter la surcharge
      .map((point: any) => {
        const timeStr = point.time || point.t;
        const time = new Date(timeStr);
        const hours = time.getHours();
        // Supporter les deux formats: point.value ou point.energy
        let value = point.value ?? point.energy ?? 0;
        // Si la valeur est 0, utiliser le pulseScore comme fallback
        if (value === 0) {
          value = pulseScoreFallback;
        }
        return {
          value: value,
          label: `${hours}h`,
        };
      });
    
    chartData = rawChartData;
    
    console.log('[EnergyAnalysis] Filtered points:', chartData.length);
    if (chartData.length > 0) {
      console.log('[EnergyAnalysis] Sample chart data (with fallback):', chartData[0], chartData[chartData.length - 1]);
    }
  }
  
  // S'assurer qu'il y a au moins 2 points pour le graphique
  if (chartData.length < 2) {
    const defaultValue = currentEnergy || pulseScoreFallback;
    chartData = [
      { value: defaultValue, label: `${wakeHour}h` },
      { value: defaultValue, label: '23h' },
    ];
    console.log('[EnergyAnalysis] Using fallback with 2 points, value:', defaultValue);
  }

  // Support des deux formats: V2 (forecast_curve + current_energy) et V1 (points + energy)
  // Si energy est 0 pour tous les points, utiliser le pulseScore comme fallback
  const firstPointEnergy = forecast.points?.[0]?.energy ?? 0;
  const fallbackEnergy = briefData?.pulseScore ?? 50;
  const currentEnergy = forecast.current_energy ?? (firstPointEnergy > 0 ? firstPointEnergy : fallbackEnergy);
  const influencers = forecast.influencers || [];
  const notes = forecast.notes || [];
  const components = forecast.components || {};
  
  console.log('[EnergyAnalysis] Current energy:', currentEnergy);
  console.log('[EnergyAnalysis] Using pulseScore as fallback:', fallbackEnergy);
  console.log('[EnergyAnalysis] Has influencers:', influencers.length);
  console.log('[EnergyAnalysis] Has notes:', notes.length);
  console.log('[EnergyAnalysis] Has components:', Object.keys(components).length);

  // Calculer les statistiques
  const positiveInfluencers = influencers.filter((inf: any) => inf.status === 'positive');
  const negativeInfluencers = influencers.filter((inf: any) => inf.status === 'negative');

  const totalPositive = positiveInfluencers.reduce((sum: number, inf: any) => {
    return sum + Math.abs(parseInt(inf.impact) || 0);
  }, 0);

  const totalNegative = negativeInfluencers.reduce((sum: number, inf: any) => {
    return sum + Math.abs(parseInt(inf.impact) || 0);
  }, 0);

  // Fonction pour partager le rapport
  const shareReport = async () => {
    try {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      
      const currentDate = new Date().toLocaleDateString('fr-FR', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
      
      // Créer un rapport texte formaté
      let reportText = `⚡ RAPPORT ANALYSE ÉNERGÉTIQUE - PULSE\n`;
      reportText += `${'='.repeat(50)}\n\n`;
      reportText += `📅 ${currentDate}\n\n`;
      
      // Score actuel
      reportText += `🔋 ÉNERGIE ACTUELLE: ${Math.round(currentEnergy)}%\n`;
      reportText += `État: ${currentEnergy < 20 ? 'Repos nécessaire' : 
                  currentEnergy < 40 ? 'Énergie basse' : 
                  currentEnergy < 60 ? 'Énergie modérée' : 
                  currentEnergy < 80 ? 'Bonne énergie' : 'Énergie excellente'}\n\n`;
      
      // Composants
      if (Object.keys(components).length > 0) {
        reportText += `${'='.repeat(50)}\n`;
        reportText += `🧬 COMPOSANTS D'ÉNERGIE\n`;
        reportText += `${'='.repeat(50)}\n\n`;
        
        if (components.recovery !== undefined) {
          const recoveryPct = Math.round((components.recovery || 0) * 100);
          const recoveryStatus = (components.recovery || 0) > 0.6 ? 'Bonne' : (components.recovery || 0) > 0.4 ? 'Partielle' : 'Insuffisante';
          reportText += `🔋 Récupération: ${recoveryPct}% (${recoveryStatus})\n`;
        }
        
        if (components.sleep_debt !== undefined) {
          const debtPct = Math.round((1 - (components.sleep_debt || 0)) * 100);
          const debtStatus = (components.sleep_debt || 0) < 0.3 ? 'Aucune' : (components.sleep_debt || 0) < 0.6 ? 'Modérée' : 'Élevée';
          reportText += `😴 Dette de sommeil: ${debtPct}% (${debtStatus})\n`;
        }
        
        if (components.overtrain !== undefined) {
          const trainPct = Math.round((1 - (components.overtrain || 0)) * 100);
          const trainStatus = (components.overtrain || 0) < 0.4 ? 'Optimale' : (components.overtrain || 0) < 0.7 ? 'Élevée' : 'Surmenage';
          reportText += `💪 Charge d'entraînement: ${trainPct}% (${trainStatus})\n`;
        }
        
        reportText += `\n`;
      }
      
      // Influencers
      if (influencers.length > 0) {
        reportText += `${'='.repeat(50)}\n`;
        reportText += `🎯 FACTEURS D'INFLUENCE\n`;
        reportText += `${'='.repeat(50)}\n\n`;
        
        if (positiveInfluencers.length > 0) {
          reportText += `✅ Facteurs positifs:\n`;
          positiveInfluencers.forEach((inf: any) => {
            reportText += `  • ${inf.name}: ${inf.impact}\n`;
          });
          reportText += `\n`;
        }
        
        if (negativeInfluencers.length > 0) {
          reportText += `⚠️ Facteurs négatifs:\n`;
          negativeInfluencers.forEach((inf: any) => {
            reportText += `  • ${inf.name}: ${inf.impact}\n`;
          });
          reportText += `\n`;
        }
      }
      
      // Notes
      if (notes.length > 0) {
        reportText += `${'='.repeat(50)}\n`;
        reportText += `📝 NOTES EXPLICATIVES\n`;
        reportText += `${'='.repeat(50)}\n\n`;
        notes.forEach((note: string) => {
          reportText += `• ${note}\n`;
        });
        reportText += `\n`;
      }
      
      // Footer
      reportText += `${'='.repeat(50)}\n`;
      reportText += `⚡ Pulse - Coach énergétique personnalisé\n`;
      reportText += `Modèle: ${forecast.model_version || 'V1'}\n`;
      reportText += `\nCe rapport est basé sur tes données Oura,\n`;
      reportText += `médicaments et conditions de santé.\n`;
      reportText += `Les prédictions sont personnalisées via ML.\n`;
      
      // Partager via l'API native
      const result = await Share.share({
        message: reportText,
        title: 'Mon Rapport Énergétique Pulse',
      });
      
      if (result.action === Share.sharedAction) {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      }
    } catch (error) {
      console.error('[EnergyAnalysis] Erreur partage:', error);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      Alert.alert(
        'Erreur',
        'Impossible de partager le rapport. Veuillez réessayer.',
        [{ text: 'OK' }]
      );
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Analyse Énergétique</Text>
        <View style={styles.headerButtons}>
          <Pressable
            style={styles.shareButton}
            onPress={shareReport}
          >
            <Text style={styles.shareButtonText}>📤</Text>
          </Pressable>
          <Pressable
            style={[styles.refreshButton, isRefreshing && styles.refreshButtonActive]}
            onPress={async () => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
              setIsRefreshing(true);
              setSelectedBarIndex(null); // Réinitialiser la sélection
              try {
                await refetch();
                Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
              } catch (error) {
                console.error('[EnergyAnalysis] Refresh error:', error);
                Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
              } finally {
                setTimeout(() => setIsRefreshing(false), 500);
              }
            }}
            disabled={isRefreshing}
          >
            <Text style={styles.refreshButtonText}>🔄</Text>
          </Pressable>
          <Pressable
            style={styles.debugButton}
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
              setShowDebugMode(!showDebugMode);
            }}
          >
            <Text style={styles.debugButtonText}>{showDebugMode ? '✓' : '🔬'}</Text>
          </Pressable>
          <Pressable
            style={[styles.debugButton, { backgroundColor: '#FF9500' }]}
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
              console.log('[EnergyAnalysis] 🧹 CLEARING ENERGY CACHE ONLY...');
              // Vider uniquement le cache des données d'énergie (pas toute l'app)
              queryClient.invalidateQueries({ queryKey: ['energy'] });
              queryClient.invalidateQueries({ queryKey: ['briefData'] });
              // Forcer un refetch immédiat
              setTimeout(() => {
                refetchExplanation();
                refetch();
              }, 100);
            }}
          >
            <Text style={styles.debugButtonText}>🧹</Text>
          </Pressable>
        </View>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Graphique */}
        <View style={styles.chartCard}>
          {/* En-tête avec stat actuelle */}
          <View style={styles.statHeader}>
            <View style={styles.statHeaderTop}>
              <View style={styles.statTitleRow}>
                <Text style={styles.statHeaderTitle}>Overall stat</Text>
                <Pressable 
                  style={styles.menuButton}
                  onPress={() => {
                    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                  }}
                >
                  <Text style={styles.menuButtonText}>⋯</Text>
                </Pressable>
              </View>
              
              {/* Segment Control */}
              <View style={styles.segmentControl}>
                <Pressable
                  style={[
                    styles.segmentButton,
                    viewMode === 'today' && styles.segmentButtonActive
                  ]}
                  onPress={() => {
                    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                    setViewMode('today');
                  }}
                >
                  <Text style={[
                    styles.segmentButtonText,
                    viewMode === 'today' && styles.segmentButtonTextActive
                  ]}>Today</Text>
                </Pressable>
                
                <Pressable
                  style={[
                    styles.segmentButton,
                    viewMode === 'week' && styles.segmentButtonActive
                  ]}
                  onPress={() => {
                    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                    setViewMode('week');
                  }}
                >
                  <Text style={[
                    styles.segmentButtonText,
                    viewMode === 'week' && styles.segmentButtonTextActive
                  ]}>Week</Text>
                </Pressable>
              </View>
            </View>
            
            <View style={styles.currentStatContainer}>
              <Text style={styles.currentStatLabel}>Current Energy</Text>
              <Text style={styles.currentStatValue}>{Math.round(currentEnergy)}%</Text>
            </View>
          </View>
          
          {chartData.length > 0 ? (
            <>
              <ScrollView 
                horizontal 
                showsHorizontalScrollIndicator={false}
                style={styles.chartScrollView}
                contentContainerStyle={styles.chartContainer}
              >
                {(() => {
                  // Utiliser directement les vraies données de prédiction
                  const now = new Date();
                  const currentHour = now.getHours();
                  
                  // Afficher TOUTES les heures disponibles (pas d'échantillonnage)
                  const displayData = chartData;
                  
                  // Trouver l'index de l'heure actuelle ou la plus proche
                  let currentIndex = -1;
                  let minDiff = Infinity;
                  
                  displayData.forEach((point: any, index: number) => {
                    const hourMatch = point.label.match(/(\d+)h/);
                    if (hourMatch) {
                      const hour = parseInt(hourMatch[1]);
                      const diff = Math.abs(hour - currentHour);
                      if (diff < minDiff) {
                        minDiff = diff;
                        currentIndex = index;
                      }
                    }
                  });
                  
                  // Créer les barres avec les vraies valeurs de prédiction
                  const barData = displayData.map((point: any, index: number) => {
                    const isCurrentHour = index === currentIndex;
                    // Pour la barre actuelle, utiliser currentEnergy
                    const displayValue = isCurrentHour ? currentEnergy : point.value;
                    
                    // Afficher le badge soit sur la barre sélectionnée, soit sur la barre actuelle
                    const shouldShowBadge = selectedBarIndex !== null 
                      ? selectedBarIndex === index 
                      : isCurrentHour;
                    
                    return {
                      value: displayValue,
                      label: point.label,
                      frontColor: isCurrentHour ? '#10B981' : '#6B7280',
                      topLabelComponent: shouldShowBadge ? () => (
                        <View style={styles.barBadge}>
                          <Text style={styles.barBadgeText}>{Math.round(displayValue)}%</Text>
                        </View>
                      ) : undefined,
                      onPress: () => {
                        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                        // Si on clique sur la même barre, la désélectionner
                        setSelectedBarIndex(selectedBarIndex === index ? null : index);
                      },
                    };
                  });
                  
                  // Calculer la valeur maximale dans les données
                  const maxDataValue = Math.max(...barData.map(d => d.value), 0);
                  // Ajouter 10% de marge en haut pour le badge
                  const chartMaxValue = Math.ceil(maxDataValue * 1.15);
                  
                  // Configurer les dimensions pour afficher toutes les heures
                  const numBars = barData.length;
                  const barWidth = 24; // Largeur fixe par barre
                  const spacing = 6; // Espacement fixe entre barres
                  const totalWidth = (numBars * barWidth) + ((numBars - 1) * spacing) + 40; // +40 pour marges
                  const chartWidth = Math.max(SCREEN_WIDTH - 80, totalWidth);
                  
                  return (
                    <BarChart
                      data={barData}
                      width={chartWidth}
                      height={220}
                      barWidth={barWidth}
                      barBorderRadius={6}
                      spacing={spacing}
                      hideRules
                      hideYAxisText
                      hideAxesAndRules
                      yAxisColor="transparent"
                      xAxisColor="transparent"
                      xAxisLabelTextStyle={{ color: '#9CA3AF', fontSize: 10 }}
                      noOfSections={4}
                      maxValue={chartMaxValue}
                      backgroundColor="#1F1F1F"
                      initialSpacing={10}
                      endSpacing={10}
                    />
                  );
                })()}
              </ScrollView>
            </>
          ) : (
            <View style={styles.noDataContainer}>
              <Text style={styles.noDataText}>📊 Aucune donnée disponible</Text>
              <Text style={styles.noDataSubtext}>
                Les prédictions seront disponibles après synchronisation avec vos données de santé
              </Text>
            </View>
          )}
        </View>

        {/* Why this score? - Explication générée par Gemini 3 Pro */}
        {energyExplanation?.cards && energyExplanation.cards.length > 0 ? (
          <View style={styles.whyScoreCard}>
            <View style={styles.whyScoreHeader}>
              <Text style={styles.whyScoreTitle}>💡 Analyse de ton énergie</Text>
              <Text style={{ color: '#8B5CF6', fontSize: 11, fontWeight: '600' }}>
                Gemini 3 Pro
              </Text>
            </View>
            
            {/* Affichage du texte avec support Markdown */}
            {energyExplanation.cards.map((card: any, index: number) => {
              console.log('[EnergyAnalysis] 📄 Card content:', {
                index,
                type: card.type,
                title: card.title,
                textLength: card.text?.length || 0,
                textPreview: card.text?.substring(0, 100) || 'NO TEXT'
              });
              return (
                <View key={index}>
                  {renderMarkdownText(card.text || 'Pas de texte disponible', styles)}
                </View>
              );
            })}
          </View>
        ) : isLoadingExplanation ? (
          <View style={styles.whyScoreCard}>
            <View style={styles.whyScoreHeader}>
              <Text style={styles.whyScoreTitle}>💡 Pourquoi ce score ?</Text>
            </View>
            <View style={{ paddingVertical: 20, alignItems: 'center' }}>
              <ActivityIndicator size="small" color="#8B5CF6" />
              <Text style={{ color: '#9CA3AF', marginTop: 8, fontSize: 13 }}>
                🧠 Analyse en cours avec Gemini 3 Pro...
              </Text>
            </View>
          </View>
        ) : (() => {
          // Fallback: afficher texte statique si Gemini échoue
          let mainExplanation = '';
          let secondaryExplanation = '';
          const keyFactors: string[] = [];
          
          // Générer une explication complète et détaillée
          const energyScore = Math.round(currentEnergy);
          let energyLevel = '';
          let energyAdvice = '';
          
          // Déterminer le niveau d'énergie
          if (energyScore >= 80) {
            energyLevel = 'excellente';
            energyAdvice = 'Vous êtes au top de votre forme ! Profitez de cette énergie pour accomplir vos tâches importantes.';
          } else if (energyScore >= 60) {
            energyLevel = 'bonne';
            energyAdvice = 'Votre niveau d\'énergie est satisfaisant. Continuez à maintenir vos bonnes habitudes.';
          } else if (energyScore >= 40) {
            energyLevel = 'modérée';
            energyAdvice = 'Votre énergie est dans la moyenne. Pensez à optimiser votre récupération.';
          } else if (energyScore >= 20) {
            energyLevel = 'basse';
            energyAdvice = 'Votre corps a besoin de repos. Privilégiez des activités légères et la récupération.';
          } else {
            energyLevel = 'très basse';
            energyAdvice = 'Repos nécessaire. Écoutez votre corps et accordez-vous du temps pour récupérer.';
          }
          
          // Construire l'explication principale
          mainExplanation = `Votre énergie actuelle est ${energyLevel} avec un score de ${energyScore}%. ${energyAdvice}`;
          
          // Analyser les composants pour l'explication secondaire
          const componentDetails: string[] = [];
          
          if (components.recovery !== undefined) {
            const recoveryPct = Math.round((components.recovery || 0) * 100);
            let recoveryDesc = '';
            if (recoveryPct > 70) {
              recoveryDesc = `Votre récupération est excellente (${recoveryPct}%), ce qui booste significativement votre énergie.`;
            } else if (recoveryPct > 50) {
              recoveryDesc = `Votre récupération est correcte (${recoveryPct}%), mais pourrait être améliorée.`;
            } else {
              recoveryDesc = `Votre récupération est insuffisante (${recoveryPct}%), ce qui limite votre énergie disponible.`;
            }
            componentDetails.push(recoveryDesc);
            keyFactors.push(`Récupération ${recoveryPct}%`);
          }
          
          if (components.sleep_debt !== undefined) {
            const sleepQuality = Math.round((1 - (components.sleep_debt || 0)) * 100);
            let sleepDesc = '';
            if (sleepQuality > 70) {
              sleepDesc = `Votre sommeil est de qualité (${sleepQuality}%), vous avez bien récupéré.`;
            } else if (sleepQuality > 50) {
              sleepDesc = `Votre sommeil est acceptable (${sleepQuality}%), mais vous pourriez avoir une petite dette.`;
            } else {
              sleepDesc = `Vous avez accumulé une dette de sommeil importante (qualité: ${sleepQuality}%), ce qui affecte votre énergie.`;
            }
            componentDetails.push(sleepDesc);
            keyFactors.push(`Sommeil ${sleepQuality}%`);
          }
          
          if (components.overtrain !== undefined) {
            const trainOptimal = Math.round((1 - (components.overtrain || 0)) * 100);
            let trainDesc = '';
            if (trainOptimal > 70) {
              trainDesc = `Votre charge d'entraînement est bien équilibrée (${trainOptimal}%).`;
            } else if (trainOptimal > 50) {
              trainDesc = `Votre charge d'entraînement est légèrement élevée (${trainOptimal}%).`;
            } else {
              trainDesc = `Attention au surmenage : votre charge d'entraînement est trop élevée (${trainOptimal}%).`;
            }
            componentDetails.push(trainDesc);
            keyFactors.push(`Training ${trainOptimal}%`);
          }
          
          // Combiner les détails
          if (componentDetails.length > 0) {
            secondaryExplanation = componentDetails.join(' ');
          }
          
          // Ajouter les influencers positifs/négatifs
          if (influencers.length > 0) {
            const topPositive = positiveInfluencers.slice(0, 2);
            const topNegative = negativeInfluencers.slice(0, 2);
            
            const influencerParts: string[] = [];
            
            if (topPositive.length > 0) {
              const posNames = topPositive.map((inf: any) => inf.name).join(' et ');
              influencerParts.push(`Les facteurs positifs comme ${posNames} améliorent votre score`);
            }
            
            if (topNegative.length > 0) {
              const negNames = topNegative.map((inf: any) => inf.name).join(' et ');
              influencerParts.push(`${topNegative.length > 0 && topPositive.length > 0 ? 'tandis que' : 'Les facteurs négatifs comme'} ${negNames} ${topPositive.length > 0 ? 'le réduisent' : 'réduisent votre score'}`);
            }
            
            if (influencerParts.length > 0) {
              const influencerText = influencerParts.join(', ') + '.';
              secondaryExplanation = secondaryExplanation 
                ? `${secondaryExplanation} ${influencerText}`
                : influencerText;
            }
          }
          
          // Si toujours rien, ne rien afficher
          if (!mainExplanation) return null;
          
          return (
            <View style={styles.whyScoreCard}>
              <View style={styles.whyScoreHeader}>
                <Text style={styles.whyScoreTitle}>💡 Pourquoi ce score ?</Text>
                <Text style={{ color: '#F59E0B', fontSize: 11, marginLeft: 8 }}>(Fallback)</Text>
              </View>
              
              <Text style={styles.whyScoreText}>
                {mainExplanation}
              </Text>
              
              {secondaryExplanation && (
                <Text style={[styles.whyScoreText, { marginTop: 12, fontSize: 13, color: '#9CA3AF' }]}>
                  {secondaryExplanation}
                </Text>
              )}
              
              {keyFactors.length > 0 && (
                <View style={styles.whyScoreChips}>
                  {keyFactors.map((factor: string, index: number) => (
                    <View key={index} style={styles.whyScoreChip}>
                      <Text style={styles.whyScoreChipText}>
                        {factor}
                      </Text>
                    </View>
                  ))}
                </View>
              )}
            </View>
          );
        })()}

        {/* Balance énergétique - style horizontal */}
        <View style={styles.balanceCard}>
          <View style={styles.balanceMetricsRow}>
            {/* Énergie actuelle */}
            <View style={styles.balanceMetric}>
              <View style={styles.balanceMetricHeader}>
                <View style={[styles.balanceIndicator, { backgroundColor: '#8B5CF6' }]} />
                <Text style={styles.balanceMetricLabel}>Energy</Text>
              </View>
              <Text style={styles.balanceMetricValue}>
                {Math.round(currentEnergy)}
                <Text style={styles.balanceMetricUnit}> %</Text>
              </Text>
            </View>

            {/* Facteurs positifs */}
            <View style={styles.balanceMetric}>
              <View style={styles.balanceMetricHeader}>
                <View style={[styles.balanceIndicator, { backgroundColor: '#10B981' }]} />
                <Text style={styles.balanceMetricLabel}>Positive</Text>
              </View>
              <Text style={styles.balanceMetricValue}>
                {totalPositive}
                <Text style={styles.balanceMetricUnit}> pts</Text>
              </Text>
            </View>

            {/* Facteurs négatifs */}
            <View style={styles.balanceMetric}>
              <View style={styles.balanceMetricHeader}>
                <View style={[styles.balanceIndicator, { backgroundColor: '#EF4444' }]} />
                <Text style={styles.balanceMetricLabel}>Negative</Text>
              </View>
              <Text style={styles.balanceMetricValue}>
                {totalNegative}
                <Text style={styles.balanceMetricUnit}> pts</Text>
              </Text>
            </View>
          </View>
        </View>

        {/* Composants d'énergie */}
        {Object.keys(components).length > 0 && (
          <View style={styles.componentsCard}>
            <Text style={[styles.sectionTitle, { marginBottom: 16 }]}>🧬 Composants d'énergie</Text>
            
            {/* Recovery */}
            {components.recovery !== undefined && (
              <View style={styles.componentItem}>
                <View style={styles.componentHeader}>
                  <Text style={styles.componentLabel}>🔋 Récupération</Text>
                  <Text style={styles.componentValue}>{Math.round((components.recovery || 0) * 100)}%</Text>
                </View>
                <View style={styles.componentBarContainer}>
                  <View 
                    style={[
                      styles.componentBar, 
                      { 
                        width: `${(components.recovery || 0) * 100}%`,
                        backgroundColor: (components.recovery || 0) > 0.6 ? '#10B981' : (components.recovery || 0) > 0.4 ? '#F59E0B' : '#EF4444'
                      }
                    ]} 
                  />
                </View>
                <Text style={styles.componentDescription}>
                  {(components.recovery || 0) > 0.6 ? 'Bonne récupération' : (components.recovery || 0) > 0.4 ? 'Récupération partielle' : 'Récupération insuffisante'}
                </Text>
              </View>
            )}

            {/* Sleep Debt */}
            {components.sleep_debt !== undefined && (
              <View style={styles.componentItem}>
                <View style={styles.componentHeader}>
                  <Text style={styles.componentLabel}>😴 Dette de sommeil</Text>
                  <Text style={styles.componentValue}>{Math.round((1 - (components.sleep_debt || 0)) * 100)}%</Text>
                </View>
                <View style={styles.componentBarContainer}>
                  <View 
                    style={[
                      styles.componentBar, 
                      { 
                        width: `${(1 - (components.sleep_debt || 0)) * 100}%`,
                        backgroundColor: (components.sleep_debt || 0) < 0.3 ? '#10B981' : (components.sleep_debt || 0) < 0.6 ? '#F59E0B' : '#EF4444'
                      }
                    ]} 
                  />
                </View>
                <Text style={styles.componentDescription}>
                  {(components.sleep_debt || 0) < 0.3 ? 'Pas de dette' : (components.sleep_debt || 0) < 0.6 ? 'Dette modérée' : 'Dette élevée'}
                </Text>
              </View>
            )}

            {/* Overtrain */}
            {components.overtrain !== undefined && (
              <View style={styles.componentItem}>
                <View style={styles.componentHeader}>
                  <Text style={styles.componentLabel}>💪 Charge d'entraînement</Text>
                  <Text style={styles.componentValue}>{Math.round((1 - (components.overtrain || 0)) * 100)}%</Text>
                </View>
                <View style={styles.componentBarContainer}>
                  <View 
                    style={[
                      styles.componentBar, 
                      { 
                        width: `${(1 - (components.overtrain || 0)) * 100}%`,
                        backgroundColor: (components.overtrain || 0) < 0.4 ? '#10B981' : (components.overtrain || 0) < 0.7 ? '#F59E0B' : '#EF4444'
                      }
                    ]} 
                  />
                </View>
                <Text style={styles.componentDescription}>
                  {(components.overtrain || 0) < 0.4 ? 'Charge optimale' : (components.overtrain || 0) < 0.7 ? 'Charge élevée' : 'Surmenage détecté'}
                </Text>
              </View>
            )}
          </View>
        )}

        {/* Facteurs d'influence en grille */}
        <View style={styles.influencersSection}>
          <Text style={[styles.sectionTitle, { marginBottom: 16, paddingHorizontal: 20 }]}>Activity</Text>
          
          {influencers.length === 0 && Object.keys(components).length === 0 ? (
            <View style={[styles.noDataContainer, { marginHorizontal: 20 }]}>
              <Text style={styles.noDataText}>🔄 Analyse en cours</Text>
              <Text style={styles.noDataSubtext}>
                Les facteurs détaillés seront disponibles après l'analyse approfondie de vos données
              </Text>
            </View>
          ) : (
            <View style={styles.influencersGrid}>
              {(() => {
                const activityCards = [];
                
                // 1. Carte Recovery (depuis components)
                if (components.recovery !== undefined) {
                  const recoveryPercent = Math.round((components.recovery || 0) * 100);
                  activityCards.push({
                    name: 'Recovery',
                    icon: '🔋',
                    value: recoveryPercent.toString(),
                    unit: '%',
                    type: 'gauge',
                    percent: recoveryPercent,
                    color: recoveryPercent > 60 ? '#10B981' : recoveryPercent > 40 ? '#F59E0B' : '#EF4444'
                  });
                }
                
                // 2. Carte Sleep (depuis components.sleep_debt)
                if (components.sleep_debt !== undefined) {
                  const sleepQuality = Math.round((1 - (components.sleep_debt || 0)) * 100);
                  activityCards.push({
                    name: 'Sleep',
                    icon: '🌙',
                    value: sleepQuality.toString(),
                    unit: 'Quality',
                    type: 'gauge',
                    percent: sleepQuality,
                    color: sleepQuality > 70 ? '#10B981' : sleepQuality > 50 ? '#F59E0B' : '#EF4444'
                  });
                }
                
                // 3. Carte Training Load (depuis components.overtrain)
                if (components.overtrain !== undefined) {
                  const trainingOptimal = Math.round((1 - (components.overtrain || 0)) * 100);
                  activityCards.push({
                    name: 'Training',
                    icon: '💪',
                    value: trainingOptimal.toString(),
                    unit: 'Load',
                    type: 'gauge',
                    percent: trainingOptimal,
                    color: trainingOptimal > 60 ? '#10B981' : trainingOptimal > 40 ? '#F59E0B' : '#EF4444'
                  });
                }
                
                // 4. Carte Energy Trend (depuis chartData)
                if (chartData.length > 0) {
                  activityCards.push({
                    name: 'Energy',
                    icon: '⚡',
                    value: Math.round(currentEnergy).toString(),
                    unit: '%',
                    type: 'chart',
                    data: chartData,
                    color: '#8B5CF6'
                  });
                }
                
                // 5. Ajouter TOUS les influencers
                influencers.forEach((inf: any) => {
                  const isPositive = inf.status === 'positive';
                  const impactValue = parseInt(inf.impact?.replace(/[^0-9-]/g, '') || '0');
                  const absImpact = Math.abs(impactValue);
                  
                  activityCards.push({
                    name: inf.name,
                    icon: isPositive ? '✨' : '⚠️',
                    value: inf.impact,
                    unit: 'Impact',
                    type: 'progress',
                    percent: absImpact,
                    color: isPositive ? '#10B981' : '#EF4444'
                  });
                });
                
                // Assurer qu'on a au moins 4 cartes pour une grille équilibrée
                if (activityCards.length < 4) {
                  while (activityCards.length < 4) {
                    activityCards.push({
                      name: 'Coming Soon',
                      icon: '📊',
                      value: '--',
                      unit: 'Data',
                      type: 'value',
                      color: '#6B7280'
                    });
                  }
                }
                
                return activityCards.map((item, index) => {
                  return (
                    <View key={index} style={styles.influencerCard}>
                      <View style={styles.influencerCardHeader}>
                        <Text style={styles.influencerCardTitle}>{item.name}</Text>
                        <Text style={styles.influencerCardIcon}>{item.icon}</Text>
                      </View>
                      
                      <View style={styles.influencerCardContent}>
                        {item.type === 'chart' && item.data && (
                          <View style={styles.miniChartContainer}>
                            {/* Mini graphique courbe amélioré */}
                            <View style={styles.miniChart}>
                              {item.data.slice(0, 12).map((point: any, i: number) => {
                                const maxVal = Math.max(...item.data.slice(0, 12).map((p: any) => p.value));
                                const minVal = Math.min(...item.data.slice(0, 12).map((p: any) => p.value));
                                const range = maxVal - minVal;
                                // Normaliser entre 20% et 100% de la hauteur pour une meilleure visualisation
                                const normalizedHeight = range > 0 
                                  ? 20 + ((point.value - minVal) / range) * 24
                                  : 24;
                                
                                return (
                                  <View 
                                    key={i} 
                                    style={[
                                      styles.miniChartBar,
                                      { 
                                        height: normalizedHeight,
                                        backgroundColor: item.color || '#8B5CF6',
                                        opacity: 0.7 + (i / 12) * 0.3, // Gradient d'opacité
                                      }
                                    ]} 
                                  />
                                );
                              })}
                            </View>
                          </View>
                        )}
                        
                        {item.type === 'gauge' && (
                          <View style={styles.gaugeContainer}>
                            {/* Jauge simple: cercle avec pourcentage */}
                            <View style={styles.simpleGaugeCircle}>
                              {/* Fond du cercle */}
                              <View style={[
                                styles.simpleGaugeBackground,
                                { borderColor: '#333333' }
                              ]} />
                              
                              {/* Arc de progression coloré */}
                              <View style={[
                                styles.simpleGaugeForeground,
                                {
                                  borderColor: item.color || '#3B82F6',
                                  // Utiliser borderWidth pour simuler le remplissage
                                  borderTopWidth: (item.percent || 0) > 0 ? 6 : 0,
                                  borderRightWidth: (item.percent || 0) > 25 ? 6 : 0,
                                  borderBottomWidth: (item.percent || 0) > 50 ? 6 : 0,
                                  borderLeftWidth: (item.percent || 0) > 75 ? 6 : 0,
                                }
                              ]} />
                              
                              {/* Centre avec pourcentage */}
                              <View style={styles.simpleGaugeCenter}>
                                <Text style={styles.gaugePercentText}>
                                  {item.percent || 0}
                                </Text>
                                <Text style={styles.gaugePercentSymbol}>%</Text>
                              </View>
                            </View>
                          </View>
                        )}
                        
                        {item.type === 'progress' && (
                          <View style={styles.progressContainer}>
                            {/* Barres horizontales stylées */}
                            <View style={styles.progressBarsWrapper}>
                              {Array.from({ length: 5 }).map((_, i) => {
                                const barPercent = ((i + 1) / 5) * 100;
                                const isActive = barPercent <= (item.percent || 0);
                                
                                return (
                                  <View
                                    key={i}
                                    style={[
                                      styles.progressBarSegment,
                                      {
                                        backgroundColor: isActive 
                                          ? (item.color || '#8B5CF6')
                                          : '#333333',
                                        opacity: isActive ? 1 : 0.3,
                                      }
                                    ]}
                                  />
                                );
                              })}
                            </View>
                          </View>
                        )}
                        
                        <Text style={[
                          styles.influencerCardValue,
                          item.color && { color: item.color }
                        ]}>
                          {item.value}
                        </Text>
                        <Text style={styles.influencerCardUnit}>{item.unit}</Text>
                      </View>
                    </View>
                  );
                });
              })()}
            </View>
          )}
        </View>

        {/* Notes explicatives */}
        {notes.length > 0 && (
          <View style={styles.notesCard}>
            <Text style={[styles.sectionTitle, { marginBottom: 16 }]}>📝 Notes explicatives</Text>
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
            <Text style={[styles.sectionTitle, { marginBottom: 16 }]}>🔬 Mode Debug</Text>
            
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

            {/* Poids ML personnalisés */}
            {forecast.ml_weights && forecast.ml_weights.length > 0 && (
              <View style={styles.debugSection}>
                <Text style={[styles.debugLabel, { marginBottom: 8, fontSize: 14, fontWeight: '600' }]}>
                  🤖 Poids ML personnalisés ({forecast.ml_weights.length})
                </Text>
                {forecast.ml_weights.map((weight: any, index: number) => (
                  <View key={index} style={styles.mlWeightItem}>
                    <Text style={styles.mlWeightType}>
                      {weight.factor_type === 'medication' ? '💊' : '🏥'} {weight.factor_code}
                    </Text>
                    <Text style={styles.mlWeightValue}>
                      ×{weight.weight_multiplier.toFixed(2)}
                    </Text>
                  </View>
                ))}
                <Text style={styles.mlWeightNote}>
                  Ces multiplicateurs ajustent l'impact de chaque facteur selon tes feedbacks
                </Text>
              </View>
            )}

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

      {/* Feedback Slider ML */}
      {showFeedback && userId && forecast && submitFeedback && (
        <FeedbackSlider
          systemScore={currentEnergy || 0}
          activeMedications={
            forecast.influencers
              ?.filter((i: any) => i.type === 'medication')
              .map((i: any) => i.code) || []
          }
          activeConditions={
            forecast.influencers
              ?.filter((i: any) => i.type === 'condition')
              .map((i: any) => i.code) || []
          }
          onSubmit={async (userScore: number) => {
            console.log('[EnergyAnalysis] 📤 onSubmit appelé avec userScore:', userScore);
            try {
              const result = await submitFeedback({
                user_id: userId,
                system_score: currentEnergy || 0,
                user_score: userScore,
                active_factors: {
                  medications:
                    forecast.influencers
                      ?.filter((i: any) => i.type === 'medication')
                      .map((i: any) => i.code) || [],
                  conditions:
                    forecast.influencers
                      ?.filter((i: any) => i.type === 'condition')
                      .map((i: any) => i.code) || [],
                },
              });
              console.log('[EnergyAnalysis] ✅ Feedback result:', result);
              Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
            } catch (error) {
              console.error('[EnergyAnalysis] ❌ Erreur feedback:', error);
            }
          }}
          onDismiss={() => {
            console.log('[EnergyAnalysis] 👋 FeedbackSlider dismissed');
            setShowFeedback(false);
          }}
        />
      )}
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
  headerTitle: {
    color: '#FFFFFF',
    fontSize: 24,
    fontWeight: '700',
    flex: 1,
  },
  headerButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  shareButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#1F1F1F',
    justifyContent: 'center',
    alignItems: 'center',
  },
  shareButtonText: {
    fontSize: 20,
  },
  refreshButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#1F1F1F',
    justifyContent: 'center',
    alignItems: 'center',
  },
  refreshButtonActive: {
    backgroundColor: '#8B5CF6',
  },
  refreshButtonText: {
    fontSize: 20,
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
    paddingBottom: 100,
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
  warningBadge: {
    marginTop: 12,
    backgroundColor: 'rgba(255, 149, 0, 0.1)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 149, 0, 0.3)',
  },
  warningText: {
    color: '#FF9500',
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
  },
  chartCard: {
    backgroundColor: '#1F1F1F',
    borderRadius: 20,
    padding: 20,
    marginBottom: 20,
  },
  chartHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
  },
  wakeTimeLabel: {
    color: '#8B5CF6',
    fontSize: 12,
    fontWeight: '600',
    backgroundColor: 'rgba(139, 92, 246, 0.1)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  chartScrollView: {
    marginVertical: 8,
  },
  chartContainer: {
    paddingLeft: 10,
  },
  chartCaption: {
    color: '#6B7280',
    fontSize: 12,
    textAlign: 'center',
    marginTop: 8,
  },
  noDataContainer: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  noDataText: {
    color: '#9CA3AF',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  noDataSubtext: {
    color: '#6B7280',
    fontSize: 13,
    textAlign: 'center',
    paddingHorizontal: 20,
    lineHeight: 20,
  },
  balanceCard: {
    backgroundColor: '#1F1F1F',
    borderRadius: 20,
    padding: 20,
    marginBottom: 20,
  },
  balanceMetricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  balanceMetric: {
    flex: 1,
  },
  balanceMetricHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  balanceIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  balanceMetricLabel: {
    color: '#9CA3AF',
    fontSize: 12,
    fontWeight: '500',
  },
  balanceMetricValue: {
    color: '#FFFFFF',
    fontSize: 24,
    fontWeight: '700',
  },
  balanceMetricUnit: {
    color: '#6B7280',
    fontSize: 12,
    fontWeight: '600',
  },
  whyScoreCard: {
    backgroundColor: '#1F1F1F',
    borderRadius: 20,
    padding: 20,
    marginBottom: 20,
  },
  whyScoreHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  whyScoreTitle: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  whyScoreText: {
    color: '#D1D5DB',
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 16,
  },
  whyScoreChips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  whyScoreChip: {
    backgroundColor: '#2A2A2A',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#3A3A3A',
  },
  whyScoreChipText: {
    color: '#9CA3AF',
    fontSize: 12,
    fontWeight: '600',
  },
  geminiCardSection: {
    marginBottom: 20,
  },
  geminiCardTitle: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 10,
    lineHeight: 22,
  },
  geminiCardText: {
    color: '#D1D5DB',
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 12,
  },
  geminiRawText: {
    color: '#E5E7EB',
    fontSize: 15,
    lineHeight: 24,
    marginTop: 4,
  },
  geminiTitle: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
    marginTop: 16,
    marginBottom: 8,
    lineHeight: 24,
  },
  geminiSubtitle: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
    marginTop: 12,
    marginBottom: 6,
    lineHeight: 22,
  },
  geminiBold: {
    fontWeight: '700',
    color: '#FFFFFF',
  },
  geminiBulletItem: {
    flexDirection: 'row',
    marginTop: 6,
    marginLeft: 8,
  },
  geminiBulletPoint: {
    color: '#8B5CF6',
    fontSize: 15,
    marginRight: 8,
    fontWeight: '700',
  },
  geminiBulletText: {
    flex: 1,
    color: '#E5E7EB',
    fontSize: 15,
    lineHeight: 24,
  },
  geminiMetricsRow: {
    flexDirection: 'row',
    gap: 16,
    marginBottom: 12,
    paddingVertical: 10,
    paddingHorizontal: 12,
    backgroundColor: '#2A2A2A',
    borderRadius: 12,
  },
  geminiMetric: {
    flex: 1,
  },
  geminiMetricLabel: {
    color: '#9CA3AF',
    fontSize: 11,
    fontWeight: '500',
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  geminiMetricValue: {
    color: '#8B5CF6',
    fontSize: 18,
    fontWeight: '700',
  },
  geminiAnalogyBox: {
    flexDirection: 'row',
    backgroundColor: 'rgba(139, 92, 246, 0.1)',
    borderLeftWidth: 3,
    borderLeftColor: '#8B5CF6',
    padding: 12,
    borderRadius: 8,
    marginTop: 4,
  },
  geminiAnalogyIcon: {
    fontSize: 16,
    marginRight: 8,
    marginTop: 2,
  },
  geminiAnalogyText: {
    flex: 1,
    color: '#C4B5FD',
    fontSize: 13,
    lineHeight: 20,
    fontStyle: 'italic',
  },
  geminiCardDivider: {
    height: 1,
    backgroundColor: '#2A2A2A',
    marginTop: 20,
  },
  componentsCard: {
    backgroundColor: '#1F1F1F',
    borderRadius: 20,
    padding: 20,
    marginBottom: 20,
  },
  componentItem: {
    marginBottom: 20,
  },
  componentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  componentLabel: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
  },
  componentValue: {
    color: '#8B5CF6',
    fontSize: 16,
    fontWeight: '700',
  },
  componentBarContainer: {
    height: 8,
    backgroundColor: '#333333',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 6,
  },
  componentBar: {
    height: '100%',
    borderRadius: 4,
  },
  componentDescription: {
    color: '#9CA3AF',
    fontSize: 12,
    fontStyle: 'italic',
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
  mlWeightItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#2A2A2A',
    padding: 10,
    borderRadius: 8,
    marginBottom: 6,
  },
  mlWeightType: {
    color: '#D1D5DB',
    fontSize: 13,
    fontFamily: 'monospace',
  },
  mlWeightValue: {
    color: '#8B5CF6',
    fontSize: 13,
    fontWeight: '700',
    fontFamily: 'monospace',
  },
  mlWeightNote: {
    color: '#6B7280',
    fontSize: 11,
    marginTop: 8,
    fontStyle: 'italic',
    lineHeight: 16,
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
  statHeader: {
    marginBottom: 24,
  },
  statHeaderTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  statTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statHeaderTitle: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  menuButton: {
    width: 24,
    height: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  menuButtonText: {
    color: '#9CA3AF',
    fontSize: 20,
    fontWeight: '700',
    transform: [{ rotate: '90deg' }],
  },
  segmentControl: {
    flexDirection: 'row',
    backgroundColor: '#2A2A2A',
    borderRadius: 12,
    padding: 3,
  },
  segmentButton: {
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 9,
  },
  segmentButtonActive: {
    backgroundColor: '#FF6B9D',
  },
  segmentButtonText: {
    color: '#9CA3AF',
    fontSize: 12,
    fontWeight: '600',
  },
  segmentButtonTextActive: {
    color: '#FFFFFF',
  },
  currentStatContainer: {
    alignItems: 'flex-start',
    paddingLeft: 4,
  },
  currentStatLabel: {
    color: '#9CA3AF',
    fontSize: 13,
    fontWeight: '500',
    marginBottom: 4,
  },
  currentStatValue: {
    color: '#FFFFFF',
    fontSize: 48,
    fontWeight: '700',
    letterSpacing: -1,
  },
  barBadge: {
    backgroundColor: '#10B981',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    marginBottom: 4,
    alignSelf: 'center',
  },
  barBadgeText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '700',
  },
  influencersSection: {
    marginBottom: 20,
  },
  influencersGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 15,
    justifyContent: 'space-between',
  },
  influencerCard: {
    width: '48%',
    backgroundColor: '#1F1F1F',
    borderRadius: 20,
    padding: 16,
    marginBottom: 12,
    minHeight: 140,
  },
  influencerCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  influencerCardTitle: {
    color: '#9CA3AF',
    fontSize: 12,
    fontWeight: '600',
  },
  influencerCardIcon: {
    fontSize: 16,
  },
  influencerCardContent: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  influencerCardValue: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FFFFFF',
    marginTop: 8,
  },
  influencerCardUnit: {
    fontSize: 11,
    color: '#6B7280',
    marginTop: 2,
  },
  miniChartContainer: {
    height: 50,
    marginBottom: 8,
  },
  miniChart: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    height: '100%',
    paddingVertical: 6,
    gap: 2,
  },
  miniChartBar: {
    flex: 1,
    borderRadius: 2,
    minHeight: 4,
  },
  gaugeContainer: {
    height: 70,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  simpleGaugeCircle: {
    width: 64,
    height: 64,
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
  },
  simpleGaugeBackground: {
    position: 'absolute',
    width: 64,
    height: 64,
    borderRadius: 32,
    borderWidth: 6,
  },
  simpleGaugeForeground: {
    position: 'absolute',
    width: 64,
    height: 64,
    borderRadius: 32,
    borderWidth: 0,
    transform: [{ rotate: '-45deg' }],
  },
  simpleGaugeCenter: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#1F1F1F',
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 1,
  },
  gaugePercentText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  gaugePercentSymbol: {
    color: '#9CA3AF',
    fontSize: 11,
    fontWeight: '600',
    marginTop: 2,
  },
  influencerProgressContainer: {
    height: 6,
    backgroundColor: '#333333',
    borderRadius: 3,
    overflow: 'hidden',
  },
  influencerProgress: {
    height: '100%',
    borderRadius: 3,
  },
  progressContainer: {
    height: 50,
    justifyContent: 'center',
    marginBottom: 8,
  },
  progressBarsWrapper: {
    flexDirection: 'row',
    gap: 4,
    height: 24,
    alignItems: 'center',
  },
  progressBarSegment: {
    flex: 1,
    height: 6,
    borderRadius: 3,
  },
});
