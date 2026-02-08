/**
 * Formulaire avancé d'ajout de traitement
 * Support récurrence complète, durée, jours de semaine
 * Route: /add-treatment?medicationId=...&medicationName=...
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Alert,
  Platform
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { ChevronLeft, Calendar, Clock, Plus, X } from 'lucide-react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { API_URL } from '@/config/api';
import { storage } from '@/lib/storage';
import { PressableScale } from '@/components/PressableScale';

const WEEKDAYS = [
  { id: 1, label: 'Lun', short: 'L' },
  { id: 2, label: 'Mar', short: 'M' },
  { id: 3, label: 'Mer', short: 'M' },
  { id: 4, label: 'Jeu', short: 'J' },
  { id: 5, label: 'Ven', short: 'V' },
  { id: 6, label: 'Sam', short: 'S' },
  { id: 7, label: 'Dim', short: 'D' },
];

const UNITS = ['mg', 'g', 'µg', 'mL', 'comprimé', 'gélule', 'dose'];

export default function AddTreatmentScreen() {
  const params = useLocalSearchParams();
  const medicationId = params.medicationId as string;
  const medicationName = params.medicationName as string;

  // Posologie
  const [dosage, setDosage] = useState('');
  const [unit, setUnit] = useState('mg');
  const [pillsPerIntake, setPillsPerIntake] = useState('1');

  // Fréquence
  const [scheduleType, setScheduleType] = useState<'once' | 'recurring'>('recurring');
  const [selectedWeekdays, setSelectedWeekdays] = useState<number[]>([1, 2, 3, 4, 5]); // Lun-Ven par défaut
  const [intakeTimes, setIntakeTimes] = useState<string[]>(['08:00']);
  const [showTimePicker, setShowTimePicker] = useState(false);
  const [editingTimeIndex, setEditingTimeIndex] = useState<number | null>(null);

  // Dates
  const [startDate, setStartDate] = useState(new Date());
  const [showStartDatePicker, setShowStartDatePicker] = useState(false);

  // Durée
  const [endMode, setEndMode] = useState<'indefinite' | 'until_date' | 'duration_days'>('indefinite');
  const [endDate, setEndDate] = useState(new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)); // +30 jours
  const [showEndDatePicker, setShowEndDatePicker] = useState(false);
  const [durationDays, setDurationDays] = useState('30');

  // Notes
  const [notes, setNotes] = useState('');

  const [submitting, setSubmitting] = useState(false);

  const toggleWeekday = (day: number) => {
    if (selectedWeekdays.includes(day)) {
      // Ne pas permettre de tout désélectionner
      if (selectedWeekdays.length > 1) {
        setSelectedWeekdays(selectedWeekdays.filter(d => d !== day));
      }
    } else {
      setSelectedWeekdays([...selectedWeekdays, day].sort());
    }
  };

  const addIntakeTime = () => {
    if (intakeTimes.length < 6) {
      setIntakeTimes([...intakeTimes, '08:00']);
    }
  };

  const removeIntakeTime = (index: number) => {
    if (intakeTimes.length > 1) {
      setIntakeTimes(intakeTimes.filter((_, i) => i !== index));
    }
  };

  const updateIntakeTime = (index: number, time: Date) => {
    const hours = time.getHours().toString().padStart(2, '0');
    const minutes = time.getMinutes().toString().padStart(2, '0');
    const timeString = `${hours}:${minutes}`;
    
    const updated = [...intakeTimes];
    updated[index] = timeString;
    setIntakeTimes(updated);
    setShowTimePicker(false);
    setEditingTimeIndex(null);
  };

  const handleSubmit = async () => {
    // Validation
    if (!medicationName) {
      Alert.alert('Erreur', 'Nom du médicament requis');
      return;
    }

    if (!dosage.trim()) {
      Alert.alert('Erreur', 'Le dosage est requis');
      return;
    }

    if (scheduleType === 'recurring') {
      if (selectedWeekdays.length === 0) {
        Alert.alert('Erreur', 'Sélectionnez au moins un jour de la semaine');
        return;
      }
      if (intakeTimes.length === 0) {
        Alert.alert('Erreur', 'Ajoutez au moins une heure de prise');
        return;
      }
    }

    if (endMode === 'until_date' && endDate <= startDate) {
      Alert.alert('Erreur', 'La date de fin doit être après la date de début');
      return;
    }

    if (endMode === 'duration_days') {
      const days = parseInt(durationDays);
      if (isNaN(days) || days <= 0) {
        Alert.alert('Erreur', 'La durée doit être un nombre positif');
        return;
      }
    }

    setSubmitting(true);

    try {
      // Récupérer le JWT token
      const token = await storage.getAuthToken();
      if (!token) {
        Alert.alert('Erreur', 'Vous devez être connecté');
        setSubmitting(false);
        return;
      }

      const payload = {
        medication_id: medicationId || null,
        medication_name: medicationName,
        dosage: dosage.trim(),
        unit: unit,
        pills_per_intake: parseFloat(pillsPerIntake) || 1,
        schedule_type: scheduleType,
        weekdays: scheduleType === 'recurring' ? selectedWeekdays : null,
        intake_times: scheduleType === 'recurring' ? intakeTimes : null,
        start_date: startDate.toISOString().split('T')[0],
        end_mode: endMode,
        end_date: endMode === 'until_date' ? endDate.toISOString().split('T')[0] : null,
        duration_days: endMode === 'duration_days' ? parseInt(durationDays) : null,
        notes: notes.trim() || null
      };

      const response = await fetch(`${API_URL}/treatments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erreur lors de la création du traitement');
      }

      const result = await response.json();
      console.log('[AddTreatment] Traitement créé:', result);

      Alert.alert(
        '✅ Traitement ajouté',
        'Votre traitement a été enregistré avec succès.',
        [
          {
            text: 'OK',
            onPress: () => {
              // Retour à la liste des médicaments ou à l'écran précédent
              router.back();
            }
          }
        ]
      );
    } catch (error: any) {
      console.error('[AddTreatment] Erreur:', error);
      Alert.alert(
        'Erreur',
        error.message || 'Impossible d\'ajouter le traitement. Veuillez réessayer.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <ChevronLeft size={28} color="#FFFFFF" strokeWidth={2.5} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Ajouter un traitement</Text>
        <View style={{width: 28}} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Médicament */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Médicament</Text>
          <View style={styles.medicationCard}>
            <Text style={styles.medicationName}>{medicationName}</Text>
          </View>
        </View>

        {/* Posologie */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Posologie</Text>
          <View style={styles.row}>
            <View style={[styles.inputContainer, {flex: 1}]}>
              <Text style={styles.label}>Dosage</Text>
              <TextInput
                style={styles.input}
                placeholder="500"
                placeholderTextColor="#8E8EA0"
                keyboardType="numeric"
                value={dosage}
                onChangeText={setDosage}
              />
            </View>
            <View style={[styles.inputContainer, {flex: 1, marginLeft: 12}]}>
              <Text style={styles.label}>Unité</Text>
              <View style={styles.pickerButton}>
                <Text style={styles.pickerButtonText}>{unit}</Text>
              </View>
            </View>
          </View>
          <View style={styles.inputContainer}>
            <Text style={styles.label}>Quantité par prise</Text>
            <View style={styles.pillsContainer}>
              {[0.25, 0.5, 1, 1.5, 2].map((num) => (
                <PressableScale
                  key={num}
                  onPress={() => setPillsPerIntake(num.toString())}
                  style={[
                    styles.pillButton,
                    pillsPerIntake === num.toString() && styles.pillButtonActive
                  ]}
                >
                  <Text style={[
                    styles.pillButtonText,
                    pillsPerIntake === num.toString() && styles.pillButtonTextActive
                  ]}>
                    {num === 0.25 ? '¼' : num === 0.5 ? '½' : num === 1.5 ? '1½' : num}
                  </Text>
                </PressableScale>
              ))}
              <TextInput
                value={pillsPerIntake}
                onChangeText={setPillsPerIntake}
                placeholder="Autre"
                placeholderTextColor="#8E8EA0"
                keyboardType="decimal-pad"
                style={[styles.input, styles.pillsInput]}
              />
            </View>
          </View>
        </View>

        {/* Type de prise */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Type de prise</Text>
          <View style={styles.toggleContainer}>
            <TouchableOpacity
              style={[styles.toggleButton, scheduleType === 'once' && styles.toggleButtonActive]}
              onPress={() => setScheduleType('once')}
            >
              <Text style={[styles.toggleButtonText, scheduleType === 'once' && styles.toggleButtonTextActive]}>
                Prise unique
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.toggleButton, scheduleType === 'recurring' && styles.toggleButtonActive]}
              onPress={() => setScheduleType('recurring')}
            >
              <Text style={[styles.toggleButtonText, scheduleType === 'recurring' && styles.toggleButtonTextActive]}>
                Récurrent
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Récurrence */}
        {scheduleType === 'recurring' && (
          <>
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Jours de la semaine</Text>
              <View style={styles.weekdaysContainer}>
                {WEEKDAYS.map(day => (
                  <TouchableOpacity
                    key={day.id}
                    style={[
                      styles.weekdayButton,
                      selectedWeekdays.includes(day.id) && styles.weekdayButtonActive
                    ]}
                    onPress={() => toggleWeekday(day.id)}
                  >
                    <Text style={[
                      styles.weekdayText,
                      selectedWeekdays.includes(day.id) && styles.weekdayTextActive
                    ]}>
                      {day.short}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <View style={styles.section}>
              <View style={styles.sectionHeader}>
                <Text style={styles.sectionTitle}>Heures de prise</Text>
                <TouchableOpacity onPress={addIntakeTime} disabled={intakeTimes.length >= 6}>
                  <Plus size={24} color={intakeTimes.length >= 6 ? '#8E8EA0' : '#5E5CE6'} />
                </TouchableOpacity>
              </View>
              {intakeTimes.map((time, index) => (
                <View key={index} style={styles.timeRow}>
                  <TouchableOpacity
                    style={styles.timeButton}
                    onPress={() => {
                      setEditingTimeIndex(index);
                      setShowTimePicker(true);
                    }}
                  >
                    <Clock size={20} color="#5E5CE6" />
                    <Text style={styles.timeText}>{time}</Text>
                  </TouchableOpacity>
                  {intakeTimes.length > 1 && (
                    <TouchableOpacity onPress={() => removeIntakeTime(index)}>
                      <X size={24} color="#FF4444" />
                    </TouchableOpacity>
                  )}
                </View>
              ))}
            </View>
          </>
        )}

        {/* Date de début */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Date de début</Text>
          <TouchableOpacity
            style={styles.dateButton}
            onPress={() => setShowStartDatePicker(true)}
          >
            <Calendar size={20} color="#5E5CE6" />
            <Text style={styles.dateText}>
              {startDate.toLocaleDateString('fr-FR', {
                day: '2-digit',
                month: 'long',
                year: 'numeric'
              })}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Durée du traitement */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Durée du traitement</Text>
          
          <TouchableOpacity
            style={styles.radioRow}
            onPress={() => setEndMode('indefinite')}
          >
            <View style={styles.radio}>
              {endMode === 'indefinite' && <View style={styles.radioSelected} />}
            </View>
            <Text style={styles.radioLabel}>Indéfiniment</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.radioRow}
            onPress={() => setEndMode('until_date')}
          >
            <View style={styles.radio}>
              {endMode === 'until_date' && <View style={styles.radioSelected} />}
            </View>
            <Text style={styles.radioLabel}>Jusqu'au</Text>
          </TouchableOpacity>
          {endMode === 'until_date' && (
            <TouchableOpacity
              style={[styles.dateButton, {marginLeft: 32, marginTop: 8}]}
              onPress={() => setShowEndDatePicker(true)}
            >
              <Calendar size={20} color="#5E5CE6" />
              <Text style={styles.dateText}>
                {endDate.toLocaleDateString('fr-FR', {
                  day: '2-digit',
                  month: 'long',
                  year: 'numeric'
                })}
              </Text>
            </TouchableOpacity>
          )}

          <TouchableOpacity
            style={[styles.radioRow, {marginTop: 12}]}
            onPress={() => setEndMode('duration_days')}
          >
            <View style={styles.radio}>
              {endMode === 'duration_days' && <View style={styles.radioSelected} />}
            </View>
            <Text style={styles.radioLabel}>Pendant</Text>
          </TouchableOpacity>
          {endMode === 'duration_days' && (
            <View style={[styles.row, {marginLeft: 32, alignItems: 'center', marginTop: 8}]}>
              <TextInput
                style={[styles.input, {flex: 0, width: 80}]}
                placeholder="30"
                placeholderTextColor="#8E8EA0"
                keyboardType="number-pad"
                value={durationDays}
                onChangeText={setDurationDays}
              />
              <Text style={[styles.label, {marginLeft: 12, marginBottom: 0}]}>jours</Text>
            </View>
          )}
        </View>

        {/* Notes */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Notes (optionnel)</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            placeholder="Ex: Avec repas, avant de dormir..."
            placeholderTextColor="#8E8EA0"
            multiline
            numberOfLines={3}
            value={notes}
            onChangeText={setNotes}
          />
        </View>

        {/* Bouton de validation */}
        <TouchableOpacity
          style={[styles.submitButton, submitting && styles.submitButtonDisabled]}
          onPress={handleSubmit}
          disabled={submitting}
        >
          <Text style={styles.submitButtonText}>
            {submitting ? 'Enregistrement...' : 'Ajouter le traitement'}
          </Text>
        </TouchableOpacity>

        <View style={{height: 40}} />
      </ScrollView>

      {/* Date pickers */}
      {showStartDatePicker && (
        <DateTimePicker
          value={startDate}
          mode="date"
          display={Platform.OS === 'ios' ? 'inline' : 'default'}
          onChange={(event, date) => {
            setShowStartDatePicker(Platform.OS === 'ios');
            if (date) setStartDate(date);
          }}
        />
      )}

      {showEndDatePicker && (
        <DateTimePicker
          value={endDate}
          mode="date"
          display={Platform.OS === 'ios' ? 'inline' : 'default'}
          minimumDate={startDate}
          onChange={(event, date) => {
            setShowEndDatePicker(Platform.OS === 'ios');
            if (date) setEndDate(date);
          }}
        />
      )}

      {showTimePicker && editingTimeIndex !== null && (
        <DateTimePicker
          value={new Date(`2000-01-01T${intakeTimes[editingTimeIndex]}:00`)}
          mode="time"
          display={Platform.OS === 'ios' ? 'spinner' : 'default'}
          onChange={(event, date) => {
            if (Platform.OS === 'android') {
              setShowTimePicker(false);
            }
            if (date) updateIntakeTime(editingTimeIndex, date);
          }}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0D0D1F',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
  },
  headerTitle: {
    flex: 1,
    fontSize: 20,
    fontWeight: '600',
    color: '#FFFFFF',
    textAlign: 'center',
    marginHorizontal: 10,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 12,
  },
  medicationCard: {
    backgroundColor: '#1A1A2E',
    padding: 16,
    borderRadius: 12,
  },
  medicationName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  row: {
    flexDirection: 'row',
  },
  inputContainer: {
    marginBottom: 12,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: '#8E8EA0',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#1A1A2E',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: '#FFFFFF',
  },
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  pickerButton: {
    backgroundColor: '#1A1A2E',
    borderRadius: 12,
    padding: 16,
  },
  pickerButtonText: {
    fontSize: 16,
    color: '#FFFFFF',
  },
  toggleContainer: {
    flexDirection: 'row',
    backgroundColor: '#1A1A2E',
    borderRadius: 12,
    padding: 4,
  },
  toggleButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderRadius: 8,
  },
  toggleButtonActive: {
    backgroundColor: '#5E5CE620',
  },
  toggleButtonText: {
    fontSize: 15,
    fontWeight: '500',
    color: '#8E8EA0',
  },
  toggleButtonTextActive: {
    color: '#5E5CE6',
    fontWeight: '600',
  },
  weekdaysContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  weekdayButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#1A1A2E',
    alignItems: 'center',
    justifyContent: 'center',
  },
  weekdayButtonActive: {
    backgroundColor: '#5E5CE6',
  },
  weekdayText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8EA0',
  },
  weekdayTextActive: {
    color: '#FFFFFF',
  },
  timeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  timeButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#1A1A2E',
    padding: 16,
    borderRadius: 12,
  },
  timeText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  dateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#1A1A2E',
    padding: 16,
    borderRadius: 12,
  },
  dateText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  radioRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  radio: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#5E5CE6',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  radioSelected: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#5E5CE6',
  },
  radioLabel: {
    fontSize: 16,
    color: '#FFFFFF',
  },
  pillsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flexWrap: 'wrap',
  },
  pillButton: {
    minWidth: 50,
    height: 48,
    paddingHorizontal: 16,
    backgroundColor: '#1A1A2E',
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: 'transparent',
  },
  pillButtonActive: {
    backgroundColor: '#5E5CE620',
    borderColor: '#5E5CE6',
  },
  pillButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#8E8EA0',
  },
  pillButtonTextActive: {
    color: '#5E5CE6',
  },
  pillsInput: {
    flex: 1,
    minWidth: 80,
    height: 48,
  },
  submitButton: {
    backgroundColor: '#5E5CE6',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  submitButtonDisabled: {
    opacity: 0.5,
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});
