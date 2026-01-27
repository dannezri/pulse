-- ============================================
-- MIGRATION 006 : Optimisation Performance biometrics
-- ============================================
-- Cette migration optimise la table biometrics pour gérer des millions de lignes
-- - Index composite optimisé
-- - Index partiels par metric_type
-- - Partitionnement par mois (recorded_at)

-- ============================================
-- 1. INDEX COMPOSITE OPTIMISÉ
-- ============================================

-- Index composite (user_id, recorded_at DESC) pour les requêtes temporelles
-- Remplace l'index existant si nécessaire
DROP INDEX IF EXISTS idx_biometrics_user_date;
CREATE INDEX IF NOT EXISTS idx_biometrics_user_date_optimized 
    ON biometrics(user_id, recorded_at DESC)
    WITH (fillfactor = 90); -- Laisse de l'espace pour les updates

COMMENT ON INDEX idx_biometrics_user_date_optimized IS 
    'Index composite optimisé pour requêtes temporelles par utilisateur. Utilisé pour récupérer les données récentes.';

-- ============================================
-- 2. INDEX PARTIELS PAR METRIC_TYPE
-- ============================================

-- Index partiel pour HR (fréquent)
CREATE INDEX IF NOT EXISTS idx_biometrics_hr_partial 
    ON biometrics(user_id, recorded_at DESC) 
    WHERE metric_type = 'hr'
    WITH (fillfactor = 90);

-- Index partiel pour HRV (fréquent)
CREATE INDEX IF NOT EXISTS idx_biometrics_hrv_partial 
    ON biometrics(user_id, recorded_at DESC) 
    WHERE metric_type = 'hrv'
    WITH (fillfactor = 90);

-- Index partiel pour sleep_duration (fréquent)
CREATE INDEX IF NOT EXISTS idx_biometrics_sleep_partial 
    ON biometrics(user_id, recorded_at DESC) 
    WHERE metric_type IN ('sleep_duration', 'sleep_score', 'sleep_quality')
    WITH (fillfactor = 90);

-- Index partiel pour steps (fréquent)
CREATE INDEX IF NOT EXISTS idx_biometrics_steps_partial 
    ON biometrics(user_id, recorded_at DESC) 
    WHERE metric_type = 'steps'
    WITH (fillfactor = 90);

COMMENT ON INDEX idx_biometrics_hr_partial IS 
    'Index partiel pour HR uniquement. Réduit la taille de l''index et améliore les performances.';

-- ============================================
-- 3. PARTITIONNEMENT PAR MOIS (recorded_at)
-- ============================================

-- Note: Le partitionnement nécessite de recréer la table
-- Cette migration prépare le partitionnement mais ne le force pas
-- (car cela nécessiterait de migrer toutes les données existantes)

-- Fonction pour générer le nom de partition
CREATE OR REPLACE FUNCTION get_biometrics_partition_name(p_date DATE)
RETURNS TEXT AS $$
BEGIN
    RETURN 'biometrics_' || to_char(p_date, 'YYYY_MM');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION get_biometrics_partition_name IS 
    'Génère le nom d''une partition mensuelle pour biometrics';

-- Fonction pour créer une partition mensuelle
CREATE OR REPLACE FUNCTION create_biometrics_partition(p_start_date DATE)
RETURNS VOID AS $$
DECLARE
    v_partition_name TEXT;
    v_end_date DATE;
BEGIN
    v_partition_name := get_biometrics_partition_name(p_start_date);
    v_end_date := (DATE_TRUNC('month', p_start_date) + INTERVAL '1 month')::DATE;
    
    -- Vérifier si la partition existe déjà
    IF NOT EXISTS (
        SELECT 1 FROM pg_class 
        WHERE relname = v_partition_name
    ) THEN
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I PARTITION OF biometrics
            FOR VALUES FROM (%L) TO (%L)
        ', v_partition_name, p_start_date, v_end_date);
        
        RAISE NOTICE 'Partition créée: % (de % à %)', v_partition_name, p_start_date, v_end_date;
    ELSE
        RAISE NOTICE 'Partition existe déjà: %', v_partition_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION create_biometrics_partition IS 
    'Crée une partition mensuelle pour biometrics si elle n''existe pas';

