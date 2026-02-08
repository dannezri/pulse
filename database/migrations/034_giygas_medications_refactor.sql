-- ============================================
-- MIGRATION 034 : Refactoring API Giygas
-- Abandon BDPM/open-medicaments → API Giygas exclusive
-- Ajout table drug_presentations (CIP13/CIP7)
-- Support scan GS1 DataMatrix (GTIN → CIP13)
-- ============================================

-- ============================================
-- 1. TABLE PRÉSENTATIONS MÉDICAMENTS
-- ============================================

-- Nouvelle table pour stocker les présentations (CIP13/CIP7, prix, remboursement)
CREATE TABLE IF NOT EXISTS drug_presentations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    item_id UUID REFERENCES medications_catalog(id) ON DELETE CASCADE NOT NULL,
    cip13 TEXT NOT NULL UNIQUE, -- Code CIP 13 chiffres (identifiant unique présentation)
    cip7 TEXT, -- Code CIP 7 chiffres (ancien format)
    label TEXT, -- Libellé de la présentation (ex: "plaquette(s) thermoformée(s) PVC aluminium de 16 comprimé(s)")
    price NUMERIC(10, 2), -- Prix public TTC en euros
    reimbursement_rate INTEGER, -- Taux de remboursement (0-100%)
    status TEXT, -- Statut AMM (ex: "Déclaration de commercialisation")
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour recherche rapide par CIP13 (scan de boîtes)
CREATE INDEX IF NOT EXISTS idx_drug_presentations_cip13 ON drug_presentations(cip13);
CREATE INDEX IF NOT EXISTS idx_drug_presentations_cip7 ON drug_presentations(cip7) WHERE cip7 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_drug_presentations_item_id ON drug_presentations(item_id);

COMMENT ON TABLE drug_presentations IS 'Présentations commerciales des médicaments (CIP13/CIP7, prix, remboursement)';
COMMENT ON COLUMN drug_presentations.cip13 IS 'Code CIP 13 chiffres - identifiant unique de la présentation (pour scan GS1)';
COMMENT ON COLUMN drug_presentations.cip7 IS 'Code CIP 7 chiffres - ancien format';
COMMENT ON COLUMN drug_presentations.price IS 'Prix public TTC en euros';
COMMENT ON COLUMN drug_presentations.reimbursement_rate IS 'Taux de remboursement Sécurité Sociale (0-100%)';

-- ============================================
-- 2. EXTENSION TABLE medication_details
-- ============================================

-- Ajouter colonnes pour composition et conditions (depuis Giygas)
ALTER TABLE medication_details 
ADD COLUMN IF NOT EXISTS composition JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS conditions JSONB DEFAULT '{}'::jsonb;

COMMENT ON COLUMN medication_details.composition IS 'Composition détaillée du médicament (substances actives + dosages)';
COMMENT ON COLUMN medication_details.conditions IS 'Conditions de prescription et délivrance';

-- ============================================
-- 3. MISE À JOUR SOURCE medications_catalog
-- ============================================

-- Mettre à jour les médicaments existants pour utiliser la source 'giygas'
-- (si migration progressive depuis BDPM)
-- NOTE: Ne pas exécuter si vous voulez conserver les anciennes données BDPM
-- UPDATE medications_catalog SET source = 'giygas' WHERE source = 'bdpm';

-- ============================================
-- 4. ROW LEVEL SECURITY
-- ============================================

-- Activer RLS sur drug_presentations
ALTER TABLE drug_presentations ENABLE ROW LEVEL SECURITY;

-- Lecture publique pour drug_presentations (données de référence)
DROP POLICY IF EXISTS "Anyone can view drug presentations" ON drug_presentations;
CREATE POLICY "Anyone can view drug presentations" ON drug_presentations
    FOR SELECT USING (true);

-- Service role peut tout gérer
DROP POLICY IF EXISTS "Service role can manage drug presentations" ON drug_presentations;
CREATE POLICY "Service role can manage drug presentations" ON drug_presentations
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================
-- 5. TRIGGERS
-- ============================================

-- Trigger pour updated_at sur drug_presentations
CREATE OR REPLACE FUNCTION update_drug_presentations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS drug_presentations_updated_at ON drug_presentations;
CREATE TRIGGER drug_presentations_updated_at
    BEFORE UPDATE ON drug_presentations
    FOR EACH ROW
    EXECUTE FUNCTION update_drug_presentations_updated_at();

-- ============================================
-- 6. FONCTION UTILITAIRE : GTIN → CIP13
-- ============================================

-- Fonction pour convertir GTIN (GS1 DataMatrix) en CIP13
CREATE OR REPLACE FUNCTION gtin_to_cip13(gtin TEXT)
RETURNS TEXT AS $$
DECLARE
    gtin_clean TEXT;
    gtin_length INTEGER;
BEGIN
    -- Nettoyer le GTIN (enlever espaces et caractères non numériques)
    gtin_clean := regexp_replace(gtin, '[^0-9]', '', 'g');
    gtin_length := length(gtin_clean);
    
    -- GTIN-14 → CIP13 : enlever le premier chiffre (indicateur packaging)
    IF gtin_length = 14 THEN
        RETURN substring(gtin_clean from 2 for 13);
    
    -- GTIN-13 → CIP13 : déjà au bon format
    ELSIF gtin_length = 13 THEN
        RETURN gtin_clean;
    
    -- Format invalide
    ELSE
        RETURN NULL;
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION gtin_to_cip13(TEXT) IS 'Convertit un code GTIN (GS1 DataMatrix) en CIP13';

-- ============================================
-- 7. VUE UTILITAIRE : MÉDICAMENTS COMPLETS
-- ============================================

-- Vue pour récupérer facilement un médicament avec toutes ses données
CREATE OR REPLACE VIEW medications_full AS
SELECT 
    mc.id,
    mc.external_id as cis,
    mc.source,
    mc.name,
    mc.form,
    mc.laboratory,
    mc.active_substance,
    mc.atc_code,
    md.composition,
    md.generics,
    md.conditions,
    md.notice_url,
    md.last_refreshed_at,
    mc.created_at,
    mc.updated_at
FROM medications_catalog mc
LEFT JOIN medication_details md ON mc.id = md.medication_id;

COMMENT ON VIEW medications_full IS 'Vue complète des médicaments avec détails (composition, génériques, conditions)';

-- ============================================
-- MIGRATION TERMINÉE
-- ============================================

-- Notes de migration :
-- 1. Les données existantes BDPM restent intactes (source='bdpm')
-- 2. Les nouvelles données utiliseront source='giygas'
-- 3. La table drug_presentations est nouvelle (CIP13/CIP7)
-- 4. Les présentations seront peuplées au fur et à mesure des recherches
-- 5. Le scan GS1 DataMatrix utilise gtin_to_cip13() puis drug_presentations.cip13

-- Pour vérifier la migration :
-- SELECT * FROM information_schema.tables WHERE table_name = 'drug_presentations';
-- SELECT * FROM medications_full LIMIT 5;
-- SELECT gtin_to_cip13('34009300015517'); -- Test conversion
