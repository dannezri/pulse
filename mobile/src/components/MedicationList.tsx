/**
 * Composant liste des médicaments
 * Design aligné avec le reste de l'app
 */

import React from 'react';
import { View, Text, Alert, StyleSheet } from 'react-native';
import { Medication } from '../hooks/useMedications';
import { MedicationImpact } from '../hooks/useMedicationImpacts';
import { PressableScale } from './PressableScale';
import { Pill, Trash2, Clock, Calendar, Repeat, TrendingUp, TrendingDown, Minus } from 'lucide-react-native';

interface MedicationListProps {
  medications: Medication[];
  onDelete?: (id: string) => void;
  emptyMessage?: string;
  getMedicationImpact?: (medication: Medication) => MedicationImpact | null;
  showImpact?: boolean;
}

// Helper pour formater l'affichage des fractions de comprimés
const formatPillCount = (count: number): string => {
  if (count === 0.25) return '¼';
  if (count === 0.5) return '½';
  if (count === 0.75) return '¾';
  if (count === 1.5) return '1½';
  if (count === 2.5) return '2½';
  return count.toString();
};

export function MedicationList({ 
  medications, 
  onDelete,
  emptyMessage = 'Aucun médicament enregistré',
  getMedicationImpact,
  showImpact = true,
}: MedicationListProps) {
  
  const handleDelete = (med: Medication) => {
    Alert.alert(
      'Supprimer',
      `Voulez-vous supprimer "${med.name}" ?`,
      [
        { text: 'Annuler', style: 'cancel' },
        { 
          text: 'Supprimer', 
          style: 'destructive',
          onPress: () => onDelete?.(med.id)
        }
      ]
    );
  };

  const formatDate = (isoDate: string) => {
    const date = new Date(isoDate);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) {
      return 'À l\'instant';
    } else if (diffMins < 60) {
      return `Il y a ${diffMins} min`;
    } else if (diffHours < 24) {
      return `Il y a ${diffHours}h`;
    } else if (diffDays === 1) {
      return 'Hier';
    } else if (diffDays < 7) {
      return `Il y a ${diffDays}j`;
    } else {
      return date.toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
      });
    }
  };

  if (medications.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyText}>{emptyMessage}</Text>
      </View>
    );
  }

  return (
    <View>
      {medications.map((item) => {
        const impact = showImpact && getMedicationImpact ? getMedicationImpact(item) : null;
        
        return (
          <View key={item.id} style={styles.card}>
            {/* Header */}
            <View style={styles.cardHeader}>
              <View style={styles.iconContainer}>
                <Pill size={20} color="#34C759" />
              </View>
              <View style={styles.cardInfo}>
                <View style={styles.nameRow}>
                  <Text style={styles.medicationName}>{item.name}</Text>
                  {/* Badge pour le type de prise */}
                  {item.isRecurring !== undefined && (
                    <View style={[
                      styles.typeBadge,
                      item.isRecurring ? styles.typeBadgeRecurring : styles.typeBadgePonctuel
                    ]}>
                      {item.isRecurring ? (
                        <Repeat size={12} color="#5E5CE6" />
                      ) : (
                        <Calendar size={12} color="#FF9500" />
                      )}
                      <Text style={[
                        styles.typeBadgeText,
                        item.isRecurring ? styles.typeBadgeTextRecurring : styles.typeBadgeTextPonctuel
                      ]}>
                        {item.isRecurring ? 'Récurrent' : 'Ponctuel'}
                      </Text>
                    </View>
                  )}
                </View>
                {(item.dosage || item.pillsPerIntake) && (
                  <Text style={styles.dosageText}>
                    {item.pillsPerIntake 
                      ? `${formatPillCount(item.pillsPerIntake)} × ` 
                      : ''}{item.dosage || 'Dosage non spécifié'} {item.dosage ? item.unit : ''}
                  </Text>
                )}
              </View>
              {onDelete && (
                <PressableScale
                  onPress={() => handleDelete(item)}
                  style={styles.deleteButton}
                >
                  <Trash2 size={18} color="#FF3B30" />
                </PressableScale>
              )}
            </View>

            {/* Impact énergétique */}
            {impact && (
              <View style={[
                styles.impactContainer,
                impact.status === 'positive' && styles.impactPositive,
                impact.status === 'negative' && styles.impactNegative,
                impact.status === 'neutral' && styles.impactNeutral,
              ]}>
                <View style={styles.impactHeader}>
                  {impact.status === 'positive' && <TrendingUp size={16} color="#34C759" strokeWidth={2.5} />}
                  {impact.status === 'negative' && <TrendingDown size={16} color="#FF3B30" strokeWidth={2.5} />}
                  {impact.status === 'neutral' && <Minus size={16} color="#8E8E93" strokeWidth={2.5} />}
                  <Text style={[
                    styles.impactLabel,
                    impact.status === 'positive' && styles.impactLabelPositive,
                    impact.status === 'negative' && styles.impactLabelNegative,
                    impact.status === 'neutral' && styles.impactLabelNeutral,
                  ]}>
                    Impact sur l'énergie
                  </Text>
                  <Text style={[
                    styles.impactValue,
                    impact.status === 'positive' && styles.impactValuePositive,
                    impact.status === 'negative' && styles.impactValueNegative,
                    impact.status === 'neutral' && styles.impactValueNeutral,
                  ]}>
                    {impact.impactText}
                  </Text>
                </View>
                {impact.description && (
                  <Text style={styles.impactDescription}>
                    {impact.description}
                  </Text>
                )}
              </View>
            )}

          {/* Détails */}
          {(item.frequency || item.intakeTimes || item.notes) && (
            <View style={styles.details}>
              {/* Afficher les heures de prise seulement si récurrent */}
              {item.isRecurring !== false && item.intakeTimes && item.intakeTimes.length > 0 ? (
                <View style={styles.intakeTimesContainer}>
                  <View style={styles.detailRow}>
                    <Clock size={14} color="#8E8E93" />
                    <Text style={styles.detailLabel}>
                      {item.dailyFrequency || item.intakeTimes.length}x par jour
                    </Text>
                  </View>
                  <View style={styles.timeChips}>
                    {item.intakeTimes.map((time, idx) => (
                      <View key={idx} style={styles.timeChip}>
                        <Text style={styles.timeChipText}>{time}</Text>
                      </View>
                    ))}
                  </View>
                </View>
              ) : item.isRecurring === false ? (
                <View style={styles.detailRow}>
                  <Calendar size={14} color="#FF9500" />
                  <Text style={styles.detailText}>Prise unique</Text>
                </View>
              ) : item.frequency ? (
                <View style={styles.detailRow}>
                  <Clock size={14} color="#8E8E93" />
                  <Text style={styles.detailText}>{item.frequency}</Text>
                </View>
              ) : null}
              {item.notes && (
                <View style={styles.notesContainer}>
                  <Text style={styles.notesText}>{item.notes}</Text>
                </View>
              )}
            </View>
          )}

            {/* Footer */}
            <View style={styles.cardFooter}>
              <Text style={styles.timeText}>
                Début: {formatDate(item.takenAt)}
              </Text>
              {item.intakeTimes && item.intakeTimes.length > 0 && (
                <Text style={styles.timeTextSecondary}>
                  Prochaine prise: {item.intakeTimes[0]}
                </Text>
              )}
            </View>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  emptyContainer: {
    padding: 24,
    alignItems: 'center',
  },
  emptyText: {
    color: '#8E8E93',
    fontSize: 14,
    textAlign: 'center',
  },
  card: {
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: 'rgba(52, 199, 89, 0.1)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  cardInfo: {
    flex: 1,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
    flexWrap: 'wrap',
  },
  medicationName: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  typeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  typeBadgeRecurring: {
    backgroundColor: 'rgba(94, 92, 230, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(94, 92, 230, 0.3)',
  },
  typeBadgePonctuel: {
    backgroundColor: 'rgba(255, 149, 0, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(255, 149, 0, 0.3)',
  },
  typeBadgeText: {
    fontSize: 11,
    fontWeight: '600',
  },
  typeBadgeTextRecurring: {
    color: '#5E5CE6',
  },
  typeBadgeTextPonctuel: {
    color: '#FF9500',
  },
  dosageText: {
    color: '#5E5CE6',
    fontSize: 14,
    fontWeight: '500',
  },
  deleteButton: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: 'rgba(255, 59, 48, 0.1)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  details: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#2C2C2E',
  },
  intakeTimesContainer: {
    marginBottom: 8,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  detailLabel: {
    color: '#8E8E93',
    fontSize: 14,
    fontWeight: '600',
  },
  detailText: {
    color: '#8E8E93',
    fontSize: 14,
  },
  timeChips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 4,
  },
  timeChip: {
    backgroundColor: 'rgba(94, 92, 230, 0.15)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(94, 92, 230, 0.3)',
  },
  timeChipText: {
    color: '#5E5CE6',
    fontSize: 13,
    fontWeight: '600',
  },
  notesContainer: {
    backgroundColor: '#0C0C0D',
    borderRadius: 10,
    padding: 12,
    marginTop: 4,
  },
  notesText: {
    color: '#8E8E93',
    fontSize: 13,
    lineHeight: 18,
  },
  cardFooter: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#2C2C2E',
  },
  timeText: {
    color: '#6E6E73',
    fontSize: 12,
    fontWeight: '500',
  },
  timeTextSecondary: {
    color: '#5E5CE6',
    fontSize: 11,
    fontWeight: '600',
    marginTop: 4,
  },
  impactContainer: {
    marginTop: 12,
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
  },
  impactPositive: {
    backgroundColor: 'rgba(52, 199, 89, 0.08)',
    borderColor: 'rgba(52, 199, 89, 0.25)',
  },
  impactNegative: {
    backgroundColor: 'rgba(255, 59, 48, 0.08)',
    borderColor: 'rgba(255, 59, 48, 0.25)',
  },
  impactNeutral: {
    backgroundColor: 'rgba(142, 142, 147, 0.08)',
    borderColor: 'rgba(142, 142, 147, 0.25)',
  },
  impactHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  impactLabel: {
    fontSize: 12,
    fontWeight: '600',
    flex: 1,
  },
  impactLabelPositive: {
    color: '#34C759',
  },
  impactLabelNegative: {
    color: '#FF3B30',
  },
  impactLabelNeutral: {
    color: '#8E8E93',
  },
  impactValue: {
    fontSize: 16,
    fontWeight: '800',
    letterSpacing: 0.3,
  },
  impactValuePositive: {
    color: '#34C759',
  },
  impactValueNegative: {
    color: '#FF3B30',
  },
  impactValueNeutral: {
    color: '#8E8E93',
  },
  impactDescription: {
    fontSize: 12,
    color: '#8E8E93',
    marginTop: 6,
    lineHeight: 16,
  },
});
