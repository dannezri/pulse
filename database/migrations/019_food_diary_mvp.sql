-- Migration 019: Food Diary MVP
-- Journal alimentaire complet avec support photo + FatSecret sync
-- Architecture extensible et ultra personnalisable

-- =====================================================
-- 1. PROFILS FATSECRET (renommé pour clarté)
-- =====================================================

-- Renommer la table existante pour clarté sémantique
ALTER TABLE fatsecret_connections RENAME TO fatsecret_profiles;

-- Ajouter colonne last_sync_at (tracking plus fin)
ALTER TABLE fatsecret_profiles 
ADD COLUMN IF NOT EXISTS last_sync_at TIMESTAMPTZ NULL;

-- Index pour recherche de profils actifs
CREATE INDEX IF NOT EXISTS idx_fatsecret_profiles_active 
ON fatsecret_profiles(user_id) WHERE is_active = TRUE;

-- =====================================================
-- 2. FOOD_LOGS (repas/événements)
-- =====================================================

CREATE TABLE IF NOT EXISTS food_logs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  
  -- Timing
  logged_at TIMESTAMPTZ NOT NULL,  -- Heure réelle du repas
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- Catégorisation
  meal_type TEXT NOT NULL CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')),
  source TEXT NOT NULL DEFAULT 'manual' CHECK (source IN ('manual', 'search', 'photo', 'import')),
  
  -- Métadonnées utilisateur (ultra personnalisable)
  note TEXT NULL,
  context JSONB DEFAULT '{}'::jsonb,  -- {hunger: 7, mood: "ok", location: "home"}
  
  -- Sync FatSecret
  fs_sync_status TEXT DEFAULT 'pending' CHECK (fs_sync_status IN ('pending', 'synced', 'error', 'skipped')),
  fs_food_entry_ids JSONB DEFAULT '[]'::jsonb,  -- Liste des IDs FatSecret créés (plusieurs items = plusieurs entries)
  fs_synced_at TIMESTAMPTZ NULL,
  fs_error TEXT NULL
);

-- Indexes optimisés pour les requêtes courantes
CREATE INDEX idx_food_logs_user_logged ON food_logs(user_id, logged_at DESC);
CREATE INDEX idx_food_logs_user_meal ON food_logs(user_id, meal_type);
CREATE INDEX idx_food_logs_sync_pending ON food_logs(user_id, fs_sync_status) 
  WHERE fs_sync_status IN ('pending', 'error');

-- Trigger pour updated_at
CREATE OR REPLACE FUNCTION update_food_logs_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_food_logs_updated_at
  BEFORE UPDATE ON food_logs
  FOR EACH ROW
  EXECUTE FUNCTION update_food_logs_timestamp();

-- =====================================================
-- 3. FOOD_LOG_ITEMS (items dans un repas)
-- =====================================================

