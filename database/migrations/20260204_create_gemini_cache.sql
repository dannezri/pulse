-- Migration: Création de la table de cache pour les explications Gemini
-- Date: 2026-02-04
-- Description: Évite les appels redondants à Gemini 3 Pro (payant + lent)

CREATE TABLE IF NOT EXISTS gemini_explanations_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    target_date DATE NOT NULL,
    
    -- Hash des données sources (pour détecter les changements)
    data_hash TEXT NOT NULL,
    
    -- Réponse complète de Gemini (JSON)
    explanation JSONB NOT NULL,
    
    -- Métadonnées
    energy_score INTEGER,
    confidence INTEGER,
    label TEXT,
    
    -- Timestamps
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    
    -- Index
    UNIQUE(user_id, target_date, data_hash)
);

-- Index pour recherches rapides
CREATE INDEX idx_gemini_cache_user_date ON gemini_explanations_cache(user_id, target_date);
CREATE INDEX idx_gemini_cache_expires ON gemini_explanations_cache(expires_at);

-- RLS Policies
ALTER TABLE gemini_explanations_cache ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own cached explanations"
    ON gemini_explanations_cache
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Service role can insert cached explanations"
    ON gemini_explanations_cache
    FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Service role can update cached explanations"
    ON gemini_explanations_cache
    FOR UPDATE
    USING (true);

CREATE POLICY "Service role can delete cached explanations"
    ON gemini_explanations_cache
    FOR DELETE
    USING (true);

-- Fonction pour nettoyer les caches expirés (à exécuter quotidiennement)
CREATE OR REPLACE FUNCTION cleanup_expired_gemini_cache()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM gemini_explanations_cache
    WHERE expires_at < NOW();
    
    RAISE NOTICE 'Cleaned up expired Gemini cache entries';
END;
$$;

-- Commentaires
COMMENT ON TABLE gemini_explanations_cache IS 'Cache des explications Gemini pour éviter les appels redondants (coût + latence)';
COMMENT ON COLUMN gemini_explanations_cache.data_hash IS 'Hash MD5 des données sources (energy + forecast + biometrics) pour détecter les changements';
COMMENT ON COLUMN gemini_explanations_cache.expires_at IS 'Cache expiré après 24h ou si données sources changent';
