import { useEffect, useState } from "react";
import { useRouter, useSegments } from "expo-router";
import { View, Text, ActivityIndicator, Platform } from "react-native";
import { supabase } from "../src/lib/supabase";
import { storage } from "../src/lib/storage";

// ID de développement pour auto-login
const DEV_OPEN_WEARABLES_ID = "a088e712-cb41-4712-b622-af4370baaa20";

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
        // Vérifier si un utilisateur est déjà connecté (via storage local)
        const userId = await storage.getUserId();
        
        if (userId) {
          // Utilisateur déjà connecté
          console.log("Utilisateur déjà connecté:", userId);
          router.replace("/(tabs)");
          setLoading(false);
          return;
        }

        // Auto-login pour le développement
        console.log("Auto-login avec Open Wearables ID:", DEV_OPEN_WEARABLES_ID);
        
        // Récupérer l'UUID Supabase à partir de l'Open Wearables ID
        const { data: profileData, error: profileError } = await supabase
          .rpc('get_user_by_open_wearables_id', { open_wearables_id: DEV_OPEN_WEARABLES_ID });

        if (profileError || !profileData || profileData.length === 0) {
          console.error("Erreur lors de l'auto-login:", profileError);
          router.replace("/login");
          setLoading(false);
          return;
        }

        // Stocker l'UUID Supabase localement
        const supabaseUserId = profileData[0].id;
        await storage.saveUserId(supabaseUserId);
        
        console.log("Auto-login réussi, UUID:", supabaseUserId);
        router.replace("/(tabs)");
      } catch (err) {
        console.error("Erreur d'initialisation:", err);
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
