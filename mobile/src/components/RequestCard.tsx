/**
 * Composant pour afficher une requête API avec icône et style
 */

import { View, Text, Pressable } from 'react-native';
import { 
  Eye, 
  Upload, 
  Edit, 
  Trash2, 
  CheckCircle, 
  XCircle, 
  Loader, 
  Download,
  Clock,
  ChevronRight
} from 'lucide-react-native';
import { useState } from 'react';
import type { ApiRequest } from '../hooks/useApiLogger';

interface RequestCardProps {
  request: ApiRequest;
}

export function RequestCard({ request }: RequestCardProps) {
  const [expanded, setExpanded] = useState(false);
  
  // Icône selon la méthode HTTP
  const MethodIcon = {
    GET: Eye,
    POST: Upload,
    PUT: Edit,
    PATCH: Edit,
    DELETE: Trash2,
  }[request.method];
  
  // Icône selon le statut
  const StatusIcon = {
    pending: Loader,
    success: CheckCircle,
    error: XCircle,
  }[request.status];
  
  // Couleur selon le statut
  const statusColor = {
    pending: '#FFD700',
    success: '#00FF41',
    error: '#FF4444',
  }[request.status];
  
  // Couleur selon la méthode
  const methodColor = {
    GET: '#00BFFF',
    POST: '#00FF41',
    PUT: '#FFD700',
    PATCH: '#FFA500',
    DELETE: '#FF4444',
  }[request.method];
  
  // Formater la durée
  const formatDuration = (ms?: number) => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };
  
  // Formater le timestamp
  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) return 'Il y a quelques secondes';
    if (diff < 3600000) return `Il y a ${Math.floor(diff / 60000)}min`;
    
    return date.toLocaleTimeString('fr-FR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };
  
  // Extraire le path de l'URL
  const getPath = (url: string) => {
    try {
      const urlObj = new URL(url);
      return urlObj.pathname;
    } catch {
      return url;
    }
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
        {/* Icône méthode */}
        <View
          style={{
            width: 40,
            height: 40,
            borderRadius: 12,
            backgroundColor: `${methodColor}15`,
            justifyContent: 'center',
            alignItems: 'center',
            marginRight: 12,
          }}
        >
          <MethodIcon size={20} color={methodColor} />
        </View>
        
        {/* Méthode + URL */}
        <View style={{ flex: 1 }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <Text
              style={{
                color: methodColor,
                fontSize: 13,
                fontWeight: '700',
                letterSpacing: 0.5,
              }}
            >
              {request.method}
            </Text>
            {request.statusCode && (
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
                {request.statusCode}
              </Text>
            )}
          </View>
          <Text
            style={{
              color: '#888',
              fontSize: 13,
              marginTop: 2,
            }}
            numberOfLines={1}
          >
            {getPath(request.url)}
          </Text>
        </View>
        
        {/* Statut */}
        <View style={{ alignItems: 'flex-end', gap: 4 }}>
          <StatusIcon 
            size={20} 
            color={statusColor}
            style={{ 
              transform: request.status === 'pending' ? [{ rotate: '360deg' }] : [] 
            }} 
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
            {formatTime(request.timestamp)}
          </Text>
        </View>
        
        {request.duration && (
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
            <Download size={14} color="#555" />
            <Text style={{ color: '#666', fontSize: 12 }}>
              {formatDuration(request.duration)}
            </Text>
          </View>
        )}
        
        {request.error && (
          <Text 
            style={{ 
              color: '#FF4444', 
              fontSize: 11,
              flex: 1,
            }}
            numberOfLines={1}
          >
            {request.error}
          </Text>
        )}
      </View>
      
      {/* Détails (expanded) */}
      {expanded && (
        <View style={{ marginTop: 16, paddingTop: 16, borderTopWidth: 1, borderTopColor: '#1a1a1a' }}>
          {/* URL complète */}
          <View style={{ marginBottom: 12 }}>
            <Text style={{ color: '#888', fontSize: 11, fontWeight: '600', marginBottom: 4 }}>
              URL COMPLÈTE
            </Text>
            <Text style={{ color: '#aaa', fontSize: 12, fontFamily: 'monospace' }}>
              {request.url}
            </Text>
          </View>
          
          {/* Request Body */}
          {request.requestBody && (
            <View style={{ marginBottom: 12 }}>
              <Text style={{ color: '#888', fontSize: 11, fontWeight: '600', marginBottom: 4 }}>
                REQUEST BODY
              </Text>
              <View style={{ backgroundColor: '#050505', padding: 12, borderRadius: 8 }}>
                <Text style={{ color: '#00FF41', fontSize: 11, fontFamily: 'monospace' }}>
                  {JSON.stringify(request.requestBody, null, 2)}
                </Text>
              </View>
            </View>
          )}
          
          {/* Response Body */}
          {request.responseBody && (
            <View>
              <Text style={{ color: '#888', fontSize: 11, fontWeight: '600', marginBottom: 4 }}>
                RESPONSE BODY
              </Text>
              <View style={{ backgroundColor: '#050505', padding: 12, borderRadius: 8 }}>
                <Text 
                  style={{ color: '#00BFFF', fontSize: 11, fontFamily: 'monospace' }}
                  numberOfLines={10}
                >
                  {JSON.stringify(request.responseBody, null, 2)}
                </Text>
              </View>
            </View>
          )}
        </View>
      )}
    </Pressable>
  );
}
