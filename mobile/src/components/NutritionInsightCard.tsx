/**
 * NutritionInsightCard Component
 * 
 * Affiche un insight nutritionnel intelligent avec :
 * - Observation (ce qui a été détecté)
 * - Conséquence (impact sur la santé)
 * - Action recommandée (conseil actionable)
 * 
 * Format visuel : Nutrition → Conséquence → Action
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { AlertCircle, ArrowRight, Lightbulb, TrendingUp, TrendingDown, Info } from 'lucide-react-native';
import type { NutritionInsight, InsightSeverity } from '../hooks/useNutritionInsights';

interface NutritionInsightCardProps {
  insight: NutritionInsight;
  compact?: boolean; // Mode compact pour affichage dans le Brief
}

const getSeverityConfig = (severity: InsightSeverity) => {
  switch (severity) {
    case 'alert':
      return {
        backgroundColor: '#FF3B30',
        borderColor: '#FF3B30',
        icon: <AlertCircle size={18} color="#FFFFFF" />,
        textColor: '#FFFFFF',
      };
    case 'warning':
      return {
        backgroundColor: '#FF9500',
        borderColor: '#FF9500',
        icon: <TrendingDown size={18} color="#FFFFFF" />,
        textColor: '#FFFFFF',
      };
    case 'positive':
      return {
        backgroundColor: '#00FF41',
        borderColor: '#00FF41',
        icon: <TrendingUp size={18} color="#000000" />,
        textColor: '#000000',
      };
    case 'neutral':
      return {
        backgroundColor: '#8E8E93',
        borderColor: '#8E8E93',
        icon: <Info size={18} color="#FFFFFF" />,
        textColor: '#FFFFFF',
      };
  }
};

export function NutritionInsightCard({ insight, compact = false }: NutritionInsightCardProps) {
  const config = getSeverityConfig(insight.severity);

  if (compact) {
    // Mode compact pour le Brief
    return (
      <View style={[styles.cardCompact, { borderLeftColor: config.borderColor }]}>
        <View style={styles.compactHeader}>
          <Text style={styles.compactEmoji}>{insight.emoji}</Text>
          <Text style={styles.compactTitle}>{insight.title}</Text>
        </View>
        <View style={styles.compactFlow}>
          <Text style={styles.compactText}>{insight.observation}</Text>
          <ArrowRight size={14} color="#8E8E93" style={styles.arrow} />
          <Text style={styles.compactText}>{insight.consequence}</Text>
        </View>
        <View style={styles.compactAction}>
          <Lightbulb size={14} color="#00FF41" />
          <Text style={styles.compactActionText}>{insight.action}</Text>
        </View>
      </View>
    );
  }

  // Mode complet pour le Journal
  return (
    <View style={styles.card}>
      {/* Header avec badge de sévérité */}
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Text style={styles.emoji}>{insight.emoji}</Text>
          <View style={styles.titleColumn}>
            <Text style={styles.title}>{insight.title}</Text>
            <Text style={styles.confidence}>
              Fiabilité: {Math.round(insight.confidence * 100)}%
            </Text>
          </View>
        </View>
        <View style={[styles.severityBadge, { backgroundColor: config.backgroundColor }]}>
          {config.icon}
        </View>
      </View>

      {/* Flow: Observation → Conséquence → Action */}
      <View style={styles.flow}>
        {/* Observation */}
        <View style={styles.flowItem}>
          <View style={styles.flowLabel}>
            <View style={[styles.flowDot, { backgroundColor: '#00C7BE' }]} />
            <Text style={styles.flowLabelText}>Observation</Text>
          </View>
          <Text style={styles.flowValue}>{insight.observation}</Text>
        </View>

        <View style={styles.flowArrow}>
          <ArrowRight size={16} color="#8E8E93" />
        </View>

        {/* Conséquence */}
        <View style={styles.flowItem}>
          <View style={styles.flowLabel}>
            <View style={[styles.flowDot, { backgroundColor: config.borderColor }]} />
            <Text style={styles.flowLabelText}>Conséquence</Text>
          </View>
          <Text style={styles.flowValue}>{insight.consequence}</Text>
        </View>

        <View style={styles.flowArrow}>
          <ArrowRight size={16} color="#8E8E93" />
        </View>

        {/* Action */}
        <View style={styles.flowItem}>
          <View style={styles.flowLabel}>
            <View style={[styles.flowDot, { backgroundColor: '#00FF41' }]} />
            <Text style={styles.flowLabelText}>Action</Text>
          </View>
          <Text style={[styles.flowValue, styles.actionValue]}>{insight.action}</Text>
        </View>
      </View>
    </View>
  );
}

// Composant container pour plusieurs insights
interface NutritionInsightsListProps {
  insights: NutritionInsight[];
  compact?: boolean;
}

export function NutritionInsightsList({ insights, compact = false }: NutritionInsightsListProps) {
  if (insights.length === 0) {
    return null;
  }

  return (
    <View style={styles.listContainer}>
      {!compact && (
        <View style={styles.listHeader}>
          <Text style={styles.listTitle}>💡 Insights Nutrition</Text>
          <Text style={styles.listSubtitle}>
            Corrélations automatiques entre ton alimentation et ta santé
          </Text>
        </View>
      )}
      
      <View style={styles.list}>
        {insights.map((insight) => (
          <NutritionInsightCard
            key={insight.id}
            insight={insight}
            compact={compact}
          />
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  // Mode complet
  card: {
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2C2C2E',
    shadowColor: '#00FF41',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
  },
  emoji: {
    fontSize: 28,
  },
  titleColumn: {
    flex: 1,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 2,
  },
  confidence: {
    fontSize: 11,
    color: '#8E8E93',
  },
  severityBadge: {
    borderRadius: 8,
    padding: 6,
    marginLeft: 8,
  },
  flow: {
    gap: 0,
  },
  flowItem: {
    marginBottom: 12,
  },
  flowLabel: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 6,
  },
  flowDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  flowLabelText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#8E8E93',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  flowValue: {
    fontSize: 14,
    color: '#FFFFFF',
    lineHeight: 20,
    paddingLeft: 14,
  },
  actionValue: {
    fontWeight: '600',
    color: '#00FF41',
  },
  flowArrow: {
    paddingLeft: 6,
    paddingVertical: 4,
  },

  // Mode compact
  cardCompact: {
    backgroundColor: '#1C1C1E',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    borderLeftWidth: 3,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  compactHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  compactEmoji: {
    fontSize: 18,
  },
  compactTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
    flex: 1,
  },
  compactFlow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
    flexWrap: 'wrap',
  },
  compactText: {
    fontSize: 12,
    color: '#8E8E93',
  },
  arrow: {
    marginHorizontal: 2,
  },
  compactAction: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 6,
    backgroundColor: '#00FF4110',
    padding: 8,
    borderRadius: 8,
  },
  compactActionText: {
    fontSize: 12,
    color: '#00FF41',
    fontWeight: '600',
    flex: 1,
    lineHeight: 16,
  },

  // Liste
  listContainer: {
    marginBottom: 16,
  },
  listHeader: {
    marginBottom: 12,
  },
  listTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  listSubtitle: {
    fontSize: 13,
    color: '#8E8E93',
    lineHeight: 18,
  },
  list: {
    gap: 0,
  },
});
