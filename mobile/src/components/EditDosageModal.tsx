import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Alert,
  ScrollView,
  Platform,
  Keyboard,
  ActivityIndicator,
} from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { X, Save, Pill, FileText, Calendar } from 'lucide-react-native';
import { Medication } from '@/hooks/useMedications';
import { PressableScale } from './PressableScale';

interface EditDosageModalProps {
  visible: boolean;
  medication: Medication | null;
  onClose: () => void;
  onSave: (params: {
    medicationId: string;
    newDosage: string;
    newDosageUnit: string;
    newPillsPerIntake: number;
    effectiveDate: string;
    notes?: string;
  }) => Promise<void>;
}

export const EditDosageModal = React.memo(function EditDosageModal({ 
  visible, 
  medication, 
  onClose, 
  onSave 
}: EditDosageModalProps) {
  const [newDosage, setNewDosage] = useState(medication?.dosage || '');
  const [pillsTaken, setPillsTaken] = useState(medication?.pillsPerIntake?.toString() || '1');
  const [effectiveDate, setEffectiveDate] = useState(new Date());
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [isReady, setIsReady] = useState(false);
  
  React.useEffect(() => {
    if (visible && medication) {
      // Fermer le clavier
      Keyboard.dismiss();
      
      // Initialiser les valeurs immédiatement
      setNewDosage(medication.dosage || '');
      setPillsTaken(medication.pillsPerIntake?.toString() || '1');
      setEffectiveDate(new Date());
      setNotes('');
      setShowDatePicker(false);
      setIsReady(true);
    }
  }, [visible, medication]);

  const handleDateChange = useCallback((event: any, selectedDate?: Date) => {
    setShowDatePicker(Platform.OS === 'ios');
    if (selectedDate) {
      setEffectiveDate(selectedDate);
    }
  }, []);

  const formatDateDisplay = useCallback((date: Date): string => {
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
    });
  }, []);

  const handleIncrementPills = useCallback(() => {
    const current = parseFloat(pillsTaken) || 1;
    setPillsTaken((current + 0.5).toString());
  }, [pillsTaken]);

  const handleDecrementPills = useCallback(() => {
    const current = parseFloat(pillsTaken) || 1;
    if (current > 0.25) {
      setPillsTaken((current - 0.5).toString());
    }
  }, [pillsTaken]);

  const handleSave = useCallback(async () => {
    if (!medication) return;

    if (!newDosage.trim()) {
      Alert.alert('❌ Erreur', 'Veuillez saisir un dosage');
      return;
    }

    const pillsPerIntake = parseFloat(pillsTaken);
    if (isNaN(pillsPerIntake) || pillsPerIntake <= 0) {
      Alert.alert('❌ Erreur', 'Veuillez saisir un nombre de comprimés valide');
      return;
    }

    try {
      setSaving(true);
      await onSave({
        medicationId: medication.id,
        newDosage: newDosage.trim(),
        newDosageUnit: medication.unit || 'mg',
        newPillsPerIntake: pillsPerIntake,
        effectiveDate: effectiveDate.toISOString(),
        notes: notes || undefined,
      });
      Alert.alert('✅ Succès', `La posologie a été modifiée à partir du ${formatDateDisplay(effectiveDate)}`);
      onClose();
    } catch (error: any) {
      Alert.alert('❌ Erreur', error.message || 'Impossible de modifier la posologie');
    } finally {
      setSaving(false);
    }
  }, [medication, newDosage, pillsTaken, effectiveDate, notes, onSave, onClose, formatDateDisplay]);

  // Ne pas rendre si pas de medication (garde le modal monté mais caché)
  if (!medication) return <Modal visible={false} />;

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
      transparent={false}
    >
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Modifier la posologie</Text>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <X size={24} color="#FFFFFF" />
          </TouchableOpacity>
        </View>

        {!isReady ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#5E5CE6" />
            <Text style={styles.loadingText}>Chargement...</Text>
          </View>
        ) : (
        <ScrollView style={styles.content} contentContainerStyle={styles.contentContainer}>
          {/* Medication Name */}
          <View style={styles.medicationHeader}>
            <View style={styles.medicationIconBadge}>
              <Pill size={24} color="#5E5CE6" strokeWidth={2.5} />
            </View>
            <View style={styles.medicationInfo}>
              <Text style={styles.medicationName}>{medication.name}</Text>
              <Text style={styles.medicationDosage}>
                Posologie actuelle : {medication.dosage} {medication.unit}
              </Text>
            </View>
          </View>

          {/* New Dosage */}
          <View style={styles.section}>
            <View style={styles.labelRow}>
              <Pill size={20} color="#5E5CE6" strokeWidth={2.5} />
              <Text style={styles.label}>Nouveau dosage</Text>
            </View>
            <View style={styles.dosageInputRow}>
              <TextInput
                style={[styles.input, styles.dosageInput]}
                value={newDosage}
                onChangeText={setNewDosage}
                placeholder="150"
                placeholderTextColor="#8E8E93"
                keyboardType="numeric"
              />
              <Text style={styles.unitText}>{medication.unit || 'mg'}</Text>
            </View>
          </View>

          {/* Pills Per Intake */}
          <View style={styles.section}>
            <View style={styles.labelRow}>
              <Pill size={20} color="#5E5CE6" strokeWidth={2.5} />
              <Text style={styles.label}>Nombre de comprimés par prise</Text>
            </View>
            <View style={styles.pillsSelectionGrid}>
              {[0.25, 0.5, 1, 1.5, 2, 2.5, 3, 4].map((num) => (
                <PressableScale
                  key={num}
                  onPress={() => setPillsTaken(num.toString())}
                  style={[
                    styles.pillChoiceButton,
                    pillsTaken === num.toString() && styles.pillChoiceButtonActive
                  ]}
                >
                  <Text style={[
                    styles.pillChoiceText,
                    pillsTaken === num.toString() && styles.pillChoiceTextActive
                  ]}>
                    {num === 0.25 ? '¼' : num === 0.5 ? '½' : num === 1.5 ? '1½' : num === 2.5 ? '2½' : num}
                  </Text>
                </PressableScale>
              ))}
            </View>
            <View style={styles.pillsCounter}>
              <TouchableOpacity
                style={styles.pillsButton}
                onPress={handleDecrementPills}
                activeOpacity={0.7}
              >
                <Text style={styles.pillsButtonText}>−</Text>
              </TouchableOpacity>
              
              <View style={styles.pillsDisplay}>
                <Text style={styles.pillsNumber}>{pillsTaken}</Text>
                <Text style={styles.pillsLabel}>comprimé{parseFloat(pillsTaken) > 1 ? 's' : ''}</Text>
              </View>
              
              <TouchableOpacity
                style={styles.pillsButton}
                onPress={handleIncrementPills}
                activeOpacity={0.7}
              >
                <Text style={styles.pillsButtonText}>+</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Effective Date */}
          <View style={styles.section}>
            <View style={styles.labelRow}>
              <Calendar size={20} color="#5E5CE6" strokeWidth={2.5} />
              <Text style={styles.label}>Date d'effet de la modification</Text>
            </View>
            <TouchableOpacity
              style={styles.dateButton}
              onPress={() => setShowDatePicker(true)}
              activeOpacity={0.7}
            >
              <Calendar size={20} color="#5E5CE6" strokeWidth={2} />
              <Text style={styles.dateButtonText}>
                {formatDateDisplay(effectiveDate)}
              </Text>
            </TouchableOpacity>
            
            {showDatePicker && (
              <DateTimePicker
                value={effectiveDate}
                mode="date"
                display={Platform.OS === 'ios' ? 'spinner' : 'default'}
                onChange={handleDateChange}
                maximumDate={new Date()}
              />
            )}
          </View>

          {/* Notes */}
          <View style={styles.section}>
            <View style={styles.labelRow}>
              <FileText size={20} color="#5E5CE6" strokeWidth={2.5} />
              <Text style={styles.label}>Raison de la modification (optionnel)</Text>
            </View>
            <TextInput
              style={[styles.input, styles.textArea]}
              value={notes}
              onChangeText={setNotes}
              placeholder="Ex: Augmentation suite à consultation médecin..."
              placeholderTextColor="#8E8E93"
              multiline
              numberOfLines={4}
              textAlignVertical="top"
            />
          </View>

          {/* Save Button */}
          <TouchableOpacity
            style={[styles.saveButton, saving && styles.saveButtonDisabled]}
            onPress={handleSave}
            disabled={saving}
            activeOpacity={0.8}
          >
            <Save size={20} color="#FFFFFF" strokeWidth={2.5} />
            <Text style={styles.saveButtonText}>{saving ? 'Enregistrement...' : 'Enregistrer'}</Text>
          </TouchableOpacity>
        </ScrollView>
        )}
      </View>
    </Modal>
  );
});

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0A0A12',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
    backgroundColor: 'rgba(13, 13, 31, 0.95)',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(94, 92, 230, 0.2)',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: -0.5,
  },
  closeButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 22,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.05)',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    fontWeight: '600',
    color: '#8E8E93',
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 20,
    paddingBottom: 40,
  },
  section: {
    marginBottom: 28,
  },
  medicationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    backgroundColor: 'rgba(94, 92, 230, 0.1)',
    borderWidth: 2,
    borderColor: 'rgba(94, 92, 230, 0.3)',
    borderRadius: 20,
    padding: 20,
    marginBottom: 32,
  },
  medicationIconBadge: {
    width: 56,
    height: 56,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(94, 92, 230, 0.2)',
    borderRadius: 16,
  },
  medicationInfo: {
    flex: 1,
  },
  medicationName: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
    letterSpacing: -0.3,
  },
  medicationDosage: {
    fontSize: 15,
    fontWeight: '600',
    color: '#5E5CE6',
  },
  labelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 14,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    letterSpacing: 0.2,
  },
  input: {
    backgroundColor: 'rgba(26, 26, 46, 0.6)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
    padding: 18,
    fontSize: 16,
    color: '#FFFFFF',
  },
  textArea: {
    minHeight: 120,
    textAlignVertical: 'top',
  },
  dosageInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  dosageInput: {
    flex: 1,
  },
  unitText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#5E5CE6',
    marginRight: 8,
  },
  dateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: 'rgba(26, 26, 46, 0.6)',
    borderWidth: 1.5,
    borderColor: 'rgba(94, 92, 230, 0.3)',
    borderRadius: 16,
    padding: 18,
  },
  dateButtonText: {
    fontSize: 17,
    fontWeight: '600',
    color: '#FFFFFF',
    flex: 1,
  },
  pillsSelectionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 16,
  },
  pillChoiceButton: {
    minWidth: 60,
    height: 48,
    paddingHorizontal: 12,
    backgroundColor: 'rgba(26, 26, 46, 0.6)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pillChoiceButtonActive: {
    backgroundColor: 'rgba(94, 92, 230, 0.2)',
    borderColor: '#5E5CE6',
    borderWidth: 2,
  },
  pillChoiceText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#8E8E93',
  },
  pillChoiceTextActive: {
    color: '#5E5CE6',
    fontWeight: '700',
  },
  pillsCounter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 16,
  },
  pillsButton: {
    width: 56,
    height: 56,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(94, 92, 230, 0.15)',
    borderWidth: 1.5,
    borderColor: 'rgba(94, 92, 230, 0.3)',
    borderRadius: 16,
  },
  pillsButtonText: {
    fontSize: 28,
    fontWeight: '700',
    color: '#5E5CE6',
  },
  pillsDisplay: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(26, 26, 46, 0.6)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
    paddingVertical: 20,
  },
  pillsNumber: {
    fontSize: 32,
    fontWeight: '900',
    color: '#FFFFFF',
    marginBottom: 4,
    letterSpacing: -1,
  },
  pillsLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#8E8E93',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  saveButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    backgroundColor: '#5E5CE6',
    borderRadius: 20,
    paddingVertical: 20,
    marginTop: 32,
    shadowColor: '#5E5CE6',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.5,
    shadowRadius: 20,
    elevation: 12,
  },
  saveButtonDisabled: {
    opacity: 0.5,
  },
  saveButtonText: {
    fontSize: 18,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: 0.3,
  },
});
