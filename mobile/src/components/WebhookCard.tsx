/**
 * Composant pour afficher un webhook reçu par le backend
 */

import { View, Text, Pressable } from 'react-native';
import { 
  Webhook,
  CheckCircle, 
  XCircle, 
  Clock,
  ChevronRight,
  Zap,
  Database,
  Activity
} from 'lucide-react-native';
import { useState } from 'react';

export interface WebhookLog {
  id: string;
  endpoint: string;
  method: string;
  event_type: string | null;
  status_code: number;
  response_message: string | null;
  duration_ms: number | null;
  error: string | null;
  received_at: string;
  processed_at: string | null;
  payload: any;
}

interface WebhookCardProps {
  webhook: WebhookLog;
}

export function WebhookCard({ webhook }: WebhookCardProps) {
  const [expanded, setExpanded] = useState(false);
  
  // Icône selon le statut
  const StatusIcon = webhook.status_code >= 200 && webhook.status_code < 300 
    ? CheckCircle 
    : XCircle;
  
  // Couleur selon le statut
  const statusColor = webhook.status_code >= 200 && webhook.status_code < 300
    ? '#00FF41'  // Succès
    : webhook.status_code >= 400 && webhook.status_code < 500
    ? '#FFD700'  // Client error
    : '#FF4444'; // Server error
  
  // Icône selon le type d'événement
  const getEventIcon = () => {
    if (!webhook.event_type) return Webhook;
    
    if (webhook.event_type.includes('historical')) return Database;
    if (webhook.event_type.includes('timeseries')) return Activity;
    if (webhook.event_type.includes('daily')) return Zap;
    
    return Webhook;
  };
  
  const EventIcon = getEventIcon();
  
  // Couleur selon le type d'événement
  const eventColor = webhook.event_type?.includes('historical')
    ? '#00BFFF'  // Bleu pour historical
    : webhook.event_type?.includes('timeseries')
    ? '#00FF41'  // Vert pour timeseries
    : webhook.event_type?.includes('daily')
    ? '#FFD700'  // Or pour daily
    : '#888888'; // Gris par défaut
  
  // Formater la durée
  const formatDuration = (ms?: number | null) => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };
  
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
  
  // Extraire le type de données de l'event_type
  const getDataType = (eventType?: string | null) => {
    if (!eventType) return 'Unknown';
    
    // Ex: "historical.data.water.created" -> "water"
    const parts = eventType.split('.');
    if (parts.length >= 3) {
      return parts[2].charAt(0).toUpperCase() + parts[2].slice(1);
    }
    
    return eventType;
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
        {/* Icône événement */}
        <View
          style={{
            width: 40,
            height: 40,
            borderRadius: 12,
            backgroundColor: `${eventColor}15`,
            justifyContent: 'center',
            alignItems: 'center',
            marginRight: 12,
          }}
        >
          <EventIcon size={20} color={eventColor} />
        </View>
        
        {/* Type de données + Event type */}
        <View style={{ flex: 1 }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <Text
              style={{
                color: eventColor,
                fontSize: 14,
                fontWeight: '700',
                letterSpacing: 0.5,
              }}
            >
              {getDataType(webhook.event_type)}
            </Text>
            <Text
              style={{
                color: statusColor,
                fontSize: 11,
                fontWeight: '600',
                backgroundColor: `${statusColor}15`,
                paddingHorizontal: 6,
                paddingVertical: 2,
                borderRadius: 4,
              }}
            >
              {webhook.status_code}
            </Text>
          </View>
          <Text
            style={{
              color: '#666',
              fontSize: 11,
              marginTop: 2,
            }}
            numberOfLines={1}
          >
            {webhook.event_type || 'No event type'}
          </Text>
        </View>
        
        {/* Statut */}
        <View style={{ alignItems: 'flex-end', gap: 4 }}>
          <StatusIcon 
            size={20} 
            color={statusColor}
          />
          <ChevronRight 
            size={16} 
            color="#444"
            style={{
              transform: expanded ? [{ rotate: '90deg' }] : [{ rotate: '0deg' }]
            }}
          />
        </View>
      </View>
      
      {/* Footer - Timing */}
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 16 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
          <Clock size={14} color="#555" />
          <Text style={{ color: '#666', fontSize: 12 }}>
            {formatTime(webhook.received_at)}
          </Text>
        </View>
        
        {webhook.duration_ms && (
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
            <Zap size={14} color="#555" />
            <Text style={{ color: '#666', fontSize: 12 }}>
              {formatDuration(webhook.duration_ms)}
            </Text>
          </View>
        )}
        
        {webhook.error && (
          <Text 
            style={{ 
              color: '#FF4444', 
              fontSize: 11,
              flex: 1,
            }}
            numberOfLines={1}
          >
            {webhook.error}
          </Text>
        )}
      </View>
      
      {/* Détails (expanded) */}
      {expanded && (
        <View style={{ marginTop: 16, paddingTop: 16, borderTopWidth: 1, borderTopColor: '#1a1a1a' }}>
          {/* Endpoint */}
          <View style={{ marginBottom: 12 }}>
            <Text style={{ color: '#888', fontSize: 11, fontWeight: '600', marginBottom: 4 }}>
              ENDPOINT
            </Text>
            <Text style={{ color: '#aaa', fontSize: 12, fontFamily: 'monospace' }}>
              {webhook.endpoint}
            </Text>
          </View>
          
          {/* Response Message */}
          {webhook.response_message && (
            <View style={{ marginBottom: 12 }}>
              <Text style={{ color: '#888', fontSize: 11, fontWeight: '600', marginBottom: 4 }}>
                RESPONSE
              </Text>
              <Text style={{ color: '#aaa', fontSize: 12 }}>
                {webhook.response_message}
              </Text>
            </View>
          )}
          
          {/* Payload */}
          {webhook.payload && (
            <View>
              <Text style={{ color: '#888', fontSize: 11, fontWeight: '600', marginBottom: 4 }}>
                PAYLOAD
              </Text>
              <View style={{ backgroundColor: '#050505', padding: 12, borderRadius: 8 }}>
                <Text 
                  style={{ color: '#00BFFF', fontSize: 11, fontFamily: 'monospace' }}
                  numberOfLines={15}
                >
                  {JSON.stringify(webhook.payload, null, 2)}
                </Text>
              </View>
            </View>
          )}
        </View>
      )}
    </Pressable>
  );
}
