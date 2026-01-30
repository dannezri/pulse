-- ============================================
-- MIGRATION 021 : Food Diary Extensible
-- ============================================
-- Cette migration crée une architecture extensible pour le journal alimentaire:
-- - food_logs: Un repas / un événement
-- - food_log_items: Items individuels d'un repas
-- - food_photos: Photos de repas
-- - Triggers automatiques pour calcul des totaux

-- ============================================
-- 1. TABLE food_logs (Repas/Événements)
-- ============================================

CREATE TABLE IF NOT EXISTS food_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    
    -- Type et timing
    meal_type TEXT NOT NULL CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack', 'other')),
    logged_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Notes utilisateur
    notes TEXT,
    
    -- ========================================
    -- TOTAUX AGRÉGÉS (mis à jour par triggers)
    -- ========================================
    total_calories FLOAT DEFAULT 0,
    total_protein FLOAT DEFAULT 0,
    total_carbs FLOAT DEFAULT 0,
    total_fat FLOAT DEFAULT 0,
    total_fiber FLOAT DEFAULT 0,
    total_sugar FLOAT DEFAULT 0,
    total_sodium FLOAT DEFAULT 0,
    
    -- Métadonnées
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index
CREATE INDEX idx_food_logs_user_date 
    ON food_logs(user_id, logged_at DESC);

CREATE INDEX idx_food_logs_user_meal 
    ON food_logs(user_id, meal_type, logged_at DESC);

CREATE INDEX idx_food_logs_date 
    ON food_logs(logged_at::DATE);

-- Commentaires
COMMENT ON TABLE food_logs IS 
    'Repas ou événements alimentaires (un log = un repas)';

COMMENT ON COLUMN food_logs.meal_type IS 
    'Type de repas: breakfast, lunch, dinner, snack, other';

COMMENT ON COLUMN food_logs.total_calories IS 
    'Somme des calories de tous les items (mis à jour par trigger)';

-- RLS
ALTER TABLE food_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own food logs" ON food_logs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own food logs" ON food_logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own food logs" ON food_logs
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own food logs" ON food_logs
    FOR DELETE USING (auth.uid() = user_id);

-- ============================================
-- 2. TABLE food_log_items (Items individuels)
-- ============================================

CREATE TABLE IF NOT EXISTS food_log_items (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    food_log_id UUID REFERENCES food_logs(id) ON DELETE CASCADE NOT NULL,
    
    -- Source
    source TEXT NOT NULL CHECK (source IN ('fatsecret', 'manual', 'photo_analysis')),
    fatsecret_id TEXT,  -- ID FatSecret (si applicable)
    
    -- Description
    food_name TEXT NOT NULL,
    brand_name TEXT,    -- Marque (optionnel)
    serving_size FLOAT NOT NULL,
    serving_unit TEXT NOT NULL,  -- 'g', 'ml', 'pièce', 'tasse', etc.
    
    -- Nutrition (par portion indiquée)
    calories FLOAT NOT NULL,
    protein FLOAT NOT NULL DEFAULT 0,
    carbs FLOAT NOT NULL DEFAULT 0,
    fat FLOAT NOT NULL DEFAULT 0,
    fiber FLOAT DEFAULT 0,
    sugar FLOAT DEFAULT 0,
    sodium FLOAT DEFAULT 0,
    
    -- Micronutriments (optionnel, pour future)
    vitamins JSONB,
    minerals JSONB,
    
    -- Ordre d'affichage
    display_order INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index
CREATE INDEX idx_food_log_items_log 
    ON food_log_items(food_log_id, display_order);

CREATE INDEX idx_food_log_items_fatsecret 
    ON food_log_items(fatsecret_id) WHERE fatsecret_id IS NOT NULL;

-- Commentaires
COMMENT ON TABLE food_log_items IS 
    'Items individuels d''un repas (aliments, boissons)';

COMMENT ON COLUMN food_log_items.source IS 
    'Source de données: fatsecret (API), manual (saisi), photo_analysis (IA vision)';

COMMENT ON COLUMN food_log_items.serving_size IS 
    'Taille de la portion (nombre d''unités)';

COMMENT ON COLUMN food_log_items.serving_unit IS 
    'Unité de mesure: g, ml, pièce, tasse, cuillère, etc.';

-- RLS (hérité via food_logs)
ALTER TABLE food_log_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own food log items" ON food_log_items
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM food_logs
            WHERE food_logs.id = food_log_items.food_log_id
            AND food_logs.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own food log items" ON food_log_items
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM food_logs
            WHERE food_logs.id = food_log_items.food_log_id
            AND food_logs.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update own food log items" ON food_log_items
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM food_logs
            WHERE food_logs.id = food_log_items.food_log_id
            AND food_logs.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete own food log items" ON food_log_items
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM food_logs
            WHERE food_logs.id = food_log_items.food_log_id
            AND food_logs.user_id = auth.uid()
        )
    );

