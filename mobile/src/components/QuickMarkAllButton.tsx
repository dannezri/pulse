import React, { useState } from 'react';
import { View, Text, StyleSheet, Alert } from 'react-native';
import { CheckCircle, Loader } from 'lucide-react-native';
import { PressableScale } from './PressableScale';
import { useMarkAsTaken } from '@/hooks/useMedicationHistory';
import { Medication } from '@/hooks/useMedications';

interface QuickMarkAllButtonProps {
  medications: Medication[];
}

/**
 * Bouton pour marquer tous les médicaments du jour comme pris en une seule action
 */
export function QuickMarkAllButton({ medications }: QuickMarkAllButtonProps) {
  const { markAsTaken, isLoading } = useMarkAsTaken();
  const [success, setSuccess] = useState(false);

  const handleMarkAll = async () => {
    if (medications.length === 0) return;

    Alert.alert(
      'Confirmer',
      `Marquer les ${medications.length} médicament${medications.length > 1 ? 's' : ''} comme pris aujourd'hui ?`,
      [
        { text: 'Annuler', style: 'cancel' },
        {
          text: 'Confirmer',
          style: 'default',
          onPress: async () => {
            try {
              // Marquer tous les médicaments en parallèle
              await Promise.all(
                medications.map((med) => {
                  const scheduledTime = med.intakeTimes?.[0];
                  return markAsTaken(med.id, scheduledTime);
                })
              );

              setSuccess(true);
              setTimeout(() => setSuccess(false), 3000);
            } catch (error) {
              console.error('[QuickMarkAllButton] Error marking all:', error);
              Alert.alert('Erreur', 'Impossible d\'enregistrer toutes les prises.');
            }
          },
        },
      ]
    );
  };

  if (medications.length === 0) return null;

  return (
    <PressableScale
      onPress={handleMarkAll}
      style={[styles.button, success && styles.buttonSuccess]}
      disabled={isLoading}
    >
      <View style={styles.content}>
        {isLoading ? (
          <Loader size={20} color="#FFFFFF" strokeWidth={2.5} />
        ) : (
          <CheckCircle
            size={20}
            color="#FFFFFF"
            strokeWidth={2.5}
            fill={success ? '#FFFFFF' : 'transparent'}
          />
        )}
        <Text style={styles.text}>
          {isLoading
            ? 'Enregistrement...'
            : success
            ? 'Tous pris ✓'
            : `Marquer tout (${medications.length})`}
        </Text>
      </View>
    </PressableScale>
  );
}

const styles = StyleSheet.create({
  button: {
    backgroundColor: '#5E5CE6',
    borderRadius: 20,
    paddingVertical: 16,
    paddingHorizontal: 24,
    marginVertical: 16,
    shadowColor: '#5E5CE6',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.4,
    shadowRadius: 16,
    elevation: 8,
  },
  buttonSuccess: {
    backgroundColor: '#34C759',
    shadowColor: '#34C759',
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  text: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 0.3,
  },
});
