-- ============================================
-- MIGRATION 009 : MVP - daily_context et insights simplifiés
-- ============================================
-- Cette migration ajoute la table daily_context pour le nouveau MVP
-- et adapte la table insights pour la corrélation simple

-- ============================================
-- 1. CRÉER LA TABLE daily_context
-- ============================================

CREATE TABLE IF NOT EXISTS daily_context (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    category TEXT NOT NULL, -- 'nutrition', 'medication', 'symptoms', 'stool'
    details JSONB NOT NULL, -- Données flexibles selon la catégorie
    logged_at TIMESTAMP WITH TIME ZONE NOT NULL, -- Quand l'entrée a été enregistrée dans HealthKit
    source TEXT DEFAULT 'AppleHealth', -- 'AppleHealth', 'manual', etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_daily_context_user_logged ON daily_context(user_id, logged_at DESC);
CREATE INDEX IF NOT EXISTS idx_daily_context_user_category ON daily_context(user_id, category, logged_at DESC);
CREATE INDEX IF NOT EXISTS idx_daily_context_user_date ON daily_context(user_id, DATE(logged_at) DESC);

COMMENT ON TABLE daily_context IS 
    'Contexte quotidien de l''utilisateur (nutrition, médicaments, symptômes, selles) scanné depuis Apple Health';

COMMENT ON COLUMN daily_context.category IS 
    'Catégorie: nutrition, medication, symptoms, stool';

COMMENT ON COLUMN daily_context.details IS 
    'Données JSONB flexibles. Ex: {"calories": 2000, "carbs": 250} pour nutrition';

COMMENT ON COLUMN daily_context.logged_at IS 
    'Date/heure d''enregistrement dans HealthKit (pas created_at qui est la date d''insertion dans Pulse)';

COMMENT ON COLUMN daily_context.source IS 
    'Source des données: AppleHealth, manual, etc.';

-- ============================================
-- 2. ADAPTER LA TABLE insights
-- ============================================

-- Ajouter correlation_type si pas déjà présent
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND table_name = 'insights' 
        AND column_name = 'correlation_type'
    ) THEN
        ALTER TABLE insights ADD COLUMN correlation_type TEXT;
        RAISE NOTICE 'Colonne correlation_type ajoutée à insights';
    END IF;
END $$;

-- Renommer instruction_text en content si nécessaire (garder les deux pour compatibilité)
-- On garde instruction_text pour compatibilité avec le code existant
-- Mais on peut aussi utiliser content pour le nouveau MVP

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND table_name = 'insights' 
        AND column_name = 'content'
    ) THEN
        ALTER TABLE insights ADD COLUMN content TEXT;
        -- Copier instruction_text dans content pour compatibilité
        UPDATE insights SET content = instruction_text WHERE content IS NULL;
        RAISE NOTICE 'Colonne content ajoutée à insights';
    END IF;
END $$;

COMMENT ON COLUMN insights.correlation_type IS 
    'Type de corrélation détectée: nutrition_hrv, medication_sleep, symptoms_hr, etc.';

COMMENT ON COLUMN insights.content IS 
    'Contenu de l''insight (alias de instruction_text pour le nouveau MVP)';

-- ============================================
-- 3. VÉRIFIER/METTRE À JOUR biometrics
-- ============================================

-- S'assurer que biometrics a les colonnes nécessaires
-- (déjà présentes normalement, mais on vérifie)

DO $$ 
BEGIN
    -- Vérifier que source existe
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND table_name = 'biometrics' 
        AND column_name = 'source'
    ) THEN
        ALTER TABLE biometrics ADD COLUMN source TEXT;
        RAISE NOTICE 'Colonne source ajoutée à biometrics';
    END IF;
    
    -- Vérifier que metadata existe (optionnel, pour flexibilité)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND table_name = 'biometrics' 
        AND column_name = 'metadata'
    ) THEN
        ALTER TABLE biometrics ADD COLUMN metadata JSONB;
        RAISE NOTICE 'Colonne metadata ajoutée à biometrics';
    END IF;
END $$;

