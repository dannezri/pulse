-- ============================================
-- MIGRATION 033 : Refonte complète schéma médicaments
-- Corrige l'incohérence entre le code mobile et la DB
-- Ajoute catalogue, détails, et améliore les traitements
-- ============================================

-- ============================================
-- 1. CATALOGUE MÉDICAMENTS (référentiel)
-- ============================================

CREATE TABLE IF NOT EXISTS medications_catalog (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    external_id TEXT NOT NULL, -- ID BDPM/ANSM (ex: CIS code)
    source TEXT NOT NULL, -- 'bdpm', 'ansm', 'manual'
    name TEXT NOT NULL,
    active_substance TEXT, -- DCI (ex: "Paracétamol")
    atc_code TEXT, -- Code ATC (ex: "N02BE01")
    laboratory TEXT,
    form TEXT, -- Forme pharmaceutique (comprimé, gélule, etc.)
    raw_data JSONB, -- Données complètes de l'API pour référence future
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source, external_id)
);

CREATE INDEX IF NOT EXISTS idx_medications_catalog_name ON medications_catalog(name);
CREATE INDEX IF NOT EXISTS idx_medications_catalog_atc ON medications_catalog(atc_code) WHERE atc_code IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_medications_catalog_substance ON medications_catalog(active_substance) WHERE active_substance IS NOT NULL;

COMMENT ON TABLE medications_catalog IS 'Catalogue de référence des médicaments (BDPM/ANSM) - Données publiques';
COMMENT ON COLUMN medications_catalog.external_id IS 'Identifiant externe du médicament (ex: code CIS BDPM)';
COMMENT ON COLUMN medications_catalog.atc_code IS 'Code ATC (Anatomical Therapeutic Chemical) WHO';
COMMENT ON COLUMN medications_catalog.active_substance IS 'Substance active / DCI (Dénomination Commune Internationale)';

-- ============================================
-- 2. DÉTAILS MÉDICAMENTS (notice, génériques, alternatives)
-- ============================================

CREATE TABLE IF NOT EXISTS medication_details (
    medication_id UUID PRIMARY KEY REFERENCES medications_catalog(id) ON DELETE CASCADE,
    notice_url TEXT, -- URL vers la notice officielle
    notice_text TEXT, -- Texte de la notice si disponible
    generics JSONB DEFAULT '[]'::jsonb, -- [{"id": "...", "name": "...", "laboratory": "..."}]
    alternatives JSONB DEFAULT '[]'::jsonb, -- [{"id": "...", "name": "...", "reason": "..."}]
    last_refreshed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE medication_details IS 'Détails enrichis des médicaments (notice, génériques, alternatives)';
COMMENT ON COLUMN medication_details.generics IS 'Liste des médicaments génériques au format JSON';
COMMENT ON COLUMN medication_details.alternatives IS 'Liste des alternatives thérapeutiques au format JSON';
COMMENT ON COLUMN medication_details.last_refreshed_at IS 'Date du dernier refresh des données depuis l''API';

-- ============================================
-- 3. TRAITEMENTS UTILISATEUR (renommage + extension)
-- ============================================

-- Renommer l'ancienne table medications en user_treatments
ALTER TABLE IF EXISTS medications RENAME TO user_treatments;

-- Ajouter les colonnes manquantes pour la gestion complète des traitements
ALTER TABLE user_treatments 
ADD COLUMN IF NOT EXISTS medication_catalog_id UUID REFERENCES medications_catalog(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS weekdays INTEGER[], -- Jours de semaine (1=lundi, 2=mardi, ..., 7=dimanche)
ADD COLUMN IF NOT EXISTS schedule_type TEXT DEFAULT 'recurring', -- 'once' (prise unique) ou 'recurring' (récurrent)
ADD COLUMN IF NOT EXISTS end_mode TEXT DEFAULT 'indefinite', -- 'indefinite', 'until_date', 'duration_days'
ADD COLUMN IF NOT EXISTS end_date DATE, -- Date de fin si end_mode='until_date'
ADD COLUMN IF NOT EXISTS duration_days INTEGER, -- Nombre de jours si end_mode='duration_days'
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE; -- Soft delete

-- Renommer la colonne taken_at en start_date pour plus de clarté
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_treatments' AND column_name = 'taken_at'
    ) THEN
        ALTER TABLE user_treatments RENAME COLUMN taken_at TO start_date;
    END IF;
END $$;

-- Convertir start_date de TIMESTAMP à DATE si nécessaire
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_treatments' 
        AND column_name = 'start_date' 
        AND data_type = 'timestamp with time zone'
    ) THEN
        ALTER TABLE user_treatments 
        ALTER COLUMN start_date TYPE DATE USING start_date::DATE;
    END IF;
END $$;

