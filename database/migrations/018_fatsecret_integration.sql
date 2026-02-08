-- Migration pour l'intégration FatSecret
-- Permet de stocker les tokens OAuth et les entrées alimentaires

-- Table pour stocker les connexions FatSecret (OAuth tokens)
CREATE TABLE IF NOT EXISTS fatsecret_connections (
  user_id UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
  oauth_token TEXT NOT NULL,
  oauth_token_secret TEXT NOT NULL,
  connected_at TIMESTAMPTZ DEFAULT NOW(),
  last_synced_date DATE NULL,
  is_active BOOLEAN DEFAULT TRUE,
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Index pour optimiser les requêtes
CREATE INDEX idx_fatsecret_connections_active ON fatsecret_connections(user_id) WHERE is_active = TRUE;

-- Table pour stocker les entrées alimentaires brutes (raw)
CREATE TABLE IF NOT EXISTS food_entries_raw (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  fatsecret_food_entry_id BIGINT NOT NULL,
  entry_date DATE NOT NULL,
  meal TEXT NOT NULL, -- breakfast/lunch/dinner/other
  description TEXT NULL,
  food_id BIGINT NULL,
  serving_id BIGINT NULL,
  number_of_units NUMERIC NULL,
  raw JSONB NOT NULL,
  inserted_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, fatsecret_food_entry_id)
);

-- Index pour optimiser les requêtes par utilisateur et date
CREATE INDEX idx_food_entries_raw_user_date ON food_entries_raw(user_id, entry_date DESC);
CREATE INDEX idx_food_entries_raw_meal ON food_entries_raw(user_id, meal);

-- Fonction pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_food_entries_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger pour updated_at
CREATE TRIGGER trigger_food_entries_updated_at
  BEFORE UPDATE ON food_entries_raw
  FOR EACH ROW
  EXECUTE FUNCTION update_food_entries_updated_at();

-- RLS Policies pour fatsecret_connections
ALTER TABLE fatsecret_connections ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own FatSecret connection"
  ON fatsecret_connections
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own FatSecret connection"
  ON fatsecret_connections
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own FatSecret connection"
  ON fatsecret_connections
  FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own FatSecret connection"
  ON fatsecret_connections
  FOR DELETE
  USING (auth.uid() = user_id);

-- RLS Policies pour food_entries_raw
ALTER TABLE food_entries_raw ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own food entries"
  ON food_entries_raw
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Service role can insert food entries"
  ON food_entries_raw
  FOR INSERT
  WITH CHECK (TRUE); -- Seul le service role peut insérer

CREATE POLICY "Service role can update food entries"
  ON food_entries_raw
  FOR UPDATE
  USING (TRUE); -- Seul le service role peut mettre à jour

-- Commentaires pour la documentation
COMMENT ON TABLE fatsecret_connections IS 'Stocke les tokens OAuth FatSecret pour chaque utilisateur';
COMMENT ON TABLE food_entries_raw IS 'Stocke les entrées alimentaires brutes récupérées depuis FatSecret';
COMMENT ON COLUMN food_entries_raw.meal IS 'Type de repas: breakfast, lunch, dinner, other';
COMMENT ON COLUMN food_entries_raw.raw IS 'Données JSON brutes complètes de FatSecret';
