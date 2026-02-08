/**
 * FeedbackBottomSheet
 * 
 * Composant pour collecter les feedbacks utilisateurs (ML adaptatif)
 * 
 * Usage:
 * ```tsx
 * <FeedbackBottomSheet
 *   isVisible={showFeedback}
 *   onClose={() => setShowFeedback(false)}
 *   systemScore={2.7}
 *   currentEnergy={2.7}
 *   hoursSinceWake={7.5}
 *   activeFactors={{medications: [...], conditions: [...]}}
 *   onSubmit={(userScore) => console.log('User score:', userScore)}
 * />
 * ```
 * 
 * Trigger conditions:
 * - Énergie < 15% (low_energy_trigger)
 * - Changement brusque > 30 points (energy_spike)
 * - Manuel (bouton "Feedback" dans le profil)
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  Pressable,
  Dimensions,
  ActivityIndicator
} from 'react-native';
import Slider from '@react-native-community/slider';
import { LinearGradient } from 'expo-linear-gradient';
import * as Haptics from 'expo-haptics';

interface FeedbackBottomSheetProps {
  isVisible: boolean;
  onClose: () => void;
  systemScore: number; // 0-100
  currentEnergy: number; // 0-100
  hoursSinceWake: number;
  activeFactors: {
    medications?: Array<{atc_code: string, name: string, impact: number}>;
    conditions?: Array<{icd11_code: string, name: string, decay_rate: number, malus: number}>;
  };
  onSubmit: (userScore: number) => void;
  feedbackContext?: 'low_energy_trigger' | 'energy_spike' | 'manual';
}

const { width, height } = Dimensions.get('window');

export const FeedbackBottomSheet: React.FC<FeedbackBottomSheetProps> = ({
  isVisible,
  onClose,
  systemScore,
  currentEnergy,
  hoursSinceWake,
  activeFactors,
  onSubmit,
  feedbackContext = 'manual'
}) => {
  const [userScore, setUserScore] = useState(50);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSliderChange = (value: number) => {
    setUserScore(Math.round(value));
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    
    try {
      await onSubmit(userScore);
      onClose();
    } catch (error) {
      console.error('[Feedback] Error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score < 30) return '#EF4444'; // red-500
    if (score < 60) return '#F59E0B'; // amber-500
    return '#10B981'; // green-500
  };

  const getScoreLabel = (score: number) => {
    if (score < 20) return 'Épuisé';
    if (score < 40) return 'Fatigué';
    if (score < 60) return 'Moyen';
    if (score < 80) return 'Bien';
    return 'Excellent';
  };

  return (
    <Modal
      visible={isVisible}
      transparent
      animationType="slide"
      onRequestClose={onClose}
    >
      <Pressable
        style={styles.overlay}
        onPress={onClose}
      >
        <Pressable
          style={styles.bottomSheet}
          onPress={(e) => e.stopPropagation()}
        >
          {/* Handle bar */}
          <View style={styles.handleBar} />

          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>💡 Comment te sens-tu ?</Text>
            <Text style={styles.subtitle}>
              Pulse estime ton énergie à{' '}
              <Text style={[styles.systemScore, { color: getScoreColor(systemScore) }]}>
                {Math.round(systemScore)}%
              </Text>
            </Text>
          </View>

          {/* Slider */}
          <View style={styles.sliderContainer}>
            <Text style={[styles.scoreValue, { color: getScoreColor(userScore) }]}>
              {userScore}%
            </Text>
            <Text style={styles.scoreLabel}>{getScoreLabel(userScore)}</Text>

            <View style={styles.sliderWrapper}>
              <LinearGradient
                colors={['#EF4444', '#F59E0B', '#10B981']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.gradientTrack}
              />
              <Slider
                style={styles.slider}
                minimumValue={0}
                maximumValue={100}
                value={userScore}
                onValueChange={handleSliderChange}
                minimumTrackTintColor="transparent"
                maximumTrackTintColor="transparent"
                thumbTintColor="#FFFFFF"
              />
            </View>

            {/* Labels */}
            <View style={styles.labels}>
              <Text style={styles.labelText}>0% · Épuisé</Text>
              <Text style={styles.labelText}>100% · Excellent</Text>
            </View>
          </View>

          {/* Info */}
          <View style={styles.info}>
            <Text style={styles.infoText}>
              ℹ️ Ton feedback aide Pulse à mieux comprendre <Text style={styles.bold}>ton corps</Text>
            </Text>
          </View>

          {/* Buttons */}
          <View style={styles.buttons}>
            <Pressable
              style={[styles.button, styles.cancelButton]}
              onPress={onClose}
            >
              <Text style={styles.cancelButtonText}>Annuler</Text>
            </Pressable>

            <Pressable
              style={[styles.button, styles.submitButton]}
              onPress={handleSubmit}
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={styles.submitButtonText}>Envoyer</Text>
              )}
            </Pressable>
          </View>
        </Pressable>
      </Pressable>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  bottomSheet: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingHorizontal: 24,
    paddingTop: 12,
    paddingBottom: 40,
    maxHeight: height * 0.7,
  },
  handleBar: {
    width: 40,
    height: 4,
    backgroundColor: '#E5E7EB',
    borderRadius: 2,
    alignSelf: 'center',
    marginBottom: 20,
  },
  header: {
    marginBottom: 32,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#6B7280',
    lineHeight: 24,
  },
  systemScore: {
    fontWeight: '600',
  },
  sliderContainer: {
    marginBottom: 24,
  },
  scoreValue: {
    fontSize: 48,
    fontWeight: '800',
    textAlign: 'center',
    marginBottom: 4,
  },
  scoreLabel: {
    fontSize: 18,
    color: '#6B7280',
    textAlign: 'center',
    marginBottom: 24,
  },
  sliderWrapper: {
    height: 40,
    justifyContent: 'center',
    marginBottom: 8,
  },
  gradientTrack: {
    position: 'absolute',
    top: 18,
    left: 0,
    right: 0,
    height: 4,
    borderRadius: 2,
  },
  slider: {
    width: '100%',
    height: 40,
  },
  labels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  labelText: {
    fontSize: 12,
    color: '#9CA3AF',
  },
  info: {
    backgroundColor: '#F3F4F6',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
  },
  infoText: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
  bold: {
    fontWeight: '600',
    color: '#111827',
  },
  buttons: {
    flexDirection: 'row',
    gap: 12,
  },
  button: {
    flex: 1,
    height: 52,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: '#F3F4F6',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
  },
  submitButton: {
    backgroundColor: '#8B5CF6', // violet-500
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});
