-- ============================================
-- MIGRATION 002 : Correction et vérification du schéma
-- ============================================
-- À exécuter dans Supabase SQL Editor
-- Cette migration vérifie et ajoute les champs manquants

-- ============================================
-- 1. TABLE PROFILES
-- ============================================

-- Ajouter open_wearables_user_id s'il n'existe pas
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND table_name = 'profiles' 
        AND column_name = 'open_wearables_user_id'
    ) THEN
        ALTER TABLE profiles ADD COLUMN open_wearables_user_id TEXT;
        RAISE NOTICE 'Colonne open_wearables_user_id ajoutée à profiles';
    END IF;
END $$;

-- Ajouter la contrainte UNIQUE si elle n'existe pas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'profiles_open_wearables_user_id_key'
    ) THEN
        ALTER TABLE profiles ADD CONSTRAINT profiles_open_wearables_user_id_key UNIQUE (open_wearables_user_id);
        RAISE NOTICE 'Contrainte UNIQUE ajoutée sur open_wearables_user_id';
    END IF;
END $$;

-- Ajouter baseline_hrv s'il n'existe pas
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND table_name = 'profiles' 
        AND column_name = 'baseline_hrv'
    ) THEN
        ALTER TABLE profiles ADD COLUMN baseline_hrv INTEGER;
        RAISE NOTICE 'Colonne baseline_hrv ajoutée à profiles';
    END IF;
END $$;

-- Ajouter baseline_resting_hr s'il n'existe pas
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND table_name = 'profiles' 
        AND column_name = 'baseline_resting_hr'
    ) THEN
        ALTER TABLE profiles ADD COLUMN baseline_resting_hr INTEGER;
        RAISE NOTICE 'Colonne baseline_resting_hr ajoutée à profiles';
    END IF;
END $$;

-- Ajouter health_goal s'il n'existe pas
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND table_name = 'profiles' 
        AND column_name = 'health_goal'
    ) THEN
        ALTER TABLE profiles ADD COLUMN health_goal TEXT DEFAULT 'energy';
        RAISE NOTICE 'Colonne health_goal ajoutée à profiles';
    END IF;
END $$;

-- ============================================
-- 2. TABLE BIOMETRICS
-- ============================================

-- Vérifier que raw_data est de type JSONB
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND table_name = 'biometrics' 
        AND column_name = 'raw_data' 
        AND data_type != 'jsonb'
    ) THEN
        ALTER TABLE biometrics ALTER COLUMN raw_data TYPE JSONB USING raw_data::jsonb;
        RAISE NOTICE 'Colonne raw_data convertie en JSONB';
    END IF;
END $$;

-- Ajouter source s'il n'existe pas
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND table_name = 'biometrics' 
        AND column_name = 'source'
    ) THEN
        ALTER TABLE biometrics ADD COLUMN source TEXT;
        RAISE NOTICE 'Colonne source ajoutée à biometrics';
    END IF;
END $$;

-- ============================================
-- 3. TABLE HEALTH_PROFILES
-- ============================================

-- Vérifier que profile_data est de type JSONB
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public'
        AND table_name = 'health_profiles' 
        AND column_name = 'profile_data' 
        AND data_type != 'jsonb'
    ) THEN
        ALTER TABLE health_profiles ALTER COLUMN profile_data TYPE JSONB USING profile_data::jsonb;
        RAISE NOTICE 'Colonne profile_data convertie en JSONB';
    END IF;
END $$;

-- Ajouter la contrainte UNIQUE si elle n'existe pas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'health_profiles_user_id_date_key'
    ) THEN
        ALTER TABLE health_profiles ADD CONSTRAINT health_profiles_user_id_date_key UNIQUE (user_id, date);
        RAISE NOTICE 'Contrainte UNIQUE ajoutée sur (user_id, date)';
    END IF;
END $$;

-- ============================================
-- 4. INDEXES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_biometrics_user_date ON biometrics(user_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_biometrics_user_type ON biometrics(user_id, metric_type, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_health_profiles_user_date ON health_profiles(user_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_profiles_open_wearables_user_id ON profiles(open_wearables_user_id);

-- ============================================
-- 5. ROW LEVEL SECURITY (RLS) - Policies pour Service Role
-- ============================================

-- Activer RLS si ce n'est pas déjà fait
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE biometrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_profiles ENABLE ROW LEVEL SECURITY;

-- Policy pour permettre au service role d'insérer dans biometrics
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public'
        AND tablename = 'biometrics' 
        AND policyname = 'Service role can insert biometrics'
    ) THEN
        CREATE POLICY "Service role can insert biometrics" ON biometrics
            FOR INSERT WITH CHECK (true);
        RAISE NOTICE 'Policy RLS ajoutée pour biometrics (service role)';
    END IF;
END $$;

-- Policy pour permettre au service role d'insérer dans health_profiles
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public'
        AND tablename = 'health_profiles' 
        AND policyname = 'Service role can insert health profiles'
    ) THEN
        CREATE POLICY "Service role can insert health profiles" ON health_profiles
            FOR INSERT WITH CHECK (true);
        RAISE NOTICE 'Policy RLS ajoutée pour health_profiles (service role)';
    END IF;
END $$;

-- Policy pour permettre au service role de mettre à jour les profiles
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public'
        AND tablename = 'profiles' 
        AND policyname = 'Service role can update profiles'
    ) THEN
        CREATE POLICY "Service role can update profiles" ON profiles
            FOR UPDATE USING (true);
        RAISE NOTICE 'Policy RLS ajoutée pour profiles (service role update)';
    END IF;
END $$;

-- ============================================
-- 6. VÉRIFICATION FINALE
-- ============================================

-- Afficher un résumé des colonnes de chaque table
DO $$
DECLARE
    col_record RECORD;
BEGIN
    RAISE NOTICE '=== RÉSUMÉ DES COLONNES ===';
    
    -- Profiles
    RAISE NOTICE 'Table: profiles';
    FOR col_record IN 
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'profiles'
        ORDER BY ordinal_position
    LOOP
        RAISE NOTICE '  - %: %', col_record.column_name, col_record.data_type;
    END LOOP;
    
    -- Biometrics
    RAISE NOTICE 'Table: biometrics';
    FOR col_record IN 
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'biometrics'
        ORDER BY ordinal_position
    LOOP
        RAISE NOTICE '  - %: %', col_record.column_name, col_record.data_type;
    END LOOP;
    
    -- Health Profiles
    RAISE NOTICE 'Table: health_profiles';
    FOR col_record IN 
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'health_profiles'
        ORDER BY ordinal_position
    LOOP
        RAISE NOTICE '  - %: %', col_record.column_name, col_record.data_type;
    END LOOP;
END $$;
