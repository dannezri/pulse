import { Tabs } from "expo-router";
import { Home, History, User, Link, Activity, Utensils, Zap } from "lucide-react-native";

export default function TabsLayout() {
  // Note: Authentication is handled by app/index.tsx and useAuth hook
  // No need to check auth here as the router already protects these tabs

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: "#000000",
          borderTopColor: "#1a1a1a",
          borderTopWidth: 1,
        },
        tabBarActiveTintColor: "#00FF41",
        tabBarInactiveTintColor: "#666666",
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: "600",
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Accueil",
          tabBarIcon: ({ color, size }) => <Home size={size} color={color} />,
          // Style plein écran immersif pour le Brief
          tabBarStyle: {
            backgroundColor: "#000000",
            borderTopColor: "transparent",
            borderTopWidth: 0,
            position: "absolute",
            elevation: 0,
            shadowOpacity: 0,
          },
        }}
      />
      <Tabs.Screen
        name="requests"
        options={{
          title: "Données",
          tabBarIcon: ({ color, size }) => <Activity size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="energie"
        options={{
          title: "Énergie",
          tabBarIcon: ({ color, size }) => <Zap size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="food-diary"
        options={{
          title: "Nutrition",
          tabBarIcon: ({ color, size }) => <Utensils size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="tendances"
        options={{
          title: "Tendances",
          tabBarIcon: ({ color, size }) => <History size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="profil"
        options={{
          title: "Profil",
          tabBarIcon: ({ color, size }) => <User size={size} color={color} />,
        }}
      />
      {/* Anciens écrans Food Diary - cachés de la navigation */}
      <Tabs.Screen
        name="journal"
        options={{
          href: null, // Cache de la navigation
        }}
      />
      <Tabs.Screen
        name="search-food"
        options={{
          href: null, // Cache de la navigation
        }}
      />
      <Tabs.Screen
        name="food-details"
        options={{
          href: null, // Cache de la navigation
        }}
      />
    </Tabs>
  );
}
