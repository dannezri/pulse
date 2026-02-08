import React, { useState, useMemo, useCallback } from 'react';
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
import { X, Save, Clock, Pill, FileText, CheckCircle2, XCircle, AlertCircle } from 'lucide-react-native';
import { MedicationIntake } from '@/hooks/useMedicationHistory';
import { PressableScale } from './PressableScale';

interface EditIntakeModalProps {
  visible: boolean;
  intake: MedicationIntake | null;
  onClose: () => void;
  onSave: (params: {
    intakeId: string;
    intakeTime?: string;
    pillsTaken?: number;
    status?: 'taken' | 'skipped' | 'late' | 'early';
    notes?: string;
  }) => Promise<void>;
}

export const EditIntakeModal = React.memo(function EditIntakeModal({ visible, intake, onClose, onSave }: EditIntakeModalProps) {
  const [intakeTime, setIntakeTime] = useState(intake?.intake_time || '');
  const [showTimePicker, setShowTimePicker] = useState(false);
  const [pillsTaken, setPillsTaken] = useState(intake?.pills_taken.toString() || '1');
  const [status, setStatus] = useState<'taken' | 'skipped' | 'late' | 'early'>(intake?.status || 'taken');
  const [notes, setNotes] = useState(intake?.notes || '');
  const [saving, setSaving] = useState(false);
  const [isReady, setIsReady] = useState(false);
  
  React.useEffect(() => {
    if (visible && intake) {
      // Fermer le clavier
      Keyboard.dismiss();
      
      // Initialiser les valeurs immédiatement
      setIntakeTime(intake.intake_time || '');
      setPillsTaken(intake.pills_taken.toString());
      setStatus(intake.status);
      setNotes(intake.notes || '');
      setShowTimePicker(false);
      setIsReady(true);
    }
  }, [visible, intake]);

  const handleTimeChange = useCallback((event: any, selectedDate?: Date) => {
    setShowTimePicker(Platform.OS === 'ios');
    if (selectedDate) {
      const hours = selectedDate.getHours().toString().padStart(2, '0');
      const minutes = selectedDate.getMinutes().toString().padStart(2, '0');
      setIntakeTime(`${hours}:${minutes}:00`);
    }
  }, []);

  const getTimeDate = useCallback((): Date => {
    if (intakeTime) {
      const [hours, minutes] = intakeTime.split(':').map(Number);
      const date = new Date();
      date.setHours(hours || 12);
      date.setMinutes(minutes || 0);
      return date;
    }
    return new Date();
  }, [intakeTime]);

  const formatTimeDisplay = useCallback((time: string): string => {
    if (!time) return 'Sélectionner une heure';
    const [hours, minutes] = time.split(':');
    return `${hours}:${minutes}`;
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
    if (!intake) return;

    try {
      setSaving(true);
      await onSave({
        intakeId: intake.id,
        intakeTime: intakeTime || undefined,
        pillsTaken: pillsTaken ? parseFloat(pillsTaken) : undefined,
        status,
        notes: notes || undefined,
      });
      Alert.alert('✅ Succès', 'La prise a été modifiée');
      onClose();
    } catch (error: any) {
      Alert.alert('❌ Erreur', error.message || 'Impossible de modifier la prise');
    } finally {
      setSaving(false);
    }
  }, [intake, intakeTime, pillsTaken, status, notes, onSave, onClose]);

  // Mémoiser les fonctions helper
  const statusConfig = useMemo(() => ({
    taken: { icon: <CheckCircle2 size={18} color="#34C759" strokeWidth={2.5} />, label: 'Pris' },
    skipped: { icon: <XCircle size={18} color="#FF3B30" strokeWidth={2.5} />, label: 'Oublié' },
    late: { icon: <AlertCircle size={18} color="#FF9500" strokeWidth={2.5} />, label: 'En retard' },
    early: { icon: <AlertCircle size={18} color="#FF9500" strokeWidth={2.5} />, label: 'En avance' },
  }), []);

  const getStatusIcon = (s: string) => statusConfig[s as keyof typeof statusConfig]?.icon || null;
  const getStatusLabel = (s: string) => statusConfig[s as keyof typeof statusConfig]?.label || s;

  // Ne pas rendre si pas d'intake (garde le modal monté mais caché)
  if (!intake) return <Modal visible={false} />;


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
          <Text style={styles.headerTitle}>Modifier la prise</Text>
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
              <Text style={styles.medicationName}>{intake.medication?.medication_name}</Text>
              <Text style={styles.medicationDosage}>
                {intake.medication?.dosage} {intake.medication?.dosage_unit}
              </Text>
            </View>
          </View>

          {/* Intake Time */}
          <View style={styles.section}>
            <View style={styles.labelRow}>
              <Clock size={20} color="#5E5CE6" strokeWidth={2.5} />
              <Text style={styles.label}>Heure de prise</Text>
            </View>
            <TouchableOpacity
              style={styles.timeButton}
              onPress={() => setShowTimePicker(true)}
              activeOpacity={0.7}
            >
              <Clock size={20} color="#5E5CE6" strokeWidth={2} />
              <Text style={styles.timeButtonText}>
                {formatTimeDisplay(intakeTime)}
              </Text>
            </TouchableOpacity>
            
            {showTimePicker && (
              <DateTimePicker
                value={getTimeDate()}
                mode="time"
                is24Hour={true}
                display={Platform.OS === 'ios' ? 'spinner' : 'default'}
                onChange={handleTimeChange}
              />
            )}
          </View>

          {/* Pills Taken */}
          <View style={styles.section}>
            <View style={styles.labelRow}>
              <Pill size={20} color="#5E5CE6" strokeWidth={2.5} />
              <Text style={styles.label}>Nombre de comprimés</Text>
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

          {/* Status */}
          <View style={styles.section}>
            <View style={styles.labelRow}>
              <CheckCircle2 size={20} color="#5E5CE6" strokeWidth={2.5} />
              <Text style={styles.label}>Statut de la prise</Text>
            </View>
            <View style={styles.statusGrid}>
              {(['taken', 'skipped', 'late', 'early'] as const).map((s) => (
                <TouchableOpacity
                  key={s}
                  style={[styles.statusCard, status === s && styles.statusCardActive]}
                  onPress={() => setStatus(s)}
                  activeOpacity={0.7}
                >
                  <View style={styles.statusIconContainer}>
                    {getStatusIcon(s)}
                  </View>
                  <Text style={[styles.statusCardText, status === s && styles.statusCardTextActive]}>
                    {getStatusLabel(s)}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Notes */}
          <View style={styles.section}>
            <View style={styles.labelRow}>
              <FileText size={20} color="#5E5CE6" strokeWidth={2.5} />
              <Text style={styles.label}>Notes (optionnel)</Text>
            </View>
            <TextInput
              style={[styles.input, styles.textArea]}
              value={notes}
              onChangeText={setNotes}
              placeholder="Ajouter une note personnelle..."
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
  timeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: 'rgba(26, 26, 46, 0.6)',
    borderWidth: 1.5,
    borderColor: 'rgba(94, 92, 230, 0.3)',
    borderRadius: 16,
    padding: 18,
  },
  timeButtonText: {
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
  statusGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  statusCard: {
    flex: 1,
    minWidth: '47%',
    alignItems: 'center',
    backgroundColor: 'rgba(26, 26, 46, 0.6)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
    padding: 16,
    gap: 8,
  },
  statusCardActive: {
    backgroundColor: 'rgba(94, 92, 230, 0.2)',
    borderColor: '#5E5CE6',
    borderWidth: 2,
  },
  statusIconContainer: {
    marginBottom: 4,
  },
  statusCardText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E93',
    textAlign: 'center',
  },
  statusCardTextActive: {
    color: '#5E5CE6',
    fontWeight: '700',
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
