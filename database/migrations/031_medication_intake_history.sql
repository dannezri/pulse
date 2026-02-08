-- Migration: Historique des prises de médicaments
-- Permet de tracker jour par jour quels médicaments ont été pris

-- Table pour l'historique des prises
CREATE TABLE IF NOT EXISTS medication_intake_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  medication_id UUID NOT NULL REFERENCES user_medications(id) ON DELETE CASCADE,
  
  -- Date et heure de la prise
  taken_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  intake_date DATE NOT NULL DEFAULT CURRENT_DATE,
  intake_time TIME, -- Heure de prise (optionnel, pour comparer avec l'heure prévue)
  
  -- Informations sur la prise
  scheduled_time TIME, -- Heure prévue (ex: "08:00")
  was_on_time BOOLEAN DEFAULT true, -- Si pris à l'heure prévue
  pills_taken INTEGER DEFAULT 1, -- Nombre de comprimés pris
  
  -- Contexte et notes
  status VARCHAR(20) DEFAULT 'taken' CHECK (status IN ('taken', 'skipped', 'late', 'early')),
  notes TEXT, -- Notes optionnelles (ex: "pris avec repas", "oublié")
  
  -- Métadonnées
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- Index pour les requêtes fréquentes
  CONSTRAINT unique_intake_per_medication_time UNIQUE (user_id, medication_id, taken_at)
);

-- Index pour optimiser les requêtes
CREATE INDEX idx_medication_intake_history_user_id ON medication_intake_history(user_id);
CREATE INDEX idx_medication_intake_history_medication_id ON medication_intake_history(medication_id);
CREATE INDEX idx_medication_intake_history_intake_date ON medication_intake_history(intake_date DESC);
CREATE INDEX idx_medication_intake_history_user_date ON medication_intake_history(user_id, intake_date DESC);

-- Trigger pour mettre à jour updated_at
CREATE OR REPLACE FUNCTION update_medication_intake_history_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_medication_intake_history_updated_at
  BEFORE UPDATE ON medication_intake_history
  FOR EACH ROW
  EXECUTE FUNCTION update_medication_intake_history_updated_at();

-- Row Level Security (RLS)
ALTER TABLE medication_intake_history ENABLE ROW LEVEL SECURITY;

-- Policy: Les utilisateurs peuvent voir leur propre historique
CREATE POLICY "Users can view their own medication intake history"
  ON medication_intake_history
  FOR SELECT
  USING (auth.uid() = user_id);

-- Policy: Les utilisateurs peuvent insérer leur propre historique
CREATE POLICY "Users can insert their own medication intake history"
  ON medication_intake_history
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Policy: Les utilisateurs peuvent mettre à jour leur propre historique
CREATE POLICY "Users can update their own medication intake history"
  ON medication_intake_history
  FOR UPDATE
  USING (auth.uid() = user_id);

-- Policy: Les utilisateurs peuvent supprimer leur propre historique
CREATE POLICY "Users can delete their own medication intake history"
  ON medication_intake_history
  FOR DELETE
  USING (auth.uid() = user_id);

-- Policy: Service role peut tout faire
CREATE POLICY "Service role can manage all medication intake history"
  ON medication_intake_history
  FOR ALL
  USING (auth.role() = 'service_role');

-- Vue pour avoir un résumé par jour
CREATE OR REPLACE VIEW medication_intake_daily_summary AS
SELECT 
  user_id,
  intake_date,
  COUNT(*) as total_intakes,
  COUNT(*) FILTER (WHERE status = 'taken') as taken_count,
  COUNT(*) FILTER (WHERE status = 'skipped') as skipped_count,
  COUNT(*) FILTER (WHERE was_on_time = true) as on_time_count,
  ARRAY_AGG(DISTINCT medication_id) as medication_ids
FROM medication_intake_history
GROUP BY user_id, intake_date
ORDER BY intake_date DESC;

-- Commentaires pour documentation
COMMENT ON TABLE medication_intake_history IS 'Historique des prises de médicaments par les utilisateurs';
COMMENT ON COLUMN medication_intake_history.status IS 'Statut: taken (pris), skipped (oublié), late (en retard), early (en avance)';
COMMENT ON COLUMN medication_intake_history.was_on_time IS 'Indique si le médicament a été pris dans la fenêtre horaire prévue';
COMMENT ON VIEW medication_intake_daily_summary IS 'Résumé quotidien des prises de médicaments par utilisateur';
