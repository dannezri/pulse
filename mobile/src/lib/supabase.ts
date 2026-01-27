import { createClient } from "@supabase/supabase-js";
import Constants from "expo-constants";

const supabaseUrl = Constants.expoConfig?.extra?.supabaseUrl || process.env.EXPO_PUBLIC_SUPABASE_URL || "";
const supabaseAnonKey = Constants.expoConfig?.extra?.supabaseAnonKey || process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY || "";

// Debug logging
console.log('🔍 Supabase Config Debug:');
console.log('  - Constants.expoConfig?.extra?.supabaseUrl:', Constants.expoConfig?.extra?.supabaseUrl);
console.log('  - process.env.EXPO_PUBLIC_SUPABASE_URL:', process.env.EXPO_PUBLIC_SUPABASE_URL);
console.log('  - Final URL:', supabaseUrl);
console.log('  - Has Key:', supabaseAnonKey ? `Yes (${supabaseAnonKey.length} chars)` : 'No');

// Utiliser des valeurs par défaut pour éviter les erreurs en développement
// Ces valeurs seront remplacées par les vraies variables d'environnement
const defaultUrl = "https://placeholder.supabase.co";
const defaultKey = "placeholder-key";

export const supabase = createClient(
  supabaseUrl || defaultUrl,
  supabaseAnonKey || defaultKey,
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
    },
  }
);
