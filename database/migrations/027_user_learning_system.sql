-- Migration 027: User Learning System (Action → Effect)
-- Système d'apprentissage pour personnaliser les prédictions et recommandations

-- Table: user_action_logs
-- Track les recommandations données et si l'utilisateur les a suivies
CREATE TABLE IF NOT EXISTS user_action_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Date de la recommandation
    action_date DATE NOT NULL,
    
    -- Type de recommandation
    recommendation_type TEXT NOT NULL,
    -- Ex: "sleep_earlier", "skip_workout", "reduce_caffeine", "increase_protein"
    
    -- Détails de la recommandation
    recommendation_text TEXT NOT NULL,
    -- Ex: "Couche-toi 1h plus tôt ce soir"
    
    -- Contexte au moment de la recommandation
    context JSONB NOT NULL,
    -- {
    --   "recovery_score": 0.65,
    --   "sleep_debt": 3.2,
    --   "predicted_energy_tomorrow": 52,
    --   "primary_cause": "sleep_debt"
    -- }
    
    -- L'utilisateur a-t-il suivi la recommandation ?
    followed BOOLEAN,
    -- null = pas encore de feedback, true = suivi, false = ignoré
    
    -- Feedback utilisateur (optionnel)
    user_feedback TEXT,
    -- Ex: "Trop difficile de me coucher plus tôt", "J'ai essayé"
    
    -- Quand l'utilisateur a donné son feedback
    feedback_at TIMESTAMP WITH TIME ZONE,
    
    -- Métadonnées
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Index pour requêtes rapides
    CONSTRAINT unique_user_action_date UNIQUE(user_id, action_date, recommendation_type)
);

-- Table: forecast_feedback
-- Compare prédictions vs réalité pour mesurer précision et apprendre
CREATE TABLE IF NOT EXISTS forecast_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Date de la journée évaluée (J)
    feedback_date DATE NOT NULL,
    
    -- Prédiction faite la veille (J-1)
    predicted_energy_score INTEGER,
    predicted_state TEXT,
    
    -- Réalité mesurée le jour J
    actual_energy_score INTEGER,
    actual_state TEXT,
    
    -- Métriques réelles du jour J
    actual_metrics JSONB,
    -- {
    --   "recovery": 0.72,
    --   "hrv": 65,
    --   "sleep_quality": 0.85,
    --   "user_felt_energy": 70  // optionnel : ressenti utilisateur
    -- }
    
    -- Erreur de prédiction
    prediction_error INTEGER,
    -- |predicted - actual|
    
    -- Recommandation donnée et suivie ?
    recommendation_followed BOOLEAN,
    recommendation_type TEXT,
    
    -- Impact mesuré (si recommandation suivie)
    impact JSONB,
    -- {
    --   "expected_effect": +15,
    --   "observed_effect": +18,
    --   "success": true
    -- }
    
    -- Confiance de la prédiction originale
    prediction_confidence DECIMAL,
    
    -- Métadonnées
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Contrainte
    CONSTRAINT unique_user_feedback_date UNIQUE(user_id, feedback_date)
);

-- Table: user_learning_weights
-- Poids personnalisés pour le modèle prédictif de chaque utilisateur
CREATE TABLE IF NOT EXISTS user_learning_weights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Poids pour chaque facteur (ajustés par apprentissage)
    recovery_weight DECIMAL DEFAULT 30.0,
    sleep_debt_weight DECIMAL DEFAULT -10.0,
    overtrain_weight DECIMAL DEFAULT -30.0,
    infection_weight DECIMAL DEFAULT -40.0,
    activity_weight DECIMAL DEFAULT -5.0,
    
    -- Patterns appris spécifiques à cet utilisateur
    learned_patterns JSONB,
    -- {
    --   "sleep_earlier_effect": { "avg_impact": +12, "success_rate": 0.75, "sample_size": 8 },
    --   "skip_workout_effect": { "avg_impact": +8, "success_rate": 0.90, "sample_size": 5 },
    --   "reduce_caffeine_effect": { "avg_impact": +5, "success_rate": 0.60, "sample_size": 3 }
    -- }
    
    -- Métriques de performance du modèle
    model_performance JSONB,
    -- {
    --   "mae": 8.5,              // Mean Absolute Error
    --   "accuracy_rate": 0.82,   // % prédictions correctes (±10%)
    --   "total_predictions": 45,
    --   "learning_iterations": 12
    -- }
    
    -- Version du modèle d'apprentissage
    model_version TEXT DEFAULT 'v1_adaptive',
    
    -- Dernière mise à jour
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Un seul enregistrement par utilisateur
    CONSTRAINT unique_user_weights UNIQUE(user_id)
);