CREATE TABLE IF NOT EXISTS food_log_items (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  food_log_id UUID NOT NULL REFERENCES food_logs(id) ON DELETE CASCADE,
  
  -- Description
  name TEXT NOT NULL,  -- Nom de l'aliment
  quantity NUMERIC NOT NULL DEFAULT 1.0,
  unit TEXT NOT NULL DEFAULT 'serving',  -- serving, g, ml, cup, oz...
  
  -- Références FatSecret (optionnelles)
  fs_food_id BIGINT NULL,
  fs_serving_id BIGINT NULL,
  
  -- Nutrition (calculée ou importée)
  nutrition JSONB DEFAULT '{}'::jsonb,  -- {calories: 200, protein: 10, carbs: 30, fat: 5}
  
  -- Données brutes FatSecret (pour audit/debug)
  raw JSONB DEFAULT '{}'::jsonb,
  
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index pour les jointures et recherches
CREATE INDEX idx_food_log_items_log ON food_log_items(food_log_id);
CREATE INDEX idx_food_log_items_fs_food ON food_log_items(fs_food_id) WHERE fs_food_id IS NOT NULL;

-- =====================================================
-- 4. FOOD_PHOTOS (photos de repas)
-- =====================================================

CREATE TABLE IF NOT EXISTS food_photos (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  food_log_id UUID NOT NULL REFERENCES food_logs(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  
  -- Storage Supabase
  storage_path TEXT NOT NULL,  -- Chemin dans Supabase Storage
  storage_bucket TEXT DEFAULT 'food-photos',
  
  -- Métadonnées
  taken_at TIMESTAMPTZ DEFAULT NOW(),
  file_size_bytes BIGINT NULL,
  mime_type TEXT NULL,
  
  -- Analyse IA (optionnelle)
  analysis JSONB DEFAULT '{}'::jsonb,  -- {items: [...], confidence: 0.85, provider: "fatsecret"}
  analysis_status TEXT DEFAULT 'pending' CHECK (analysis_status IN ('pending', 'success', 'failed', 'skipped')),
  confidence NUMERIC NULL CHECK (confidence >= 0 AND confidence <= 1),
  
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index pour recherche de photos
CREATE INDEX idx_food_photos_log ON food_photos(food_log_id);
CREATE INDEX idx_food_photos_user ON food_photos(user_id, taken_at DESC);

-- =====================================================
-- 5. RLS POLICIES
-- =====================================================

-- food_logs
ALTER TABLE food_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own food logs"
  ON food_logs FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own food logs"
  ON food_logs FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own food logs"
  ON food_logs FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own food logs"
  ON food_logs FOR DELETE
  USING (auth.uid() = user_id);

-- food_log_items
ALTER TABLE food_log_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own food items"
  ON food_log_items FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM food_logs 
      WHERE food_logs.id = food_log_items.food_log_id 
      AND food_logs.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert their own food items"
  ON food_log_items FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM food_logs 
      WHERE food_logs.id = food_log_items.food_log_id 
      AND food_logs.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update their own food items"
  ON food_log_items FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM food_logs 
      WHERE food_logs.id = food_log_items.food_log_id 
      AND food_logs.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete their own food items"
  ON food_log_items FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM food_logs 
      WHERE food_logs.id = food_log_items.food_log_id 
      AND food_logs.user_id = auth.uid()
    )
  );

-- food_photos
ALTER TABLE food_photos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own food photos"
  ON food_photos FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own food photos"
  ON food_photos FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own food photos"
  ON food_photos FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own food photos"
  ON food_photos FOR DELETE
  USING (auth.uid() = user_id);

-- =====================================================
-- 6. VIEWS UTILES (pour optimisation requêtes)
-- =====================================================

-- Vue pour les repas complets (avec items + photos)
CREATE OR REPLACE VIEW food_logs_complete AS
SELECT 
  fl.id,
  fl.user_id,
  fl.logged_at,
  fl.meal_type,
  fl.source,
  fl.note,
  fl.context,
  fl.fs_sync_status,
  
  -- Agrégation items
  COALESCE(
    json_agg(
      json_build_object(
        'id', fli.id,
        'name', fli.name,
        'quantity', fli.quantity,
        'unit', fli.unit,
        'nutrition', fli.nutrition
      ) ORDER BY fli.created_at
    ) FILTER (WHERE fli.id IS NOT NULL),
    '[]'::json
  ) as items,
  
  -- Agrégation photos
  COALESCE(
    json_agg(
      json_build_object(
        'id', fp.id,
        'storage_path', fp.storage_path,
        'taken_at', fp.taken_at
      ) ORDER BY fp.taken_at
    ) FILTER (WHERE fp.id IS NOT NULL),
    '[]'::json
  ) as photos,
  
  fl.created_at,
  fl.updated_at
FROM food_logs fl
LEFT JOIN food_log_items fli ON fl.id = fli.food_log_id
LEFT JOIN food_photos fp ON fl.id = fp.food_log_id
GROUP BY fl.id;

-- =====================================================
-- 7. COMMENTAIRES (documentation)
-- =====================================================

COMMENT ON TABLE food_logs IS 'Journal alimentaire principal - un log = un repas/événement';
COMMENT ON TABLE food_log_items IS 'Items alimentaires dans un repas (plusieurs items possibles)';
COMMENT ON TABLE food_photos IS 'Photos de repas avec analyse IA optionnelle';

COMMENT ON COLUMN food_logs.logged_at IS 'Heure réelle du repas (pas created_at)';
COMMENT ON COLUMN food_logs.context IS 'Contexte ultra personnalisable: {hunger:7, mood:"ok", location:"home"}';
COMMENT ON COLUMN food_logs.fs_sync_status IS 'Statut sync FatSecret: pending|synced|error|skipped';
COMMENT ON COLUMN food_logs.fs_food_entry_ids IS 'Liste des food_entry_id FatSecret (JSON array)';

COMMENT ON COLUMN food_log_items.nutrition IS 'Macros/micros: {calories:200, protein:10, carbs:30, fat:5, fiber:3}';
COMMENT ON COLUMN food_log_items.raw IS 'Payload FatSecret brut (pour audit)';

COMMENT ON COLUMN food_photos.analysis IS 'Résultat analyse IA: {items:[...], confidence:0.85, provider:"fatsecret"}';
COMMENT ON COLUMN food_photos.storage_path IS 'Chemin complet dans Supabase Storage';
