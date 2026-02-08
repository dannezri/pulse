import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { CheckCircle2, AlertTriangle, XCircle, TrendingUp, TrendingDown, Minus } from 'lucide-react-native';
import { Baseline, BaselineData } from '@/hooks/useBaselines';

interface BaselineCardProps {
  baseline: Baseline;
}

/**
 * Retourne l'icône de statut selon l'état de la baseline
 */
const getStatusIcon = (status: Baseline['status']) => {
  switch (status) {
    case 'ok':
      return <CheckCircle2 size={18} color="#34C759" />;
    case 'insufficient_data':
      return <AlertTriangle size={18} color="#FFCC00" />;
    case 'error':
      return <XCircle size={18} color="#FF3B30" />;
    default:
      return null;
  }
};

/**
 * Retourne l'icône de tendance selon la direction
 */
const getTrendIcon = (direction: BaselineData['trend']['direction']) => {
  switch (direction) {
    case 'up':
      return <TrendingUp size={16} color="#34C759" />;
    case 'down':
      return <TrendingDown size={16} color="#FF3B30" />;
    case 'flat':
      return <Minus size={16} color="#8E8E93" />;
    default:
      return null;
  }
};

/**
 * Formatte le nom du type de baseline pour l'affichage
 */
const formatBaselineTitle = (baselineType: string): string => {
  const titles: Record<string, string> = {
    sleep: 'Sommeil',
    hrv: 'Variabilité Cardiaque (HRV)',
    caffeine_sensitivity: 'Sensibilité à la Caféine',
    alcohol_sensitivity: 'Sensibilité à l\'Alcool',
    recovery_time: 'Temps de Récupération',
    late_meal_impact: 'Impact des Repas Tardifs',
    chronotype: 'Chronotype',
  };

  return titles[baselineType] || baselineType.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
};

/**
 * Composant générique pour afficher une baseline
 * Fonctionne pour tous les types grâce à la structure standardisée
 */
export default function BaselineCard({ baseline }: BaselineCardProps) {
  const {
    baseline_type,
    baseline_data,
    calculated_at,
    confidence,
    sample_size,
    status,
    error_message,
    window_start,
    window_end,
  } = baseline;

  const { value, unit, normal_range, trend, details } = baseline_data;

  const title = formatBaselineTitle(baseline_type);

  return (
    <View style={styles.card}>
      {/* Header avec titre et statut */}
      <View style={styles.header}>
        <Text style={styles.title}>{title}</Text>
        <View style={styles.statusContainer}>
          {getStatusIcon(status)}
          <Text
            style={[
              styles.statusText,
              status === 'ok' && styles.statusOk,
              status === 'insufficient_data' && styles.statusWarning,
              status === 'error' && styles.statusError,
            ]}
          >
            {status === 'ok' ? 'OK' : status === 'insufficient_data' ? 'Données insuffisantes' : 'Erreur'}
          </Text>
        </View>
      </View>

      {/* Contenu selon le statut */}
      {status === 'ok' ? (
        <>
          {/* Valeur principale */}
          <Text style={styles.value}>
            {value} {unit}
          </Text>

          {/* Range normal */}
          {normal_range && normal_range.min !== 0 && normal_range.max !== 0 && (
            <Text style={styles.range}>
              Normal: {normal_range.min} - {normal_range.max} {unit}
            </Text>
          )}

          {/* Tendance */}
          {trend && trend.direction !== 'flat' && (
            <View style={styles.trendContainer}>
              {getTrendIcon(trend.direction)}
              <Text style={styles.trendText}>
                Tendance: {trend.slope_per_week > 0 ? '+' : ''}
                {trend.slope_per_week} {unit}/semaine ({trend.direction === 'up' ? 'hausse' : 'baisse'})
              </Text>
            </View>
          )}

          {/* Confiance */}
          <View style={styles.confidenceContainer}>
            <Text style={styles.confidenceLabel}>Confiance:</Text>
            <View style={styles.confidenceBar}>
              <View
                style={[
                  styles.confidenceFill,
                  {
                    width: `${confidence * 100}%`,
                    backgroundColor: confidence >= 0.7 ? '#34C759' : confidence >= 0.3 ? '#FFCC00' : '#FF3B30',
                  },
                ]}
              />
            </View>
            <Text style={styles.confidenceText}>{(confidence * 100).toFixed(0)}%</Text>
          </View>

          {/* Détails supplémentaires (sample_size toujours affiché) */}
          <Text style={styles.sampleSize}>{sample_size} échantillons analysés</Text>
        </>
      ) : (
        /* Message d'erreur ou d'avertissement */
        <Text style={styles.errorMessage}>{error_message || 'Impossible de calculer la baseline.'}</Text>
      )}

      {/* Footer: Période et date de calcul */}
      {window_start && window_end && (
        <Text style={styles.windowDates}>
          Période: {new Date(window_start).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })} -{' '}
          {new Date(window_end).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })}
        </Text>
      )}
      <Text style={styles.calculatedAt}>
        Dernier calcul: {new Date(calculated_at).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    flex: 1,
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '500',
  },
  statusOk: {
    color: '#34C759',
  },
  statusWarning: {
    color: '#FFCC00',
  },
  statusError: {
    color: '#FF3B30',
  },
  value: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  range: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 8,
  },
  trendContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 12,
  },
  trendText: {
    fontSize: 14,
    color: '#8E8E93',
  },
  confidenceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  confidenceLabel: {
    fontSize: 14,
    color: '#8E8E93',
    width: 80,
  },
  confidenceBar: {
    flex: 1,
    height: 8,
    backgroundColor: '#2C2C2E',
    borderRadius: 4,
    overflow: 'hidden',
  },
  confidenceFill: {
    height: '100%',
    borderRadius: 4,
  },
  confidenceText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
    width: 40,
    textAlign: 'right',
  },
  sampleSize: {
    fontSize: 12,
    color: '#6C6C6E',
    marginBottom: 8,
  },
  errorMessage: {
    fontSize: 14,
    color: '#FF3B30',
    fontStyle: 'italic',
    marginVertical: 12,
  },
  windowDates: {
    fontSize: 11,
    color: '#6C6C6E',
    marginTop: 8,
  },
  calculatedAt: {
    fontSize: 11,
    color: '#6C6C6E',
    marginTop: 4,
  },
});
