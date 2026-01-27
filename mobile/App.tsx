import React, { useEffect, useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaView, View, Text, StyleSheet, ActivityIndicator, ScrollView } from 'react-native';
import { supabase } from './src/lib/supabase';
import InsightCard from './src/components/InsightCard';
import { MetricCard } from './src/components/MetricCard';

// UUID de test
const TEST_USER_UUID = '006b5096-1983-44ae-9fc5-a8431c9f40be';

interface Insight {
  id: string;
  instruction_text: string;
  category?: string;
  created_at: string;
}

interface HealthProfile {
  profile_data: {
    current_metrics?: {
      sleep?: {
        duration_minutes?: number;
      };
      hrv?: {
        average_ms?: number;
      };
      heart_rate?: {
        resting_bpm?: number;
      };
    };
    baselines?: {
      sleep_baseline?: number;
      hrv_baseline?: number;
      hr_baseline?: number;
    };
    anomalies?: string[];
  };
  date: string;
}

export default function App() {
  const [insight, setInsight] = useState<Insight | null>(null);
  const [healthProfile, setHealthProfile] = useState<HealthProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);

      // Récupérer l'insight et le health_profile en parallèle
      const [insightResult, healthProfileResult] = await Promise.all([
        supabase.rpc('get_latest_insight', { user_uuid: TEST_USER_UUID }),
        supabase.rpc('get_latest_health_profile', { user_uuid: TEST_USER_UUID }),
      ]);

      if (insightResult.data && insightResult.data.length > 0) {
        setInsight(insightResult.data[0]);
      } else {
        setInsight(null);
      }

      if (healthProfileResult.data && healthProfileResult.data.length > 0) {
        setHealthProfile(healthProfileResult.data[0]);
      } else {
        setHealthProfile(null);
      }
    } catch (err) {
      console.error('Erreur inattendue:', err);
    } finally {
      setLoading(false);
    }
  };

  // Formatage Sommeil : duration_minutes / 60 avec 1 décimale, unité "h"
  const formatSleepValue = (minutes?: number): number | string => {
    if (!minutes) return '--';
    return (minutes / 60).toFixed(1);
  };

  const formatSleepBaseline = (baseline?: number): number | undefined => {
    if (!baseline) return undefined;
    return parseFloat((baseline / 60).toFixed(1));
  };

  // Formatage HRV : average_ms, unité "ms"
  const formatHRVValue = (ms?: number): number | string => {
    if (!ms) return '--';
    return Math.round(ms);
  };

  const formatHRVBaseline = (baseline?: number): number | undefined => {
    if (!baseline) return undefined;
    return Math.round(baseline);
  };

  // Formatage Repos : resting_bpm, unité "bpm"
  const formatHeartRateValue = (bpm?: number): number | string => {
    if (!bpm) return '--';
    return Math.round(bpm);
  };

  const formatHeartRateBaseline = (baseline?: number): number | undefined => {
    if (!baseline) return undefined;
    return Math.round(baseline);
  };

  const checkAnomaly = (metricName: string): boolean => {
    if (!healthProfile?.profile_data?.anomalies) return false;
    return healthProfile.profile_data.anomalies.some(anomaly => 
      anomaly.toLowerCase().includes(metricName.toLowerCase())
    );
  };

  const sleepDuration = healthProfile?.profile_data?.current_metrics?.sleep?.duration_minutes;
  const sleepBaseline = healthProfile?.profile_data?.baselines?.sleep_baseline;
  const hrvValue = healthProfile?.profile_data?.current_metrics?.hrv?.average_ms;
  const hrvBaseline = healthProfile?.profile_data?.baselines?.hrv_baseline;
  const heartRate = healthProfile?.profile_data?.current_metrics?.heart_rate?.resting_bpm;
  const hrBaseline = healthProfile?.profile_data?.baselines?.hr_baseline;

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        <View style={styles.content}>
          <Text style={styles.title}>Aujourd'hui</Text>

          {loading ? (
            <View style={styles.center}>
              <ActivityIndicator size="large" color="#FFFFFF" />
            </View>
          ) : (
            <>
              {insight ? (
                <InsightCard
                  instructionText={insight.instruction_text}
                  category={insight.category}
                  createdAt={insight.created_at}
                />
              ) : (
                <View style={styles.emptyCard}>
                  <Text style={styles.emptyText}>En attente de nouvelles données...</Text>
                </View>
              )}

              {/* Grille de métriques */}
              <View style={styles.metricsGrid}>
                <MetricCard
                  iconName="Moon"
                  title="Sommeil"
                  value={formatSleepValue(sleepDuration)}
                  unit="h"
                  baseline={formatSleepBaseline(sleepBaseline)}
                  color="#5E5CE6"
                  isAnomaly={checkAnomaly('sleep')}
                />
                <MetricCard
                  iconName="Activity"
                  title="HRV"
                  value={formatHRVValue(hrvValue)}
                  unit="ms"
                  baseline={formatHRVBaseline(hrvBaseline)}
                  color="#32D74B"
                  isAnomaly={checkAnomaly('hrv')}
                />
                <MetricCard
                  iconName="Heart"
                  title="Repos"
                  value={formatHeartRateValue(heartRate)}
                  unit="bpm"
                  baseline={formatHeartRateBaseline(hrBaseline)}
                  color="#FF453A"
                  isAnomaly={checkAnomaly('heart') || checkAnomaly('hr')}
                />
              </View>
            </>
          )}
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
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 40,
  },
  content: {
    paddingHorizontal: 20,
    paddingTop: 20,
  },
  title: {
    fontSize: 34,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: 200,
  },
  emptyCard: {
    backgroundColor: '#1C1C1E',
    borderWidth: 1,
    borderColor: '#2C2C2E',
    borderRadius: 20,
    padding: 16,
    marginTop: 16,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 100,
  },
  emptyText: {
    color: '#8E8E93',
    fontSize: 16,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 16,
  },
});
