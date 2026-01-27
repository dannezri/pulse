import React, { useEffect } from 'react';
import { View, Text, StyleSheet, Dimensions, TouchableOpacity } from 'react-native';
import { BlurView } from 'expo-blur';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  runOnJS,
} from 'react-native-reanimated';
import { Camera } from 'lucide-react-native';
import { WhyPills } from './WhyPills';
import type { Anomaly } from '../services/ZScoreCalculator';

const { height: SCREEN_HEIGHT } = Dimensions.get('window');
const DRAWER_HEIGHT = SCREEN_HEIGHT * 0.6; // 60% de l'écran

interface BottomDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  anomalies: Anomaly[];
  insight: string;
}

export function BottomDrawer({ isOpen, onClose, anomalies, insight }: BottomDrawerProps) {
  const translateY = useSharedValue(DRAWER_HEIGHT);
  const opacity = useSharedValue(0);

  useEffect(() => {
    if (isOpen) {
      // Ouvrir le drawer
      translateY.value = withSpring(0, {
        damping: 25,
        stiffness: 200,
      });
      opacity.value = withTiming(1, { duration: 300 });
    } else {
      // Fermer le drawer
      translateY.value = withSpring(DRAWER_HEIGHT, {
        damping: 25,
        stiffness: 200,
      });
      opacity.value = withTiming(0, { duration: 200 });
    }
  }, [isOpen]);

  // Geste Pan pour swipe down
  const panGesture = Gesture.Pan()
    .onUpdate((event) => {
      // Permettre seulement le swipe vers le bas
      if (event.translationY > 0) {
        translateY.value = event.translationY;
      }
    })
    .onEnd((event) => {
      // Si swipe > 100px ou vélocité > 500, fermer
      if (event.translationY > 100 || event.velocityY > 500) {
        translateY.value = withSpring(DRAWER_HEIGHT);
        opacity.value = withTiming(0, { duration: 200 });
        runOnJS(onClose)();
      } else {
        // Sinon, revenir à la position ouverte
        translateY.value = withSpring(0);
      }
    });

  const animatedStyle = useAnimatedStyle(() => {
    return {
      transform: [{ translateY: translateY.value }],
    };
  });

  const backdropStyle = useAnimatedStyle(() => {
    return {
      opacity: opacity.value * 0.5,
    };
  });

  if (!isOpen && opacity.value === 0) {
    return null;
  }

  return (
    <>
      {/* Backdrop */}
      <Animated.View style={[styles.backdrop, backdropStyle]}>
        <TouchableOpacity 
          style={StyleSheet.absoluteFill} 
          onPress={onClose}
          activeOpacity={1}
        />
      </Animated.View>

      {/* Drawer */}
      <GestureDetector gesture={panGesture}>
        <Animated.View style={[styles.drawer, animatedStyle]}>
          <BlurView intensity={80} tint="dark" style={styles.blurContainer}>
            {/* Handle pour indiquer le swipe */}
            <View style={styles.handle} />

            {/* Contenu du drawer */}
            <View style={styles.content}>
              {/* One-Line Insight */}
              <Text style={styles.insightText}>{insight}</Text>

              {/* WhyPills : Top 3 anomalies */}
              {anomalies.length > 0 && (
                <View style={styles.pillsContainer}>
                  <Text style={styles.pillsTitle}>Pourquoi ?</Text>
                  <WhyPills anomalies={anomalies.slice(0, 3)} />
                </View>
              )}

              {/* Bouton Vision (placeholder) */}
              <TouchableOpacity 
                style={styles.visionButton}
                onPress={() => {
                  console.log('[BottomDrawer] Vision button pressed - Feature à venir');
                }}
                accessible
                accessibilityLabel="Scanner un repas avec la caméra"
                accessibilityHint="Fonctionnalité à venir"
                activeOpacity={0.8}
              >
                <Camera size={24} color="#FFFFFF" strokeWidth={2} />
                <Text style={styles.visionButtonText}>Scanner un repas</Text>
              </TouchableOpacity>
            </View>
          </BlurView>
        </Animated.View>
      </GestureDetector>
    </>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#000000',
    zIndex: 100,
  },
  drawer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: DRAWER_HEIGHT,
    zIndex: 101,
    borderTopLeftRadius: 32,
    borderTopRightRadius: 32,
    overflow: 'hidden',
  },
  blurContainer: {
    flex: 1,
    backgroundColor: 'rgba(28, 28, 30, 0.85)', // Glassmorphism
    borderTopLeftRadius: 32,
    borderTopRightRadius: 32,
    borderTopWidth: 1,
    borderLeftWidth: 1,
    borderRightWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  handle: {
    width: 40,
    height: 5,
    backgroundColor: '#8E8E93',
    borderRadius: 3,
    alignSelf: 'center',
    marginTop: 12,
    marginBottom: 20,
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    paddingBottom: 40,
  },
  insightText: {
    fontSize: 26,
    lineHeight: 36,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: -0.5,
    marginBottom: 32,
  },
  pillsContainer: {
    marginBottom: 32,
  },
  pillsTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#8E8E93',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 16,
  },
  visionButton: {
    position: 'absolute',
    bottom: 40,
    right: 24,
    backgroundColor: '#00FF41',
    borderRadius: 28,
    paddingVertical: 14,
    paddingHorizontal: 20,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    shadowColor: '#00FF41',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 16,
    elevation: 8,
  },
  visionButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});
