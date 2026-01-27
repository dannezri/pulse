import React, { useState } from "react";
import {
  View,
  Text,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  StyleSheet,
} from "react-native";
import { useAuth } from "../../src/hooks/useAuth";
import { useProfile } from "../../src/hooks/useProfile";
import { useAnomalyDetection } from "../../src/hooks/useAnomalyDetection";
import { useMainInsight } from "../../src/hooks/useMainInsight";
import { useShakeRefresh } from "../../src/hooks/useShakeRefresh";
import { GestureOrbWrapper } from "../../src/components/GestureOrbWrapper";
import { BottomDrawer } from "../../src/components/BottomDrawer";
import { AmbientInsightCard, CalmStateCard } from "../../src/components/AmbientInsightCard";
import { FadeInView } from "../../src/components/FadeInView";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "expo-router";

export default function AmbientHomeScreen() {
  const { userId, loading: authLoading } = useAuth();
  const { data: profile, isLoading: profileLoading } = useProfile(userId);
  const { anomalies, state, isLoading: anomalyLoading } = useAnomalyDetection(userId);
  const { data: mainInsight, isLoading: insightLoading } = useMainInsight(userId, anomalies);
  const queryClient = useQueryClient();
  const router = useRouter();
  const [refreshing, setRefreshing] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  
  // Hook pour rafraîchir les données avec le shake
  useShakeRefresh();

  const onRefresh = async () => {
    setRefreshing(true);
    await queryClient.invalidateQueries();
    setRefreshing(false);
  };

  const firstName = profile?.full_name?.split(" ")[0] || "Utilisateur";
  
  // Format date
  const today = new Date();
  const formattedDate = today.toLocaleDateString("fr-FR", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });

  const isLoading = authLoading || profileLoading || anomalyLoading;

  // Loading state
  if (isLoading && !profile) {
    return (
      <View style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#34C759" />
        </View>
      </View>
    );
  }

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
      {/* Header minimaliste */}
      <FadeInView delay={0} duration={600} useSpring>
        <View style={styles.header}>
          <Text style={styles.date}>{formattedDate}</Text>
          <Text style={styles.greeting}>Bonjour {firstName}</Text>
        </View>
      </FadeInView>

      {/* GestureOrbWrapper avec Orb organique */}
      <FadeInView delay={150} duration={800} useSpring>
        <View style={styles.orbContainer}>
          <GestureOrbWrapper 
            state={state} 
            size={150}
            onTap={() => setDrawerOpen(true)}
            onPinch={() => router.push('/details')}
          />
        </View>
      </FadeInView>

      {/* Message d'état sous l'Orb */}
      <FadeInView delay={300} duration={600} useSpring>
        <View style={styles.stateMessageContainer}>
          <Text style={styles.stateMessage}>
            {state === 'calm' && "Système nerveux en équilibre"}
            {state === 'warning' && "Attention requise"}
            {state === 'alert' && "Repos recommandé"}
          </Text>
        </View>
      </FadeInView>

      {/* Carte Insight unique ou Calm State */}
      <FadeInView delay={450} duration={600} useSpring>
        {insightLoading ? (
          <View style={styles.insightLoading}>
            <ActivityIndicator size="small" color="#8E8E93" />
            <Text style={styles.insightLoadingText}>Analyse en cours...</Text>
          </View>
        ) : anomalies.length > 0 && mainInsight ? (
          <AmbientInsightCard
            insight={mainInsight.content}
            state={state}
            anomalies={anomalies}
            onTapForDetails={() => router.push('/details')}
          />
        ) : (
          <CalmStateCard message={mainInsight?.content} />
        )}
      </FadeInView>

      {/* Timeline de pertinence (optionnel) */}
      {anomalies.length > 0 && (
        <FadeInView delay={600} duration={600} useSpring>
          <View style={styles.anomalyTimeline}>
            <Text style={styles.timelineTitle}>Métriques surveillées</Text>
            {anomalies.slice(0, 3).map((anomaly, index) => (
              <View key={anomaly.metric} style={styles.anomalyItem}>
                <View style={styles.anomalyDot} />
                <View style={styles.anomalyContent}>
                  <Text style={styles.anomalyMetric}>
                    {getMetricDisplayName(anomaly.metric)}
                  </Text>
                  <Text style={styles.anomalyValue}>
                    {anomaly.value} ({anomaly.direction === 'above' ? '↑' : '↓'} {Math.abs(anomaly.z_score)}σ)
                  </Text>
                </View>
              </View>
            ))}
          </View>
        </FadeInView>
      )}

      {/* Spacer pour ne pas coller au bas */}
      <View style={styles.bottomSpacer} />
      
      {/* Bottom Drawer glassmorphique */}
      <BottomDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        anomalies={anomalies}
        insight={mainInsight?.content || "Analyse en cours..."}
      />
    </ScrollView>
  );
}

/**
 * Helper pour afficher des noms de métriques lisibles
 */
function getMetricDisplayName(metric: string): string {
  const names: Record<string, string> = {
    hrv: "Variabilité cardiaque",
    heart_rate: "Fréquence cardiaque",
    body_temperature: "Température corporelle",
    sleep_duration: "Durée de sommeil",
    sleep: "Sommeil",
    stress: "Niveau de stress",
    glucose: "Glycémie",
    spo2: "Oxygénation",
    steps: "Nombre de pas",
    calories: "Calories",
    water: "Hydratation",
    active_calories: "Calories actives",
    weight: "Poids",
    respiratory_rate: "Fréquence respiratoire",
    caffeine: "Caféine",
    distance: "Distance parcourue",
    floors_climbed: "Étages montés",
  };
  return names[metric] || metric;
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
  header: {
    marginBottom: 32,
  },
  date: {
    fontSize: 14,
    color: "#8E8E93",
    fontWeight: "500",
    marginBottom: 4,
    textTransform: "capitalize",
  },
  greeting: {
    fontSize: 32,
    fontWeight: "700",
    color: "#FFFFFF",
  },
  orbContainer: {
    alignItems: "center",
    justifyContent: "center",
    marginVertical: 40,
  },
  stateMessageContainer: {
    alignItems: "center",
    marginBottom: 24,
  },
  stateMessage: {
    fontSize: 16,
    color: "#8E8E93",
    fontWeight: "600",
    letterSpacing: 0.3,
    textTransform: "uppercase",
  },
  insightLoading: {
    alignItems: "center",
    paddingVertical: 40,
  },
  insightLoadingText: {
    color: "#8E8E93",
    fontSize: 14,
    marginTop: 12,
  },
  anomalyTimeline: {
    marginTop: 24,
    backgroundColor: "#1C1C1E",
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: "#2C2C2E",
  },
  timelineTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: "#8E8E93",
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginBottom: 16,
  },
  anomalyItem: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 16,
  },
  anomalyDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#FF9500",
    marginRight: 12,
  },
  anomalyContent: {
    flex: 1,
  },
  anomalyMetric: {
    fontSize: 15,
    color: "#FFFFFF",
    fontWeight: "600",
    marginBottom: 2,
  },
  anomalyValue: {
    fontSize: 13,
    color: "#8E8E93",
  },
  bottomSpacer: {
    height: 40,
  },
});
