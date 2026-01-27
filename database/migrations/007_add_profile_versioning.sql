-- ============================================
-- MIGRATION 007 : Versioning du format de profil de santé
-- ============================================
-- Cette migration ajoute le versioning pour permettre l'évolution du schéma JSON
-- sans casser l'application existante

-- ============================================
-- 1. AJOUT DES CHAMPS DE VERSION
-- ============================================

-- Ajouter profile_version à health_profiles
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND table_name = 'health_profiles' 
        AND column_name = 'profile_version'
    ) THEN
        ALTER TABLE health_profiles ADD COLUMN profile_version INTEGER DEFAULT 1;
        RAISE NOTICE 'Colonne profile_version ajoutée à health_profiles';
    END IF;
END $$;

-- Ajouter normalizer_version à health_profiles
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND table_name = 'health_profiles' 
        AND column_name = 'normalizer_version'
    ) THEN
        ALTER TABLE health_profiles ADD COLUMN normalizer_version TEXT;
        RAISE NOTICE 'Colonne normalizer_version ajoutée à health_profiles';
    END IF;
END $$;

-- Ajouter schema_version à health_profiles (optionnel, pour référence)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND table_name = 'health_profiles' 
        AND column_name = 'schema_version'
    ) THEN
        ALTER TABLE health_profiles ADD COLUMN schema_version TEXT;
        RAISE NOTICE 'Colonne schema_version ajoutée à health_profiles';
    END IF;
END $$;

-- ============================================
-- 2. MISE À JOUR DES DONNÉES EXISTANTES
-- ============================================

-- Marquer les profils existants comme version 1
UPDATE health_profiles 
SET profile_version = 1 
WHERE profile_version IS NULL;

-- ============================================
-- 3. INDEX POUR LES REQUÊTES PAR VERSION
-- ============================================

-- Index pour filtrer par version (utile pour migration/recalcul)
CREATE INDEX IF NOT EXISTS idx_health_profiles_version 
    ON health_profiles(user_id, profile_version, date DESC);

COMMENT ON INDEX idx_health_profiles_version IS 
    'Index pour filtrer les profils par version. Utile pour identifier les profils à recalculer.';

-- ============================================
-- 4. COMMENTAIRES
-- ============================================

COMMENT ON COLUMN health_profiles.profile_version IS 
    'Version du format JSON du profil (ex: 1, 2, 3). Permet l''évolution du schéma sans casser l''app.';

COMMENT ON COLUMN health_profiles.normalizer_version IS 
    'Version du normalizer utilisé pour générer ce profil (ex: "1.0.0", "1.1.0"). Utile pour le debugging.';

COMMENT ON COLUMN health_profiles.schema_version IS 
    'Version du schéma de données source (optionnel). Référence pour traçabilité.';

-- ============================================
-- 5. FONCTIONS UTILITAIRES
-- ============================================

-- Fonction pour obtenir les profils d'une version spécifique
CREATE OR REPLACE FUNCTION get_profiles_by_version(
    p_user_id UUID,
    p_profile_version INTEGER
)
RETURNS TABLE (
    id UUID,
    date DATE,
    profile_version INTEGER,
    normalizer_version TEXT,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        hp.id,
        hp.date,
        hp.profile_version,
        hp.normalizer_version,
        hp.created_at
    FROM health_profiles hp
    WHERE hp.user_id = p_user_id
      AND hp.profile_version = p_profile_version
    ORDER BY hp.date DESC;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_profiles_by_version IS 
    'Retourne tous les profils d''un utilisateur pour une version donnée. Utile pour identifier les profils à recalculer.';

-- Fonction pour compter les profils par version
CREATE OR REPLACE FUNCTION count_profiles_by_version(p_user_id UUID)
RETURNS TABLE (
    profile_version INTEGER,
    count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        hp.profile_version,
        COUNT(*)::BIGINT
    FROM health_profiles hp
    WHERE hp.user_id = p_user_id
    GROUP BY hp.profile_version
    ORDER BY hp.profile_version;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION count_profiles_by_version IS 
    'Compte les profils d''un utilisateur par version. Utile pour vérifier la distribution des versions.';

-- ============================================
-- 6. VÉRIFICATION
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '=== MIGRATION 007 TERMINÉE ===';
    RAISE NOTICE 'Champs de version ajoutés: profile_version, normalizer_version, schema_version';
    RAISE NOTICE 'Profils existants marqués comme version 1';
    RAISE NOTICE 'Fonctions utilitaires créées pour gérer les versions';
    RAISE NOTICE '';
    RAISE NOTICE 'Pour recalculer les profils d''une version:';
    RAISE NOTICE '  SELECT * FROM get_profiles_by_version(user_id, 1);';
END $$;
