import { Tabs } from "expo-router";
import { Home, History, User, Pill, Link } from "lucide-react-native";

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
          title: "Aujourd'hui",
          tabBarIcon: ({ color, size }) => <Home size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="connections"
        options={{
          title: "Sources",
          tabBarIcon: ({ color, size }) => <Link size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="medications"
        options={{
          title: "Médicaments",
          tabBarIcon: ({ color, size }) => <Pill size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="history"
        options={{
          title: "Historique",
          tabBarIcon: ({ color, size }) => <History size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: "Profil",
          tabBarIcon: ({ color, size }) => <User size={size} color={color} />,
        }}
      />
    </Tabs>
  );
}
