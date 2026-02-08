/**
 * BriefCard Component - Style "Modern Stack" Samsung/Apple
 * 
 * Design Premium:
 * - Halos de couleur (LinearGradient) en fond selon l'état
 * - Hiérarchie visuelle: Icône/Titre → Score énorme → Description → Action Pill
 * - Effet de profondeur avec shadows et bordure fine en verre sombre
 * - Pulsation rouge pour l'état alert
 * - Tap effect avec spring (scale 0.97)
 */

import React from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import Animated, { useSharedValue, useAnimatedStyle, withSpring } from 'react-native-reanimated';
import { LinearGradient } from 'expo-linear-gradient';
import * as Haptics from 'expo-haptics';
import * as Lucide from 'lucide-react-native';
import { BriefCard as BriefCardType } from '../types/brief';

interface BriefCardProps extends BriefCardType {
  index?: number;
  onPress?: () => void;
}

/**
 * Parse le texte Markdown (gras uniquement) et retourne un tableau de composants Text
 * Exemple: "Ceci est **gras** et normal" → [Text("Ceci est "), Text("gras" bold), Text(" et normal")]
 */
function parseMarkdownText(text: string, baseStyle: any): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  const regex = /\*\*(.*?)\*\*/g;
  let lastIndex = 0;
  let match;
  let key = 0;

  while ((match = regex.exec(text)) !== null) {
    // Texte avant le gras
    if (match.index > lastIndex) {
      parts.push(
        <Text key={`text-${key++}`} style={baseStyle}>
          {text.substring(lastIndex, match.index)}
        </Text>
      );
    }
    
    // Texte en gras
    parts.push(
      <Text key={`bold-${key++}`} style={[baseStyle, { fontWeight: '700' }]}>
        {match[1]}
      </Text>
    );
    
    lastIndex = regex.lastIndex;
  }

  // Texte après le dernier gras
  if (lastIndex < text.length) {
    parts.push(
      <Text key={`text-${key++}`} style={baseStyle}>
        {text.substring(lastIndex)}
      </Text>
    );
  }

  return parts.length > 0 ? parts : [<Text key="default" style={baseStyle}>{text}</Text>];
}

// Styles pour les halos de couleur selon l'état (opacité réduite pour confort visuel)
const stateStyles = {
  optimal: {
    glow: ['rgba(52, 199, 89, 0.12)', 'transparent'], // Vert subtil
    accent: '#34C759',
  },
  warning: {
    glow: ['rgba(255, 149, 0, 0.15)', 'transparent'], // Orange doux
    accent: '#FF9500',
  },
  alert: {
    glow: ['rgba(255, 59, 48, 0.15)', 'transparent'], // Rouge atténué
    accent: '#FF3B30',
  },
  neutral: {
    glow: ['rgba(142, 142, 147, 0.10)', 'transparent'], // Gris très subtil
    accent: '#8E8E93',
  }
};

