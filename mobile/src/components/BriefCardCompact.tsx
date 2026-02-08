/**
 * BriefCardCompact - Version compacte des cartes Brief
 * 
 * Affichage condensé des insights sous le Daily Energy Card
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { 
  Activity, 
  Heart, 
  Moon, 
  Zap, 
  AlertTriangle,
  TrendingUp,
  Target,
  Calendar,
  Coffee
} from 'lucide-react-native';
import { BriefCard } from '../types/brief';

interface BriefCardCompactProps {
  card: BriefCard;
}

const iconMap: Record<string, any> = {
  Activity,
  Heart,
  Moon,
  Zap,
  AlertTriangle,
  TrendingUp,
  Target,
  Calendar,
  Coffee,
};

const stateColors = {
  optimal: '#10b981',   // green
  warning: '#f59e0b',   // orange
  alert: '#ef4444',     // red
  neutral: '#6b7280',   // gray
};

export const BriefCardCompact: React.FC<BriefCardCompactProps> = ({ card }) => {
  const Icon = iconMap[card.iconName] || Activity;
  const color = stateColors[card.state];

  return (
    <View style={styles.card}>
      {/* Header */}
      <View style={styles.header}>
        <View style={[styles.iconCircle, { backgroundColor: `${color}20` }]}>
          <Icon size={18} color={color} strokeWidth={2.5} />
        </View>
        <View style={styles.headerText}>
          <Text style={styles.title} numberOfLines={1}>{card.title}</Text>
          {card.badge !== undefined && (
            <Text style={[styles.badge, { color }]}>
              {card.badge}{card.badgeUnit || '%'}
            </Text>
          )}
        </View>
      </View>

      {/* Content */}
      <Text style={styles.content} numberOfLines={2}>
        {card.content}
      </Text>

      {/* State indicator */}
      <View style={[styles.stateBar, { backgroundColor: color }]} />
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#1f2937',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 3,
    borderLeftColor: 'transparent',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  iconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  headerText: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  title: {
    flex: 1,
    fontSize: 15,
    fontWeight: '700',
    color: '#f9fafb',
  },
  badge: {
    fontSize: 14,
    fontWeight: '800',
    marginLeft: 8,
  },
  content: {
    fontSize: 14,
    color: '#d1d5db',
    lineHeight: 20,
  },
  stateBar: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: 3,
    borderTopLeftRadius: 16,
    borderBottomLeftRadius: 16,
  },
});
