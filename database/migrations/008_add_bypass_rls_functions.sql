-- ============================================
-- MIGRATION 008 : Fonctions pour contourner RLS
-- ============================================
-- Ces fonctions permettent à l'app React Native d'accéder aux données
-- sans authentification Supabase Auth (utilise l'UUID stocké localement)

-- ============================================
-- 1. FONCTION : Récupérer le profil utilisateur par UUID
-- ============================================

CREATE OR REPLACE FUNCTION get_user_profile(p_user_id UUID)
RETURNS TABLE (
    id UUID,
    full_name TEXT,
    health_goal TEXT,
    open_wearables_user_id TEXT,
    baseline_hrv INTEGER,
    baseline_resting_hr INTEGER,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.full_name,
        p.health_goal,
        p.open_wearables_user_id,
        p.baseline_hrv,
        p.baseline_resting_hr,
        p.created_at,
        p.updated_at
    FROM profiles p
    WHERE p.id = p_user_id
    LIMIT 1;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

COMMENT ON FUNCTION get_user_profile IS 
    'Récupère le profil utilisateur par UUID. Contourne RLS pour permettre l''accès depuis l''app React Native.';

-- ============================================
-- 2. FONCTION : Récupérer le dernier insight
-- ============================================

CREATE OR REPLACE FUNCTION get_latest_insight(p_user_id UUID)
RETURNS TABLE (
    id UUID,
    user_id UUID,
    instruction_text TEXT,
    category TEXT,
    priority INTEGER,
    is_read BOOLEAN,
    user_feedback TEXT,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        i.id,
        i.user_id,
        i.instruction_text,
        i.category,
        i.priority,
        i.is_read,
        i.user_feedback,
        i.created_at
    FROM insights i
    WHERE i.user_id = p_user_id
    ORDER BY i.created_at DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

COMMENT ON FUNCTION get_latest_insight IS 
    'Récupère le dernier insight pour un utilisateur. Contourne RLS pour permettre l''accès depuis l''app React Native.';

-- ============================================
-- 3. FONCTION : Récupérer le dernier health_profile
-- ============================================

CREATE OR REPLACE FUNCTION get_latest_health_profile(p_user_id UUID)
RETURNS TABLE (
    id UUID,
    user_id UUID,
    profile_data JSONB,
    date DATE,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        hp.id,
        hp.user_id,
        hp.profile_data,
        hp.date,
        hp.created_at
    FROM health_profiles hp
    WHERE hp.user_id = p_user_id
    ORDER BY hp.date DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

COMMENT ON FUNCTION get_latest_health_profile IS 
    'Récupère le dernier health_profile pour un utilisateur. Contourne RLS pour permettre l''accès depuis l''app React Native.';

-- ============================================
-- 4. FONCTION : Récupérer les health_profiles des 7 derniers jours
-- ============================================

CREATE OR REPLACE FUNCTION get_health_profiles_trends(p_user_id UUID, p_days INTEGER DEFAULT 7)
RETURNS TABLE (
    id UUID,
    user_id UUID,
    profile_data JSONB,
    date DATE,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
DECLARE
    v_start_date DATE;
BEGIN
    v_start_date := CURRENT_DATE - (p_days - 1);
    
    RETURN QUERY
    SELECT 
        hp.id,
        hp.user_id,
        hp.profile_data,
        hp.date,
        hp.created_at
    FROM health_profiles hp
    WHERE hp.user_id = p_user_id
      AND hp.date >= v_start_date
    ORDER BY hp.date ASC;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

COMMENT ON FUNCTION get_health_profiles_trends IS 
    'Récupère les health_profiles des N derniers jours pour un utilisateur. Contourne RLS pour permettre l''accès depuis l''app React Native.';

-- ============================================
-- 5. GRANT PERMISSIONS
-- ============================================

-- Permettre à tous les utilisateurs authentifiés (anon key) d'exécuter ces fonctions
GRANT EXECUTE ON FUNCTION get_user_profile(UUID) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION get_latest_insight(UUID) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION get_latest_health_profile(UUID) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION get_health_profiles_trends(UUID, INTEGER) TO anon, authenticated;
