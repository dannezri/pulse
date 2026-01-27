import { useEffect, useState } from 'react';
import { storage } from '../lib/storage';

export function useAuth() {
  const [userId, setUserId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get userId from local storage
    storage.getUserId().then((id) => {
      setUserId(id);
      setLoading(false);
    });
  }, []);

  const signOut = async () => {
    await storage.clearUserId();
    setUserId(null);
  };

  return {
    userId,
    loading,
    signOut,
  };
}
