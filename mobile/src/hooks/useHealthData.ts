import { useState, useEffect, useCallback } from 'react';
import { supabase } from '@/src/lib/supabase';
import { storage } from '@/src/lib/storage';

// Types
export interface Insight {
  id: string;
  instruction_text: string;
  category: string | null;
  priority: number;
  created_at: string;
}

export interface HealthProfile {
  id: string;
  user_id: string;
  profile_data: {
    current_metrics?: {
      hrv?: {
        average_ms?: number;
      };
      sleep?: {
        duration_minutes?: number;
      };
      heart_rate?: {
        resting_bpm?: number;
      };
    };
    baselines?: {
      hrv_baseline?: number;
      sleep_baseline?: number;
      hr_baseline?: number;
    };
    anomalies?: Array<{
      type: string;
      severity?: string;
    }>;
  };
  date: string;
  created_at: string;
}

export interface UserProfile {
  id: string;
  full_name: string | null;
  health_goal: string;
  open_wearables_user_id: string | null;
  baseline_hrv: number | null;
  baseline_resting_hr: number | null;
}

export interface UseHealthDataReturn {
  // Data
  latestInsight: Insight | null;
  healthProfile: HealthProfile | null;
  trends: HealthProfile[];
  userProfile: UserProfile | null;
  
  // Loading states
  loadingInsight: boolean;
  loadingHealthProfile: boolean;
  loadingTrends: boolean;
  loadingUserProfile: boolean;
  
  // Functions
  fetchLatestInsight: () => Promise<void>;
  fetchHealthProfile: () => Promise<void>;
  fetchTrends: () => Promise<void>;
  fetchUserProfile: () => Promise<void>;
  refreshAll: () => Promise<void>;
  
  // Update functions
  updateHealthGoal: (newGoal: string) => Promise<boolean>;
}

