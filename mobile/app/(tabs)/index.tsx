import React, { useState } from "react";
import {
  View,
  Text,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  ActivityIndicator,
  Platform,
  StyleSheet,
} from "react-native";
import { useAuth } from "../../src/hooks/useAuth";
import { useProfile } from "../../src/hooks/useProfile";
import { useHealthProfile } from "../../src/hooks/useHealthProfile";
import { useLatestInsight } from "../../src/hooks/useLatestInsight";
import { useRecentInsights } from "../../src/hooks/useRecentInsights";
import { useCurrentMetrics } from "../../src/hooks/useCurrentMetrics";
import { useVital } from "../../src/hooks/useVital";
import { InsightCard } from "../../src/components/InsightCard";
import { MetricCard } from "../../src/components/MetricCard";
import { RecoveryScore } from "../../src/components/RecoveryScore";
import { FadeInView } from "../../src/components/FadeInView";
import { PressableScale } from "../../src/components/PressableScale";
import { Moon, Heart, Activity, RefreshCw, Link, Footprints, Droplets, Wind, Scale, Brain, Coffee, Flame } from "lucide-react-native";
import { useQueryClient } from "@tanstack/react-query";
import { syncLast6Hours } from "../../src/services/HealthScanner";
import { useRouter } from "expo-router";

