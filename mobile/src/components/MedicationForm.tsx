/**
 * Composant formulaire pour ajouter un médicament
 * Design aligné avec le reste de l'app
 */

import React, { useState } from 'react';
import { View, Text, TextInput, ScrollView, StyleSheet, Platform } from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { PressableScale } from './PressableScale';
import { MedicationAutocomplete } from './MedicationAutocomplete';
import type { MedicationSuggestion } from '../services/GiygasMedicationAPI';
import { Clock, Plus, X } from 'lucide-react-native';

interface MedicationFormProps {
  onSubmit: (medication: {
    name: string;
    dosage?: string;
    unit?: string;
    pillsPerIntake?: number; // Nombre de comprimés par prise (peut être 0.5, 1, 1.5, 2...)
    frequency?: string;
    intakeTimes?: string[]; // Heures de prise dans la journée (format "HH:mm")
    dailyFrequency?: number; // Nombre de prises par jour
    takenAt: string;
  }) => void;
  onCancel?: () => void;
}

export function MedicationForm({ onSubmit, onCancel }: MedicationFormProps) {
  const [name, setName] = useState('');
  const [dosage, setDosage] = useState('');
  const [unit, setUnit] = useState('mg');
  const [pillsPerIntake, setPillsPerIntake] = useState('1'); // Stocké en string pour faciliter l'édition
  const [takenAt, setTakenAt] = useState(new Date());
  
  // Gestion de la fréquence quotidienne
  const [dailyFrequency, setDailyFrequency] = useState<number>(1);
  const [intakeTimes, setIntakeTimes] = useState<string[]>(['08:00']);
  const [showTimePickerForIndex, setShowTimePickerForIndex] = useState<number | null>(null);


  const handleSubmit = () => {
    if (!name.trim()) {
      return;
    }

    // Parser le nombre de comprimés (gérer les décimaux)
    const pillsValue = parseFloat(pillsPerIntake) || undefined;

    // Construire le texte de fréquence pour compatibilité
    const frequencyText = `${dailyFrequency}x par jour à ${intakeTimes.join(', ')}`;

    onSubmit({
      name: name.trim(),
      dosage: dosage.trim() || undefined,
      unit: unit.trim() || undefined,
      pillsPerIntake: pillsValue,
      frequency: frequencyText,
      intakeTimes,
      dailyFrequency,
      takenAt: takenAt.toISOString(),
    });

    // Reset form
    setName('');
    setDosage('');
    setUnit('mg');
    setPillsPerIntake('1');
    setDailyFrequency(1);
    setIntakeTimes(['08:00']);
  };

  // Ajouter une nouvelle heure de prise
  const addIntakeTime = () => {
    if (intakeTimes.length < 6) { // Max 6 prises par jour
      const newTime = '08:00';
      setIntakeTimes([...intakeTimes, newTime]);
      setDailyFrequency(intakeTimes.length + 1);
    }
  };

  // Supprimer une heure de prise
  const removeIntakeTime = (index: number) => {
    if (intakeTimes.length > 1) {
      const updated = intakeTimes.filter((_, i) => i !== index);
      setIntakeTimes(updated);
      setDailyFrequency(updated.length);
    }
  };

  // Mettre à jour une heure de prise
  const updateIntakeTime = (index: number, date: Date) => {
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    const timeString = `${hours}:${minutes}`;
    
    const updated = [...intakeTimes];
    updated[index] = timeString;
    setIntakeTimes(updated);
    setShowTimePickerForIndex(null);
  };

  // Sélection rapide de fréquence commune
  const setQuickFrequency = (freq: number) => {
    setDailyFrequency(freq);
    
    // Heures suggérées selon la fréquence
    const suggestions: { [key: number]: string[] } = {
      1: ['08:00'],
      2: ['08:00', '20:00'],
      3: ['08:00', '13:00', '20:00'],
      4: ['08:00', '12:00', '16:00', '20:00'],
    };
    
    setIntakeTimes(suggestions[freq] || ['08:00']);
  };

  // Sélection rapide de date de première prise
  const setQuickDate = (period: 'today' | 'yesterday' | 'week' | 'month' | 'months3') => {
    const now = new Date();
    const date = new Date();
    
    switch (period) {
      case 'today':
        // Aujourd'hui
        break;
      case 'yesterday':
        // Hier
        date.setDate(now.getDate() - 1);
        break;
      case 'week':
        // Il y a 1 semaine
        date.setDate(now.getDate() - 7);
        break;
      case 'month':
        // Il y a 1 mois
        date.setMonth(now.getMonth() - 1);
        break;
      case 'months3':
        // Il y a 3 mois
        date.setMonth(now.getMonth() - 3);
        break;
    }
    
    setTakenAt(date);
  };

  // Formatter la date pour l'affichage
  const formatDateDisplay = (date: Date): string => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffDays === 0) {
      return "Aujourd'hui";
    } else if (diffDays === 1) {
      return 'Hier';
    } else if (diffDays < 7) {
      return `Il y a ${diffDays} jours`;
    } else if (diffDays < 30) {
      const weeks = Math.floor(diffDays / 7);
      return weeks === 1 ? 'Il y a 1 semaine' : `Il y a ${weeks} semaines`;
    } else if (diffDays < 365) {
      const months = Math.floor(diffDays / 30);
      return months === 1 ? 'Il y a 1 mois' : `Il y a ${months} mois`;
    } else {
      return date.toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      });
    }
  };

  const units = ['mg', 'g', 'mL', 'µg', 'UI', 'comprimé(s)', 'gélule(s)', 'goutte(s)'];

  const handleSelectMedication = (medication: MedicationSuggestion) => {
    // Pré-remplir le nom
    setName(medication.name);
    
    // Pré-remplir les champs si disponibles
    if (medication.dosage) {
      // Extraire la valeur et l'unité du dosage (ex: "500mg" -> "500" + "mg", "100µg" -> "100" + "µg")
      const match = medication.dosage.match(/^(\d+(?:\.\d+)?)\s*([a-zµμ]+|UI)$/i);
      if (match) {
        const value = match[1];
        const unit = match[2].toLowerCase();
        setDosage(value);
        
        // Normaliser l'unité (accepter μ et µ comme µg)
        if (unit === 'μg' || unit === 'µg') {
          setUnit('µg');
        } else {
          setUnit(unit);
        }
      }
    }

    // La fréquence commune n'est plus disponible avec l'API Giygas
    // On garde la valeur par défaut (1x/jour)
  };

  return (
    <View style={styles.container}>
      {/* Nom du médicament avec autocomplétion */}
      <View style={styles.fieldContainer}>
        <Text style={styles.label}>Nom du médicament *</Text>
        <MedicationAutocomplete
          value={name}
          onChangeText={setName}
          onSelectMedication={handleSelectMedication}
          placeholder="Ex: Doliprane, Ibuprofène..."
        />
        <Text style={styles.hint}>
          💡 Commencez à taper pour voir les suggestions
        </Text>
      </View>

      {/* Dosage */}
      <View style={styles.fieldContainer}>
        <Text style={styles.label}>Dosage</Text>
        <View style={styles.dosageContainer}>
          <TextInput
            value={dosage}
            onChangeText={setDosage}
            placeholder="Ex: 500"
            placeholderTextColor="#8E8E93"
            keyboardType="decimal-pad"
            style={[styles.input, styles.dosageInput]}
          />
          <ScrollView 
            horizontal 
            showsHorizontalScrollIndicator={false}
            style={styles.unitScroll}
          >
            {units.map((u) => (
              <PressableScale
                key={u}
                onPress={() => setUnit(u)}
                style={[
                  styles.unitButton,
                  unit === u && styles.unitButtonActive
                ]}
              >
                <Text style={[
                  styles.unitButtonText,
                  unit === u && styles.unitButtonTextActive
                ]}>
                  {u}
                </Text>
              </PressableScale>
            ))}
          </ScrollView>
        </View>
      </View>

      {/* Nombre de comprimés par prise */}
      <View style={styles.fieldContainer}>
        <Text style={styles.label}>Nombre de comprimés par prise</Text>
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
            placeholderTextColor="#8E8E93"
            keyboardType="decimal-pad"
            style={[styles.input, styles.pillsInput]}
          />
        </View>
        <Text style={styles.hint}>
          💊 Vous pouvez utiliser ¼, ½ ou des valeurs personnalisées
        </Text>
      </View>

      {/* Fréquence quotidienne */}
      <View style={styles.fieldContainer}>
        <Text style={styles.label}>Récurrence quotidienne</Text>
        <View style={styles.frequencyButtonsContainer}>
          {[1, 2, 3, 4].map((freq) => (
            <PressableScale
              key={freq}
              onPress={() => setQuickFrequency(freq)}
              style={[
                styles.frequencyButton,
                dailyFrequency === freq && styles.frequencyButtonActive
              ]}
            >
              <Text style={[
                styles.frequencyButtonText,
                dailyFrequency === freq && styles.frequencyButtonTextActive
              ]}>
                {freq}x/jour
              </Text>
            </PressableScale>
          ))}
        </View>
      </View>

      {/* Heures de prise */}
      <View style={styles.fieldContainer}>
        <View style={styles.labelWithAction}>
          <Text style={styles.label}>Heures de prise</Text>
          {intakeTimes.length < 6 && (
            <PressableScale onPress={addIntakeTime} style={styles.addTimeButton}>
              <Plus size={16} color="#5E5CE6" />
              <Text style={styles.addTimeButtonText}>Ajouter</Text>
            </PressableScale>
          )}
        </View>
        
        {intakeTimes.map((time, index) => {
          // Créer un objet Date pour le picker
          const [hours, minutes] = time.split(':').map(Number);
          const pickerDate = new Date();
          pickerDate.setHours(hours);
          pickerDate.setMinutes(minutes);

          return (
            <View key={index} style={styles.timeSlot}>
              <PressableScale
                onPress={() => setShowTimePickerForIndex(index)}
                style={styles.timeDisplay}
              >
                <Clock size={18} color="#5E5CE6" />
                <Text style={styles.timeText}>{time}</Text>
              </PressableScale>
              
              {intakeTimes.length > 1 && (
                <PressableScale
                  onPress={() => removeIntakeTime(index)}
                  style={styles.removeTimeButton}
                >
                  <X size={18} color="#FF3B30" />
                </PressableScale>
              )}

              {/* Time Picker pour cette heure */}
              {showTimePickerForIndex === index && (
                Platform.OS === 'ios' ? (
                  <View style={styles.iosTimePickerContainer}>
                    <DateTimePicker
                      value={pickerDate}
                      mode="time"
                      display="spinner"
                      onChange={(event, selectedDate) => {
                        if (selectedDate) {
                          updateIntakeTime(index, selectedDate);
                        }
                      }}
                      locale="fr-FR"
                      themeVariant="dark"
                    />
                    <PressableScale
                      onPress={() => setShowTimePickerForIndex(null)}
                      style={styles.timePickerDoneButton}
                    >
                      <Text style={styles.timePickerDoneText}>Terminé</Text>
                    </PressableScale>
                  </View>
                ) : (
                  <DateTimePicker
                    value={pickerDate}
                    mode="time"
                    display="default"
                    onChange={(event, selectedDate) => {
                      if (event.type === 'set' && selectedDate) {
                        updateIntakeTime(index, selectedDate);
                      } else {
                        setShowTimePickerForIndex(null);
                      }
                    }}
                    is24Hour={true}
                  />
                )
              )}
            </View>
          );
        })}
        
        <Text style={styles.hint}>
          🕐 Définissez les heures habituelles de prise
        </Text>
      </View>

      {/* Date de première prise */}
      <View style={styles.fieldContainer}>
        <Text style={styles.label}>Quand avez-vous commencé à prendre ce médicament ?</Text>
        <View style={styles.dateQuickSelect}>
          <PressableScale
            onPress={() => setQuickDate('today')}
            style={styles.dateQuickButton}
          >
            <Text style={styles.dateQuickButtonText}>Aujourd'hui</Text>
          </PressableScale>
          <PressableScale
            onPress={() => setQuickDate('yesterday')}
            style={styles.dateQuickButton}
          >
            <Text style={styles.dateQuickButtonText}>Hier</Text>
          </PressableScale>
          <PressableScale
            onPress={() => setQuickDate('week')}
            style={styles.dateQuickButton}
          >
            <Text style={styles.dateQuickButtonText}>Cette semaine</Text>
          </PressableScale>
        </View>
        <View style={styles.dateQuickSelect}>
          <PressableScale
            onPress={() => setQuickDate('month')}
            style={styles.dateQuickButton}
          >
            <Text style={styles.dateQuickButtonText}>Il y a 1 mois</Text>
          </PressableScale>
          <PressableScale
            onPress={() => setQuickDate('months3')}
            style={styles.dateQuickButton}
          >
            <Text style={styles.dateQuickButtonText}>Il y a 3 mois</Text>
          </PressableScale>
        </View>
        <View style={styles.dateDisplaySelected}>
          <Clock size={16} color="#5E5CE6" />
          <Text style={styles.dateDisplayText}>
            {formatDateDisplay(takenAt)}
          </Text>
        </View>
      </View>

      {/* Actions */}
      <View style={styles.actions}>
        {onCancel && (
          <PressableScale
            onPress={onCancel}
            style={styles.cancelButton}
          >
            <Text style={styles.cancelButtonText}>
              Annuler
            </Text>
          </PressableScale>
        )}
        <PressableScale
          onPress={handleSubmit}
          style={[
            styles.submitButton,
            !name.trim() && styles.submitButtonDisabled
          ]}
          disabled={!name.trim()}
        >
          <Text style={styles.submitButtonText}>
            Ajouter
          </Text>
        </PressableScale>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 20,
  },
  fieldContainer: {
    marginBottom: 20,
  },
  label: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  hint: {
    color: '#6E6E73',
    fontSize: 12,
    marginTop: 6,
  },
  input: {
    backgroundColor: '#1C1C1E',
    color: '#FFFFFF',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  dosageContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  dosageInput: {
    flex: 1,
  },
  pillsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  pillButton: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 12,
    backgroundColor: '#1C1C1E',
    borderWidth: 1,
    borderColor: '#2C2C2E',
    minWidth: 50,
    alignItems: 'center',
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
  pillsInput: {
    flex: 1,
    minWidth: 80,
  },
  unitScroll: {
    flex: 1,
  },
  unitButton: {
    paddingHorizontal: 12,
    paddingVertical: 14,
    borderRadius: 12,
    backgroundColor: '#1C1C1E',
    borderWidth: 1,
    borderColor: '#2C2C2E',
    marginRight: 8,
  },
  unitButtonActive: {
    backgroundColor: '#5E5CE6',
    borderColor: '#5E5CE6',
  },
  unitButtonText: {
    color: '#8E8E93',
    fontSize: 14,
    fontWeight: '500',
  },
  unitButtonTextActive: {
    color: '#FFFFFF',
  },
  frequencyButtonsContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  frequencyButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 12,
    backgroundColor: '#1C1C1E',
    borderWidth: 1,
    borderColor: '#2C2C2E',
    alignItems: 'center',
  },
  frequencyButtonActive: {
    backgroundColor: '#5E5CE6',
    borderColor: '#5E5CE6',
  },
  frequencyButtonText: {
    color: '#8E8E93',
    fontSize: 14,
    fontWeight: '600',
  },
  frequencyButtonTextActive: {
    color: '#FFFFFF',
  },
  labelWithAction: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  addTimeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: 'rgba(94, 92, 230, 0.1)',
  },
  addTimeButtonText: {
    color: '#5E5CE6',
    fontSize: 13,
    fontWeight: '600',
  },
  timeSlot: {
    marginBottom: 12,
  },
  timeDisplay: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#1C1C1E',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  timeText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '600',
    flex: 1,
  },
  removeTimeButton: {
    position: 'absolute',
    right: 12,
    top: 12,
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: 'rgba(255, 59, 48, 0.1)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  iosTimePickerContainer: {
    backgroundColor: '#1C1C1E',
    borderRadius: 12,
    marginTop: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  timePickerDoneButton: {
    backgroundColor: '#5E5CE6',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 12,
  },
  timePickerDoneText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  dateQuickSelect: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 8,
  },
  dateQuickButton: {
    flex: 1,
    backgroundColor: '#1C1C1E',
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#2C2C2E',
    alignItems: 'center',
  },
  dateQuickButtonText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '600',
  },
  dateDisplaySelected: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: 'rgba(94, 92, 230, 0.1)',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: 'rgba(94, 92, 230, 0.3)',
    marginTop: 4,
  },
  dateDisplayText: {
    color: '#5E5CE6',
    fontSize: 14,
    fontWeight: '600',
  },
  actions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 12,
  },
  cancelButton: {
    flex: 1,
    backgroundColor: '#1C1C1E',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  cancelButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  submitButton: {
    flex: 1,
    backgroundColor: '#5E5CE6',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  submitButtonDisabled: {
    backgroundColor: '#2C2C2E',
    opacity: 0.5,
  },
  submitButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});
