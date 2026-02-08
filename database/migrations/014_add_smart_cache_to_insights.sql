-- ============================================
-- Migration 014: Smart Cache pour Insights
-- ============================================
-- Ajout des colonnes pour le système de cache intelligent
-- qui évite de rappeler OpenAI si les données biométriques n'ont pas changé

-- Ajouter l'ID de l'événement du calendrier (UUID stable généré par le backend)
ALTER TABLE insights ADD COLUMN IF NOT EXISTS calendar_event_id TEXT;

-- Ajouter le timestamp de référence de la dernière biométrie prise en compte
ALTER TABLE insights ADD COLUMN IF NOT EXISTS biometrics_ref_at TIMESTAMPTZ;

-- Index pour accélérer la recherche d'insights par événement
CREATE INDEX IF NOT EXISTS idx_insights_event ON insights(calendar_event_id);

-- Index composé pour recherche rapide par utilisateur et événement
CREATE INDEX IF NOT EXISTS idx_insights_user_event ON insights(user_id, calendar_event_id, created_at DESC);

-- Commentaires pour documentation
COMMENT ON COLUMN insights.calendar_event_id IS 'UUID stable de l''événement du calendrier (généré côté backend)';
COMMENT ON COLUMN insights.biometrics_ref_at IS 'Timestamp de la dernière donnée biométrique prise en compte lors de la génération de cet insight';
