import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { router } from 'expo-router';
import { useHealthData } from '@/src/hooks/useHealthData';
import { storage } from '@/src/lib/storage';
import { User, Mail, Target, Watch, CheckCircle2, LogOut } from 'lucide-react-native';

type HealthGoal = 'energy' | 'focus' | 'recovery';

const HEALTH_GOAL_LABELS: Record<HealthGoal, string> = {
  energy: 'Energy',
  focus: 'Focus',
  recovery: 'Recovery',
};

export default function ProfilScreen() {
  const { userProfile, loadingUserProfile, fetchUserProfile, updateHealthGoal } = useHealthData();
  const [updating, setUpdating] = useState(false);
  const [signingOut, setSigningOut] = useState(false);

  // Load profile on mount
  useEffect(() => {
    fetchUserProfile();
  }, [fetchUserProfile]);

  const handleUpdateGoal = async (newGoal: HealthGoal) => {
    if (updating || !userProfile) return;

    setUpdating(true);
    const success = await updateHealthGoal(newGoal);
    if (!success) {
      console.error('Failed to update health goal');
    }
    setUpdating(false);
  };

  const handleSignOut = async () => {
    Alert.alert(
      'Déconnexion',
      'Êtes-vous sûr de vouloir vous déconnecter ?',
      [
        {
          text: 'Annuler',
          style: 'cancel',
        },
        {
          text: 'Déconnexion',
          style: 'destructive',
          onPress: async () => {
            setSigningOut(true);
            try {
              // Effacer le stockage local
              await storage.clearUserId();
              
              // Rediriger vers la page de login
              router.replace('/login');
            } catch (error) {
              console.error('Exception signing out:', error);
              Alert.alert('Erreur', 'Une erreur est survenue lors de la déconnexion.');
              setSigningOut(false);
            }
          },
        },
      ]
    );
  };

  if (loadingUserProfile) {
    return (
      <View style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#34C759" />
        </View>
      </View>
    );
  }

  const isWearableConnected = !!userProfile?.open_wearables_user_id;
  const currentGoal = (userProfile?.health_goal as HealthGoal) || 'energy';

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Profil</Text>
      </View>

      {/* Info Utilisateur */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <User size={20} color="#FFFFFF" />
          <Text style={styles.sectionTitle}>Informations</Text>
        </View>
        <View style={styles.infoCard}>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Nom</Text>
            <Text style={styles.infoValue}>{userProfile?.full_name || 'Non défini'}</Text>
          </View>
          <View style={styles.infoRow}>
            <Mail size={16} color="#8E8E93" />
            <Text style={styles.infoLabel}>Email</Text>
            <Text style={styles.infoValue}>Utilisateur connecté</Text>
          </View>
        </View>
      </View>

      {/* Objectif Santé */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Target size={20} color="#FFFFFF" />
          <Text style={styles.sectionTitle}>Objectif Santé</Text>
        </View>
        <View style={styles.goalCard}>
          <Text style={styles.goalDescription}>
            Sélectionnez votre objectif principal. L'IA adaptera ses conseils en conséquence.
          </Text>
          <View style={styles.goalOptions}>
            {(['energy', 'focus', 'recovery'] as HealthGoal[]).map((goal) => (
              <TouchableOpacity
                key={goal}
                style={[
                  styles.goalOption,
                  currentGoal === goal && styles.goalOptionActive,
                  updating && styles.goalOptionDisabled,
                ]}
                onPress={() => handleUpdateGoal(goal)}
                disabled={updating}
              >
                <Text
                  style={[
                    styles.goalOptionText,
                    currentGoal === goal && styles.goalOptionTextActive,
                  ]}
                >
                  {HEALTH_GOAL_LABELS[goal]}
                </Text>
                {currentGoal === goal && (
                  <CheckCircle2 size={18} color="#34C759" style={styles.checkIcon} />
                )}
              </TouchableOpacity>
            ))}
          </View>
          {updating && (
            <View style={styles.updatingIndicator}>
              <ActivityIndicator size="small" color="#34C759" />
              <Text style={styles.updatingText}>Mise à jour...</Text>
            </View>
          )}
        </View>
      </View>

      {/* Statut Connexion Wearable */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Watch size={20} color="#FFFFFF" />
          <Text style={styles.sectionTitle}>Wearable</Text>
        </View>
        <View style={styles.wearableCard}>
          <View style={styles.wearableStatus}>
            {isWearableConnected ? (
              <>
                <CheckCircle2 size={24} color="#34C759" />
                <View style={styles.wearableInfo}>
                  <Text style={styles.wearableStatusText}>Connecté</Text>
                  <Text style={styles.wearableStatusSubtext}>
                    Vos données sont synchronisées
                  </Text>
                </View>
              </>
            ) : (
              <>
                <View style={styles.wearableIconPlaceholder} />
                <View style={styles.wearableInfo}>
                  <Text style={styles.wearableStatusText}>Non connecté</Text>
                  <Text style={styles.wearableStatusSubtext}>
                    Connectez un wearable pour commencer
                  </Text>
                </View>
              </>
            )}
          </View>
        </View>
      </View>

      {/* Bouton Déconnexion */}
      <View style={styles.section}>
        <TouchableOpacity
          style={[styles.logoutButton, signingOut && styles.logoutButtonDisabled]}
          onPress={handleSignOut}
          disabled={signingOut}
        >
          {signingOut ? (
            <ActivityIndicator size="small" color="#FF3B30" />
          ) : (
            <LogOut size={20} color="#FF3B30" />
          )}
          <Text style={styles.logoutButtonText}>
            {signingOut ? 'Déconnexion...' : 'Déconnexion'}
          </Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  contentContainer: {
    padding: 20,
    paddingTop: 60,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    marginBottom: 32,
  },
  title: {
    fontSize: 32,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  section: {
    marginBottom: 32,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 8,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  infoCard: {
    backgroundColor: '#1C1C1E',
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 12,
  },
  infoLabel: {
    fontSize: 16,
    color: '#8E8E93',
    fontWeight: '500',
    minWidth: 80,
  },
  infoValue: {
    fontSize: 16,
    color: '#FFFFFF',
    fontWeight: '600',
    flex: 1,
  },
  goalCard: {
    backgroundColor: '#1C1C1E',
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  goalDescription: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
    marginBottom: 20,
  },
  goalOptions: {
    gap: 12,
  },
  goalOption: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#2C2C2E',
    borderRadius: 16,
    padding: 16,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  goalOptionActive: {
    backgroundColor: '#1C1C1E',
    borderColor: '#34C759',
  },
  goalOptionDisabled: {
    opacity: 0.5,
  },
  goalOptionText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#8E8E93',
  },
  goalOptionTextActive: {
    color: '#FFFFFF',
  },
  checkIcon: {
    marginLeft: 'auto',
  },
  updatingIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 12,
    gap: 8,
  },
  updatingText: {
    fontSize: 14,
    color: '#8E8E93',
  },
  wearableCard: {
    backgroundColor: '#1C1C1E',
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  wearableStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  wearableIconPlaceholder: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#2C2C2E',
  },
  wearableInfo: {
    flex: 1,
  },
  wearableStatusText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  wearableStatusSubtext: {
    fontSize: 14,
    color: '#8E8E93',
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1C1C1E',
    borderRadius: 20,
    padding: 16,
    borderWidth: 1,
    borderColor: '#FF3B30',
    gap: 12,
  },
  logoutButtonDisabled: {
    opacity: 0.5,
  },
  logoutButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FF3B30',
  },
});
