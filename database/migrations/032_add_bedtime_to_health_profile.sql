-- ============================================
-- MIGRATION 032: Ajouter bedtime_end au health_profile
-- ============================================
-- Cette migration ajoute la récupération de l'heure de réveil (bedtime_end)
-- depuis les biometrics pour permettre au modèle d'énergie de démarrer
-- la courbe depuis l'heure de réveil réelle

-- Mettre à jour la fonction get_today_health_profile pour inclure bedtime_end
CREATE OR REPLACE FUNCTION get_today_health_profile(p_user_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_profile JSONB;
    v_bedtime_end TIMESTAMP WITH TIME ZONE;
BEGIN
    -- Récupérer le bedtime_end du jour (heure de réveil)
    SELECT recorded_at
    INTO v_bedtime_end
    FROM biometrics
    WHERE user_id = p_user_id
      AND metric_type = 'bedtime_end'
      AND DATE(recorded_at) = CURRENT_DATE
    ORDER BY recorded_at DESC
    LIMIT 1;
    
    -- Si pas de bedtime_end aujourd'hui, prendre celui d'hier (plus réaliste)
    IF v_bedtime_end IS NULL THEN
        SELECT recorded_at
        INTO v_bedtime_end
        FROM biometrics
        WHERE user_id = p_user_id
          AND metric_type = 'bedtime_end'
          AND DATE(recorded_at) = CURRENT_DATE - INTERVAL '1 day'
        ORDER BY recorded_at DESC
        LIMIT 1;
    END IF;
    
    -- Construire le profil avec bedtime_end
    SELECT jsonb_build_object(
        'readiness_score', COALESCE((current_metrics->>'readiness_score')::int, 0),
        'hrv_ms', COALESCE((current_metrics->>'hrv_ms')::int, 0),
        'anomalies', COALESCE(anomalies, '[]'::jsonb),
        'profile_date', TO_CHAR(health_profiles.date, 'YYYY-MM-DD'),
        'bedtime_end', v_bedtime_end
    )
    INTO v_profile
    FROM health_profiles
    WHERE health_profiles.user_id = p_user_id
      AND health_profiles.date = CURRENT_DATE
    LIMIT 1;
    
    -- Si pas de health_profile, retourner au moins bedtime_end
    IF v_profile IS NULL AND v_bedtime_end IS NOT NULL THEN
        v_profile := jsonb_build_object(
            'readiness_score', 0,
            'hrv_ms', 0,
            'anomalies', '[]'::jsonb,
            'profile_date', TO_CHAR(CURRENT_DATE, 'YYYY-MM-DD'),
            'bedtime_end', v_bedtime_end
        );
    END IF;
    
    RETURN COALESCE(v_profile, '{}'::jsonb);
END;
$$;

COMMENT ON FUNCTION get_today_health_profile IS 'Récupère le profil santé du jour + bedtime_end (heure de réveil) pour calcul Pulse Energy Decay';
