-- ============================================
-- MIGRATION 020 : Baselines Robustes (Median/IQR)
-- ============================================
-- Cette migration remplace les baselines mean/std par median/IQR
-- pour une détection d'anomalies plus robuste aux outliers

-- ============================================
-- 1. BACKUP de l'ancienne table
-- ============================================

-- Renommer l'ancienne table (backup)
ALTER TABLE IF EXISTS user_baselines RENAME TO user_baselines_legacy;

-- Désactiver les policies sur l'ancienne table
ALTER TABLE IF EXISTS user_baselines_legacy DISABLE ROW LEVEL SECURITY;

-- ============================================
-- 2. CRÉER NOUVELLE TABLE user_baselines
-- ============================================

CREATE TABLE IF NOT EXISTS user_baselines (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    baseline_type TEXT NOT NULL, -- 'hrv', 'heart_rate', 'sleep_duration', etc.
    
    -- ========================================
    -- STATISTIQUES ROBUSTES (principal)
    -- ========================================
    median FLOAT NOT NULL,       -- Médiane (Q2) - résistant aux outliers
    iqr FLOAT NOT NULL,          -- Interquartile Range (Q3 - Q1)
    p25 FLOAT NOT NULL,          -- Percentile 25 (Q1)
    p75 FLOAT NOT NULL,          -- Percentile 75 (Q3)
    
    -- ========================================
    -- STATISTIQUES CLASSIQUES (optionnel)
    -- ========================================
    mean FLOAT,                  -- Moyenne arithmétique (pour graphiques)
    std FLOAT,                   -- Écart-type (pour graphiques)
    
    -- ========================================
    -- MÉTADONNÉES
    -- ========================================
    sample_count INTEGER NOT NULL,
    confidence TEXT NOT NULL CHECK (confidence IN ('low', 'medium', 'high')),
    model_version TEXT NOT NULL DEFAULT 'baseline_v2_robust',
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Contrainte unique
    UNIQUE(user_id, baseline_type, model_version)
);

-- Commentaires
COMMENT ON TABLE user_baselines IS 
    'Baselines personnelles avec statistiques robustes (median/IQR) résistantes aux outliers';

COMMENT ON COLUMN user_baselines.median IS 
    'Médiane (Q2) - valeur centrale robuste aux outliers';

COMMENT ON COLUMN user_baselines.iqr IS 
    'Interquartile Range (Q3-Q1) - dispersion robuste';

COMMENT ON COLUMN user_baselines.p25 IS 
    'Percentile 25 (Q1) - borne inférieure normale';

COMMENT ON COLUMN user_baselines.p75 IS 
    'Percentile 75 (Q3) - borne supérieure normale';

COMMENT ON COLUMN user_baselines.mean IS 
    'Moyenne arithmétique (optionnel, pour graphiques lisses)';

COMMENT ON COLUMN user_baselines.std IS 
    'Écart-type (optionnel, pour graphiques de confiance)';

COMMENT ON COLUMN user_baselines.confidence IS 
    'Confiance du calcul: low (<30 points), medium (30-59), high (≥60)';

COMMENT ON COLUMN user_baselines.model_version IS 
    'Version de l''algorithme (permet invalidation cache)';

-- ============================================
-- 3. INDEX pour performance
-- ============================================

-- Index principal : user + type
CREATE INDEX idx_baselines_user_type 
    ON user_baselines(user_id, baseline_type);

-- Index pour invalidation cache par version
CREATE INDEX idx_baselines_model_version 
    ON user_baselines(model_version);

-- Index pour requêtes temporelles
CREATE INDEX idx_baselines_calculated_at 
    ON user_baselines(calculated_at DESC);

-- ============================================
-- 4. ROW LEVEL SECURITY (RLS)
-- ============================================

-- Activer RLS
ALTER TABLE user_baselines ENABLE ROW LEVEL SECURITY;

-- Policy: Les utilisateurs peuvent voir leurs propres baselines
CREATE POLICY "Users can view own baselines" ON user_baselines
    FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Les utilisateurs peuvent insérer leurs baselines
CREATE POLICY "Users can insert own baselines" ON user_baselines
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy: Les utilisateurs peuvent mettre à jour leurs baselines
CREATE POLICY "Users can update own baselines" ON user_baselines
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Policy: Les utilisateurs peuvent supprimer leurs baselines
CREATE POLICY "Users can delete own baselines" ON user_baselines
    FOR DELETE
    USING (auth.uid() = user_id);

