/**
 * TrendsSummaryCard Component
 * 
 * Affiche un résumé visuel des tendances clés sur 30 jours
 * en haut de l'écran Tendances pour une compréhension rapide.
 * 
 * Format: Emoji + Label + Flèche + Description
 * Exemple: "💚 HRV ↗ amélioration (12%)"
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react-native';
import { TrendsSummary, TrendDirection } from '../hooks/useTrendsSummary';

interface TrendsSummaryCardProps {
  summary: TrendsSummary;
}

const getTrendIcon = (trend: TrendDirection) => {
  switch (trend) {
    case 'up':
      return <TrendingUp size={14} color="#00FF41" />;
    case 'down':
      return <TrendingDown size={14} color="#FF3B30" />;
    case 'stable':
      return <Minus size={14} color="#8E8E93" />;
    case 'insufficient':
      return <Minus size={14} color="#48484A" />;
  }
};

const getTrendColor = (trend: TrendDirection): string => {
  switch (trend) {
    case 'up':
      return '#00FF41';
    case 'down':
      return '#FF3B30';
    case 'stable':
      return '#8E8E93';
    case 'insufficient':
      return '#48484A';
  }
};

export function TrendsSummaryCard({ summary }: TrendsSummaryCardProps) {
  if (!summary.hasData) {
    return (
      <View style={styles.card}>
        <View style={styles.header}>
          <Text style={styles.title}>📊 Résumé sur {summary.period} jours</Text>
        </View>
        <View style={styles.emptyState}>
          <Text style={styles.emptyText}>
            Collectez plus de données pour voir vos tendances automatiques
          </Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.card}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>📊 Résumé sur {summary.period} jours</Text>
        <Text style={styles.subtitle}>
          Tendances automatiques des métriques clés
        </Text>
      </View>

      {/* Metrics Grid */}
      <View style={styles.metricsGrid}>
        {summary.metrics.map((metric, index) => (
          <View 
            key={metric.key} 
            style={[
              styles.metricRow,
              index !== summary.metrics.length - 1 && styles.metricRowBorder
            ]}
          >
            {/* Emoji + Label */}
            <View style={styles.metricLabel}>
              <Text style={styles.metricEmoji}>{metric.emoji}</Text>
              <Text style={styles.metricName}>{metric.label}</Text>
            </View>

            {/* Trend Badge */}
            <View style={styles.trendContainer}>
              <View style={[
                styles.trendBadge,
                { backgroundColor: getTrendColor(metric.trend) + '20' }
              ]}>
                {getTrendIcon(metric.trend)}
                <Text style={[
                  styles.trendText,
                  { color: getTrendColor(metric.trend) }
                ]}>
                  {metric.description}
                </Text>
              </View>
            </View>
          </View>
        ))}
      </View>

      {/* Footer hint */}
      <View style={styles.footer}>
        <Text style={styles.footerText}>
          Scrollez pour voir les graphiques détaillés ↓
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#1C1C1E',
    borderRadius: 20,
    padding: 20,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#2C2C2E',
    // Halo effect subtle
    shadowColor: '#00FF41',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 4,
  },
  header: {
    marginBottom: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 13,
    color: '#8E8E93',
    lineHeight: 18,
  },
  metricsGrid: {
    gap: 0,
  },
  metricRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
  },
  metricRowBorder: {
    borderBottomWidth: 1,
    borderBottomColor: '#2C2C2E',
  },
  metricLabel: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
  },
  metricEmoji: {
    fontSize: 20,
  },
  metricName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  trendContainer: {
    flexShrink: 0,
  },
  trendBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  trendText: {
    fontSize: 13,
    fontWeight: '600',
  },
  footer: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#2C2C2E',
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: '#8E8E93',
    fontStyle: 'italic',
  },
  emptyState: {
    paddingVertical: 20,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 20,
  },
});
