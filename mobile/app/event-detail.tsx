import React, { useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useLocalSearchParams, useRouter, Stack } from 'expo-router';
import { useAuth } from '../src/hooks/useAuth';
import { useReadinessScore } from '../src/hooks/useReadinessScore';
import { useEventAnalysis } from '../src/hooks/useEventAnalysis';
import { CalendarEvent } from '../src/hooks/useCalendarEvents';
import { ChevronLeft, RefreshCw, CheckCircle, AlertTriangle, AlertCircle } from 'lucide-react-native';
import Markdown, { MarkdownIt } from 'react-native-markdown-display';
import Animated, { FadeInDown, FadeIn } from 'react-native-reanimated';

/**
 * Formate un timestamp en "il y a X min/heures"
 */
function getTimeAgo(timestamp: string): string {
  const now = new Date();
  const analyzed = new Date(timestamp);
  const diffMs = now.getTime() - analyzed.getTime();
  const diffMinutes = Math.floor(diffMs / 60000);
  
  if (diffMinutes < 1) return 'à l\'instant';
  if (diffMinutes === 1) return '1 min';
  if (diffMinutes < 60) return `${diffMinutes} min`;
  
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours === 1) return '1 heure';
  if (diffHours < 24) return `${diffHours} heures`;
  
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays === 1) return '1 jour';
  return `${diffDays} jours`;
}

/**
 * Formate une date en "15 jan à 10h00"
 */
function formatDate(timestamp: string): string {
  const date = new Date(timestamp);
  const day = date.getDate();
  const month = date.toLocaleDateString('fr-FR', { month: 'short' });
  const time = date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  return `${day} ${month} à ${time}`;
}

/**
 * Détecte le niveau d'urgence d'une blockquote basé sur son contenu
 */
function detectUrgencyLevel(text: string): 'urgent' | 'warning' | 'ok' {
  const lowerText = text.toLowerCase();
  
  // Mots-clés d'urgence critique
  const urgentKeywords = [
    '🔴', 'urgent', 'immédiat', 'critique', 'danger', 'risque élevé',
    'annule', 'éviter', 'ne pas', 'interdit', 'blessure', 'hypoglycémie'
  ];
  
  // Mots-clés de vigilance
  const warningKeywords = [
    '🟡', 'attention', 'vigilance', 'surveille', 'prudence', 'modéré',
    'pendant', 'si tu décides', 'écoute ton corps'
  ];
  
  // Mots-clés positifs
  const okKeywords = [
    '🟢', 'ok', 'optimal', 'bon', 'excellent', 'prêt', 'go',
    'après', 'récupération', 'alternative'
  ];
  
  // Vérifier urgent en premier (priorité haute)
  if (urgentKeywords.some(keyword => lowerText.includes(keyword))) {
    return 'urgent';
  }
  
  // Puis vérifier OK (recommandations positives)
  if (okKeywords.some(keyword => lowerText.includes(keyword))) {
    return 'ok';
  }
  
  // Par défaut, vigilance
  if (warningKeywords.some(keyword => lowerText.includes(keyword))) {
    return 'warning';
  }
  
  // Détection par position : "Avant" = urgent, "Après" = ok
  if (lowerText.includes('avant')) return 'urgent';
  if (lowerText.includes('après') || lowerText.includes('alternative')) return 'ok';
  
  return 'warning'; // Défaut
}

/**
 * Retourne les couleurs selon le niveau d'urgence
 */
function getUrgencyColors(level: 'urgent' | 'warning' | 'ok'): {
  borderColor: string;
  shadowColor: string;
  backgroundColor: string;
} {
  switch (level) {
    case 'urgent':
      return {
        borderColor: '#FF3B30', // Rouge iOS
        shadowColor: '#FF3B30',
        backgroundColor: '#1C1C1E',
      };
    case 'warning':
      return {
        borderColor: '#FF9500', // Orange iOS
        shadowColor: '#FF9500',
        backgroundColor: '#1C1C1E',
      };
    case 'ok':
      return {
        borderColor: '#34C759', // Vert iOS
        shadowColor: '#34C759',
        backgroundColor: '#1C1C1E',
      };
  }
}

