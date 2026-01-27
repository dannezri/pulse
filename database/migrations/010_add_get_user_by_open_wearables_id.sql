-- MIGRATION 010 : Ajouter la fonction RPC get_user_by_open_wearables_id
-- Cette fonction permet à l'app mobile de récupérer un profil utilisateur via son Open Wearables ID

CREATE OR REPLACE FUNCTION get_user_by_open_wearables_id(open_wearables_id TEXT)
RETURNS TABLE (
    id UUID,
    full_name TEXT,
    email TEXT,
    goal TEXT,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.user_id as id,
        p.full_name,
        p.email,
        p.goal,
        p.created_at
    FROM profiles p
    INNER JOIN external_identities ei 
        ON p.user_id = ei.supabase_user_id
    WHERE ei.provider_system = 'open-wearables'
        AND ei.external_user_id = open_wearables_id
        AND ei.is_active = TRUE
    LIMIT 1;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

COMMENT ON FUNCTION get_user_by_open_wearables_id IS 
    'Retourne le profil d''un utilisateur à partir de son Open Wearables ID';

-- Accorder les permissions d'exécution
GRANT EXECUTE ON FUNCTION get_user_by_open_wearables_id(TEXT) TO anon;
GRANT EXECUTE ON FUNCTION get_user_by_open_wearables_id(TEXT) TO authenticated;
