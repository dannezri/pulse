-- ============================================
-- MIGRATION 017 : user_conditions - Conditions de santé ICD-11
-- ============================================
-- Cette migration crée la table user_conditions pour stocker les pathologies
-- et conditions de santé des utilisateurs basées sur ICD-11 (WHO)

-- ============================================
-- 1. CRÉER LA TABLE user_conditions
-- ============================================

CREATE TABLE IF NOT EXISTS user_conditions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    system TEXT NOT NULL, -- 'icd11' (permet d'ajouter SNOMED CT ou autre plus tard)
    code TEXT NOT NULL, -- Code ICD-11 (ex: '6A70', 'GA34.3')
    display TEXT NOT NULL, -- Libellé de la condition au moment de la sélection
    category TEXT, -- Catégorie de la condition (ex: 'Troubles mentaux', 'Endocrinologie')
    severity TEXT, -- optional: 'mild', 'moderate', 'severe'
    diagnosed BOOLEAN DEFAULT NULL, -- optional: si la condition est diagnostiquée officiellement
    noted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, system, code)
);

COMMENT ON TABLE user_conditions IS 
    'Conditions de santé et pathologies des utilisateurs (basées sur ICD-11)';

COMMENT ON COLUMN user_conditions.system IS 
    'Système de classification: icd11 (WHO), peut être étendu à SNOMED CT plus tard';

COMMENT ON COLUMN user_conditions.code IS 
    'Code de la condition selon le système (ex: 6A70 pour TDAH dans ICD-11)';

COMMENT ON COLUMN user_conditions.display IS 
    'Libellé de la condition dans la langue de l''utilisateur au moment de la sélection';

COMMENT ON COLUMN user_conditions.category IS 
    'Catégorie de la condition pour faciliter l''affichage (ex: Troubles mentaux, Endocrinologie)';

COMMENT ON COLUMN user_conditions.severity IS 
    'Sévérité optionnelle: mild (léger), moderate (modéré), severe (sévère)';

COMMENT ON COLUMN user_conditions.diagnosed IS 
    'Indique si la condition a été officiellement diagnostiquée par un professionnel';

-- ============================================
-- 2. INDEX pour requêtes performantes
-- ============================================

CREATE INDEX idx_user_conditions_user ON user_conditions(user_id);
CREATE INDEX idx_user_conditions_system_code ON user_conditions(system, code);

-- ============================================
-- 3. ROW LEVEL SECURITY (RLS)
-- ============================================

ALTER TABLE user_conditions ENABLE ROW LEVEL SECURITY;

-- Policy SELECT: Les utilisateurs voient uniquement leurs propres conditions
CREATE POLICY "Users can view own conditions" ON user_conditions
    FOR SELECT USING (auth.uid() = user_id);

-- Policy INSERT: Les utilisateurs peuvent ajouter leurs propres conditions
CREATE POLICY "Users can insert own conditions" ON user_conditions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policy DELETE: Les utilisateurs peuvent supprimer leurs propres conditions
CREATE POLICY "Users can delete own conditions" ON user_conditions
    FOR DELETE USING (auth.uid() = user_id);

-- Policy UPDATE: Les utilisateurs peuvent modifier leurs propres conditions
CREATE POLICY "Users can update own conditions" ON user_conditions
    FOR UPDATE USING (auth.uid() = user_id);

-- ============================================
-- 4. TABLE CACHE pour recherches ICD-11
-- ============================================
-- Cache simple pour éviter de surcharger l'API WHO

CREATE TABLE IF NOT EXISTS terminology_cache (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    cache_key TEXT NOT NULL UNIQUE, -- Format: 'icd11:search:{lang}:{query}'
    cache_data JSONB NOT NULL, -- Résultats de la recherche
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '7 days')
);

COMMENT ON TABLE terminology_cache IS 
    'Cache pour les recherches de terminologie médicale (ICD-11, etc.) pour réduire les appels API';

COMMENT ON COLUMN terminology_cache.cache_key IS 
    'Clé unique du cache (ex: icd11:search:fr:depression)';

COMMENT ON COLUMN terminology_cache.cache_data IS 
    'Données cachées (résultats de recherche au format JSON)';

COMMENT ON COLUMN terminology_cache.expires_at IS 
    'Date d''expiration du cache (par défaut 7 jours)';

-- Index pour nettoyage automatique des entrées expirées
CREATE INDEX idx_terminology_cache_expires ON terminology_cache(expires_at);

-- Cette table n'a pas besoin de RLS car elle est gérée uniquement par le backend (service role)

-- ============================================
-- 5. FONCTIONS RPC
-- ============================================

-- Fonction pour récupérer les conditions d'un utilisateur
CREATE OR REPLACE FUNCTION get_user_conditions(p_user_id UUID)
RETURNS TABLE (
    id UUID,
    system TEXT,
    code TEXT,
    display TEXT,
    category TEXT,
    severity TEXT,
    diagnosed BOOLEAN,
    noted_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT uc.id, uc.system, uc.code, uc.display, uc.category, 
           uc.severity, uc.diagnosed, uc.noted_at
    FROM user_conditions uc
    WHERE uc.user_id = p_user_id
    ORDER BY uc.noted_at DESC;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_user_conditions IS 
    'Récupère les conditions de santé pour un utilisateur. S''appuie sur RLS pour la sécurité.';

-- Fonction pour nettoyer le cache expiré (à appeler via cron)
CREATE OR REPLACE FUNCTION clean_expired_terminology_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM terminology_cache
    WHERE expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION clean_expired_terminology_cache IS 
    'Nettoie les entrées expirées du cache de terminologie. À appeler périodiquement.';

-- ============================================
-- 6. GRANT PERMISSIONS
-- ============================================

-- Permettre aux utilisateurs authentifiés d'exécuter la fonction
GRANT EXECUTE ON FUNCTION get_user_conditions(UUID) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION clean_expired_terminology_cache() TO anon, authenticated;

-- ============================================
-- 7. VÉRIFICATION
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '=== MIGRATION 017 TERMINÉE ===';
    RAISE NOTICE 'Table user_conditions créée';
    RAISE NOTICE 'Table terminology_cache créée';
    RAISE NOTICE 'Index créés: user, system+code, expires';
    RAISE NOTICE 'RLS activé sur user_conditions';
    RAISE NOTICE 'Fonction RPC créée: get_user_conditions, clean_expired_terminology_cache';
    RAISE NOTICE '';
    RAISE NOTICE 'Systèmes supportés:';
    RAISE NOTICE '  - icd11 (WHO International Classification of Diseases)';
    RAISE NOTICE '  - Extensible à SNOMED CT plus tard';
    RAISE NOTICE '';
    RAISE NOTICE 'Cache terminology: TTL par défaut 7 jours';
END $$;
