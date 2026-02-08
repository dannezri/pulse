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
  Keyboard,
  ActivityIndicator,
  Alert
} from 'react-native';
import { searchMedications, getMedicationDetails, MedicationSuggestion, scanMedicationBarcode } from '../services/GiygasMedicationAPI';
import { Pill, ScanBarcode } from 'lucide-react-native';
import { BarcodeScannerModal } from './BarcodeScannerModal';

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
  const [isSearching, setIsSearching] = useState(false);
  const [scannerVisible, setScannerVisible] = useState(false);
  const debounceTimeout = useRef<NodeJS.Timeout>();

  useEffect(() => {
    // Debounce: attendre 300ms après la dernière frappe
    if (debounceTimeout.current) {
      clearTimeout(debounceTimeout.current);
    }

    if (value.trim().length < 2) {
      // Afficher les médicaments populaires si aucune recherche
      if (value.trim().length === 0) {
        setSuggestions([]);
        setShowSuggestions(false);
        setIsSearching(false);
      }
      return;
    }

    setIsSearching(true);

    debounceTimeout.current = setTimeout(async () => {
      try {
        const results = await searchMedications(value);
        setSuggestions(results);
        setShowSuggestions(results.length > 0);
      } catch (error) {
        console.error('[MedicationAutocomplete] Erreur recherche:', error);
        setSuggestions([]);
        setShowSuggestions(false);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => {
      if (debounceTimeout.current) {
        clearTimeout(debounceTimeout.current);
      }
    };
  }, [value]);

  const handleSelect = (medication: MedicationSuggestion) => {
    // Fermer immédiatement pour éviter tout conflit
    setShowSuggestions(false);
    setSuggestions([]);
    
    // Appeler le callback parent pour pré-remplir tous les champs
    if (onSelectMedication) {
      onSelectMedication(medication);
    } else {
      // Si pas de callback, au moins mettre à jour le nom
      onChangeText(medication.name);
    }
    
    Keyboard.dismiss();
  };

  const handleFocus = () => {
    // Avec l'API Giygas, on ne peut plus afficher de suggestions sans recherche
    if (suggestions.length > 0) {
      setShowSuggestions(true);
    }
  };

  const handleBarcodeScanned = async (barcode: string) => {
    console.log('[MedicationAutocomplete] Code-barres scanné:', barcode);
    setIsSearching(true);
    setShowSuggestions(false);

    try {
      const medication = await scanMedicationBarcode(barcode);
      
      if (medication) {
        // Sélectionner automatiquement le médicament trouvé
        handleSelect(medication);
        Alert.alert(
          '✅ Médicament trouvé',
          `${medication.name} a été ajouté automatiquement.`,
          [{ text: 'OK' }]
        );
      } else {
        Alert.alert(
          'Médicament introuvable',
          'Le code-barres a été scanné avec succès, mais ce médicament n\'est pas encore dans notre base de données.\n\nVeuillez rechercher le médicament par son nom dans la barre de recherche ci-dessus.',
          [{ text: 'Compris' }]
        );
      }
    } catch (error) {
      console.error('[MedicationAutocomplete] Erreur scan:', error);
      Alert.alert(
        'Erreur',
        'Une erreur est survenue lors de la recherche. Veuillez réessayer.',
        [{ text: 'OK' }]
      );
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.searchRow}>
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
          />
        </View>
        
        {/* Bouton Scanner */}
        <TouchableOpacity
          style={styles.scanButton}
          onPress={() => setScannerVisible(true)}
          activeOpacity={0.7}
        >
          <ScanBarcode size={24} color="#FFFFFF" strokeWidth={2} />
        </TouchableOpacity>
      </View>

      {/* Indicateur de chargement */}
      {isSearching && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color="#5E5CE6" />
          <Text style={styles.loadingText}>Recherche en cours...</Text>
        </View>
      )}

      {showSuggestions && suggestions.length > 0 && !isSearching && (
        <View style={styles.suggestionsContainer}>
          <FlatList
            data={suggestions}
            keyExtractor={(item) => item.id}
            scrollEnabled={false}
            nestedScrollEnabled={true}
            keyboardShouldPersistTaps="always"
            style={styles.suggestionsList}
            renderItem={({ item }) => {
              return (
                <TouchableOpacity
                  style={styles.suggestionItem}
                  onPress={() => handleSelect(item)}
                  activeOpacity={0.7}
                >
                  <View style={styles.suggestionIcon}>
                    <Pill size={16} color="#34C759" />
                  </View>
                  <View style={styles.suggestionContent}>
                    <View style={styles.suggestionNameRow}>
                      <Text style={styles.suggestionName}>{item.name}</Text>
                    </View>
                    {(item.form || item.activeSubstance) && (
                      <Text style={styles.suggestionDetails}>
                        {[item.form, item.activeSubstance].filter(Boolean).join(' • ')}
                      </Text>
                    )}
                    {item.laboratory && (
                      <Text style={styles.suggestionLab}>{item.laboratory}</Text>
                    )}
                  </View>
                </TouchableOpacity>
              );
            }}
            ListFooterComponent={() => {
              return (
                <View style={styles.footer}>
                  <Text style={styles.footerText}>
                    🌐 Base publique française des médicaments (Giygas API)
                  </Text>
                </View>
              );
            }}
          />
        </View>
      )}

      {/* Modal Scanner */}
      <BarcodeScannerModal
        visible={scannerVisible}
        onClose={() => setScannerVisible(false)}
        onBarcodeScanned={handleBarcodeScanned}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'relative',
  },
  searchRow: {
    flexDirection: 'row',
    gap: 12,
    alignItems: 'center',
  },
  inputContainer: {
    flex: 1,
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
  scanButton: {
    width: 52,
    height: 52,
    backgroundColor: '#5E5CE6',
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#5E5CE6',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 3,
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
  suggestionIconAPI: {
    backgroundColor: 'rgba(52, 199, 89, 0.1)',
  },
  suggestionContent: {
    flex: 1,
  },
  suggestionNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 2,
  },
  suggestionName: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
  },
  apiBadge: {
    backgroundColor: 'rgba(52, 199, 89, 0.15)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: 'rgba(52, 199, 89, 0.3)',
  },
  apiBadgeText: {
    color: '#34C759',
    fontSize: 10,
    fontWeight: '700',
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
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1C1C1E',
    borderRadius: 12,
    marginTop: 8,
    paddingVertical: 16,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderColor: '#2C2C2E',
    gap: 12,
  },
  loadingText: {
    color: '#8E8E93',
    fontSize: 13,
    fontWeight: '500',
  },
});
