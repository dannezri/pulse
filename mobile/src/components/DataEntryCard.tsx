/**
 * Composant pour afficher une entrée de données (biometric, insight, meal)
 */

import { View, Text, Pressable } from 'react-native';
import { 
  Activity,
  Heart,
  Brain,
  Footprints,
  Moon,
  Zap,
  ChevronRight,
  Clock,
  Lightbulb,
  Utensils,
  TrendingUp,
  AlertCircle
} from 'lucide-react-native';
import { useState } from 'react';

export interface DataEntry {
  id: string | number;
  type: 'biometric' | 'insight' | 'meal';
  subtype: string;
  value?: number;
  content?: string;
  calories?: number;
  priority?: number;
  is_read?: boolean;
  timestamp?: string;
  source?: string;
  created_at: string;
}

interface DataEntryCardProps {
  entry: DataEntry;
}

export function DataEntryCard({ entry }: DataEntryCardProps) {
  const [expanded, setExpanded] = useState(false);
  
  // Icône selon le type
  const getIcon = () => {
    if (entry.type === 'biometric') {
      switch (entry.subtype) {
        case 'hr':
        case 'resting_hr':
          return Heart;
        case 'hrv':
          return Activity;
        case 'steps':
          return Footprints;
        case 'sleep_score':
        case 'sleep_duration':
        case 'sleep_quality':
          return Moon;
        default:
          return Activity;
      }
    } else if (entry.type === 'insight') {
      return entry.priority === 2 ? AlertCircle : Lightbulb;
    } else if (entry.type === 'meal') {
      return Utensils;
    }
    return Activity;
  };
  
  const Icon = getIcon();
  
  // Couleur selon le type
  const getColor = () => {
    if (entry.type === 'biometric') {
      return '#00BFFF'; // Bleu
    } else if (entry.type === 'insight') {
      return entry.priority === 2 ? '#FF4444' : '#FFD700'; // Rouge si urgent, sinon or
    } else if (entry.type === 'meal') {
      return '#00FF41'; // Vert
    }
    return '#888888';
  };
  
  const color = getColor();
  
  // Formater le timestamp
  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) return 'Il y a quelques secondes';
    if (diff < 3600000) return `Il y a ${Math.floor(diff / 60000)}min`;
    if (diff < 86400000) return `Il y a ${Math.floor(diff / 3600000)}h`;
    
    return date.toLocaleString('fr-FR', { 
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };
  
  // Obtenir le titre
  const getTitle = () => {
    if (entry.type === 'biometric') {
      const typeMap: Record<string, string> = {
        'hr': 'Fréquence cardiaque',
        'resting_hr': 'FC au repos',
        'hrv': 'Variabilité cardiaque',
        'steps': 'Pas',
        'sleep_score': 'Score de sommeil',
        'sleep_duration': 'Durée de sommeil',
        'sleep_quality': 'Qualité de sommeil',
        'glucose': 'Glycémie',
        'calories': 'Calories',
        'distance': 'Distance',
        'vo2max': 'VO2 Max',
        'respiratory_rate': 'Fréquence respiratoire',
        'body_temperature': 'Température corporelle'
      };
      return typeMap[entry.subtype] || entry.subtype;
    } else if (entry.type === 'insight') {
      return entry.priority === 2 ? 'Insight Urgent' : 'Nouvel Insight';
    } else if (entry.type === 'meal') {
      return 'Nouveau Repas';
    }
    return 'Donnée';
  };
  
  // Obtenir la description
  const getDescription = () => {
    if (entry.type === 'biometric' && entry.value !== undefined) {
      const units: Record<string, string> = {
        'hr': 'bpm',
        'resting_hr': 'bpm',
        'hrv': 'ms',
        'steps': 'pas',
        'sleep_score': '/100',
        'sleep_duration': 'min',
        'sleep_quality': '/100',
        'glucose': 'mg/dL',
        'calories': 'kcal',
        'distance': 'm',
        'vo2max': 'mL/kg/min',
        'respiratory_rate': '/min',
        'body_temperature': '°C'
      };
      const unit = units[entry.subtype] || '';
      return `${entry.value.toFixed(entry.subtype === 'hrv' ? 0 : 1)} ${unit}`;
    } else if (entry.type === 'insight' && entry.content) {
      return entry.content.substring(0, 100) + (entry.content.length > 100 ? '...' : '');
    } else if (entry.type === 'meal' && entry.content) {
      return entry.content.substring(0, 100) + (entry.content.length > 100 ? '...' : '');
    }
    return '';
  };
  
  // Badge selon le type
  const getBadge = () => {
    if (entry.type === 'biometric' && entry.source) {
      return entry.source.toUpperCase();
    } else if (entry.type === 'insight') {
      return entry.subtype ? entry.subtype.toUpperCase() : 'GÉNÉRAL';
    } else if (entry.type === 'meal' && entry.calories) {
      return `${entry.calories} kcal`;
    }
    return entry.type.toUpperCase();
  };
  
  return (
    <Pressable
      onPress={() => setExpanded(!expanded)}
      style={{
        backgroundColor: '#0a0a0a',
        borderRadius: 16,
        padding: 16,
        marginBottom: 12,
        borderWidth: 1,
        borderColor: '#1a1a1a',
      }}
    >
      {/* Header */}
      <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
        {/* Icône */}
        <View
          style={{
            width: 40,
            height: 40,
            borderRadius: 12,
            backgroundColor: `${color}15`,
            justifyContent: 'center',
            alignItems: 'center',
            marginRight: 12,
          }}
        >
          <Icon size={20} color={color} />
        </View>
        
        {/* Titre + Description */}
        <View style={{ flex: 1 }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <Text
              style={{
                color: color,
                fontSize: 14,
                fontWeight: '700',
                letterSpacing: 0.5,
              }}
            >
              {getTitle()}
            </Text>
            <Text
              style={{
                color: '#666',
                fontSize: 11,
                fontWeight: '600',
                backgroundColor: `${color}15`,
                paddingHorizontal: 6,
                paddingVertical: 2,
                borderRadius: 4,
              }}
            >
              {getBadge()}
            </Text>
          </View>
          <Text
            style={{
              color: '#aaa',
              fontSize: 13,
              marginTop: 4,
            }}
            numberOfLines={expanded ? undefined : 2}
          >
            {getDescription()}
          </Text>
        </View>
        
        {/* Chevron */}
        <ChevronRight 
          size={20} 
          color="#444"
          style={{
            transform: expanded ? [{ rotate: '90deg' }] : [{ rotate: '0deg' }]
          }}
        />
      </View>
      
      {/* Footer - Timing */}
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 16 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
          <Clock size={14} color="#555" />
          <Text style={{ color: '#666', fontSize: 12 }}>
            {formatTime(entry.created_at)}
          </Text>
        </View>
        
        {entry.type === 'insight' && entry.is_read !== undefined && (
          <Text 
            style={{ 
              color: entry.is_read ? '#555' : color, 
              fontSize: 11,
              fontWeight: '600',
            }}
          >
            {entry.is_read ? '✓ Lu' : '• Non lu'}
          </Text>
        )}
      </View>
      
      {/* Détails (expanded) */}
      {expanded && (
        <View style={{ marginTop: 16, paddingTop: 16, borderTopWidth: 1, borderTopColor: '#1a1a1a' }}>
          {/* Contenu complet pour insights et meals */}
          {entry.type === 'insight' && entry.content && (
            <View style={{ marginBottom: 12 }}>
              <Text style={{ color: '#888', fontSize: 11, fontWeight: '600', marginBottom: 4 }}>
                CONSIGNE IA
              </Text>
              <Text style={{ color: '#aaa', fontSize: 13, lineHeight: 20 }}>
                {entry.content}
              </Text>
            </View>
          )}
          
          {entry.type === 'meal' && entry.content && (
            <View style={{ marginBottom: 12 }}>
              <Text style={{ color: '#888', fontSize: 11, fontWeight: '600', marginBottom: 4 }}>
                DESCRIPTION
              </Text>
              <Text style={{ color: '#aaa', fontSize: 13, lineHeight: 20 }}>
                {entry.content}
              </Text>
            </View>
          )}
          
          {/* Métadonnées */}
          <View>
            <Text style={{ color: '#888', fontSize: 11, fontWeight: '600', marginBottom: 4 }}>
              MÉTADONNÉES
            </Text>
            <View style={{ backgroundColor: '#050505', padding: 12, borderRadius: 8 }}>
              <Text style={{ color: '#666', fontSize: 11, fontFamily: 'monospace' }}>
                ID: {entry.id}
              </Text>
              <Text style={{ color: '#666', fontSize: 11, fontFamily: 'monospace' }}>
                Type: {entry.type}
              </Text>
              {entry.timestamp && (
                <Text style={{ color: '#666', fontSize: 11, fontFamily: 'monospace' }}>
                  Enregistré: {new Date(entry.timestamp).toLocaleString('fr-FR')}
                </Text>
              )}
              <Text style={{ color: '#666', fontSize: 11, fontFamily: 'monospace' }}>
                Créé: {new Date(entry.created_at).toLocaleString('fr-FR')}
              </Text>
            </View>
          </View>
        </View>
      )}
    </Pressable>
  );
}
