/**
 * WhyEnergyStack - Composant de storytelling pour expliquer le score d'énergie
 * 
 * Affiche des cartes narratives générées par l'IA pour expliquer de manière
 * pédagogique et empathique pourquoi le score d'énergie est à son niveau actuel.
 * 
 * Architecture:
 * - UI pure (pas de logique métier)
 * - Reçoit les données via props
 * - Utilise expo-blur pour l'effet glassmorphism
 * - Animations fluides avec react-native-reanimated
 */

import React, { useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Dimensions,
  Pressable,
  Platform,
} from 'react-native';
import { BlurView } from 'expo-blur';
import Animated, {
  FadeInRight,
  FadeInUp,
  useAnimatedStyle,
  withSpring,
  useSharedValue,
} from 'react-native-reanimated';
import type { EnergyCard } from '@/hooks/useEnergyExplanation';
import { getCardIcon, getCardColor, formatMetric } from '@/hooks/useEnergyExplanation';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const CARD_WIDTH = SCREEN_WIDTH - 64; // 32px padding de chaque côté
const CARD_SPACING = 16;

interface WhyEnergyStackProps {
  cards: EnergyCard[];
  energyScore?: number;
  label?: string;
  onCardPress?: (card: EnergyCard, index: number) => void;
}

/**
 * Composant de carte individuelle avec effet glassmorphism
 */
const EnergyExplanationCard: React.FC<{
  card: EnergyCard;
  index: number;
  onPress?: () => void;
}> = ({ card, index, onPress }) => {
  const scale = useSharedValue(1);
  const colors = getCardColor(card.type);
  const icon = getCardIcon(card.type);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const handlePressIn = () => {
    scale.value = withSpring(0.98);
  };

  const handlePressOut = () => {
    scale.value = withSpring(1);
  };

  return (
    <Animated.View
      entering={FadeInRight.delay(index * 100).springify()}
      style={[styles.cardWrapper, animatedStyle]}
    >
      <Pressable
        onPress={onPress}
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        disabled={!onPress}
      >
        <BlurView
          intensity={Platform.OS === 'ios' ? 80 : 60}
          tint="dark"
          style={[
            styles.card,
            {
              borderColor: colors.border,
              backgroundColor: Platform.OS === 'android' ? 'rgba(30, 30, 30, 0.9)' : undefined,
            },
          ]}
        >
          {/* Header avec icône et type */}
          <View style={styles.cardHeader}>
            <View style={[styles.iconContainer, { backgroundColor: colors.background }]}>
              <Text style={styles.iconText}>{icon}</Text>
            </View>
            <View style={[styles.typeBadge, { backgroundColor: colors.background }]}>
              <Text style={[styles.typeBadgeText, { color: colors.accent }]}>
                {card.type === 'nervous' && 'Système Nerveux'}
                {card.type === 'chemistry' && 'Chimie Corporelle'}
                {card.type === 'load' && 'Charge & Effort'}
              </Text>
            </View>
          </View>

          {/* Titre principal */}
          <Text style={styles.cardTitle}>{card.title}</Text>

          {/* Texte explicatif */}
          <Text style={styles.cardText}>{card.text}</Text>

          {/* Métriques si disponibles */}
          {card.metrics && (card.metrics.primary || card.metrics.secondary) && (
            <View style={styles.metricsContainer}>
              {card.metrics.primary && (
                <View style={styles.metricItem}>
                  <Text style={styles.metricLabel}>{card.metrics.primary.label}</Text>
                  <Text style={[styles.metricValue, { color: colors.accent }]}>
                    {formatMetric(card.metrics.primary)}
                  </Text>
                </View>
              )}
              {card.metrics.secondary && (
                <View style={styles.metricItem}>
                  <Text style={styles.metricLabel}>{card.metrics.secondary.label}</Text>
                  <Text style={styles.metricValueSecondary}>
                    {formatMetric(card.metrics.secondary)}
                  </Text>
                </View>
              )}
            </View>
          )}

          {/* Analogie (la partie "aha!") */}
          <View style={[styles.analogyBox, { backgroundColor: colors.background }]}>
            <Text style={styles.analogyIcon}>💡</Text>
            <Text style={[styles.analogyText, { color: colors.accent }]}>{card.analogy}</Text>
          </View>
        </BlurView>
      </Pressable>
    </Animated.View>
  );
};