-- ============================================
-- 3. TABLE food_photos (Photos de repas)
-- ============================================

CREATE TABLE IF NOT EXISTS food_photos (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    food_log_id UUID REFERENCES food_logs(id) ON DELETE CASCADE NOT NULL,
    
    -- Stockage Supabase
    storage_path TEXT NOT NULL,     -- Chemin dans bucket 'food-photos'
    thumbnail_path TEXT,            -- Thumbnail (optionnel)
    file_size_bytes INTEGER,        -- Taille du fichier
    mime_type TEXT,                 -- Type MIME (image/jpeg, etc.)
    
    -- Analyse IA (future feature)
    analysis_status TEXT DEFAULT 'pending' 
        CHECK (analysis_status IN ('pending', 'processing', 'analyzed', 'failed', 'manual')),
    analysis_result JSONB,          -- Résultat GPT-4 Vision
    analysis_confidence FLOAT,      -- Confiance 0-1
    analyzed_at TIMESTAMPTZ,
    
    -- Métadonnées
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index
CREATE INDEX idx_food_photos_log 
    ON food_photos(food_log_id);

CREATE INDEX idx_food_photos_analysis 
    ON food_photos(analysis_status) WHERE analysis_status = 'pending';

-- Commentaires
COMMENT ON TABLE food_photos IS 
    'Photos de repas avec analyse IA optionnelle';

COMMENT ON COLUMN food_photos.analysis_status IS 
    'Statut analyse: pending (en attente), processing (en cours), analyzed (terminé), failed (échec), manual (pas d''analyse IA)';

COMMENT ON COLUMN food_photos.analysis_result IS 
    'Résultat GPT-4 Vision: {items: [...], total_calories: ..., confidence: ...}';

-- RLS
ALTER TABLE food_photos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own food photos" ON food_photos
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM food_logs
            WHERE food_logs.id = food_photos.food_log_id
            AND food_logs.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own food photos" ON food_photos
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM food_logs
            WHERE food_logs.id = food_photos.food_log_id
            AND food_logs.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update own food photos" ON food_photos
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM food_logs
            WHERE food_logs.id = food_photos.food_log_id
            AND food_logs.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete own food photos" ON food_photos
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM food_logs
            WHERE food_logs.id = food_photos.food_log_id
            AND food_logs.user_id = auth.uid()
        )
    );

-- ============================================
-- 4. TRIGGERS : Mise à jour automatique totaux
-- ============================================

CREATE OR REPLACE FUNCTION update_food_log_totals()
RETURNS TRIGGER AS $$
DECLARE
    log_id UUID;
BEGIN
    -- Déterminer le food_log_id concerné
    IF TG_OP = 'DELETE' THEN
        log_id := OLD.food_log_id;
    ELSE
        log_id := NEW.food_log_id;
    END IF;
    
    -- Recalculer tous les totaux
    UPDATE food_logs
    SET
        total_calories = COALESCE((
            SELECT SUM(calories)
            FROM food_log_items
            WHERE food_log_id = log_id
        ), 0),
        total_protein = COALESCE((
            SELECT SUM(protein)
            FROM food_log_items
            WHERE food_log_id = log_id
        ), 0),
        total_carbs = COALESCE((
            SELECT SUM(carbs)
            FROM food_log_items
            WHERE food_log_id = log_id
        ), 0),
        total_fat = COALESCE((
            SELECT SUM(fat)
            FROM food_log_items
            WHERE food_log_id = log_id
        ), 0),
        total_fiber = COALESCE((
            SELECT SUM(fiber)
            FROM food_log_items
            WHERE food_log_id = log_id
        ), 0),
        total_sugar = COALESCE((
            SELECT SUM(sugar)
            FROM food_log_items
            WHERE food_log_id = log_id
        ), 0),
        total_sodium = COALESCE((
            SELECT SUM(sodium)
            FROM food_log_items
            WHERE food_log_id = log_id
        ), 0),
        updated_at = NOW()
    WHERE id = log_id;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Appliquer trigger sur toutes les opérations
