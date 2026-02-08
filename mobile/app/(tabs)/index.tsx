/**
 * Page d'Accueil - Brief Quotidien
 * 
 * Cette page affiche le briefing quotidien avec:
 * - Score Pulse révolutionnaire
 * - Cartes triées par pertinence
 * - Animations Smooth Stack
 * - État vide intelligent
 */

import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as Haptics from 'expo-haptics';
import { useAuth } from '../../src/hooks/useAuth';
import { useProfile } from '../../src/hooks/useProfile';
import { useBriefData } from '../../src/hooks/useBriefData';
import { BriefStack } from '../../src/components/BriefStack';
import { FeedbackBottomSheet } from '../../src/components/FeedbackBottomSheet';
import { useFeedback } from '../../src/hooks/useFeedback';

export default function HomeScreen() {
  const { userId, loading: authLoading } = useAuth();
  const { data: profile, isLoading: profileLoading } = useProfile(userId);
  const { data: briefData, isLoading: briefLoading, refetch } = useBriefData(userId);
  
  const [refreshing, setRefreshing] = React.useState(false);

  // Extraire les données du forecast pour le système ML
  const forecast = briefData?.intraday_energy_forecast;
  const currentEnergy = forecast?.current_energy || 0;
  const systemScore = currentEnergy; // Score système = énergie courante

  // Calculer les heures depuis le réveil (estimation: 8h par défaut)
  const calculateHoursSinceWake = () => {
    const now = new Date();
    const wakeTime = new Date(now);
    wakeTime.setHours(8, 0, 0, 0); // 8h par défaut
    
    if (now < wakeTime) {
      wakeTime.setDate(wakeTime.getDate() - 1);
    }
    
    return (now.getTime() - wakeTime.getTime()) / (1000 * 60 * 60);
  };

  // Extraire les facteurs actifs depuis le forecast
  const extractActiveFactors = () => {
    if (!forecast?.influencers) return { medications: [], conditions: [] };

    const medications = forecast.influencers
      .filter((inf: any) => inf.name.startsWith('💊'))
      .map((inf: any) => {
        const name = inf.name.replace('💊 ', '');
        return {
          atc_code: 'UNKNOWN', // On ne l'a pas directement, mais le backend le récupérera
          name: name,
          impact: parseInt(inf.impact) || 0,
        };
      });

    const conditions = forecast.influencers
      .filter((inf: any) => 
        inf.name.includes('Dépression') || 
        inf.name.includes('TDAH') || 
        inf.name.includes('Fatigue')
      )
      .map((inf: any) => {
        const name = inf.name.replace(/^[😔🧠⚡] /, '');
        return {
          icd11_code: 'UNKNOWN', // Sera récupéré par le backend
          name: name,
          decay_rate: 0,
          malus: parseInt(inf.impact) || 0,
        };
      });

    return { medications, conditions };
  };

  // Hook de feedback ML
  const {
    showFeedbackSheet,
    feedbackContext,
    handleSubmitFeedback,
    closeFeedbackSheet,
  } = useFeedback({
    userId,
    currentEnergy,
    systemScore,
    hoursSinceWake: calculateHoursSinceWake(),
    activeFactors: extractActiveFactors(),
  });

  // Handler de refresh avec feedback haptique premium
  const onRefresh = async () => {
    console.log('[HomeScreen] 🔄 Pull-to-refresh démarré');
    
    // Déclencher une vibration satisfaisante au début du refresh
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    
    setRefreshing(true);
    console.log('[HomeScreen] 📡 Appel refetch...');
    await refetch();
    console.log('[HomeScreen] ✅ Refetch terminé');
    setRefreshing(false);
    
    // Petite vibration de confirmation à la fin du refresh
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
  };

  // Format date
  const today = new Date();
  const formattedDate = today.toLocaleDateString('fr-FR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  });

  const firstName = profile?.full_name?.split(' ')[0] || 'Utilisateur';

  // Loading state initial
  if ((authLoading || profileLoading || briefLoading) && !briefData) {
    return (
      <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#00FF41" />
          <Text style={styles.loadingText}>Calcul de votre Brief...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      {/* Stack de cartes plein écran avec animations */}
      <BriefStack
        cards={briefData?.cards || []}
        pulseScore={briefData?.pulseScore || 0}
        loading={briefLoading}
        onRefresh={onRefresh}
        refreshing={refreshing}
      />

      {/* Feedback ML Adaptatif */}
      <FeedbackBottomSheet
        isVisible={showFeedbackSheet}
        onClose={closeFeedbackSheet}
        systemScore={systemScore}
        currentEnergy={currentEnergy}
        hoursSinceWake={calculateHoursSinceWake()}
        activeFactors={extractActiveFactors()}
        onSubmit={handleSubmitFeedback}
        feedbackContext={feedbackContext}
      />
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
    padding: 40,
    backgroundColor: '#000000',
  },
  loadingText: {
    color: '#8E8E93',
    fontSize: 16,
    fontWeight: '600',
    marginTop: 16,
  },
});