-- Index pour performance
CREATE INDEX idx_action_logs_user_date ON user_action_logs(user_id, action_date DESC);
CREATE INDEX idx_feedback_user_date ON forecast_feedback(user_id, feedback_date DESC);
CREATE INDEX idx_action_logs_followed ON user_action_logs(user_id, followed) WHERE followed IS NOT NULL;

-- RLS Policies
ALTER TABLE user_action_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE forecast_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_learning_weights ENABLE ROW LEVEL SECURITY;

-- Policies: user_action_logs
CREATE POLICY "Users can view own action logs"
    ON user_action_logs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own action logs"
    ON user_action_logs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own action logs"
    ON user_action_logs FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "System can manage action logs"
    ON user_action_logs FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- Policies: forecast_feedback
CREATE POLICY "Users can view own feedback"
    ON forecast_feedback FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "System can manage feedback"
    ON forecast_feedback FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- Policies: user_learning_weights
CREATE POLICY "Users can view own weights"
    ON user_learning_weights FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "System can manage weights"
    ON user_learning_weights FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- RPC Functions

-- 1. Enregistrer une action utilisateur
CREATE OR REPLACE FUNCTION log_user_action(
    p_user_id UUID,
    p_action_date DATE,
    p_recommendation_type TEXT,
    p_recommendation_text TEXT,
    p_context JSONB
) RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_log_id UUID;
BEGIN
    INSERT INTO user_action_logs (
        user_id,
        action_date,
        recommendation_type,
        recommendation_text,
        context
    ) VALUES (
        p_user_id,
        p_action_date,
        p_recommendation_type,
        p_recommendation_text,
        p_context
    )
    ON CONFLICT (user_id, action_date, recommendation_type)
    DO UPDATE SET
        recommendation_text = EXCLUDED.recommendation_text,
        context = EXCLUDED.context
    RETURNING id INTO v_log_id;
    
    RETURN v_log_id;
END;
$$;

-- 2. Enregistrer feedback utilisateur (a-t-il suivi la recommandation ?)
CREATE OR REPLACE FUNCTION record_action_feedback(
    p_user_id UUID,
    p_action_date DATE,
    p_recommendation_type TEXT,
    p_followed BOOLEAN,
    p_user_feedback TEXT DEFAULT NULL
) RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    UPDATE user_action_logs
    SET 
        followed = p_followed,
        user_feedback = p_user_feedback,
        feedback_at = NOW()
    WHERE user_id = p_user_id
      AND action_date = p_action_date
      AND recommendation_type = p_recommendation_type;
    
    RETURN FOUND;
END;
$$;

-- 3. Calculer feedback de prédiction (prévu vs réel)
CREATE OR REPLACE FUNCTION calculate_forecast_feedback(
    p_user_id UUID,
    p_feedback_date DATE
) RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_predicted_score INTEGER;
    v_predicted_state TEXT;
    v_prediction_confidence DECIMAL;
    v_actual_recovery DECIMAL;
    v_actual_energy INTEGER;
    v_error INTEGER;
    v_recommendation_followed BOOLEAN;
    v_recommendation_type TEXT;
