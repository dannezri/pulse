import { useEffect, useState } from "react";
import { useRouter, useSegments } from "expo-router";
import { View, Text, ActivityIndicator, Platform } from "react-native";
import { supabase } from "../src/lib/supabase";
import { storage } from "../src/lib/storage";
import * as SecureStore from 'expo-secure-store';
import Constants from 'expo-constants';

// UUID de développement pour auto-login (depuis .env ou variable d'environnement)
// Pour le définir : ajouter EXPO_PUBLIC_DEV_USER_UUID dans mobile/.env
console.log('🔍 UUID Debug:', {
  fromExpoConfig: Constants.expoConfig?.extra?.devUserUuid,
  fromEnv: process.env.EXPO_PUBLIC_DEV_USER_UUID,
  allExtra: Constants.expoConfig?.extra
});
const DEV_USER_UUID = Constants.expoConfig?.extra?.devUserUuid || process.env.EXPO_PUBLIC_DEV_USER_UUID;

export default function Index() {
  const router = useRouter();
  const segments = useSegments();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [initError, setInitError] = useState<string | null>(null);

  useEffect(() => {
    const initAuth = async () => {
      // Vérifier d'abord si Supabase est configuré
      const supabaseUrl = process.env.EXPO_PUBLIC_SUPABASE_URL;
      const supabaseKey = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY;
      
      if (!supabaseUrl || !supabaseKey || supabaseUrl === "https://placeholder.supabase.co" || supabaseKey === "placeholder-key") {
        setInitError("Supabase non configuré");
        setLoading(false);
        return;
      }

      try {
        // Vérifier si DEV_USER_UUID est configuré
        if (!DEV_USER_UUID) {
          console.error("❌ DEV_USER_UUID non configuré. Ajoutez EXPO_PUBLIC_DEV_USER_UUID dans mobile/.env");
          setError("UUID de développement non configuré");
          setLoading(false);
          return;
        }

        // Vérifier si un utilisateur est déjà connecté (via storage local)
        const userId = await storage.getUserId();
        
        // Si l'UUID stocké est différent de celui en dev, le remplacer
        if (userId && userId !== DEV_USER_UUID) {
          console.log("⚠️ UUID différent détecté, mise à jour:", userId, "→", DEV_USER_UUID);
          
          // Vider le cache des médicaments et autres données utilisateur
          try {
            console.log("🗑️ Vidage du cache utilisateur...");
            await SecureStore.deleteItemAsync('pulse_medications', {
              keychainAccessible: SecureStore.AFTER_FIRST_UNLOCK_THIS_DEVICE_ONLY,
            });
            console.log("✅ Cache des médicaments vidé");
          } catch (err) {
            console.warn("⚠️ Erreur lors du vidage du cache:", err);
          }
          
          await storage.saveUserId(DEV_USER_UUID);
          console.log("✅ UUID mis à jour:", DEV_USER_UUID);
          router.replace("/(tabs)");
          setLoading(false);
          return;
        }
        
        if (userId === DEV_USER_UUID) {
          // Utilisateur déjà connecté avec le bon UUID
          console.log("✅ Utilisateur déjà connecté:", userId);
          router.replace("/(tabs)");
          setLoading(false);
          return;
        }

        // Aucun utilisateur connecté : Auto-login pour le développement
        console.log("🔐 Auto-login avec UUID:", DEV_USER_UUID);
        
        // Vider le cache pour partir sur une base propre
        try {
          console.log("🗑️ Nettoyage du cache au premier démarrage...");
          await SecureStore.deleteItemAsync('pulse_medications', {
            keychainAccessible: SecureStore.AFTER_FIRST_UNLOCK_THIS_DEVICE_ONLY,
          });
        } catch (err) {
          // Ignore si la clé n'existe pas
        }
        
        // Stocker l'UUID Supabase localement (pas besoin de RPC)
        await storage.saveUserId(DEV_USER_UUID);
        
        console.log("✅ Auto-login réussi, UUID:", DEV_USER_UUID);
        router.replace("/(tabs)");
      } catch (err) {
        console.error("❌ Erreur d'initialisation:", err);
        setError(err instanceof Error ? err.message : "Erreur inconnue");
        router.replace("/login");
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  if (loading) {
    return (
      <View style={{ flex: 1, backgroundColor: "#000000", justifyContent: "center", alignItems: "center" }}>
        <Text style={{ color: "#00FF41", fontSize: 24, fontWeight: "bold", marginBottom: 16 }}>Pulse</Text>
        <ActivityIndicator size="large" color="#00FF41" />
      </View>
    );
  }

  if (initError || error) {
    // Afficher un message d'erreur visible
    return (
      <View style={{ flex: 1, backgroundColor: "#000000", justifyContent: "center", alignItems: "center", padding: 20 }}>
        <Text style={{ color: "#FF6B35", fontSize: 18, fontWeight: "bold", marginBottom: 12, textAlign: "center" }}>
          {initError || "Erreur de configuration"}
        </Text>
        <Text style={{ color: "#666666", fontSize: 14, textAlign: "center", marginBottom: 8 }}>
          {initError 
            ? "Créez un fichier `.env` dans le dossier `mobile/` avec vos variables Supabase"
            : error}
        </Text>
        {initError && (
          <Text style={{ color: "#00FF41", fontSize: 12, fontFamily: Platform.OS === "web" ? "monospace" : "mono", textAlign: "center", marginTop: 16 }}>
            EXPO_PUBLIC_SUPABASE_URL=https://votre-projet.supabase.co{'\n'}
            EXPO_PUBLIC_SUPABASE_ANON_KEY=votre_cle_anon
          </Text>
        )}
        <Text style={{ color: "#666666", fontSize: 12, textAlign: "center", marginTop: 24 }}>
          Testez aussi : /test pour voir si React fonctionne
        </Text>
      </View>
    );
  }

  return null;
}
