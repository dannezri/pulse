import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import { supabase } from '../lib/supabase';
import { storage } from '../lib/storage';

export default function LoginScreen({ onLoginSuccess }: { onLoginSuccess: () => void }) {
  const [openWearablesUserId, setOpenWearablesUserId] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!openWearablesUserId.trim()) {
      Alert.alert('Erreur', 'Veuillez entrer votre Open Wearables User ID');
      return;
    }

    const trimmedId = openWearablesUserId.trim();

    try {
      setLoading(true);

      // Utiliser la fonction PostgreSQL pour rechercher par open_wearables_user_id
      // Cette fonction contourne RLS pour permettre la recherche
      const { data: profileData, error: profileError } = await supabase
        .rpc('get_user_by_open_wearables_id', { open_wearables_id: trimmedId });

      if (profileError) {
        console.error('Erreur Supabase:', profileError);
        Alert.alert('Erreur', `Erreur lors de la recherche: ${profileError.message}`);
        return;
      }

      if (!profileData || profileData.length === 0) {
        Alert.alert('Erreur', `Open Wearables User ID "${trimmedId}" non trouvé dans la base de données`);
        return;
      }

      // Récupérer l'UUID Supabase du profil
      const profile = profileData[0];
      const supabaseUserId = profile.id;

      // Stocker l'UUID localement (sans authentification Supabase)
      await storage.saveUserId(supabaseUserId);

      onLoginSuccess();
    } catch (err) {
      Alert.alert('Erreur', 'Une erreur est survenue');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Pulse</Text>
      <Text style={styles.subtitle}>
        Entrez votre Open Wearables User ID
      </Text>

      <View style={styles.form}>
        <TextInput
          style={styles.input}
          placeholder="Open Wearables User ID"
          placeholderTextColor="#666"
          value={openWearablesUserId}
          onChangeText={setOpenWearablesUserId}
          autoCapitalize="none"
          autoCorrect={false}
          editable={!loading}
        />

        <TouchableOpacity
          style={[styles.button, loading && styles.buttonDisabled]}
          onPress={handleLogin}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#000" />
          ) : (
            <Text style={styles.buttonText}>Se connecter</Text>
          )}
        </TouchableOpacity>

        <Text style={styles.helpText}>
          Entrez votre identifiant Open Wearables
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
    justifyContent: 'center',
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 48,
    fontWeight: '700',
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 18,
    color: '#999999',
    textAlign: 'center',
    marginBottom: 40,
  },
  form: {
    width: '100%',
  },
  input: {
    backgroundColor: '#1A1A1A',
    borderWidth: 1,
    borderColor: '#333333',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: '#FFFFFF',
    marginBottom: 16,
  },
  button: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#000000',
    fontSize: 16,
    fontWeight: '600',
  },
  helpText: {
    marginTop: 16,
    color: '#666666',
    fontSize: 12,
    textAlign: 'center',
  },
});
