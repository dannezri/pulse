import React, { useEffect } from 'react';
import { StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming,
  withSpring,
  Easing,
} from 'react-native-reanimated';
import type { GlobalState } from '../services/ZScoreCalculator';

interface PulseOrbOrganicProps {
  state: GlobalState;
  size?: number;
  onTap?: () => void;
}

const STATE_COLORS = {
  calm: {
    start: '#00FF41', // Vert Électrique
    end: '#34C759',   // Vert iOS
  },
  warning: {
    start: '#FF9500', // Orange Ambre
    end: '#FFB340',   // Orange plus clair
  },
  alert: {
    start: '#FF3B30', // Rouge Système
    end: '#FF6259',   // Rouge plus clair
  },
};

const STATE_DURATIONS = {
  calm: 3000,    // Pulse lent et fluide
  warning: 1000, // Vibrations rapides
  alert: 4000,   // Pulse lent/statique
};

export function PulseOrbOrganic({ state, size = 150, onTap }: PulseOrbOrganicProps) {
  // Scale pour la pulsation
  const scale = useSharedValue(1);
  
  // Rotation pour l'effet erratique
  const rotation = useSharedValue(0);
  
  // Opacité pour le glow
  const glowOpacity = useSharedValue(0.3);
  
  const colors = STATE_COLORS[state];
  const duration = STATE_DURATIONS[state];

  useEffect(() => {
    // Reset
    scale.value = 1;
    rotation.value = 0;
    
    if (state === 'calm') {
      // Pulsation lente et fluide
      scale.value = withRepeat(
        withSpring(1.1, {
          damping: 12,
          stiffness: 40,
        }),
        -1,
        true
      );
      
      glowOpacity.value = withRepeat(
        withTiming(0.6, { duration: duration, easing: Easing.inOut(Easing.ease) }),
        -1,
        true
      );
      
    } else if (state === 'warning') {
      // Vibrations rapides et erratiques
      scale.value = withRepeat(
        withTiming(1.15, {
          duration: duration,
          easing: Easing.bezier(0.25, 0.1, 0.25, 1),
        }),
        -1,
        true
      );
      
      // Rotation rapide pour l'effet erratique
      rotation.value = withRepeat(
        withTiming(360, {
          duration: duration * 3,
          easing: Easing.linear,
        }),
        -1,
        false
      );
      
      glowOpacity.value = withRepeat(
        withTiming(0.8, { duration: duration, easing: Easing.linear }),
        -1,
        true
      );
      
    } else if (state === 'alert') {
      // Contraction, forme plus petite et statique
      scale.value = withTiming(0.85, {
        duration: 1000,
        easing: Easing.out(Easing.ease),
      });
      
      glowOpacity.value = withRepeat(
        withTiming(0.4, { duration: duration, easing: Easing.inOut(Easing.ease) }),
        -1,
        true
      );
    }
  }, [state, duration]);

  const animatedStyle = useAnimatedStyle(() => {
    return {
      transform: [
        { scale: scale.value },
        { rotate: `${rotation.value}deg` },
      ],
    };
  });

  const glowStyle = useAnimatedStyle(() => {
    return {
      opacity: glowOpacity.value,
    };
  });

  // Message d'accessibilité
  const accessibilityLabel = 
    state === 'calm' 
      ? "État de santé optimal. Votre corps est en équilibre."
      : state === 'warning'
      ? "État de santé nécessitant attention. Des anomalies ont été détectées."
      : "État de santé en alerte. Repos recommandé.";

  return (
    <Animated.View 
      style={[styles.container, { width: size, height: size }]}
      accessible
      accessibilityLabel={accessibilityLabel}
      accessibilityRole="image"
      accessibilityHint="Appuyez pour voir les détails, pincez pour voir tous les critères"
    >
      {/* Glow effect (outer) */}
      <Animated.View style={[styles.glow, glowStyle, {
        width: size * 1.4,
        height: size * 1.4,
        borderRadius: (size * 1.4) / 2,
        backgroundColor: colors.start,
      }]} />
      
      {/* Main Orb */}
      <Animated.View style={[animatedStyle, { width: size, height: size }]}>
        <LinearGradient
          colors={[colors.start, colors.end]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={[styles.gradient, {
            width: size,
            height: size,
            borderRadius: size / 2,
          }]}
        />
      </Animated.View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  glow: {
    position: 'absolute',
    opacity: 0.3,
    shadowRadius: 30,
    shadowOpacity: 0.6,
    elevation: 8,
  },
  gradient: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.4,
    shadowRadius: 20,
    elevation: 10,
  },
});
