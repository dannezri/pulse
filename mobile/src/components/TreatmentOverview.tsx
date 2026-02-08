/**
 * TreatmentOverview - Analyse globale des traitements actuels générée par Gemini
 * Affiche un texte brut en introduction de la page médicaments
 */

import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Brain, Sparkles, AlertCircle } from 'lucide-react-native';
import { useMedicationComparativeAnalysis } from '@/hooks/useMedicationComparativeAnalysis';
import { Medication } from '@/hooks/useMedications';

interface TreatmentOverviewProps {
  userId: string | null;
  medications: Medication[];
}

// Helper pour rendre le texte Markdown avec styles
const renderMarkdownText = (text: string, styles: any) => {
  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];
  
  lines.forEach((line, lineIndex) => {
    // Titres (##, ###)
    if (line.startsWith('###')) {
      const title = line.replace(/^###\s*/, '');
      elements.push(
        <Text key={`h3-${lineIndex}`} style={styles.geminiSubtitle}>
          {parseInlineMarkdown(title, styles)}
        </Text>
      );
    } else if (line.startsWith('##')) {
      const title = line.replace(/^##\s*/, '');
      elements.push(
        <Text key={`h2-${lineIndex}`} style={styles.geminiTitle}>
          {parseInlineMarkdown(title, styles)}
        </Text>
      );
    }
    // Listes à puces (*, -)
    else if (line.match(/^\s*[\*\-]\s+/)) {
      const content = line.replace(/^\s*[\*\-]\s+/, '');
      elements.push(
        <View key={`li-${lineIndex}`} style={styles.geminiBulletItem}>
          <Text style={styles.geminiBulletPoint}>•</Text>
          <Text style={styles.geminiBulletText}>
            {parseInlineMarkdown(content, styles)}
          </Text>
        </View>
      );
    }
    // Ligne vide (paragraphe)
    else if (line.trim() === '') {
      elements.push(<View key={`space-${lineIndex}`} style={{ height: 12 }} />);
    }
    // Texte normal
    else if (line.trim() !== '') {
      elements.push(
        <Text key={`p-${lineIndex}`} style={styles.geminiRawText}>
          {parseInlineMarkdown(line, styles)}
        </Text>
      );
    }
  });
  
  return <>{elements}</>;
};

// Parser le Markdown inline (**gras**, emojis)
const parseInlineMarkdown = (text: string, styles: any) => {
  const parts: React.ReactNode[] = [];
  let currentIndex = 0;
  
  // Regex pour détecter **texte en gras**
  const boldRegex = /\*\*(.+?)\*\*/g;
  let match;
  
  while ((match = boldRegex.exec(text)) !== null) {
    // Ajouter le texte avant le gras
    if (match.index > currentIndex) {
      parts.push(text.substring(currentIndex, match.index));
    }
    
    // Ajouter le texte en gras
    parts.push(
      <Text key={`bold-${match.index}`} style={styles.geminiBold}>
        {match[1]}
      </Text>
    );
    
    currentIndex = match.index + match[0].length;
  }
  
  // Ajouter le reste du texte
  if (currentIndex < text.length) {
    parts.push(text.substring(currentIndex));
  }
  
  return parts;
};

export function TreatmentOverview({ userId, medications }: TreatmentOverviewProps) {
  const { data: analysisData, isLoading, error } = useMedicationComparativeAnalysis({ 
    userId, 
    enabled: !!userId && medications.length > 0 
  });

  // Si pas de médicaments, ne rien afficher
  if (medications.length === 0) {
    return null;
  }

  // Loading state
  if (isLoading) {
    return (
      <View style={styles.container}>
        <LinearGradient
          colors={['rgba(94, 92, 230, 0.15)', 'rgba(94, 92, 230, 0.05)']}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.card}
        >
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="small" color="#5E5CE6" />
            <Text style={styles.loadingText}>Analyse détaillée en cours avec Gemini...</Text>
          </View>
        </LinearGradient>
      </View>
    );
  }

  // Error state
  if (error) {
    console.error('[TreatmentOverview] Error:', error);
    return null; // Masquer silencieusement en cas d'erreur
  }

  // Si pas de données d'analyse, ne rien afficher
  if (!analysisData || !analysisData.analysis_text) {
    return null;
  }

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['rgba(94, 92, 230, 0.15)', 'rgba(94, 92, 230, 0.05)']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.card}
      >
        {/* Header avec icône */}
        <View style={styles.header}>
          <View style={styles.iconBadge}>
            <Brain size={20} color="#5E5CE6" strokeWidth={2.5} />
          </View>
          <Text style={styles.title}>Analyse de vos traitements</Text>
          <View style={styles.geminiTag}>
            <Sparkles size={12} color="#FFB800" strokeWidth={2.5} />
            <Text style={styles.geminiText}>Gemini</Text>
          </View>
        </View>

        {/* Badge des changements uniquement si nouveaux médicaments (les arrêts sont déjà dans l'analyse) */}
        {analysisData.has_changes && analysisData.new_medications > 0 && (
          <View style={styles.changesBadge}>
            <AlertCircle size={14} color="#FFB800" strokeWidth={2.5} />
            <Text style={styles.changesBadgeText}>
              {`${analysisData.new_medications} nouveau${analysisData.new_medications > 1 ? 'x' : ''}`}
            </Text>
          </View>
        )}

        {/* Analyse complète générée par Gemini avec formatage Markdown */}
        <View style={styles.analysisContent}>
          {renderMarkdownText(analysisData.analysis_text, styles)}
        </View>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 24,
  },
  card: {
    borderRadius: 20,
    padding: 20,
    borderWidth: 1.5,
    borderColor: 'rgba(94, 92, 230, 0.3)',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    justifyContent: 'center',
    paddingVertical: 8,
  },
  loadingText: {
    fontSize: 14,
    color: '#8E8E93',
    fontWeight: '500',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 10,
  },
  iconBadge: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: 'rgba(94, 92, 230, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(94, 92, 230, 0.3)',
  },
  title: {
    flex: 1,
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 0.2,
  },
  geminiTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(255, 184, 0, 0.15)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 184, 0, 0.3)',
  },
  geminiText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#FFB800',
    letterSpacing: 0.5,
  },
  changesBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(255, 184, 0, 0.15)',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 184, 0, 0.3)',
  },
  changesBadgeText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#FFB800',
    letterSpacing: 0.3,
  },
  analysisContent: {
    marginTop: 4,
  },
  // Styles pour le rendu Markdown
  geminiTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 12,
    marginTop: 16,
    letterSpacing: 0.3,
  },
  geminiSubtitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#E0E0E0',
    marginBottom: 10,
    marginTop: 14,
    letterSpacing: 0.2,
  },
  geminiRawText: {
    fontSize: 15,
    color: '#E5E7EB',
    lineHeight: 24,
    marginBottom: 8,
  },
  geminiBold: {
    fontWeight: '700',
    color: '#FFFFFF',
  },
  geminiBulletItem: {
    flexDirection: 'row',
    marginBottom: 8,
    paddingLeft: 4,
  },
  geminiBulletPoint: {
    color: '#5E5CE6',
    fontSize: 18,
    lineHeight: 24,
    marginRight: 8,
    fontWeight: '700',
  },
  geminiBulletText: {
    flex: 1,
    color: '#E5E7EB',
    fontSize: 15,
    lineHeight: 24,
  },
});
