/**
 * FeedbackSlider - Composant de capture du feedback utilisateur
 * 
 * Permet à l'utilisateur d'indiquer son niveau d'énergie ressenti
 * pour alimenter le système d'apprentissage adaptatif (ML).
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import Slider from '@react-native-community/slider';
import { X, Send, TrendingUp } from 'lucide-react-native';

interface FeedbackSliderProps {
  systemScore: number; // Score calculé par le système (0-100)
  activeMedications: string[]; // Codes ATC des médicaments actifs
  activeConditions: string[]; // Codes ICD-11 des conditions actives
  onSubmit: (userScore: number) => Promise<void>;
  onDismiss: () => void;
}

export const FeedbackSlider: React.FC<FeedbackSliderProps> = ({
  systemScore,
  activeMedications,
  activeConditions,
  onSubmit,
  onDismiss,
}) => {
  const [userScore, setUserScore] = useState(50);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [fadeAnim] = useState(new Animated.Value(0));

  React.useEffect(() => {
    // Animation d'apparition
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 300,
      useNativeDriver: true,
    }).start();
    
    // Debug: Vérifier que onSubmit est bien défini
    console.log('[FeedbackSlider] onSubmit type:', typeof onSubmit);
    console.log('[FeedbackSlider] onSubmit defined:', onSubmit !== undefined);
  }, []);

  const handleSubmit = async () => {
    console.log('[FeedbackSlider] handleSubmit appelé, userScore:', userScore);
    console.log('[FeedbackSlider] onSubmit est:', typeof onSubmit);
    
    if (typeof onSubmit !== 'function') {
      console.error('[FeedbackSlider] ❌ onSubmit n\'est pas une fonction:', onSubmit);
      return;
    }
    
    setIsSubmitting(true);
    try {
      console.log('[FeedbackSlider] 🚀 Appel onSubmit...');
      await onSubmit(userScore);
      console.log('[FeedbackSlider] ✅ onSubmit terminé');
      
      // Animation de disparition
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 200,
        useNativeDriver: true,
      }).start(() => {
        onDismiss();
      });
    } catch (error) {
      console.error('[FeedbackSlider] ❌ Error submitting feedback:', error);
      setIsSubmitting(false);
    }
  };

  const handleDismiss = () => {
    Animated.timing(fadeAnim, {
      toValue: 0,
      duration: 200,
      useNativeDriver: true,
    }).start(() => {
      onDismiss();
    });
  };

  const getErrorMessage = () => {
    const error = userScore - systemScore;
    if (Math.abs(error) < 10) {
      return "Très proche ! 🎯";
    } else if (error > 0) {
      return `Vous vous sentez mieux (+${Math.round(error)}%) 📈`;
    } else {
      return `Vous vous sentez moins bien (${Math.round(error)}%) 📉`;
    }
  };

  const getScoreColor = (score: number) => {
    if (score < 30) return '#EF4444'; // Rouge
    if (score < 50) return '#F59E0B'; // Orange
    if (score < 70) return '#FCD34D'; // Jaune
    return '#10B981'; // Vert
  };

  return (
    <Animated.View
      style={[
        styles.container,
        {
          opacity: fadeAnim,
          transform: [
            {
              translateY: fadeAnim.interpolate({
                inputRange: [0, 1],
                outputRange: [50, 0],
              }),
            },
          ],
        },
      ]}
    >
      <View style={styles.card}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.titleContainer}>
            <TrendingUp size={20} color="#6366F1" />
            <Text style={styles.title}>Comment vous sentez-vous ?</Text>
          </View>
          <TouchableOpacity onPress={handleDismiss} disabled={isSubmitting}>
            <X size={24} color="#9CA3AF" />
          </TouchableOpacity>
        </View>

        {/* System Score Info */}
        <View style={styles.systemScoreContainer}>
          <Text style={styles.systemScoreLabel}>
            Pulse estime votre énergie à
          </Text>
          <Text
            style={[
              styles.systemScoreValue,
              { color: getScoreColor(systemScore) },
            ]}
          >
            {Math.round(systemScore)}%
          </Text>
        </View>

        {/* User Score Slider */}
        <View style={styles.sliderContainer}>
          <Text style={styles.userScoreLabel}>Votre ressenti :</Text>
          <View style={styles.sliderRow}>
            <Text style={styles.sliderValue}>0%</Text>
            <Slider
              style={styles.slider}
              minimumValue={0}
              maximumValue={100}
              step={5}
              value={userScore}
              onValueChange={setUserScore}
              minimumTrackTintColor={getScoreColor(userScore)}
              maximumTrackTintColor="#E5E7EB"
              thumbTintColor={getScoreColor(userScore)}
            />
            <Text style={styles.sliderValue}>100%</Text>
          </View>
          <Text
            style={[styles.userScoreValue, { color: getScoreColor(userScore) }]}
          >
            {userScore}%
          </Text>
        </View>

        {/* Error Message */}
        <Text style={styles.errorMessage}>{getErrorMessage()}</Text>

        {/* Submit Button */}
        <TouchableOpacity
          style={[
            styles.submitButton,
            isSubmitting && styles.submitButtonDisabled,
          ]}
          onPress={handleSubmit}
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <ActivityIndicator color="#FFF" />
          ) : (
            <>
              <Send size={18} color="#FFF" />
              <Text style={styles.submitButtonText}>Envoyer</Text>
            </>
          )}
        </TouchableOpacity>

        {/* Info Text */}
        <Text style={styles.infoText}>
          Votre feedback aide Pulse à apprendre votre métabolisme unique 🧠
        </Text>
      </View>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    right: 20,
    zIndex: 1000,
  },
  card: {
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 8,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  systemScoreContainer: {
    alignItems: 'center',
    marginBottom: 20,
    padding: 16,
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
  },
  systemScoreLabel: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 8,
  },
  systemScoreValue: {
    fontSize: 36,
    fontWeight: 'bold',
  },
  sliderContainer: {
    marginBottom: 16,
  },
  userScoreLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 12,
  },
  sliderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  slider: {
    flex: 1,
    height: 40,
  },
  sliderValue: {
    fontSize: 12,
    color: '#9CA3AF',
    width: 35,
    textAlign: 'center',
  },
  userScoreValue: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginTop: 8,
  },
  errorMessage: {
    fontSize: 14,
    color: '#6366F1',
    textAlign: 'center',
    marginBottom: 16,
    fontWeight: '500',
  },
  submitButton: {
    backgroundColor: '#6366F1',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  submitButtonDisabled: {
    opacity: 0.6,
  },
  submitButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  infoText: {
    fontSize: 12,
    color: '#9CA3AF',
    textAlign: 'center',
    fontStyle: 'italic',
  },
});
