import React, { useEffect, useRef } from "react";
import { Animated, ViewStyle } from "react-native";

interface FadeInViewProps {
  children: React.ReactNode;
  delay?: number;
  duration?: number;
  style?: ViewStyle;
  useSpring?: boolean; // Utiliser spring pour un effet plus naturel
}

export function FadeInView({
  children,
  delay = 0,
  duration = 500,
  style,
  useSpring = false,
}: FadeInViewProps) {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const translateY = useRef(new Animated.Value(20)).current;
  const scale = useRef(new Animated.Value(0.95)).current;

  useEffect(() => {
    if (useSpring) {
      // Animation avec spring pour un effet plus naturel et fluide
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: duration * 0.8,
          delay,
          useNativeDriver: true,
        }),
        Animated.spring(translateY, {
          toValue: 0,
          delay,
          tension: 50,
          friction: 8,
          useNativeDriver: true,
        }),
        Animated.spring(scale, {
          toValue: 1,
          delay,
          tension: 50,
          friction: 8,
          useNativeDriver: true,
        }),
      ]).start();
    } else {
      // Animation timing classique
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration,
          delay,
          useNativeDriver: true,
        }),
        Animated.timing(translateY, {
          toValue: 0,
          duration,
          delay,
          useNativeDriver: true,
        }),
        Animated.timing(scale, {
          toValue: 1,
          duration,
          delay,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [fadeAnim, translateY, scale, delay, duration, useSpring]);

  return (
    <Animated.View
      style={[
        {
          opacity: fadeAnim,
          transform: [{ translateY }, { scale }],
        },
        style,
      ]}
    >
      {children}
    </Animated.View>
  );
}
