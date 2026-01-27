import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { Activity } from "lucide-react-native";

interface RecoveryScoreProps {
  score: number;
}

export function RecoveryScore({ score }: RecoveryScoreProps) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return "#34C759";
    if (score >= 60) return "#FFD60A";
    if (score >= 40) return "#FF9500";
    return "#FF3B30";
  };

  const getScoreLabel = (score: number) => {
    if (score >= 80) return "Excellent";
    if (score >= 60) return "Bon";
    if (score >= 40) return "Moyen";
    if (score > 0) return "Faible";
    return "En attente";
  };

  const getScoreEmoji = (score: number) => {
    if (score >= 80) return "🚀";
    if (score >= 60) return "💪";
    if (score >= 40) return "😊";
    if (score > 0) return "😴";
    return "⏳";
  };

  const color = getScoreColor(score);
  const label = getScoreLabel(score);
  const emoji = getScoreEmoji(score);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Activity size={14} color="#8E8E93" strokeWidth={2} />
        <Text style={styles.headerText}>Récupération</Text>
      </View>

      <View style={styles.scoreContainer}>
        <Text style={styles.emoji}>{emoji}</Text>
        <Text style={[styles.score, { color }]}>{score}</Text>
        <View style={[styles.labelBadge, { backgroundColor: `${color}15` }]}>
          <Text style={[styles.label, { color }]}>{label}</Text>
        </View>
      </View>

      {score === 0 && (
        <Text style={styles.syncHint}>Synchronisez vos données</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#1C1C1E",
    borderRadius: 20,
    padding: 16,
    alignItems: "center",
    justifyContent: "center",
    minWidth: 120,
    borderWidth: 1,
    borderColor: "#2C2C2E",
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 8,
    gap: 4,
  },
  headerText: {
    color: "#8E8E93",
    fontSize: 11,
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  scoreContainer: {
    alignItems: "center",
  },
  emoji: {
    fontSize: 32,
    marginBottom: 4,
  },
  score: {
    fontSize: 36,
    fontWeight: "700",
  },
  labelBadge: {
    marginTop: 4,
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  label: {
    fontSize: 11,
    fontWeight: "700",
  },
  syncHint: {
    color: "#8E8E93",
    fontSize: 10,
    marginTop: 8,
    textAlign: "center",
  },
});
