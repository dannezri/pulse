// Types de base de données Pulse

export interface Insight {
  id: string;
  user_id: string;
  instruction_text: string;
  content: string | null;
  category: string | null;
  priority: number;
  is_read: boolean;
  created_at: string;
  correlation_type: string | null;
}

export interface Profile {
  id: string;
  full_name: string | null;
  baseline_hrv: number | null;
  baseline_resting_hr: number | null;
  open_wearables_user_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface HealthProfile {
  id: string;
  user_id: string;
  date: string;
  profile_data: any; // JSONB flexible
  created_at: string;
}
