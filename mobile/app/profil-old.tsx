import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Modal,
} from 'react-native';
import { router } from 'expo-router';
import { useHealthData } from '@/hooks/useHealthData';
import { useBaselines } from '@/hooks/useBaselines';
import { useMedications } from '@/hooks/useMedications';
import { useConditions } from '@/hooks/useConditions';
import { useEnergyProfile } from '@/hooks/useEnergyProfile';
import { storage } from '@/lib/storage';
import { User, Mail, Watch, CheckCircle2, LogOut, TrendingUp, Activity, RefreshCw, Pill, Plus, Heart, X, ChevronLeft } from 'lucide-react-native';
import BaselineCard from '@/components/BaselineCard';
import { EventTracker } from '@/components/EventTracker';
import { MedicationForm } from '@/components/MedicationForm';
import { MedicationList } from '@/components/MedicationList';
import { ConditionPicker } from '@/components/ConditionPicker';
import { EnergyProfileCard } from '@/components/EnergyProfileCard';

export default function ProfilOldScreen() {
  const { userProfile, loadingUserProfile, fetchUserProfile } = useHealthData();
  const [signingOut, setSigningOut] = useState(false);
  const [eventTrackerVisible, setEventTrackerVisible] = useState(false);
  const [medicationFormVisible, setMedicationFormVisible] = useState(false);
  const [conditionPickerVisible, setConditionPickerVisible] = useState(false);
  const [recalculating, setRecalculating] = useState(false);
  
  // Baselines personnelles
  const { baselines, loading: loadingBaselines, triggerRecalculation } = useBaselines(userProfile?.id || null);
  
  // Médicaments
  const { medications, loading: loadingMedications, addMedication, deleteMedication, getTodayMedications } = useMedications();
  
  // Conditions de santé
  const { conditions, loading: loadingConditions, deleteCondition, fetchConditions } = useConditions();

  // Profil énergétique personnel
  const { data: energyProfile, isLoading: loadingEnergyProfile } = useEnergyProfile(userProfile?.id || null);

  // Load profile on mount
  useEffect(() => {
    fetchUserProfile();
  }, [fetchUserProfile]);

  const handleRecalculateBaselines = async () => {
    if (recalculating) return;
    
    setRecalculating(true);
    const success = await triggerRecalculation();
    setRecalculating(false);
    
    if (success) {
      Alert.alert('Succès', 'Les baselines ont été recalculées.');
    } else {
      Alert.alert('Erreur', 'Impossible de recalculer les baselines.');
    }
  };

  const handleAddMedication = async (medication: any) => {
    try {
      await addMedication(medication);
      setMedicationFormVisible(false);
      Alert.alert('✅ Ajouté', `${medication.name} a été enregistré.`);
    } catch (error) {
      console.error('[ProfilScreen] Erreur ajout médicament:', error);
      Alert.alert('Erreur', 'Impossible d\'ajouter le médicament.');
    }
  };

  const handleDeleteMedication = async (id: string) => {
    try {
      await deleteMedication(id);
    } catch (error) {
      console.error('[ProfilScreen] Erreur suppression médicament:', error);
      Alert.alert('Erreur', 'Impossible de supprimer le médicament.');
    }
  };

  const handleDeleteCondition = async (id: string, display: string) => {
    Alert.alert(
      'Supprimer la condition',
      `Voulez-vous retirer "${display}" de votre profil ?`,
      [
        { text: 'Annuler', style: 'cancel' },
        {
          text: 'Supprimer',
          style: 'destructive',
          onPress: async () => {
            try {
              const success = await deleteCondition(id);
              if (!success) {
                Alert.alert('Erreur', 'Impossible de supprimer la condition.');
              }
            } catch (error) {
              console.error('[ProfilScreen] Erreur suppression condition:', error);
              Alert.alert('Erreur', 'Impossible de supprimer la condition.');
            }
          },
        },
      ]
    );
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
              await storage.clearUserId();
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

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      {/* Header avec bouton retour */}
      <View style={styles.headerWithBack}>
        <TouchableOpacity 
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <ChevronLeft size={28} color="#FFFFFF" strokeWidth={2.5} />
        </TouchableOpacity>
        <Text style={styles.title}>Profil (Ancienne Version)</Text>
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

      {/* Profil Énergétique Personnel */}
      {!loadingEnergyProfile && energyProfile && (
        <EnergyProfileCard profile={energyProfile} />
      )}

      {/* Conditions de santé */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Heart size={20} color="#FF2D55" />
          <Text style={styles.sectionTitle}>Conditions de santé</Text>
          <View style={styles.optionalBadge}>
            <Text style={styles.optionalText}>Facultatif</Text>
          </View>
        </View>
        <Text style={styles.sectionDescription}>
          💡 Renseignez vos conditions pour des conseils personnalisés et plus précis.
        </Text>

        {loadingConditions ? (
          <View style={styles.conditionsLoadingContainer}>
            <ActivityIndicator size="large" color="#34C759" />
            <Text style={styles.loadingConditionsText}>Chargement...</Text>
          </View>
        ) : conditions.length > 0 ? (
          <>
            <View style={styles.conditionsHeader}>
              <Text style={styles.conditionsCount}>
                {conditions.length} condition{conditions.length > 1 ? 's' : ''} renseignée{conditions.length > 1 ? 's' : ''}
              </Text>
            </View>
            <View style={styles.conditionsChipsContainer}>
              {conditions.map((condition, index) => (
                <View 
                  key={condition.id} 
                  style={[
                    styles.conditionChip,
                    { 
                      backgroundColor: index % 3 === 0 ? '#FF950020' : 
                                       index % 3 === 1 ? '#5E5CE620' : '#34C75920',
                      borderColor: index % 3 === 0 ? '#FF9500' : 
                                   index % 3 === 1 ? '#5E5CE6' : '#34C759'
                    }
                  ]}
                >
                  <View style={styles.conditionChipContent}>
                    <View style={[
                      styles.conditionChipDot,
                      { backgroundColor: index % 3 === 0 ? '#FF9500' : 
                                        index % 3 === 1 ? '#5E5CE6' : '#34C759' }
                    ]} />
                    <Text style={styles.conditionChipText} numberOfLines={2}>
                      {condition.display}
                    </Text>
                  </View>
                  <TouchableOpacity
                    onPress={() => handleDeleteCondition(condition.id, condition.display)}
                    style={styles.conditionChipDelete}
                    hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                  >
                    <X size={16} color="#FFFFFF" />
                  </TouchableOpacity>
                </View>
              ))}
            </View>
          </>
        ) : (
          <View style={styles.emptyConditionState}>
            <View style={styles.emptyConditionIcon}>
              <Heart size={32} color="#FF2D55" />
            </View>
            <Text style={styles.emptyConditionTitle}>
              Aucune condition renseignée
            </Text>
            <Text style={styles.emptyConditionText}>
              Commencez par ajouter vos conditions de santé pour des conseils plus personnalisés
            </Text>
          </View>
        )}

        <TouchableOpacity
          style={styles.addConditionButton}
          onPress={() => setConditionPickerVisible(true)}
          activeOpacity={0.8}
        >
          <View style={styles.addConditionButtonIcon}>
            <Plus size={20} color="#FFFFFF" />
          </View>
          <Text style={styles.addConditionButtonText}>
            {conditions.length > 0 ? 'Ajouter une condition' : 'Renseigner mes conditions'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Journal d'Activités */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Activity size={20} color="#FFFFFF" />
          <Text style={styles.sectionTitle}>Journal d'Activités</Text>
        </View>
        <Text style={styles.sectionDescription}>
          Suivez votre consommation de caféine, d'alcool, vos repas et vos séances de sport pour des analyses plus précises.
        </Text>
        <TouchableOpacity
          style={styles.logEventButton}
          onPress={() => setEventTrackerVisible(true)}
        >
          <Activity size={20} color="#FFFFFF" />
          <Text style={styles.logEventButtonText}>Enregistrer un événement</Text>
        </TouchableOpacity>
      </View>

      {/* Médicaments */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Pill size={20} color="#FFFFFF" />
          <Text style={styles.sectionTitle}>Médicaments</Text>
        </View>
        <Text style={styles.sectionDescription}>
          Suivez vos prises de médicaments pour une meilleure analyse de votre santé.
        </Text>
        
        {/* Stats */}
        <View style={styles.medicationStats}>
          <View style={styles.medicationStatCard}>
            <Text style={styles.medicationStatValue}>{getTodayMedications().length}</Text>
            <Text style={styles.medicationStatLabel}>Aujourd'hui</Text>
          </View>
          <View style={styles.medicationStatCard}>
            <Text style={styles.medicationStatValue}>{medications.length}</Text>
            <Text style={styles.medicationStatLabel}>Total</Text>
          </View>
        </View>

        {/* Bouton d'ajout */}
        <TouchableOpacity
          style={styles.addMedicationButton}
          onPress={() => setMedicationFormVisible(true)}
        >
          <Plus size={20} color="#FFFFFF" />
          <Text style={styles.addMedicationButtonText}>Ajouter un médicament</Text>
        </TouchableOpacity>

        {/* Liste des médicaments récents */}
        {loadingMedications ? (
          <View style={styles.medicationLoadingContainer}>
            <ActivityIndicator size="small" color="#34C759" />
          </View>
        ) : medications.length > 0 ? (
          <View>
            <MedicationList
              medications={medications.slice(0, 5)}
              onDelete={handleDeleteMedication}
            />
            {medications.length > 5 && (
              <Text style={styles.medicationMoreText}>
                et {medications.length - 5} autre{medications.length - 5 > 1 ? 's' : ''}...
              </Text>
            )}
          </View>
        ) : (
          <View style={styles.emptyMedicationState}>
            <Text style={styles.emptyMedicationText}>
              Aucun médicament enregistré
            </Text>
          </View>
        )}
      </View>

      {/* Baselines Personnelles */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <TrendingUp size={20} color="#FFFFFF" />
          <Text style={styles.sectionTitle}>Normalisation Personnelle</Text>
        </View>
        <Text style={styles.sectionDescription}>
          Vos métriques de référence personnelles, calculées automatiquement à partir de vos données.
        </Text>
        
        {loadingBaselines ? (
          <View style={styles.baselinesLoadingContainer}>
            <ActivityIndicator size="large" color="#34C759" />
            <Text style={styles.baselinesLoadingText}>Chargement des baselines...</Text>
          </View>
        ) : baselines && baselines.length > 0 ? (
          <>
            <View style={styles.baselinesGrid}>
              {baselines.map((baseline) => (
                <BaselineCard key={baseline.baseline_type} baseline={baseline} />
              ))}
            </View>
            
            <TouchableOpacity
              style={[styles.recalculateButton, recalculating && styles.recalculateButtonDisabled]}
              onPress={handleRecalculateBaselines}
              disabled={recalculating}
            >
              {recalculating ? (
                <ActivityIndicator size="small" color="#34C759" />
              ) : (
                <RefreshCw size={18} color="#34C759" />
              )}
              <Text style={styles.recalculateButtonText}>
                {recalculating ? 'Recalcul en cours...' : 'Recalculer manuellement'}
              </Text>
            </TouchableOpacity>
            <Text style={styles.recalculateInfoText}>
              Note: Les baselines sont recalculées automatiquement chaque nuit.
            </Text>
          </>
        ) : (
          <View style={styles.noBaselinesContainer}>
            <Text style={styles.noBaselinesText}>
              Aucune baseline disponible pour le moment.
            </Text>
            <Text style={styles.noBaselinesSubtext}>
              Continuez à enregistrer vos données de santé pour générer vos baselines personnelles.
            </Text>
          </View>
        )}
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

      {/* Modal Event Tracker */}
      <Modal
        visible={eventTrackerVisible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setEventTrackerVisible(false)}
      >
        <EventTracker
          onClose={() => setEventTrackerVisible(false)}
          onSuccess={() => {}}
        />
      </Modal>

      {/* Modal Medication Form */}
      <Modal
        visible={medicationFormVisible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setMedicationFormVisible(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Ajouter un médicament</Text>
            <TouchableOpacity 
              onPress={() => setMedicationFormVisible(false)}
              style={styles.closeButton}
            >
              <Text style={styles.closeButtonText}>✕</Text>
            </TouchableOpacity>
          </View>
          <ScrollView 
            style={styles.modalContent}
            keyboardShouldPersistTaps="handled"
            nestedScrollEnabled={true}
          >
            <MedicationForm
              onSubmit={handleAddMedication}
              onCancel={() => setMedicationFormVisible(false)}
            />
          </ScrollView>
        </View>
      </Modal>

      {/* Modal Condition Picker */}
      <Modal
        visible={conditionPickerVisible}
        animationType="slide"
        presentationStyle="fullScreen"
        onRequestClose={() => setConditionPickerVisible(false)}
      >
        <ConditionPicker
          onClose={() => setConditionPickerVisible(false)}
          onSuccess={() => {
            fetchConditions();
          }}
        />
      </Modal>
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
    paddingBottom: 40,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerWithBack: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
    gap: 12,
  },
  backButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1C1C1E',
    borderRadius: 22,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: 0.5,
    flex: 1,
  },
  section: {
    marginBottom: 28,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 10,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    flex: 1,
  },
  infoCard: {
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: '#2C2C2E',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    gap: 12,
  },
  infoLabel: {
    fontSize: 15,
    color: '#8E8E93',
    fontWeight: '500',
    flex: 1,
  },
  infoValue: {
    fontSize: 15,
    color: '#FFFFFF',
    fontWeight: '600',
    flex: 2,
  },
  wearableCard: {
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: '#2C2C2E',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  wearableStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  wearableIconPlaceholder: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#2C2C2E',
  },
  wearableInfo: {
    flex: 1,
  },
  wearableStatusText: {
    fontSize: 17,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  wearableStatusSubtext: {
    fontSize: 13,
    color: '#8E8E93',
    lineHeight: 18,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1C1C1E',
    borderRadius: 14,
    paddingVertical: 15,
    paddingHorizontal: 20,
    borderWidth: 1.5,
    borderColor: '#FF3B30',
    gap: 10,
    shadowColor: '#FF3B30',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
  },
  logoutButtonDisabled: {
    opacity: 0.6,
  },
  logoutButtonText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FF3B30',
    letterSpacing: 0.3,
  },
  sectionDescription: {
    fontSize: 13,
    color: '#8E8E93',
    lineHeight: 19,
    marginBottom: 14,
    letterSpacing: 0.1,
  },
  logEventButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#34C759',
    borderRadius: 14,
    paddingVertical: 15,
    paddingHorizontal: 20,
    gap: 10,
    shadowColor: '#34C759',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  logEventButtonText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 0.3,
  },
  baselinesLoadingContainer: {
    alignItems: 'center',
    paddingVertical: 48,
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  baselinesLoadingText: {
    fontSize: 13,
    color: '#8E8E93',
    marginTop: 12,
    fontWeight: '500',
  },
  baselinesGrid: {
    gap: 10,
  },
  recalculateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1C1C1E',
    borderRadius: 14,
    paddingVertical: 14,
    paddingHorizontal: 20,
    gap: 10,
    marginTop: 14,
    borderWidth: 1.5,
    borderColor: '#34C759',
  },
  recalculateButtonDisabled: {
    opacity: 0.6,
  },
  recalculateButtonText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#34C759',
    letterSpacing: 0.3,
  },
  recalculateInfoText: {
    fontSize: 11,
    color: '#6C6C6E',
    textAlign: 'center',
    marginTop: 10,
    fontStyle: 'italic',
    lineHeight: 16,
  },
  noBaselinesContainer: {
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    padding: 32,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#2C2C2E',
    borderStyle: 'dashed',
  },
  noBaselinesText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 8,
    textAlign: 'center',
  },
  noBaselinesSubtext: {
    fontSize: 13,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 19,
  },
  medicationStats: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 14,
  },
  medicationStatCard: {
    flex: 1,
    backgroundColor: '#1C1C1E',
    borderRadius: 14,
    paddingVertical: 18,
    paddingHorizontal: 16,
    borderWidth: 1,
    borderColor: '#2C2C2E',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
  },
  medicationStatValue: {
    fontSize: 28,
    fontWeight: '800',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  medicationStatLabel: {
    fontSize: 11,
    color: '#8E8E93',
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  addMedicationButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#5E5CE6',
    borderRadius: 14,
    paddingVertical: 15,
    paddingHorizontal: 24,
    marginBottom: 14,
    gap: 10,
    shadowColor: '#5E5CE6',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  addMedicationButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  medicationLoadingContainer: {
    padding: 24,
    alignItems: 'center',
    backgroundColor: '#1C1C1E',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  medicationMoreText: {
    fontSize: 11,
    color: '#8E8E93',
    textAlign: 'center',
    marginTop: 10,
    fontStyle: 'italic',
    fontWeight: '500',
  },
  emptyMedicationState: {
    backgroundColor: '#1C1C1E',
    borderRadius: 14,
    padding: 28,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#2C2C2E',
    borderStyle: 'dashed',
  },
  emptyMedicationText: {
    fontSize: 13,
    color: '#8E8E93',
    textAlign: 'center',
    fontWeight: '500',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#000000',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#2C2C2E',
    backgroundColor: '#000000',
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: 0.3,
  },
  closeButton: {
    width: 36,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1C1C1E',
    borderRadius: 18,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  closeButtonText: {
    fontSize: 18,
    color: '#8E8E93',
    fontWeight: '700',
  },
  modalContent: {
    flex: 1,
    backgroundColor: '#000000',
  },
  optionalBadge: {
    backgroundColor: '#2C2C2E',
    borderRadius: 10,
    paddingHorizontal: 10,
    paddingVertical: 4,
    marginLeft: 'auto',
  },
  optionalText: {
    fontSize: 10,
    color: '#8E8E93',
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  conditionsLoadingContainer: {
    padding: 40,
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  loadingConditionsText: {
    fontSize: 13,
    color: '#8E8E93',
    fontWeight: '500',
  },
  conditionsHeader: {
    marginBottom: 14,
  },
  conditionsCount: {
    fontSize: 12,
    fontWeight: '700',
    color: '#8E8E93',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  conditionsChipsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 18,
  },
  conditionChip: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderRadius: 14,
    paddingVertical: 10,
    paddingLeft: 12,
    paddingRight: 8,
    gap: 8,
    borderWidth: 1.5,
    minWidth: '45%',
    maxWidth: '100%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
  },
  conditionChipContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flex: 1,
  },
  conditionChipDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  conditionChipText: {
    fontSize: 13,
    color: '#FFFFFF',
    fontWeight: '700',
    flex: 1,
    lineHeight: 17,
  },
  conditionChipDelete: {
    width: 26,
    height: 26,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FF3B3080',
    borderRadius: 13,
  },
  addConditionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FF2D55',
    borderRadius: 14,
    paddingVertical: 15,
    paddingHorizontal: 24,
    gap: 10,
    shadowColor: '#FF2D55',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 10,
  },
  addConditionButtonIcon: {
    width: 22,
    height: 22,
    backgroundColor: '#FFFFFF30',
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
  },
  addConditionButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  emptyConditionState: {
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    padding: 32,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#2C2C2E',
    borderStyle: 'dashed',
    marginBottom: 14,
  },
  emptyConditionIcon: {
    width: 60,
    height: 60,
    backgroundColor: '#2C2C2E',
    borderRadius: 30,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 14,
  },
  emptyConditionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  emptyConditionText: {
    fontSize: 13,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 19,
  },
});
