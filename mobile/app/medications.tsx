import React, { useState } from 'react';
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
import { ChevronLeft, Pill, Plus, Calendar, Clock, TrendingUp, TrendingDown, Activity, Zap, Info } from 'lucide-react-native';
import { useAuth } from '@/hooks/useAuth';
import { useMedications } from '@/hooks/useMedications';
import { useMedicationImpacts } from '@/hooks/useMedicationImpacts';
import { useMedicationAnalysis } from '@/hooks/useMedicationAnalysis';
import { useMedicationHistorySync } from '@/hooks/useMedicationHistorySync';
import { MedicationFormSimplified } from '@/components/MedicationFormSimplified';
import { MedicationCard } from '@/components/MedicationCard';
import { MedicationHistoryTab } from '@/components/MedicationHistoryTab';
import { QuickMarkAllButton } from '@/components/QuickMarkAllButton';
import { TreatmentOverview } from '@/components/TreatmentOverview';

type TabType = 'medications' | 'history';

export default function MedicationsScreen() {
  const [medicationFormVisible, setMedicationFormVisible] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('medications');
  const { userId } = useAuth();
  const { medications, loading: loadingMedications, addMedication, deleteMedication, getTodayMedications } = useMedications();
  const { getMedicationImpact, getTotalImpact, loading: loadingImpacts } = useMedicationImpacts(userId);
  const { data: analysisData, isLoading: loadingAnalysis, error: analysisError } = useMedicationAnalysis({ userId });
  
  // Synchroniser l'historique des médicaments à l'ouverture de cette page
  useMedicationHistorySync(userId);

  // Debug: Log des analyses
  React.useEffect(() => {
    console.log('[Medications] 🔍 Debug Analyses Gemini:');
    console.log('  - userId:', userId);
    console.log('  - analysisData:', analysisData);
    console.log('  - loadingAnalysis:', loadingAnalysis);
    console.log('  - analysisError:', analysisError);
    if (analysisData?.analyse_traitements) {
      console.log('  - Nombre d\'analyses:', analysisData.analyse_traitements.length);
      analysisData.analyse_traitements.forEach((item, idx) => {
        console.log(`  - [${idx}] ${item.nom}`);
      });
    }
    if (medications.length > 0) {
      console.log('  - Médicaments actuels:');
      medications.forEach((med, idx) => {
        console.log(`  - [${idx}] ${med.name}`);
      });
    }
  }, [analysisData, loadingAnalysis, analysisError, userId, medications]);

  // Helper pour obtenir l'analyse d'un médicament avec matching flexible
  const getMedicationAnalysis = (medicationName: string) => {
    if (!analysisData || !analysisData.analyse_traitements) {
      console.log(`[Medications] ⚠️ Pas de données d'analyse disponibles pour ${medicationName}`);
      return null;
    }
    
    const normalizedSearchName = medicationName.toLowerCase().trim();
    
    const found = analysisData.analyse_traitements.find((item) => {
      const normalizedItemName = item.nom.toLowerCase().trim();
      
      // 1. Exact match
      if (normalizedItemName === normalizedSearchName) return true;
      
      // 2. Partial match - l'un contient l'autre
      if (normalizedItemName.includes(normalizedSearchName)) return true;
      if (normalizedSearchName.includes(normalizedItemName)) return true;
      
      // 3. Match sans la forme pharmaceutique (", gélule", ", comprimé", etc.)
      const searchWithoutForm = normalizedSearchName.split(',')[0].trim();
      const itemWithoutForm = normalizedItemName.split(',')[0].trim();
      
      if (searchWithoutForm === itemWithoutForm) return true;
      if (searchWithoutForm.includes(itemWithoutForm)) return true;
      if (itemWithoutForm.includes(searchWithoutForm)) return true;
      
      return false;
    });
    
    console.log(`[Medications] 🔎 Recherche analyse pour "${medicationName}": ${found ? '✅ Trouvée' : '❌ Non trouvée'}`);
    if (found) {
      console.log(`[Medications]    ↳ Matché avec: "${found.nom}"`);
    }
    return found || null;
  };

  const handleAddMedication = async (medication: any) => {
    try {
      await addMedication(medication);
      setMedicationFormVisible(false);
      Alert.alert('✅ Ajouté', `${medication.name} a été enregistré.`);
    } catch (error) {
      console.error('[Medications] Erreur ajout médicament:', error);
      Alert.alert('Erreur', 'Impossible d\'ajouter le médicament.');
    }
  };

  const handleDeleteMedication = async (id: string) => {
    try {
      await deleteMedication(id);
    } catch (error) {
      console.error('[Medications] Erreur suppression médicament:', error);
      Alert.alert('Erreur', 'Impossible de supprimer le médicament.');
    }
  };

  const todayMedications = getTodayMedications();
  const totalImpact = getTotalImpact();

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.headerButton}
          onPress={() => router.back()}
        >
          <ChevronLeft size={28} color="#FFFFFF" strokeWidth={2.5} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Médicaments</Text>
        <TouchableOpacity 
          style={styles.headerButton}
          onPress={() => setMedicationFormVisible(true)}
        >
          <Plus size={28} color="#FFFFFF" strokeWidth={2.5} />
        </TouchableOpacity>
      </View>

      {/* Onglets */}
      <View style={styles.tabContainer}>
        <TouchableOpacity 
          style={[styles.tab, activeTab === 'medications' && styles.tabActive]}
          onPress={() => setActiveTab('medications')}
          activeOpacity={0.7}
        >
          <Pill size={20} color={activeTab === 'medications' ? '#5E5CE6' : '#8E8E93'} strokeWidth={2.5} />
          <Text style={[styles.tabText, activeTab === 'medications' && styles.tabTextActive]}>
            Mes Médicaments
          </Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.tab, activeTab === 'history' && styles.tabActive]}
          onPress={() => setActiveTab('history')}
          activeOpacity={0.7}
        >
          <Calendar size={20} color={activeTab === 'history' ? '#5E5CE6' : '#8E8E93'} strokeWidth={2.5} />
          <Text style={[styles.tabText, activeTab === 'history' && styles.tabTextActive]}>
            Historique
          </Text>
        </TouchableOpacity>
      </View>

      {activeTab === 'medications' ? (
        <ScrollView 
          style={styles.content}
          contentContainerStyle={styles.contentContainer}
          showsVerticalScrollIndicator={false}
        >
          <>
            {/* Hero Section */}
            <View style={styles.heroSection}>
              <Text style={styles.heroTitle}>Vos Médicaments</Text>
              <Text style={styles.heroSubtitle}>
                Analyse détaillée de l'impact énergétique de chaque traitement
              </Text>
            </View>

            {/* Analyse globale des traitements par Gemini */}
            <TreatmentOverview 
              userId={userId} 
              medications={medications}
            />

        {/* Stats Overview avec Impact Énergétique - ENHANCED */}
        {medications.length > 0 && !loadingMedications && (
          <View style={styles.statsContainer}>
            {/* Today Card */}
            <View style={styles.statCard}>
              <View style={styles.statIconContainer}>
                <Clock size={20} color="#5E5CE6" strokeWidth={2.5} />
              </View>
              <Text style={styles.statValue}>{todayMedications.length}</Text>
              <Text style={styles.statLabel}>Aujourd'hui</Text>
            </View>

            {/* Total Card */}
            <View style={styles.statCard}>
              <View style={styles.statIconContainer}>
                <Pill size={20} color="#5E5CE6" strokeWidth={2.5} />
              </View>
              <Text style={styles.statValue}>{medications.length}</Text>
              <Text style={styles.statLabel}>Total</Text>
            </View>

            {/* Impact Card - HERO */}
            <View style={[
              styles.statCardImpact,
              totalImpact > 0 && styles.statCardPositive,
              totalImpact < 0 && styles.statCardNegative,
            ]}>
              <View style={[
                styles.impactIconLarge,
                totalImpact > 0 && styles.impactIconPositive,
                totalImpact < 0 && styles.impactIconNegative,
              ]}>
                {totalImpact > 0 ? (
                  <TrendingUp size={32} color="#34C759" strokeWidth={3} />
                ) : totalImpact < 0 ? (
                  <TrendingDown size={32} color="#FF3B30" strokeWidth={3} />
                ) : (
                  <Activity size={32} color="#8E8E93" strokeWidth={3} />
                )}
              </View>
              <Text style={[
                styles.statValueImpact,
                totalImpact > 0 && styles.statValuePositive,
                totalImpact < 0 && styles.statValueNegative,
              ]}>
                {totalImpact > 0 ? '+' : ''}{totalImpact.toFixed(1)}%
              </Text>
              <Text style={styles.statLabelImpact}>Impact Total</Text>
            </View>
          </View>
        )}

        {/* Today's Medications */}
        {todayMedications.length > 0 && !loadingMedications && (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Clock size={20} color="#5E5CE6" strokeWidth={2.5} />
              <Text style={styles.sectionTitle}>Aujourd'hui</Text>
              <Text style={styles.sectionCount}>{todayMedications.length}</Text>
            </View>
            
            {todayMedications.map((medication) => (
              <MedicationCard
                key={medication.id}
                medication={medication}
                impact={getMedicationImpact(medication)}
                analysis={getMedicationAnalysis(medication.name)}
                onDelete={handleDeleteMedication}
                showImpact={true}
              />
            ))}
          </View>
        )}

        {/* All Medications */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Pill size={20} color="#5E5CE6" strokeWidth={2.5} />
            <Text style={styles.sectionTitle}>Tous les médicaments</Text>
            {medications.length > 0 && !loadingMedications && (
              <Text style={styles.sectionCount}>{medications.length}</Text>
            )}
          </View>
          
          {loadingMedications ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#5E5CE6" />
              <Text style={styles.loadingText}>Chargement des médicaments...</Text>
            </View>
          ) : medications.length > 0 ? (
            <>
              {medications.map((medication) => (
                <MedicationCard
                  key={medication.id}
                  medication={medication}
                  impact={getMedicationImpact(medication)}
                  analysis={getMedicationAnalysis(medication.name)}
                  onDelete={handleDeleteMedication}
                  showImpact={true}
                />
              ))}
            </>
          ) : (
            <View style={styles.emptyState}>
              <View style={styles.emptyIconContainer}>
                <Pill size={64} color="#FFFFFF40" strokeWidth={2} />
              </View>
              <Text style={styles.emptyTitle}>Aucun médicament enregistré</Text>
              <Text style={styles.emptyDescription}>
                Commencez par ajouter vos médicaments pour suivre vos traitements et obtenir des analyses plus précises.
              </Text>
              <TouchableOpacity
                style={styles.emptyButton}
                onPress={() => setMedicationFormVisible(true)}
                activeOpacity={0.8}
              >
                <Plus size={20} color="#FFFFFF" strokeWidth={2.5} />
                <Text style={styles.emptyButtonText}>Ajouter un médicament</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Add Button (when medications exist) */}
        {medications.length > 0 && !loadingMedications && (
          <TouchableOpacity
            style={styles.addButton}
            onPress={() => setMedicationFormVisible(true)}
            activeOpacity={0.8}
          >
            <Plus size={20} color="#FFFFFF" strokeWidth={2.5} />
            <Text style={styles.addButtonText}>Ajouter un médicament</Text>
          </TouchableOpacity>
        )}

        {/* Impact Énergétique Expliqué - ENHANCED */}
        {medications.length > 0 && !loadingImpacts && (
          <View style={styles.section}>
            <View style={styles.sectionHeaderWithIcon}>
              <View style={styles.sectionIconBadge}>
                <Zap size={20} color="#FFB800" strokeWidth={2.5} />
              </View>
              <Text style={styles.sectionTitle}>Comment ça marche ?</Text>
            </View>
            
            <View style={styles.impactExplainCard}>
              <Text style={styles.impactExplainIntro}>
                L'impact énergétique est calculé en temps réel grâce à :
              </Text>
              <View style={styles.impactExplainList}>
                <View style={styles.impactExplainItem}>
                  <View style={styles.impactExplainIconBadge}>
                    <Pill size={16} color="#5E5CE6" strokeWidth={2} />
                  </View>
                  <View style={styles.impactExplainContent}>
                    <Text style={styles.impactExplainItemBold}>Dosage total</Text>
                    <Text style={styles.impactExplainItemText}>
                      Nombre de comprimés × dosage unitaire
                    </Text>
                  </View>
                </View>
                <View style={styles.impactExplainItem}>
                  <View style={styles.impactExplainIconBadge}>
                    <Clock size={16} color="#5E5CE6" strokeWidth={2} />
                  </View>
                  <View style={styles.impactExplainContent}>
                    <Text style={styles.impactExplainItemBold}>Pharmacocinétique</Text>
                    <Text style={styles.impactExplainItemText}>
                      Courbe d'absorption et élimination
                    </Text>
                  </View>
                </View>
                <View style={styles.impactExplainItem}>
                  <View style={styles.impactExplainIconBadge}>
                    <Calendar size={16} color="#5E5CE6" strokeWidth={2} />
                  </View>
                  <View style={styles.impactExplainContent}>
                    <Text style={styles.impactExplainItemBold}>Adaptation chronique</Text>
                    <Text style={styles.impactExplainItemText}>
                      Effet à long terme selon la durée
                    </Text>
                  </View>
                </View>
                <View style={styles.impactExplainItem}>
                  <View style={styles.impactExplainIconBadge}>
                    <Activity size={16} color="#5E5CE6" strokeWidth={2} />
                  </View>
                  <View style={styles.impactExplainContent}>
                    <Text style={styles.impactExplainItemBold}>Profil personnalisé</Text>
                    <Text style={styles.impactExplainItemText}>
                      Poids ML adapté à votre organisme
                    </Text>
                  </View>
                </View>
              </View>
            </View>
          </View>
        )}

        {/* Why it matters */}
        <View style={styles.section}>
          <View style={styles.sectionHeaderWithIcon}>
            <View style={[styles.sectionIconBadge, { backgroundColor: 'rgba(94, 92, 230, 0.15)', borderColor: 'rgba(94, 92, 230, 0.3)' }]}>
              <Info size={20} color="#5E5CE6" strokeWidth={2.5} />
            </View>
            <Text style={styles.sectionTitle}>Pourquoi c'est important ?</Text>
          </View>
          
          <View style={styles.whyCard}>
            <View style={styles.whyItem}>
              <View style={styles.whyIcon}>
                <Text style={styles.whyEmoji}>⚡</Text>
              </View>
              <View style={styles.whyContent}>
                <Text style={styles.whyTitle}>Impact en temps réel</Text>
                <Text style={styles.whyDescription}>
                  Visualisez comment chaque médicament affecte votre énergie
                </Text>
              </View>
            </View>

            <View style={styles.whyDivider} />

            <View style={styles.whyItem}>
              <View style={styles.whyIcon}>
                <Text style={styles.whyEmoji}>🎯</Text>
              </View>
              <View style={styles.whyContent}>
                <Text style={styles.whyTitle}>Dosage optimisé</Text>
                <Text style={styles.whyDescription}>
                  Ajustez vos doses selon votre ressenti et l'impact mesuré
                </Text>
              </View>
            </View>

            <View style={styles.whyDivider} />

            <View style={styles.whyItem}>
              <View style={styles.whyIcon}>
                <Text style={styles.whyEmoji}>📊</Text>
              </View>
              <View style={styles.whyContent}>
                <Text style={styles.whyTitle}>Analyses précises</Text>
                <Text style={styles.whyDescription}>
                  Des insights basés sur la pharmacocinétique et vos données
                </Text>
              </View>
            </View>
          </View>
        </View>
          </>
        </ScrollView>
      ) : (
        /* Onglet Historique */
        <View style={styles.content}>
          <MedicationHistoryTab />
        </View>
      )}

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
            <MedicationFormSimplified
              onSubmit={handleAddMedication}
              onCancel={() => setMedicationFormVisible(false)}
            />
          </ScrollView>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0A0A12',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 16,
    backgroundColor: 'rgba(13, 13, 31, 0.95)',
    borderBottomWidth: 0,
    borderBottomColor: 'rgba(255, 255, 255, 0.05)',
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: 'rgba(13, 13, 31, 0.95)',
    paddingHorizontal: 16,
    paddingBottom: 12,
    gap: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.05)',
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 16,
    backgroundColor: 'rgba(26, 26, 46, 0.4)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.05)',
  },
  tabActive: {
    backgroundColor: 'rgba(94, 92, 230, 0.15)',
    borderColor: 'rgba(94, 92, 230, 0.4)',
  },
  tabText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E93',
    letterSpacing: 0.2,
  },
  tabTextActive: {
    color: '#5E5CE6',
    fontWeight: '700',
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
  content: {
    flex: 1,
  },
  contentContainer: {
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 40,
  },
  heroSection: {
    marginBottom: 24,
  },
  heroTitle: {
    fontSize: 32,
    fontWeight: '900',
    color: '#FFFFFF',
    marginBottom: 8,
    letterSpacing: -0.5,
  },
  heroSubtitle: {
    fontSize: 15,
    fontWeight: '500',
    color: '#8E8E93',
    lineHeight: 22,
  },
  infoCard: {
    backgroundColor: '#5E5CE620',
    borderRadius: 24,
    padding: 24,
    alignItems: 'center',
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#5E5CE640',
  },
  infoIconContainer: {
    width: 64,
    height: 64,
    backgroundColor: '#5E5CE640',
    borderRadius: 32,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  infoTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 12,
    textAlign: 'center',
    letterSpacing: 0.3,
  },
  infoDescription: {
    fontSize: 14,
    fontWeight: '500',
    color: '#FFFFFF80',
    textAlign: 'center',
    lineHeight: 20,
  },
  statsContainer: {
    flexDirection: 'row',
    gap: 14,
    marginBottom: 32,
  },
  statCard: {
    flex: 1,
    backgroundColor: 'rgba(26, 26, 46, 0.6)',
    borderRadius: 20,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    gap: 10,
  },
  statIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: 'rgba(94, 92, 230, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  statValue: {
    fontSize: 32,
    fontWeight: '900',
    color: '#FFFFFF',
    letterSpacing: -1,
  },
  statLabel: {
    fontSize: 10,
    fontWeight: '800',
    color: 'rgba(255, 255, 255, 0.5)',
    textAlign: 'center',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },
  statCardImpact: {
    flex: 1.2,
    borderRadius: 20,
    padding: 20,
    alignItems: 'center',
    borderWidth: 2,
    gap: 8,
  },
  statCardPositive: {
    backgroundColor: 'rgba(52, 199, 89, 0.15)',
    borderColor: 'rgba(52, 199, 89, 0.4)',
  },
  statCardNegative: {
    backgroundColor: 'rgba(255, 59, 48, 0.15)',
    borderColor: 'rgba(255, 59, 48, 0.4)',
  },
  impactIconLarge: {
    width: 56,
    height: 56,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  impactIconPositive: {
    backgroundColor: 'rgba(52, 199, 89, 0.2)',
  },
  impactIconNegative: {
    backgroundColor: 'rgba(255, 59, 48, 0.2)',
  },
  statValueImpact: {
    fontSize: 36,
    fontWeight: '900',
    color: '#FFFFFF',
    letterSpacing: -1.5,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  statValuePositive: {
    color: '#34C759',
  },
  statValueNegative: {
    color: '#FF3B30',
  },
  statLabelImpact: {
    fontSize: 10,
    fontWeight: '800',
    color: 'rgba(255, 255, 255, 0.6)',
    textAlign: 'center',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },
  impactExplainCard: {
    backgroundColor: 'rgba(94, 92, 230, 0.1)',
    borderRadius: 24,
    padding: 24,
    borderWidth: 2,
    borderColor: 'rgba(94, 92, 230, 0.3)',
  },
  impactExplainIntro: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 20,
    lineHeight: 22,
  },
  impactExplainList: {
    gap: 16,
  },
  impactExplainItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 14,
  },
  impactExplainIconBadge: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: 'rgba(94, 92, 230, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(94, 92, 230, 0.3)',
  },
  impactExplainContent: {
    flex: 1,
    gap: 4,
  },
  impactExplainItemBold: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 0.2,
  },
  impactExplainItemText: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.7)',
    lineHeight: 18,
  },
  section: {
    marginBottom: 36,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 18,
  },
  sectionHeaderWithIcon: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 18,
  },
  sectionIconBadge: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: 'rgba(255, 184, 0, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 184, 0, 0.3)',
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: '#FFFFFF',
    flex: 1,
    letterSpacing: -0.3,
  },
  sectionCount: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF60',
    backgroundColor: '#5E5CE620',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  loadingContainer: {
    backgroundColor: '#1A1A2E',
    borderRadius: 20,
    padding: 48,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#FFFFFF10',
  },
  loadingText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF60',
    marginTop: 16,
  },
  emptyState: {
    backgroundColor: 'rgba(26, 26, 46, 0.4)',
    borderRadius: 28,
    padding: 56,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    borderStyle: 'dashed',
  },
  emptyIconContainer: {
    width: 120,
    height: 120,
    backgroundColor: '#FFFFFF10',
    borderRadius: 60,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 12,
    textAlign: 'center',
  },
  emptyDescription: {
    fontSize: 14,
    fontWeight: '500',
    color: '#FFFFFF60',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 24,
  },
  emptyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#5E5CE6',
    borderRadius: 20,
    paddingVertical: 18,
    paddingHorizontal: 36,
    gap: 12,
    shadowColor: '#5E5CE6',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.4,
    shadowRadius: 16,
    elevation: 8,
  },
  emptyButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 0.3,
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#5E5CE6',
    borderRadius: 20,
    paddingVertical: 18,
    gap: 12,
    marginBottom: 32,
    shadowColor: '#5E5CE6',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.4,
    shadowRadius: 16,
    elevation: 8,
  },
  addButtonText: {
    fontSize: 17,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 0.3,
  },
  whyCard: {
    backgroundColor: 'rgba(26, 26, 46, 0.6)',
    borderRadius: 20,
    padding: 24,
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  whyItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 16,
  },
  whyIcon: {
    width: 52,
    height: 52,
    backgroundColor: 'rgba(94, 92, 230, 0.12)',
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: 'rgba(94, 92, 230, 0.25)',
  },
  whyEmoji: {
    fontSize: 24,
  },
  whyContent: {
    flex: 1,
    paddingTop: 4,
  },
  whyTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 6,
    letterSpacing: 0.2,
  },
  whyDescription: {
    fontSize: 14,
    fontWeight: '500',
    color: '#FFFFFF60',
    lineHeight: 20,
  },
  whyDivider: {
    height: 1,
    backgroundColor: '#FFFFFF10',
    marginVertical: 20,
  },
  tipsCard: {
    backgroundColor: '#FFB80020',
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: '#FFB80040',
  },
  tipsTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFB800',
    marginBottom: 12,
    letterSpacing: 0.2,
  },
  tipsText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#FFB800',
    lineHeight: 22,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#0A0A12',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#FFFFFF10',
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
    backgroundColor: '#1A1A2E',
    borderRadius: 18,
    borderWidth: 1,
    borderColor: '#FFFFFF10',
  },
  closeButtonText: {
    fontSize: 18,
    color: '#FFFFFF',
    fontWeight: '700',
  },
  modalContent: {
    flex: 1,
  },
});
