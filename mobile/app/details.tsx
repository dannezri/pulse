import React from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
} from "react-native";
import { useRouter, Stack } from "expo-router";
import { useAuth } from "../src/hooks/useAuth";
import { useAnomalyDetection, Anomaly } from "../src/hooks/useAnomalyDetection";
import { useCurrentMetrics } from "../src/hooks/useCurrentMetrics";
import { ChevronLeft, TrendingUp, TrendingDown, AlertCircle } from "lucide-react-native";

export default function DetailsScreen() {
  const router = useRouter();
  const { userId } = useAuth();
  const { anomalies, state } = useAnomalyDetection(userId);
  const { data: currentMetrics } = useCurrentMetrics(userId);

  const stateColors = {
    calm: '#34C759',
    warning: '#FF9500',
    alert: '#FF3B30',
  };

  const stateColor = stateColors[state];

  return (
    <>
      <Stack.Screen
        options={{
          headerShown: true,
          headerTitle: "Détails",
          headerStyle: {
            backgroundColor: "#000000",
          },
          headerTintColor: "#FFFFFF",
          headerLeft: () => (
            <TouchableOpacity onPress={() => router.back()}>
              <ChevronLeft size={24} color="#FFFFFF" />
            </TouchableOpacity>
          ),
        }}
      />
      <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
        {/* Niveau 1 : État global */}
        <View style={styles.section}>
          <View style={[styles.stateCard, { borderColor: stateColor }]}>
            <AlertCircle size={32} color={stateColor} />
            <Text style={styles.stateTitle}>
              {state === 'calm' && "État Normal"}
              {state === 'warning' && "Attention Requise"}
              {state === 'alert' && "Alerte"}
            </Text>
            <Text style={styles.stateDescription}>
              {anomalies.length === 0 && "Aucune anomalie détectée"}
              {anomalies.length === 1 && "1 anomalie détectée"}
              {anomalies.length > 1 && `${anomalies.length} anomalies détectées`}
            </Text>
          </View>
        </View>

        {/* Niveau 2 : Anomalies détectées */}
        {anomalies.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Anomalies Détectées</Text>
            <Text style={styles.sectionSubtitle}>
              Métriques sortant significativement de votre baseline
            </Text>
            {anomalies.map((anomaly) => (
              <AnomalyDetailCard key={anomaly.metric} anomaly={anomaly} />
            ))}
          </View>
        )}

        {/* Niveau 3 : Toutes les métriques */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Toutes les Métriques</Text>
          <Text style={styles.sectionSubtitle}>
            Vue complète de vos données actuelles
          </Text>
          {currentMetrics && (
            <View style={styles.metricsGrid}>
              {/* Vitals */}
              <MetricGroup title="Signes Vitaux">
                {currentMetrics.hrv && (
                  <MetricRow label="HRV" value={`${Math.round(currentMetrics.hrv)} ms`} />
                )}
                {currentMetrics.hr && (
                  <MetricRow label="Fréquence cardiaque" value={`${Math.round(currentMetrics.hr)} bpm`} />
                )}
                {currentMetrics.spo2 && (
                  <MetricRow label="SpO2" value={`${Math.round(currentMetrics.spo2)}%`} />
                )}
                {currentMetrics.body_temperature && (
                  <MetricRow label="Température" value={`${currentMetrics.body_temperature.toFixed(1)}°C`} />
                )}
                {currentMetrics.respiratory_rate && (
                  <MetricRow label="Respiration" value={`${Math.round(currentMetrics.respiratory_rate)} /min`} />
                )}
              </MetricGroup>

              {/* Activity */}
              <MetricGroup title="Activité">
                {currentMetrics.steps && (
                  <MetricRow label="Pas" value={Math.round(currentMetrics.steps).toLocaleString('fr-FR')} />
                )}
                {currentMetrics.distance && (
                  <MetricRow label="Distance" value={`${(currentMetrics.distance / 1000).toFixed(2)} km`} />
                )}
                {currentMetrics.calories && (
                  <MetricRow label="Calories" value={`${Math.round(currentMetrics.calories)} kcal`} />
                )}
                {currentMetrics.active_calories && (
                  <MetricRow label="Calories actives" value={`${Math.round(currentMetrics.active_calories)} kcal`} />
                )}
                {currentMetrics.floors_climbed && (
                  <MetricRow label="Étages" value={`${Math.round(currentMetrics.floors_climbed)}`} />
                )}
              </MetricGroup>

              {/* Sleep */}
              {currentMetrics.sleep && (
                <MetricGroup title="Sommeil">
                  <MetricRow label="Durée" value={`${Math.round(currentMetrics.sleep.duration / 60)}h`} />
                  <MetricRow label="Score" value={`${Math.round(currentMetrics.sleep.score)}/100`} />
                </MetricGroup>
              )}

              {/* Wellness */}
              <MetricGroup title="Bien-être">
                {currentMetrics.stress && (
                  <MetricRow label="Stress" value={`${Math.round(currentMetrics.stress)}/100`} />
                )}
                {currentMetrics.glucose && (
                  <MetricRow label="Glycémie" value={`${Math.round(currentMetrics.glucose)} mg/dL`} />
                )}
              </MetricGroup>

              {/* Nutrition */}
              <MetricGroup title="Nutrition">
                {currentMetrics.water && (
                  <MetricRow label="Eau" value={`${Math.round(currentMetrics.water)} mL`} />
                )}
                {currentMetrics.caffeine && (
                  <MetricRow label="Caféine" value={`${Math.round(currentMetrics.caffeine)} mg`} />
                )}
              </MetricGroup>

              {/* Body */}
              {currentMetrics.weight && (
                <MetricGroup title="Corps">
                  <MetricRow label="Poids" value={`${currentMetrics.weight.toFixed(1)} kg`} />
                </MetricGroup>
              )}
            </View>
          )}
        </View>
      </ScrollView>
    </>
  );
}

