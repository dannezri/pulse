-- Migration 030: Intraday Energy Forecast
-- Crée la table pour stocker les prévisions d'énergie intraday (courbe de la journée)
-- Différent de energy_forecast (J+1) - Celui-ci est pour la journée en cours

-- Table: intraday_energy_forecast
CREATE TABLE IF NOT EXISTS intraday_energy_forecast (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    forecast_date DATE NOT NULL,
    timezone TEXT NOT NULL DEFAULT 'UTC',
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Données de prévision
    points JSONB NOT NULL,        -- Courbe d'énergie (points toutes les 30 min)
    windows JSONB,                -- Fenêtres de risque (creux d'énergie)
    events JSONB,                 -- Événements calendrier avec impact
    notes JSONB,                  -- Notes explicatives (max 3)
    
    -- Métadonnées
    model_version TEXT NOT NULL DEFAULT 'intraday_v1',
    confidence FLOAT NOT NULL DEFAULT 0.5,
    
    -- Contraintes
    UNIQUE(user_id, forecast_date),
    CHECK (confidence >= 0 AND confidence <= 1)
);

-- Index pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS idx_intraday_forecast_user_date 
    ON intraday_energy_forecast(user_id, forecast_date DESC);

CREATE INDEX IF NOT EXISTS idx_intraday_forecast_generated 
    ON intraday_energy_forecast(generated_at DESC);

-- RPC Function: Récupérer la prévision intraday
CREATE OR REPLACE FUNCTION get_intraday_forecast(
    p_user_id UUID,
    p_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    id UUID,
    user_id UUID,
    forecast_date DATE,
    timezone TEXT,
    generated_at TIMESTAMPTZ,
    points JSONB,
    windows JSONB,
    events JSONB,
    notes JSONB,
    model_version TEXT,
    confidence FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.id,
        f.user_id,
        f.forecast_date,
        f.timezone,
        f.generated_at,
        f.points,
        f.windows,
        f.events,
        f.notes,
        f.model_version,
        f.confidence
    FROM intraday_energy_forecast f
    WHERE f.user_id = p_user_id
      AND f.forecast_date = p_date
    ORDER BY f.generated_at DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql STABLE;

-- Commentaires
COMMENT ON TABLE intraday_energy_forecast IS 
    'Prévisions d''énergie intraday (courbe sur la journée) - Utilisé par IntradayEnergyCurveCard';

COMMENT ON COLUMN intraday_energy_forecast.points IS 
    'Points de la courbe d''énergie toutes les 30 minutes - Format: [{"t": "ISO8601", "energy": 0-100}]';

COMMENT ON COLUMN intraday_energy_forecast.windows IS 
    'Fenêtres de risque (creux d''énergie) - Format: [{"from": "HH:MM", "to": "HH:MM", "kind": "dip", "label": "..."}]';

COMMENT ON COLUMN intraday_energy_forecast.events IS 
    'Événements calendrier avec impact - Format: [{"id": "...", "start": "ISO8601", "end": "ISO8601", "title": "...", "impact": -20 à +10, "confidence": 0-1, "tags": [...]}]';

COMMENT ON COLUMN intraday_energy_forecast.notes IS 
    'Notes explicatives (max 3) - Format: ["Note 1", "Note 2", "Note 3"]';
