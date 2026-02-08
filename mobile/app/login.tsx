import { View, Text, TextInput, TouchableOpacity, SafeAreaView, Alert } from "react-native";
import { useState } from "react";
import { supabase } from "@/lib/supabase";
import { useRouter } from "expo-router";

export default function LoginScreen() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert("Erreur", "Veuillez remplir tous les champs");
      return;
    }

    setLoading(true);
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    setLoading(false);

    if (error) {
      Alert.alert("Erreur de connexion", error.message);
    } else if (data.session) {
      router.replace("/(tabs)");
    }
  };

  return (
    <SafeAreaView className="flex-1 bg-black">
      <View className="flex-1 items-center justify-center px-6">
        <Text className="text-white text-3xl font-bold mb-2">Pulse</Text>
        <Text className="text-gray-400 text-center mb-8">
          Connectez-vous pour accéder à vos données de santé
        </Text>

        <View className="w-full mb-4">
          <Text className="text-gray-400 text-sm mb-2">Email</Text>
          <TextInput
            className="bg-gray-900 text-white rounded-xl p-4 border border-gray-800"
            placeholder="votre@email.com"
            placeholderTextColor="#666666"
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            keyboardType="email-address"
          />
        </View>

        <View className="w-full mb-6">
          <Text className="text-gray-400 text-sm mb-2">Mot de passe</Text>
          <TextInput
            className="bg-gray-900 text-white rounded-xl p-4 border border-gray-800"
            placeholder="••••••••"
            placeholderTextColor="#666666"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
          />
        </View>

        <TouchableOpacity
          className="bg-primary w-full rounded-xl p-4 items-center"
          onPress={handleLogin}
          disabled={loading}
        >
          <Text className="text-black font-bold text-lg">
            {loading ? "Connexion..." : "Se connecter"}
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}
