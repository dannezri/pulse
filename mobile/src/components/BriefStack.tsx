/**
 * BriefStack Component - Full Screen Cards (Style Stories/TikTok)
 * 
 * Fonctionnalités:
 * - Cartes plein écran (une carte = une hauteur d'écran)
 * - Scroll vertical carte par carte avec snap
 * - Staggered entrance (cascade progressive avec FadeInDown)
 * - Haptic feedback à chaque changement de carte
 * - Pull-to-refresh
 */

import React, { useCallback, useRef, useState, useEffect } from 'react';
import { View, Text, StyleSheet, RefreshControl, Dimensions } from 'react-native';
import Animated, { FadeInDown, useAnimatedScrollHandler, useSharedValue, runOnJS } from 'react-native-reanimated';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import * as Haptics from 'expo-haptics';
import { BriefCard } from './BriefCard';
import { BriefCard as BriefCardType } from '../types/brief';
import { BriefNavigator } from './BriefNavigator';

interface BriefStackProps {
  cards: BriefCardType[];
  pulseScore: number;
  loading?: boolean;
  onRefresh?: () => void;
  refreshing?: boolean;
}

const { height: WINDOW_HEIGHT } = Dimensions.get('window');
const TAB_BAR_HEIGHT = 80; // Hauteur approximative de la tab bar

export function BriefStack({ cards, pulseScore, loading, onRefresh, refreshing }: BriefStackProps) {
  const scrollY = useSharedValue(0);
  const scrollViewRef = useRef<any>(null);
  const lastCardIndex = useRef(0);
  const [containerHeight, setContainerHeight] = React.useState(WINDOW_HEIGHT - 100);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [navigatorVisible, setNavigatorVisible] = useState(true);
  const hideTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Mesurer la hauteur réelle du conteneur au runtime
  const handleLayout = useCallback((event: any) => {
    const { height } = event.nativeEvent.layout;
    if (height > 0) {
      setContainerHeight(height);
    }
  }, []);

  // Réinitialiser le timer d'auto-hide du navigator
  const resetHideTimer = useCallback(() => {
    setNavigatorVisible(true);
    
    if (hideTimerRef.current) {
      clearTimeout(hideTimerRef.current);
    }
    
    hideTimerRef.current = setTimeout(() => {
      setNavigatorVisible(false);
    }, 2000); // 2 secondes d'inactivité
  }, []);

  // Nettoyer le timer au démontage
  useEffect(() => {
    return () => {
      if (hideTimerRef.current) {
        clearTimeout(hideTimerRef.current);
      }
    };
  }, []);

  // Trigger haptic feedback au changement de carte
  const triggerHaptic = useCallback(() => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  }, []);

  // Update du currentCardIndex
  const updateCardIndex = useCallback((index: number) => {
    setCurrentCardIndex(index);
    resetHideTimer();
  }, [resetHideTimer]);

  // Handler de scroll avec détection de changement de carte
  const scrollHandler = useAnimatedScrollHandler({
    onScroll: (event) => {
      scrollY.value = event.contentOffset.y;
      
      // Détecter le changement de carte pour le haptic
      const currentCardIndex = Math.round(event.contentOffset.y / containerHeight);
      if (currentCardIndex !== lastCardIndex.current) {
        lastCardIndex.current = currentCardIndex;
        runOnJS(triggerHaptic)();
        runOnJS(updateCardIndex)(currentCardIndex);
      }
    },
  });

  // Fonction de navigation rapide (Quick-Jump)
  const handleNavigate = useCallback((index: number) => {
    if (scrollViewRef.current && containerHeight > 0) {
      scrollViewRef.current.scrollTo({
        y: index * containerHeight,
        animated: true,
      });
    }
  }, [containerHeight]);

  if (loading && cards.length === 0) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Calcul de votre Brief...</Text>
      </View>
    );
  }

  return (
    <View style={styles.wrapper} onLayout={handleLayout}>
      <Animated.ScrollView
        ref={scrollViewRef}
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        onScroll={scrollHandler}
        scrollEventThrottle={16}
        showsVerticalScrollIndicator={false}
        snapToInterval={containerHeight}
        decelerationRate="fast"
        snapToAlignment="start"
        disableIntervalMomentum={true}
        bounces={true}
        onTouchStart={resetHideTimer}
        refreshControl={
          onRefresh ? (
            <RefreshControl
              refreshing={refreshing || false}
              onRefresh={onRefresh}
              tintColor="#00FF41"
            />
          ) : undefined
        }
      >
        {/* Cartes Brief détaillées */}
        {cards.map((card, index) => {
          return (
            <AnimatedCardWrapper
              key={card.id}
              card={card}
              index={index}
              scrollY={scrollY}
              cardHeight={containerHeight}
            />
          );
        })}
      </Animated.ScrollView>

      {/* Bio-Navigator - Side indicator */}
      {cards.length > 0 && (
        <BriefNavigator
          cards={cards.map(card => ({
            id: card.id,
            iconName: card.iconName,
            state: card.state,
          }))}
          currentIndex={currentCardIndex}
          pulseScore={pulseScore}
          onNavigate={handleNavigate}
          visible={navigatorVisible}
        />
      )}
    </View>
  );
}

/**
 * Wrapper animé pour chaque carte
 * Gère l'entrée staggered
 */
interface AnimatedCardWrapperProps {
  card: BriefCardType;
  index: number;
  scrollY: Animated.SharedValue<number>;
  cardHeight: number;
  onAnimationComplete?: () => void;
}

function AnimatedCardWrapper({ card, index, scrollY, cardHeight, onAnimationComplete }: AnimatedCardWrapperProps) {
  // Animation d'entrée staggered uniquement (pas de parallaxe pour éviter les décalages)
  const entering = FadeInDown
    .delay(index * 150)
    .springify()
    .damping(12);

  return (
    <Animated.View
      entering={entering}
      style={[styles.fullScreenCard, { height: cardHeight }]}
    >
      <BriefCard {...card} index={index} />
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    flex: 1,
    backgroundColor: '#000000',
  },
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  contentContainer: {
    flexGrow: 1,
  },
  fullScreenCard: {
    width: '100%',
    justifyContent: 'center',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
    backgroundColor: '#000000',
  },
  loadingText: {
    color: '#8E8E93',
    fontSize: 16,
    fontWeight: '600',
  },
  energyCardWrapper: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 0,
  },
  swipeHint: {
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 24,
  },
  swipeHintText: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.4)',
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
});