CREATE TRIGGER trigger_update_food_log_totals_insert
    AFTER INSERT ON food_log_items
    FOR EACH ROW
    EXECUTE FUNCTION update_food_log_totals();

CREATE TRIGGER trigger_update_food_log_totals_update
    AFTER UPDATE ON food_log_items
    FOR EACH ROW
    EXECUTE FUNCTION update_food_log_totals();

CREATE TRIGGER trigger_update_food_log_totals_delete
    AFTER DELETE ON food_log_items
    FOR EACH ROW
    EXECUTE FUNCTION update_food_log_totals();

-- ============================================
-- 5. FONCTION RPC : Récupérer diary d'un jour
-- ============================================

CREATE OR REPLACE FUNCTION get_food_diary_by_date(
    p_user_id UUID,
    p_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    log_id UUID,
    meal_type TEXT,
    logged_at TIMESTAMPTZ,
    notes TEXT,
    total_calories FLOAT,
    total_protein FLOAT,
    total_carbs FLOAT,
    total_fat FLOAT,
    items JSONB,
    photos JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        fl.id as log_id,
        fl.meal_type,
        fl.logged_at,
        fl.notes,
        fl.total_calories,
        fl.total_protein,
        fl.total_carbs,
        fl.total_fat,
        -- Agréger items en JSONB
        COALESCE(
            (SELECT jsonb_agg(
                jsonb_build_object(
                    'id', fli.id,
                    'food_name', fli.food_name,
                    'serving_size', fli.serving_size,
                    'serving_unit', fli.serving_unit,
                    'calories', fli.calories,
                    'protein', fli.protein,
                    'carbs', fli.carbs,
                    'fat', fli.fat,
                    'source', fli.source
                ) ORDER BY fli.display_order
            )
            FROM food_log_items fli
            WHERE fli.food_log_id = fl.id),
            '[]'::jsonb
        ) as items,
        -- Agréger photos en JSONB
        COALESCE(
            (SELECT jsonb_agg(
                jsonb_build_object(
                    'id', fp.id,
                    'storage_path', fp.storage_path,
                    'thumbnail_path', fp.thumbnail_path
                )
            )
            FROM food_photos fp
            WHERE fp.food_log_id = fl.id),
            '[]'::jsonb
        ) as photos
    FROM food_logs fl
    WHERE fl.user_id = p_user_id
      AND fl.logged_at::DATE = p_date
    ORDER BY fl.logged_at;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_food_diary_by_date IS 
    'Récupère le journal alimentaire complet d''un utilisateur pour un jour donné';

-- ============================================
-- 6. VIEW : Compatibilité avec ancien schéma
-- ============================================

-- Pour compatibilité avec l'ancien schéma food_diary_entries (si existant)
CREATE OR REPLACE VIEW food_diary_entries AS
SELECT
    fli.id,
    fl.user_id,
    fl.meal_type,
    fli.food_name,
    fli.serving_size,
    fli.serving_unit,
    fli.calories,
    fli.protein,
    fli.carbs,
    fli.fat,
    fli.fiber,
    fli.sugar,
    fli.sodium,
    fl.logged_at,
    fli.source,
    fli.fatsecret_id,
    fli.created_at
FROM food_log_items fli
JOIN food_logs fl ON fl.id = fli.food_log_id
ORDER BY fl.logged_at DESC, fli.display_order;

COMMENT ON VIEW food_diary_entries IS 
    'Vue de compatibilité avec l''ancien schéma (un item par ligne)';

-- ============================================
-- 7. VALIDATION
-- ============================================

DO $$
BEGIN
    RAISE NOTICE 'Migration 021 completed successfully';
    RAISE NOTICE 'Tables created: food_logs, food_log_items, food_photos';
    RAISE NOTICE 'Triggers: Auto-update totals on food_log_items changes';
    RAISE NOTICE 'RPC function: get_food_diary_by_date(user_id, date)';
END $$;

-- ============================================
-- FIN DE LA MIGRATION
-- ============================================
