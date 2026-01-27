-- ============================================
-- MIGRATION 005 : Table external_identities pour mapping d'identité
-- ============================================
-- Cette table formalise le mapping entre identifiants externes et utilisateurs Supabase
-- Permet de gérer plusieurs providers (Open Wearables, Apple Health, imports, etc.)

-- Table pour stocker les mappings d'identité
CREATE TABLE IF NOT EXISTS external_identities (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    supabase_user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    provider_system TEXT NOT NULL, -- 'open_wearables', 'apple_health', 'file_import', etc.
    external_user_id TEXT NOT NULL, -- ID utilisateur dans le système externe
    metadata JSONB, -- Métadonnées additionnelles (tokens, dates de connexion, etc.)
    is_active BOOLEAN DEFAULT TRUE, -- Permet de désactiver une connexion
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Contrainte unique : un utilisateur ne peut avoir qu'un seul ID par provider
    UNIQUE(supabase_user_id, provider_system, external_user_id)
);

-- Index pour les requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_external_identities_provider_user 
    ON external_identities(provider_system, external_user_id);
    
CREATE INDEX IF NOT EXISTS idx_external_identities_supabase_user 
    ON external_identities(supabase_user_id, provider_system);
    
CREATE INDEX IF NOT EXISTS idx_external_identities_active 
    ON external_identities(supabase_user_id, is_active) 
    WHERE is_active = TRUE;

-- RLS pour external_identities
ALTER TABLE external_identities ENABLE ROW LEVEL SECURITY;

-- Policy : Service role peut tout faire
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public'
        AND tablename = 'external_identities' 
        AND policyname = 'Service role can manage external identities'
    ) THEN
        CREATE POLICY "Service role can manage external identities" ON external_identities
            FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;

-- Policy : Utilisateurs peuvent voir leurs propres identités
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public'
        AND tablename = 'external_identities' 
        AND policyname = 'Users can view own external identities'
    ) THEN
        CREATE POLICY "Users can view own external identities" ON external_identities
            FOR SELECT USING (auth.uid() = supabase_user_id);
    END IF;
END $$;

-- Policy : Utilisateurs peuvent mettre à jour leurs propres identités
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public'
        AND tablename = 'external_identities' 
        AND policyname = 'Users can update own external identities'
    ) THEN
        CREATE POLICY "Users can update own external identities" ON external_identities
            FOR UPDATE USING (auth.uid() = supabase_user_id);
    END IF;
END $$;

-- Trigger pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_external_identities_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'update_external_identities_updated_at'
    ) THEN
        CREATE TRIGGER update_external_identities_updated_at 
            BEFORE UPDATE ON external_identities
            FOR EACH ROW 
            EXECUTE FUNCTION update_external_identities_updated_at();
    END IF;
END $$;

-- Commentaires
COMMENT ON TABLE external_identities IS 
    'Mappings entre identifiants externes (providers) et utilisateurs Supabase. Permet de gérer plusieurs sources de données par utilisateur.';

COMMENT ON COLUMN external_identities.provider_system IS 
    'Système externe : open_wearables, apple_health, file_import, garmin_direct, etc.';

COMMENT ON COLUMN external_identities.external_user_id IS 
    'ID utilisateur dans le système externe (provider_system)';

COMMENT ON COLUMN external_identities.metadata IS 
    'Métadonnées additionnelles : tokens OAuth, dates de connexion, permissions, etc.';

-- ============================================
-- MIGRATION DES DONNÉES EXISTANTES
-- ============================================

-- Migrer les open_wearables_user_id existants depuis profiles vers external_identities
DO $$
DECLARE
    profile_record RECORD;
BEGIN
    FOR profile_record IN 
        SELECT id, open_wearables_user_id 
        FROM profiles 
        WHERE open_wearables_user_id IS NOT NULL
    LOOP
        -- Insérer dans external_identities si n'existe pas déjà
        INSERT INTO external_identities (
            supabase_user_id,
            provider_system,
            external_user_id,
            is_active
        )
        VALUES (
            profile_record.id,
            'open_wearables',
            profile_record.open_wearables_user_id,
            TRUE
        )
        ON CONFLICT (supabase_user_id, provider_system, external_user_id) 
        DO NOTHING;
        
        RAISE NOTICE 'Migré: user % -> open_wearables:%', 
            profile_record.id, 
            profile_record.open_wearables_user_id;
    END LOOP;
    
    RAISE NOTICE 'Migration des identités externes terminée';
END $$;

-- ============================================
-- FONCTIONS UTILITAIRES
-- ============================================

-- Fonction pour obtenir le supabase_user_id depuis un external_user_id
CREATE OR REPLACE FUNCTION get_supabase_user_by_external_id(
    p_provider_system TEXT,
    p_external_user_id TEXT
)
RETURNS UUID AS $$
DECLARE
    v_user_id UUID;
BEGIN
    SELECT supabase_user_id INTO v_user_id
    FROM external_identities
    WHERE provider_system = p_provider_system
      AND external_user_id = p_external_user_id
      AND is_active = TRUE
    LIMIT 1;
    
    RETURN v_user_id;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_supabase_user_by_external_id IS 
    'Retourne le supabase_user_id correspondant à un external_user_id pour un provider donné';

-- Fonction pour obtenir tous les external_user_id d'un utilisateur
CREATE OR REPLACE FUNCTION get_external_identities(p_supabase_user_id UUID)
RETURNS TABLE (
    provider_system TEXT,
    external_user_id TEXT,
    is_active BOOLEAN,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ei.provider_system,
        ei.external_user_id,
        ei.is_active,
        ei.metadata
    FROM external_identities ei
    WHERE ei.supabase_user_id = p_supabase_user_id
    ORDER BY ei.provider_system, ei.created_at;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_external_identities IS 
    'Retourne toutes les identités externes d''un utilisateur Supabase';