-- Fonction pour créer les partitions futures (3 mois à l'avance)
CREATE OR REPLACE FUNCTION create_future_biometrics_partitions()
RETURNS VOID AS $$
DECLARE
    v_date DATE;
    v_month_count INT := 3; -- Créer 3 mois à l'avance
BEGIN
    -- Créer les partitions pour les mois à venir
    FOR i IN 0..v_month_count LOOP
        v_date := DATE_TRUNC('month', CURRENT_DATE + (i || ' months')::INTERVAL)::DATE;
        PERFORM create_biometrics_partition(v_date);
    END LOOP;
    
    RAISE NOTICE 'Partitions futures créées';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION create_future_biometrics_partitions IS 
    'Crée automatiquement les partitions pour les mois à venir';

-- ============================================
-- 4. VÉRIFICATIONS ET STATISTIQUES
-- ============================================

-- Fonction pour analyser les statistiques de la table
CREATE OR REPLACE FUNCTION analyze_biometrics_stats()
RETURNS TABLE (
    total_rows BIGINT,
    rows_per_user_avg NUMERIC,
    oldest_record TIMESTAMP WITH TIME ZONE,
    newest_record TIMESTAMP WITH TIME ZONE,
    metric_types_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_rows,
        ROUND(AVG(user_count)::NUMERIC, 2) as rows_per_user_avg,
        MIN(recorded_at) as oldest_record,
        MAX(recorded_at) as newest_record,
        COUNT(DISTINCT metric_type)::BIGINT as metric_types_count
    FROM (
        SELECT 
            user_id,
            recorded_at,
            metric_type,
            COUNT(*) OVER (PARTITION BY user_id) as user_count
        FROM biometrics
    ) subq;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION analyze_biometrics_stats IS 
    'Analyse les statistiques de la table biometrics pour monitoring';

-- ============================================
-- 5. MAINTENANCE AUTOMATIQUE
-- ============================================

-- Fonction pour VACUUM et ANALYZE sur les partitions récentes
CREATE OR REPLACE FUNCTION maintain_biometrics_partitions()
RETURNS VOID AS $$
DECLARE
    v_partition_name TEXT;
    v_partition_record RECORD;
BEGIN
    -- VACUUM et ANALYZE sur les partitions des 3 derniers mois
    FOR v_partition_record IN
        SELECT schemaname, tablename
        FROM pg_tables
        WHERE tablename LIKE 'biometrics_%'
          AND tablename >= 'biometrics_' || to_char(CURRENT_DATE - INTERVAL '3 months', 'YYYY_MM')
        ORDER BY tablename DESC
        LIMIT 3
    LOOP
        EXECUTE format('VACUUM ANALYZE %I.%I', v_partition_record.schemaname, v_partition_record.tablename);
        RAISE NOTICE 'Maintenance effectuée sur: %', v_partition_record.tablename;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION maintain_biometrics_partitions IS 
    'Effectue VACUUM et ANALYZE sur les partitions récentes pour optimiser les performances';

-- ============================================
-- 6. INDEX ADDITIONNELS POUR PERFORMANCE
-- ============================================

-- Index pour les requêtes de baselines (7 derniers jours)
CREATE INDEX IF NOT EXISTS idx_biometrics_baseline_query 
    ON biometrics(user_id, metric_type, recorded_at DESC) 
    WHERE recorded_at >= CURRENT_DATE - INTERVAL '7 days'
    WITH (fillfactor = 90);

COMMENT ON INDEX idx_biometrics_baseline_query IS 
    'Index optimisé pour les requêtes de calcul de baselines (7 derniers jours)';

-- Index pour source_event_id (déjà créé, mais vérifier)
-- L'index existant devrait suffire

-- ============================================
-- 7. NOTES IMPORTANTES
-- ============================================

-- IMPORTANT: Pour activer le partitionnement, il faut:
-- 1. Créer une nouvelle table partitionnée
-- 2. Migrer les données existantes
-- 3. Renommer les tables
-- 
-- Cette opération est lourde et doit être planifiée.
-- Pour l'instant, les index optimisés suffisent pour des millions de lignes.
--
-- Le partitionnement sera activé dans une migration ultérieure si nécessaire.

DO $$
BEGIN
    RAISE NOTICE '=== MIGRATION 006 TERMINÉE ===';
    RAISE NOTICE 'Index optimisés créés';
    RAISE NOTICE 'Fonctions de partitionnement préparées';
    RAISE NOTICE '';
    RAISE NOTICE 'IMPORTANT: Les lectures IA doivent utiliser health_profiles, jamais biometrics directement';
    RAISE NOTICE 'Pour activer le partitionnement, exécuter la migration 007 (si nécessaire)';
END $$;
