/**
 * Composant liste des médicaments
 * Design aligné avec le reste de l'app
 */

import React from 'react';
import { View, Text, Alert, StyleSheet } from 'react-native';
import { Medication } from '../hooks/useMedications';
import { PressableScale } from './PressableScale';
import { Pill, Trash2, Clock } from 'lucide-react-native';

interface MedicationListProps {
  medications: Medication[];
  onDelete?: (id: string) => void;
  emptyMessage?: string;
}

export function MedicationList({ 
  medications, 
  onDelete,
  emptyMessage = 'Aucun médicament enregistré'
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
      {medications.map((item) => (
        <View key={item.id} style={styles.card}>
          {/* Header */}
          <View style={styles.cardHeader}>
            <View style={styles.iconContainer}>
              <Pill size={20} color="#34C759" />
            </View>
            <View style={styles.cardInfo}>
              <Text style={styles.medicationName}>{item.name}</Text>
              {item.dosage && (
                <Text style={styles.dosageText}>
                  {item.dosage} {item.unit}
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

          {/* Détails */}
          {(item.frequency || item.notes) && (
            <View style={styles.details}>
              {item.frequency && (
                <View style={styles.detailRow}>
                  <Clock size={14} color="#8E8E93" />
                  <Text style={styles.detailText}>{item.frequency}</Text>
                </View>
              )}
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
              {formatDate(item.takenAt)}
            </Text>
          </View>
        </View>
      ))}
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
  medicationName: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
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
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  detailText: {
    color: '#8E8E93',
    fontSize: 14,
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
});
