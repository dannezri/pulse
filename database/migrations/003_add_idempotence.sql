-- ============================================
-- MIGRATION 003 : Idempotence & Dédoublonnage des Webhooks
-- ============================================
-- À exécuter dans Supabase SQL Editor
-- Cette migration ajoute le support de l'idempotence pour éviter les doublons

-- ============================================
-- 1. AJOUT DU CHAMP source_event_id
-- ============================================

-- Ajouter source_event_id à la table biometrics
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND table_name = 'biometrics' 
        AND column_name = 'source_event_id'
    ) THEN
        ALTER TABLE biometrics ADD COLUMN source_event_id TEXT;
        RAISE NOTICE 'Colonne source_event_id ajoutée à biometrics';
    END IF;
END $$;

-- ============================================
-- 2. INDEX POUR PERFORMANCE
-- ============================================

-- Index pour accélérer les recherches par source_event_id
CREATE INDEX IF NOT EXISTS idx_biometrics_source_event_id 
    ON biometrics(source_event_id) 
    WHERE source_event_id IS NOT NULL;

-- Index composite pour la contrainte unique
CREATE INDEX IF NOT EXISTS idx_biometrics_user_source_event 
    ON biometrics(user_id, source, source_event_id) 
    WHERE source_event_id IS NOT NULL;

-- ============================================
-- 3. CONTRAINTE UNIQUE POUR IDEMPOTENCE
-- ============================================

-- Ajouter la contrainte unique (user_id, source, source_event_id)
-- Cette contrainte empêche les doublons basés sur l'ID d'événement source
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'biometrics_user_source_event_unique'
    ) THEN
        -- Créer une contrainte unique partielle (seulement si source_event_id n'est pas NULL)
        -- On utilise un index unique partiel car source_event_id peut être NULL pour les anciennes données
        CREATE UNIQUE INDEX biometrics_user_source_event_unique 
            ON biometrics(user_id, source, source_event_id) 
            WHERE source_event_id IS NOT NULL;
        RAISE NOTICE 'Contrainte unique ajoutée sur (user_id, source, source_event_id)';
    END IF;
END $$;

-- ============================================
-- 4. COMMENTAIRES POUR DOCUMENTATION
-- ============================================

COMMENT ON COLUMN biometrics.source_event_id IS 
    'ID unique de l''événement depuis la source (webhook/provider). Utilisé pour l''idempotence et le dédoublonnage. Peut être un UUID, un hash du payload, ou un identifiant fourni par le provider.';

-- ============================================
-- 5. FONCTION UTILITAIRE : Générer un hash du payload
-- ============================================

-- Fonction pour générer un hash MD5 d'un JSON (fallback si pas de source_event_id)
-- Cette fonction peut être utilisée côté application pour générer un source_event_id
-- à partir du payload si le provider n'en fournit pas
CREATE OR REPLACE FUNCTION generate_payload_hash(payload JSONB)
RETURNS TEXT AS $$
BEGIN
    RETURN encode(digest(payload::text, 'md5'), 'hex');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION generate_payload_hash IS 
    'Génère un hash MD5 du payload JSON. Utilisé comme fallback pour source_event_id si le provider n''en fournit pas.';

-- ============================================
-- 6. VÉRIFICATION
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '=== MIGRATION 003 TERMINÉE ===';
    RAISE NOTICE 'Colonne source_event_id ajoutée';
    RAISE NOTICE 'Contrainte unique créée sur (user_id, source, source_event_id)';
    RAISE NOTICE 'Index de performance créés';
    RAISE NOTICE '';
    RAISE NOTICE 'Note: Les anciennes données auront source_event_id = NULL';
    RAISE NOTICE 'Les nouvelles insertions devraient inclure source_event_id pour l''idempotence';
END $$;
