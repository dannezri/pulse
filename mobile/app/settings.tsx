import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
} from 'react-native';
import { router } from 'expo-router';
import { 
  ChevronLeft, 
  Bell, 
  Moon, 
  Globe, 
  Shield, 
  HelpCircle,
  ChevronRight,
  Smartphone,
  Database
} from 'lucide-react-native';

export default function SettingsScreen() {
  const [notifications, setNotifications] = useState(true);
  const [darkMode, setDarkMode] = useState(true);
  const [autoSync, setAutoSync] = useState(true);

  const settingsSections = [
    {
      title: 'Préférences',
      items: [
        {
          id: 'notifications',
          label: 'Notifications',
          icon: Bell,
          color: '#FF6B35',
          type: 'toggle',
          value: notifications,
          onToggle: setNotifications,
        },
        {
          id: 'darkMode',
          label: 'Mode sombre',
          icon: Moon,
          color: '#7B6CF6',
          type: 'toggle',
          value: darkMode,
          onToggle: setDarkMode,
        },
        {
          id: 'language',
          label: 'Langue',
          icon: Globe,
          color: '#4ECDC4',
          type: 'navigation',
          value: 'Français',
        },
      ],
    },
    {
      title: 'Données',
      items: [
        {
          id: 'autoSync',
          label: 'Synchronisation auto',
          icon: Smartphone,
          color: '#FFB800',
          type: 'toggle',
          value: autoSync,
          onToggle: setAutoSync,
        },
        {
          id: 'dataManagement',
          label: 'Gestion des données',
          icon: Database,
          color: '#FF6B9D',
          type: 'navigation',
        },
      ],
    },
    {
      title: 'Sécurité & Aide',
      items: [
        {
          id: 'privacy',
          label: 'Confidentialité',
          icon: Shield,
          color: '#34C759',
          type: 'navigation',
        },
        {
          id: 'help',
          label: 'Aide & Support',
          icon: HelpCircle,
          color: '#5E5CE6',
          type: 'navigation',
        },
      ],
    },
  ];

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.headerButton}
          onPress={() => router.back()}
        >
          <ChevronLeft size={28} color="#FFFFFF" strokeWidth={2.5} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Settings</Text>
        <View style={styles.headerButton} />
      </View>

      <ScrollView 
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {settingsSections.map((section, sectionIndex) => (
          <View key={sectionIndex} style={styles.section}>
            <Text style={styles.sectionTitle}>{section.title}</Text>
            
            <View style={styles.settingsGroup}>
              {section.items.map((item, itemIndex) => {
                const IconComponent = item.icon;
                const isLast = itemIndex === section.items.length - 1;
                
                return (
                  <View key={item.id}>
                    <TouchableOpacity
                      style={styles.settingItem}
                      activeOpacity={item.type === 'navigation' ? 0.7 : 1}
                      disabled={item.type === 'toggle'}
                    >
                      <View style={[styles.settingIcon, { backgroundColor: item.color + '20' }]}>
                        <IconComponent size={20} color={item.color} strokeWidth={2.5} />
                      </View>
                      
                      <Text style={styles.settingLabel}>{item.label}</Text>
                      
                      {item.type === 'toggle' && (
                        <Switch
                          value={item.value}
                          onValueChange={item.onToggle}
                          trackColor={{ false: '#3A3A4C', true: item.color }}
                          thumbColor="#FFFFFF"
                          ios_backgroundColor="#3A3A4C"
                        />
                      )}
                      
                      {item.type === 'navigation' && (
                        <View style={styles.settingRight}>
                          {item.value && (
                            <Text style={styles.settingValue}>{item.value}</Text>
                          )}
                          <ChevronRight size={20} color="#FFFFFF40" strokeWidth={2} />
                        </View>
                      )}
                    </TouchableOpacity>
                    
                    {!isLast && <View style={styles.settingDivider} />}
                  </View>
                );
              })}
            </View>
          </View>
        ))}

        {/* App Version */}
        <View style={styles.versionContainer}>
          <Text style={styles.versionText}>Pulse v1.0.0</Text>
          <Text style={styles.versionSubtext}>Dernière mise à jour: 4 Fév 2026</Text>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0D0D1F',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
  },
  headerButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 0.3,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    paddingHorizontal: 20,
    paddingBottom: 40,
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF60',
    marginBottom: 12,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  settingsGroup: {
    backgroundColor: '#1A1A2E',
    borderRadius: 20,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#FFFFFF10',
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 16,
  },
  settingIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  settingLabel: {
    flex: 1,
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    letterSpacing: 0.2,
  },
  settingRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  settingValue: {
    fontSize: 15,
    fontWeight: '500',
    color: '#FFFFFF60',
  },
  settingDivider: {
    height: 1,
    backgroundColor: '#FFFFFF10',
    marginLeft: 68,
  },
  versionContainer: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  versionText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF40',
    marginBottom: 4,
  },
  versionSubtext: {
    fontSize: 12,
    fontWeight: '500',
    color: '#FFFFFF30',
  },
});
