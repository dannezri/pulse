-- Migration: Création de la table user_feedback pour le ML adaptatif
-- Date: 2026-01-31
-- Description: Stocke les feedbacks utilisateurs pour ajuster les poids personnalisés

CREATE TABLE IF NOT EXISTS user_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    
    -- Scores
    system_score FLOAT NOT NULL, -- Score calculé par l'algorithme (0-100)
    user_score INT NOT NULL CHECK (user_score >= 0 AND user_score <= 100), -- Score ressenti par l'utilisateur
    error FLOAT GENERATED ALWAYS AS (user_score - system_score) STORED, -- Erreur quadratique
    
    -- Contexte
    active_factors JSONB NOT NULL DEFAULT '{}'::jsonb, -- Snapshot des médicaments/conditions actifs
    -- Format: {
    --   "medications": [{"atc_code": "N06AB06", "impact": -20, "weight": 1.0}],
    --   "conditions": [{"icd11_code": "6A70", "decay_rate": 0.08, "malus": -10, "weight": 1.0}]
    -- }
    
    energy_at_feedback FLOAT, -- Énergie calculée au moment du feedback
    hours_since_wake FLOAT, -- Heures depuis le réveil
    time_of_day TIME, -- Heure du feedback
    
    -- Métadonnées
    processed BOOLEAN DEFAULT false, -- Traité par l'optimiseur ML
    processed_at TIMESTAMPTZ,
    feedback_context TEXT, -- "low_energy_trigger" | "manual" | "energy_spike"
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Index pour performance
    CONSTRAINT user_feedback_unique UNIQUE (user_id, created_at)
);

-- Index pour requêtes rapides
CREATE INDEX idx_user_feedback_user_processed ON user_feedback(user_id, processed);
CREATE INDEX idx_user_feedback_created ON user_feedback(created_at DESC);
CREATE INDEX idx_user_feedback_error ON user_feedback(ABS(error) DESC) WHERE NOT processed;

-- RLS Policies
ALTER TABLE user_feedback ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own feedback"
    ON user_feedback FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own feedback"
    ON user_feedback FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Fonction pour compter les feedbacks non traités
CREATE OR REPLACE FUNCTION get_unprocessed_feedback_count(p_user_id UUID)
RETURNS INT
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_count INT;
BEGIN
    SELECT COUNT(*)
    INTO v_count
    FROM user_feedback
    WHERE user_id = p_user_id
      AND processed = false;
    
    RETURN v_count;
END;
$$;

COMMENT ON TABLE user_feedback IS 'Stocke les feedbacks utilisateurs pour le système ML adaptatif (PWA)';
COMMENT ON COLUMN user_feedback.error IS 'Erreur = user_score - system_score (positif = utilisateur se sent mieux que prévu)';
COMMENT ON COLUMN user_feedback.active_factors IS 'Snapshot JSON des facteurs actifs au moment du feedback pour ajuster les poids';
