import { Stack } from "expo-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { useEffect, useState } from "react";
import { Session } from "@supabase/supabase-js";
import { View, Text, ActivityIndicator, Platform } from "react-native";
import { supabase } from "../src/lib/supabase";
import "../global.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
});

function LoadingScreen() {
  return (
    <View style={{ flex: 1, backgroundColor: "#000000", justifyContent: "center", alignItems: "center" }}>
      <Text style={{ color: "#00FF41", fontSize: 24, fontWeight: "bold", marginBottom: 16 }}>Pulse</Text>
      <ActivityIndicator size="large" color="#00FF41" />
    </View>
  );
}

export default function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <SafeAreaProvider>
        <Stack
          screenOptions={{
            headerShown: false,
            contentStyle: { backgroundColor: "#000000" },
          }}
        />
      </SafeAreaProvider>
    </QueryClientProvider>
  );
}
