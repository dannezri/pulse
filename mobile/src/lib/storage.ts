import * as SecureStore from 'expo-secure-store';

const USER_ID_KEY = 'pulse_user_id';

export const storage = {
  async saveUserId(userId: string): Promise<void> {
    try {
      await SecureStore.setItemAsync(USER_ID_KEY, userId);
    } catch (error) {
      console.error('Erreur lors de la sauvegarde de l\'UUID:', error);
    }
  },

  async getUserId(): Promise<string | null> {
    try {
      return await SecureStore.getItemAsync(USER_ID_KEY);
    } catch (error) {
      console.error('Erreur lors de la récupération de l\'UUID:', error);
      return null;
    }
  },

  async clearUserId(): Promise<void> {
    try {
      await SecureStore.deleteItemAsync(USER_ID_KEY);
    } catch (error) {
      console.error('Erreur lors de la suppression de l\'UUID:', error);
    }
  },
};