export default function EventDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const { userId } = useAuth();
  
  // Reconstruire l'événement depuis les params
  const event: CalendarEvent = {
    id: params.eventId as string,
    title: params.eventTitle as string,
    startDate: new Date(params.eventStart as string),
    endDate: new Date(params.eventEnd as string),
    location: params.eventLocation as string || undefined,
    notes: params.eventNotes as string || undefined,
  };

  const { data: readinessScore } = useReadinessScore(userId);
  const { mutate, data: analysisData, isLoading, error } = useEventAnalysis(userId, event);

  // Lancer l'analyse automatiquement au montage du composant
  useEffect(() => {
    if (userId && event) {
      mutate({ forceRefresh: false });
    }
  }, [userId, event?.id]);

  // Handler pour forcer une nouvelle analyse
  const handleForceRefresh = () => {
    mutate({ forceRefresh: true });
  };

  // Calculer le badge de probabilité de succès
  const getSuccessBadge = () => {
    if (!readinessScore) return null;
    
    const score = readinessScore.totalScore;
    
    if (score >= 80) {
      return {
        text: 'Feu vert pour cet événement',
        emoji: '🟢',
        icon: CheckCircle,
        color: '#34C759',
        backgroundColor: '#1C3A2E',
      };
    } else if (score >= 60) {
      return {
        text: 'Événement faisable (vigilance requise)',
        emoji: '🟡',
        icon: AlertTriangle,
        color: '#FF9500',
        backgroundColor: '#3A2E1C',
      };
    } else {
      return {
        text: 'Événement à risque (Impact Fatigue)',
        emoji: '🔴',
        icon: AlertCircle,
        color: '#FF3B30',
        backgroundColor: '#3A1C1E',
      };
    }
  };

  const successBadge = getSuccessBadge();

  // Styles Markdown "Pulse Bubbles" - Apple Health Style amélioré
  const markdownStyles = {
    body: {
      color: '#FFFFFF',
      fontSize: 15,
      lineHeight: 22,
    },
    heading1: {
      color: '#34C759', // Vert Pulse pour les titres principaux
      fontSize: 22,
      fontWeight: '700' as '700',
      marginTop: 20,
      marginBottom: 10,
      letterSpacing: -0.5,
    },
    heading2: {
      color: '#FF9500', // Orange Attention pour les sections importantes
      fontSize: 18,
      fontWeight: '600' as '600',
      marginTop: 15,
      marginBottom: 8,
    },
    heading3: {
      color: '#FFFFFF',
      fontSize: 16,
      fontWeight: '600' as '600',
      marginTop: 12,
      marginBottom: 6,
    },
    strong: {
      color: '#34C759', // Le gras ressort en vert pour la pédagogie
      fontWeight: '700' as '700',
    },
    em: {
      color: '#8E8E93',
      fontStyle: 'italic' as 'italic',
    },
    text: {
      color: '#FFFFFF',
    },
    bullet_list: {
      marginVertical: 10,
    },
    ordered_list: {
      marginVertical: 10,
    },
    list_item: {
      marginBottom: 8,
    },
    bullet_list_icon: {
      color: '#34C759',
      fontSize: 18,
      marginRight: 8,
    },
    bullet_list_content: {
      color: '#FFFFFF',
      flex: 1,
    },
    ordered_list_content: {
      color: '#FFFFFF',
      flex: 1,
    },
    code_inline: {
      backgroundColor: '#2C2C2E',
      color: '#34C759',
      paddingHorizontal: 6,
      paddingVertical: 2,
      borderRadius: 4,
      fontFamily: 'Courier',
      fontSize: 14,
    },
    fence: {
      backgroundColor: '#2C2C2E',
      borderRadius: 12,
      padding: 16,
      marginVertical: 12,
    },
    code_block: {
      color: '#34C759',
      fontFamily: 'Courier',
      fontSize: 13,
      lineHeight: 20,
    },
    // Bulles d'alerte "Pulse" - Styles de base (override par renderer)
    blockquote: {
      backgroundColor: '#1C1C1E',
      borderLeftWidth: 4,
      borderLeftColor: '#FF3B30',
      borderRadius: 12,
      paddingHorizontal: 16,
      paddingVertical: 12,
      marginVertical: 15,
    },
    paragraph: {
      marginTop: 8,
      marginBottom: 8,
      color: '#FFFFFF',
      lineHeight: 22,
    },
    link: {
      color: '#0A84FF', // Bleu iOS
      textDecorationLine: 'underline' as 'underline',
    },
    hr: {
      backgroundColor: '#3A3A3C',
      height: 1,
      marginVertical: 16,
    },
  };

  // Renderer personnalisé pour les blockquotes avec couleurs dynamiques et animations
  const renderRules = {
    blockquote: (node: any, children: any, parent: any, styles: any, inheritedStyles: any = {}) => {
      // Extraire le texte de la blockquote pour détecter l'urgence
      const extractText = (node: any): string => {
        if (typeof node === 'string') return node;
        if (node.content) return node.content;
        if (Array.isArray(node.children)) {
          return node.children.map(extractText).join(' ');
        }
        return '';
      };
      
      const blockquoteText = extractText(node);
      const urgencyLevel = detectUrgencyLevel(blockquoteText);
      const colors = getUrgencyColors(urgencyLevel);
      
      // Index unique pour l'animation décalée
      const blockquoteIndex = parent?.children?.indexOf(node) || 0;
      
      return (
        <Animated.View
          key={node.key}
          entering={FadeInDown.duration(400).delay(blockquoteIndex * 100)}
          style={[
            styles.blockquote,
            {
              borderLeftColor: colors.borderColor,
              backgroundColor: colors.backgroundColor,
              shadowColor: colors.shadowColor,
              shadowOffset: { width: 0, height: 2 },
              shadowOpacity: 0.25,
              shadowRadius: 10,
              elevation: 5, // Pour Android
            },
          ]}
        >
          {children}
        </Animated.View>
      );
    },
  };

  return (
    <>
      <Stack.Screen
        options={{
          headerShown: true,
          headerTitle: 'Analyse IA',
          headerStyle: {
            backgroundColor: '#000000',
          },
          headerTintColor: '#FFFFFF',
          headerLeft: () => (
            <TouchableOpacity onPress={() => router.back()}>
              <ChevronLeft size={24} color="#FFFFFF" />
            </TouchableOpacity>
          ),
          headerRight: () => (
            <TouchableOpacity 
              onPress={handleForceRefresh}
              disabled={isLoading}
            >
              <RefreshCw 
                size={20} 
                color={isLoading ? '#8E8E93' : '#34C759'} 
              />
            </TouchableOpacity>
          ),
        }}
      />
      
      <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
        {/* Badge de Probabilité de Succès */}
        {successBadge && (
          <View style={[styles.successBadge, { backgroundColor: successBadge.backgroundColor, borderColor: successBadge.color }]}>
            <successBadge.icon size={24} color={successBadge.color} />
            <View style={styles.badgeTextContainer}>
              <Text style={[styles.badgeText, { color: successBadge.color }]}>
                {successBadge.emoji} {successBadge.text}
              </Text>
              <Text style={styles.badgeSubtext}>
                Score de Readiness: {readinessScore?.totalScore}%
              </Text>
            </View>
          </View>
        )}

        {/* En-tête événement */}
        <View style={styles.eventHeader}>
          <Text style={styles.eventTitle}>{event.title}</Text>
          <Text style={styles.eventTime}>
            {event.startDate.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
            {' - '}
            {event.endDate.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
          </Text>
          {event.location && (
            <Text style={styles.eventLocation}>{event.location}</Text>
          )}
        </View>

        {/* État de chargement */}
        {isLoading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#34C759" />
            <Text style={styles.loadingText}>L'IA analyse votre état biologique...</Text>
            <Text style={styles.loadingSubtext}>Cela peut prendre quelques secondes</Text>
          </View>
        )}

        {/* Erreur */}
        {error && !isLoading && (
          <View style={styles.errorContainer}>
            <AlertCircle size={48} color="#FF3B30" />
            <Text style={styles.errorTitle}>Erreur d'analyse</Text>
            <Text style={styles.errorText}>
              {error instanceof Error ? error.message : 'Une erreur est survenue'}
            </Text>
            <TouchableOpacity 
              style={styles.retryButton}
              onPress={handleForceRefresh}
            >
              <RefreshCw size={16} color="#FFFFFF" />
              <Text style={styles.retryButtonText}>Réessayer</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Analyse IA en Markdown */}
        {analysisData && !isLoading && !error && (
          <>
            <View style={styles.analysisContainer}>
              <Markdown style={markdownStyles} rules={renderRules}>
                {analysisData.insight}
              </Markdown>
            </View>

            {/* Footer avec timestamp et indicateur de cache */}
            <View style={styles.timestampContainer}>
              <Text style={styles.timestampText}>
                {analysisData.cached && '💾 '}
                Analysé il y a {getTimeAgo(analysisData.analyzed_at)}
                {analysisData.cached && ' (Cache)'}
              </Text>
              <Text style={styles.timestampSubtext}>
                Basé sur vos données du {formatDate(analysisData.biometrics_ref_at)}
              </Text>
            </View>

            {/* Bouton "Recalculer" discret */}
            <TouchableOpacity 
              style={styles.recalculateButton}
              onPress={handleForceRefresh}
              disabled={isLoading}
            >
              <RefreshCw size={14} color="#8E8E93" />
              <Text style={styles.recalculateText}>🔄 Recalculer</Text>
            </TouchableOpacity>
          </>
        )}

        <View style={styles.bottomSpacer} />
      </ScrollView>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  contentContainer: {
    padding: 20,
  },
  successBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 16,
    marginBottom: 20,
    borderWidth: 2,
  },
  badgeTextContainer: {
    marginLeft: 12,
    flex: 1,
  },
  badgeText: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 4,
  },
  badgeSubtext: {
    fontSize: 13,
    color: '#8E8E93',
    fontWeight: '600',
  },
  eventHeader: {
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
    borderLeftWidth: 4,
    borderLeftColor: '#34C759',
  },
  eventTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  eventTime: {
    fontSize: 15,
    color: '#8E8E93',
    fontWeight: '600',
    marginBottom: 4,
  },
  eventLocation: {
    fontSize: 14,
    color: '#8E8E93',
  },
  instructionsBox: {
    backgroundColor: '#1C1C1E',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#FF9500',
  },
  instructionsTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FF9500',
    marginBottom: 8,
  },
  instructionsText: {
    fontSize: 14,
    color: '#FFFFFF',
    lineHeight: 20,
  },
  loadingContainer: {
    padding: 60,
    alignItems: 'center',
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    marginBottom: 20,
  },
  loadingText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
    marginTop: 16,
  },
  loadingSubtext: {
    color: '#8E8E93',
    fontSize: 13,
    marginTop: 8,
  },
  errorContainer: {
    padding: 40,
    alignItems: 'center',
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#FF3B30',
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FF3B30',
    marginTop: 16,
  },
  errorText: {
    fontSize: 14,
    color: '#FFFFFF',
    textAlign: 'center',
    marginTop: 8,
    lineHeight: 20,
  },
  retryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FF3B30',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 20,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
    marginLeft: 8,
  },
  analysisContainer: {
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  timestampContainer: {
    backgroundColor: '#1C1C1E',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 3,
    borderLeftColor: '#34C759',
  },
  timestampText: {
    fontSize: 14,
    color: '#FFFFFF',
    fontWeight: '600',
    marginBottom: 4,
  },
  timestampSubtext: {
    fontSize: 12,
    color: '#8E8E93',
  },
  recalculateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    marginBottom: 20,
  },
  recalculateText: {
    fontSize: 13,
    color: '#8E8E93',
    marginLeft: 6,
    fontWeight: '500',
  },
  bottomSpacer: {
    height: 40,
  },
});
