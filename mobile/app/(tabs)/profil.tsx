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
import { useHealthData } from '@/hooks/useHealthData';
import { storage } from '@/lib/storage';
import { ChevronLeft, MoreVertical, Target, User as UserIcon, Settings as SettingsIcon, TrendingUp, Heart, Pill } from 'lucide-react-native';

export default function ProfilScreen() {
  const { userProfile, loadingUserProfile, fetchUserProfile } = useHealthData();
  const [signingOut, setSigningOut] = useState(false);

  // Load profile on mount
  useEffect(() => {
    fetchUserProfile();
  }, [fetchUserProfile]);


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
          <ActivityIndicator size="large" color="#7B6CF6" />
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.headerButton}>
          <ChevronLeft size={28} color="#FFFFFF" strokeWidth={2.5} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Account</Text>
        <TouchableOpacity 
          style={styles.headerButton}
          onPress={() => router.push('/profil-old')}
        >
          <MoreVertical size={28} color="#FFFFFF" strokeWidth={2.5} />
        </TouchableOpacity>
      </View>

      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Badge comparaison */}
        <View style={styles.comparisonBadge}>
          <Text style={styles.comparisonText}>🆕 Nouvelle version</Text>
          <TouchableOpacity 
            style={styles.comparisonButton}
            onPress={() => router.push('/profil-old')}
          >
            <Text style={styles.comparisonButtonText}>Voir ancienne version →</Text>
          </TouchableOpacity>
        </View>

        {/* Profile Avatar & Name */}
        <View style={styles.profileSection}>
          <View style={styles.avatarContainer}>
            <View style={styles.avatar}>
              {/* Simple avatar with initials */}
              <Text style={styles.avatarText}>
                {userProfile?.full_name?.split(' ').map((n: string) => n[0]).join('').toUpperCase() || 'U'}
              </Text>
            </View>
          </View>
          <Text style={styles.userName}>{userProfile?.full_name || 'Utilisateur'}</Text>
          <View style={styles.proBadge}>
            <Text style={styles.proText}>Pro</Text>
          </View>
        </View>

        {/* Menu Items */}
        <View style={styles.menuContainer}>
          {/* Goals */}
          <TouchableOpacity 
            style={styles.menuItem}
            onPress={() => router.push('/goals')}
            activeOpacity={0.7}
          >
            <View style={[styles.menuIcon, { backgroundColor: '#FF6B35' }]}>
              <Target size={24} color="#FFFFFF" strokeWidth={2.5} />
            </View>
            <Text style={styles.menuText}>Goals</Text>
            <View style={styles.menuArrow} />
          </TouchableOpacity>

          {/* My Body */}
          <TouchableOpacity 
            style={styles.menuItem}
            onPress={() => router.push('/my-body')}
            activeOpacity={0.7}
          >
            <View style={[styles.menuIcon, { backgroundColor: '#FF6B9D' }]}>
              <UserIcon size={24} color="#FFFFFF" strokeWidth={2.5} />
            </View>
            <Text style={styles.menuText}>My Body</Text>
            <View style={styles.menuArrow} />
          </TouchableOpacity>

          {/* Settings */}
          <TouchableOpacity 
            style={styles.menuItem}
            onPress={() => router.push('/settings')}
            activeOpacity={0.7}
          >
            <View style={[styles.menuIcon, { backgroundColor: '#4ECDC4' }]}>
              <SettingsIcon size={24} color="#FFFFFF" strokeWidth={2.5} />
            </View>
            <Text style={styles.menuText}>Settings</Text>
            <View style={styles.menuArrow} />
          </TouchableOpacity>

          {/* Normalisation */}
          <TouchableOpacity 
            style={styles.menuItem}
            onPress={() => router.push('/baselines')}
            activeOpacity={0.7}
          >
            <View style={[styles.menuIcon, { backgroundColor: '#7B6CF6' }]}>
              <TrendingUp size={24} color="#FFFFFF" strokeWidth={2.5} />
            </View>
            <Text style={styles.menuText}>Normalisation</Text>
            <View style={styles.menuArrow} />
          </TouchableOpacity>

          {/* Conditions de santé */}
          <TouchableOpacity 
            style={styles.menuItem}
            onPress={() => router.push('/health-conditions')}
            activeOpacity={0.7}
          >
            <View style={[styles.menuIcon, { backgroundColor: '#FF2D55' }]}>
              <Heart size={24} color="#FFFFFF" strokeWidth={2.5} />
            </View>
            <Text style={styles.menuText}>Conditions de santé</Text>
            <View style={styles.menuArrow} />
          </TouchableOpacity>

          {/* Médicaments */}
          <TouchableOpacity 
            style={styles.menuItem}
            onPress={() => router.push('/medications')}
            activeOpacity={0.7}
          >
            <View style={[styles.menuIcon, { backgroundColor: '#5E5CE6' }]}>
              <Pill size={24} color="#FFFFFF" strokeWidth={2.5} />
            </View>
            <Text style={styles.menuText}>Médicaments</Text>
            <View style={styles.menuArrow} />
          </TouchableOpacity>
        </View>

        {/* Sign Out Button */}
        <View style={styles.signOutContainer}>
          <TouchableOpacity
            style={[styles.signOutButton, signingOut && styles.signOutButtonDisabled]}
            onPress={handleSignOut}
            disabled={signingOut}
            activeOpacity={0.8}
          >
            {signingOut ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <Text style={styles.signOutText}>Sign Out</Text>
            )}
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0D0D1F',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
    backgroundColor: '#0D0D1F',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 40,
  },
  headerButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 0.3,
  },
  comparisonBadge: {
    backgroundColor: '#7B6CF620',
    borderRadius: 16,
    padding: 16,
    marginHorizontal: 20,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#7B6CF640',
  },
  comparisonText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#7B6CF6',
    marginBottom: 8,
    letterSpacing: 0.3,
  },
  comparisonButton: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  comparisonButtonText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#FFFFFF',
    letterSpacing: 0.2,
  },
  profileSection: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  avatarContainer: {
    marginBottom: 20,
  },
  avatar: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#7B6CF6',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: '#FFFFFF15',
  },
  avatarText: {
    fontSize: 36,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  userName: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 10,
    letterSpacing: 0.3,
  },
  proBadge: {
    backgroundColor: '#FF6B35',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 6,
  },
  proText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 0.5,
  },
  menuContainer: {
    paddingHorizontal: 20,
    gap: 0,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 18,
    paddingHorizontal: 16,
    backgroundColor: '#1A1A2E',
    marginBottom: 12,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#FFFFFF10',
  },
  menuIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  menuText: {
    fontSize: 17,
    fontWeight: '600',
    color: '#FFFFFF',
    flex: 1,
    letterSpacing: 0.2,
  },
  menuArrow: {
    width: 8,
    height: 8,
    borderTopWidth: 2,
    borderRightWidth: 2,
    borderColor: '#FFFFFF60',
    transform: [{ rotate: '45deg' }],
  },
  signOutContainer: {
    paddingHorizontal: 20,
    marginTop: 32,
    paddingBottom: 20,
  },
  signOutButton: {
    backgroundColor: 'transparent',
    borderRadius: 20,
    paddingVertical: 18,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#FFFFFF20',
  },
  signOutButtonDisabled: {
    opacity: 0.5,
  },
  signOutText: {
    fontSize: 17,
    fontWeight: '600',
    color: '#FFFFFF',
    letterSpacing: 0.3,
  },
});
