/**
 * BriefNavigator - Side Bio-Indicator
 * 
 * Navigation verticale discrète avec icônes synchronisées au scroll
 * - Auto-hide après 2 secondes d'inactivité
 * - Quick-jump vers chaque carte
 * - Indicateur de couleur basé sur le Pulse Score
 * - Animations fluides et haptic feedback
 */

import React, { useEffect, useMemo } from 'react';
import { View, StyleSheet, Pressable } from 'react-native';
import Animated, {
  useAnimatedStyle,
  withSpring,
  withTiming,
  useSharedValue,
} from 'react-native-reanimated';
import { BlurView } from 'expo-blur';
import * as Haptics from 'expo-haptics';
import * as Lucide from 'lucide-react-native';

interface BriefNavigatorProps {
  cards: Array<{
    id: string;
    iconName: string;
    state: 'optimal' | 'warning' | 'alert' | 'neutral';
  }>;
  currentIndex: number;
  pulseScore: number;
  onNavigate: (index: number) => void;
  visible: boolean;
}

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

export function BriefNavigator({
  cards,
  currentIndex,
  pulseScore,
  onNavigate,
  visible,
}: BriefNavigatorProps) {
  const opacity = useSharedValue(1);

  // Calculer le centrage vertical dynamiquement selon le nombre de cartes
  // Chaque dot fait 40px de hauteur + 18px de gap = 58px par carte
  // On centre en fonction du nombre total de cartes
  const centerOffset = useMemo(() => {
    const dotHeight = 40;
    const gap = 18;
    const padding = 28; // paddingVertical * 2
    const totalHeight = (cards.length * dotHeight) + ((cards.length - 1) * gap) + padding;
    return -(totalHeight / 2);
  }, [cards.length]);

  // Déterminer la couleur du thermomètre selon le Pulse Score
  const getScoreColor = () => {
    if (pulseScore >= 75) return '#34C759'; // Vert
    if (pulseScore >= 50) return '#FF9500'; // Orange
    return '#FF3B30'; // Rouge
  };

  // Animation de visibilité
  useEffect(() => {
    opacity.value = withTiming(visible ? 1 : 0, { duration: 300 });
  }, [visible, opacity]);

  const containerStyle = useAnimatedStyle(() => ({
    opacity: opacity.value,
  }), [opacity]);

  const handlePress = (index: number) => {
    Haptics.selectionAsync();
    onNavigate(index);
  };

  return (
    <Animated.View 
      style={[
        styles.container, 
        containerStyle,
        { transform: [{ translateY: centerOffset }] }
      ]} 
      pointerEvents={visible ? 'auto' : 'none'}
    >
      <BlurView intensity={20} tint="dark" style={styles.blurContainer}>
        <View style={styles.indicatorBar}>
          {cards.map((card, index) => {
            const isActive = index === currentIndex;
            const IconComponent = (Lucide as any)[card.iconName] || Lucide.Activity;
            
            // Couleur spéciale pour energy-overview et verdict
            let iconColor: string;
            if (card.id === 'energy-overview') {
              // Couleur basée sur l'état de l'energy overview
              if (card.state === 'optimal') {
                iconColor = isActive ? '#34C759' : 'rgba(52, 199, 89, 0.5)';
              } else if (card.state === 'warning') {
                iconColor = isActive ? '#FF9500' : 'rgba(255, 149, 0, 0.5)';
              } else if (card.state === 'alert') {
                iconColor = isActive ? '#FF3B30' : 'rgba(255, 59, 48, 0.5)';
              } else {
                iconColor = isActive ? '#8E8E93' : 'rgba(142, 142, 147, 0.5)';
              }
            } else if (card.id === 'verdict') {
              iconColor = getScoreColor();
            } else {
              iconColor = isActive ? '#FFFFFF' : 'rgba(255, 255, 255, 0.3)';
            }

            return (
              <NavigatorDot
                key={card.id}
                icon={IconComponent}
                color={iconColor}
                isActive={isActive}
                state={card.state}
                onPress={() => handlePress(index)}
              />
            );
          })}
        </View>
      </BlurView>
    </Animated.View>
  );
}

interface NavigatorDotProps {
  icon: any;
  color: string;
  isActive: boolean;
  state: 'optimal' | 'warning' | 'alert' | 'neutral';
  onPress: () => void;
}

function NavigatorDot({ icon: Icon, color, isActive, state, onPress }: NavigatorDotProps) {
  const scale = useSharedValue(1);
  const glowOpacity = useSharedValue(0);

  useEffect(() => {
    scale.value = withSpring(isActive ? 1.5 : 1, {
      damping: 12,
      stiffness: 300,
    });
    
    glowOpacity.value = withTiming(isActive ? 0.4 : 0, { duration: 200 });
  }, [isActive]);

  const animatedDotStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const animatedGlowStyle = useAnimatedStyle(() => ({
    opacity: glowOpacity.value,
  }));

  // Couleur du glow selon l'état
  const getGlowColor = () => {
    if (state === 'optimal') return 'rgba(52, 199, 89, 0.5)';
    if (state === 'alert') return 'rgba(255, 59, 48, 0.5)';
    if (state === 'warning') return 'rgba(255, 149, 0, 0.5)';
    return 'rgba(255, 255, 255, 0.3)';
  };

  return (
    <AnimatedPressable
      onPress={onPress}
      style={[styles.dotContainer, animatedDotStyle]}
    >
      {/* Glow effect pour la carte active */}
      <Animated.View
        style={[
          styles.glow,
          animatedGlowStyle,
          { backgroundColor: getGlowColor() },
        ]}
      />
      
      {/* Icône */}
      <Icon
        size={isActive ? 20 : 15}
        color={color}
        strokeWidth={isActive ? 3 : 2}
      />
    </AnimatedPressable>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    right: 10,
    top: '50%',
    zIndex: 100,
  },
  blurContainer: {
    borderRadius: 20,
    overflow: 'hidden',
    backgroundColor: 'rgba(28, 28, 30, 0.5)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.05)',
  },
  indicatorBar: {
    paddingVertical: 14,
    paddingHorizontal: 10,
    gap: 18,
  },
  dotContainer: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  glow: {
    position: 'absolute',
    width: 36,
    height: 36,
    borderRadius: 18,
  },
});