-- Index pour les requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_user_treatments_medication ON user_treatments(medication_catalog_id) WHERE medication_catalog_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_user_treatments_active ON user_treatments(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_user_treatments_dates ON user_treatments(user_id, start_date DESC) WHERE is_active = TRUE;

COMMENT ON TABLE user_treatments IS 'Traitements et prises de médicaments des utilisateurs';
COMMENT ON COLUMN user_treatments.medication_catalog_id IS 'Lien vers le catalogue (optionnel, peut être null pour médicaments non référencés)';
COMMENT ON COLUMN user_treatments.weekdays IS 'Jours de semaine pour récurrence (1=lundi, 7=dimanche) - NULL si schedule_type=once';
COMMENT ON COLUMN user_treatments.schedule_type IS 'Type de prise: once (prise unique) ou recurring (récurrent)';
COMMENT ON COLUMN user_treatments.end_mode IS 'Mode de fin du traitement: indefinite, until_date, duration_days';
COMMENT ON COLUMN user_treatments.end_date IS 'Date de fin du traitement si end_mode=until_date';
COMMENT ON COLUMN user_treatments.duration_days IS 'Durée en jours si end_mode=duration_days';
COMMENT ON COLUMN user_treatments.is_active IS 'Traitement actif (false = soft delete)';

-- ============================================
-- 4. ROW LEVEL SECURITY (RLS)
-- ============================================

-- Activer RLS sur les nouvelles tables
ALTER TABLE medications_catalog ENABLE ROW LEVEL SECURITY;
ALTER TABLE medication_details ENABLE ROW LEVEL SECURITY;

-- Catalog et details : lecture publique (données de référence)
DROP POLICY IF EXISTS "Anyone can view medications catalog" ON medications_catalog;
CREATE POLICY "Anyone can view medications catalog" ON medications_catalog
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Service role can manage medications catalog" ON medications_catalog;
CREATE POLICY "Service role can manage medications catalog" ON medications_catalog
    FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Anyone can view medication details" ON medication_details;
CREATE POLICY "Anyone can view medication details" ON medication_details
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Service role can manage medication details" ON medication_details;
CREATE POLICY "Service role can manage medication details" ON medication_details
    FOR ALL USING (auth.role() = 'service_role');

-- user_treatments : les policies existantes sont conservées automatiquement
-- Vérifier qu'elles existent, sinon les créer
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'user_treatments' AND policyname = 'Users can view own medications'
    ) THEN
        CREATE POLICY "Users can view own medications" ON user_treatments
            FOR SELECT USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'user_treatments' AND policyname = 'Users can insert own medications'
    ) THEN
        CREATE POLICY "Users can insert own medications" ON user_treatments
            FOR INSERT WITH CHECK (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'user_treatments' AND policyname = 'Users can update own medications'
    ) THEN
        CREATE POLICY "Users can update own medications" ON user_treatments
            FOR UPDATE USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'user_treatments' AND policyname = 'Users can delete own medications'
    ) THEN
        CREATE POLICY "Users can delete own medications" ON user_treatments
            FOR DELETE USING (auth.uid() = user_id);
    END IF;
END $$;

-- ============================================
-- 5. TRIGGERS
-- ============================================

-- Trigger pour updated_at sur medications_catalog
CREATE OR REPLACE FUNCTION update_medications_catalog_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS medications_catalog_updated_at ON medications_catalog;
CREATE TRIGGER medications_catalog_updated_at
    BEFORE UPDATE ON medications_catalog
    FOR EACH ROW
    EXECUTE FUNCTION update_medications_catalog_updated_at();

-- Le trigger pour user_treatments existe déjà (update_medications_updated_at)
-- mais on s'assure qu'il fonctionne avec le nouveau nom de table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'medications_updated_at' AND tgrelid = 'user_treatments'::regclass
    ) AND EXISTS (
        SELECT 1 FROM pg_proc WHERE proname = 'update_medications_updated_at'
    ) THEN
        CREATE TRIGGER medications_updated_at
            BEFORE UPDATE ON user_treatments
            FOR EACH ROW
            EXECUTE FUNCTION update_medications_updated_at();
    END IF;
END $$;

-- ============================================
-- 6. DONNÉES DE TEST (optionnel)
-- ============================================

-- Insérer quelques médicaments courants pour le développement
INSERT INTO medications_catalog (external_id, source, name, active_substance, atc_code, laboratory, form)
VALUES 
    ('CIS-60001551', 'bdpm', 'DOLIPRANE 500 mg, comprimé', 'Paracétamol', 'N02BE01', 'OPELLA HEALTHCARE FRANCE SAS', 'Comprimé'),
    ('CIS-61133534', 'bdpm', 'DOLIPRANE 1000 mg, comprimé', 'Paracétamol', 'N02BE01', 'OPELLA HEALTHCARE FRANCE SAS', 'Comprimé'),
    ('CIS-67132169', 'bdpm', 'LEVOTHYROX 50 microgrammes, comprimé sécable', 'Lévothyroxine sodique', 'H03AA01', 'MERCK SANTE', 'Comprimé'),
    ('CIS-67132434', 'bdpm', 'LEVOTHYROX 100 microgrammes, comprimé sécable', 'Lévothyroxine sodique', 'H03AA01', 'MERCK SANTE', 'Comprimé')
ON CONFLICT (source, external_id) DO NOTHING;

-- ============================================
-- MIGRATION TERMINÉE
-- ============================================

-- Note: Pour vérifier la migration, exécuter:
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('medications_catalog', 'medication_details', 'user_treatments');
