-- Migration: Création de la table personalized_weights pour le ML adaptatif
-- Date: 2026-01-31
-- Description: Stocke les multiplicateurs personnalisés par utilisateur pour chaque facteur (médicament/condition)

CREATE TABLE IF NOT EXISTS personalized_weights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    
    -- Identification du facteur
    factor_type TEXT NOT NULL CHECK (factor_type IN ('medication', 'condition')), -- Type de facteur
    factor_code TEXT NOT NULL, -- ATC code pour médicament, ICD-11 pour condition
    factor_name TEXT, -- Nom lisible (ex: "Sertraline", "Dépression")
    
    -- Poids personnalisé
    weight_multiplier FLOAT NOT NULL DEFAULT 1.0 CHECK (weight_multiplier >= 0.5 AND weight_multiplier <= 2.0),
    -- 1.0 = baseline (impact par défaut)
    -- < 1.0 = l'utilisateur tolère mieux (impact réduit)
    -- > 1.0 = l'utilisateur est plus sensible (impact augmenté)
    
    -- Historique d'apprentissage
    feedback_count INT DEFAULT 0, -- Nombre de feedbacks ayant influencé ce poids
    last_adjustment TIMESTAMPTZ, -- Dernière modification du poids
    adjustment_history JSONB DEFAULT '[]'::jsonb, -- Historique des ajustements
    -- Format: [{"date": "2026-01-31T15:00:00Z", "old_weight": 1.0, "new_weight": 0.95, "error": 7.3}]
    
    -- Statistiques
    avg_error FLOAT, -- Erreur moyenne pour ce facteur
    confidence_score FLOAT DEFAULT 0.0, -- Score de confiance (0-1) basé sur feedback_count
    
    -- Métadonnées
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Contrainte d'unicité : un seul poids par utilisateur par facteur
    CONSTRAINT personalized_weights_unique UNIQUE (user_id, factor_type, factor_code)
);

-- Index pour performance
CREATE INDEX idx_personalized_weights_user ON personalized_weights(user_id, is_active);
CREATE INDEX idx_personalized_weights_factor ON personalized_weights(factor_code, factor_type);
CREATE INDEX idx_personalized_weights_confidence ON personalized_weights(confidence_score DESC);

-- RLS Policies
ALTER TABLE personalized_weights ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own weights"
    ON personalized_weights FOR SELECT
    USING (auth.uid() = user_id);

-- Fonction pour récupérer le poids personnalisé d'un facteur
CREATE OR REPLACE FUNCTION get_personalized_weight(
    p_user_id UUID,
    p_factor_type TEXT,
    p_factor_code TEXT
)
RETURNS FLOAT
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_weight FLOAT;
BEGIN
    SELECT weight_multiplier
    INTO v_weight
    FROM personalized_weights
    WHERE user_id = p_user_id
      AND factor_type = p_factor_type
      AND factor_code = p_factor_code
      AND is_active = true;
    
    -- Si pas de poids personnalisé, retourner 1.0 (baseline)
    RETURN COALESCE(v_weight, 1.0);
END;
$$;

-- Fonction pour récupérer tous les poids d'un utilisateur
CREATE OR REPLACE FUNCTION get_all_personalized_weights(p_user_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_weights JSONB;
BEGIN
    SELECT jsonb_object_agg(
        factor_type || ':' || factor_code,
        jsonb_build_object(
            'weight_multiplier', weight_multiplier,
            'feedback_count', feedback_count,
            'confidence_score', confidence_score
        )
    )
    INTO v_weights
    FROM personalized_weights
    WHERE user_id = p_user_id
      AND is_active = true;
    
    RETURN COALESCE(v_weights, '{}'::jsonb);
END;
$$;

-- Trigger pour mettre à jour updated_at
CREATE OR REPLACE FUNCTION update_personalized_weights_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_personalized_weights_timestamp
BEFORE UPDATE ON personalized_weights
FOR EACH ROW
EXECUTE FUNCTION update_personalized_weights_timestamp();

COMMENT ON TABLE personalized_weights IS 'Poids personnalisés par utilisateur pour ajuster l''impact des médicaments et conditions (ML adaptatif)';
COMMENT ON COLUMN personalized_weights.weight_multiplier IS 'Multiplicateur appliqué à l''impact de base (0.5-2.0, défaut 1.0)';
COMMENT ON COLUMN personalized_weights.confidence_score IS 'Confiance dans le poids basée sur le nombre de feedbacks (0-1)';
