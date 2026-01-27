import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  runOnJS,
} from 'react-native-reanimated';
import { PulseOrbOrganic } from './PulseOrbOrganic';
import type { GlobalState } from '../services/ZScoreCalculator';

interface GestureOrbWrapperProps {
  state: GlobalState;
  size?: number;
  onTap?: () => void;
  onPinch?: () => void;
}

export function GestureOrbWrapper({ 
  state, 
  size = 150, 
  onTap,
  onPinch,
}: GestureOrbWrapperProps) {
  // Valeurs partagées pour les animations
  const scale = useSharedValue(1);
  const savedScale = useSharedValue(1);

  // Geste Tap
  const tapGesture = Gesture.Tap()
    .onStart(() => {
      // Feedback visuel : scale down
      scale.value = withSpring(0.95, {
        damping: 15,
        stiffness: 300,
      });
    })
    .onEnd(() => {
      // Retour à la normale
      scale.value = withSpring(1, {
        damping: 15,
        stiffness: 300,
      });
      
      // Déclencher le callback
      if (onTap) {
        runOnJS(onTap)();
      }
    })
    .onFinalize(() => {
      // Assurer le retour à la normale même si annulé
      scale.value = withSpring(1);
    });

  // Geste Pinch
  const pinchGesture = Gesture.Pinch()
    .onStart(() => {
      savedScale.value = scale.value;
    })
    .onUpdate((event) => {
      // Appliquer le scale du pinch (limité entre 0.5 et 2)
      const newScale = savedScale.value * event.scale;
      scale.value = Math.min(Math.max(newScale, 0.5), 2);
    })
    .onEnd((event) => {
      // Si le pinch est significatif (> 1.3x), déclencher l'action
      if (event.scale > 1.3 && onPinch) {
        runOnJS(onPinch)();
      }
      
      // Retour à la normale
      scale.value = withSpring(1, {
        damping: 15,
        stiffness: 200,
      });
      savedScale.value = 1;
    })
    .onFinalize(() => {
      // Assurer le retour à la normale
      scale.value = withSpring(1);
      savedScale.value = 1;
    });

  // Composer les gestes (pinch a priorité sur tap)
  const composedGesture = Gesture.Simultaneous(pinchGesture, tapGesture);

  // Style animé pour le feedback
  const animatedStyle = useAnimatedStyle(() => {
    return {
      transform: [{ scale: scale.value }],
    };
  });

  return (
    <GestureDetector gesture={composedGesture}>
      <Animated.View style={[styles.container, animatedStyle]}>
        <PulseOrbOrganic state={state} size={size} />
      </Animated.View>
    </GestureDetector>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
});
