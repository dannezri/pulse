/**
 * EnergyProfileCard Component
 * 
 * Affiche le profil énergétique personnel de l'utilisateur
 * - Traits appris sur le long terme (patterns personnels)
 * - Groupés par catégorie avec icônes
 * - Score de confiance affiché
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { 
  Moon, Apple, Activity, Heart, Brain, Clock,
  ChevronRight, Info, TrendingUp, Sparkles
} from 'lucide-react-native';
import type { EnergyProfile, EnergyProfileTrait, TraitCategory } from '../hooks/useEnergyProfile';

interface EnergyProfileCardProps {
  profile: EnergyProfile;
  onTraitPress?: (trait: EnergyProfileTrait) => void;
}

const getCategoryIcon = (category: TraitCategory, size: number = 18, color: string = '#FFFFFF') => {
  switch (category) {
    case 'sleep':
      return <Moon size={size} color={color} />;
    case 'nutrition':
      return <Apple size={size} color={color} />;
    case 'exercise':
      return <Activity size={size} color={color} />;
    case 'recovery':
      return <Heart size={size} color={color} />;
    case 'stress':
      return <Brain size={size} color={color} />;
    case 'timing':
      return <Clock size={size} color={color} />;
  }
};

const getCategoryLabel = (category: TraitCategory): string => {
  const labels: Record<TraitCategory, string> = {
    sleep: 'Sommeil',
    nutrition: 'Nutrition',
    exercise: 'Exercice',
    recovery: 'Récupération',
    stress: 'Stress',
    timing: 'Timing',
  };
  return labels[category];
};

const getConfidenceColor = (confidence: number): string => {
  if (confidence >= 0.85) return '#00FF41'; // Vert - Très fiable
  if (confidence >= 0.75) return '#00C7BE'; // Cyan - Fiable
  if (confidence >= 0.65) return '#FF9500'; // Orange - Modéré
  return '#8E8E93'; // Gris - Faible
};

const getConfidenceLabel = (confidence: number): string => {
  if (confidence >= 0.85) return 'Très fiable';
  if (confidence >= 0.75) return 'Fiable';
  if (confidence >= 0.65) return 'Modéré';
  return 'En cours';
};

function TraitItem({ trait, onPress }: { trait: EnergyProfileTrait; onPress?: (trait: EnergyProfileTrait) => void }) {
  const confidenceColor = getConfidenceColor(trait.confidence);
  const confidencePercent = Math.round(trait.confidence * 100);

  return (
    <TouchableOpacity
      style={styles.traitItem}
      onPress={() => onPress?.(trait)}
      activeOpacity={onPress ? 0.7 : 1}
      disabled={!onPress}
    >
      <View style={styles.traitHeader}>
        <View style={styles.traitTitleRow}>
          <Text style={styles.traitTitle}>{trait.title}</Text>
          <View style={[styles.confidenceBadge, { backgroundColor: confidenceColor + '20' }]}>
            <Text style={[styles.confidenceText, { color: confidenceColor }]}>
              {confidencePercent}%
            </Text>
          </View>
        </View>
      </View>

      <Text style={styles.traitDescription}>{trait.description}</Text>

      <View style={styles.traitFooter}>
        <View style={styles.traitMeta}>
          <Text style={styles.metaText}>
            {trait.data_points_count} points de données
          </Text>
          {trait.support_data?.improvement && (
            <>
              <Text style={styles.metaDot}>•</Text>
              <Text style={[styles.metaText, styles.improvement]}>
                {trait.support_data.improvement}
              </Text>
            </>
          )}
        </View>
        {onPress && (
          <ChevronRight size={16} color="#8E8E93" />
        )}
      </View>
    </TouchableOpacity>
  );
}

function CategorySection({ 
  category, 
  traits, 
  onTraitPress 
}: { 
  category: TraitCategory; 
  traits: EnergyProfileTrait[]; 
  onTraitPress?: (trait: EnergyProfileTrait) => void;
}) {
  if (traits.length === 0) return null;

  return (
    <View style={styles.categorySection}>
      <View style={styles.categoryHeader}>
        {getCategoryIcon(category, 20, '#00FF41')}
        <Text style={styles.categoryTitle}>{getCategoryLabel(category)}</Text>
        <View style={styles.categoryCount}>
          <Text style={styles.categoryCountText}>{traits.length}</Text>
        </View>
      </View>

      <View style={styles.traitsContainer}>
        {traits.map((trait) => (
          <TraitItem key={trait.id} trait={trait} onPress={onTraitPress} />
        ))}
      </View>
    </View>
  );
}

export function EnergyProfileCard({ profile, onTraitPress }: EnergyProfileCardProps) {
  if (!profile.hasData) {
    return (
      <View style={styles.card}>
        <View style={styles.header}>
          <View style={styles.titleRow}>
            <Sparkles size={24} color="#00FF41" />
            <Text style={styles.title}>Ton Profil Énergétique</Text>
          </View>
          <Text style={styles.subtitle}>
            Patterns personnels appris sur le long terme
          </Text>
        </View>

        <View style={styles.emptyState}>
          <View style={styles.emptyIcon}>
            <TrendingUp size={48} color="#48484A" />
          </View>
          <Text style={styles.emptyTitle}>Apprentissage en cours</Text>
          <Text style={styles.emptyText}>
            Nous analysons ton historique pour identifier tes patterns personnels.
            {'\n\n'}
            Continue à utiliser Pulse pendant au moins 30 jours pour découvrir ce qui fonctionne le mieux pour toi.
          </Text>
        </View>
      </View>
    );
  }

  const categories: TraitCategory[] = ['sleep', 'nutrition', 'exercise', 'recovery', 'stress', 'timing'];

  return (
    <View style={styles.card}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Sparkles size={24} color="#00FF41" />
          <Text style={styles.title}>Ton Profil Énergétique</Text>
        </View>
        <Text style={styles.subtitle}>
          {profile.traits.length} trait{profile.traits.length > 1 ? 's' : ''} personnel
          {profile.traits.length > 1 ? 's' : ''} découvert
          {profile.traits.length > 1 ? 's' : ''}
        </Text>
      </View>

      {/* High Confidence Highlight (si applicable) */}
      {profile.highConfidenceTraits.length > 0 && (
        <View style={styles.highlightSection}>
          <View style={styles.highlightHeader}>
            <Info size={14} color="#00FF41" />
            <Text style={styles.highlightTitle}>
              {profile.highConfidenceTraits.length} trait{profile.highConfidenceTraits.length > 1 ? 's' : ''} haute confiance
            </Text>
          </View>
          <Text style={styles.highlightText}>
            Ces patterns sont validés par un grand nombre de données et sont très fiables.
          </Text>
        </View>
      )}

      {/* Traits par catégorie */}
      <View style={styles.categoriesContainer}>
        {categories.map(category => (
          <CategorySection
            key={category}
            category={category}
            traits={profile.traitsByCategory[category]}
            onTraitPress={onTraitPress}
          />
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#1C1C1E',
    borderRadius: 20,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#2C2C2E',
    shadowColor: '#00FF41',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 4,
  },
  header: {
    marginBottom: 20,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 6,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  subtitle: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
  },
  highlightSection: {
    backgroundColor: '#00FF4110',
    borderRadius: 12,
    padding: 12,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#00FF4120',
  },
  highlightHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
  },
  highlightTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#00FF41',
  },
  highlightText: {
    fontSize: 12,
    color: '#8E8E93',
    lineHeight: 16,
  },
  categoriesContainer: {
    gap: 20,
  },
  categorySection: {
    gap: 12,
  },
  categoryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  categoryTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
    flex: 1,
  },
  categoryCount: {
    backgroundColor: '#2C2C2E',
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  categoryCountText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#8E8E93',
  },
  traitsContainer: {
    gap: 8,
  },
  traitItem: {
    backgroundColor: '#2C2C2E',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: '#3C3C3E',
  },
  traitHeader: {
    marginBottom: 8,
  },
  traitTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 10,
  },
  traitTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFFFFF',
    flex: 1,
  },
  confidenceBadge: {
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  confidenceText: {
    fontSize: 12,
    fontWeight: '600',
  },
  traitDescription: {
    fontSize: 14,
    color: '#AEAEB2',
    lineHeight: 20,
    marginBottom: 10,
  },
  traitFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  traitMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    flex: 1,
  },
  metaText: {
    fontSize: 11,
    color: '#8E8E93',
  },
  metaDot: {
    fontSize: 11,
    color: '#48484A',
  },
  improvement: {
    color: '#00FF41',
    fontWeight: '600',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyIcon: {
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 8,
    textAlign: 'center',
  },
  emptyText: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
    textAlign: 'center',
    maxWidth: 300,
  },
});
