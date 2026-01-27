/**
 * Écran de gestion des médicaments
 * Design aligné avec le reste de l'app
 */

import React, { useState } from 'react';
import { 
  View, 
  Text, 
  TouchableOpacity, 
  Modal, 
  SafeAreaView, 
  ActivityIndicator, 
  Alert,
  ScrollView,
  StyleSheet 
} from 'react-native';
import { useMedications } from '../../src/hooks/useMedications';
import { MedicationForm } from '../../src/components/MedicationForm';
import { MedicationList } from '../../src/components/MedicationList';
import { FadeInView } from '../../src/components/FadeInView';
import { PressableScale } from '../../src/components/PressableScale';
import { Plus, Pill } from 'lucide-react-native';

export default function MedicationsScreen() {
  const [showForm, setShowForm] = useState(false);
  const { medications, loading, addMedication, deleteMedication, getTodayMedications } = useMedications();

  const todayCount = getTodayMedications().length;

  const handleAdd = async (medication: any) => {
    try {
      await addMedication(medication);
      setShowForm(false);
      Alert.alert('✅ Ajouté', `${medication.name} a été enregistré.`);
    } catch (error) {
      console.error('[MedicationsScreen] Erreur ajout:', error);
      Alert.alert('Erreur', 'Impossible d\'ajouter le médicament.');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteMedication(id);
    } catch (error) {
      console.error('[MedicationsScreen] Erreur suppression:', error);
      Alert.alert('Erreur', 'Impossible de supprimer le médicament.');
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#34C759" />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.contentContainer}
      >
        {/* Header */}
        <FadeInView delay={0} duration={600}>
          <View style={styles.header}>
            <View>
              <Text style={styles.subtitle}>
                {new Date().toLocaleDateString('fr-FR', {
                  weekday: 'long',
                  day: 'numeric',
                  month: 'long'
                })}
              </Text>
              <Text style={styles.title}>💊 Médicaments</Text>
            </View>
          </View>
        </FadeInView>

        {/* Stats Cards */}
        <FadeInView delay={100} duration={600}>
          <View style={styles.statsContainer}>
            <View style={styles.statCard}>
              <Pill size={20} color="#34C759" />
              <Text style={styles.statValue}>{todayCount}</Text>
              <Text style={styles.statLabel}>Aujourd'hui</Text>
            </View>
            <View style={styles.statCard}>
              <Pill size={20} color="#5E5CE6" />
              <Text style={styles.statValue}>{medications.length}</Text>
              <Text style={styles.statLabel}>Total</Text>
            </View>
          </View>
        </FadeInView>

        {/* Add Button */}
        <FadeInView delay={200} duration={600}>
          <PressableScale
            style={styles.addButton}
            onPress={() => setShowForm(true)}
          >
            <Plus size={20} color="#FFFFFF" />
            <Text style={styles.addButtonText}>Ajouter un médicament</Text>
          </PressableScale>
        </FadeInView>

        {/* List Section */}
        <FadeInView delay={300} duration={600}>
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Historique</Text>
              {medications.length > 0 && (
                <Text style={styles.sectionSubtitle}>
                  {medications.length} enregistrement{medications.length !== 1 ? 's' : ''}
                </Text>
              )}
            </View>
            
            {medications.length === 0 ? (
              <View style={styles.emptyState}>
                <Text style={styles.emptyIcon}>💊</Text>
                <Text style={styles.emptyTitle}>Aucun médicament</Text>
                <Text style={styles.emptyText}>
                  Commencez à suivre vos prises de médicaments pour une meilleure analyse de votre santé.
                </Text>
              </View>
            ) : (
              <MedicationList
                medications={medications}
                onDelete={handleDelete}
              />
            )}
          </View>
        </FadeInView>
      </ScrollView>

      {/* Modal formulaire */}
      <Modal
        visible={showForm}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowForm(false)}
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Ajouter un médicament</Text>
            <TouchableOpacity 
              onPress={() => setShowForm(false)}
              style={styles.closeButton}
            >
              <Text style={styles.closeButtonText}>✕</Text>
            </TouchableOpacity>
          </View>
          <ScrollView style={styles.modalContent}>
            <MedicationForm
              onSubmit={handleAdd}
              onCancel={() => setShowForm(false)}
            />
          </ScrollView>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  scrollView: {
    flex: 1,
  },
  contentContainer: {
    padding: 20,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    marginBottom: 24,
  },
  subtitle: {
    fontSize: 14,
    color: '#8E8E93',
    fontWeight: '500',
    marginBottom: 4,
  },
  title: {
    fontSize: 32,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  statsContainer: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 24,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#2C2C2E',
    alignItems: 'center',
  },
  statValue: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FFFFFF',
    marginTop: 8,
  },
  statLabel: {
    fontSize: 12,
    color: '#8E8E93',
    marginTop: 4,
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#5E5CE6',
    borderRadius: 16,
    paddingVertical: 16,
    paddingHorizontal: 24,
    marginBottom: 32,
    gap: 8,
  },
  addButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  section: {
    marginBottom: 32,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  sectionSubtitle: {
    fontSize: 12,
    color: '#8E8E93',
  },
  emptyState: {
    backgroundColor: '#1C1C1E',
    borderRadius: 20,
    padding: 32,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2C2C2E',
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 12,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 20,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#000000',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#2C2C2E',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  closeButton: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
  },
  closeButtonText: {
    fontSize: 20,
    color: '#8E8E93',
  },
  modalContent: {
    flex: 1,
  },
});