/**
 * Carte détaillée d'une anomalie
 */
function AnomalyDetailCard({ anomaly }: { anomaly: Anomaly }) {
  const isAbove = anomaly.direction === 'above';
  const Icon = isAbove ? TrendingUp : TrendingDown;
  const color = isAbove ? '#FF9500' : '#FF3B30';

  return (
    <View style={[styles.anomalyCard, { borderLeftColor: color }]}>
      <View style={styles.anomalyHeader}>
        <View style={styles.anomalyTitleContainer}>
          <Text style={styles.anomalyTitle}>{getMetricDisplayName(anomaly.metric)}</Text>
          <View style={[styles.anomalyBadge, { backgroundColor: `${color}20` }]}>
            <Text style={[styles.anomalyBadgeText, { color }]}>
              {anomaly.direction === 'above' ? 'Au-dessus' : 'En-dessous'}
            </Text>
          </View>
        </View>
        <Icon size={24} color={color} />
      </View>

      <View style={styles.anomalyStats}>
        <View style={styles.anomalyStat}>
          <Text style={styles.anomalyStatLabel}>Valeur actuelle</Text>
          <Text style={styles.anomalyStatValue}>{anomaly.value}</Text>
        </View>
        <View style={styles.anomalyStat}>
          <Text style={styles.anomalyStatLabel}>Baseline (μ)</Text>
          <Text style={styles.anomalyStatValue}>{anomaly.baseline.mean}</Text>
        </View>
        <View style={styles.anomalyStat}>
          <Text style={styles.anomalyStatLabel}>Écart (Z-Score)</Text>
          <Text style={[styles.anomalyStatValue, { color }]}>{anomaly.z_score}σ</Text>
        </View>
      </View>

      <View style={styles.anomalyFooter}>
        <Text style={styles.anomalyPriority}>
          Priorité: {anomaly.priority.toFixed(1)} (poids: {anomaly.weight})
        </Text>
      </View>
    </View>
  );
}

/**
 * Groupe de métriques
 */
function MetricGroup({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={styles.metricGroup}>
      <Text style={styles.metricGroupTitle}>{title}</Text>
      {children}
    </View>
  );
}

/**
 * Ligne de métrique
 */
function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.metricRow}>
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={styles.metricValue}>{value}</Text>
    </View>
  );
}

function getMetricDisplayName(metric: string): string {
  const names: Record<string, string> = {
    hrv: "Variabilité cardiaque (HRV)",
    heart_rate: "Fréquence cardiaque",
    body_temperature: "Température corporelle",
    sleep_duration: "Durée de sommeil",
    sleep: "Sommeil",
    stress: "Niveau de stress",
    glucose: "Glycémie",
    spo2: "Oxygénation (SpO2)",
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
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: "700",
    color: "#FFFFFF",
    marginBottom: 8,
  },
  sectionSubtitle: {
    fontSize: 14,
    color: "#8E8E93",
    marginBottom: 20,
  },
  stateCard: {
    backgroundColor: "#1C1C1E",
    borderRadius: 24,
    padding: 32,
    alignItems: "center",
    borderLeftWidth: 4,
  },
  stateTitle: {
    fontSize: 24,
    fontWeight: "700",
    color: "#FFFFFF",
    marginTop: 16,
    marginBottom: 8,
  },
  stateDescription: {
    fontSize: 16,
    color: "#8E8E93",
  },
  anomalyCard: {
    backgroundColor: "#1C1C1E",
    borderRadius: 20,
    padding: 20,
    marginBottom: 16,
    borderLeftWidth: 4,
  },
  anomalyHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 16,
  },
  anomalyTitleContainer: {
    flex: 1,
  },
  anomalyTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#FFFFFF",
    marginBottom: 8,
  },
  anomalyBadge: {
    alignSelf: "flex-start",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  anomalyBadgeText: {
    fontSize: 12,
    fontWeight: "600",
  },
  anomalyStats: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 16,
  },
  anomalyStat: {
    flex: 1,
  },
  anomalyStatLabel: {
    fontSize: 11,
    color: "#8E8E93",
    marginBottom: 4,
    textTransform: "uppercase",
    fontWeight: "600",
  },
  anomalyStatValue: {
    fontSize: 18,
    fontWeight: "700",
    color: "#FFFFFF",
  },
  anomalyFooter: {
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: "#2C2C2E",
  },
  anomalyPriority: {
    fontSize: 13,
    color: "#8E8E93",
    fontWeight: "500",
  },
  metricsGrid: {
    gap: 16,
  },
  metricGroup: {
    backgroundColor: "#1C1C1E",
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
  },
  metricGroupTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: "#8E8E93",
    textTransform: "uppercase",
    marginBottom: 12,
    letterSpacing: 0.5,
  },
  metricRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#2C2C2E",
  },
  metricLabel: {
    fontSize: 15,
    color: "#FFFFFF",
    fontWeight: "500",
  },
  metricValue: {
    fontSize: 15,
    color: "#8E8E93",
    fontWeight: "600",
  },
});
