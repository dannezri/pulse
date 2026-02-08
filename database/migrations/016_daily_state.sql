-- ============================================
-- MIGRATION 016 : daily_state - États latents physiologiques quotidiens
-- ============================================
-- Cette migration crée la table daily_state pour stocker les états latents
-- calculés quotidiennement (récupération, dette sommeil, surcharge, infection-like)

-- ============================================
-- 1. CRÉER LA TABLE daily_state
-- ============================================

CREATE TABLE IF NOT EXISTS daily_state (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    state_type TEXT NOT NULL, -- 'recovery', 'sleep_debt', 'overtrain', 'infection_like'
    state_date DATE NOT NULL, -- Jour local utilisateur (évite bugs timezone)
    score FLOAT NOT NULL, -- 0.0 to 1.0, raw score calculé
    smoothed_score FLOAT, -- 0.0 to 1.0, EMA lissé pour tendance
    confidence FLOAT NOT NULL, -- 0.0 to 1.0
    top_factors JSONB, -- Facteurs contributifs au format standardisé
    metadata JSONB, -- Données brutes pour debugging (EMA, raw_inputs, etc.)
    model_version TEXT NOT NULL DEFAULT 'latent_v1', -- Version algorithme (permet invalidation cache)
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT now(), -- Timestamp du calcul
    
    -- Constraint pour un seul état par type par jour par utilisateur
    UNIQUE(user_id, state_type, state_date)
);

COMMENT ON TABLE daily_state IS 
    'États latents physiologiques calculés quotidiennement (récupération, dette sommeil, surcharge, infection-like)';

COMMENT ON COLUMN daily_state.state_type IS 
    'Type d''état: recovery, sleep_debt, overtrain, infection_like';

COMMENT ON COLUMN daily_state.state_date IS 
    'Jour local utilisateur (DATE) - évite les bugs timezone';

COMMENT ON COLUMN daily_state.score IS 
    'Score brut calculé (0.0-1.0), réactif aux changements immédiats';

COMMENT ON COLUMN daily_state.smoothed_score IS 
    'Score lissé par EMA (0.0-1.0), représente la tendance stable';

COMMENT ON COLUMN daily_state.confidence IS 
    'Confiance du calcul (0.0-1.0) basée sur complétude des données';

COMMENT ON COLUMN daily_state.top_factors IS 
    'Facteurs principaux au format standardisé: [{"factor": "hrv_below_baseline", "direction": "down", "weight": 0.40, "evidence": {...}}]';

COMMENT ON COLUMN daily_state.metadata IS 
    'Métadonnées pour debugging: EMA (alpha, prev_smoothed), raw_inputs, calculation details';

COMMENT ON COLUMN daily_state.model_version IS 
    'Version de l''algorithme de calcul (ex: latent_v1) - permet invalidation cache quand formule change';

-- ============================================
-- 2. INDEX pour performance
-- ============================================

-- Index principal pour récupérer les états d'un utilisateur par date
CREATE INDEX IF NOT EXISTS idx_daily_state_user_date 
    ON daily_state(user_id, state_date DESC);

-- Index pour récupérer un type d'état spécifique
CREATE INDEX IF NOT EXISTS idx_daily_state_user_type_date 
    ON daily_state(user_id, state_type, state_date DESC);

-- Index pour filtrer par model_version (invalidation cache)
CREATE INDEX IF NOT EXISTS idx_daily_state_model_version 
    ON daily_state(model_version);

COMMENT ON INDEX idx_daily_state_user_date IS 
    'Index principal pour requêtes temporelles par utilisateur';

COMMENT ON INDEX idx_daily_state_user_type_date IS 
    'Index pour récupérer un type d''état spécifique (ex: tous les recovery)';

-- ============================================
-- 3. ROW LEVEL SECURITY (RLS)
-- ============================================

-- Activer RLS sur daily_state
ALTER TABLE daily_state ENABLE ROW LEVEL SECURITY;

-- Policy: Les utilisateurs peuvent voir leurs propres états
CREATE POLICY "Users can view own daily_state" ON daily_state
    FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Les utilisateurs peuvent insérer leurs propres états
CREATE POLICY "Users can insert own daily_state" ON daily_state
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy: Les utilisateurs peuvent mettre à jour leurs propres états
CREATE POLICY "Users can update own daily_state" ON daily_state
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Policy: Les utilisateurs peuvent supprimer leurs propres états
CREATE POLICY "Users can delete own daily_state" ON daily_state
    FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================
-- 4. VALIDATION CONSTRAINTS
-- ============================================

-- Vérifier que score est entre 0 et 1
ALTER TABLE daily_state ADD CONSTRAINT daily_state_score_range 
    CHECK (score >= 0.0 AND score <= 1.0);

-- Vérifier que smoothed_score est entre 0 et 1 (si non NULL)
ALTER TABLE daily_state ADD CONSTRAINT daily_state_smoothed_score_range 
    CHECK (smoothed_score IS NULL OR (smoothed_score >= 0.0 AND smoothed_score <= 1.0));

-- Vérifier que confidence est entre 0 et 1
ALTER TABLE daily_state ADD CONSTRAINT daily_state_confidence_range 
    CHECK (confidence >= 0.0 AND confidence <= 1.0);

-- Vérifier que state_type est valide
ALTER TABLE daily_state ADD CONSTRAINT daily_state_valid_type 
    CHECK (state_type IN ('recovery', 'sleep_debt', 'overtrain', 'infection_like'));

-- ============================================
-- 5. HELPER FUNCTION pour récupérer les états d'un jour
-- ============================================

CREATE OR REPLACE FUNCTION get_daily_states(
    p_user_id UUID,
    p_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    state_type TEXT,
    score FLOAT,
    smoothed_score FLOAT,
    confidence FLOAT,
    top_factors JSONB,
    metadata JSONB,
    model_version TEXT,
    calculated_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ds.state_type,
        ds.score,
        ds.smoothed_score,
        ds.confidence,
        ds.top_factors,
        ds.metadata,
        ds.model_version,
        ds.calculated_at
    FROM daily_state ds
    WHERE ds.user_id = p_user_id
      AND ds.state_date = p_date
    ORDER BY ds.state_type;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_daily_states IS 
    'Récupère tous les états latents d''un utilisateur pour un jour donné';
