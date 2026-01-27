/**
 * Composant formulaire pour ajouter un médicament
 * Design aligné avec le reste de l'app
 */

import React, { useState } from 'react';
import { View, Text, TextInput, ScrollView, StyleSheet } from 'react-native';
import { PressableScale } from './PressableScale';
import { MedicationAutocomplete } from './MedicationAutocomplete';
import type { MedicationSuggestion } from '../services/MedicationAPI';

interface MedicationFormProps {
  onSubmit: (medication: {
    name: string;
    dosage?: string;
    unit?: string;
    frequency?: string;
    notes?: string;
    takenAt: string;
  }) => void;
  onCancel?: () => void;
}

export function MedicationForm({ onSubmit, onCancel }: MedicationFormProps) {
  const [name, setName] = useState('');
  const [dosage, setDosage] = useState('');
  const [unit, setUnit] = useState('mg');
  const [frequency, setFrequency] = useState('');
  const [notes, setNotes] = useState('');
  const [takenAt] = useState(new Date());

  const handleSubmit = () => {
    if (!name.trim()) {
      return;
    }

    onSubmit({
      name: name.trim(),
      dosage: dosage.trim() || undefined,
      unit: unit.trim() || undefined,
      frequency: frequency.trim() || undefined,
      notes: notes.trim() || undefined,
      takenAt: takenAt.toISOString(),
    });

    // Reset form
    setName('');
    setDosage('');
    setUnit('mg');
    setFrequency('');
    setNotes('');
  };

  const units = ['mg', 'g', 'mL', 'µg', 'UI', 'comprimé(s)', 'gélule(s)', 'goutte(s)'];

  const handleSelectMedication = (medication: MedicationSuggestion) => {
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

      {/* Fréquence */}
      <View style={styles.fieldContainer}>
        <Text style={styles.label}>Fréquence</Text>
        <TextInput
          value={frequency}
          onChangeText={setFrequency}
          placeholder="Ex: 3x par jour, matin/soir"
          placeholderTextColor="#8E8E93"
          style={styles.input}
        />
      </View>

      {/* Date et heure de prise */}
      <View style={styles.fieldContainer}>
        <Text style={styles.label}>Date et heure de prise</Text>
        <View style={styles.dateDisplay}>
          <Text style={styles.dateText}>
            {takenAt.toLocaleDateString('fr-FR', {
              day: 'numeric',
              month: 'long',
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}
          </Text>
          <Text style={styles.dateHint}>
            Enregistré au moment de l'ajout
          </Text>
        </View>
      </View>

      {/* Notes */}
      <View style={styles.fieldContainer}>
        <Text style={styles.label}>Notes</Text>
        <TextInput
          value={notes}
          onChangeText={setNotes}
          placeholder="Ex: Pris avec de l'eau, après le repas"
          placeholderTextColor="#8E8E93"
          multiline
          numberOfLines={3}
          style={[styles.input, styles.notesInput]}
        />
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
  dateDisplay: {
    backgroundColor: '#1C1C1E',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  dateText: {
    color: '#FFFFFF',
    fontSize: 16,
  },
  dateHint: {
    color: '#8E8E93',
    fontSize: 12,
    marginTop: 4,
  },
  notesInput: {
    minHeight: 80,
    textAlignVertical: 'top',
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
