import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { router } from 'expo-router';
import { ChevronLeft, Heart, Activity, Brain, Droplet } from 'lucide-react-native';

export default function MyBodyScreen() {
  const metrics = [
    {
      id: '1',
      title: 'Fréquence cardiaque',
      icon: Heart,
      color: '#FF6B35',
      value: '68',
      unit: 'bpm',
      status: 'Normal',
      statusColor: '#4ECDC4',
    },
    {
      id: '2',
      title: 'Variabilité (HRV)',
      icon: Activity,
      color: '#7B6CF6',
      value: '45',
      unit: 'ms',
      status: 'Moyen',
      statusColor: '#FFB800',
    },
    {
      id: '3',
      title: 'Niveau de stress',
      icon: Brain,
      color: '#FF6B9D',
      value: '25',
      unit: '/100',
      status: 'Faible',
      statusColor: '#4ECDC4',
    },
    {
      id: '4',
      title: 'Hydratation',
      icon: Droplet,
      color: '#4ECDC4',
      value: '2.1',
      unit: 'L',
      status: 'Bon',
      statusColor: '#4ECDC4',
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
        <Text style={styles.headerTitle}>My Body</Text>
        <View style={styles.headerButton} />
      </View>

      <ScrollView 
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {/* Body Overview */}
        <View style={styles.overviewCard}>
          <Text style={styles.overviewTitle}>État général</Text>
          <View style={styles.overviewScore}>
            <Text style={styles.overviewScoreValue}>85</Text>
            <Text style={styles.overviewScoreLabel}>/ 100</Text>
          </View>
          <Text style={styles.overviewStatus}>Excellent</Text>
        </View>

        {/* Metrics */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Métriques clés</Text>
          
          {metrics.map((metric) => {
            const IconComponent = metric.icon;
            return (
              <View key={metric.id} style={styles.metricCard}>
                <View style={[styles.metricIcon, { backgroundColor: metric.color + '20' }]}>
                  <IconComponent size={24} color={metric.color} strokeWidth={2.5} />
                </View>
                <View style={styles.metricInfo}>
                  <Text style={styles.metricTitle}>{metric.title}</Text>
                  <View style={styles.metricValueContainer}>
                    <Text style={styles.metricValue}>{metric.value}</Text>
                    <Text style={styles.metricUnit}>{metric.unit}</Text>
                  </View>
                </View>
                <View style={styles.metricStatus}>
                  <View style={[styles.statusDot, { backgroundColor: metric.statusColor }]} />
                  <Text style={[styles.statusText, { color: metric.statusColor }]}>
                    {metric.status}
                  </Text>
                </View>
              </View>
            );
          })}
        </View>

        {/* Quick Actions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Actions rapides</Text>
          
          <TouchableOpacity style={styles.actionButton} activeOpacity={0.8}>
            <Text style={styles.actionButtonText}>📊 Voir l'historique complet</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={[styles.actionButton, styles.actionButtonSecondary]} activeOpacity={0.8}>
            <Text style={[styles.actionButtonText, styles.actionButtonTextSecondary]}>
              🔄 Synchroniser les données
            </Text>
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
  overviewCard: {
    backgroundColor: '#1A1A2E',
    borderRadius: 24,
    padding: 32,
    alignItems: 'center',
    marginBottom: 32,
    borderWidth: 1,
    borderColor: '#FFFFFF10',
  },
  overviewTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF80',
    marginBottom: 16,
  },
  overviewScore: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 12,
  },
  overviewScoreValue: {
    fontSize: 56,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: -2,
  },
  overviewScoreLabel: {
    fontSize: 24,
    fontWeight: '600',
    color: '#FFFFFF40',
    marginLeft: 4,
  },
  overviewStatus: {
    fontSize: 18,
    fontWeight: '700',
    color: '#4ECDC4',
    letterSpacing: 0.5,
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 16,
    letterSpacing: 0.3,
  },
  metricCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1A1A2E',
    borderRadius: 20,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#FFFFFF10',
  },
  metricIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  metricInfo: {
    flex: 1,
  },
  metricTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 6,
    letterSpacing: 0.2,
  },
  metricValueContainer: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  metricValue: {
    fontSize: 24,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: -0.5,
  },
  metricUnit: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF60',
    marginLeft: 4,
  },
  metricStatus: {
    alignItems: 'flex-end',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginBottom: 6,
  },
  statusText: {
    fontSize: 13,
    fontWeight: '700',
    letterSpacing: 0.2,
  },
  actionButton: {
    backgroundColor: '#7B6CF6',
    borderRadius: 20,
    paddingVertical: 18,
    alignItems: 'center',
    marginBottom: 12,
  },
  actionButtonSecondary: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: '#FFFFFF20',
  },
  actionButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 0.3,
  },
  actionButtonTextSecondary: {
    color: '#FFFFFF',
  },
});
