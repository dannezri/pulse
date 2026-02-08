-- ============================================
-- MIGRATION 029 : daily_energy - Score d'énergie quotidien consolidé
-- ============================================
-- Cette migration crée la table daily_energy pour stocker le score d'énergie
-- quotidien calculé à partir des états latents (recovery, sleep_debt, overtrain, infection)

-- ============================================
-- 1. CRÉER LA TABLE daily_energy
-- ============================================

CREATE TABLE IF NOT EXISTS daily_energy (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    energy_date DATE NOT NULL, -- Jour local utilisateur
    energy_score FLOAT NOT NULL, -- 0.0 to 1.0, score d'énergie global
    label TEXT NOT NULL, -- 'Excellente journée', 'Bonne journée', 'Journée moyenne', 'Journée fragile'
    confidence FLOAT NOT NULL, -- 0.0 to 1.0, moyenne pondérée des confidences des states
    reasons JSONB NOT NULL, -- Array de raisons [{key, text}]
    primary_action JSONB NOT NULL, -- Action unique du jour {key, title, why}
    risk_windows JSONB, -- Array de creux prévus [{from, to, risk, text}]
    components JSONB, -- Détail des composants {recovery, sleep_debt, overtrain, infection}
    model_version TEXT NOT NULL DEFAULT 'energy_v1', -- Version de l'algorithme
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT now(), -- Timestamp du calcul
    
    -- Constraint pour un seul energy par jour par utilisateur
    UNIQUE(user_id, energy_date)
);

COMMENT ON TABLE daily_energy IS 
    'Score d''énergie quotidien consolidé calculé à partir des états latents (recovery, sleep_debt, overtrain, infection)';

COMMENT ON COLUMN daily_energy.energy_date IS 
    'Jour local utilisateur (DATE) - évite les bugs timezone';

COMMENT ON COLUMN daily_energy.energy_score IS 
    'Score d''énergie global (0.0-1.0), agrégation pondérée des états latents';

COMMENT ON COLUMN daily_energy.label IS 
    'Label lifestyle: Excellente journée, Bonne journée, Journée moyenne, Journée fragile';

COMMENT ON COLUMN daily_energy.confidence IS 
    'Confiance du calcul (0.0-1.0), moyenne pondérée des confidences des états latents';

COMMENT ON COLUMN daily_energy.reasons IS 
    'Top 2-3 raisons expliquant le score: [{"key": "recovery_good", "text": "Excellente récupération"}]';

COMMENT ON COLUMN daily_energy.primary_action IS 
    'Action clé unique du jour: {"key": "deep_work_morning", "title": "...", "why": "..."}';

COMMENT ON COLUMN daily_energy.risk_windows IS 
    'Creux d''énergie prévus: [{"from": "16:00", "to": "18:00", "risk": "dip", "text": "..."}]';

COMMENT ON COLUMN daily_energy.components IS 
    'Détail des composants normalisés: {"recovery": 0.72, "sleep_debt": 0.65, "overtrain": 0.60, "infection": 0.75}';

COMMENT ON COLUMN daily_energy.model_version IS 
    'Version de l''algorithme de calcul (ex: energy_v1) - permet invalidation cache quand formule change';

-- ============================================
-- 2. INDEX pour performance
-- ============================================

-- Index principal pour récupérer l'énergie d'un utilisateur par date
CREATE INDEX IF NOT EXISTS idx_daily_energy_user_date 
    ON daily_energy(user_id, energy_date DESC);

-- Index pour filtrer par model_version (invalidation cache)
CREATE INDEX IF NOT EXISTS idx_daily_energy_model_version 
    ON daily_energy(model_version);

COMMENT ON INDEX idx_daily_energy_user_date IS 
    'Index principal pour requêtes temporelles par utilisateur';

-- ============================================
-- 3. ROW LEVEL SECURITY (RLS)
-- ============================================

-- Activer RLS sur daily_energy
ALTER TABLE daily_energy ENABLE ROW LEVEL SECURITY;

-- Policy: Les utilisateurs peuvent voir leur propre énergie
CREATE POLICY "Users can view own daily_energy" ON daily_energy
    FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Les utilisateurs peuvent insérer leur propre énergie
CREATE POLICY "Users can insert own daily_energy" ON daily_energy
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy: Les utilisateurs peuvent mettre à jour leur propre énergie
CREATE POLICY "Users can update own daily_energy" ON daily_energy
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Policy: Les utilisateurs peuvent supprimer leur propre énergie
CREATE POLICY "Users can delete own daily_energy" ON daily_energy
    FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================
-- 4. VALIDATION CONSTRAINTS
-- ============================================

-- Vérifier que energy_score est entre 0 et 1
ALTER TABLE daily_energy ADD CONSTRAINT daily_energy_score_range 
    CHECK (energy_score >= 0.0 AND energy_score <= 1.0);

-- Vérifier que confidence est entre 0 et 1
ALTER TABLE daily_energy ADD CONSTRAINT daily_energy_confidence_range 
    CHECK (confidence >= 0.0 AND confidence <= 1.0);

-- Vérifier que label est valide
ALTER TABLE daily_energy ADD CONSTRAINT daily_energy_valid_label 
    CHECK (label IN ('Excellente journée', 'Bonne journée', 'Journée moyenne', 'Journée fragile'));

-- ============================================
-- 5. HELPER FUNCTION pour récupérer l'énergie d'un jour
-- ============================================

CREATE OR REPLACE FUNCTION get_daily_energy_by_date(
    p_user_id UUID,
    p_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    energy_score FLOAT,
    label TEXT,
    confidence FLOAT,
    reasons JSONB,
    primary_action JSONB,
    risk_windows JSONB,
    components JSONB,
    model_version TEXT,
    calculated_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        de.energy_score,
        de.label,
        de.confidence,
        de.reasons,
        de.primary_action,
        de.risk_windows,
        de.components,
        de.model_version,
        de.calculated_at
    FROM daily_energy de
    WHERE de.user_id = p_user_id
      AND de.energy_date = p_date;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_daily_energy_by_date IS 
    'Récupère le daily_energy d''un utilisateur pour un jour donné';
