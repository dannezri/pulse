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
import { ChevronLeft, Heart, Plus, X, Info } from 'lucide-react-native';
import { useConditions } from '@/hooks/useConditions';
import { ConditionPicker } from '@/components/ConditionPicker';

export default function HealthConditionsScreen() {
  const [conditionPickerVisible, setConditionPickerVisible] = useState(false);
  const { conditions, loading: loadingConditions, deleteCondition, fetchConditions } = useConditions();

  // Load conditions on mount
  useEffect(() => {
    fetchConditions();
  }, [fetchConditions]);

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
              console.error('[HealthConditions] Erreur suppression condition:', error);
              Alert.alert('Erreur', 'Impossible de supprimer la condition.');
            }
          },
        },
      ]
    );
  };

  const getConditionColor = (index: number) => {
    const colors = [
      { bg: '#FF950020', border: '#FF9500', dot: '#FF9500' },
      { bg: '#5E5CE620', border: '#5E5CE6', dot: '#5E5CE6' },
      { bg: '#34C75920', border: '#34C759', dot: '#34C759' },
      { bg: '#FF6B9D20', border: '#FF6B9D', dot: '#FF6B9D' },
      { bg: '#4ECDC420', border: '#4ECDC4', dot: '#4ECDC4' },
      { bg: '#FFB80020', border: '#FFB800', dot: '#FFB800' },
    ];
    return colors[index % colors.length];
  };

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
        <Text style={styles.headerTitle}>Conditions de Santé</Text>
        <TouchableOpacity 
          style={styles.headerButton}
          onPress={() => setConditionPickerVisible(true)}
        >
          <Plus size={28} color="#FFFFFF" strokeWidth={2.5} />
        </TouchableOpacity>
      </View>

      <ScrollView 
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {/* Info Card */}
        <View style={styles.infoCard}>
          <View style={styles.infoIconContainer}>
            <Heart size={32} color="#FF2D55" strokeWidth={2.5} />
          </View>
          <Text style={styles.infoTitle}>Personnalisez vos conseils</Text>
          <Text style={styles.infoDescription}>
            Renseignez vos conditions de santé pour recevoir des recommandations plus précises et adaptées à votre situation.
          </Text>
          <View style={styles.optionalBadge}>
            <Text style={styles.optionalText}>Facultatif</Text>
          </View>
        </View>

        {/* Stats Overview */}
        {conditions.length > 0 && !loadingConditions && (
          <View style={styles.statsContainer}>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>{conditions.length}</Text>
              <Text style={styles.statLabel}>Condition{conditions.length > 1 ? 's' : ''}</Text>
            </View>
            <View style={styles.statCard}>
              <Heart size={24} color="#FF2D55" strokeWidth={2.5} />
              <Text style={styles.statLabel}>Actives</Text>
            </View>
            <View style={styles.statCard}>
              <Info size={24} color="#7B6CF6" strokeWidth={2.5} />
              <Text style={styles.statLabel}>Suivies</Text>
            </View>
          </View>
        )}

        {/* Conditions List */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Mes Conditions</Text>
            {conditions.length > 0 && !loadingConditions && (
              <Text style={styles.sectionCount}>
                {conditions.length} condition{conditions.length > 1 ? 's' : ''}
              </Text>
            )}
          </View>
          
          {loadingConditions ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#FF2D55" />
              <Text style={styles.loadingText}>Chargement des conditions...</Text>
            </View>
          ) : conditions.length > 0 ? (
            <View style={styles.conditionsGrid}>
              {conditions.map((condition, index) => {
                const colors = getConditionColor(index);
                return (
                  <View 
                    key={condition.id} 
                    style={[
                      styles.conditionCard,
                      { 
                        backgroundColor: colors.bg,
                        borderColor: colors.border,
                      }
                    ]}
                  >
                    <View style={styles.conditionHeader}>
                      <View style={[styles.conditionDot, { backgroundColor: colors.dot }]} />
                      <Text style={styles.conditionTitle} numberOfLines={2}>
                        {condition.display}
                      </Text>
                    </View>
                    
                    {condition.code && (
                      <Text style={styles.conditionCode}>Code: {condition.code}</Text>
                    )}
                    
                    <TouchableOpacity
                      onPress={() => handleDeleteCondition(condition.id, condition.display)}
                      style={styles.deleteButton}
                      hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                    >
                      <X size={18} color="#FFFFFF" strokeWidth={2.5} />
                    </TouchableOpacity>
                  </View>
                );
              })}
            </View>
          ) : (
            <View style={styles.emptyState}>
              <View style={styles.emptyIconContainer}>
                <Heart size={64} color="#FFFFFF40" strokeWidth={2} />
              </View>
              <Text style={styles.emptyTitle}>Aucune condition renseignée</Text>
              <Text style={styles.emptyDescription}>
                Commencez par ajouter vos conditions de santé pour des conseils plus personnalisés et des analyses plus précises.
              </Text>
              <TouchableOpacity
                style={styles.emptyButton}
                onPress={() => setConditionPickerVisible(true)}
                activeOpacity={0.8}
              >
                <Plus size={20} color="#FFFFFF" strokeWidth={2.5} />
                <Text style={styles.emptyButtonText}>Ajouter une condition</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Add Button (when conditions exist) */}
        {conditions.length > 0 && !loadingConditions && (
          <TouchableOpacity
            style={styles.addButton}
            onPress={() => setConditionPickerVisible(true)}
            activeOpacity={0.8}
          >
            <Plus size={20} color="#FFFFFF" strokeWidth={2.5} />
            <Text style={styles.addButtonText}>Ajouter une condition</Text>
          </TouchableOpacity>
        )}

        {/* Why it matters */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Pourquoi c'est important ?</Text>
          
          <View style={styles.whyCard}>
            <View style={styles.whyItem}>
              <View style={styles.whyIcon}>
                <Text style={styles.whyEmoji}>🎯</Text>
              </View>
              <View style={styles.whyContent}>
                <Text style={styles.whyTitle}>Conseils personnalisés</Text>
                <Text style={styles.whyDescription}>
                  Recevez des recommandations adaptées à votre situation de santé
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
                  Des interprétations de vos métriques plus pertinentes
                </Text>
              </View>
            </View>

            <View style={styles.whyDivider} />

            <View style={styles.whyItem}>
              <View style={styles.whyIcon}>
                <Text style={styles.whyEmoji}>🔒</Text>
              </View>
              <View style={styles.whyContent}>
                <Text style={styles.whyTitle}>Confidentialité</Text>
                <Text style={styles.whyDescription}>
                  Vos données restent privées et sécurisées
                </Text>
              </View>
            </View>
          </View>
        </View>

        {/* Privacy Note */}
        <View style={styles.privacyNote}>
          <Text style={styles.privacyText}>
            🔒 Ces informations sont strictement confidentielles et ne sont utilisées que pour personnaliser votre expérience.
          </Text>
        </View>
      </ScrollView>

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
    paddingBottom: 40,
  },
  infoCard: {
    backgroundColor: '#FF2D5520',
    borderRadius: 24,
    padding: 24,
    alignItems: 'center',
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#FF2D5540',
  },
  infoIconContainer: {
    width: 64,
    height: 64,
    backgroundColor: '#FF2D5540',
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
    marginBottom: 16,
  },
  optionalBadge: {
    backgroundColor: '#FFB800',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 6,
  },
  optionalText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#000000',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  statsContainer: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 32,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#1A1A2E',
    borderRadius: 20,
    padding: 20,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#FFFFFF10',
    gap: 8,
  },
  statValue: {
    fontSize: 28,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  statLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF60',
    textAlign: 'center',
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
    letterSpacing: 0.3,
  },
  sectionCount: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF60',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
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
  conditionsGrid: {
    gap: 12,
  },
  conditionCard: {
    borderRadius: 20,
    padding: 20,
    borderWidth: 2,
    position: 'relative',
  },
  conditionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 8,
    paddingRight: 40,
  },
  conditionDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  conditionTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#FFFFFF',
    flex: 1,
    lineHeight: 22,
  },
  conditionCode: {
    fontSize: 13,
    fontWeight: '500',
    color: '#FFFFFF60',
    marginLeft: 22,
  },
  deleteButton: {
    position: 'absolute',
    top: 16,
    right: 16,
    width: 32,
    height: 32,
    backgroundColor: '#FF3B3080',
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyState: {
    backgroundColor: '#1A1A2E',
    borderRadius: 24,
    padding: 48,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#FFFFFF10',
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
    backgroundColor: '#FF2D55',
    borderRadius: 20,
    paddingVertical: 16,
    paddingHorizontal: 32,
    gap: 10,
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
    backgroundColor: '#FF2D55',
    borderRadius: 20,
    paddingVertical: 18,
    gap: 12,
    marginBottom: 32,
  },
  addButtonText: {
    fontSize: 17,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 0.3,
  },
  whyCard: {
    backgroundColor: '#1A1A2E',
    borderRadius: 20,
    padding: 24,
    borderWidth: 1,
    borderColor: '#FFFFFF10',
  },
  whyItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 16,
  },
  whyIcon: {
    width: 48,
    height: 48,
    backgroundColor: '#FFFFFF10',
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
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
  privacyNote: {
    backgroundColor: '#34C75920',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#34C75940',
  },
  privacyText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#34C759',
    lineHeight: 19,
    textAlign: 'center',
  },
});
