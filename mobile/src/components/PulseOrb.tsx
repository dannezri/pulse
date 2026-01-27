import React, { useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  withRepeat,
  withSpring,
  Easing,
  interpolate,
} from 'react-native-reanimated';
import { LinearGradient } from 'expo-linear-gradient';
import type { GlobalState } from '../services/ZScoreCalculator';

interface PulseOrbProps {
  state: GlobalState;
  size?: number;
}

const STATE_COLORS = {
  calm: {
    start: '#34C759', // Vert iOS
    end: '#30D158',   // Vert plus clair
    shadow: '#34C759',
  },
  warning: {
    start: '#FF9500', // Orange iOS
    end: '#FFB340',   // Orange plus clair
    shadow: '#FF9500',
  },
  alert: {
    start: '#FF3B30', // Rouge iOS
    end: '#FF6259',   // Rouge plus clair
    shadow: '#FF3B30',
  },
};

const STATE_DURATIONS = {
  calm: 3000,    // Pulse lent et fluide
  warning: 1500, // Pulse erratique (plus rapide)
  alert: 4000,   // Pulse lent/statique
};

export function PulseOrb({ state, size = 140 }: PulseOrbProps) {
  // Animation de scale (pulsation)
  const scale = useSharedValue(1);
  // Animation de rotation (pour l'effet erratique en warning)
  const rotation = useSharedValue(0);
  // Animation d'opacité pour transition
  const opacity = useSharedValue(1);

  const colors = STATE_COLORS[state];
  const duration = STATE_DURATIONS[state];

  useEffect(() => {
    // Reset animations
    scale.value = 1;
    rotation.value = 0;

    if (state === 'calm') {
      // Pulse lent et fluide (calm)
      scale.value = withRepeat(
        withSpring(1.1, {
          damping: 10,
          stiffness: 50,
        }),
        -1,
        true
      );
    } else if (state === 'warning') {
      // Pulse erratique (warning)
      scale.value = withRepeat(
        withTiming(1.15, {
          duration: duration,
          easing: Easing.bezier(0.25, 0.1, 0.25, 1),
        }),
        -1,
        true
      );
      
      // Ajouter une légère rotation pour l'effet erratique
      rotation.value = withRepeat(
        withTiming(360, {
          duration: duration * 2,
          easing: Easing.linear,
        }),
        -1,
        false
      );
    } else if (state === 'alert') {
      // Pulse lent/statique (alert)
      scale.value = withRepeat(
        withTiming(1.05, {
          duration: duration,
          easing: Easing.ease,
        }),
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
      opacity: opacity.value,
    };
  });

  const shadowAnimatedStyle = useAnimatedStyle(() => {
    // Shadow qui pulse également
    const shadowRadius = interpolate(scale.value, [1, 1.2], [20, 40]);
    const shadowOpacity = interpolate(scale.value, [1, 1.2], [0.3, 0.6]);

    return {
      shadowRadius,
      shadowOpacity,
    };
  });

  // Message d'accessibilité descriptif
  const accessibilityLabel = 
    state === 'calm' 
      ? "État de santé optimal. Votre corps est en équilibre."
      : state === 'warning'
      ? "État de santé nécessitant attention. Des anomalies ont été détectées."
      : "État de santé en alerte. Repos recommandé.";

  return (
    <View 
      style={styles.container} 
      accessible 
      accessibilityLabel={accessibilityLabel}
      accessibilityRole="image"
      accessibilityHint="Indicateur visuel de votre état de santé basé sur vos métriques physiologiques"
    >
      <Animated.View style={[styles.orb, animatedStyle, shadowAnimatedStyle, {
        width: size,
        height: size,
        borderRadius: size / 2,
        shadowColor: colors.shadow,
      }]}>
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
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  orb: {
    shadowOffset: { width: 0, height: 0 },
    elevation: 8,
  },
  gradient: {
    overflow: 'hidden',
  },
});
