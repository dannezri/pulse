/**
 * Page détaillée d'un médicament
 * Affiche notice, génériques, alternatives
 * Route: /medication-detail?id=...
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Linking,
  Alert
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { ChevronLeft, ExternalLink, Pill, FileText, Users, Lightbulb } from 'lucide-react-native';
import { API_URL } from '@/config/api';

interface MedicationDetails {
  id: string;
  external_id?: string;
  name: string;
  form?: string;
  laboratory?: string;
  active_substance?: string;
  atc_code?: string;
  notice_url?: string;
  notice_text?: string;
  generics: Array<{id: string; name: string; laboratory?: string}>;
  alternatives: Array<{id: string; name: string; laboratory?: string; reason?: string}>;
}

export default function MedicationDetailScreen() {
  const params = useLocalSearchParams();
  const medicationId = params.id as string;
  const medicationName = params.name as string; // Optionnel pour pré-affichage
  
  const [details, setDetails] = useState<MedicationDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'notice' | 'generics' | 'alternatives'>('notice');

  useEffect(() => {
    if (medicationId) {
      loadMedicationDetails();
    }
  }, [medicationId]);

  const loadMedicationDetails = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/medications/${medicationId}`);
      
      if (!response.ok) {
        throw new Error('Erreur chargement médicament');
      }
      
      const data = await response.json();
      setDetails(data);
    } catch (error) {
      console.error('[MedicationDetail] Erreur chargement:', error);
      Alert.alert('Erreur', 'Impossible de charger les détails du médicament');
    } finally {
      setLoading(false);
    }
  };

  const openNotice = () => {
    if (details?.notice_url) {
      Linking.openURL(details.notice_url);
    } else {
      Alert.alert('Notice indisponible', 'La notice de ce médicament n\'est pas disponible pour le moment.');
    }
  };

  const handleAddToTreatments = () => {
    if (!details) return;
    
    // Navigation vers le formulaire d'ajout de traitement
    router.push({
      pathname: '/add-treatment',
      params: {
        medicationId: details.id,
        medicationName: details.name
      }
    });
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#5E5CE6" />
        <Text style={styles.loadingText}>Chargement...</Text>
      </View>
    );
  }

  if (!details) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>Médicament non trouvé</Text>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>Retour</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <ChevronLeft size={28} color="#FFFFFF" strokeWidth={2.5} />
        </TouchableOpacity>
        <Text style={styles.headerTitle} numberOfLines={1}>
          {details.name}
        </Text>
        <View style={{width: 28}} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Card principale */}
        <View style={styles.mainCard}>
          <View style={styles.pillIconContainer}>
            <Pill size={40} color="#5E5CE6" strokeWidth={2.5} />
          </View>
          <Text style={styles.medicationName}>{details.name}</Text>
          {details.active_substance && (
            <Text style={styles.activeSubstance}>{details.active_substance}</Text>
          )}
          {details.laboratory && (
            <Text style={styles.laboratory}>{details.laboratory}</Text>
          )}
          {details.form && (
            <Text style={styles.form}>{details.form}</Text>
          )}
          {details.atc_code && (
            <Text style={styles.atcCode}>Code ATC: {details.atc_code}</Text>
          )}
        </View>

        {/* Tabs */}
        <View style={styles.tabs}>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'notice' && styles.tabActive]}
            onPress={() => setActiveTab('notice')}
          >
            <FileText size={20} color={activeTab === 'notice' ? '#5E5CE6' : '#8E8EA0'} />
            <Text style={[styles.tabText, activeTab === 'notice' && styles.tabTextActive]}>
              Notice
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.tab, activeTab === 'generics' && styles.tabActive]}
            onPress={() => setActiveTab('generics')}
          >
            <Users size={20} color={activeTab === 'generics' ? '#5E5CE6' : '#8E8EA0'} />
            <Text style={[styles.tabText, activeTab === 'generics' && styles.tabTextActive]}>
              Génériques ({details.generics.length})
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.tab, activeTab === 'alternatives' && styles.tabActive]}
            onPress={() => setActiveTab('alternatives')}
          >
            <Lightbulb size={20} color={activeTab === 'alternatives' ? '#5E5CE6' : '#8E8EA0'} />
            <Text style={[styles.tabText, activeTab === 'alternatives' && styles.tabTextActive]}>
              Alternatives ({details.alternatives.length})
            </Text>
          </TouchableOpacity>
        </View>

        {/* Contenu des tabs */}
        <View style={styles.tabContent}>
          {activeTab === 'notice' && (
            <View>
              {details.notice_url ? (
                <>
                  <Text style={styles.sectionTitle}>Notice officielle</Text>
                  <TouchableOpacity style={styles.noticeButton} onPress={openNotice}>
                    <ExternalLink size={20} color="#5E5CE6" />
                    <Text style={styles.noticeButtonText}>Consulter la notice</Text>
                  </TouchableOpacity>
                  <Text style={styles.noticeHint}>
                    La notice sera ouverte dans votre navigateur
                  </Text>
                </>
              ) : (
                <View style={styles.emptyState}>
                  <FileText size={48} color="#8E8EA0" strokeWidth={1.5} />
                  <Text style={styles.emptyText}>Notice non disponible</Text>
                  <Text style={styles.emptyHint}>
                    Les informations de notice ne sont pas encore disponibles pour ce médicament.
                  </Text>
                </View>
              )}
            </View>
          )}

          {activeTab === 'generics' && (
            <View>
              {details.generics.length > 0 ? (
                <>
                  <Text style={styles.sectionTitle}>Médicaments génériques</Text>
                  <Text style={styles.sectionSubtitle}>
                    Les génériques contiennent la même substance active que le médicament de référence.
                  </Text>
                  {details.generics.map((generic, index) => (
                    <View key={index} style={styles.itemCard}>
                      <Text style={styles.itemName}>{generic.name}</Text>
                      {generic.laboratory && (
                        <Text style={styles.itemLab}>Laboratoire: {generic.laboratory}</Text>
                      )}
                    </View>
                  ))}
                </>
              ) : (
                <View style={styles.emptyState}>
                  <Users size={48} color="#8E8EA0" strokeWidth={1.5} />
                  <Text style={styles.emptyText}>Aucun générique disponible</Text>
                  <Text style={styles.emptyHint}>
                    Aucun médicament générique n'est référencé pour ce produit.
                  </Text>
                </View>
              )}
            </View>
          )}

          {activeTab === 'alternatives' && (
            <View>
              {details.alternatives.length > 0 ? (
                <>
                  <Text style={styles.sectionTitle}>Alternatives thérapeutiques</Text>
                  <Text style={styles.sectionSubtitle}>
                    Médicaments avec la même substance active ou un effet similaire.
                  </Text>
                  {details.alternatives.map((alt, index) => (
                    <View key={index} style={styles.itemCard}>
                      <Text style={styles.itemName}>{alt.name}</Text>
                      {alt.laboratory && (
                        <Text style={styles.itemLab}>Laboratoire: {alt.laboratory}</Text>
                      )}
                      {alt.reason && (
                        <View style={styles.reasonTag}>
                          <Text style={styles.reasonText}>{alt.reason}</Text>
                        </View>
                      )}
                    </View>
                  ))}
                </>
              ) : (
                <View style={styles.emptyState}>
                  <Lightbulb size={48} color="#8E8EA0" strokeWidth={1.5} />
                  <Text style={styles.emptyText}>Aucune alternative trouvée</Text>
                  <Text style={styles.emptyHint}>
                    Aucune alternative thérapeutique n'est actuellement référencée.
                  </Text>
                </View>
              )}
            </View>
          )}
        </View>

        {/* Bouton d'ajout */}
        <TouchableOpacity style={styles.addButton} onPress={handleAddToTreatments}>
          <Text style={styles.addButtonText}>Ajouter à mes prises</Text>
        </TouchableOpacity>

        <View style={{height: 40}} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0D0D1F',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
  },
  headerTitle: {
    flex: 1,
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
    textAlign: 'center',
    marginHorizontal: 10,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  mainCard: {
    backgroundColor: '#1A1A2E',
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    marginBottom: 24,
  },
  pillIconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#5E5CE620',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  medicationName: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: 8,
  },
  activeSubstance: {
    fontSize: 16,
    color: '#8E8EA0',
    marginBottom: 4,
    textAlign: 'center',
  },
  laboratory: {
    fontSize: 14,
    color: '#8E8EA0',
    marginBottom: 4,
  },
  form: {
    fontSize: 14,
    color: '#5E5CE6',
    marginBottom: 4,
  },
  atcCode: {
    fontSize: 13,
    color: '#8E8EA0',
    fontFamily: 'monospace',
  },
  tabs: {
    flexDirection: 'row',
    backgroundColor: '#1A1A2E',
    borderRadius: 12,
    padding: 4,
    marginBottom: 20,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 8,
    gap: 6,
  },
  tabActive: {
    backgroundColor: '#5E5CE620',
  },
  tabText: {
    fontSize: 12,
    color: '#8E8EA0',
    fontWeight: '500',
  },
  tabTextActive: {
    color: '#5E5CE6',
    fontWeight: '600',
  },
  tabContent: {
    minHeight: 200,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  sectionSubtitle: {
    fontSize: 14,
    color: '#8E8EA0',
    marginBottom: 16,
    lineHeight: 20,
  },
  noticeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: '#5E5CE620',
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
  },
  noticeButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#5E5CE6',
  },
  noticeHint: {
    fontSize: 13,
    color: '#8E8EA0',
    marginLeft: 4,
  },
  emptyState: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyHint: {
    fontSize: 14,
    color: '#8E8EA0',
    textAlign: 'center',
    paddingHorizontal: 20,
    lineHeight: 20,
  },
  itemCard: {
    backgroundColor: '#1A1A2E',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  itemName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 6,
  },
  itemLab: {
    fontSize: 14,
    color: '#8E8EA0',
    marginBottom: 4,
  },
  reasonTag: {
    backgroundColor: '#5E5CE620',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    alignSelf: 'flex-start',
    marginTop: 8,
  },
  reasonText: {
    fontSize: 13,
    color: '#5E5CE6',
    fontWeight: '500',
  },
  addButton: {
    backgroundColor: '#5E5CE6',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 24,
  },
  addButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: '#0D0D1F',
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#8E8EA0',
    marginTop: 16,
  },
  errorContainer: {
    flex: 1,
    backgroundColor: '#0D0D1F',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  errorText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FF4444',
    marginBottom: 20,
  },
  backButton: {
    backgroundColor: '#1A1A2E',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  backButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#5E5CE6',
  },
});