export function BriefCard(props: BriefCardProps) {
  const {
    type,
    title,
    content,
    state,
    iconName,
    badge,
    badgeUnit = '%', // Par défaut "%"
    onPress,
    actionButton,
    headerText,
  } = props;

  // Animation de scale au toucher (effet premium)
  const scale = useSharedValue(1);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  // Handlers pour l'interaction tactile
  const handlePressIn = () => {
    scale.value = withSpring(0.96, {
      damping: 15,
      stiffness: 300,
    });
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  };

  const handlePressOut = () => {
    scale.value = withSpring(1, {
      damping: 15,
      stiffness: 300,
    });
  };

  // Obtenir l'icône
  const IconComponent = (Lucide as any)[iconName] || Lucide.Activity;
  
  // Styles pour l'état actuel (avec fallback sur 'neutral' si state invalide)
  const currentStateStyle = stateStyles[state] || stateStyles.neutral;

  // Limiter le contenu à 10 lignes maximum (environ 550 caractères)
  // L'IA est contrainte à 500 caractères, on garde une marge
  const shortContent = content.length > 550 ? content.substring(0, 547) + '...' : content;

  return (
    <Pressable
      onPress={onPress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      accessible
      accessibilityRole={onPress ? 'button' : 'text'}
      accessibilityLabel={`Carte ${title}: ${content}`}
      style={{ flex: 1 }}
    >
      <Animated.View style={[{ flex: 1 }, animatedStyle]}>
        <View style={styles.cardContainer}>
            {/* Halo de couleur en fond (top-right) */}
            <LinearGradient
              colors={currentStateStyle.glow}
              start={{ x: 0.5, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={styles.glowEffect}
            />

            {/* Header Text optionnel (date + prénom) */}
            {headerText && (
              <Text style={styles.headerText}>{headerText}</Text>
            )}

            {/* Header: Icône + Titre en petites capitales */}
            <View style={styles.header}>
              <View style={[styles.iconCircle, { backgroundColor: `${currentStateStyle.accent}20` }]}>
                <IconComponent 
                  size={24} 
                  color={currentStateStyle.accent} 
                  strokeWidth={3}
                />
              </View>
              <Text style={styles.categoryTitle}>{type.toUpperCase()}</Text>
            </View>

            {/* Spacer pour centrer le contenu */}
            <View style={{ flex: 1 }} />

            {/* Contenu principal centré */}
            <View style={styles.contentCenter}>
              {/* Score énorme comme point focal */}
              {badge !== undefined && (
                <View style={styles.scoreRow}>
                  <Text style={[styles.scoreText, { color: currentStateStyle.accent }]}>
                    {badge}
                  </Text>
                  <Text style={styles.unitText}>{badgeUnit}</Text>
                </View>
              )}

              {/* Titre principal */}
              <Text style={styles.mainTitle} numberOfLines={3}>
                {parseMarkdownText(title, styles.mainTitle)}
              </Text>

              {/* Description pédagogique (10 lignes max) */}
              <Text style={styles.description} numberOfLines={10}>
                {parseMarkdownText(shortContent, styles.description)}
              </Text>
            </View>

            {/* Spacer pour pousser le bouton en bas */}
            <View style={{ flex: 1 }} />

            {/* Action button en bas */}
            {actionButton && (
              <Pressable
                style={[styles.actionPill, { borderColor: currentStateStyle.accent, borderWidth: 2 }]}
                onPress={actionButton.onPress}
              >
                <Text style={[styles.actionText, { color: currentStateStyle.accent }]}>
                  {actionButton.label}
                </Text>
              </Pressable>
            )}
          </View>
        </Animated.View>
      </Pressable>
  );
}

const styles = StyleSheet.create({
  cardContainer: {
    flex: 1,
    backgroundColor: '#000000',
    borderRadius: 0,
    paddingLeft: 24,
    paddingRight: 90, // Espace augmenté pour le Bio-Navigator à droite
    paddingTop: 40,
    paddingBottom: 100, // Augmenté pour éviter que la tab bar masque le contenu
    borderWidth: 0,
    overflow: 'hidden',
    justifyContent: 'flex-start',
  },
  glowEffect: {
    position: 'absolute',
    top: 0,
    right: 0,
    width: 300,
    height: 300,
    borderRadius: 150,
  },
  headerText: {
    fontSize: 15,
    color: '#8E8E93',
    fontWeight: '600',
    marginBottom: 20,
    textTransform: 'capitalize',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 0,
  },
  contentCenter: {
    alignItems: 'flex-start',
  },
  iconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  categoryTitle: {
    fontSize: 12,
    fontWeight: '800',
    color: 'rgba(255, 255, 255, 0.6)',
    letterSpacing: 2,
    textTransform: 'uppercase',
  },
  scoreRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 24,
  },
  scoreText: {
    fontSize: 96,
    fontWeight: '900',
    letterSpacing: -4,
  },
  unitText: {
    fontSize: 36,
    color: 'rgba(255, 255, 255, 0.5)',
    marginLeft: 8,
    fontWeight: '700',
  },
  mainTitle: {
    fontSize: 36,
    fontWeight: '800',
    color: '#FFFFFF',
    marginBottom: 20,
    letterSpacing: -1,
    lineHeight: 42,
  },
  description: {
    fontSize: 16,
    lineHeight: 24,
    color: 'rgba(255, 255, 255, 0.8)',
    letterSpacing: -0.3,
  },
  actionPill: {
    backgroundColor: 'rgba(255, 255, 255, 0.12)',
    alignSelf: 'flex-start',
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: 30,
    marginTop: 20,
  },
  actionText: {
    fontSize: 15,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
});
