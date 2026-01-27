import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { supabase } from '../lib/supabase';
import { storage } from '../lib/storage';
import InsightCard from '../components/InsightCard';

interface Insight {
  id: string;
  instruction_text: string;
  category?: string;
  created_at: string;
}

export default function HomeScreen() {
  const [insight, setInsight] = useState<Insight | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userName, setUserName] = useState<string>('');

  useEffect(() => {
    fetchLatestInsight();
    fetchUserName();
  }, []);

  const fetchLatestInsight = async () => {
    try {
      setLoading(true);
      setError(null);

      // Récupérer l'UUID depuis le stockage local
      const targetUserId = await storage.getUserId();
      if (!targetUserId) {
        setError('Utilisateur non connecté');
        setLoading(false);
        return;
      }

      // Utiliser la fonction PostgreSQL qui contourne RLS
      const { data: insightData, error: fetchError } = await supabase
        .rpc('get_latest_insight', { user_uuid: targetUserId });

      if (fetchError) {
        console.error('Erreur lors de la récupération de l\'insight:', fetchError);
        setError(fetchError.message);
        return;
      }

      if (insightData && insightData.length > 0) {
        setInsight(insightData[0]);
      } else {
        setInsight(null);
      }
    } catch (err) {
      console.error('Erreur inattendue:', err);
      setError('Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  };

  const fetchUserName = async () => {
    try {
      // Récupérer l'UUID depuis le stockage local
      const targetUserId = await storage.getUserId();
      if (targetUserId) {
        // Utiliser la fonction PostgreSQL qui contourne RLS
        const { data: nameData, error: nameError } = await supabase
          .rpc('get_user_name', { user_uuid: targetUserId });
        
        if (!nameError && nameData && nameData.length > 0 && nameData[0].full_name) {
          setUserName(nameData[0].full_name);
        } else {
          setUserName('Utilisateur');
        }
      } else {
        setUserName('Utilisateur');
      }
    } catch (err) {
      console.error('Erreur lors de la récupération du nom:', err);
      setUserName('Utilisateur');
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.greeting}>Bonjour {userName}</Text>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#FFFFFF" />
          <Text style={styles.loadingText}>Chargement...</Text>
        </View>
      ) : error ? (
        <View style={styles.center}>
          <Text style={styles.errorText}>Erreur: {error}</Text>
          <Text style={styles.debugText}>
            Vérifiez que les variables EXPO_PUBLIC_SUPABASE_URL et EXPO_PUBLIC_SUPABASE_ANON_KEY sont configurées.
          </Text>
        </View>
      ) : insight ? (
        <InsightCard
          instructionText={insight.instruction_text}
          category={insight.category}
          createdAt={insight.created_at}
        />
      ) : (
        <View style={styles.center}>
          <Text style={styles.emptyText}>Aucun insight disponible</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
    paddingTop: 60,
    paddingHorizontal: 20,
  },
  header: {
    marginBottom: 24,
  },
  greeting: {
    fontSize: 28,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    color: '#FFFFFF',
    fontSize: 16,
  },
  errorText: {
    color: '#FF3B30',
    fontSize: 16,
    marginBottom: 8,
    textAlign: 'center',
  },
  debugText: {
    color: '#999999',
    fontSize: 12,
    textAlign: 'center',
    marginTop: 8,
    paddingHorizontal: 20,
  },
  emptyText: {
    color: '#999999',
    fontSize: 16,
  },
});
