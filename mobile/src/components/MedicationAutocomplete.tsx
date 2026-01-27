/**
 * Composant d'autocomplétion pour les médicaments
 * Recherche dans une base locale de 100+ médicaments français
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  View, 
  Text, 
  TextInput, 
  TouchableOpacity, 
  FlatList, 
  StyleSheet,
  Keyboard
} from 'react-native';
import { searchMedications, getPopularMedications, MedicationSuggestion } from '../services/MedicationAPI';
import { Pill } from 'lucide-react-native';

interface MedicationAutocompleteProps {
  value: string;
  onChangeText: (text: string) => void;
  onSelectMedication?: (medication: MedicationSuggestion) => void;
  placeholder?: string;
}

export function MedicationAutocomplete({ 
  value, 
  onChangeText, 
  onSelectMedication,
  placeholder = "Ex: Doliprane"
}: MedicationAutocompleteProps) {
  const [suggestions, setSuggestions] = useState<MedicationSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const debounceTimeout = useRef<NodeJS.Timeout>();

  useEffect(() => {
    // Debounce: attendre 200ms après la dernière frappe
    if (debounceTimeout.current) {
      clearTimeout(debounceTimeout.current);
    }

    if (value.trim().length < 2) {
      // Afficher les médicaments populaires si aucune recherche
      if (value.trim().length === 0) {
        setSuggestions([]);
        setShowSuggestions(false);
      }
      return;
    }

    debounceTimeout.current = setTimeout(() => {
      const results = searchMedications(value);
      setSuggestions(results);
      setShowSuggestions(results.length > 0);
    }, 200);

    return () => {
      if (debounceTimeout.current) {
        clearTimeout(debounceTimeout.current);
      }
    };
  }, [value]);

  const handleSelect = (medication: MedicationSuggestion) => {
    onChangeText(medication.name);
    setShowSuggestions(false);
    setSuggestions([]);
    Keyboard.dismiss();
    onSelectMedication?.(medication);
  };

  const handleFocus = () => {
    if (value.trim().length === 0) {
      // Afficher les médicaments populaires
      const popular = getPopularMedications();
      setSuggestions(popular);
      setShowSuggestions(true);
    } else if (suggestions.length > 0) {
      setShowSuggestions(true);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.inputContainer}>
        <TextInput
          value={value}
          onChangeText={(text) => {
            onChangeText(text);
            if (text.length >= 2) {
              setShowSuggestions(true);
            }
          }}
          placeholder={placeholder}
          placeholderTextColor="#8E8E93"
          style={styles.input}
          autoCapitalize="words"
          onFocus={handleFocus}
          onBlur={() => {
            // Délai pour permettre le clic sur une suggestion
            setTimeout(() => setShowSuggestions(false), 200);
          }}
        />
      </View>

      {showSuggestions && suggestions.length > 0 && (
        <View style={styles.suggestionsContainer}>
          <FlatList
            data={suggestions}
            keyExtractor={(item) => item.id}
            scrollEnabled={false}
            keyboardShouldPersistTaps="handled"
            style={styles.suggestionsList}
            renderItem={({ item }) => (
              <TouchableOpacity
                style={styles.suggestionItem}
                onPress={() => handleSelect(item)}
              >
                <View style={styles.suggestionIcon}>
                  <Pill size={16} color="#5E5CE6" />
                </View>
                <View style={styles.suggestionContent}>
                  <Text style={styles.suggestionName}>{item.name}</Text>
                  {(item.dosage || item.form) && (
                    <Text style={styles.suggestionDetails}>
                      {[item.dosage, item.form].filter(Boolean).join(' • ')}
                    </Text>
                  )}
                  {item.laboratory && (
                    <Text style={styles.suggestionLab}>{item.laboratory}</Text>
                  )}
                </View>
              </TouchableOpacity>
            )}
            ListFooterComponent={
              value.trim().length === 0 ? (
                <View style={styles.footer}>
                  <Text style={styles.footerText}>
                    💊 Médicaments les plus courants
                  </Text>
                </View>
              ) : (
                <View style={styles.footer}>
                  <Text style={styles.footerText}>
                    Base locale • 100+ médicaments français
                  </Text>
                </View>
              )
            }
          />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'relative',
  },
  inputContainer: {
    position: 'relative',
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
  suggestionsContainer: {
    backgroundColor: '#1C1C1E',
    borderRadius: 12,
    marginTop: 8,
    borderWidth: 1,
    borderColor: '#2C2C2E',
    maxHeight: 300,
    overflow: 'hidden',
  },
  suggestionsList: {
    flexGrow: 0,
  },
  suggestionItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#2C2C2E',
  },
  suggestionIcon: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: 'rgba(94, 92, 230, 0.1)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  suggestionContent: {
    flex: 1,
  },
  suggestionName: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 2,
  },
  suggestionDetails: {
    color: '#5E5CE6',
    fontSize: 13,
    marginBottom: 2,
  },
  suggestionLab: {
    color: '#8E8E93',
    fontSize: 12,
  },
  footer: {
    padding: 8,
    alignItems: 'center',
    backgroundColor: '#0C0C0D',
  },
  footerText: {
    color: '#6E6E73',
    fontSize: 10,
    fontWeight: '500',
  },
});
