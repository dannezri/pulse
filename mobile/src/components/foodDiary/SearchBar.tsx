/**
 * SearchBar - Barre de recherche d'aliments (Design Pulse)
 * UI Pure : Pas de logique métier
 */

import React from 'react'
import { View, TextInput, StyleSheet, ActivityIndicator, TouchableOpacity } from 'react-native'
import { Search, X } from 'lucide-react-native'

interface SearchBarProps {
  value: string
  onChangeText: (text: string) => void
  placeholder?: string
  loading?: boolean
  autoFocus?: boolean
}

export const SearchBar: React.FC<SearchBarProps> = ({
  value,
  onChangeText,
  placeholder = 'Rechercher un aliment...',
  loading = false,
  autoFocus = false
}) => {
  return (
    <View style={styles.container}>
      <Search size={20} color="#8E8E93" style={styles.icon} />
      
      <TextInput
        style={styles.input}
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor="#666666"
        autoFocus={autoFocus}
        autoCapitalize="none"
        autoCorrect={false}
        returnKeyType="search"
      />
      
      {loading && (
        <ActivityIndicator size="small" color="#00FF41" style={styles.loader} />
      )}
      
      {!loading && value.length > 0 && (
        <TouchableOpacity onPress={() => onChangeText('')} style={styles.clearButton}>
          <X size={20} color="#8E8E93" />
        </TouchableOpacity>
      )}
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#2C2C2E',
    paddingHorizontal: 16,
    paddingVertical: 14
  },
  icon: {
    marginRight: 12
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: '#FFFFFF',
    fontWeight: '500'
  },
  loader: {
    marginLeft: 12
  },
  clearButton: {
    marginLeft: 12,
    padding: 4
  }
})
