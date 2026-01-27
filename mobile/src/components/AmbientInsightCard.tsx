import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { ChevronRight } from 'lucide-react-native';
import type { Anomaly } from '../services/ZScoreCalculator';
import type { GlobalState } from '../hooks/useAnomalyDetection';

interface AmbientInsightCardProps {
  insight: string;
  state: GlobalState;
  anomalies?: Anomaly[];
  onTapForDetails?: () => void;
}

const STATE_COLORS = {
  calm: '#34C759',
  warning: '#FF9500',
  alert: '#FF3B30',
};

const STATE_BG_COLORS = {
  calm: 'rgba(52, 199, 89, 0.1)',
  warning: 'rgba(255, 149, 0, 0.1)',
  alert: 'rgba(255, 59, 48, 0.1)',
};

export function AmbientInsightCard({
  insight,
  state,
  anomalies = [],
  onTapForDetails,
}: AmbientInsightCardProps) {
  const borderColor = STATE_COLORS[state];
  const backgroundColor = STATE_BG_COLORS[state];
  const hasDetails = anomalies.length > 0 && onTapForDetails;

  return (
    <TouchableOpacity
      style={[
        styles.container,
        {
          borderLeftColor: borderColor,
          backgroundColor,
        },
      ]}
      onPress={onTapForDetails}
      disabled={!hasDetails}
      activeOpacity={hasDetails ? 0.7 : 1}
      accessible
      accessibilityRole={hasDetails ? "button" : "text"}
      accessibilityLabel={`Recommandation santé: ${insight}`}
      accessibilityHint={hasDetails ? "Appuyez deux fois pour voir les détails des anomalies détectées" : undefined}
      accessibilityState={{ disabled: !hasDetails }}
    >
      {/* Insight principal (grande typographie) */}
      <Text style={styles.insightText}>{insight}</Text>

      {/* Footer avec nombre d'anomalies et chevron */}
      {hasDetails && (
        <View style={styles.footer}>
          <Text style={[styles.anomalyCount, { color: borderColor }]}>
            {anomalies.length} {anomalies.length === 1 ? 'anomalie détectée' : 'anomalies détectées'}
          </Text>
          <ChevronRight size={16} color={borderColor} strokeWidth={2.5} />
        </View>
      )}
    </TouchableOpacity>
  );
}

/**
 * Composant pour l'état "calm" (aucune anomalie)
 */
export function CalmStateCard({ message }: { message?: string }) {
  return (
    <View
      style={[
        styles.container,
        {
          borderLeftColor: STATE_COLORS.calm,
          backgroundColor: STATE_BG_COLORS.calm,
        },
      ]}
      accessible
      accessibilityRole="text"
      accessibilityLabel={`État optimal: ${message || "Votre corps est en parfaite homéostasie. Profitez de ce pic d'énergie."}`}
    >
      <View style={styles.calmContainer}>
        <Text style={styles.calmEmoji}>✨</Text>
        <Text style={styles.calmText}>
          {message || "Votre corps est en parfaite homéostasie."}
        </Text>
        <Text style={styles.calmSubtext}>
          Profitez de ce pic d'énergie
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#1C1C1E',
    borderRadius: 24,
    padding: 24,
    borderLeftWidth: 4,
    marginVertical: 16,
  },
  insightText: {
    color: '#FFFFFF',
    fontSize: 22,
    lineHeight: 32,
    fontWeight: '600',
    letterSpacing: -0.5,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#2C2C2E',
  },
  anomalyCount: {
    fontSize: 13,
    fontWeight: '600',
    letterSpacing: 0.3,
  },
  calmContainer: {
    alignItems: 'center',
    paddingVertical: 8,
  },
  calmEmoji: {
    fontSize: 48,
    marginBottom: 12,
  },
  calmText: {
    color: '#FFFFFF',
    fontSize: 20,
    lineHeight: 28,
    fontWeight: '600',
    textAlign: 'center',
    letterSpacing: -0.3,
  },
  calmSubtext: {
    color: '#8E8E93',
    fontSize: 15,
    marginTop: 8,
    textAlign: 'center',
  },
});
