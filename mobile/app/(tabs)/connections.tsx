/**
 * Écran Connexions - Gestion des sources de données Vital
 * 
 * Affiche les sources connectées (Apple Health, Fitbit, etc.)
 * et permet de connecter de nouvelles sources via Vital Link.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  RefreshControl,
  Modal,
  Platform,
} from 'react-native';
import { useVital } from '@/src/hooks/useVital';
import { vitalService } from '@/src/services/vitalService';
import { Linking } from 'react-native';

export default function ConnectionsScreen() {
  const {
    isVitalConfigured,
    connections,
    isLoading,
    error,
    setupVital,
    refreshConnections,
    getLinkToken,
    disconnectProvider,
    connectedCount,
  } = useVital();

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

  /**
   * Rafraîchir les connexions avec pull-to-refresh
   */
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refreshConnections();
    } catch (err) {
      console.error('Error refreshing:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  /**
   * Configurer Vital pour la première fois
   */
  const handleSetupVital = async () => {
    try {
      await setupVital();
      Alert.alert(
        'Succès',
        'Vital configuré avec succès. Vous pouvez maintenant connecter des sources.',
        [{ text: 'OK' }]
      );
    } catch (err) {
      Alert.alert(
        'Erreur',
        'Impossible de configurer Vital. Vérifiez votre connexion.',
        [{ text: 'OK' }]
      );
    }
  };

  /**
   * Ouvrir Vital Link pour connecter une nouvelle source
   */
  const handleConnectSource = async () => {
    try {
      setIsConnecting(true);

      // Générer le token Vital Link
      const linkToken = await getLinkToken();

      // Construire l'URL du widget
      const linkUrl = vitalService.getVitalLinkUrl(linkToken);

      // Ouvrir dans le navigateur externe
      const canOpen = await Linking.canOpenURL(linkUrl);
      if (canOpen) {
        await Linking.openURL(linkUrl);
        
        Alert.alert(
          'Connectez vos sources',
          'Une fois la connexion établie dans le navigateur, revenez ici et rafraîchissez la liste.',
          [
            {
              text: 'Rafraîchir',
              onPress: () => refreshConnections(),
            },
            { text: 'Plus tard' },
          ]
        );
      } else {
        throw new Error('Cannot open Vital Link URL');
      }
    } catch (err) {
      console.error('Error opening Vital Link:', err);
      Alert.alert(
        'Erreur',
        'Impossible d\'ouvrir Vital Link. Vérifiez votre connexion.',
        [{ text: 'OK' }]
      );
    } finally {
      setIsConnecting(false);
    }
  };

  /**
   * Déconnecter une source
   */
  const handleDisconnect = (providerSlug: string, providerName: string) => {
    Alert.alert(
      'Déconnecter',
      `Êtes-vous sûr de vouloir déconnecter ${providerName} ?`,
      [
        { text: 'Annuler', style: 'cancel' },
        {
          text: 'Déconnecter',
          style: 'destructive',
          onPress: async () => {
            try {
              await disconnectProvider(providerSlug);
              Alert.alert('Succès', `${providerName} déconnecté.`, [{ text: 'OK' }]);
            } catch (err) {
              Alert.alert(
                'Erreur',
                `Impossible de déconnecter ${providerName}.`,
                [{ text: 'OK' }]
              );
            }
          },
        },
      ]
    );
  };

  /**
   * Affiche un provider
   */
  const renderProvider = (provider: any) => {
    const isConnected = provider.status === 'connected' || provider.status === 'active';
    const statusColor = isConnected ? '#00FF41' : '#666';
    const statusText = isConnected ? 'Connecté' : provider.status || 'Inconnu';

    return (
      <View
        key={provider.slug}
        style={{
          backgroundColor: '#1a1a1a',
          borderRadius: 12,
          padding: 16,
          marginBottom: 12,
          borderWidth: 1,
          borderColor: isConnected ? '#00FF41' : '#333',
        }}
      >
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <View style={{ flex: 1 }}>
            <Text style={{ color: '#fff', fontSize: 16, fontWeight: '600', marginBottom: 4 }}>
              {provider.name || provider.slug}
            </Text>
            <Text style={{ color: statusColor, fontSize: 14 }}>
              {statusText}
            </Text>
            {provider.last_sync_at && (
              <Text style={{ color: '#666', fontSize: 12, marginTop: 4 }}>
                Dernière synchro: {new Date(provider.last_sync_at).toLocaleString('fr-FR')}
              </Text>
            )}
          </View>

          {isConnected && (
            <TouchableOpacity
              onPress={() => handleDisconnect(provider.slug, provider.name)}
              style={{
                backgroundColor: '#ff4444',
                borderRadius: 8,
                padding: 8,
                paddingHorizontal: 12,
              }}
            >
              <Text style={{ color: '#fff', fontSize: 12, fontWeight: '600' }}>
                Déconnecter
              </Text>
            </TouchableOpacity>
          )}
        </View>
      </View>
    );
  };

  // État de chargement initial
  if (isLoading && connections.length === 0) {
    return (
      <View style={{ flex: 1, backgroundColor: '#000', justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#00FF41" />
        <Text style={{ color: '#00FF41', marginTop: 16, fontSize: 16 }}>
          Chargement des connexions...
        </Text>
      </View>
    );
  }

  // Vital n'est pas configuré
  if (!isVitalConfigured) {
    return (
      <View style={{ flex: 1, backgroundColor: '#000', padding: 20, justifyContent: 'center' }}>
        <Text style={{ color: '#00FF41', fontSize: 24, fontWeight: 'bold', marginBottom: 16, textAlign: 'center' }}>
          Sources de données
        </Text>
        
        <View style={{ backgroundColor: '#1a1a1a', borderRadius: 16, padding: 24, marginBottom: 20 }}>
          <Text style={{ color: '#fff', fontSize: 16, marginBottom: 12, textAlign: 'center' }}>
            Connectez vos applications de tracking pour synchroniser automatiquement vos données de santé.
          </Text>
          <Text style={{ color: '#666', fontSize: 14, textAlign: 'center' }}>
            Disponibles: Apple Health, Google Fit, Fitbit, Oura, Whoop, Strava, Garmin, et plus.
          </Text>
        </View>

        <TouchableOpacity
          onPress={handleSetupVital}
          disabled={isLoading}
          style={{
            backgroundColor: '#00FF41',
            borderRadius: 12,
            padding: 16,
            alignItems: 'center',
          }}
        >
          {isLoading ? (
            <ActivityIndicator color="#000" />
          ) : (
            <Text style={{ color: '#000', fontSize: 16, fontWeight: 'bold' }}>
              Configurer Vital
            </Text>
          )}
        </TouchableOpacity>

        {error && (
          <View style={{ backgroundColor: '#ff4444', borderRadius: 8, padding: 12, marginTop: 16 }}>
            <Text style={{ color: '#fff', fontSize: 14 }}>
              Erreur: {error}
            </Text>
          </View>
        )}
      </View>
    );
  }

  // Vital configuré - afficher les connexions
  return (
    <View style={{ flex: 1, backgroundColor: '#000' }}>
      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={{ padding: 20 }}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            tintColor="#00FF41"
          />
        }
      >
        <Text style={{ color: '#00FF41', fontSize: 24, fontWeight: 'bold', marginBottom: 8 }}>
          Sources de données
        </Text>
        
        <Text style={{ color: '#666', fontSize: 14, marginBottom: 20 }}>
          {connectedCount} source{connectedCount > 1 ? 's' : ''} connectée{connectedCount > 1 ? 's' : ''}
        </Text>

        {/* Bouton connecter une source */}
        <TouchableOpacity
          onPress={handleConnectSource}
          disabled={isConnecting || isLoading}
          style={{
            backgroundColor: '#00FF41',
            borderRadius: 12,
            padding: 16,
            alignItems: 'center',
            marginBottom: 24,
          }}
        >
          {isConnecting ? (
            <ActivityIndicator color="#000" />
          ) : (
            <Text style={{ color: '#000', fontSize: 16, fontWeight: 'bold' }}>
              + Connecter une source
            </Text>
          )}
        </TouchableOpacity>

        {/* Liste des connexions */}
        {connections.length > 0 ? (
          <>
            <Text style={{ color: '#fff', fontSize: 16, fontWeight: '600', marginBottom: 12 }}>
              Mes connexions
            </Text>
            {connections.map(renderProvider)}
          </>
        ) : (
          <View style={{ backgroundColor: '#1a1a1a', borderRadius: 12, padding: 24, alignItems: 'center' }}>
            <Text style={{ color: '#666', fontSize: 16, textAlign: 'center' }}>
              Aucune source connectée.
            </Text>
            <Text style={{ color: '#666', fontSize: 14, textAlign: 'center', marginTop: 8 }}>
              Commencez par connecter une source de données.
            </Text>
          </View>
        )}

        {error && (
          <View style={{ backgroundColor: '#ff4444', borderRadius: 8, padding: 12, marginTop: 16 }}>
            <Text style={{ color: '#fff', fontSize: 14 }}>
              {error}
            </Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
}
