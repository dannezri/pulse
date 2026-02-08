-- ============================================
-- MIGRATION 013 : Ajouter target_sleep_minutes pour Readiness Score
-- ============================================

-- Ajouter target_sleep_minutes pour le calcul du Readiness Score
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS target_sleep_minutes INTEGER DEFAULT 480;

COMMENT ON COLUMN profiles.target_sleep_minutes IS 
    'Durée de sommeil cible en minutes (défaut: 480 = 8h) pour le calcul du Readiness Score';

-- Vérification
DO $$
BEGIN
    RAISE NOTICE '=== MIGRATION 013 TERMINÉE ===';
    RAISE NOTICE 'Colonne target_sleep_minutes ajoutée à profiles (défaut: 480 minutes = 8h)';
END $$;
