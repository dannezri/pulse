/**
 * LearningStatsCard - Affiche les stats d'apprentissage personnalisé
 * 
 * Montre à l'utilisateur comment Pulse apprend de ses actions et améliore
 * ses prédictions au fil du temps.
 * 
 * Affiché dans l'écran Profil.
 */

import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { Brain, TrendingUp, CheckCircle, Target } from 'lucide-react-native';
import { useLearningStats, translateRecommendationType } from '../hooks/useActionFeedback';

export const LearningStatsCard: React.FC = () => {
  const { stats, loading } = useLearningStats();

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="small" color="#00FF41" />
      </View>
    );
  }

  if (!stats || stats.total_recommendations === 0) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Brain size={24} color="#8b5cf6" strokeWidth={2.5} />
          <Text style={styles.title}>Apprentissage Personnalisé</Text>
        </View>
        <Text style={styles.emptyText}>
          Pulse va bientôt commencer à apprendre de tes actions pour mieux te comprendre.
        </Text>
      </View>
    );
  }

  const followRate = Math.round((stats.follow_rate || 0) * 100);
  const predictionError = Math.round(stats.avg_prediction_error || 0);
  const accuracy = 100 - Math.min(predictionError, 100);

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Brain size={24} color="#8b5cf6" strokeWidth={2.5} />
        <Text style={styles.title}>Apprentissage Personnalisé</Text>
      </View>

      {/* Stats Grid */}
      <View style={styles.statsGrid}>
        {/* Total recommandations */}
        <View style={styles.statBox}>
          <Target size={20} color="#3b82f6" strokeWidth={2} />
          <Text style={styles.statValue}>{stats.total_recommendations}</Text>
          <Text style={styles.statLabel}>Recommandations</Text>
        </View>

        {/* Taux de suivi */}
        <View style={styles.statBox}>
          <CheckCircle size={20} color="#10b981" strokeWidth={2} />
          <Text style={styles.statValue}>{followRate}%</Text>
          <Text style={styles.statLabel}>Suivies</Text>
        </View>

        {/* Précision */}
        <View style={styles.statBox}>
          <TrendingUp size={20} color="#f59e0b" strokeWidth={2} />
          <Text style={styles.statValue}>{accuracy}%</Text>
          <Text style={styles.statLabel}>Précision</Text>
        </View>
      </View>

      {/* Best recommendation */}
      {stats.best_recommendation && stats.best_impact > 0 && (
        <View style={styles.bestRecSection}>
          <Text style={styles.bestRecLabel}>🏆 Ta meilleure action :</Text>
          <Text style={styles.bestRecText}>
            {translateRecommendationType(stats.best_recommendation)}
          </Text>
          <Text style={styles.bestRecImpact}>
            Impact moyen : {stats.best_impact > 0 ? '+' : ''}{Math.round(stats.best_impact)}% d'énergie
          </Text>
        </View>
      )}

      {/* Explication */}
      <View style={styles.explanationSection}>
        <Text style={styles.explanationText}>
          Pulse apprend de tes actions pour affiner ses prédictions et recommandations.
          Plus tu donnes de feedback, plus il devient précis !
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#1f2937',
    borderRadius: 20,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 6,
  },

  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    gap: 12,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#f9fafb',
  },

  // Empty state
  emptyText: {
    fontSize: 14,
    color: '#9ca3af',
    lineHeight: 20,
    textAlign: 'center',
    paddingVertical: 12,
  },

  // Stats Grid
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
    gap: 12,
  },
  statBox: {
    flex: 1,
    backgroundColor: '#374151',
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
    gap: 8,
  },
  statValue: {
    fontSize: 24,
    fontWeight: '800',
    color: '#f9fafb',
  },
  statLabel: {
    fontSize: 11,
    color: '#9ca3af',
    fontWeight: '600',
    textAlign: 'center',
  },

  // Best recommendation
  bestRecSection: {
    backgroundColor: '#8b5cf615',
    borderWidth: 1,
    borderColor: '#8b5cf640',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
  },
  bestRecLabel: {
    fontSize: 12,
    color: '#9ca3af',
    fontWeight: '600',
    marginBottom: 8,
  },
  bestRecText: {
    fontSize: 15,
    color: '#8b5cf6',
    fontWeight: '700',
    marginBottom: 6,
  },
  bestRecImpact: {
    fontSize: 13,
    color: '#d1d5db',
    fontWeight: '500',
  },

  // Explanation
  explanationSection: {
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#374151',
  },
  explanationText: {
    fontSize: 12,
    color: '#9ca3af',
    lineHeight: 18,
    textAlign: 'center',
  },
});
