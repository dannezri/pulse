/**
 * MedicationCard - Card premium avec analyse détaillée du médicament
 * Design moderne avec gradients, glassmorphism et micro-interactions
 */

import React, { useState } from 'react';
import { View, Text, StyleSheet, Pressable, Animated, Modal, TouchableOpacity, Alert, Platform } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import DateTimePicker from '@react-native-community/datetimepicker';
import { 
  Pill, 
  Trash2, 
  Clock, 
  Calendar, 
  Repeat, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  ChevronDown,
  ChevronUp,
  Activity,
  Zap,
  AlertCircle,
  Info,
  CheckCircle,
  StopCircle,
  X,
  Edit3,
  MoreVertical,
} from 'lucide-react-native';
import { Medication } from '../hooks/useMedications';
import { MedicationImpact } from '../hooks/useMedicationImpacts';
import { MedicationAnalysisItem } from '../hooks/useMedicationAnalysis';
import { useMarkAsTaken } from '../hooks/useMedicationHistory';
import { useStopMedication } from '../hooks/useStopMedication';
import { useUpdateMedicationDosage } from '../hooks/useUpdateMedicationDosage';
import { PressableScale } from './PressableScale';
import { HourlyEffectChart } from './HourlyEffectChart';
import { EditDosageModal } from './EditDosageModal';

interface MedicationCardProps {
  medication: Medication;
  impact?: MedicationImpact | null;
  analysis?: MedicationAnalysisItem | null;
  onDelete?: (id: string) => void;
  showImpact?: boolean;
}

// Helper pour formater l'affichage des fractions de comprimés
const formatPillCount = (count: number): string => {
  if (count === 0.25) return '¼';
  if (count === 0.5) return '½';
  if (count === 0.75) return '¾';
  if (count === 1.5) return '1½';
  if (count === 2.5) return '2½';
  return count.toString();
};

