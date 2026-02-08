/**
 * Composant pour rechercher et sélectionner des conditions de santé (ICD-11)
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  Animated,
} from 'react-native';
import { Search, X, Plus, AlertCircle, Sparkles, Check } from 'lucide-react-native';
import { useConditions, SearchResult } from '@/hooks/useConditions';

interface ConditionPickerProps {
  onClose: () => void;
  onSuccess?: () => void;
}

export function ConditionPicker({ onClose, onSuccess }: ConditionPickerProps) {
  const { searchConditions, addCondition } = useConditions();
  
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [moreResults, setMoreResults] = useState(false);
  const [searching, setSearching] = useState(false);
  const [adding, setAdding] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [addedConditions, setAddedConditions] = useState<Set<string>>(new Set());
  
  // Debounce timer
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Effectuer la recherche (fonction appelée après debounce)
  const performSearch = useCallback(async (searchQuery: string) => {
    if (searchQuery.trim().length < 2) {
      setSearchResults([]);
      setSuggestions([]);
      setMoreResults(false);
      setSearchError(null);
      setSearching(false);
      return;
    }

    try {
      setSearching(true);
      setSearchError(null);
      
      const response = await searchConditions(searchQuery, 'fr');
      
      // Le nouveau format retourne {suggestions, results, more_results}
      if (response && typeof response === 'object' && 'suggestions' in response) {
        setSuggestions(response.suggestions || []);
        setSearchResults(response.results || []);
        setMoreResults(response.more_results || false);
        
        // Aucun résultat seulement si ni suggestions ni résultats
        if ((response.suggestions || []).length === 0 && (response.results || []).length === 0) {
          setSearchError('Aucun résultat trouvé');
        }
      } else {
        // Fallback pour format legacy
        setSearchResults(Array.isArray(response) ? response : []);
        setSuggestions([]);
        setMoreResults(false);
        
        if ((Array.isArray(response) ? response : []).length === 0) {
          setSearchError('Aucun résultat trouvé');
        }
      }
    } catch (err: any) {
      console.error('[ConditionPicker] Search error:', err);
      setSearchError('Erreur lors de la recherche');
      setSearchResults([]);
      setSuggestions([]);
      setMoreResults(false);
    } finally {
      setSearching(false);
    }
  }, [searchConditions]);

  // Gérer le changement de texte avec debounce
  const handleSearch = useCallback((searchQuery: string) => {
    setQuery(searchQuery);
    
    // Annuler le timer précédent
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    // Si moins de 2 caractères, effacer immédiatement
    if (searchQuery.trim().length < 2) {
      setSearchResults([]);
      setSearchError(null);
      setSearching(false);
      return;
    }
    
    // Indiquer qu'on va chercher (pour le feedback visuel)
    setSearching(true);
    setSearchError(null);
    
    // Lancer la recherche après 400ms
    searchTimeoutRef.current = setTimeout(() => {
      performSearch(searchQuery);
    }, 400);
  }, [performSearch]);

  // Nettoyer le timeout au démontage
  useEffect(() => {
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, []);

  // Ajouter une condition
  const handleAddCondition = async (result: SearchResult) => {
    if (adding || addedConditions.has(result.code)) return;

    try {
      setAdding(true);
      
      const success = await addCondition(result);
      
      if (success) {
        // Marquer comme ajouté
        setAddedConditions(prev => new Set(prev).add(result.code));
        
        // Feedback visuel court et simple
        Alert.alert(
          '✅ Ajouté',
          `"${result.display}" a été ajouté à votre profil.`,
          [
            {
              text: 'OK',
              onPress: () => {
                // Continuer à chercher
              },
            },
            {
              text: 'Terminer',
              style: 'cancel',
              onPress: () => {
                if (onSuccess) onSuccess();
                onClose();
              },
            },
          ]
        );
      } else {
        Alert.alert(
          'Déjà ajouté',
          'Cette condition est déjà dans votre profil.'
        );
      }
    } catch (err: any) {
      console.error('[ConditionPicker] Add error:', err);
      Alert.alert('Erreur', 'Impossible d\'ajouter cette condition.');
    } finally {
      setAdding(false);
    }
  };

  // Obtenir la couleur de la catégorie
  const getCategoryColor = (category: string) => {
    if (category.toLowerCase().includes('mentaux') || category.toLowerCase().includes('mood')) {
      return '#FF9500'; // Orange pour troubles mentaux
    }
    if (category.toLowerCase().includes('endocrin')) {
      return '#5E5CE6'; // Violet pour endocrinologie
    }
    if (category.toLowerCase().includes('anxieux')) {
      return '#FF375F'; // Rouge pour anxiété
    }
    if (category.toLowerCase().includes('génito') || category.toLowerCase().includes('reproduct')) {
      return '#FF2D55'; // Rose pour système génito-urinaire
    }
    return '#34C759'; // Vert par défaut
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerTop}>
          <Text style={styles.title}>Conditions de santé</Text>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <X size={24} color="#8E8E93" />
          </TouchableOpacity>
        </View>
        <Text style={styles.subtitle}>
          Recherchez vos conditions de santé pour personnaliser les conseils.
        </Text>
        
        {/* Disclaimer */}
        <View style={styles.disclaimerCard}>
          <AlertCircle size={16} color="#FF9500" />
          <Text style={styles.disclaimerText}>
            Ceci n'est pas un diagnostic. Ces informations servent uniquement à personnaliser vos conseils.
          </Text>
        </View>
      </View>

      {/* Search Input */}
      <View style={styles.searchContainer}>
        <View style={styles.searchInputContainer}>
          <Search size={20} color="#8E8E93" />
          <TextInput
            style={styles.searchInput}
            placeholder="Tapez pour rechercher..."
            placeholderTextColor="#6C6C6E"
            value={query}
            onChangeText={handleSearch}
            autoCapitalize="none"
            autoCorrect={false}
            autoFocus={true}
            returnKeyType="search"
          />
          {searching && query.length >= 2 && (
            <ActivityIndicator size="small" color="#34C759" style={styles.searchingIndicator} />
          )}
          {query.length > 0 && !searching && (
            <TouchableOpacity
              onPress={() => {
                setQuery('');
                setSearchResults([]);
                setSearchError(null);
                if (searchTimeoutRef.current) {
                  clearTimeout(searchTimeoutRef.current);
                }
              }}
              style={styles.clearButton}
            >
              <X size={18} color="#8E8E93" />
            </TouchableOpacity>
          )}
        </View>
        {query.length > 0 && query.length < 2 && (
          <Text style={styles.searchHint}>
            Tapez au moins 2 caractères...
          </Text>
        )}
      </View>

      {/* Results */}
      <ScrollView style={styles.resultsContainer} contentContainerStyle={styles.resultsContent}>
        {searching && suggestions.length === 0 && searchResults.length === 0 && query.length >= 2 && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#34C759" />
            <Text style={styles.loadingText}>Recherche en cours...</Text>
          </View>
        )}

        {!searching && searchError && suggestions.length === 0 && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{searchError}</Text>
          </View>
        )}

        {/* Suggestions grand public (prioritaires) */}
        {!searching && suggestions.length > 0 && (
          <View style={styles.suggestionsList}>
            <View style={styles.suggestionsHeaderContainer}>
              <Sparkles size={18} color="#FF9500" />
              <Text style={styles.suggestionsHeader}>
                Suggestions
              </Text>
            </View>
            {suggestions.map((suggestion, index) => {
              const isAdded = suggestion.codes?.some((code: string) => addedConditions.has(code));
              
              return (
                <TouchableOpacity
                  key={`suggestion-${index}`}
                  style={[
                    styles.suggestionCard,
                    isAdded && styles.resultCardAdded
                  ]}
                  onPress={() => handleAddCondition(suggestion)}
                  disabled={adding || isAdded}
                  activeOpacity={0.7}
                >
                  <View style={styles.resultContent}>
                    <Text style={[
                      styles.suggestionTitle,
                      isAdded && styles.resultTitleAdded
                    ]}>
                      {suggestion.label}
                    </Text>
                    <View style={styles.suggestionBadge}>
                      <Text style={styles.suggestionBadgeText}>Terme courant</Text>
                    </View>
                  </View>
                  <View style={styles.resultAction}>
                    {isAdded ? (
                      <View style={styles.addedBadge}>
                        <Check size={18} color="#34C759" />
                        <Text style={styles.addedText}>Ajouté</Text>
                      </View>
                    ) : adding ? (
                      <ActivityIndicator size="small" color="#34C759" />
                    ) : (
                      <View style={styles.addButton}>
                        <Plus size={20} color="#FFFFFF" />
                      </View>
                    )}
                  </View>
                </TouchableOpacity>
              );
            })}
          </View>
        )}

        {/* Résultats ICD-11 détaillés */}
        {!searching && !searchError && searchResults.length > 0 && (
          <View style={styles.resultsList}>
            <View style={styles.resultsHeaderContainer}>
              <Text style={styles.resultsHeader}>
                Résultats détaillés ({searchResults.length})
              </Text>
              {moreResults && (
                <Text style={styles.moreResultsHint}>+ autres résultats</Text>
              )}
            </View>
            {searchResults.map((result, index) => {
              const isAdded = addedConditions.has(result.code);
              const categoryColor = getCategoryColor(result.category || '');
              
              return (
                <TouchableOpacity
                  key={`${result.code}-${index}`}
                  style={[
                    styles.resultCard,
                    isAdded && styles.resultCardAdded
                  ]}
                  onPress={() => handleAddCondition(result)}
                  disabled={adding || isAdded}
                  activeOpacity={0.7}
                >
                  <View style={styles.resultContent}>
                    <Text style={[
                      styles.resultTitle,
                      isAdded && styles.resultTitleAdded
                    ]}>
                      {result.display}
                    </Text>
                    {result.category && (
                      <View style={[styles.categoryBadge, { backgroundColor: categoryColor + '20' }]}>
                        <View style={[styles.categoryDot, { backgroundColor: categoryColor }]} />
                        <Text style={[styles.categoryText, { color: categoryColor }]}>
                          {result.category}
                        </Text>
                      </View>
                    )}
                    <Text style={styles.resultCode}>Code ICD-11: {result.code}</Text>
                  </View>
                  <View style={styles.resultAction}>
                    {isAdded ? (
                      <View style={styles.addedBadge}>
                        <Check size={18} color="#34C759" />
                        <Text style={styles.addedText}>Ajouté</Text>
                      </View>
                    ) : adding ? (
                      <ActivityIndicator size="small" color="#34C759" />
                    ) : (
                      <View style={styles.addButton}>
                        <Plus size={20} color="#FFFFFF" />
                      </View>
                    )}
                  </View>
                </TouchableOpacity>
              );
            })}
          </View>
        )}

        {!searching && !searchError && query.length === 0 && suggestions.length === 0 && searchResults.length === 0 && (
          <View style={styles.emptyState}>
            <View style={styles.emptyStateIconContainer}>
              <Search size={48} color="#34C759" />
            </View>
            <Text style={styles.emptyStateTitle}>Recherche instantanée</Text>
            <Text style={styles.emptyStateText}>
              Commencez à taper pour voir les résultats en temps réel
            </Text>
            
            {/* Exemples populaires */}
            <View style={styles.examplesContainer}>
              <Text style={styles.examplesTitle}>✨ Recherches populaires</Text>
              <View style={styles.examplesGrid}>
                {[
                  { text: 'TDAH', icon: '🧠', color: '#FF9500' },
                  { text: 'Dépression', icon: '💭', color: '#FF9500' },
                  { text: 'Diabète', icon: '🩺', color: '#5E5CE6' },
                  { text: 'Anxiété', icon: '💫', color: '#FF375F' },
                  { text: 'SOP', icon: '🔬', color: '#FF2D55' },
                ].map((example) => (
                  <TouchableOpacity
                    key={example.text}
                    style={[styles.exampleChipNew, { borderColor: example.color }]}
                    onPress={() => handleSearch(example.text)}
                    activeOpacity={0.7}
                  >
                    <Text style={styles.exampleIcon}>{example.icon}</Text>
                    <Text style={styles.exampleChipTextNew}>{example.text}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        )}
      </ScrollView>

      {/* Option: Je préfère ne pas répondre */}
      <View style={styles.footer}>
        <TouchableOpacity
          style={styles.skipButton}
          onPress={onClose}
        >
          <Text style={styles.skipButtonText}>Je préfère ne pas répondre</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#2C2C2E',
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  subtitle: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
    marginBottom: 16,
  },
  closeButton: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
  },
  disclaimerCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1C1C1E',
    borderRadius: 12,
    padding: 12,
    gap: 8,
    borderWidth: 1,
    borderColor: '#FF9500',
  },
  disclaimerText: {
    flex: 1,
    fontSize: 12,
    color: '#FF9500',
    lineHeight: 16,
  },
  searchContainer: {
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  searchInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 12,
    borderWidth: 2,
    borderColor: '#34C759',
    shadowColor: '#34C759',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: '#FFFFFF',
  },
  searchingIndicator: {
    marginRight: 4,
  },
  clearButton: {
    padding: 4,
  },
  searchHint: {
    fontSize: 12,
    color: '#6C6C6E',
    marginTop: 8,
    marginLeft: 4,
  },
  resultsContainer: {
    flex: 1,
  },
  resultsContent: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  loadingContainer: {
    paddingVertical: 60,
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 14,
    color: '#8E8E93',
    marginTop: 12,
  },
  errorContainer: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  errorText: {
    fontSize: 14,
    color: '#FF3B30',
  },
  resultsList: {
    gap: 12,
  },
  suggestionsList: {
    gap: 12,
    marginBottom: 24,
  },
  suggestionsHeaderContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
    paddingHorizontal: 4,
  },
  suggestionsHeader: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FF9500',
  },
  suggestionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#1C1C1E',
    borderRadius: 20,
    padding: 18,
    gap: 16,
    borderWidth: 2,
    borderColor: '#FF9500',
    shadowColor: '#FF9500',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
  },
  suggestionTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#FFFFFF',
    lineHeight: 22,
    marginBottom: 6,
  },
  suggestionBadge: {
    backgroundColor: '#FF950020',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  suggestionBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#FF9500',
  },
  resultsHeaderContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
    paddingHorizontal: 4,
  },
  resultsHeader: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E93',
  },
  moreResultsHint: {
    fontSize: 11,
    color: '#6C6C6E',
    fontStyle: 'italic',
  },
  resultCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#1C1C1E',
    borderRadius: 20,
    padding: 18,
    gap: 16,
    borderWidth: 2,
    borderColor: '#2C2C2E',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
  },
  resultCardAdded: {
    backgroundColor: '#0A2618',
    borderColor: '#34C759',
    opacity: 0.6,
  },
  resultContent: {
    flex: 1,
    gap: 8,
  },
  resultTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#FFFFFF',
    lineHeight: 22,
  },
  resultTitleAdded: {
    color: '#8E8E93',
  },
  categoryBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
    gap: 6,
  },
  categoryDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  categoryText: {
    fontSize: 12,
    fontWeight: '600',
  },
  resultCategory: {
    fontSize: 13,
    color: '#8E8E93',
  },
  resultCode: {
    fontSize: 11,
    color: '#6C6C6E',
    fontWeight: '500',
  },
  resultAction: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  addButton: {
    width: 44,
    height: 44,
    backgroundColor: '#34C759',
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#34C759',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  addedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#0A2618',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#34C759',
  },
  addedText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#34C759',
  },
  emptyState: {
    paddingVertical: 40,
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  emptyStateIconContainer: {
    width: 80,
    height: 80,
    backgroundColor: '#1C1C1E',
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#34C759',
    marginBottom: 20,
  },
  emptyStateTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  emptyStateText: {
    fontSize: 15,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 22,
  },
  examplesContainer: {
    marginTop: 36,
    width: '100%',
  },
  examplesTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 16,
  },
  examplesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  exampleChipNew: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1C1C1E',
    borderRadius: 20,
    paddingVertical: 12,
    paddingHorizontal: 16,
    gap: 8,
    borderWidth: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  exampleIcon: {
    fontSize: 18,
  },
  exampleChipTextNew: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  exampleChip: {
    backgroundColor: '#1C1C1E',
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 16,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  exampleChipText: {
    fontSize: 14,
    color: '#FFFFFF',
  },
  footer: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderTopWidth: 1,
    borderTopColor: '#2C2C2E',
  },
  skipButton: {
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    paddingVertical: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  skipButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E93',
  },
});
