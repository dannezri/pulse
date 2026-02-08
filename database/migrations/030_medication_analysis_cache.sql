-- Migration: Medication Analysis Cache Table
-- Stocke les analyses générées par Gemini pour les médicaments
-- Cache de 7 jours pour économiser les appels API

CREATE TABLE IF NOT EXISTS medication_analysis_cache (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    medications_hash VARCHAR(32) NOT NULL, -- MD5 hash des médicaments
    analysis JSONB NOT NULL, -- Analyse générée par Gemini
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Index pour recherche rapide
    UNIQUE(user_id, medications_hash)
);

-- Index pour performance
CREATE INDEX IF NOT EXISTS idx_medication_analysis_cache_user_id 
    ON medication_analysis_cache(user_id);
CREATE INDEX IF NOT EXISTS idx_medication_analysis_cache_expires_at 
    ON medication_analysis_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_medication_analysis_cache_hash 
    ON medication_analysis_cache(medications_hash);

-- RLS Policies
ALTER TABLE medication_analysis_cache ENABLE ROW LEVEL SECURITY;

-- Policy: Utilisateurs peuvent lire leurs propres analyses
CREATE POLICY "Users can view their own medication analysis cache"
    ON medication_analysis_cache
    FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Service backend peut tout faire (via service_role key)
CREATE POLICY "Service role can manage all medication analysis cache"
    ON medication_analysis_cache
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Commentaires
COMMENT ON TABLE medication_analysis_cache IS 'Cache des analyses de médicaments générées par Gemini 3 Pro';
COMMENT ON COLUMN medication_analysis_cache.medications_hash IS 'Hash MD5 des médicaments pour détecter les changements';
COMMENT ON COLUMN medication_analysis_cache.analysis IS 'Analyse JSON générée par Gemini avec intro, impacts, observations';
COMMENT ON COLUMN medication_analysis_cache.expires_at IS 'Date d''expiration du cache (7 jours par défaut)';