/**
 * Composant principal - Stack de cartes explicatives
 */
export const WhyEnergyStack: React.FC<WhyEnergyStackProps> = ({
  cards,
  energyScore,
  label,
  onCardPress,
}) => {
  const scrollViewRef = useRef<ScrollView>(null);

  console.log('[WhyEnergyStack] 🎨 Component rendered with:', {
    cardsCount: cards?.length || 0,
    energyScore,
    label,
  });

  if (!cards || cards.length === 0) {
    console.log('[WhyEnergyStack] ⚠️ No cards to display');
    return (
      <View style={styles.container}>
        <Text style={styles.emptyStateText}>
          Aucune explication disponible pour le moment.
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <Animated.View entering={FadeInUp.springify()} style={styles.headerContainer}>
        <Text style={styles.header}>Pourquoi ce score ?</Text>
        {energyScore !== undefined && label && (
          <View style={styles.scoreContainer}>
            <Text style={styles.scoreValue}>{energyScore}%</Text>
            <Text style={styles.scoreLabel}>{label}</Text>
          </View>
        )}
      </Animated.View>

      {/* Cartes en défilement horizontal */}
      <ScrollView
        ref={scrollViewRef}
        horizontal
        pagingEnabled={Platform.OS === 'ios'}
        showsHorizontalScrollIndicator={false}
        decelerationRate={Platform.OS === 'ios' ? 0 : 0.9}
        snapToInterval={CARD_WIDTH + CARD_SPACING}
        snapToAlignment="start"
        contentContainerStyle={styles.scrollContent}
        style={styles.scrollView}
      >
        {cards.map((card, index) => (
          <EnergyExplanationCard
            key={`${card.type}-${index}`}
            card={card}
            index={index}
            onPress={onCardPress ? () => onCardPress(card, index) : undefined}
          />
        ))}
      </ScrollView>

      {/* Indicateur de pagination (dots) */}
      {cards.length > 1 && (
        <View style={styles.paginationContainer}>
          {cards.map((_, index) => (
            <View
              key={index}
              style={[
                styles.paginationDot,
                index === 0 && styles.paginationDotActive,
              ]}
            />
          ))}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 24,
  },
  headerContainer: {
    paddingHorizontal: 32,
    marginBottom: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  header: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: -0.5,
  },
  scoreContainer: {
    alignItems: 'flex-end',
  },
  scoreValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  scoreLabel: {
    fontSize: 12,
    color: '#AAAAAA',
    marginTop: 2,
  },
  scrollView: {
    flexGrow: 0,
  },
  scrollContent: {
    paddingHorizontal: 32,
    paddingRight: 32 + CARD_SPACING,
  },
  cardWrapper: {
    width: CARD_WIDTH,
    marginRight: CARD_SPACING,
  },
  card: {
    width: '100%',
    borderRadius: 24,
    padding: 24,
    borderWidth: 1,
    overflow: 'hidden',
    minHeight: 340,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    justifyContent: 'space-between',
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconText: {
    fontSize: 24,
  },
  typeBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  typeBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  cardTitle: {
    color: '#FFFFFF',
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 12,
    lineHeight: 28,
  },
  cardText: {
    color: '#CCCCCC',
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 16,
  },
  metricsContainer: {
    flexDirection: 'row',
    gap: 16,
    marginBottom: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.1)',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  metricItem: {
    flex: 1,
  },
  metricLabel: {
    fontSize: 11,
    color: '#888888',
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  metricValue: {
    fontSize: 20,
    fontWeight: '700',
  },
  metricValueSecondary: {
    fontSize: 18,
    fontWeight: '600',
    color: '#AAAAAA',
  },
  analogyBox: {
    marginTop: 'auto',
    paddingTop: 16,
    paddingHorizontal: 16,
    paddingBottom: 16,
    borderRadius: 16,
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  analogyIcon: {
    fontSize: 20,
    marginTop: 2,
  },
  analogyText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
    fontStyle: 'italic',
    fontWeight: '500',
  },
  paginationContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 20,
    gap: 8,
  },
  paginationDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
  },
  paginationDotActive: {
    width: 24,
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
  },
  emptyStateText: {
    color: '#888888',
    fontSize: 15,
    textAlign: 'center',
    paddingVertical: 40,
  },
});
