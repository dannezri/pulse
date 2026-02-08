import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { ReadinessResult } from '../utils/calculateReadiness';

interface Props {
  readiness: ReadinessResult | null;
  loading?: boolean;
}

export function ReadinessScoreCard({ readiness, loading }: Props) {
  if (loading || !readiness) {
    return (
      <View style={styles.container}>
        <Text style={styles.loadingText}>Calcul en cours...</Text>
      </View>
    );
  }

  return (
    <View style={[styles.container, { borderLeftColor: readiness.color }]}>
      <View style={styles.scoreContainer}>
        <Text style={[styles.score, { color: readiness.color }]}>
          {readiness.totalScore}
        </Text>
        <Text style={styles.interpretation}>
          {readiness.interpretationText}
        </Text>
      </View>
      
      <View style={styles.breakdown}>
        <Text style={styles.breakdownText}>
          HRV: {readiness.hrvScore}/45 • Sommeil: {readiness.sleepScore}/40 • RHR: {readiness.rhrScore}/15
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#1C1C1E',
    borderRadius: 20,
    padding: 24,
    borderLeftWidth: 4,
    marginBottom: 24,
  },
  scoreContainer: {
    alignItems: 'center',
    marginBottom: 12,
  },
  score: {
    fontSize: 56,
    fontWeight: '700',
  },
  interpretation: {
    fontSize: 14,
    color: '#8E8E93',
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginTop: 4,
  },
  breakdown: {
    borderTopWidth: 1,
    borderTopColor: '#2C2C2E',
    paddingTop: 12,
  },
  breakdownText: {
    fontSize: 12,
    color: '#8E8E93',
    textAlign: 'center',
  },
  loadingText: {
    color: '#8E8E93',
    fontSize: 14,
    textAlign: 'center',
  },
});
