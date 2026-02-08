-- ============================================
-- MIGRATION 032 : Table medications
-- Suivi des médicaments des utilisateurs
-- ============================================

-- Créer la table medications
CREATE TABLE IF NOT EXISTS medications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    dosage TEXT,
    unit TEXT,
    pills_per_intake FLOAT, -- Nombre de comprimés par prise (peut être 0.5, 1, 1.5, 2...)
    frequency TEXT, -- Texte descriptif (ex: "3x par jour à 08:00, 13:00, 20:00")
    intake_times TEXT[], -- Array des heures de prise (format "HH:mm")
    daily_frequency INTEGER, -- Nombre de prises par jour (1-6)
    notes TEXT,
    taken_at TIMESTAMP WITH TIME ZONE NOT NULL, -- Date/heure de première prise
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour les requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_medications_user_id ON medications(user_id);
CREATE INDEX IF NOT EXISTS idx_medications_user_taken_at ON medications(user_id, taken_at DESC);
CREATE INDEX IF NOT EXISTS idx_medications_user_created_at ON medications(user_id, created_at DESC);

-- Row Level Security (RLS)
ALTER TABLE medications ENABLE ROW LEVEL SECURITY;

-- Policy : Les utilisateurs peuvent voir leurs propres médicaments
CREATE POLICY "Users can view own medications" ON medications
    FOR SELECT USING (auth.uid() = user_id);

-- Policy : Les utilisateurs peuvent insérer leurs propres médicaments
CREATE POLICY "Users can insert own medications" ON medications
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policy : Les utilisateurs peuvent mettre à jour leurs propres médicaments
CREATE POLICY "Users can update own medications" ON medications
    FOR UPDATE USING (auth.uid() = user_id);

-- Policy : Les utilisateurs peuvent supprimer leurs propres médicaments
CREATE POLICY "Users can delete own medications" ON medications
    FOR DELETE USING (auth.uid() = user_id);

-- Trigger pour updated_at automatique
CREATE OR REPLACE FUNCTION update_medications_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER medications_updated_at
    BEFORE UPDATE ON medications
    FOR EACH ROW
    EXECUTE FUNCTION update_medications_updated_at();

-- Commentaires sur la table
COMMENT ON TABLE medications IS 'Suivi des médicaments pris par les utilisateurs';
COMMENT ON COLUMN medications.pills_per_intake IS 'Nombre de comprimés par prise (supporte les décimaux: 0.5, 1.5, etc.)';
COMMENT ON COLUMN medications.intake_times IS 'Array des heures de prise quotidiennes au format HH:mm';
COMMENT ON COLUMN medications.daily_frequency IS 'Nombre de prises par jour (1-6)';
COMMENT ON COLUMN medications.taken_at IS 'Date et heure de la première prise du médicament';