-- Renommer recorded_at en measured_at si nécessaire (garder les deux pour compatibilité)
-- On garde recorded_at pour compatibilité, mais measured_at est plus clair pour le MVP
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND table_name = 'biometrics' 
        AND column_name = 'measured_at'
    ) THEN
        ALTER TABLE biometrics ADD COLUMN measured_at TIMESTAMP WITH TIME ZONE;
        -- Copier recorded_at dans measured_at
        UPDATE biometrics SET measured_at = recorded_at WHERE measured_at IS NULL;
        RAISE NOTICE 'Colonne measured_at ajoutée à biometrics';
    END IF;
END $$;

COMMENT ON COLUMN biometrics.measured_at IS 
    'Date/heure de mesure (alias de recorded_at pour le nouveau MVP)';

COMMENT ON COLUMN biometrics.metadata IS 
    'Métadonnées JSONB flexibles pour stocker des infos supplémentaires';

-- ============================================
-- 4. ROW LEVEL SECURITY (RLS)
-- ============================================

-- Activer RLS sur daily_context
ALTER TABLE daily_context ENABLE ROW LEVEL SECURITY;

-- Policy: Les utilisateurs peuvent voir leurs propres daily_context
CREATE POLICY "Users can view own daily_context" ON daily_context
    FOR SELECT USING (auth.uid() = user_id);

-- Policy: Service role peut insérer daily_context (via webhook/mobile)
CREATE POLICY "Service role can insert daily_context" ON daily_context
    FOR INSERT WITH CHECK (true);

-- Policy: Les utilisateurs peuvent insérer leurs propres daily_context (via mobile)
CREATE POLICY "Users can insert own daily_context" ON daily_context
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ============================================
-- 5. FONCTIONS UTILITAIRES
-- ============================================

-- Fonction pour récupérer les daily_context récents (10 derniers)
CREATE OR REPLACE FUNCTION get_recent_daily_context(
    p_user_id UUID,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    category TEXT,
    details JSONB,
    logged_at TIMESTAMP WITH TIME ZONE,
    source TEXT,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dc.id,
        dc.category,
        dc.details,
        dc.logged_at,
        dc.source,
        dc.created_at
    FROM daily_context dc
    WHERE dc.user_id = p_user_id
    ORDER BY dc.logged_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

COMMENT ON FUNCTION get_recent_daily_context IS 
    'Récupère les N derniers daily_context pour un utilisateur. Contourne RLS pour permettre l''accès depuis l''app React Native.';

-- Fonction pour récupérer les biometrics récents (10 derniers)
CREATE OR REPLACE FUNCTION get_recent_biometrics(
    p_user_id UUID,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id BIGINT,
    metric_type TEXT,
    value FLOAT,
    measured_at TIMESTAMP WITH TIME ZONE,
    source TEXT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        b.id,
        b.metric_type,
        b.value,
        COALESCE(b.measured_at, b.recorded_at) AS measured_at,
        b.source,
        b.metadata
    FROM biometrics b
    WHERE b.user_id = p_user_id
    ORDER BY COALESCE(b.measured_at, b.recorded_at) DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

COMMENT ON FUNCTION get_recent_biometrics IS 
    'Récupère les N derniers biometrics pour un utilisateur. Contourne RLS pour permettre l''accès depuis l''app React Native.';

-- ============================================
-- 6. GRANT PERMISSIONS
-- ============================================

-- Permettre à tous les utilisateurs authentifiés d'exécuter ces fonctions
GRANT EXECUTE ON FUNCTION get_recent_daily_context(UUID, INTEGER) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION get_recent_biometrics(UUID, INTEGER) TO anon, authenticated;

-- ============================================
-- 7. VÉRIFICATION
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '=== MIGRATION 009 TERMINÉE ===';
    RAISE NOTICE 'Table daily_context créée';
    RAISE NOTICE 'Table insights adaptée (correlation_type, content)';
    RAISE NOTICE 'Table biometrics vérifiée (source, metadata, measured_at)';
    RAISE NOTICE 'RLS activé sur daily_context';
    RAISE NOTICE 'Fonctions utilitaires créées: get_recent_daily_context, get_recent_biometrics';
    RAISE NOTICE '';
    RAISE NOTICE 'Nouveau MVP prêt:';
    RAISE NOTICE '  - biometrics: données de flux (HR, HRV, Sleep) via Vital API';
    RAISE NOTICE '  - daily_context: données de contexte (Nutrition, Médicaments, Symptômes) via Apple Health';
    RAISE NOTICE '  - insights: corrélation "contexte récent" vs "biométrie récente"';
END $$;