export default function HomeScreen() {
  const { userId, loading: authLoading } = useAuth();
  const { data: profile, isLoading: profileLoading } = useProfile(userId);
  const { data: healthProfile, isLoading: healthProfileLoading } =
    useHealthProfile(userId);
  const { data: latestInsight, isLoading: insightLoading } =
    useLatestInsight(userId);
  const { data: recentInsights, isLoading: recentInsightsLoading } =
    useRecentInsights(userId, 3);
  const { data: currentMetrics, isLoading: metricsLoading } =
    useCurrentMetrics(userId);
  const { isVitalConfigured, connectedCount } = useVital();
  const queryClient = useQueryClient();
  const router = useRouter();
  const [refreshing, setRefreshing] = useState(false);
  const [syncingContext, setSyncingContext] = useState(false);

  const onRefresh = async () => {
    setRefreshing(true);
    await queryClient.invalidateQueries();
    setRefreshing(false);
  };

  // Calculate recovery score
  const calculateRecoveryScore = (): number => {
    if (!healthProfile?.profile_data) return 0;

    const { current_metrics, baselines } = healthProfile.profile_data;
    let score = 50;

    if (current_metrics.hrv?.latest_ms && baselines.hrv_baseline) {
      const hrvRatio = current_metrics.hrv.latest_ms / baselines.hrv_baseline;
      if (hrvRatio >= 1) score += 30;
      else if (hrvRatio >= 0.9) score += 20;
      else if (hrvRatio >= 0.8) score += 10;
    }

    if (current_metrics.sleep?.quality_score) {
      score += (current_metrics.sleep.quality_score / 100) * 30;
    }

    if (current_metrics.heart_rate?.resting_bpm && baselines.hr_baseline) {
      const hrDiff = Math.abs(
        current_metrics.heart_rate.resting_bpm - baselines.hr_baseline
      );
      if (hrDiff <= 2) score += 20;
      else if (hrDiff <= 5) score += 10;
    }

    return Math.min(100, Math.max(0, Math.round(score)));
  };

  const recoveryScore = calculateRecoveryScore();
  const firstName = profile?.full_name?.split(" ")[0] || "Utilisateur";

  const getTrend = (current: number | null, baseline: number | null) => {
    if (!current || !baseline) return null;
    const diff = ((current - baseline) / baseline) * 100;
    if (diff > 5) return "up";
    if (diff < -5) return "down";
    return "stable";
  };

  const isLoading =
    authLoading ||
    profileLoading ||
    healthProfileLoading ||
    insightLoading ||
    metricsLoading;

  const hasError = profileLoading === false && !profile && !authLoading;

  if (isLoading && !profile) {
    return (
      <View style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#34C759" />
        </View>
      </View>
    );
  }

  if (hasError) {
    return (
      <View style={styles.container}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>
            Impossible de charger votre profil
          </Text>
          <TouchableOpacity style={styles.retryButton} onPress={onRefresh}>
            <Text style={styles.retryButtonText}>Réessayer</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  const hasNoData = recoveryScore === 0 && !latestInsight;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.contentContainer}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={onRefresh}
          tintColor="#34C759"
        />
      }
    >
      {/* Header */}
      <FadeInView delay={0} duration={600}>
        <View style={styles.header}>
          <Text style={styles.subtitle}>
            {new Date().toLocaleDateString("fr-FR", {
              weekday: "long",
              day: "numeric",
              month: "long",
            })}
          </Text>
          <Text style={styles.title}>Bonjour {firstName}</Text>
        </View>
      </FadeInView>

      {/* Vital Status */}
      <FadeInView delay={100} duration={600}>
        <TouchableOpacity
          onPress={() => router.push("/(tabs)/connections")}
          style={{
            backgroundColor: isVitalConfigured ? "#1a1a1a" : "#1a3a1a",
            borderRadius: 12,
            padding: 16,
            marginBottom: 16,
            borderWidth: 1,
            borderColor: isVitalConfigured ? "#333" : "#00FF41",
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <View style={{ flexDirection: "row", alignItems: "center", flex: 1 }}>
            <Link size={20} color={isVitalConfigured ? "#00FF41" : "#fff"} />
            <View style={{ marginLeft: 12, flex: 1 }}>
              <Text style={{ color: "#fff", fontSize: 14, fontWeight: "600" }}>
                {isVitalConfigured
                  ? `${connectedCount} source${connectedCount > 1 ? 's' : ''} connectée${connectedCount > 1 ? 's' : ''}`
                  : "Connecter vos sources de données"}
              </Text>
              <Text style={{ color: "#666", fontSize: 12, marginTop: 2 }}>
                {isVitalConfigured
                  ? "Apple Health, Fitbit, Oura, etc."
                  : "Synchronisez automatiquement vos données"}
              </Text>
            </View>
          </View>
          <Text style={{ color: "#00FF41", fontSize: 14, fontWeight: "600" }}>
            {isVitalConfigured ? "Gérer" : "Configurer"}
          </Text>
        </TouchableOpacity>
      </FadeInView>

      {/* Recovery Score & Sync Button */}
      <FadeInView delay={100} duration={600}>
        <View style={styles.headerActions}>
          <RecoveryScore score={recoveryScore} />

          {Platform.OS === "ios" && (
            <PressableScale
              style={[
                styles.syncButton,
                syncingContext && styles.syncButtonDisabled,
              ]}
              onPress={async () => {
                console.log('[HomeScreen] 🔄 Bouton Synchroniser cliqué');
                setSyncingContext(true);
                try {
                  const result = await syncLast6Hours();
                  console.log('[HomeScreen] Résultat synchronisation:', result);
                  if (result.success) {
                    console.log('[HomeScreen] Invalidation des queries...');
                    await queryClient.invalidateQueries();
                  }
                } catch (error) {
                  console.error("[HomeScreen] ❌ Erreur synchronisation:", error);
                } finally {
                  setSyncingContext(false);
                  console.log('[HomeScreen] Synchronisation terminée');
                }
              }}
              disabled={syncingContext}
            >
              {syncingContext ? (
                <>
                  <ActivityIndicator size="small" color="#FFFFFF" />
                  <Text style={styles.syncButtonText}>Sync...</Text>
                </>
              ) : (
                <>
                  <RefreshCw size={16} color="#FFFFFF" />
                  <Text style={styles.syncButtonText}>Synchroniser</Text>
                </>
              )}
            </PressableScale>
          )}
        </View>
      </FadeInView>

      {/* Welcome Message */}
      {hasNoData && (
        <FadeInView delay={200} duration={600}>
          <View style={styles.welcomeCard}>
            <Text style={styles.welcomeTitle}>🚀 Commencez votre parcours</Text>
            <Text style={styles.welcomeText}>
              Synchronisez vos données de santé pour obtenir des insights
              personnalisés et optimiser votre bien-être.
            </Text>
            {Platform.OS === "ios" && (
              <View style={styles.welcomeTip}>
                <Text style={styles.welcomeTipText}>
                  💡 Appuyez sur "Synchroniser" pour importer vos données HealthKit
                </Text>
              </View>
            )}
          </View>
        </FadeInView>
      )}

      {/* Latest AI Insight */}
      {latestInsight && (
        <FadeInView delay={200} duration={600}>
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>💡 Insight du jour</Text>
            </View>
            <InsightCard insight={latestInsight} isLatest={true} />
          </View>
        </FadeInView>
      )}

      {/* Metrics Grid */}
      <FadeInView delay={300} duration={600}>
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <View>
              <Text style={styles.sectionTitle}>📊 Vos métriques</Text>
              <Text style={styles.sectionSubtitle}>Suivi quotidien</Text>
            </View>
          </View>
          <View style={styles.metricsGrid}>
            {/* Sleep */}
            <View style={styles.metricItem}>
              <MetricCard
                title="Sommeil"
                value={
                  currentMetrics?.sleep?.duration
                    ? `${Math.round(currentMetrics.sleep.duration / 60)}h`
                    : null
                }
                subtitle={
                  currentMetrics?.sleep?.score
                    ? `Score: ${Math.round(currentMetrics.sleep.score)}`
                    : undefined
                }
                trend={getTrend(
                  currentMetrics?.sleep?.duration || null,
                  healthProfile?.profile_data?.baselines?.sleep_baseline || null
                )}
                icon={<Moon size={18} color="#0066FF" />}
                color="#0066FF"
              />
            </View>

            {/* HRV */}
            <View style={styles.metricItem}>
              <MetricCard
                title="HRV"
                value={
                  currentMetrics?.hrv ? `${Math.round(currentMetrics.hrv)}ms` : null
                }
                subtitle={
                  healthProfile?.profile_data?.baselines?.hrv_baseline
                    ? `Baseline: ${Math.round(
                        healthProfile.profile_data.baselines.hrv_baseline
                      )}ms`
                    : undefined
                }
                trend={getTrend(
                  currentMetrics?.hrv || null,
                  healthProfile?.profile_data?.baselines?.hrv_baseline || null
                )}
                icon={<Activity size={18} color="#34C759" />}
                color="#34C759"
              />
            </View>

            {/* HR */}
            <View style={styles.metricItem}>
              <MetricCard
                title="Rythme Cardiaque"
                value={
                  currentMetrics?.hr ? `${Math.round(currentMetrics.hr)} bpm` : null
                }
                subtitle={
                  healthProfile?.profile_data?.baselines?.hr_baseline
                    ? `Repos: ${Math.round(
                        healthProfile.profile_data.baselines.hr_baseline
                      )} bpm`
                    : undefined
                }
                trend={getTrend(
                  currentMetrics?.hr || null,
                  healthProfile?.profile_data?.baselines?.hr_baseline || null
                )}
                icon={<Heart size={18} color="#FF9500" />}
                color="#FF9500"
              />
            </View>

            {/* Steps */}
            <View style={styles.metricItem}>
              <MetricCard
                title="Pas"
                value={
                  currentMetrics?.steps 
                    ? `${Math.round(currentMetrics.steps).toLocaleString('fr-FR')}` 
                    : null
                }
                subtitle="Aujourd'hui"
                icon={<Footprints size={18} color="#FF2D55" />}
                color="#FF2D55"
              />
            </View>

            {/* Water */}
            {currentMetrics?.water && (
              <View style={styles.metricItem}>
                <MetricCard
                  title="Eau"
                  value={`${Math.round(currentMetrics.water)} mL`}
                  subtitle="Hydratation"
                  icon={<Droplets size={18} color="#00C7BE" />}
                  color="#00C7BE"
                />
              </View>
            )}

            {/* Calories */}
            {currentMetrics?.calories && (
              <View style={styles.metricItem}>
                <MetricCard
                  title="Calories"
                  value={`${Math.round(currentMetrics.calories)}`}
                  subtitle="Dépensées"
                  icon={<Flame size={18} color="#FF3B30" />}
                  color="#FF3B30"
                />
              </View>
            )}

            {/* SpO2 */}
            {currentMetrics?.spo2 && (
              <View style={styles.metricItem}>
                <MetricCard
                  title="SpO2"
                  value={`${Math.round(currentMetrics.spo2)}%`}
                  subtitle="Oxygène"
                  icon={<Wind size={18} color="#00C7BE" />}
                  color="#00C7BE"
                />
              </View>
            )}

            {/* Glucose */}
            {currentMetrics?.glucose && (
              <View style={styles.metricItem}>
                <MetricCard
                  title="Glycémie"
                  value={`${Math.round(currentMetrics.glucose)}`}
                  subtitle="mg/dL"
                  icon={<Droplets size={18} color="#BF5AF2" />}
                  color="#BF5AF2"
                />
              </View>
            )}

            {/* Weight */}
            {currentMetrics?.weight && (
              <View style={styles.metricItem}>
                <MetricCard
                  title="Poids"
                  value={`${currentMetrics.weight.toFixed(1)} kg`}
                  subtitle="Aujourd'hui"
                  icon={<Scale size={18} color="#FF9F0A" />}
                  color="#FF9F0A"
                />
              </View>
            )}

            {/* Stress */}
            {currentMetrics?.stress && (
              <View style={styles.metricItem}>
                <MetricCard
                  title="Stress"
                  value={`${Math.round(currentMetrics.stress)}`}
                  subtitle="Niveau"
                  icon={<Brain size={18} color="#FF2D55" />}
                  color="#FF2D55"
                />
              </View>
            )}

            {/* Caffeine */}
            {currentMetrics?.caffeine && (
              <View style={styles.metricItem}>
                <MetricCard
                  title="Caféine"
                  value={`${Math.round(currentMetrics.caffeine)} mg`}
                  subtitle="Consommée"
                  icon={<Coffee size={18} color="#8B4513" />}
                  color="#8B4513"
                />
              </View>
            )}
          </View>
        </View>
      </FadeInView>

      {/* Recent Insights */}
      {recentInsights && recentInsights.length > 0 ? (
        <FadeInView delay={400} duration={600}>
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <View>
                <Text style={styles.sectionTitle}>📜 Historique</Text>
                <Text style={styles.sectionSubtitle}>
                  {recentInsights.filter((i) => i.id !== latestInsight?.id).length}{" "}
                  insights récents
                </Text>
              </View>
            </View>
            {recentInsights
              .filter((insight) => insight.id !== latestInsight?.id)
              .map((insight, index) => (
                <FadeInView key={insight.id} delay={450 + index * 50} duration={500}>
                  <View style={styles.insightItem}>
                    <InsightCard insight={insight} />
                  </View>
                </FadeInView>
              ))}
          </View>
        </FadeInView>
      ) : (
        !latestInsight && (
          <FadeInView delay={400} duration={600}>
            <View style={styles.emptyState}>
              <Text style={styles.emptyIcon}>🤖</Text>
              <Text style={styles.emptyTitle}>Pas encore d'insights</Text>
              <Text style={styles.emptyText}>
                Synchronisez vos données pour que l'IA puisse analyser votre santé
                et vous donner des recommandations personnalisées.
              </Text>
            </View>
          </FadeInView>
        )
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#000000",
  },
  contentContainer: {
    padding: 20,
    paddingTop: 60,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  errorContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  errorText: {
    color: "#FF3B30",
    fontSize: 16,
    fontWeight: "600",
    marginBottom: 16,
    textAlign: "center",
  },
  retryButton: {
    backgroundColor: "#1C1C1E",
    borderRadius: 16,
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderWidth: 1,
    borderColor: "#2C2C2E",
  },
  retryButtonText: {
    color: "#34C759",
    fontSize: 16,
    fontWeight: "600",
  },
  header: {
    marginBottom: 24,
  },
  title: {
    fontSize: 32,
    fontWeight: "700",
    color: "#FFFFFF",
  },
  subtitle: {
    fontSize: 14,
    color: "#8E8E93",
    fontWeight: "500",
    marginBottom: 4,
  },
  headerActions: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 32,
  },
  syncButton: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#5E5CE6",
    borderRadius: 16,
    paddingVertical: 12,
    paddingHorizontal: 16,
    gap: 8,
  },
  syncButtonDisabled: {
    opacity: 0.6,
  },
  syncButtonText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "600",
  },
  welcomeCard: {
    backgroundColor: "#1C1C1E",
    borderRadius: 20,
    padding: 20,
    marginBottom: 32,
    borderWidth: 1,
    borderColor: "#2C2C2E",
  },
  welcomeTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#FFFFFF",
    marginBottom: 12,
  },
  welcomeText: {
    fontSize: 14,
    color: "#8E8E93",
    lineHeight: 20,
    marginBottom: 16,
  },
  welcomeTip: {
    backgroundColor: "rgba(52, 199, 89, 0.1)",
    borderRadius: 12,
    padding: 12,
  },
  welcomeTipText: {
    fontSize: 12,
    color: "#34C759",
    fontWeight: "600",
  },
  section: {
    marginBottom: 32,
  },
  sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: "700",
    color: "#FFFFFF",
  },
  sectionSubtitle: {
    fontSize: 12,
    color: "#8E8E93",
    marginTop: 2,
  },
  metricsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 12,
  },
  metricItem: {
    width: "48%",
  },
  insightItem: {
    marginBottom: 12,
  },
  emptyState: {
    backgroundColor: "#1C1C1E",
    borderRadius: 20,
    padding: 32,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#2C2C2E",
    marginBottom: 32,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 12,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#FFFFFF",
    textAlign: "center",
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: "#8E8E93",
    textAlign: "center",
    lineHeight: 20,
  },
});
