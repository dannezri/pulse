import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import RNShake from 'react-native-shake';
import * as Haptics from 'expo-haptics';

/**
 * Hook pour rafraîchir les données lorsque l'utilisateur secoue le téléphone
 * 
 * Utilise react-native-shake pour détecter le geste et expo-haptics pour le feedback
 */
export function useShakeRefresh() {
  const queryClient = useQueryClient();

  useEffect(() => {
    // Écouter l'événement shake
    const subscription = RNShake.addListener(() => {
      console.log('[useShakeRefresh] Shake detected - Refreshing data');
      
      // Feedback haptique
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      
      // Invalider toutes les queries pour forcer un refresh
      queryClient.invalidateQueries();
    });

    // Cleanup
    return () => {
      subscription.remove();
    };
  }, [queryClient]);
}
