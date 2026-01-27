import React, { useEffect } from 'react';
import { ViewStyle } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  withSpring,
  Easing,
} from 'react-native-reanimated';

interface AnimatedTransitionProps {
  children: React.ReactNode;
  visible: boolean;
  duration?: number;
  delay?: number;
  style?: ViewStyle;
  type?: 'fade' | 'slide' | 'scale';
}

/**
 * Composant générique pour les transitions animées
 * Utilisé pour améliorer l'UX avec des animations fluides
 */
export function AnimatedTransition({
  children,
  visible,
  duration = 300,
  delay = 0,
  style,
  type = 'fade',
}: AnimatedTransitionProps) {
  const opacity = useSharedValue(visible ? 1 : 0);
  const translateY = useSharedValue(visible ? 0 : 20);
  const scale = useSharedValue(visible ? 1 : 0.9);

  useEffect(() => {
    const timeout = setTimeout(() => {
      if (type === 'fade') {
        opacity.value = withTiming(visible ? 1 : 0, {
          duration,
          easing: Easing.bezier(0.25, 0.1, 0.25, 1),
        });
      } else if (type === 'slide') {
        opacity.value = withTiming(visible ? 1 : 0, { duration });
        translateY.value = withSpring(visible ? 0 : 20, {
          damping: 15,
          stiffness: 100,
        });
      } else if (type === 'scale') {
        opacity.value = withTiming(visible ? 1 : 0, { duration });
        scale.value = withSpring(visible ? 1 : 0.9, {
          damping: 12,
          stiffness: 80,
        });
      }
    }, delay);

    return () => clearTimeout(timeout);
  }, [visible, duration, delay, type]);

  const animatedStyle = useAnimatedStyle(() => {
    if (type === 'slide') {
      return {
        opacity: opacity.value,
        transform: [{ translateY: translateY.value }],
      };
    } else if (type === 'scale') {
      return {
        opacity: opacity.value,
        transform: [{ scale: scale.value }],
      };
    }
    return {
      opacity: opacity.value,
    };
  });

  return (
    <Animated.View style={[style, animatedStyle]}>
      {children}
    </Animated.View>
  );
}
