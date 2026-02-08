import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { router } from 'expo-router';
import { ChevronLeft, TrendingUp, RefreshCw } from 'lucide-react-native';
import { useHealthData } from '@/hooks/useHealthData';
import { useBaselines } from '@/hooks/useBaselines';
import BaselineCard from '@/components/BaselineCard';

export default function BaselinesScreen() {
  const { userProfile, loadingUserProfile, fetchUserProfile } = useHealthData();
  const [recalculating, setRecalculating] = useState(false);
  
  // Baselines personnelles
  const { baselines, loading: loadingBaselines, triggerRecalculation } = useBaselines(userProfile?.id || null);

  // Load profile on mount
  useEffect(() => {
    fetchUserProfile();
  }, [fetchUserProfile]);

  const handleRecalculateBaselines = async () => {
    if (recalculating) return;
    
    setRecalculating(true);
    const success = await triggerRecalculation();
    setRecalculating(false);
    
    if (success) {
      Alert.alert('Succès', 'Les baselines ont été recalculées.');
    } else {
      Alert.alert('Erreur', 'Impossible de recalculer les baselines.');
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.headerButton}
          onPress={() => router.back()}
        >
          <ChevronLeft size={28} color="#FFFFFF" strokeWidth={2.5} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Normalisation</Text>
        <View style={styles.headerButton} />
      </View>

      <ScrollView 
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {/* Info Card */}
        <View style={styles.infoCard}>
          <View style={styles.infoIconContainer}>
            <TrendingUp size={32} color="#7B6CF6" strokeWidth={2.5} />
          </View>
          <Text style={styles.infoTitle}>Métriques Personnalisées</Text>
          <Text style={styles.infoDescription}>
            Vos valeurs de référence sont calculées automatiquement à partir de vos données des 30 derniers jours. Elles permettent une analyse plus précise de votre état de santé.
          </Text>
        </View>

        {/* Stats Overview */}
        {baselines && baselines.length > 0 && !loadingBaselines && (
          <View style={styles.statsContainer}>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>{baselines.length}</Text>
              <Text style={styles.statLabel}>Métriques</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>30j</Text>
              <Text style={styles.statLabel}>Période</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>Auto</Text>
              <Text style={styles.statLabel}>Calcul</Text>
            </View>
          </View>
        )}

        {/* Baselines List */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Vos Baselines</Text>
          
          {loadingBaselines || loadingUserProfile ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#7B6CF6" />
              <Text style={styles.loadingText}>Chargement des baselines...</Text>
            </View>
          ) : baselines && baselines.length > 0 ? (
            <>
              <View style={styles.baselinesGrid}>
                {baselines.map((baseline) => (
                  <BaselineCard key={baseline.baseline_type} baseline={baseline} />
                ))}
              </View>
              
              {/* Recalculate Button */}
              <TouchableOpacity
                style={[styles.recalculateButton, recalculating && styles.recalculateButtonDisabled]}
                onPress={handleRecalculateBaselines}
                disabled={recalculating}
                activeOpacity={0.8}
              >
                {recalculating ? (
                  <ActivityIndicator size="small" color="#FFFFFF" />
                ) : (
                  <RefreshCw size={20} color="#FFFFFF" strokeWidth={2.5} />
                )}
                <Text style={styles.recalculateButtonText}>
                  {recalculating ? 'Recalcul en cours...' : 'Recalculer maintenant'}
                </Text>
              </TouchableOpacity>
              
              <View style={styles.infoBox}>
                <Text style={styles.infoBoxText}>
                  💡 Les baselines sont automatiquement recalculées chaque nuit avec vos nouvelles données.
                </Text>
              </View>
            </>
          ) : (
            <View style={styles.emptyState}>
              <View style={styles.emptyIconContainer}>
                <TrendingUp size={48} color="#FFFFFF40" strokeWidth={2} />
              </View>
              <Text style={styles.emptyTitle}>Aucune baseline disponible</Text>
              <Text style={styles.emptyDescription}>
                Continuez à enregistrer vos données de santé pendant quelques jours pour générer vos baselines personnelles.
              </Text>
            </View>
          )}
        </View>

        {/* How it works */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Comment ça marche ?</Text>
          
          <View style={styles.howItWorksCard}>
            <View style={styles.stepContainer}>
              <View style={styles.stepNumber}>
                <Text style={styles.stepNumberText}>1</Text>
              </View>
              <View style={styles.stepContent}>
                <Text style={styles.stepTitle}>Collecte des données</Text>
                <Text style={styles.stepDescription}>
                  Vos métriques de santé sont collectées via votre wearable
                </Text>
              </View>
            </View>

            <View style={styles.stepDivider} />

            <View style={styles.stepContainer}>
              <View style={styles.stepNumber}>
                <Text style={styles.stepNumberText}>2</Text>
              </View>
              <View style={styles.stepContent}>
                <Text style={styles.stepTitle}>Analyse statistique</Text>
                <Text style={styles.stepDescription}>
                  Calcul de la moyenne et de l'écart-type sur 30 jours
                </Text>
              </View>
            </View>

            <View style={styles.stepDivider} />

            <View style={styles.stepContainer}>
              <View style={styles.stepNumber}>
                <Text style={styles.stepNumberText}>3</Text>
              </View>
              <View style={styles.stepContent}>
                <Text style={styles.stepTitle}>Normalisation</Text>
                <Text style={styles.stepDescription}>
                  Vos valeurs sont comparées à votre baseline personnelle
                </Text>
              </View>
            </View>
          </View>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0D0D1F',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
  },
  headerButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 0.3,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    paddingHorizontal: 20,
    paddingBottom: 40,
  },
  infoCard: {
    backgroundColor: '#7B6CF620',
    borderRadius: 24,
    padding: 24,
    alignItems: 'center',
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#7B6CF640',
  },
  infoIconContainer: {
    width: 64,
    height: 64,
    backgroundColor: '#7B6CF640',
    borderRadius: 32,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  infoTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 12,
    textAlign: 'center',
    letterSpacing: 0.3,
  },
  infoDescription: {
    fontSize: 14,
    fontWeight: '500',
    color: '#FFFFFF80',
    textAlign: 'center',
    lineHeight: 20,
  },
  statsContainer: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 32,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#1A1A2E',
    borderRadius: 20,
    padding: 20,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#FFFFFF10',
  },
  statValue: {
    fontSize: 24,
    fontWeight: '800',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF60',
    textAlign: 'center',
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 16,
    letterSpacing: 0.3,
  },
  loadingContainer: {
    backgroundColor: '#1A1A2E',
    borderRadius: 20,
    padding: 48,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#FFFFFF10',
  },
  loadingText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF60',
    marginTop: 16,
  },
  baselinesGrid: {
    gap: 12,
  },
  recalculateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#7B6CF6',
    borderRadius: 20,
    paddingVertical: 18,
    gap: 12,
    marginTop: 24,
    marginBottom: 16,
  },
  recalculateButtonDisabled: {
    opacity: 0.5,
  },
  recalculateButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 0.3,
  },
  infoBox: {
    backgroundColor: '#FFB80020',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#FFB80040',
  },
  infoBoxText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#FFB800',
    lineHeight: 19,
  },
  emptyState: {
    backgroundColor: '#1A1A2E',
    borderRadius: 24,
    padding: 48,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#FFFFFF10',
    borderStyle: 'dashed',
  },
  emptyIconContainer: {
    width: 96,
    height: 96,
    backgroundColor: '#FFFFFF10',
    borderRadius: 48,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 12,
    textAlign: 'center',
  },
  emptyDescription: {
    fontSize: 14,
    fontWeight: '500',
    color: '#FFFFFF60',
    textAlign: 'center',
    lineHeight: 20,
  },
  howItWorksCard: {
    backgroundColor: '#1A1A2E',
    borderRadius: 20,
    padding: 24,
    borderWidth: 1,
    borderColor: '#FFFFFF10',
  },
  stepContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 16,
  },
  stepNumber: {
    width: 40,
    height: 40,
    backgroundColor: '#7B6CF6',
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepNumberText: {
    fontSize: 18,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  stepContent: {
    flex: 1,
    paddingTop: 4,
  },
  stepTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 6,
    letterSpacing: 0.2,
  },
  stepDescription: {
    fontSize: 14,
    fontWeight: '500',
    color: '#FFFFFF60',
    lineHeight: 20,
  },
  stepDivider: {
    height: 24,
    width: 2,
    backgroundColor: '#FFFFFF10',
    marginLeft: 19,
    marginVertical: 8,
  },
});
