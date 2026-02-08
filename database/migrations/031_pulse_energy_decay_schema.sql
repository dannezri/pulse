-- ============================================
-- MIGRATION 031: Pulse Energy Decay Schema
-- ============================================
-- Extension du schéma pour supporter le modèle mathématique précis d'énergie

-- 1. Extension de la table profiles pour inclure medications et conditions
ALTER TABLE profiles 
ADD COLUMN IF NOT EXISTS medications JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS conditions JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS chronotype TEXT DEFAULT 'neutral';

-- 2. Nouvelle table: health_profiles (profil santé quotidien)
CREATE TABLE IF NOT EXISTS health_profiles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    profile_date DATE NOT NULL,
    current_metrics JSONB DEFAULT '{}'::jsonb,
    anomalies JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, profile_date)
);

-- 3. Index pour requêtes rapides
CREATE INDEX IF NOT EXISTS idx_health_profiles_user_date ON health_profiles(user_id, profile_date DESC);

-- 4. RLS Policies
ALTER TABLE health_profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own health profiles" ON health_profiles;
CREATE POLICY "Users can view their own health profiles"
    ON health_profiles FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own health profiles" ON health_profiles;
CREATE POLICY "Users can insert their own health profiles"
    ON health_profiles FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own health profiles" ON health_profiles;
CREATE POLICY "Users can update their own health profiles"
    ON health_profiles FOR UPDATE
    USING (auth.uid() = user_id);

-- 5. Extension de intraday_energy_forecast pour inclure les influencers
ALTER TABLE intraday_energy_forecast
ADD COLUMN IF NOT EXISTS influencers JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS calculation_model TEXT DEFAULT 'heuristic_v1';
