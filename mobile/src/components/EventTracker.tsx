import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { Coffee, Wine, Utensils, Activity, X } from 'lucide-react-native';
import { useEventTracking } from '@/hooks/useEventTracking';

interface EventTrackerProps {
  onClose: () => void;
  onSuccess?: () => void;
}

type EventType = 'caffeine' | 'alcohol' | 'meal' | 'exercise';

export function EventTracker({ onClose, onSuccess }: EventTrackerProps) {
  const [selectedType, setSelectedType] = useState<EventType | null>(null);
  const { logCaffeine, logAlcohol, logMeal, logExercise, isLogging } = useEventTracking();

  // Caffeine state
  const [caffeineAmount, setCaffeineAmount] = useState('100');

  // Alcohol state
  const [alcoholUnits, setAlcoholUnits] = useState('1');
  const [alcoholType, setAlcoholType] = useState('');

  // Meal state
  const [mealSize, setMealSize] = useState<'small' | 'medium' | 'large'>('medium');
  const [mealTime, setMealTime] = useState(new Date());

  // Exercise state
  const [exerciseType, setExerciseType] = useState('');
  const [exerciseDuration, setExerciseDuration] = useState('30');
  const [exerciseIntensity, setExerciseIntensity] = useState<'light' | 'moderate' | 'intense'>('moderate');
  const [exerciseCalories, setExerciseCalories] = useState('');

  const handleSubmit = async () => {
    if (!selectedType) return;

    let result;
    switch (selectedType) {
      case 'caffeine':
        const caffeineValue = parseInt(caffeineAmount);
        if (isNaN(caffeineValue) || caffeineValue <= 0) {
          Alert.alert('Erreur', 'Veuillez entrer une quantité valide');
          return;
        }
        result = await logCaffeine(caffeineValue);
        break;

      case 'alcohol':
        const alcoholValue = parseFloat(alcoholUnits);
        if (isNaN(alcoholValue) || alcoholValue <= 0) {
          Alert.alert('Erreur', 'Veuillez entrer un nombre d\'unités valide');
          return;
        }
        if (!alcoholType.trim()) {
          Alert.alert('Erreur', 'Veuillez spécifier le type d\'alcool');
          return;
        }
        result = await logAlcohol(alcoholValue, alcoholType);
        break;

      case 'meal':
        result = await logMeal(mealTime, mealSize);
        break;

      case 'exercise':
        const duration = parseInt(exerciseDuration);
        if (isNaN(duration) || duration <= 0) {
          Alert.alert('Erreur', 'Veuillez entrer une durée valide');
          return;
        }
        if (!exerciseType.trim()) {
          Alert.alert('Erreur', 'Veuillez spécifier le type d\'exercice');
          return;
        }
        const calories = exerciseCalories ? parseInt(exerciseCalories) : undefined;
        result = await logExercise(exerciseType, duration, exerciseIntensity, calories);
        break;

      default:
        return;
    }

    if (result.success) {
      Alert.alert(
        'Événement enregistré',
        'Les baselines seront recalculées cette nuit.',
        [
          {
            text: 'OK',
            onPress: () => {
              onSuccess?.();
              onClose();
            },
          },
        ]
      );
    } else {
      Alert.alert('Erreur', result.error || 'Une erreur est survenue');
    }
  };

  const renderTypeSelector = () => (
    <View style={styles.typeSelector}>
      <Text style={styles.title}>Journal d'Activités</Text>
      <Text style={styles.subtitle}>Sélectionnez le type d'événement à enregistrer</Text>

      <View style={styles.typeButtons}>
        <TouchableOpacity
          style={styles.typeButton}
          onPress={() => setSelectedType('caffeine')}
        >
          <Coffee size={32} color="#8B4513" />
          <Text style={styles.typeButtonText}>Café</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.typeButton}
          onPress={() => setSelectedType('alcohol')}
        >
          <Wine size={32} color="#722F37" />
          <Text style={styles.typeButtonText}>Alcool</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.typeButton}
          onPress={() => setSelectedType('meal')}
        >
          <Utensils size={32} color="#FF6B6B" />
          <Text style={styles.typeButtonText}>Repas</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.typeButton}
          onPress={() => setSelectedType('exercise')}
        >
          <Activity size={32} color="#4ECDC4" />
          <Text style={styles.typeButtonText}>Sport</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderCaffeineForm = () => (
    <View style={styles.form}>
      <Text style={styles.formTitle}>☕ Caféine</Text>
      <Text style={styles.label}>Quantité (mg)</Text>
      <TextInput
        style={styles.input}
        value={caffeineAmount}
        onChangeText={setCaffeineAmount}
        keyboardType="numeric"
        placeholder="100"
        placeholderTextColor="#666"
      />
      <Text style={styles.hint}>Une tasse de café ≈ 80-100mg</Text>
    </View>
  );

  const renderAlcoholForm = () => (
    <View style={styles.form}>
      <Text style={styles.formTitle}>🍷 Alcool</Text>
      <Text style={styles.label}>Nombre d'unités</Text>
      <TextInput
        style={styles.input}
        value={alcoholUnits}
        onChangeText={setAlcoholUnits}
        keyboardType="numeric"
        placeholder="1"
        placeholderTextColor="#666"
      />
      <Text style={styles.label}>Type</Text>
      <TextInput
        style={styles.input}
        value={alcoholType}
        onChangeText={setAlcoholType}
        placeholder="Vin, bière, etc."
        placeholderTextColor="#666"
      />
      <Text style={styles.hint}>1 unité = 1 verre standard</Text>
    </View>
  );

  const renderMealForm = () => (
    <View style={styles.form}>
      <Text style={styles.formTitle}>🍽️ Repas</Text>
      <Text style={styles.label}>Taille du repas</Text>
      <View style={styles.sizeButtons}>
        {(['small', 'medium', 'large'] as const).map((size) => (
          <TouchableOpacity
            key={size}
            style={[
              styles.sizeButton,
              mealSize === size && styles.sizeButtonActive,
            ]}
            onPress={() => setMealSize(size)}
          >
            <Text
              style={[
                styles.sizeButtonText,
                mealSize === size && styles.sizeButtonTextActive,
              ]}
            >
              {size === 'small' ? 'Petit' : size === 'medium' ? 'Moyen' : 'Grand'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
      <Text style={styles.hint}>
        {mealTime.getHours() >= 20
          ? '⚠️ Repas tardif (peut affecter le sommeil)'
          : 'Heure: ' + mealTime.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
      </Text>
    </View>
  );

  const renderExerciseForm = () => (
    <View style={styles.form}>
      <Text style={styles.formTitle}>🏃 Sport</Text>
      <Text style={styles.label}>Type d'exercice</Text>
      <TextInput
        style={styles.input}
        value={exerciseType}
        onChangeText={setExerciseType}
        placeholder="Course, vélo, musculation..."
        placeholderTextColor="#666"
      />
      <Text style={styles.label}>Durée (minutes)</Text>
      <TextInput
        style={styles.input}
        value={exerciseDuration}
        onChangeText={setExerciseDuration}
        keyboardType="numeric"
        placeholder="30"
        placeholderTextColor="#666"
      />
      <Text style={styles.label}>Intensité</Text>
      <View style={styles.sizeButtons}>
        {(['light', 'moderate', 'intense'] as const).map((intensity) => (
          <TouchableOpacity
            key={intensity}
            style={[
              styles.sizeButton,
              exerciseIntensity === intensity && styles.sizeButtonActive,
            ]}
            onPress={() => setExerciseIntensity(intensity)}
          >
            <Text
              style={[
                styles.sizeButtonText,
                exerciseIntensity === intensity && styles.sizeButtonTextActive,
              ]}
            >
              {intensity === 'light' ? 'Léger' : intensity === 'moderate' ? 'Modéré' : 'Intense'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
      <Text style={styles.label}>Calories (optionnel)</Text>
      <TextInput
        style={styles.input}
        value={exerciseCalories}
        onChangeText={setExerciseCalories}
        keyboardType="numeric"
        placeholder="250"
        placeholderTextColor="#666"
      />
    </View>
  );

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <TouchableOpacity style={styles.closeButton} onPress={onClose}>
          <X size={24} color="#FFFFFF" />
        </TouchableOpacity>

        {!selectedType ? (
          renderTypeSelector()
        ) : (
          <>
            {selectedType === 'caffeine' && renderCaffeineForm()}
            {selectedType === 'alcohol' && renderAlcoholForm()}
            {selectedType === 'meal' && renderMealForm()}
            {selectedType === 'exercise' && renderExerciseForm()}

            <View style={styles.buttonGroup}>
              <TouchableOpacity
                style={styles.backButton}
                onPress={() => setSelectedType(null)}
                disabled={isLogging}
              >
                <Text style={styles.backButtonText}>Retour</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.submitButton, isLogging && styles.submitButtonDisabled]}
                onPress={handleSubmit}
                disabled={isLogging}
              >
                {isLogging ? (
                  <ActivityIndicator color="#FFFFFF" />
                ) : (
                  <Text style={styles.submitButtonText}>Enregistrer</Text>
                )}
              </TouchableOpacity>
            </View>
          </>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  scrollContent: {
    padding: 20,
  },
  closeButton: {
    alignSelf: 'flex-end',
    padding: 8,
    marginBottom: 16,
  },
  typeSelector: {
    marginTop: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#8E8E93',
    marginBottom: 32,
  },
  typeButtons: {
    gap: 16,
  },
  typeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    padding: 20,
    gap: 16,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  typeButtonText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  form: {
    marginTop: 20,
  },
  formTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 24,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 8,
    marginTop: 16,
  },
  input: {
    backgroundColor: '#1C1C1E',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  hint: {
    fontSize: 14,
    color: '#8E8E93',
    marginTop: 8,
  },
  sizeButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  sizeButton: {
    flex: 1,
    backgroundColor: '#1C1C1E',
    borderRadius: 12,
    padding: 12,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  sizeButtonActive: {
    backgroundColor: '#2C2C2E',
    borderColor: '#34C759',
  },
  sizeButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E93',
    textAlign: 'center',
  },
  sizeButtonTextActive: {
    color: '#FFFFFF',
  },
  buttonGroup: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 32,
  },
  backButton: {
    flex: 1,
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  backButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    textAlign: 'center',
  },
  submitButton: {
    flex: 1,
    backgroundColor: '#34C759',
    borderRadius: 16,
    padding: 16,
  },
  submitButtonDisabled: {
    opacity: 0.5,
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    textAlign: 'center',
  },
});
