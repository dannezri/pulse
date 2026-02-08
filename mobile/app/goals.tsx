import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { router } from 'expo-router';
import { ChevronLeft, Target, TrendingUp, Activity, Heart } from 'lucide-react-native';

export default function GoalsScreen() {
  const goals = [
    {
      id: '1',
      title: 'Améliorer mon sommeil',
      icon: '🌙',
      progress: 65,
      color: '#7B6CF6',
      target: '8h par nuit',
      current: '6.5h',
    },
    {
      id: '2',
      title: 'Augmenter mon HRV',
      icon: '💓',
      progress: 45,
      color: '#FF6B35',
      target: '60ms',
      current: '45ms',
    },
    {
      id: '3',
      title: 'Réduire mon stress',
      icon: '🧘',
      progress: 80,
      color: '#4ECDC4',
      target: 'Score < 30',
      current: 'Score 25',
    },
  ];

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
        <Text style={styles.headerTitle}>Goals</Text>
        <View style={styles.headerButton} />
      </View>

      <ScrollView 
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {/* Stats Overview */}
        <View style={styles.statsContainer}>
          <View style={styles.statCard}>
            <Target size={24} color="#7B6CF6" strokeWidth={2.5} />
            <Text style={styles.statValue}>3</Text>
            <Text style={styles.statLabel}>Objectifs actifs</Text>
          </View>
          <View style={styles.statCard}>
            <TrendingUp size={24} color="#4ECDC4" strokeWidth={2.5} />
            <Text style={styles.statValue}>63%</Text>
            <Text style={styles.statLabel}>Progression moy.</Text>
          </View>
        </View>

        {/* Goals List */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Mes Objectifs</Text>
          
          {goals.map((goal) => (
            <View key={goal.id} style={styles.goalCard}>
              <View style={styles.goalHeader}>
                <View style={styles.goalIconContainer}>
                  <Text style={styles.goalIcon}>{goal.icon}</Text>
                </View>
                <View style={styles.goalInfo}>
                  <Text style={styles.goalTitle}>{goal.title}</Text>
                  <View style={styles.goalStats}>
                    <Text style={styles.goalCurrent}>{goal.current}</Text>
                    <Text style={styles.goalSeparator}>→</Text>
                    <Text style={styles.goalTarget}>{goal.target}</Text>
                  </View>
                </View>
              </View>
              
              {/* Progress Bar */}
              <View style={styles.progressContainer}>
                <View style={styles.progressBar}>
                  <View 
                    style={[
                      styles.progressFill, 
                      { width: `${goal.progress}%`, backgroundColor: goal.color }
                    ]} 
                  />
                </View>
                <Text style={styles.progressText}>{goal.progress}%</Text>
              </View>
            </View>
          ))}
        </View>

        {/* Add Goal Button */}
        <TouchableOpacity style={styles.addButton} activeOpacity={0.8}>
          <Text style={styles.addButtonText}>+ Ajouter un objectif</Text>
        </TouchableOpacity>
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
  },
  statValue: {
    fontSize: 28,
    fontWeight: '800',
    color: '#FFFFFF',
    marginTop: 12,
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF60',
    textAlign: 'center',
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 16,
    letterSpacing: 0.3,
  },
  goalCard: {
    backgroundColor: '#1A1A2E',
    borderRadius: 20,
    padding: 20,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#FFFFFF10',
  },
  goalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  goalIconContainer: {
    width: 56,
    height: 56,
    backgroundColor: '#FFFFFF10',
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  goalIcon: {
    fontSize: 28,
  },
  goalInfo: {
    flex: 1,
  },
  goalTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 8,
    letterSpacing: 0.2,
  },
  goalStats: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  goalCurrent: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF80',
  },
  goalSeparator: {
    fontSize: 14,
    color: '#FFFFFF40',
  },
  goalTarget: {
    fontSize: 14,
    fontWeight: '700',
    color: '#4ECDC4',
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  progressBar: {
    flex: 1,
    height: 8,
    backgroundColor: '#FFFFFF10',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  progressText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
    minWidth: 45,
    textAlign: 'right',
  },
  addButton: {
    backgroundColor: '#7B6CF6',
    borderRadius: 20,
    paddingVertical: 18,
    alignItems: 'center',
    marginTop: 12,
  },
  addButtonText: {
    fontSize: 17,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 0.3,
  },
});