export function MedicationCard({ 
  medication, 
  impact,
  analysis,
  onDelete,
  showImpact = true,
}: MedicationCardProps) {
  const [expanded, setExpanded] = useState(false);
  const { markAsTaken, isLoading: isMarkingAsTaken } = useMarkAsTaken();
  const { stopMedication, isLoading: isStoppingMedication } = useStopMedication();
  const { updateDosage, isLoading: isUpdatingDosage } = useUpdateMedicationDosage();
  const [markedToday, setMarkedToday] = useState(false);
  const [showStopModal, setShowStopModal] = useState(false);
  const [showDosageModal, setShowDosageModal] = useState(false);
  const [showActionsMenu, setShowActionsMenu] = useState(false);
  const [endDate, setEndDate] = useState(new Date());
  const [showDatePicker, setShowDatePicker] = useState(false);

  const formatDate = (isoDate: string) => {
    const date = new Date(isoDate);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffDays === 0) return "Aujourd'hui";
    if (diffDays === 1) return 'Hier';
    if (diffDays < 7) return `Il y a ${diffDays}j`;
    if (diffDays < 30) return `Il y a ${Math.floor(diffDays / 7)} semaines`;
    return `Il y a ${Math.floor(diffDays / 30)} mois`;
  };

  const getDaysSinceStart = () => {
    const start = new Date(medication.takenAt);
    const now = new Date();
    return Math.floor((now.getTime() - start.getTime()) / 86400000);
  };

  const getImpactAnalysis = () => {
    if (!impact) return null;

    const daysSince = getDaysSinceStart();
    const isAcutePhase = daysSince < 7;
    const isChronicPhase = daysSince >= 30;

    return {
      phase: isAcutePhase ? 'acute' : isChronicPhase ? 'chronic' : 'adaptation',
      phaseLabel: isAcutePhase ? 'Phase aiguë' : isChronicPhase ? 'Phase chronique' : 'Phase d\'adaptation',
      phaseDescription: isAcutePhase 
        ? 'Les premiers jours montrent souvent les effets les plus marqués'
        : isChronicPhase
        ? 'Votre corps s\'est adapté au traitement, l\'effet est stabilisé'
        : 'Votre corps s\'adapte progressivement au traitement',
      daysSince,
    };
  };

  const phaseAnalysis = getImpactAnalysis();

  // Couleurs selon l'impact
  const getImpactColors = () => {
    if (!impact) return {
      gradient: ['#1A1A2E', '#1C1C1E'],
      border: '#2C2C2E',
      text: '#8E8E93',
      icon: '#8E8E93',
    };

    switch (impact.status) {
      case 'positive':
        return {
          gradient: ['#1B4332', '#1C1C1E'],
          border: 'rgba(52, 199, 89, 0.4)',
          text: '#34C759',
          icon: '#34C759',
        };
      case 'negative':
        return {
          gradient: ['#4C1D1D', '#1C1C1E'],
          border: 'rgba(255, 59, 48, 0.4)',
          text: '#FF3B30',
          icon: '#FF3B30',
        };
      default:
        return {
          gradient: ['#1A1A2E', '#1C1C1E'],
          border: '#2C2C2E',
          text: '#8E8E93',
          icon: '#8E8E93',
        };
    }
  };

  const colors = getImpactColors();

  const handleDelete = () => {
    if (onDelete) {
      onDelete(medication.id);
    }
  };

  const handleMarkAsTaken = async () => {
    if (markedToday || isMarkingAsTaken) return;
    
    try {
      const scheduledTime = medication.intakeTimes?.[0]; // Premier horaire de prise
      await markAsTaken(medication.id, scheduledTime);
      setMarkedToday(true);
      
      // Réinitialiser après 2 secondes
      setTimeout(() => setMarkedToday(false), 2000);
    } catch (error) {
      console.error('[MedicationCard] Error marking as taken:', error);
    }
  };

  const handleStopMedication = async () => {
    try {
      await stopMedication({
        medicationId: medication.id,
        endDate: endDate.toISOString(),
      });
      setShowStopModal(false);
      Alert.alert('✅ Traitement terminé', `Le traitement "${medication.name}" a été arrêté le ${endDate.toLocaleDateString('fr-FR')}`);
    } catch (error: any) {
      Alert.alert('❌ Erreur', error.message || 'Impossible de terminer le traitement');
    }
  };

  const openDosageModal = () => {
    setShowDosageModal(true);
  };

  const handleUpdateDosage = async (params: {
    medicationId: string;
    newDosage: string;
    newDosageUnit: string;
    newPillsPerIntake: number;
    effectiveDate: string;
    notes?: string;
  }) => {
    try {
      await updateDosage(params);
    } catch (error: any) {
      throw error;
    }
  };

  const openStopModal = () => {
    setEndDate(new Date());
    setShowStopModal(true);
  };

  return (
    <View style={styles.container}>
      {/* Overlay pour fermer le menu quand on clique en dehors */}
      {showActionsMenu && (
        <Pressable
          style={styles.menuOverlay}
          onPress={() => setShowActionsMenu(false)}
        />
      )}
      
      <LinearGradient
        colors={colors.gradient}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={[styles.card, { borderColor: colors.border }]}
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.iconContainer}>
            <LinearGradient
              colors={['rgba(94, 92, 230, 0.2)', 'rgba(94, 92, 230, 0.05)']}
              style={styles.iconGradient}
            >
              <Pill size={22} color="#5E5CE6" strokeWidth={2.5} />
            </LinearGradient>
          </View>

          <View style={styles.headerInfo}>
            <View style={styles.nameRow}>
              <Text style={styles.medicationName}>{medication.name}</Text>
              {medication.isRecurring !== undefined && (
                <View style={[
                  styles.typeBadge,
                  medication.isRecurring ? styles.typeBadgeRecurring : styles.typeBadgePonctuel
                ]}>
                  {medication.isRecurring ? (
                    <Repeat size={10} color="#5E5CE6" />
                  ) : (
                    <Calendar size={10} color="#FF9500" />
                  )}
                  <Text style={[
                    styles.typeBadgeText,
                    medication.isRecurring ? styles.typeBadgeTextRecurring : styles.typeBadgeTextPonctuel
                  ]}>
                    {medication.isRecurring ? 'Récurrent' : 'Ponctuel'}
                  </Text>
                </View>
              )}
            </View>

            {(medication.dosage || medication.pillsPerIntake) && (
              <View style={styles.dosageRow}>
                <Text style={styles.dosageText}>
                  {medication.pillsPerIntake 
                    ? `${formatPillCount(medication.pillsPerIntake)} × ` 
                    : ''}{medication.dosage || 'Dosage non spécifié'} {medication.dosage ? medication.unit : ''}
                </Text>
                {medication.intakeTimes && medication.intakeTimes.length > 0 && (
                  <Text style={styles.frequencyText}>
                    • {medication.dailyFrequency || medication.intakeTimes.length}x/jour
                  </Text>
                )}
              </View>
            )}
          </View>

          {onDelete && (
            <View style={styles.actionButtons}>
              <PressableScale 
                onPress={() => setShowActionsMenu(!showActionsMenu)} 
                style={styles.menuButton}
              >
                <MoreVertical size={20} color="#FFFFFF" strokeWidth={2} />
              </PressableScale>
              
              {/* Menu Dropdown */}
              {showActionsMenu && (
                <View style={styles.actionsMenu}>
                  <TouchableOpacity
                    style={styles.menuItem}
                    onPress={() => {
                      setShowActionsMenu(false);
                      openDosageModal();
                    }}
                    activeOpacity={0.7}
                  >
                    <Edit3 size={18} color="#5E5CE6" strokeWidth={2} />
                    <Text style={styles.menuItemText}>Modifier la posologie</Text>
                  </TouchableOpacity>
                  
                  <View style={styles.menuDivider} />
                  
                  <TouchableOpacity
                    style={styles.menuItem}
                    onPress={() => {
                      setShowActionsMenu(false);
                      openStopModal();
                    }}
                    activeOpacity={0.7}
                  >
                    <StopCircle size={18} color="#FF9500" strokeWidth={2} />
                    <Text style={styles.menuItemText}>Arrêter le traitement</Text>
                  </TouchableOpacity>
                  
                  <View style={styles.menuDivider} />
                  
                  <TouchableOpacity
                    style={[styles.menuItem, styles.menuItemDanger]}
                    onPress={() => {
                      setShowActionsMenu(false);
                      handleDelete();
                    }}
                    activeOpacity={0.7}
                  >
                    <Trash2 size={18} color="#FF3B30" strokeWidth={2} />
                    <Text style={[styles.menuItemText, styles.menuItemTextDanger]}>
                      Supprimer
                    </Text>
                  </TouchableOpacity>
                </View>
              )}
            </View>
          )}
        </View>

        {/* Impact Section - REDESIGNED */}
        {showImpact && impact && (
          <View style={styles.impactSection}>
            <LinearGradient
              colors={
                impact.status === 'positive' 
                  ? ['rgba(52, 199, 89, 0.2)', 'rgba(52, 199, 89, 0.08)']
                  : impact.status === 'negative'
                  ? ['rgba(255, 59, 48, 0.2)', 'rgba(255, 59, 48, 0.08)']
                  : ['rgba(142, 142, 147, 0.2)', 'rgba(142, 142, 147, 0.08)']
              }
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={styles.impactGradient}
            >
              {/* Big Impact Value - Hero */}
              <View style={styles.impactHero}>
                <View style={styles.impactIconBadge}>
                  {impact.status === 'positive' && <TrendingUp size={28} color={colors.text} strokeWidth={3} />}
                  {impact.status === 'negative' && <TrendingDown size={28} color={colors.text} strokeWidth={3} />}
                  {impact.status === 'neutral' && <Activity size={28} color={colors.text} strokeWidth={3} />}
                </View>
                <View style={styles.impactHeroContent}>
                  <Text style={styles.impactHeroLabel}>Impact sur l'énergie</Text>
                  <Text style={[styles.impactHeroValue, { color: colors.text }]}>
                    {impact.impactText}
                  </Text>
                </View>
              </View>

              {/* Phase Badge */}
              {phaseAnalysis && (
                <View style={styles.phaseBadge}>
                  <Zap size={16} color="#FFB800" strokeWidth={2.5} />
                  <View style={styles.phaseBadgeContent}>
                    <Text style={styles.phaseBadgeLabel}>{phaseAnalysis.phaseLabel}</Text>
                    <Text style={styles.phaseBadgeDays}>Jour {phaseAnalysis.daysSince}</Text>
                  </View>
                </View>
              )}

              {/* Description */}
              {impact.description && (
                <Text style={styles.impactDescription}>
                  {impact.description}
                </Text>
              )}

              {/* Progress Bar - Visual representation */}
              {phaseAnalysis && (
                <View style={styles.progressSection}>
                  <View style={styles.progressBar}>
                    <View 
                      style={[
                        styles.progressFill,
                        {
                          width: `${Math.min((phaseAnalysis.daysSince / 30) * 100, 100)}%`,
                          backgroundColor: colors.text,
                        }
                      ]}
                    />
                  </View>
                  <Text style={styles.progressLabel}>
                    {phaseAnalysis.phaseDescription}
                  </Text>
                </View>
              )}
            </LinearGradient>
          </View>
        )}

        {/* Intake Times */}
        {medication.isRecurring !== false && medication.intakeTimes && medication.intakeTimes.length > 0 && (
          <View style={styles.intakeTimesSection}>
            <View style={styles.intakeTimesHeader}>
              <Clock size={14} color="#8E8E93" strokeWidth={2} />
              <Text style={styles.intakeTimesLabel}>Heures de prise</Text>
            </View>
            <View style={styles.timeChips}>
              {medication.intakeTimes.map((time, idx) => (
                <View key={idx} style={styles.timeChip}>
                  <Text style={styles.timeChipText}>{time}</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Analyse Détaillée Expandable */}
        <Pressable 
          onPress={() => setExpanded(!expanded)}
          style={styles.expandButton}
        >
          <View style={styles.expandButtonContent}>
            <Text style={styles.expandButtonText}>
              {expanded ? 'Moins de détails' : 'Analyse complète'}
            </Text>
            {expanded ? (
              <ChevronUp size={16} color="#5E5CE6" strokeWidth={2.5} />
            ) : (
              <ChevronDown size={16} color="#5E5CE6" strokeWidth={2.5} />
            )}
          </View>
        </Pressable>

        {/* Expanded Analysis */}
        {expanded && (
          <View style={styles.expandedSection}>
            {/* Analyse Gemini */}
            {analysis && (
              <>
                {/* Intro Explicative */}
                <View style={[styles.expandedCard, styles.geminiCard]}>
                  <View style={styles.expandedCardHeader}>
                    <View style={styles.geminiIconBadge}>
                      <Pill size={16} color="#5E5CE6" strokeWidth={2.5} />
                    </View>
                    <Text style={styles.expandedCardTitle}>Fonction du médicament</Text>
                  </View>
                  <View style={styles.expandedCardContent}>
                    <Text style={styles.geminiText}>{analysis.intro_explicative}</Text>
                  </View>
                </View>

                {/* Impact sur le Corps */}
                <View style={[styles.expandedCard, styles.geminiCard]}>
                  <View style={styles.expandedCardHeader}>
                    <View style={styles.geminiIconBadge}>
                      <Activity size={16} color="#5E5CE6" strokeWidth={2.5} />
                    </View>
                    <Text style={styles.expandedCardTitle}>Impact sur le corps</Text>
                  </View>
                  <View style={styles.expandedCardContent}>
                    <Text style={styles.geminiText}>{analysis.impact_corps}</Text>
                  </View>
                </View>

                {/* Impact sur la Journée */}
                <View style={[styles.expandedCard, styles.geminiCard]}>
                  <View style={styles.expandedCardHeader}>
                    <View style={styles.geminiIconBadge}>
                      <Clock size={16} color="#5E5CE6" strokeWidth={2.5} />
                    </View>
                    <Text style={styles.expandedCardTitle}>Ressenti quotidien</Text>
                  </View>
                  <View style={styles.expandedCardContent}>
                    <Text style={styles.geminiText}>{analysis.impact_journee}</Text>
                  </View>
                </View>

                {/* Observation */}
                <View style={[styles.expandedCard, styles.geminiCard, styles.observationCard]}>
                  <View style={styles.expandedCardHeader}>
                    <View style={[styles.geminiIconBadge, styles.observationIconBadge]}>
                      <AlertCircle size={16} color="#FFB800" strokeWidth={2.5} />
                    </View>
                    <Text style={styles.expandedCardTitle}>À surveiller</Text>
                  </View>
                  <View style={styles.expandedCardContent}>
                    <Text style={[styles.geminiText, styles.observationText]}>{analysis.observation}</Text>
                  </View>
                </View>

                {/* Graphique des effets horaires */}
                {analysis.effets_horaires && analysis.effets_horaires.length > 0 && (
                  <View style={[styles.expandedCard, styles.geminiCard]}>
                    <View style={styles.expandedCardHeader}>
                      <View style={styles.geminiIconBadge}>
                        <Activity size={16} color="#5E5CE6" strokeWidth={2.5} />
                      </View>
                      <Text style={styles.expandedCardTitle}>Profil d'efficacité sur 24h</Text>
                    </View>
                    <View style={styles.expandedCardContent}>
                      <Text style={styles.geminiText}>
                        Visualisez comment le médicament agit tout au long de la journée
                      </Text>
                      <HourlyEffectChart 
                        data={analysis.effets_horaires}
                        intakeTimes={medication.intakeTimes}
                        labelConcentration={analysis.label_concentration}
                        labelEfficacite={analysis.label_efficacite}
                        labelEffetsSecondaires={analysis.label_effets_secondaires}
                      />
                    </View>
                  </View>
                )}
              </>
            )}

            {/* Pharmacocinétique */}
            <View style={styles.expandedCard}>
              <View style={styles.expandedCardHeader}>
                <Zap size={16} color="#FFB800" strokeWidth={2.5} />
                <Text style={styles.expandedCardTitle}>Pharmacocinétique</Text>
              </View>
              <View style={styles.expandedCardContent}>
                {medication.intakeTimes && medication.intakeTimes.length > 0 && (
                  <View style={styles.infoRow}>
                    <Text style={styles.infoLabel}>Pic d'efficacité:</Text>
                    <Text style={styles.infoValue}>
                      ~2-3h après la prise
                    </Text>
                  </View>
                )}
                <View style={styles.infoRow}>
                  <Text style={styles.infoLabel}>Demi-vie:</Text>
                  <Text style={styles.infoValue}>Variable selon le composé</Text>
                </View>
                {medication.pillsPerIntake && medication.pillsPerIntake !== 1 && (
                  <View style={styles.infoRow}>
                    <Text style={styles.infoLabel}>Dosage ajusté:</Text>
                    <Text style={styles.infoValue}>
                      {(parseFloat(medication.dosage || '0') * medication.pillsPerIntake).toFixed(1)} {medication.unit}
                    </Text>
                  </View>
                )}
              </View>
            </View>

            {/* Durée du traitement */}
            <View style={styles.expandedCard}>
              <View style={styles.expandedCardHeader}>
                <Calendar size={16} color="#5E5CE6" strokeWidth={2.5} />
                <Text style={styles.expandedCardTitle}>Durée du traitement</Text>
              </View>
              <View style={styles.expandedCardContent}>
                <View style={styles.infoRow}>
                  <Text style={styles.infoLabel}>Début:</Text>
                  <Text style={styles.infoValue}>{formatDate(medication.takenAt)}</Text>
                </View>
                <View style={styles.infoRow}>
                  <Text style={styles.infoLabel}>Durée:</Text>
                  <Text style={styles.infoValue}>{getDaysSinceStart()} jours</Text>
                </View>
                {phaseAnalysis && (
                  <View style={styles.infoRow}>
                    <Text style={styles.infoLabel}>Phase:</Text>
                    <Text style={[styles.infoValue, { color: '#5E5CE6' }]}>
                      {phaseAnalysis.phaseLabel}
                    </Text>
                  </View>
                )}
              </View>
            </View>

            {/* Recommandations - ENHANCED */}
            {impact && Math.abs(impact.impact) > 5 && (
              <View style={[styles.expandedCard, styles.alertCard]}>
                <LinearGradient
                  colors={
                    impact.status === 'negative'
                      ? ['rgba(255, 59, 48, 0.15)', 'rgba(255, 59, 48, 0.05)']
                      : ['rgba(52, 199, 89, 0.15)', 'rgba(52, 199, 89, 0.05)']
                  }
                  style={styles.alertGradient}
                >
                  <View style={styles.expandedCardHeader}>
                    <View style={[
                      styles.alertIconBadge,
                      impact.status === 'negative' 
                        ? styles.alertIconBadgeNegative 
                        : styles.alertIconBadgePositive
                    ]}>
                      <AlertCircle 
                        size={20} 
                        color={impact.status === 'negative' ? '#FF3B30' : '#34C759'} 
                        strokeWidth={2.5} 
                      />
                    </View>
                    <Text style={styles.expandedCardTitle}>
                      {impact.status === 'negative' ? '⚠️ Attention' : '✅ Excellent'}
                    </Text>
                  </View>
                  <View style={styles.expandedCardContent}>
                    <Text style={[
                      styles.recommendationText,
                      impact.status === 'negative' 
                        ? styles.recommendationTextNegative 
                        : styles.recommendationTextPositive
                    ]}>
                      {impact.status === 'negative' 
                        ? `Impact négatif important (${impact.impactText}). Consultez votre médecin si cela affecte votre quotidien.`
                        : `Impact positif marqué (${impact.impactText}). Le traitement semble bien adapté à votre profil.`
                      }
                    </Text>
                  </View>
                </LinearGradient>
              </View>
            )}

            {/* Notes */}
            {medication.notes && (
              <View style={styles.expandedCard}>
                <View style={styles.expandedCardHeader}>
                  <Info size={16} color="#8E8E93" strokeWidth={2.5} />
                  <Text style={styles.expandedCardTitle}>Notes</Text>
                </View>
                <View style={styles.expandedCardContent}>
                  <Text style={styles.notesText}>{medication.notes}</Text>
                </View>
              </View>
            )}
          </View>
        )}

        {/* Footer */}
        <View style={styles.footer}>
          <View style={styles.footerItem}>
            <Calendar size={12} color="#6E6E73" strokeWidth={2} />
            <Text style={styles.footerText}>
              Début: {formatDate(medication.takenAt)}
            </Text>
          </View>
          {medication.intakeTimes && medication.intakeTimes.length > 0 && (
            <View style={styles.footerItem}>
              <Clock size={12} color="#5E5CE6" strokeWidth={2} />
              <Text style={[styles.footerText, { color: '#5E5CE6' }]}>
                Prochaine: {medication.intakeTimes[0]}
              </Text>
            </View>
          )}
        </View>
      </LinearGradient>

      {/* Modal pour terminer le traitement */}
      <Modal
        visible={showStopModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowStopModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <View style={styles.modalTitleRow}>
                <StopCircle size={24} color="#FF9500" strokeWidth={2} />
                <Text style={styles.modalTitle}>Terminer le traitement</Text>
              </View>
              <TouchableOpacity onPress={() => setShowStopModal(false)}>
                <X size={24} color="#8E8E93" />
              </TouchableOpacity>
            </View>

            <Text style={styles.modalSubtitle}>
              Vous souhaitez arrêter le traitement "{medication.name}"
            </Text>

            <View style={styles.dateSection}>
              <Text style={styles.dateLabel}>Date de fin du traitement</Text>
              <TouchableOpacity
                style={styles.dateButton}
                onPress={() => setShowDatePicker(true)}
              >
                <Calendar size={20} color="#5E5CE6" />
                <Text style={styles.dateButtonText}>
                  {endDate.toLocaleDateString('fr-FR', {
                    day: '2-digit',
                    month: 'long',
                    year: 'numeric'
                  })}
                </Text>
              </TouchableOpacity>
            </View>

            {showDatePicker && (
              <DateTimePicker
                value={endDate}
                mode="date"
                display={Platform.OS === 'ios' ? 'inline' : 'default'}
                onChange={(event, selectedDate) => {
                  setShowDatePicker(Platform.OS === 'ios');
                  if (selectedDate) {
                    setEndDate(selectedDate);
                  }
                }}
                maximumDate={new Date()}
              />
            )}

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={() => setShowStopModal(false)}
              >
                <Text style={styles.cancelButtonText}>Annuler</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.confirmButton, isStoppingMedication && styles.confirmButtonDisabled]}
                onPress={handleStopMedication}
                disabled={isStoppingMedication}
              >
                <StopCircle size={18} color="#FFFFFF" strokeWidth={2} />
                <Text style={styles.confirmButtonText}>
                  {isStoppingMedication ? 'Enregistrement...' : 'Terminer'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Modal Modifier la posologie */}
      <EditDosageModal
        visible={showDosageModal}
        medication={medication}
        onClose={() => setShowDosageModal(false)}
        onSave={handleUpdateDosage}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
    position: 'relative',
  },
  menuOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 999,
  },
  card: {
    borderRadius: 24,
    borderWidth: 1.5,
    padding: 20,
    overflow: 'hidden',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  iconContainer: {
    marginRight: 14,
  },
  iconGradient: {
    width: 48,
    height: 48,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerInfo: {
    flex: 1,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flexWrap: 'wrap',
    marginBottom: 6,
  },
  medicationName: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 0.2,
  },
  typeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  typeBadgeRecurring: {
    backgroundColor: 'rgba(94, 92, 230, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(94, 92, 230, 0.3)',
  },
  typeBadgePonctuel: {
    backgroundColor: 'rgba(255, 149, 0, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(255, 149, 0, 0.3)',
  },
  typeBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  typeBadgeTextRecurring: {
    color: '#5E5CE6',
  },
  typeBadgeTextPonctuel: {
    color: '#FF9500',
  },
  dosageRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  dosageText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#5E5CE6',
  },
  frequencyText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#8E8E93',
  },
  menuButton: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionsMenu: {
    position: 'absolute',
    top: 48,
    right: 0,
    backgroundColor: 'rgba(26, 26, 46, 0.98)',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
    minWidth: 220,
    paddingVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 8,
    zIndex: 1000,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 14,
    paddingHorizontal: 16,
  },
  menuItemText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
    flex: 1,
  },
  menuItemDanger: {
    // Style spécifique pour l'action dangereuse
  },
  menuItemTextDanger: {
    color: '#FF3B30',
  },
  menuDivider: {
    height: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    marginHorizontal: 12,
  },
  impactSection: {
    marginBottom: 18,
  },
  impactGradient: {
    borderRadius: 20,
    padding: 20,
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.15)',
  },
  impactHero: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    marginBottom: 16,
  },
  impactIconBadge: {
    width: 64,
    height: 64,
    borderRadius: 18,
    backgroundColor: 'rgba(0, 0, 0, 0.25)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  impactHeroContent: {
    flex: 1,
  },
  impactHeroLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
    opacity: 0.7,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 4,
  },
  impactHeroValue: {
    fontSize: 36,
    fontWeight: '900',
    letterSpacing: -1,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  phaseBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: 'rgba(255, 184, 0, 0.15)',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 14,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: 'rgba(255, 184, 0, 0.3)',
  },
  phaseBadgeContent: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  phaseBadgeLabel: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFB800',
    letterSpacing: 0.3,
  },
  phaseBadgeDays: {
    fontSize: 12,
    fontWeight: '800',
    color: '#FFB800',
    opacity: 0.8,
  },
  impactDescription: {
    fontSize: 14,
    color: '#FFFFFF',
    opacity: 0.85,
    lineHeight: 20,
    marginBottom: 14,
  },
  progressSection: {
    gap: 8,
  },
  progressBar: {
    height: 6,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 3,
  },
  progressLabel: {
    fontSize: 11,
    color: '#FFFFFF',
    opacity: 0.6,
    fontWeight: '600',
    letterSpacing: 0.3,
  },
  intakeTimesSection: {
    marginBottom: 16,
  },
  intakeTimesHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 10,
  },
  intakeTimesLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#8E8E93',
  },
  timeChips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  timeChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(94, 92, 230, 0.15)',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: 'rgba(94, 92, 230, 0.35)',
    shadowColor: '#5E5CE6',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  timeChipText: {
    fontSize: 15,
    fontWeight: '800',
    color: '#5E5CE6',
    letterSpacing: 0.5,
  },
  expandButton: {
    marginBottom: 16,
  },
  expandButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    paddingHorizontal: 20,
    backgroundColor: 'rgba(94, 92, 230, 0.15)',
    borderRadius: 16,
    borderWidth: 2,
    borderColor: 'rgba(94, 92, 230, 0.3)',
    shadowColor: '#5E5CE6',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 4,
  },
  expandButtonText: {
    fontSize: 14,
    fontWeight: '800',
    color: '#5E5CE6',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  expandedSection: {
    gap: 12,
    marginBottom: 16,
  },
  expandedCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.05)',
  },
  alertCard: {
    padding: 0,
    overflow: 'hidden',
  },
  alertGradient: {
    padding: 14,
    borderRadius: 14,
  },
  alertIconBadge: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 2,
  },
  alertIconBadgeNegative: {
    backgroundColor: 'rgba(255, 59, 48, 0.2)',
  },
  alertIconBadgePositive: {
    backgroundColor: 'rgba(52, 199, 89, 0.2)',
  },
  expandedCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  expandedCardTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 0.2,
  },
  expandedCardContent: {
    gap: 8,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  infoLabel: {
    fontSize: 13,
    fontWeight: '500',
    color: '#8E8E93',
  },
  infoValue: {
    fontSize: 13,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  recommendationText: {
    fontSize: 14,
    lineHeight: 20,
    fontWeight: '500',
  },
  recommendationTextNegative: {
    color: '#FF3B30',
  },
  recommendationTextPositive: {
    color: '#34C759',
  },
  notesText: {
    fontSize: 13,
    color: '#FFFFFF',
    opacity: 0.8,
    lineHeight: 18,
  },
  geminiCard: {
    backgroundColor: 'rgba(94, 92, 230, 0.08)',
    borderColor: 'rgba(94, 92, 230, 0.25)',
  },
  geminiIconBadge: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: 'rgba(94, 92, 230, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 2,
  },
  geminiText: {
    fontSize: 14,
    color: '#FFFFFF',
    lineHeight: 21,
    opacity: 0.9,
  },
  observationCard: {
    backgroundColor: 'rgba(255, 184, 0, 0.08)',
    borderColor: 'rgba(255, 184, 0, 0.3)',
  },
  observationIconBadge: {
    backgroundColor: 'rgba(255, 184, 0, 0.15)',
  },
  observationText: {
    color: '#FFB800',
    opacity: 1,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 14,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.05)',
  },
  footerItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  footerText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6E6E73',
  },
  markAsTakenButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    paddingHorizontal: 20,
    marginBottom: 16,
    backgroundColor: 'rgba(94, 92, 230, 0.15)',
    borderRadius: 16,
    borderWidth: 2,
    borderColor: 'rgba(94, 92, 230, 0.3)',
  },
  markAsTakenButtonActive: {
    backgroundColor: 'rgba(52, 199, 89, 0.15)',
    borderColor: 'rgba(52, 199, 89, 0.4)',
  },
  markAsTakenText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#5E5CE6',
    letterSpacing: 0.3,
  },
  markAsTakenTextActive: {
    color: '#34C759',
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: '#1A1A2E',
    borderRadius: 24,
    padding: 24,
    width: '100%',
    maxWidth: 400,
    borderWidth: 1,
    borderColor: 'rgba(94, 92, 230, 0.3)',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  modalTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  modalSubtitle: {
    fontSize: 15,
    color: '#8E8E93',
    marginBottom: 24,
    lineHeight: 22,
  },
  dateSection: {
    marginBottom: 24,
  },
  dateLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 12,
  },
  dateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: 'rgba(94, 92, 230, 0.1)',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: 'rgba(94, 92, 230, 0.3)',
  },
  dateButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  modalActions: {
    flexDirection: 'row',
    gap: 12,
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 14,
    paddingHorizontal: 20,
    backgroundColor: 'rgba(142, 142, 147, 0.2)',
    borderRadius: 12,
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#8E8E93',
  },
  confirmButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    paddingHorizontal: 20,
    backgroundColor: '#FF9500',
    borderRadius: 12,
  },
  confirmButtonDisabled: {
    opacity: 0.5,
  },
  confirmButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});
