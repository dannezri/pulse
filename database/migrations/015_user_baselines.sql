-- ============================================
-- MIGRATION 015 : user_baselines - Baselines personnelles dynamiques
-- ============================================
-- Cette migration crée la table user_baselines pour stocker les baselines
-- calculées pour chaque utilisateur (sommeil, HRV, sensibilités, etc.)

-- ============================================
-- 1. CRÉER LA TABLE user_baselines
-- ============================================

CREATE TABLE IF NOT EXISTS user_baselines (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    baseline_type TEXT NOT NULL, -- 'sleep', 'hrv', 'caffeine_sensitivity', 'alcohol_sensitivity', 'recovery_time', 'late_meal_impact', 'chronotype'
    baseline_data JSONB NOT NULL, -- Structure standardisée: {value, unit, normal_range, trend, details}
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    confidence FLOAT DEFAULT 0.0, -- 0.0 à 1.0
    sample_size INTEGER DEFAULT 0, -- Nombre de données utilisées
    
    -- Champs critiques pour debugging et traçabilité
    model_version TEXT NOT NULL DEFAULT 'v1', -- Version de l'algorithme de calcul
    window_start TIMESTAMPTZ, -- Début de la période de calcul
    window_end TIMESTAMPTZ, -- Fin de la période de calcul
    status TEXT NOT NULL DEFAULT 'ok', -- 'ok' | 'insufficient_data' | 'error'
    error_message TEXT, -- Message d'erreur si status != 'ok'
    
    UNIQUE(user_id, baseline_type)
);

COMMENT ON TABLE user_baselines IS 
    'Baselines personnelles calculées pour chaque utilisateur (normalisation dynamique)';

COMMENT ON COLUMN user_baselines.baseline_type IS 
    'Type de baseline: sleep, hrv, caffeine_sensitivity, alcohol_sensitivity, recovery_time, late_meal_impact, chronotype';

COMMENT ON COLUMN user_baselines.baseline_data IS 
    'Structure JSONB standardisée: {value: number, unit: string, normal_range: {min, max}, trend: {slope_per_week, direction}, details: {...}}';

COMMENT ON COLUMN user_baselines.confidence IS 
    'Score de confiance (0-1) calculé selon: sample_factor * data_quality_factor * window_factor';

COMMENT ON COLUMN user_baselines.model_version IS 
    'Version de l''algorithme de calcul (permet de comparer les résultats entre versions)';

COMMENT ON COLUMN user_baselines.window_start IS 
    'Date de début de la période de données utilisée pour le calcul';

COMMENT ON COLUMN user_baselines.window_end IS 
    'Date de fin de la période de données utilisée pour le calcul';

COMMENT ON COLUMN user_baselines.status IS 
    'Statut du calcul: ok (succès), insufficient_data (pas assez de données), error (erreur)';

-- ============================================
-- 2. INDEX pour requêtes performantes
-- ============================================

CREATE INDEX idx_user_baselines_user ON user_baselines(user_id);
CREATE INDEX idx_user_baselines_type ON user_baselines(user_id, baseline_type);
CREATE INDEX idx_user_baselines_status ON user_baselines(user_id, status);

-- ============================================
-- 3. ROW LEVEL SECURITY (RLS)
-- ============================================

ALTER TABLE user_baselines ENABLE ROW LEVEL SECURITY;

-- Policy SELECT: Les utilisateurs voient uniquement leurs propres baselines
CREATE POLICY "Users can view own baselines" ON user_baselines
    FOR SELECT USING (auth.uid() = user_id);

-- Policy INSERT: Uniquement pour les utilisateurs (en pratique, seul le backend via service role)
CREATE POLICY "Users can insert own baselines" ON user_baselines
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policy UPDATE: Uniquement pour les utilisateurs (en pratique, seul le backend via service role)
CREATE POLICY "Users can update own baselines" ON user_baselines
    FOR UPDATE USING (auth.uid() = user_id);

-- Note: Le backend utilise SUPABASE_SERVICE_KEY qui bypass automatiquement RLS
-- Pas besoin de policy spéciale "WITH CHECK (true)" pour le service role

-- ============================================
-- 4. FONCTIONS RPC
-- ============================================

-- Fonction pour récupérer les baselines d'un utilisateur
-- Sans SECURITY DEFINER pour s'appuyer sur RLS
CREATE OR REPLACE FUNCTION get_user_baselines(p_user_id UUID)
RETURNS TABLE (
    baseline_type TEXT,
    baseline_data JSONB,
    calculated_at TIMESTAMP WITH TIME ZONE,
    confidence FLOAT,
    sample_size INTEGER,
    model_version TEXT,
    window_start TIMESTAMPTZ,
    window_end TIMESTAMPTZ,
    status TEXT,
    error_message TEXT
) AS $$
BEGIN
    -- Pas de SECURITY DEFINER = RLS actif
    -- L'utilisateur ne peut lire que ses propres baselines
    RETURN QUERY
    SELECT ub.baseline_type, ub.baseline_data, ub.calculated_at, 
           ub.confidence, ub.sample_size, ub.model_version,
           ub.window_start, ub.window_end, ub.status, ub.error_message
    FROM user_baselines ub
    WHERE ub.user_id = p_user_id
    ORDER BY ub.baseline_type;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_user_baselines IS 
    'Récupère les baselines pour un utilisateur. S''appuie sur RLS pour la sécurité.';

-- ============================================
-- 5. GRANT PERMISSIONS
-- ============================================

-- Permettre aux utilisateurs authentifiés d'exécuter la fonction
GRANT EXECUTE ON FUNCTION get_user_baselines(UUID) TO anon, authenticated;

-- ============================================
-- 6. VÉRIFICATION
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '=== MIGRATION 015 TERMINÉE ===';
    RAISE NOTICE 'Table user_baselines créée';
    RAISE NOTICE 'Index créés: user, type, status';
    RAISE NOTICE 'RLS activé sur user_baselines';
    RAISE NOTICE 'Fonction RPC créée: get_user_baselines';
    RAISE NOTICE '';
    RAISE NOTICE 'Structure baseline_data standardisée:';
    RAISE NOTICE '  {value, unit, normal_range: {min, max}, trend: {slope_per_week, direction}, details}';
    RAISE NOTICE '';
    RAISE NOTICE 'Formule de confiance unifiée:';
    RAISE NOTICE '  confidence = sample_factor * data_quality_factor * window_factor';
END $$;