-- Policy: Service role peut tout faire (pour cron)
CREATE POLICY "Service role can manage all baselines" ON user_baselines
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- ============================================
-- 5. TRIGGER pour auto-update last_updated
-- ============================================

CREATE OR REPLACE FUNCTION update_baseline_last_updated()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_baseline_last_updated
    BEFORE UPDATE ON user_baselines
    FOR EACH ROW
    EXECUTE FUNCTION update_baseline_last_updated();

-- ============================================
-- 6. FONCTION RPC : Récupérer baselines
-- ============================================

CREATE OR REPLACE FUNCTION get_user_baselines_robust(
    p_user_id UUID,
    p_model_version TEXT DEFAULT 'baseline_v2_robust'
)
RETURNS TABLE (
    baseline_type TEXT,
    median FLOAT,
    iqr FLOAT,
    p25 FLOAT,
    p75 FLOAT,
    mean FLOAT,
    std FLOAT,
    sample_count INTEGER,
    confidence TEXT,
    calculated_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ub.baseline_type,
        ub.median,
        ub.iqr,
        ub.p25,
        ub.p75,
        ub.mean,
        ub.std,
        ub.sample_count,
        ub.confidence,
        ub.calculated_at
    FROM user_baselines ub
    WHERE ub.user_id = p_user_id
      AND ub.model_version = p_model_version
    ORDER BY ub.baseline_type;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_user_baselines_robust IS 
    'Récupère toutes les baselines robustes d''un utilisateur';

-- ============================================
-- 7. MIGRATION DES DONNÉES (optionnel)
-- ============================================

-- Option A: Forcer recalcul complet (RECOMMANDÉ)
-- Les nouvelles baselines seront calculées au prochain cron nocturne
-- Aucune migration nécessaire

-- Option B: Migrer avec approximations (si besoin de continuité immédiate)
-- Note: Pour distribution normale, IQR ≈ 1.35 * std et median ≈ mean

INSERT INTO user_baselines (
    user_id,
    baseline_type,
    median,
    iqr,
    p25,
    p75,
    mean,
    std,
    sample_count,
    confidence,
    model_version,
    calculated_at
)
SELECT 
    user_id,
    baseline_type,
    mean as median,                      -- Approximation: median ≈ mean si normale
    GREATEST(std * 1.35, 0.1) as iqr,   -- Approximation: IQR ≈ 1.35*std, min 0.1
    mean - (std * 0.675) as p25,        -- Q1 ≈ mean - 0.675*std
    mean + (std * 0.675) as p75,        -- Q3 ≈ mean + 0.675*std
    mean,
    std,
    sample_count,
    confidence,
    'baseline_v2_robust_migrated',      -- Version spéciale pour migration
    calculated_at
FROM user_baselines_legacy
WHERE mean IS NOT NULL AND std IS NOT NULL
ON CONFLICT (user_id, baseline_type, model_version) DO NOTHING;

-- ============================================
-- 8. VALIDATION
-- ============================================

-- Vérifier que les données migrées sont cohérentes
DO $$
DECLARE
    migrated_count INTEGER;
    legacy_count INTEGER;
BEGIN
    -- Compter baselines migrées
    SELECT COUNT(*) INTO migrated_count
    FROM user_baselines
    WHERE model_version = 'baseline_v2_robust_migrated';
    
    -- Compter baselines legacy
    SELECT COUNT(*) INTO legacy_count
    FROM user_baselines_legacy;
    
    -- Log
    RAISE NOTICE 'Migration completed: % baselines migrated from % legacy baselines', 
        migrated_count, legacy_count;
    
    -- Vérifier que median et IQR sont positifs
    IF EXISTS (
        SELECT 1 FROM user_baselines 
        WHERE median < 0 OR iqr < 0
    ) THEN
        RAISE EXCEPTION 'Invalid baselines detected: negative median or IQR';
    END IF;
END $$;

-- ============================================
-- 9. CLEANUP (à faire après validation en prod)
-- ============================================

-- À exécuter après validation que tout fonctionne:
-- DROP TABLE IF EXISTS user_baselines_legacy CASCADE;

-- ============================================
-- FIN DE LA MIGRATION
-- ============================================
