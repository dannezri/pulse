-- ============================================
-- MIGRATION 031: Pulse Energy Decay Model
-- ============================================
-- Extension du schéma pour supporter le modèle mathématique précis d'énergie
-- Basé sur: readiness Oura, HRV Z-Score, pharmacocinétique, conditions

-- 1. Extension de la table profiles pour inclure medications et conditions
ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS medications JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS conditions JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS chronotype TEXT DEFAULT 'neutral'; -- 'morning', 'evening', 'neutral'

COMMENT ON COLUMN profiles.medications IS 'Liste des médicaments avec horaires et types: [{"name": "L-Thyroxin", "time": "08:00", "type": "stimulant", "dose": "50mcg"}]';
COMMENT ON COLUMN profiles.conditions IS 'Conditions de santé actuelles: ["fatigue_chronique", "infection", "overtrain"]';

-- 2. Nouvelle table: health_profiles (profil santé quotidien)
CREATE TABLE IF NOT EXISTS health_profiles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    profile_date DATE NOT NULL,
    
    -- Métriques actuelles
    current_metrics JSONB DEFAULT '{}'::jsonb,
    /* Structure:
    {
        "readiness_score": 85,        -- Score Oura 0-100
        "hrv_ms": 65,                  -- HRV du jour
        "resting_hr": 58,              -- RHR du jour
        "sleep_score": 82,             -- Score sommeil
        "activity_score": 75,          -- Score activité
        "temperature_deviation": 0.2   -- Écart température corporelle
    }
    */
    
    -- Anomalies détectées
    anomalies JSONB DEFAULT '[]'::jsonb,
    /* Structure:
    [
        {"type": "hrv_drop", "severity": "high", "z_score": -2.3, "detected_at": "2026-01-31T08:00:00Z"},
        {"type": "temp_spike", "severity": "medium", "value": 37.8}
    ]
    */
    
    -- Métadonnées
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Contraintes
    UNIQUE(user_id, profile_date)
);

-- Index pour requêtes rapides
CREATE INDEX idx_health_profiles_user_date ON health_profiles(user_id, profile_date DESC);

-- RLS Policies
ALTER TABLE health_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own health profiles"
    ON health_profiles FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own health profiles"
    ON health_profiles FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own health profiles"
    ON health_profiles FOR UPDATE
    USING (auth.uid() = user_id);

-- 3. Extension de intraday_energy_forecast pour inclure les influencers
ALTER TABLE intraday_energy_forecast
ADD COLUMN IF NOT EXISTS influencers JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS calculation_model TEXT DEFAULT 'heuristic_v1';

COMMENT ON COLUMN intraday_energy_forecast.influencers IS 'Facteurs d''influence avec impacts: [{"name": "Sommeil", "impact": "+85", "status": "positive"}]';
COMMENT ON COLUMN intraday_energy_forecast.calculation_model IS 'Modèle de calcul utilisé: heuristic_v1, pulse_energy_decay_v1';

-- 4. Fonction helper: Récupérer le profil santé du jour
CREATE OR REPLACE FUNCTION get_today_health_profile(p_user_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_profile JSONB;
BEGIN
    SELECT jsonb_build_object(
        'readiness_score', COALESCE((current_metrics->>'readiness_score')::int, 0),
        'hrv_ms', COALESCE((current_metrics->>'hrv_ms')::int, 0),
        'anomalies', COALESCE(anomalies, '[]'::jsonb),
        'profile_date', TO_CHAR(health_profiles.profile_date, 'YYYY-MM-DD')
    )
    INTO v_profile
    FROM health_profiles
    WHERE health_profiles.user_id = p_user_id
      AND health_profiles.profile_date = CURRENT_DATE
    LIMIT 1;
    
    RETURN COALESCE(v_profile, '{}'::jsonb);
END;
$$;

-- 5. Fonction helper: Récupérer les médicaments actifs
CREATE OR REPLACE FUNCTION get_active_medications(p_user_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_medications JSONB;
BEGIN
    SELECT medications
    INTO v_medications
    FROM profiles
    WHERE id = p_user_id;
    
    RETURN COALESCE(v_medications, '[]'::jsonb);
END;
$$;

-- 6. Fonction helper: Récupérer les conditions de santé
CREATE OR REPLACE FUNCTION get_health_conditions(p_user_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_conditions JSONB;
BEGIN
    SELECT conditions
    INTO v_conditions
    FROM profiles
    WHERE id = p_user_id;
    
    RETURN COALESCE(v_conditions, '[]'::jsonb);
END;
$$;

COMMENT ON FUNCTION get_today_health_profile IS 'Récupère le profil santé du jour pour calcul Pulse Energy Decay';
COMMENT ON FUNCTION get_active_medications IS 'Récupère la liste des médicaments avec pharmacocinétique';
COMMENT ON FUNCTION get_health_conditions IS 'Récupère les conditions de santé actives (fatigue, infection, etc.)';
