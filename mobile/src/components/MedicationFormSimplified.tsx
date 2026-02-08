/**
 * Formulaire simplifié pour ajouter un médicament
 * Design par étapes (wizard) pour une meilleure UX
 */

import React, { useState } from 'react';
import { View, Text, TextInput, StyleSheet, Alert, TouchableOpacity, Platform } from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { PressableScale } from './PressableScale';
import { MedicationAutocomplete } from './MedicationAutocomplete';
import { CustomTimePicker } from './CustomTimePicker';
import type { MedicationSuggestion } from '../services/GiygasMedicationAPI';
import { Pill, Clock, Check, ChevronRight, Calendar, Repeat, Edit2 } from 'lucide-react-native';

interface MedicationFormSimplifiedProps {
  onSubmit: (medication: {
    name: string;
    dosage?: string;
    unit?: string;
    pillsPerIntake?: number;
    frequency?: string;
    intakeTimes?: string[];
    dailyFrequency?: number;
    isRecurring?: boolean;
    takenAt: string;
  }) => void;
  onCancel?: () => void;
}

export function MedicationFormSimplified({ onSubmit, onCancel }: MedicationFormSimplifiedProps) {
  // États du formulaire
  const [step, setStep] = useState(1); // Étape actuelle (1-4)
  const [name, setName] = useState('');
  const [dosage, setDosage] = useState('');
  const [unit, setUnit] = useState('mg');
  const [pillsPerIntake, setPillsPerIntake] = useState<number>(1);
  const [selectedMedication, setSelectedMedication] = useState<MedicationSuggestion | null>(null);
  
  // Étape 2 : Type de prise
  const [isRecurring, setIsRecurring] = useState<boolean>(true);
  
  // Étape 3 : Fréquence et heures
  const [dailyFrequency, setDailyFrequency] = useState<number>(1);
  const [intakeTimes, setIntakeTimes] = useState<string[]>(['08:00']);
  const [showTimePickerForIndex, setShowTimePickerForIndex] = useState<number | null>(null);
  const [initialPickerValue, setInitialPickerValue] = useState<Date | null>(null);
  
  // Date de début du traitement (pour les traitements récurrents)
  const [startDate, setStartDate] = useState<Date>(new Date());
  const [showStartDatePicker, setShowStartDatePicker] = useState<boolean>(false);
  
  // Fonction helper pour créer une Date depuis une heure (HH:MM) - Pour Android uniquement
  const createDateFromTime = (timeString: string): Date => {
    const [hoursStr, minutesStr] = timeString.split(':');
    const hours = parseInt(hoursStr, 10);
    const minutes = parseInt(minutesStr, 10);
    
    if (isNaN(hours) || isNaN(minutes)) {
      const now = new Date();
      const year = now.getFullYear();
      const month = now.getMonth();
      const day = now.getDate();
      return new Date(year, month, day, 8, 0, 0, 0);
    }
    
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();
    const day = now.getDate();
    return new Date(year, month, day, hours, minutes, 0, 0);
  };
  
  // Heures de prise prédéfinies selon la fréquence
  const getDefaultTimes = (freq: number): string[] => {
    const times = {
      1: ['08:00'],
      2: ['08:00', '20:00'],
      3: ['08:00', '14:00', '20:00'],
      4: ['08:00', '12:00', '16:00', '20:00'],
    };
    return times[freq as keyof typeof times] || ['08:00'];
  };

  const handleSelectMedication = (medication: MedicationSuggestion) => {
    setSelectedMedication(medication);
    setName(medication.name);
    
    // Extraction automatique du dosage si disponible
    if (medication.dosage) {
      const match = medication.dosage.match(/^(\d+(?:\.\d+)?)\s*([a-zµμ]+|UI)$/i);
      if (match) {
        setDosage(match[1]);
        setUnit(match[2].toLowerCase());
      }
    }
  };

  // Gérer le changement de fréquence
  const handleFrequencyChange = (freq: number) => {
    setDailyFrequency(freq);
    setIntakeTimes(getDefaultTimes(freq));
  };

  // Mettre à jour une heure spécifique
  const updateIntakeTime = (index: number, time: string) => {
    const updated = [...intakeTimes];
    updated[index] = time;
    setIntakeTimes(updated);
  };

  // Gérer le changement de temps depuis le picker (Android uniquement)
  const handleTimeChange = (event: any, selectedDate?: Date) => {
    // Sur Android, fermer le picker et sauvegarder immédiatement
    setShowTimePickerForIndex(null);
    setInitialPickerValue(null);
    
    if (selectedDate && showTimePickerForIndex !== null && event.type !== 'dismissed') {
      const hours = selectedDate.getHours().toString().padStart(2, '0');
      const minutes = selectedDate.getMinutes().toString().padStart(2, '0');
      console.log('[Picker] ✅ Android - Heure sélectionnée:', hours, ':', minutes);
      updateIntakeTime(showTimePickerForIndex, `${hours}:${minutes}`);
    }
  };

  // Gérer le changement de date de début
  const handleStartDateChange = (event: any, selectedDate?: Date) => {
    // Sur Android, fermer immédiatement après la sélection
    if (Platform.OS === 'android') {
      setShowStartDatePicker(false);
      if (selectedDate) {
        setStartDate(selectedDate);
      }
      return;
    }
    
    // Sur iOS, mettre à jour la date mais NE PAS fermer le picker
    // L'utilisateur doit cliquer sur le bouton "OK" pour confirmer
    if (selectedDate) {
      setStartDate(selectedDate);
    }
  };

  // Formater la date pour l'affichage
  const formatDate = (date: Date): string => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const dateToCheck = new Date(date);
    dateToCheck.setHours(0, 0, 0, 0);

    if (dateToCheck.getTime() === today.getTime()) {
      return "Aujourd'hui";
    }

    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    if (dateToCheck.getTime() === tomorrow.getTime()) {
      return 'Demain';
    }

    return date.toLocaleDateString('fr-FR', {
      weekday: 'short',
      day: 'numeric',
      month: 'long',
    });
  };

  const handleSubmit = () => {
    if (!name.trim()) {
      Alert.alert('Erreur', 'Veuillez entrer le nom du médicament');
      return;
    }

    const frequencyText = isRecurring 
      ? `${dailyFrequency}x par jour à ${intakeTimes.join(', ')}`
      : 'Prise ponctuelle';

    // Utiliser la date de début choisie pour les traitements récurrents, sinon aujourd'hui
    const medicationDate = isRecurring ? startDate : new Date();

    onSubmit({
      name: name.trim(),
      dosage: dosage.trim() || undefined,
      unit: unit.trim() || undefined,
      pillsPerIntake: pillsPerIntake,
      frequency: frequencyText,
      intakeTimes: isRecurring ? intakeTimes : undefined,
      dailyFrequency: isRecurring ? dailyFrequency : undefined,
      isRecurring,
      takenAt: medicationDate.toISOString(),
    });

    // Reset
    setStep(1);
    setName('');
    setDosage('');
    setUnit('mg');
    setPillsPerIntake(1);
    setDailyFrequency(1);
    setIntakeTimes(['08:00']);
    setIsRecurring(true);
    setStartDate(new Date());
    setSelectedMedication(null);
  };

  const canGoNext = () => {
    if (step === 1) return name.trim().length > 0;
    if (step === 2) return true; // Type de prise toujours valide
    if (step === 3) return isRecurring ? dailyFrequency > 0 : true;
    return true;
  };

  const nextStep = () => {
    if (!canGoNext()) return;
    
    // Si on est à l'étape 2 et c'est ponctuel, on saute l'étape 3
    if (step === 2 && !isRecurring) {
      setStep(4);
    } else if (step < 4) {
      setStep(step + 1);
    }
  };

  const prevStep = () => {
    // Si on est à l'étape 4 et c'est ponctuel, on revient à l'étape 2
    if (step === 4 && !isRecurring) {
      setStep(2);
    } else if (step > 1) {
      setStep(step - 1);
    }
  };

  // Calculer le nombre total d'étapes selon le type
  const totalSteps = isRecurring ? 4 : 3;
  const currentDisplayStep = step > 2 && !isRecurring ? step - 1 : step;

  return (
    <View style={styles.container}>
      {/* Progress Indicator */}
      <View style={styles.progressContainer}>
        {Array.from({ length: totalSteps }).map((_, idx) => {
          const s = idx + 1;
          const isActive = s === currentDisplayStep;
          const isCompleted = s < currentDisplayStep;
          
          return (
            <View key={s} style={styles.progressStepContainer}>
              <View style={[
                styles.progressDot,
                isActive && styles.progressDotActive,
                isCompleted && styles.progressDotCompleted
              ]}>
                {isCompleted ? (
                  <Check size={14} color="#FFFFFF" strokeWidth={3} />
                ) : (
                  <Text style={[
                    styles.progressDotText,
                    isActive && styles.progressDotTextActive
                  ]}>
                    {s}
                  </Text>
                )}
              </View>
              {s < totalSteps && <View style={[
                styles.progressLine,
                isCompleted && styles.progressLineCompleted
              ]} />}
            </View>
          );
        })}
      </View>

      {/* Step Title */}
      <Text style={styles.stepTitle}>
        {step === 1 && '🔍 Quel médicament ?'}
        {step === 2 && '📋 Type de prise'}
        {step === 3 && '⏰ Fréquence et heures'}
        {step === 4 && '✅ Confirmation'}
      </Text>

      {/* Step 1: Medication Selection */}
      {step === 1 && (
        <View style={styles.stepContent}>
          <MedicationAutocomplete
            value={name}
            onChangeText={setName}
            onSelectMedication={handleSelectMedication}
            placeholder="Ex: Doliprane, Ibuprofène..."
          />
          
          {selectedMedication && (
            <View style={styles.selectedCard}>
              <View style={styles.selectedIconContainer}>
                <Pill size={24} color="#34C759" />
              </View>
              <View style={styles.selectedInfo}>
                <Text style={styles.selectedName}>{selectedMedication.name}</Text>
                {selectedMedication.form && (
                  <Text style={styles.selectedDetail}>{selectedMedication.form}</Text>
                )}
                {selectedMedication.laboratory && (
                  <Text style={styles.selectedLab}>{selectedMedication.laboratory}</Text>
                )}
              </View>
            </View>
          )}

          <Text style={styles.hint}>
            💡 Tapez au moins 2 lettres pour voir les suggestions
          </Text>
        </View>
      )}

      {/* Step 2: Intake Type (Ponctuel / Récurrent) */}
      {step === 2 && (
        <View style={styles.stepContent}>
          <Text style={styles.label}>S'agit-il d'une prise ponctuelle ou récurrente ?</Text>
          
          <View style={styles.typeGrid}>
            <PressableScale
              onPress={() => setIsRecurring(false)}
              style={[
                styles.typeCard,
                !isRecurring && styles.typeCardActive
              ]}
            >
              <View style={[
                styles.typeIconContainer,
                !isRecurring && styles.typeIconContainerActive
              ]}>
                <Calendar size={28} color={!isRecurring ? '#FFFFFF' : '#FF9500'} />
              </View>
              <Text style={[
                styles.typeTitle,
                !isRecurring && styles.typeTextActive
              ]}>
                Ponctuel
              </Text>
              <Text style={[
                styles.typeDescription,
                !isRecurring && styles.typeDescriptionActive
              ]}>
                Une seule prise
              </Text>
            </PressableScale>

            <PressableScale
              onPress={() => setIsRecurring(true)}
              style={[
                styles.typeCard,
                isRecurring && styles.typeCardActive
              ]}
            >
              <View style={[
                styles.typeIconContainer,
                isRecurring && styles.typeIconContainerActive
              ]}>
                <Repeat size={28} color={isRecurring ? '#FFFFFF' : '#5E5CE6'} />
              </View>
              <Text style={[
                styles.typeTitle,
                isRecurring && styles.typeTextActive
              ]}>
                Récurrent
              </Text>
              <Text style={[
                styles.typeDescription,
                isRecurring && styles.typeDescriptionActive
              ]}>
                Prise régulière
              </Text>
            </PressableScale>
          </View>

          {/* Pills Per Intake */}
          <View style={styles.pillsSection}>
            <Text style={styles.label}>Nombre de comprimés par prise</Text>
            <View style={styles.pillsGrid}>
              {[0.25, 0.5, 1, 2, 3, 4].map((count) => (
                <PressableScale
                  key={count}
                  onPress={() => setPillsPerIntake(count)}
                  style={[
                    styles.pillButton,
                    pillsPerIntake === count && styles.pillButtonActive
                  ]}
                >
                  <Pill size={20} color={pillsPerIntake === count ? '#FFFFFF' : '#5E5CE6'} />
                  <Text style={[
                    styles.pillButtonText,
                    pillsPerIntake === count && styles.pillButtonTextActive
                  ]}>
                    {count === 0.25 ? '¼' : count === 0.5 ? '½' : count}
                  </Text>
                </PressableScale>
              ))}
              <TouchableOpacity
                onPress={() => {
                  Alert.prompt(
                    'Nombre de comprimés',
                    'Entrez le nombre de comprimés par prise',
                    (value) => {
                      const num = parseInt(value, 10);
                      if (!isNaN(num) && num > 0 && num <= 20) {
                        setPillsPerIntake(num);
                      } else {
                        Alert.alert('Erreur', 'Veuillez entrer un nombre entre 1 et 20');
                      }
                    },
                    'plain-text',
                    pillsPerIntake.toString()
                  );
                }}
                style={[
                  styles.pillButton,
                  pillsPerIntake > 4 && styles.pillButtonActive
                ]}
              >
                <Edit2 size={16} color={pillsPerIntake > 4 ? '#FFFFFF' : '#5E5CE6'} />
                <Text style={[
                  styles.pillButtonText,
                  pillsPerIntake > 4 && styles.pillButtonTextActive
                ]}>
                  {pillsPerIntake > 4 ? pillsPerIntake : 'Autre'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          <Text style={styles.hint}>
            💡 Choisissez "Récurrent" pour un traitement quotidien
          </Text>
        </View>
      )}

      {/* Step 3: Frequency & Times (only for recurring) */}
      {step === 3 && isRecurring && (
        <View style={styles.stepContent}>
          <Text style={styles.label}>Combien de fois par jour ?</Text>
          
          <View style={styles.frequencyGrid}>
            {[1, 2, 3, 4].map((freq) => (
              <PressableScale
                key={freq}
                onPress={() => handleFrequencyChange(freq)}
                style={[
                  styles.frequencyCard,
                  dailyFrequency === freq && styles.frequencyCardActive
                ]}
              >
                <View style={[
                  styles.frequencyIconContainer,
                  dailyFrequency === freq && styles.frequencyIconContainerActive
                ]}>
                  <Clock size={24} color={dailyFrequency === freq ? '#FFFFFF' : '#5E5CE6'} />
                </View>
                <Text style={[
                  styles.frequencyText,
                  dailyFrequency === freq && styles.frequencyTextActive
                ]}>
                  {freq}x/jour
                </Text>
              </PressableScale>
            ))}
          </View>

          {/* Start Date Selection */}
          <View style={styles.dateSection}>
            <Text style={styles.timesLabel}>Date de début du traitement</Text>
            <TouchableOpacity
              onPress={() => setShowStartDatePicker(true)}
              style={styles.dateButton}
            >
              <Calendar size={20} color="#5E5CE6" />
              <Text style={styles.dateButtonText}>{formatDate(startDate)}</Text>
              <Edit2 size={16} color="#8E8E93" />
            </TouchableOpacity>
          </View>

          {/* Start Date Picker */}
          {showStartDatePicker && (
            <View style={styles.datePickerContainer}>
              <DateTimePicker
                value={startDate}
                mode="date"
                display={Platform.OS === 'ios' ? 'spinner' : 'default'}
                onChange={handleStartDateChange}
                maximumDate={new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)}
                locale="fr-FR"
              />
              {Platform.OS === 'ios' && (
                <PressableScale
                  onPress={() => setShowStartDatePicker(false)}
                  style={styles.datePickerDone}
                >
                  <Text style={styles.datePickerDoneText}>OK</Text>
                </PressableScale>
              )}
            </View>
          )}

          {/* Time Customization */}
          <View style={styles.timesSection}>
            <Text style={styles.timesLabel}>Heures de prise</Text>
            <View style={styles.timesGrid}>
              {intakeTimes.map((time, index) => (
                <TouchableOpacity
                  key={index}
                  onPress={() => {
                    console.log('[Picker] Ouverture du picker pour l\'heure:', time);
                    // Sur Android, initialiser initialPickerValue
                    if (Platform.OS === 'android') {
                      const dateValue = createDateFromTime(time);
                      setInitialPickerValue(dateValue);
                    }
                    setShowTimePickerForIndex(index);
                  }}
                  style={styles.timeChip}
                >
                  <Clock size={16} color="#5E5CE6" />
                  <Text style={styles.timeChipText}>{time}</Text>
                  <Edit2 size={14} color="#8E8E93" />
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Time Picker */}
          {showTimePickerForIndex !== null && Platform.OS === 'ios' && (
            <View style={styles.timePickerContainer}>
              <CustomTimePicker
                initialHour={parseInt(intakeTimes[showTimePickerForIndex].split(':')[0], 10) || 8}
                initialMinute={parseInt(intakeTimes[showTimePickerForIndex].split(':')[1], 10) || 0}
                onConfirm={(hour, minute) => {
                  const formattedTime = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
                  console.log('[Picker] ✅ Confirmation:', formattedTime);
                  updateIntakeTime(showTimePickerForIndex, formattedTime);
                  setShowTimePickerForIndex(null);
                }}
                onCancel={() => setShowTimePickerForIndex(null)}
              />
            </View>
          )}

          {/* Time Picker Android */}
          {showTimePickerForIndex !== null && Platform.OS === 'android' && initialPickerValue && (
            <View style={styles.timePickerContainer}>
              <DateTimePicker
                value={initialPickerValue}
                mode="time"
                is24Hour={true}
                display="default"
                onChange={handleTimeChange}
              />
            </View>
          )}

          <Text style={styles.hint}>
            💡 Touchez une heure pour la personnaliser
          </Text>
        </View>
      )}

      {/* Step 4: Confirmation */}
      {step === 4 && (
        <View style={styles.stepContent}>
          <View style={styles.summaryCard}>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Médicament</Text>
              <Text style={styles.summaryValue}>{name}</Text>
            </View>
            
            {dosage && (
              <View style={styles.summaryRow}>
                <Text style={styles.summaryLabel}>Dosage</Text>
                <Text style={styles.summaryValue}>{dosage} {unit}</Text>
              </View>
            )}
            
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Nombre par prise</Text>
              <Text style={styles.summaryValue}>
                {pillsPerIntake} {pillsPerIntake > 1 ? 'comprimés' : 'comprimé'}
              </Text>
            </View>
            
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Type</Text>
              <Text style={styles.summaryValue}>
                {isRecurring ? 'Récurrent' : 'Ponctuel'}
              </Text>
            </View>
            
            {isRecurring && (
              <>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Date de début</Text>
                  <Text style={styles.summaryValue}>{formatDate(startDate)}</Text>
                </View>
                
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Fréquence</Text>
                  <Text style={styles.summaryValue}>{dailyFrequency}x par jour</Text>
                </View>
                
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Heures</Text>
                  <Text style={styles.summaryValue}>{intakeTimes.join(', ')}</Text>
                </View>
              </>
            )}
          </View>

          <View style={styles.confirmationMessage}>
            <Text style={styles.confirmationEmoji}>🎉</Text>
            <Text style={styles.confirmationText}>
              Votre médicament sera ajouté à votre suivi
            </Text>
          </View>
        </View>
      )}

      {/* Navigation Buttons */}
      <View style={styles.navigation}>
        {step > 1 && (
          <PressableScale
            onPress={prevStep}
            style={styles.secondaryButton}
          >
            <Text style={styles.secondaryButtonText}>Retour</Text>
          </PressableScale>
        )}
        
        {step < 4 ? (
          <PressableScale
            onPress={nextStep}
            style={[
              styles.primaryButton,
              !canGoNext() && styles.primaryButtonDisabled,
              step === 1 && styles.primaryButtonFull
            ]}
            disabled={!canGoNext()}
          >
            <Text style={styles.primaryButtonText}>Suivant</Text>
            <ChevronRight size={20} color="#FFFFFF" strokeWidth={2.5} />
          </PressableScale>
        ) : (
          <PressableScale
            onPress={handleSubmit}
            style={[styles.primaryButton, styles.primaryButtonFull]}
          >
            <Check size={20} color="#FFFFFF" strokeWidth={2.5} />
            <Text style={styles.primaryButtonText}>Confirmer</Text>
          </PressableScale>
        )}
      </View>

      {/* Cancel Button */}
      {onCancel && (
        <PressableScale
          onPress={onCancel}
          style={styles.cancelButton}
        >
          <Text style={styles.cancelButtonText}>Annuler</Text>
        </PressableScale>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 32,
  },
  progressStepContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  progressDot: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#1C1C1E',
    borderWidth: 2,
    borderColor: '#2C2C2E',
    alignItems: 'center',
    justifyContent: 'center',
  },
  progressDotActive: {
    backgroundColor: '#5E5CE6',
    borderColor: '#5E5CE6',
  },
  progressDotCompleted: {
    backgroundColor: '#34C759',
    borderColor: '#34C759',
  },
  progressDotText: {
    color: '#8E8E93',
    fontSize: 16,
    fontWeight: '700',
  },
  progressDotTextActive: {
    color: '#FFFFFF',
  },
  progressLine: {
    width: 40,
    height: 2,
    backgroundColor: '#2C2C2E',
    marginHorizontal: 8,
  },
  progressLineCompleted: {
    backgroundColor: '#34C759',
  },
  stepTitle: {
    fontSize: 24,
    fontWeight: '800',
    color: '#FFFFFF',
    marginBottom: 24,
    textAlign: 'center',
    lineHeight: 32,
  },
  stepContent: {
    flex: 1,
    marginBottom: 24,
  },
  hint: {
    color: '#8E8E93',
    fontSize: 13,
    marginTop: 12,
    textAlign: 'center',
    lineHeight: 18,
  },
  selectedCard: {
    flexDirection: 'row',
    backgroundColor: 'rgba(52, 199, 89, 0.1)',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(52, 199, 89, 0.3)',
    marginTop: 16,
  },
  selectedIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(52, 199, 89, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  selectedInfo: {
    flex: 1,
  },
  selectedName: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 4,
  },
  selectedDetail: {
    color: '#34C759',
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 2,
  },
  selectedLab: {
    color: '#8E8E93',
    fontSize: 12,
  },
  label: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 16,
    textAlign: 'center',
  },
  // Type selection (Ponctuel/Récurrent)
  typeGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  typeCard: {
    flex: 1,
    backgroundColor: '#1C1C1E',
    borderRadius: 20,
    padding: 24,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#2C2C2E',
  },
  typeCardActive: {
    backgroundColor: 'rgba(94, 92, 230, 0.15)',
    borderColor: '#5E5CE6',
  },
  typeIconContainer: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: 'rgba(94, 92, 230, 0.1)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  typeIconContainerActive: {
    backgroundColor: '#5E5CE6',
  },
  typeTitle: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 6,
  },
  typeTextActive: {
    color: '#5E5CE6',
  },
  typeDescription: {
    color: '#8E8E93',
    fontSize: 13,
    fontWeight: '500',
    textAlign: 'center',
  },
  typeDescriptionActive: {
    color: '#FFFFFF',
  },
  // Frequency selection
  frequencyGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 24,
  },
  frequencyCard: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: '#1C1C1E',
    borderRadius: 20,
    padding: 20,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#2C2C2E',
  },
  frequencyCardActive: {
    backgroundColor: 'rgba(94, 92, 230, 0.15)',
    borderColor: '#5E5CE6',
  },
  frequencyIconContainer: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: 'rgba(94, 92, 230, 0.1)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  frequencyIconContainerActive: {
    backgroundColor: '#5E5CE6',
  },
  frequencyText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
  },
  frequencyTextActive: {
    color: '#5E5CE6',
  },
  // Date selection
  dateSection: {
    marginTop: 24,
    marginBottom: 24,
  },
  dateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1C1C1E',
    borderWidth: 1.5,
    borderColor: '#5E5CE6',
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 16,
    gap: 12,
  },
  dateButtonText: {
    flex: 1,
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  datePickerContainer: {
    marginTop: 16,
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  datePickerDone: {
    marginTop: 12,
    backgroundColor: '#5E5CE6',
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
  },
  datePickerDoneText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  // Pills per intake
  pillsSection: {
    marginTop: 24,
    marginBottom: 24,
  },
  pillsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginTop: 12,
  },
  pillButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderWidth: 2,
    borderColor: '#2C2C2E',
  },
  pillButtonActive: {
    backgroundColor: '#5E5CE6',
    borderColor: '#5E5CE6',
  },
  pillButtonText: {
    color: '#8E8E93',
    fontSize: 16,
    fontWeight: '600',
  },
  pillButtonTextActive: {
    color: '#FFFFFF',
  },
  // Time customization
  timesSection: {
    marginTop: 8,
  },
  timesLabel: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 12,
  },
  timesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  timeChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1C1C1E',
    borderWidth: 1.5,
    borderColor: '#5E5CE6',
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 14,
    gap: 8,
  },
  timeChipText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  timePickerContainer: {
    marginTop: 16,
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  timePickerDone: {
    marginTop: 12,
    backgroundColor: '#5E5CE6',
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
  },
  timePickerDoneText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  summaryCard: {
    backgroundColor: '#1C1C1E',
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#2C2C2E',
  },
  summaryLabel: {
    color: '#8E8E93',
    fontSize: 14,
    fontWeight: '600',
  },
  summaryValue: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
    textAlign: 'right',
    flex: 1,
    marginLeft: 12,
  },
  confirmationMessage: {
    alignItems: 'center',
    marginTop: 32,
  },
  confirmationEmoji: {
    fontSize: 64,
    marginBottom: 16,
  },
  confirmationText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
    lineHeight: 24,
  },
  navigation: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  primaryButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#5E5CE6',
    borderRadius: 14,
    paddingVertical: 16,
    gap: 8,
    shadowColor: '#5E5CE6',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  primaryButtonFull: {
    flex: 1,
  },
  primaryButtonDisabled: {
    backgroundColor: '#2C2C2E',
    opacity: 0.5,
    shadowOpacity: 0,
    elevation: 0,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 17,
    fontWeight: '700',
    letterSpacing: 0.2,
  },
  secondaryButton: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1C1C1E',
    borderRadius: 14,
    paddingVertical: 16,
    borderWidth: 2,
    borderColor: '#3A3A3C',
  },
  secondaryButtonText: {
    color: '#FFFFFF',
    fontSize: 17,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
  cancelButton: {
    alignItems: 'center',
    paddingVertical: 14,
    marginTop: 8,
  },
  cancelButtonText: {
    color: '#8E8E93',
    fontSize: 15,
    fontWeight: '600',
  },
});
