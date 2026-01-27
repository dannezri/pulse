import React, { useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  Dimensions,
  ActivityIndicator,
  TouchableOpacity,
  Platform,
  Alert,
} from 'react-native';
import { useHealthData } from '@/src/hooks/useHealthData';
import { useNativeHealth } from '@/src/hooks/useNativeHealth';
import { MetricCard } from '@/src/components/MetricCard';
import InsightCard from '@/src/components/InsightCard';
import { AlertCircle, CheckCircle2, RefreshCw, Apple } from 'lucide-react-native';

const { width } = Dimensions.get('window');

export default function DashboardScreen() {
  const {
    latestInsight,
    healthProfile,
    userProfile,
    loadingInsight,
    loadingHealthProfile,
    loadingUserProfile,
    refreshAll,
  } = useHealthData();

  const {
    isAuthorized,
    isSyncing,
    lastSyncDate,
    authorizeHealthKit,
    syncHealthData,
    checkAuthorizationStatus,
    sync,
    isAvailable,
    isAvailableValue,
  } = useNativeHealth();

  const [refreshing, setRefreshing] = React.useState(false);
  const [availabilityChecked, setAvailabilityChecked] = React.useState(false);

  // Vérifier la disponibilité et le statut d'autorisation au montage
  useEffect(() => {
    const checkAvailability = async () => {
      if (Platform.OS === 'ios') {
        const available = await isAvailable();
        if (available) {
          await checkAuthorizationStatus();
        }
        setAvailabilityChecked(true);
      } else {
        setAvailabilityChecked(true);
      }
    };
    checkAvailability();
  }, [isAvailable, checkAuthorizationStatus]);

  // Load data on mount
  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await refreshAll();
    setRefreshing(false);
  }, [refreshAll]);

  const formatDate = () => {
    const today = new Date();
    const options: Intl.DateTimeFormatOptions = {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    };
    return today.toLocaleDateString('fr-FR', options);
  };

  const profileData = healthProfile?.profile_data;
  const currentMetrics = profileData?.current_metrics;
  const baselines = profileData?.baselines;
  const anomalies = profileData?.anomalies || [];

  const isLoading = loadingInsight || loadingHealthProfile || loadingUserProfile;

  // Debug logs
  useEffect(() => {
    if (healthProfile) {
      console.log('Dashboard - Health Profile received:', JSON.stringify(healthProfile, null, 2));
      console.log('Dashboard - Current Metrics:', currentMetrics);
      console.log('Dashboard - Baselines:', baselines);
      console.log('Dashboard - HRV:', currentMetrics?.hrv);
      console.log('Dashboard - Sleep:', currentMetrics?.sleep);
      console.log('Dashboard - Heart Rate:', currentMetrics?.heart_rate);
    } else {
      console.log('Dashboard - No health profile available');
    }
  }, [healthProfile, currentMetrics, baselines]);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.contentContainer}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#FFFFFF" />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.greeting}>
          Bonjour {userProfile?.full_name || 'Dan'}
        </Text>
        <Text style={styles.date}>{formatDate()}</Text>
      </View>

      {/* HealthKit Sync Status */}
      {(Platform.OS === 'ios' || availabilityChecked) && (
        <View style={styles.healthKitContainer}>
          <View style={styles.healthKitStatus}>
            <Apple size={16} color="#FFFFFF" />
            <Text style={styles.healthKitText}>
              Source : Apple Health
            </Text>
            {isAuthorized === true && (
              <CheckCircle2 size={16} color="#34C759" style={styles.checkIcon} />
            )}
          </View>
          <TouchableOpacity
            style={[
              styles.syncButton,
              (isSyncing || !availabilityChecked || (Platform.OS === 'ios' && isAvailableValue === false)) && styles.syncButtonDisabled,
            ]}
            onPress={async () => {
              try {
                await sync();
                // Rafraîchir les données après synchronisation
                await refreshAll();
              } catch (error) {
                // Le hook gère déjà les erreurs et affiche les messages appropriés
                console.error('Erreur lors de la synchronisation:', error);
              }
            }}
            disabled={isSyncing || !availabilityChecked}
          >
            {isSyncing ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <>
                <RefreshCw size={14} color="#FFFFFF" />
                <Text style={styles.syncButtonText}>
                  {isAuthorized === false ? 'Autoriser' : 'Synchroniser'}
                </Text>
              </>
            )}
          </TouchableOpacity>
          {lastSyncDate && (
            <Text style={styles.lastSyncText}>
              Dernière sync : {lastSyncDate.toLocaleTimeString('fr-FR', {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </Text>
          )}
        </View>
      )}

      {/* Loading Indicator */}
      {isLoading && !refreshing && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#34C759" />
        </View>
      )}

      {/* Insight IA */}
      {latestInsight && (
        <InsightCard
          instructionText={latestInsight.instruction_text}
          category={latestInsight.category || undefined}
          priority={latestInsight.priority}
        />
      )}

      {/* Anomalies Badge */}
      {anomalies.length > 0 && (
        <View style={styles.anomalyBadge}>
          <AlertCircle size={16} color="#FF9500" />
          <Text style={styles.anomalyText}>
            Analyse en cours : {anomalies[0].type.replace('_', ' ')}
          </Text>
        </View>
      )}

      {/* Metrics Grid */}
      <View style={styles.metricsGrid}>
        {/* Carte HRV */}
        <MetricCard
          title="HRV"
          value={currentMetrics?.hrv?.average_ms?.toFixed(0) || '--'}
          unit="ms"
          baseline={baselines?.hrv_baseline?.toFixed(0)}
          iconName="Activity"
          color="#34C759"
          isAnomaly={anomalies.some((a) => a.type === 'hrv_drop') || false}
        />

        {/* Carte Sommeil */}
        <MetricCard
          title="Sommeil"
          value={
            currentMetrics?.sleep?.duration_minutes
              ? `${Math.floor((currentMetrics.sleep.duration_minutes || 0) / 60)}h${(currentMetrics.sleep.duration_minutes || 0) % 60}`
              : '--'
          }
          unit=""
          baseline={
            baselines?.sleep_baseline
              ? `${Math.floor((baselines.sleep_baseline || 0) / 60)}h${(baselines.sleep_baseline || 0) % 60}`
              : undefined
          }
          iconName="Moon"
          color="#5E5CE6"
          isAnomaly={anomalies.some((a) => a.type === 'sleep_deficit') || false}
        />

        {/* Carte Repos */}
        <MetricCard
          title="Repos"
          value={currentMetrics?.heart_rate?.resting_bpm?.toFixed(0) || '--'}
          unit="bpm"
          baseline={baselines?.hr_baseline?.toFixed(0)}
          iconName="Heart"
          color="#FF9500"
          isAnomaly={anomalies.some((a) => a.type === 'elevated_resting_hr') || false}
        />
      </View>
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
  header: {
    marginBottom: 24,
  },
  greeting: {
    fontSize: 32,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  date: {
    fontSize: 16,
    color: '#8E8E93',
    fontWeight: '500',
  },
  loadingContainer: {
    padding: 20,
    alignItems: 'center',
  },
  anomalyBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1C1C1E',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    marginTop: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#FF9500',
  },
  anomalyText: {
    color: '#FF9500',
    fontSize: 13,
    fontWeight: '600',
    marginLeft: 8,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginTop: 24,
  },
  healthKitContainer: {
    backgroundColor: '#1C1C1E',
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  healthKitStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  healthKitText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '600',
    marginLeft: 8,
    flex: 1,
  },
  checkIcon: {
    marginLeft: 4,
  },
  syncButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#34C759',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginBottom: 4,
  },
  syncButtonDisabled: {
    backgroundColor: '#8E8E93',
    opacity: 0.6,
  },
  syncButtonText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '600',
    marginLeft: 6,
  },
  lastSyncText: {
    color: '#8E8E93',
    fontSize: 11,
    textAlign: 'center',
    marginTop: 4,
  },
});