BEGIN
    -- Récupérer prédiction de la veille
    SELECT 
        predicted_energy_score,
        predicted_state,
        confidence
    INTO v_predicted_score, v_predicted_state, v_prediction_confidence
    FROM energy_forecast
    WHERE user_id = p_user_id
      AND forecast_date = p_feedback_date
    ORDER BY created_at DESC
    LIMIT 1;
    
    IF v_predicted_score IS NULL THEN
        RETURN FALSE;  -- Pas de prédiction trouvée
    END IF;
    
    -- Récupérer recovery réel du jour
    SELECT smoothed_score
    INTO v_actual_recovery
    FROM daily_state
    WHERE user_id = p_user_id
      AND state_date = p_feedback_date
      AND state_type = 'recovery';
    
    -- Calculer énergie réelle (approximation)
    v_actual_energy := COALESCE(v_actual_recovery * 100, 50);
    
    -- Calculer erreur
    v_error := ABS(v_predicted_score - v_actual_energy);
    
    -- Vérifier si recommandation suivie (veille)
    SELECT followed, recommendation_type
    INTO v_recommendation_followed, v_recommendation_type
    FROM user_action_logs
    WHERE user_id = p_user_id
      AND action_date = p_feedback_date - INTERVAL '1 day';
    
    -- Insérer feedback
    INSERT INTO forecast_feedback (
        user_id,
        feedback_date,
        predicted_energy_score,
        predicted_state,
        actual_energy_score,
        actual_metrics,
        prediction_error,
        recommendation_followed,
        recommendation_type,
        prediction_confidence
    ) VALUES (
        p_user_id,
        p_feedback_date,
        v_predicted_score,
        v_predicted_state,
        v_actual_energy,
        jsonb_build_object('recovery', v_actual_recovery),
        v_error,
        v_recommendation_followed,
        v_recommendation_type,
        v_prediction_confidence
    )
    ON CONFLICT (user_id, feedback_date) DO UPDATE
    SET 
        actual_energy_score = EXCLUDED.actual_energy_score,
        actual_metrics = EXCLUDED.actual_metrics,
        prediction_error = EXCLUDED.prediction_error;
    
    RETURN TRUE;
END;
$$;

-- 4. Récupérer statistiques d'apprentissage utilisateur
CREATE OR REPLACE FUNCTION get_user_learning_stats(
    p_user_id UUID
) RETURNS TABLE(
    total_recommendations INTEGER,
    followed_count INTEGER,
    follow_rate DECIMAL,
    avg_prediction_error DECIMAL,
    best_recommendation TEXT,
    best_impact DECIMAL
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    WITH stats AS (
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE followed = true) as followed,
            CAST(COUNT(*) FILTER (WHERE followed = true) AS DECIMAL) / NULLIF(COUNT(*), 0) as rate
        FROM user_action_logs
        WHERE user_id = p_user_id
          AND followed IS NOT NULL
    ),
    prediction_stats AS (
        SELECT AVG(prediction_error) as avg_error
        FROM forecast_feedback
        WHERE user_id = p_user_id
    ),
    best_rec AS (
        SELECT 
            ff.recommendation_type,
            AVG(
                CASE 
                    WHEN al.followed = true 
                    THEN ff.actual_energy_score - ff.predicted_energy_score
                    ELSE 0
                END
            ) as avg_impact
        FROM forecast_feedback ff
        LEFT JOIN user_action_logs al 
            ON al.user_id = ff.user_id 
            AND al.action_date = ff.feedback_date - INTERVAL '1 day'
        WHERE ff.user_id = p_user_id
          AND ff.recommendation_followed = true
        GROUP BY ff.recommendation_type
        ORDER BY avg_impact DESC
        LIMIT 1
    )
    SELECT 
        COALESCE(s.total, 0)::INTEGER,
        COALESCE(s.followed, 0)::INTEGER,
        COALESCE(s.rate, 0.0),
        COALESCE(ps.avg_error, 0.0),
        br.recommendation_type,
        COALESCE(br.avg_impact, 0.0)
    FROM stats s, prediction_stats ps
    LEFT JOIN best_rec br ON true;
END;
$$;

-- Grant permissions
GRANT EXECUTE ON FUNCTION log_user_action(UUID, DATE, TEXT, TEXT, JSONB) TO authenticated;
GRANT EXECUTE ON FUNCTION record_action_feedback(UUID, DATE, TEXT, BOOLEAN, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION calculate_forecast_feedback(UUID, DATE) TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_learning_stats(UUID) TO authenticated;

-- Comments
COMMENT ON TABLE user_action_logs IS 'Track recommandations données et si utilisateur les a suivies';
COMMENT ON TABLE forecast_feedback IS 'Compare prédictions vs réalité pour mesurer précision';
COMMENT ON TABLE user_learning_weights IS 'Poids personnalisés du modèle prédictif par utilisateur';
COMMENT ON COLUMN user_action_logs.followed IS 'null=pas de feedback, true=suivi, false=ignoré';
COMMENT ON COLUMN forecast_feedback.prediction_error IS 'Erreur absolue entre prévu et réel';
COMMENT ON COLUMN user_learning_weights.learned_patterns IS 'Patterns action→effet appris pour cet utilisateur';
