import React, { useState, useMemo, useRef } from 'react';
import { View, Text, StyleSheet, SectionList, ActivityIndicator, RefreshControl, TouchableOpacity, Alert, ScrollView } from 'react-native';
import { useMedicationHistoryByDay, DailyIntakeSummary, MedicationIntake, useUpdateMedicationIntake, useDeleteMedicationIntake } from '@/hooks/useMedicationHistory';
import { useManualMedicationSync } from '@/hooks/useMedicationHistorySync';
import { Calendar, CheckCircle, XCircle, Clock, Edit2, Trash2, Award, AlertCircle } from 'lucide-react-native';
import { EditIntakeModal } from './EditIntakeModal';
import { PressableScale } from './PressableScale';

interface TreatmentChange {
  type: 'added' | 'stopped' | 'dosage_changed';
  medicationName: string;
  date: string;
  oldDosage?: string;
  newDosage?: string;
}

interface MonthSection {
  title: string;
  key: string;
  data: DailyIntakeSummary[];
  totalDays: number;
  totalIntakes: number;
  completionRate: number;
  treatmentChanges: TreatmentChange[];
}

// Composant wrapper pour isoler le state du modal et éviter les re-renders du parent
function EditModalWrapper() {
  const [modalState, setModalState] = useState<{ visible: boolean; intake: MedicationIntake | null }>({
    visible: false,
    intake: null,
  });
  const updateIntake = useUpdateMedicationIntake();
  const { refetch } = useMedicationHistoryByDay();

  const handleOpen = React.useCallback((intake: MedicationIntake) => {
    setModalState({ visible: true, intake });
  }, []);

  const handleClose = React.useCallback(() => {
    setModalState({ visible: false, intake: null });
  }, []);

  const handleSave = React.useCallback(async (params: any) => {
    await updateIntake.mutateAsync(params);
    setModalState({ visible: false, intake: null });
    await refetch();
  }, [updateIntake, refetch]);

  // Exposer handleOpen via un contexte ou ref
  React.useEffect(() => {
    (global as any).__editModalOpen = handleOpen;
  }, [handleOpen]);

  return (
    <EditIntakeModal
      visible={modalState.visible}
      intake={modalState.intake}
      onClose={handleClose}
      onSave={handleSave}
    />
  );
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

export function MedicationHistoryTab() {
  const { data: historyByDay, isLoading, error, refetch } = useMedicationHistoryByDay();
  const { syncHistory } = useManualMedicationSync();
  const deleteIntake = useDeleteMedicationIntake();
  const [refreshing, setRefreshing] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);
  const monthNavScrollRef = useRef<ScrollView>(null);

  // Grouper les données par mois
  const historyByMonth = useMemo(() => {
    if (!historyByDay || historyByDay.length === 0) return [];

    const monthsMap = new Map<string, DailyIntakeSummary[]>();

    historyByDay.forEach((day) => {
      const date = new Date(day.date);
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      
      if (!monthsMap.has(monthKey)) {
        monthsMap.set(monthKey, []);
      }
      monthsMap.get(monthKey)!.push(day);
    });

    const sections: MonthSection[] = Array.from(monthsMap.entries()).map(([monthKey, days]) => {
      const [year, month] = monthKey.split('-');
      const monthNames = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'];
      const monthName = monthNames[parseInt(month) - 1];
      
      const totalIntakes = days.reduce((sum, day) => sum + day.totalIntakes, 0);
      const takenIntakes = days.reduce((sum, day) => sum + day.takenCount, 0);
      const completionRate = totalIntakes > 0 ? (takenIntakes / totalIntakes) * 100 : 0;

      // Détecter les variations de traitement dans le mois
      const treatmentChanges: TreatmentChange[] = [];
      const sortedDays = [...days].sort((a, b) => a.date.localeCompare(b.date));
      
      // Suivre les médicaments par jour
      const medicationsByDay = new Map<string, Set<string>>();
      const dosagesByDay = new Map<string, Map<string, string>>();
      const pillsByDay = new Map<string, Map<string, number>>();
      
      sortedDays.forEach((day) => {
        const medications = new Set<string>();
        const dosages = new Map<string, string>();
        const pills = new Map<string, number>();
        
        day.intakes.forEach((intake) => {
          const medName = intake.medication?.medication_name || 'Inconnu';
          medications.add(medName);
          
          // Stocker le dosage (concentration)
          if (intake.medication?.dosage) {
            const dosageStr = `${intake.medication.dosage} ${intake.medication.dosage_unit || ''}`.trim();
            dosages.set(medName, dosageStr);
          }
          
          // Stocker le nombre de comprimés
          pills.set(medName, intake.pills_taken || 1);
        });
        
        medicationsByDay.set(day.date, medications);
        dosagesByDay.set(day.date, dosages);
        pillsByDay.set(day.date, pills);
      });
      
      // Garder trace des médicaments déjà traités pour éviter les doublons
      const processedAdditions = new Set<string>();
      const processedStops = new Set<string>();
      
      // Comparer jour par jour pour détecter les changements
      for (let i = 1; i < sortedDays.length; i++) {
        const prevDay = sortedDays[i - 1];
        const currentDay = sortedDays[i];
        
        const prevMeds = medicationsByDay.get(prevDay.date) || new Set();
        const currentMeds = medicationsByDay.get(currentDay.date) || new Set();
        
        const prevDosages = dosagesByDay.get(prevDay.date) || new Map();
        const currentDosages = dosagesByDay.get(currentDay.date) || new Map();
        
        const prevPills = pillsByDay.get(prevDay.date) || new Map();
        const currentPills = pillsByDay.get(currentDay.date) || new Map();
        
        // Détecter les nouveaux médicaments
        currentMeds.forEach((med) => {
          if (!prevMeds.has(med) && !processedAdditions.has(med)) {
            treatmentChanges.push({
              type: 'added',
              medicationName: med,
              date: currentDay.date,
            });
            processedAdditions.add(med);
          } else {
            // Vérifier les changements de nombre de comprimés
            const prevPillCount = prevPills.get(med);
            const currentPillCount = currentPills.get(med);
            
            if (prevPillCount && currentPillCount && prevPillCount !== currentPillCount) {
              const prevDosage = prevDosages.get(med);
              const pillUnit = prevPillCount === 1 ? 'comprimé' : 'comprimés';
              const currentPillUnit = currentPillCount === 1 ? 'comprimé' : 'comprimés';
              
              treatmentChanges.push({
                type: 'dosage_changed',
                medicationName: med,
                date: currentDay.date,
                oldDosage: `${prevPillCount} ${pillUnit}${prevDosage ? ` (${prevDosage})` : ''}`,
                newDosage: `${currentPillCount} ${currentPillUnit}${prevDosage ? ` (${prevDosage})` : ''}`,
              });
            }
          }
        });
        
        // Détecter les médicaments arrêtés (une seule fois par médicament)
        prevMeds.forEach((med) => {
          if (!currentMeds.has(med) && !processedStops.has(med)) {
            treatmentChanges.push({
              type: 'stopped',
              medicationName: med,
              date: currentDay.date,
            });
            processedStops.add(med);
          }
        });
      }

      return {
        title: `${monthName} ${year}`,
        key: monthKey,
        data: days,
        totalDays: days.length,
        totalIntakes,
        completionRate,
        treatmentChanges,
      };
    });

    return sections;
  }, [historyByDay]);

  // Initialiser avec le premier mois par défaut
  React.useEffect(() => {
    if (historyByMonth.length > 0 && !selectedMonth) {
      setSelectedMonth(historyByMonth[0].key);
    }
  }, [historyByMonth, selectedMonth]);


  const selectMonth = (monthKey: string) => {
    setSelectedMonth(monthKey);
    
    // Scroller la navbar pour centrer le bouton sélectionné
    const sectionIndex = historyByMonth.findIndex(section => section.key === monthKey);
    if (monthNavScrollRef.current && sectionIndex !== -1) {
      const buttonWidth = 120;
      const scrollX = (sectionIndex * buttonWidth) - (buttonWidth * 1.5);
      monthNavScrollRef.current.scrollTo({
        x: Math.max(0, scrollX),
        animated: true,
      });
    }
  };

  // Filtrer les données pour n'afficher que le mois sélectionné
  const filteredHistoryByMonth = React.useMemo(() => {
    if (!selectedMonth || historyByMonth.length === 0) {
      return historyByMonth;
    }
    return historyByMonth.filter(section => section.key === selectedMonth);
  }, [historyByMonth, selectedMonth]);


  const onRefresh = async () => {
    setRefreshing(true);
    try {
      // Synchroniser l'historique
      await syncHistory();
      // Recharger les données
      await refetch();
    } catch (err) {
      console.error('[MedicationHistoryTab] Refresh error:', err);
    } finally {
      setRefreshing(false);
    }
  };

  const handleEdit = React.useCallback((intake: MedicationIntake) => {
    // Utiliser la fonction globale pour éviter le re-render du parent
    if ((global as any).__editModalOpen) {
      (global as any).__editModalOpen(intake);
    }
  }, []);

  const handleDelete = React.useCallback((intake: MedicationIntake) => {
    Alert.alert(
      'Supprimer la prise',
      `Voulez-vous vraiment supprimer cette prise de ${intake.medication?.medication_name} ?`,
      [
        { text: 'Annuler', style: 'cancel' },
        {
          text: 'Supprimer',
          style: 'destructive',
          onPress: async () => {
            try {
              await deleteIntake.mutateAsync(intake.id);
              Alert.alert('✅ Succès', 'La prise a été supprimée');
            } catch (error: any) {
              Alert.alert('❌ Erreur', error.message || 'Impossible de supprimer la prise');
            }
          },
        },
      ]
    );
  }, [deleteIntake]);


  if (isLoading) {
    return (
      <View style={styles.centerContainer}>
        <View style={styles.loadingIconContainer}>
          <ActivityIndicator size="large" color="#5E5CE6" />
        </View>
        <Text style={styles.loadingText}>Chargement de l'historique...</Text>
        <Text style={styles.loadingSubText}>Analyse de vos prises en cours</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centerContainer}>
        <View style={styles.errorIconContainer}>
          <XCircle size={56} color="#FF3B30" strokeWidth={2.5} />
        </View>
        <Text style={styles.errorText}>Erreur de chargement</Text>
        <Text style={styles.errorSubText}>{error.message}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={onRefresh} activeOpacity={0.8}>
          <Text style={styles.retryButtonText}>Réessayer</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (!historyByDay || historyByDay.length === 0) {
    return (
      <View style={styles.centerContainer}>
        <View style={styles.emptyIconContainer}>
          <Calendar size={56} color="#5E5CE6" strokeWidth={2} />
        </View>
        <Text style={styles.emptyText}>Aucun historique</Text>
        <Text style={styles.emptySubText}>
          Marquez vos prises de médicaments pour commencer votre suivi
        </Text>
      </View>
    );
  }

  return (
    <>
      {/* Barre de navigation des mois */}
      {historyByMonth.length > 0 && (
        <View style={styles.monthNavContainer}>
          <ScrollView 
            ref={monthNavScrollRef}
            horizontal 
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.monthNavContent}
          >
            {historyByMonth.map((section) => {
              const [monthName, year] = section.title.split(' ');
              const shortYear = year.slice(-2);
              return (
                <TouchableOpacity
                  key={section.key}
                  style={[
                    styles.monthNavButton,
                    selectedMonth === section.key && styles.monthNavButtonActive,
                  ]}
                  onPress={() => selectMonth(section.key)}
                  activeOpacity={0.7}
                >
                  <View style={styles.monthNavButtonContent}>
                    <Text style={[
                      styles.monthNavText,
                      selectedMonth === section.key && styles.monthNavTextActive,
                    ]}>
                      {monthName}
                    </Text>
                    <Text style={styles.monthNavYear}>'{shortYear}</Text>
                  </View>
                  <View style={[
                    styles.monthNavBadge,
                    section.completionRate === 100 && styles.monthNavBadgeSuccess,
                  ]}>
                    <Text style={styles.monthNavBadgeText}>{section.totalDays}</Text>
                  </View>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>
      )}
      
      <SectionList
        sections={filteredHistoryByMonth}
        keyExtractor={(item) => item.date}
        initialNumToRender={30}
        maxToRenderPerBatch={20}
        windowSize={10}
        renderItem={({ item, index, section }) => {
          const isLastInSection = index === section.data.length - 1;
          return (
            <DayHistoryCard 
              summary={item} 
              onEdit={handleEdit}
              onDelete={handleDelete}
              isLastInSection={isLastInSection}
            />
          );
        }}
        renderSectionHeader={({ section }) => (
          <>
            {/* Carte de récapitulatif du mois */}
            <View style={styles.monthSummaryCard}>
              <View style={styles.monthSummaryHeader}>
                <View style={styles.monthSummaryIconContainer}>
                  <Calendar size={24} color="#5E5CE6" strokeWidth={2.5} />
                </View>
                <View style={styles.monthSummaryHeaderContent}>
                  <Text style={styles.monthSummaryTitle}>{section.title}</Text>
                  <Text style={styles.monthSummarySubtitle}>Récapitulatif du mois</Text>
                </View>
              </View>

              {/* Statistiques */}
              <View style={styles.monthStatsGrid}>
                {/* Total jours */}
                <View style={styles.monthStatItem}>
                  <View style={styles.monthStatIconBadge}>
                    <Calendar size={18} color="#5E5CE6" strokeWidth={2.5} />
                  </View>
                  <Text style={styles.monthStatValue}>{section.totalDays}</Text>
                  <Text style={styles.monthStatLabel}>Jour{section.totalDays > 1 ? 's' : ''}</Text>
                </View>

                {/* Total prises */}
                <View style={styles.monthStatItem}>
                  <View style={styles.monthStatIconBadge}>
                    <CheckCircle size={18} color="#34C759" strokeWidth={2.5} />
                  </View>
                  <Text style={styles.monthStatValue}>{section.totalIntakes}</Text>
                  <Text style={styles.monthStatLabel}>Prise{section.totalIntakes > 1 ? 's' : ''}</Text>
                </View>

                {/* Taux de complétion */}
                <View style={styles.monthStatItem}>
                  <View style={[
                    styles.monthStatIconBadge,
                    section.completionRate === 100 && styles.monthStatIconSuccess,
                    section.completionRate < 100 && section.completionRate >= 50 && styles.monthStatIconWarning,
                    section.completionRate < 50 && styles.monthStatIconDanger,
                  ]}>
                    <Award size={18} color="#FFFFFF" strokeWidth={2.5} />
                  </View>
                  <Text style={[
                    styles.monthStatValue,
                    section.completionRate === 100 && styles.monthStatValueSuccess,
                  ]}>
                    {Math.round(section.completionRate)}%
                  </Text>
                  <Text style={styles.monthStatLabel}>Complété</Text>
                </View>
              </View>

              {/* Variations de traitement */}
              {section.treatmentChanges && section.treatmentChanges.length > 0 && (
                <View style={styles.treatmentChangesContainer}>
                  <View style={styles.treatmentChangesHeader}>
                    <AlertCircle size={18} color="#FF9500" strokeWidth={2.5} />
                    <Text style={styles.treatmentChangesTitle}>
                      Variations du traitement ({section.treatmentChanges.length})
                    </Text>
                  </View>
                  {section.treatmentChanges.map((change, idx) => (
                    <View key={idx} style={styles.treatmentChangeItem}>
                      <View style={[
                        styles.changeIndicator,
                        change.type === 'added' && styles.changeIndicatorAdded,
                        change.type === 'stopped' && styles.changeIndicatorStopped,
                        change.type === 'dosage_changed' && styles.changeIndicatorChanged,
                      ]} />
                      <View style={styles.changeContent}>
                        <Text style={styles.changeMedicationName}>{change.medicationName}</Text>
                        <Text style={styles.changeDescription}>
                          {change.type === 'added' && '🆕 Traitement ajouté'}
                          {change.type === 'stopped' && '⏹️ Traitement arrêté'}
                          {change.type === 'dosage_changed' && `💊 Dosage modifié: ${change.oldDosage} → ${change.newDosage}`}
                        </Text>
                        <Text style={styles.changeDate}>
                          Le {new Date(change.date).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })}
                        </Text>
                      </View>
                    </View>
                  ))}
                </View>
              )}
            </View>

            {/* En-tête simple */}
            <View style={styles.simpleSectionHeader}>
              <Text style={styles.simpleSectionTitle}>Détail jour par jour</Text>
            </View>
          </>
        )}
        renderSectionFooter={() => <View style={styles.sectionSeparator} />}
        contentContainerStyle={styles.listContainer}
        showsVerticalScrollIndicator={false}
        stickySectionHeadersEnabled={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor="#5E5CE6"
            colors={['#5E5CE6']}
          />
        }
      />
      
      <EditModalWrapper />
    </>
  );
}

interface DayHistoryCardProps {
  summary: DailyIntakeSummary;
  onEdit: (intake: MedicationIntake) => void;
  onDelete: (intake: MedicationIntake) => void;
  isLastInSection?: boolean;
}

const DayHistoryCard = React.memo(function DayHistoryCard({ summary, onEdit, onDelete, isLastInSection }: DayHistoryCardProps) {
  const formattedDate = formatDate(summary.date);
  const isToday = summary.date === new Date().toISOString().split('T')[0];
  const completionRate = summary.totalIntakes > 0 ? (summary.takenCount / summary.totalIntakes) * 100 : 0;
  const isPerfectDay = completionRate === 100 && summary.totalIntakes > 0;

  return (
    <View style={[styles.dayCard, isLastInSection && styles.dayCardLast]}>
      {/* En-tête simplifié */}
      <View style={styles.dayHeader}>
        <View style={styles.dayHeaderLeft}>
          <View style={styles.dateContainer}>
            <Text style={styles.dayDate}>
              {isToday ? "Aujourd'hui" : formattedDate}
            </Text>
            {isToday && <View style={styles.todayDot} />}
          </View>
        </View>
        
        <View style={styles.statsRow}>
          {isPerfectDay && (
            <Award size={18} color="#FFB800" strokeWidth={2.5} style={styles.trophyIcon} />
          )}
          <Text style={styles.statsText}>
            <Text style={styles.statsNumber}>{summary.takenCount}</Text>
            <Text style={styles.statsSlash}>/</Text>
            <Text style={styles.statsTotalNumber}>{summary.totalIntakes}</Text>
          </Text>
        </View>
      </View>

      {/* Barre de progression simplifiée */}
      <View style={styles.progressContainer}>
        <View style={styles.progressBar}>
          <View 
            style={[
              styles.progressFill,
              { 
                width: `${completionRate}%`,
                backgroundColor: completionRate === 100 ? '#34C759' : completionRate >= 50 ? '#FF9500' : '#FF3B30'
              }
            ]} 
          />
        </View>
      </View>

      {/* Liste des prises simplifiée */}
      {summary.intakes.map((intake, index) => (
        <View key={intake.id} style={[
          styles.intakeRow, 
          index === summary.intakes.length - 1 && styles.intakeRowLast
        ]}>
          {/* Indicateur de statut simple */}
          <View style={[
            styles.statusIndicator,
            intake.status === 'taken' && styles.statusIndicatorTaken,
            intake.status === 'skipped' && styles.statusIndicatorSkipped,
          ]} />

          <View style={styles.intakeMain}>
            {/* Nom et statut */}
            <View style={styles.intakeTopRow}>
              <Text style={styles.medicationName} numberOfLines={1}>
                {intake.medication?.medication_name || 'Médicament inconnu'}
              </Text>
              {intake.status === 'taken' ? (
                <CheckCircle size={18} color="#34C759" strokeWidth={2.5} />
              ) : intake.status === 'skipped' ? (
                <XCircle size={18} color="#FF3B30" strokeWidth={2.5} />
              ) : (
                <Clock size={18} color="#FF9500" strokeWidth={2.5} />
              )}
            </View>

            {/* Infos secondaires */}
            <View style={styles.intakeBottomRow}>
              <Text style={styles.intakeTimeText}>
                {intake.intake_time || formatTime(intake.taken_at)}
              </Text>
              {intake.pills_taken > 0 && (
                <>
                  <Text style={styles.separator}>•</Text>
                  <Text style={styles.pillsText}>
                    {formatPillCount(intake.pills_taken)} cp
                  </Text>
                </>
              )}
              {intake.scheduled_time && (
                <>
                  <Text style={styles.separator}>•</Text>
                  <Text style={styles.scheduledText}>
                    prévu {intake.scheduled_time}
                  </Text>
                </>
              )}
            </View>

            {/* Notes si présentes */}
            {intake.notes && (
              <Text style={styles.notesText} numberOfLines={2}>
                {intake.notes}
              </Text>
            )}
          </View>

          {/* Actions */}
          <View style={styles.actions}>
            <PressableScale 
              onPress={() => onEdit(intake)} 
              style={styles.actionBtn}
            >
              <Edit2 size={16} color="#8E8E93" strokeWidth={2} />
            </PressableScale>
            
            <PressableScale onPress={() => onDelete(intake)} style={styles.actionBtn}>
              <Trash2 size={16} color="#8E8E93" strokeWidth={2} />
            </PressableScale>
          </View>
        </View>
      ))}
    </View>
  );
});

// Helpers
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const options: Intl.DateTimeFormatOptions = { 
    weekday: 'long', 
    day: 'numeric', 
    month: 'long' 
  };
  return date.toLocaleDateString('fr-FR', options);
}

function formatTime(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}

function getStatusLabel(status: string): string {
  switch (status) {
    case 'taken': return 'Pris';
    case 'skipped': return 'Oublié';
    case 'late': return 'En retard';
    case 'early': return 'En avance';
    default: return status;
  }
}

const styles = StyleSheet.create({
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  loadingIconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(94, 92, 230, 0.1)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
    borderWidth: 2,
    borderColor: 'rgba(94, 92, 230, 0.2)',
  },
  loadingText: {
    fontSize: 17,
    color: '#FFFFFF',
    fontWeight: '700',
    marginBottom: 6,
  },
  loadingSubText: {
    fontSize: 14,
    color: '#8E8E93',
  },
  errorIconContainer: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: 'rgba(255, 59, 48, 0.1)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
    borderWidth: 2,
    borderColor: 'rgba(255, 59, 48, 0.2)',
  },
  errorText: {
    fontSize: 18,
    color: '#FF3B30',
    fontWeight: '700',
    marginBottom: 8,
  },
  errorSubText: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    marginBottom: 20,
    paddingHorizontal: 40,
  },
  retryButton: {
    backgroundColor: '#5E5CE6',
    paddingHorizontal: 28,
    paddingVertical: 12,
    borderRadius: 12,
  },
  retryButtonText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  emptyIconContainer: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: 'rgba(94, 92, 230, 0.1)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
    borderWidth: 2,
    borderColor: 'rgba(94, 92, 230, 0.2)',
  },
  emptyText: {
    fontSize: 20,
    color: '#FFFFFF',
    fontWeight: '700',
    marginBottom: 8,
  },
  emptySubText: {
    fontSize: 15,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 22,
    paddingHorizontal: 40,
  },
  listContainer: {
    padding: 16,
    paddingBottom: 32,
  },
  // Month Navigation Bar Styles
  monthNavContainer: {
    backgroundColor: 'rgba(13, 13, 31, 0.98)',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(94, 92, 230, 0.2)',
    paddingVertical: 12,
  },
  monthNavContent: {
    paddingHorizontal: 16,
    gap: 8,
  },
  monthNavButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 12,
    backgroundColor: 'rgba(26, 26, 46, 0.6)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    gap: 10,
  },
  monthNavButtonActive: {
    backgroundColor: 'rgba(94, 92, 230, 0.2)',
    borderColor: '#5E5CE6',
  },
  monthNavButtonContent: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 4,
  },
  monthNavText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#8E8E93',
  },
  monthNavTextActive: {
    color: '#5E5CE6',
  },
  monthNavYear: {
    fontSize: 11,
    fontWeight: '600',
    color: '#636366',
  },
  monthNavBadge: {
    minWidth: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: 'rgba(142, 142, 147, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 6,
  },
  monthNavBadgeSuccess: {
    backgroundColor: 'rgba(52, 199, 89, 0.2)',
  },
  monthNavBadgeText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  // Month Summary Card Styles
  monthSummaryCard: {
    backgroundColor: 'rgba(26, 26, 46, 0.8)',
    marginHorizontal: 16,
    marginTop: 16,
    marginBottom: 12,
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(94, 92, 230, 0.3)',
  },
  monthSummaryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    gap: 12,
  },
  monthSummaryIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 16,
    backgroundColor: 'rgba(94, 92, 230, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(94, 92, 230, 0.3)',
  },
  monthSummaryHeaderContent: {
    flex: 1,
  },
  monthSummaryTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: -0.3,
    marginBottom: 2,
  },
  monthSummarySubtitle: {
    fontSize: 13,
    fontWeight: '500',
    color: '#8E8E93',
  },
  monthStatsGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  monthStatItem: {
    flex: 1,
    backgroundColor: 'rgba(13, 13, 31, 0.6)',
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  monthStatIconBadge: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: 'rgba(94, 92, 230, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(94, 92, 230, 0.3)',
  },
  monthStatIconSuccess: {
    backgroundColor: 'rgba(52, 199, 89, 0.2)',
    borderColor: 'rgba(52, 199, 89, 0.4)',
  },
  monthStatIconWarning: {
    backgroundColor: 'rgba(255, 149, 0, 0.2)',
    borderColor: 'rgba(255, 149, 0, 0.4)',
  },
  monthStatIconDanger: {
    backgroundColor: 'rgba(255, 59, 48, 0.2)',
    borderColor: 'rgba(255, 59, 48, 0.4)',
  },
  monthStatValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
    letterSpacing: -0.5,
  },
  monthStatValueSuccess: {
    color: '#34C759',
  },
  monthStatLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#8E8E93',
    textAlign: 'center',
  },
  // Treatment Changes Styles
  treatmentChangesContainer: {
    marginTop: 20,
    paddingTop: 20,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.1)',
  },
  treatmentChangesHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 16,
  },
  treatmentChangesTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FF9500',
  },
  treatmentChangeItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    paddingVertical: 12,
    paddingHorizontal: 12,
    backgroundColor: 'rgba(13, 13, 31, 0.4)',
    borderRadius: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.05)',
  },
  changeIndicator: {
    width: 6,
    height: '100%',
    borderRadius: 3,
    backgroundColor: '#8E8E93',
    minHeight: 50,
  },
  changeIndicatorAdded: {
    backgroundColor: '#34C759',
  },
  changeIndicatorStopped: {
    backgroundColor: '#FF3B30',
  },
  changeIndicatorChanged: {
    backgroundColor: '#FF9500',
  },
  changeContent: {
    flex: 1,
  },
  changeMedicationName: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  changeDescription: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E93',
    marginBottom: 4,
  },
  changeDate: {
    fontSize: 12,
    fontWeight: '500',
    color: '#636366',
  },
  // Simple Section Header Styles
  simpleSectionHeader: {
    backgroundColor: 'rgba(13, 13, 31, 0.8)',
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(94, 92, 230, 0.2)',
  },
  simpleSectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  simpleSectionSubtitle: {
    fontSize: 13,
    fontWeight: '500',
    color: '#8E8E93',
  },
  dayCard: {
    backgroundColor: 'rgba(26, 26, 46, 0.6)',
    borderRadius: 20,
    padding: 20,
    marginBottom: 12,
    marginLeft: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  dayCardLast: {
    marginBottom: 0,
  },
  sectionSeparator: {
    height: 20,
  },
  dayHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  dayHeaderLeft: {
    flex: 1,
  },
  dateContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  dayDate: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: -0.3,
  },
  todayDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#5E5CE6',
  },
  statsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  trophyIcon: {
    marginRight: 4,
  },
  statsText: {
    fontSize: 20,
    fontWeight: '700',
  },
  statsNumber: {
    color: '#FFFFFF',
    fontSize: 22,
  },
  statsSlash: {
    color: '#6E6E73',
    fontSize: 18,
  },
  statsTotalNumber: {
    color: '#6E6E73',
    fontSize: 20,
  },
  progressContainer: {
    marginBottom: 20,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  progressBar: {
    height: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 2,
  },
  intakeRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.05)',
  },
  intakeRowLast: {
    borderBottomWidth: 0,
    paddingBottom: 0,
  },
  statusIndicator: {
    width: 4,
    height: 48,
    borderRadius: 2,
    backgroundColor: '#8E8E93',
  },
  statusIndicatorTaken: {
    backgroundColor: '#34C759',
  },
  statusIndicatorSkipped: {
    backgroundColor: '#FF3B30',
  },
  intakeMain: {
    flex: 1,
  },
  intakeTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
    gap: 12,
  },
  medicationName: {
    flex: 1,
    fontSize: 17,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: -0.2,
  },
  intakeBottomRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 8,
  },
  intakeTimeText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#5E5CE6',
  },
  separator: {
    fontSize: 14,
    color: '#6E6E73',
  },
  pillsText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#FFFFFF',
    opacity: 0.7,
  },
  scheduledText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#8E8E93',
  },
  notesText: {
    fontSize: 13,
    color: '#FFFFFF',
    opacity: 0.6,
    marginTop: 8,
    lineHeight: 18,
    fontStyle: 'italic',
  },
  actions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  actionBtn: {
    width: 36,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
});