export function useHealthData(): UseHealthDataReturn {
  // State
  const [latestInsight, setLatestInsight] = useState<Insight | null>(null);
  const [healthProfile, setHealthProfile] = useState<HealthProfile | null>(null);
  const [trends, setTrends] = useState<HealthProfile[]>([]);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  
  // Loading states
  const [loadingInsight, setLoadingInsight] = useState(false);
  const [loadingHealthProfile, setLoadingHealthProfile] = useState(false);
  const [loadingTrends, setLoadingTrends] = useState(false);
  const [loadingUserProfile, setLoadingUserProfile] = useState(false);

  // Fetch latest insight
  const fetchLatestInsight = useCallback(async () => {
    setLoadingInsight(true);
    try {
      const userId = await storage.getUserId();
      if (!userId) {
        console.log('No user ID found, skipping insight fetch');
        setLatestInsight(null);
        setLoadingInsight(false);
        return;
      }

      console.log('Fetching latest insight for user:', userId);
      const { data, error, status, statusText } = await supabase
        .rpc('get_latest_insight', { p_user_id: userId });

      console.log('Insight query status:', status, statusText);
      if (error) {
        console.error('Error fetching latest insight:', error);
        console.error('Error details:', JSON.stringify(error, null, 2));
        setLatestInsight(null);
        return;
      }

      console.log('Latest insight data:', data);
      // RPC returns array, take first element
      const insight = Array.isArray(data) && data.length > 0 ? data[0] : null;
      console.log('Latest insight count:', insight ? 1 : 0);
      setLatestInsight(insight as Insight | null);
    } catch (error) {
      console.error('Exception fetching latest insight:', error);
      setLatestInsight(null);
    } finally {
      setLoadingInsight(false);
    }
  }, []);

  // Fetch latest health profile
  const fetchHealthProfile = useCallback(async () => {
    setLoadingHealthProfile(true);
    try {
      const userId = await storage.getUserId();
      if (!userId) {
        console.log('No user ID found, skipping health profile fetch');
        setHealthProfile(null);
        setLoadingHealthProfile(false);
        return;
      }

      console.log('Fetching health profile for user:', userId);
      const { data, error, status, statusText } = await supabase
        .rpc('get_latest_health_profile', { p_user_id: userId });

      console.log('Health profile query status:', status, statusText);
      if (error) {
        console.error('Error fetching health profile:', error);
        console.error('Error details:', JSON.stringify(error, null, 2));
        setHealthProfile(null);
        return;
      }

      console.log('Health profile data:', data);
      // RPC returns array, take first element
      const profile = Array.isArray(data) && data.length > 0 ? data[0] : null;
      if (profile) {
        console.log('Profile data structure:', JSON.stringify(profile.profile_data, null, 2));
      } else {
        console.log('No health profile found for user:', userId);
      }
      setHealthProfile(profile as HealthProfile | null);
    } catch (error) {
      console.error('Exception fetching health profile:', error);
      setHealthProfile(null);
    } finally {
      setLoadingHealthProfile(false);
    }
  }, []);

  // Fetch trends (7 last days)
  const fetchTrends = useCallback(async () => {
    setLoadingTrends(true);
    try {
      const userId = await storage.getUserId();
      if (!userId) {
        console.log('No user ID found, skipping trends fetch');
        setTrends([]);
        setLoadingTrends(false);
        return;
      }

      // Calculate date 7 days ago
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
      const sevenDaysAgoStr = sevenDaysAgo.toISOString().split('T')[0];

      console.log('Fetching trends for user:', userId, 'from date:', sevenDaysAgoStr);
      const { data, error, status, statusText } = await supabase
        .rpc('get_health_profiles_trends', { p_user_id: userId, p_days: 7 });

      console.log('Trends query status:', status, statusText);
      if (error) {
        console.error('Error fetching trends:', error);
        console.error('Error details:', JSON.stringify(error, null, 2));
        setTrends([]);
        return;
      }

      // RPC returns array directly
      const trendsData = Array.isArray(data) ? data : [];
      console.log('Trends data count:', trendsData.length);
      if (trendsData.length > 0) {
        console.log('First trend profile_data sample:', JSON.stringify(trendsData[0].profile_data, null, 2));
      } else {
        console.log('No trends found for user:', userId, 'from date:', sevenDaysAgoStr);
      }

      setTrends(trendsData as HealthProfile[]);
    } catch (error) {
      console.error('Exception fetching trends:', error);
      setTrends([]);
    } finally {
      setLoadingTrends(false);
    }
  }, []);

  // Fetch user profile
  const fetchUserProfile = useCallback(async () => {
    setLoadingUserProfile(true);
    try {
      const userId = await storage.getUserId();
      if (!userId) {
        console.log('No user ID found, skipping user profile fetch');
        setUserProfile(null);
        setLoadingUserProfile(false);
        return;
      }

      console.log('Fetching user profile for user:', userId);
      const { data, error, status, statusText } = await supabase
        .rpc('get_user_profile', { p_user_id: userId });

      console.log('User profile query status:', status, statusText);
      if (error) {
        console.error('Error fetching user profile:', error);
        console.error('Error details:', JSON.stringify(error, null, 2));
        setUserProfile(null);
        return;
      }

      console.log('User profile data:', data);
      // RPC returns array, take first element
      const profile = Array.isArray(data) && data.length > 0 ? data[0] : null;
      if (!profile) {
        console.log('No user profile found for user:', userId);
      }
      setUserProfile(profile as UserProfile | null);
    } catch (error) {
      console.error('Exception fetching user profile:', error);
      setUserProfile(null);
    } finally {
      setLoadingUserProfile(false);
    }
  }, []);

  // Refresh all data
  const refreshAll = useCallback(async () => {
    await Promise.all([
      fetchLatestInsight(),
      fetchHealthProfile(),
      fetchTrends(),
      fetchUserProfile(),
    ]);
  }, [fetchLatestInsight, fetchHealthProfile, fetchTrends, fetchUserProfile]);

  // Update health goal
  const updateHealthGoal = useCallback(async (newGoal: string): Promise<boolean> => {
    try {
      const userId = await storage.getUserId();
      if (!userId) {
        console.error('No user ID found, cannot update health goal');
        return false;
      }

      const { error } = await supabase
        .from('profiles')
        .update({ health_goal: newGoal })
        .eq('id', userId);

      if (error) {
        console.error('Error updating health goal:', error);
        return false;
      }

      // Refresh user profile after update
      await fetchUserProfile();
      return true;
    } catch (error) {
      console.error('Exception updating health goal:', error);
      return false;
    }
  }, [fetchUserProfile]);

  // Real-time subscription for insights
  useEffect(() => {
    let channel: any = null;

    const setupSubscription = async () => {
      const userId = await storage.getUserId();
      if (!userId) {
        console.log('No user ID found, skipping real-time subscription');
        return;
      }

      channel = supabase
        .channel('insights-changes')
        .on(
          'postgres_changes',
          {
            event: 'INSERT',
            schema: 'public',
            table: 'insights',
            filter: `user_id=eq.${userId}`,
          },
          (payload) => {
            console.log('New insight received:', payload.new);
            // Update the latest insight when a new one is inserted
            fetchLatestInsight();
          }
        )
        .subscribe();
    };

    setupSubscription();

    return () => {
      if (channel) {
        supabase.removeChannel(channel);
      }
    };
  }, [fetchLatestInsight]);

  return {
    // Data
    latestInsight,
    healthProfile,
    trends,
    userProfile,
    
    // Loading states
    loadingInsight,
    loadingHealthProfile,
    loadingTrends,
    loadingUserProfile,
    
    // Functions
    fetchLatestInsight,
    fetchHealthProfile,
    fetchTrends,
    fetchUserProfile,
    refreshAll,
    
    // Update functions
    updateHealthGoal,
  };
}
