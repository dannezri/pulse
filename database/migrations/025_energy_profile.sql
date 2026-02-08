-- Migration 025: Energy Profile
-- Table pour stocker le profil énergétique personnel de chaque utilisateur
-- Patterns appris sur le long terme (ex: "Tu récupères mieux avec 7h45 de sommeil")

-- Table: user_energy_profile
CREATE TABLE IF NOT EXISTS user_energy_profile (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Type de trait personnel
    trait_type TEXT NOT NULL,
    -- 'optimal_sleep_duration', 'caffeine_cutoff', 'late_exercise_impact',
    -- 'optimal_meal_timing', 'alcohol_sensitivity', 'stress_resilience',
    -- 'morning_recovery', 'protein_requirement', 'hydration_threshold', etc.
    
    -- Catégorie
    category TEXT NOT NULL,
    -- 'sleep', 'nutrition', 'exercise', 'recovery', 'stress', 'timing'
    
    -- Titre court
    title TEXT NOT NULL,
    -- Ex: "Sommeil optimal: 7h45"
    
    -- Description détaillée
    description TEXT NOT NULL,
    -- Ex: "Tu récupères mieux avec 7h45 de sommeil qu'avec 8h ou 9h"
    
    -- Valeur numérique (si applicable)
    value_numeric DECIMAL,
    -- Ex: 7.75 pour 7h45
    
    -- Valeur texte (si applicable)
    value_text TEXT,
    -- Ex: "14h00" pour cutoff caféine
    
    -- Score de confiance (0-1)
    confidence DECIMAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    -- Basé sur nombre de data points et cohérence
    
    -- Métriques support
    support_data JSONB,
    -- {
    --   "sample_size": 45,
    --   "correlation": 0.78,
    --   "average_impact": "+12%",
    --   "best_case": { "hrv": 58, "recovery": 85 },
    --   "worst_case": { "hrv": 48, "recovery": 62 }
    -- }
    
    -- Metadata
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_validated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data_points_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Contraintes
    CONSTRAINT unique_user_trait UNIQUE(user_id, trait_type)
);

-- Index pour requêtes rapides
CREATE INDEX idx_energy_profile_user ON user_energy_profile(user_id) WHERE is_active = TRUE;
CREATE INDEX idx_energy_profile_category ON user_energy_profile(category) WHERE is_active = TRUE;
CREATE INDEX idx_energy_profile_confidence ON user_energy_profile(confidence DESC);

-- RLS Policies
ALTER TABLE user_energy_profile ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only read their own profile
CREATE POLICY "Users can view own energy profile"
    ON user_energy_profile
    FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: System can insert (backend cron job)
CREATE POLICY "System can insert energy profile"
    ON user_energy_profile
    FOR INSERT
    WITH CHECK (auth.uid() = user_id OR auth.jwt()->>'role' = 'service_role');

-- Policy: System can update (backend cron job)
CREATE POLICY "System can update energy profile"
    ON user_energy_profile
    FOR UPDATE
    USING (auth.uid() = user_id OR auth.jwt()->>'role' = 'service_role');

-- RPC Function: Get active energy profile for a user
CREATE OR REPLACE FUNCTION get_user_energy_profile(p_user_id UUID)
RETURNS TABLE (
    id UUID,
    trait_type TEXT,
    category TEXT,
    title TEXT,
    description TEXT,
    value_numeric DECIMAL,
    value_text TEXT,
    confidence DECIMAL,
    support_data JSONB,
    discovered_at TIMESTAMP WITH TIME ZONE,
    last_validated TIMESTAMP WITH TIME ZONE,
    data_points_count INTEGER
) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        uep.id,
        uep.trait_type,
        uep.category,
        uep.title,
        uep.description,
        uep.value_numeric,
        uep.value_text,
        uep.confidence,
        uep.support_data,
        uep.discovered_at,
        uep.last_validated,
        uep.data_points_count
    FROM user_energy_profile uep
    WHERE uep.user_id = p_user_id
      AND uep.is_active = TRUE
    ORDER BY uep.confidence DESC, uep.category ASC;
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION get_user_energy_profile(UUID) TO authenticated;

-- Comment
COMMENT ON TABLE user_energy_profile IS 'Profil énergétique personnel - Patterns appris sur le long terme pour chaque utilisateur';
COMMENT ON COLUMN user_energy_profile.trait_type IS 'Type de trait personnel (ex: optimal_sleep_duration, caffeine_cutoff)';
COMMENT ON COLUMN user_energy_profile.confidence IS 'Score de confiance (0-1) basé sur nombre de data points et cohérence';
COMMENT ON COLUMN user_energy_profile.support_data IS 'Métriques support (sample_size, correlation, average_impact, etc.)';
