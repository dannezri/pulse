import * as SecureStore from 'expo-secure-store';

const USER_ID_KEY = 'pulse_user_id';

// Options de sécurité pour le Keychain iOS
// AFTER_FIRST_UNLOCK_THIS_DEVICE_ONLY permet l'accès même quand l'appareil est verrouillé
// (après le premier déverrouillage post-boot), évitant les erreurs "User interaction is not allowed"
const KEYCHAIN_OPTIONS: SecureStore.SecureStoreOptions = {
  keychainAccessible: SecureStore.AFTER_FIRST_UNLOCK_THIS_DEVICE_ONLY,
};

export const storage = {
  async saveUserId(userId: string): Promise<void> {
    try {
      await SecureStore.setItemAsync(USER_ID_KEY, userId, KEYCHAIN_OPTIONS);
    } catch (error) {
      console.error('Erreur lors de la sauvegarde de l\'UUID:', error);
      throw error; // Propager l'erreur pour que l'appelant puisse la gérer
    }
  },

  async getUserId(): Promise<string | null> {
    try {
      return await SecureStore.getItemAsync(USER_ID_KEY, KEYCHAIN_OPTIONS);
    } catch (error) {
      console.error('Erreur lors de la récupération de l\'UUID:', error);
      return null;
    }
  },

  async clearUserId(): Promise<void> {
    try {
      await SecureStore.deleteItemAsync(USER_ID_KEY, KEYCHAIN_OPTIONS);
    } catch (error) {
      console.error('Erreur lors de la suppression de l\'UUID:', error);
      throw error; // Propager l'erreur pour que l'appelant puisse la gérer
    }
  },
};
