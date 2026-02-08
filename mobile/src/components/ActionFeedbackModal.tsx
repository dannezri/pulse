/**
 * ActionFeedbackModal - Modal pour recueillir le feedback utilisateur
 * 
 * Demande à l'utilisateur s'il a suivi la recommandation d'hier pour alimenter
 * le système d'apprentissage personnalisé.
 * 
 * Affiché automatiquement le lendemain matin si pas encore de feedback donné.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { CheckCircle, XCircle, MessageSquare } from 'lucide-react-native';
import { useActionFeedback, translateRecommendationType } from '../hooks/useActionFeedback';

interface ActionFeedbackModalProps {
  visible: boolean;
  onClose: () => void;
}

export const ActionFeedbackModal: React.FC<ActionFeedbackModalProps> = ({
  visible,
  onClose,
}) => {
  const { todayAction, submitFeedback, hasGivenFeedback } = useActionFeedback();
  const [userFeedback, setUserFeedback] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);

  // Ne pas afficher si pas d'action ou feedback déjà donné
  if (!todayAction || hasGivenFeedback) {
    return null;
  }

  const handleSubmit = async (followed: boolean) => {
    setSubmitting(true);
    
    const success = await submitFeedback(
      followed,
      userFeedback.trim() || undefined
    );
    
    setSubmitting(false);
    
    if (success) {
      onClose();
    }
  };

  const recommendationType = translateRecommendationType(todayAction.recommendation_type);

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.overlay}
      >
        <TouchableOpacity
          style={styles.backdrop}
          activeOpacity={1}
          onPress={onClose}
        />

        <View style={styles.modalContainer}>
          <ScrollView
            contentContainerStyle={styles.scrollContent}
            keyboardShouldPersistTaps="handled"
          >
            {/* Header */}
            <View style={styles.header}>
              <Text style={styles.title}>💭 Feedback sur hier</Text>
              <Text style={styles.subtitle}>
                Aide Pulse à mieux te comprendre
              </Text>
            </View>

            {/* Recommandation rappelée */}
            <View style={styles.reminderSection}>
              <Text style={styles.reminderLabel}>Recommandation d'hier :</Text>
              <Text style={styles.reminderText}>
                {todayAction.recommendation_text}
              </Text>
              <Text style={styles.reminderType}>
                Type : {recommendationType}
              </Text>
            </View>

            {/* Question */}
            <View style={styles.questionSection}>
              <Text style={styles.questionText}>
                As-tu suivi cette recommandation ?
              </Text>
            </View>

            {/* Boutons Oui/Non */}
            <View style={styles.buttonsRow}>
              <TouchableOpacity
                style={[styles.button, styles.buttonYes]}
                onPress={() => handleSubmit(true)}
                disabled={submitting}
              >
                <CheckCircle size={24} color="#10b981" strokeWidth={2.5} />
                <Text style={[styles.buttonText, styles.buttonTextYes]}>
                  Oui, suivi
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.button, styles.buttonNo]}
                onPress={() => handleSubmit(false)}
                disabled={submitting}
              >
                <XCircle size={24} color="#ef4444" strokeWidth={2.5} />
                <Text style={[styles.buttonText, styles.buttonTextNo]}>
                  Non, ignoré
                </Text>
              </TouchableOpacity>
            </View>

            {/* Feedback optionnel */}
            <View style={styles.feedbackSection}>
              <View style={styles.feedbackHeader}>
                <MessageSquare size={16} color="#9ca3af" strokeWidth={2} />
                <Text style={styles.feedbackLabel}>
                  Commentaire (optionnel)
                </Text>
              </View>
              <TextInput
                style={styles.feedbackInput}
                placeholder="Ex: Trop difficile, j'avais une soirée..."
                placeholderTextColor="#6b7280"
                value={userFeedback}
                onChangeText={setUserFeedback}
                multiline
                numberOfLines={3}
                maxLength={200}
              />
            </View>

            {/* Skip button */}
            <TouchableOpacity
              style={styles.skipButton}
              onPress={onClose}
            >
              <Text style={styles.skipText}>Plus tard</Text>
            </TouchableOpacity>
          </ScrollView>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
  },
  modalContainer: {
    width: '90%',
    maxWidth: 420,
    maxHeight: '80%',
    backgroundColor: '#1f2937',
    borderRadius: 24,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.4,
    shadowRadius: 24,
    elevation: 16,
  },
  scrollContent: {
    padding: 24,
  },

  // Header
  header: {
    marginBottom: 24,
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: '800',
    color: '#f9fafb',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#9ca3af',
    fontWeight: '500',
  },

  // Reminder
  reminderSection: {
    backgroundColor: '#374151',
    borderRadius: 16,
    padding: 16,
    marginBottom: 24,
  },
  reminderLabel: {
    fontSize: 12,
    color: '#9ca3af',
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  reminderText: {
    fontSize: 15,
    color: '#f9fafb',
    fontWeight: '500',
    lineHeight: 22,
    marginBottom: 8,
  },
  reminderType: {
    fontSize: 12,
    color: '#6b7280',
    fontStyle: 'italic',
  },

  // Question
  questionSection: {
    marginBottom: 20,
  },
  questionText: {
    fontSize: 16,
    color: '#e5e7eb',
    fontWeight: '600',
    textAlign: 'center',
  },

  // Buttons
  buttonsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24,
    gap: 12,
  },
  button: {
    flex: 1,
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    paddingHorizontal: 12,
    borderRadius: 16,
    borderWidth: 2,
    gap: 8,
  },
  buttonYes: {
    backgroundColor: '#10b98115',
    borderColor: '#10b98140',
  },
  buttonNo: {
    backgroundColor: '#ef444415',
    borderColor: '#ef444440',
  },
  buttonText: {
    fontSize: 14,
    fontWeight: '700',
  },
  buttonTextYes: {
    color: '#10b981',
  },
  buttonTextNo: {
    color: '#ef4444',
  },

  // Feedback input
  feedbackSection: {
    marginBottom: 20,
  },
  feedbackHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    gap: 6,
  },
  feedbackLabel: {
    fontSize: 13,
    color: '#9ca3af',
    fontWeight: '600',
  },
  feedbackInput: {
    backgroundColor: '#374151',
    borderRadius: 12,
    padding: 12,
    color: '#f9fafb',
    fontSize: 14,
    minHeight: 80,
    textAlignVertical: 'top',
  },

  // Skip
  skipButton: {
    alignItems: 'center',
    paddingVertical: 12,
  },
  skipText: {
    fontSize: 14,
    color: '#6b7280',
    fontWeight: '600',
  },
});
