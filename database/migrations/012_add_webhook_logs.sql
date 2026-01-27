-- Migration: Ajouter table pour logger les webhooks Vital
-- Description: Stocke tous les webhooks reçus avec leurs détails pour debugging

-- Table pour les logs de webhooks
CREATE TABLE IF NOT EXISTS webhook_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Informations de la requête
    endpoint TEXT NOT NULL,                          -- Ex: /api/webhooks/vital
    method TEXT NOT NULL DEFAULT 'POST',             -- HTTP method
    
    -- Payload du webhook
    event_type TEXT,                                 -- Ex: historical.data.water.created
    user_id TEXT,                                    -- Vital user_id
    client_user_id UUID REFERENCES profiles(id),     -- Supabase user_id
    payload JSONB NOT NULL,                          -- Payload complet
    
    -- Métadonnées
    status_code INT NOT NULL DEFAULT 200,            -- Code de réponse HTTP
    response_message TEXT,                           -- Message de réponse
    duration_ms INT,                                 -- Durée de traitement (ms)
    error TEXT,                                      -- Message d'erreur si échec
    
    -- Headers (optionnel)
    headers JSONB,                                   -- Headers HTTP reçus
    
    -- Timestamps
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- Timestamp de réception
    processed_at TIMESTAMPTZ,                        -- Timestamp de fin de traitement
    
    -- Indexation
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index pour performances
CREATE INDEX IF NOT EXISTS idx_webhook_logs_endpoint ON webhook_logs(endpoint);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_event_type ON webhook_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_client_user_id ON webhook_logs(client_user_id);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_received_at ON webhook_logs(received_at DESC);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_status_code ON webhook_logs(status_code);

-- Index composite pour récupération rapide
CREATE INDEX IF NOT EXISTS idx_webhook_logs_user_time 
    ON webhook_logs(client_user_id, received_at DESC)
    WHERE client_user_id IS NOT NULL;

-- RLS (Row Level Security)
ALTER TABLE webhook_logs ENABLE ROW LEVEL SECURITY;

-- Policy : Les utilisateurs peuvent voir leurs propres webhooks
CREATE POLICY "Users can view their own webhook logs"
    ON webhook_logs
    FOR SELECT
    USING (client_user_id = auth.uid());

-- Policy : Service role peut tout faire (pour le backend)
CREATE POLICY "Service role can insert webhook logs"
    ON webhook_logs
    FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Service role can select all webhook logs"
    ON webhook_logs
    FOR SELECT
    USING (true);

-- Fonction pour récupérer les derniers webhooks d'un utilisateur
CREATE OR REPLACE FUNCTION get_user_webhook_logs(
    p_user_id UUID,
    p_limit INT DEFAULT 50
)
RETURNS TABLE (
    id UUID,
    endpoint TEXT,
    method TEXT,
    event_type TEXT,
    status_code INT,
    response_message TEXT,
    duration_ms INT,
    error TEXT,
    received_at TIMESTAMPTZ,
    processed_at TIMESTAMPTZ,
    payload JSONB
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        wl.id,
        wl.endpoint,
        wl.method,
        wl.event_type,
        wl.status_code,
        wl.response_message,
        wl.duration_ms,
        wl.error,
        wl.received_at,
        wl.processed_at,
        wl.payload
    FROM webhook_logs wl
    WHERE wl.client_user_id = p_user_id
    ORDER BY wl.received_at DESC
    LIMIT p_limit;
END;
$$;

-- Fonction pour récupérer tous les webhooks (admin)
CREATE OR REPLACE FUNCTION get_all_webhook_logs(
    p_limit INT DEFAULT 100
)
RETURNS TABLE (
    id UUID,
    endpoint TEXT,
    method TEXT,
    event_type TEXT,
    client_user_id UUID,
    status_code INT,
    response_message TEXT,
    duration_ms INT,
    error TEXT,
    received_at TIMESTAMPTZ,
    processed_at TIMESTAMPTZ,
    payload JSONB
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        wl.id,
        wl.endpoint,
        wl.method,
        wl.event_type,
        wl.client_user_id,
        wl.status_code,
        wl.response_message,
        wl.duration_ms,
        wl.error,
        wl.received_at,
        wl.processed_at,
        wl.payload
    FROM webhook_logs wl
    ORDER BY wl.received_at DESC
    LIMIT p_limit;
END;
$$;

-- Commentaires
COMMENT ON TABLE webhook_logs IS 'Logs des webhooks reçus par le backend (Vital, etc.)';
COMMENT ON COLUMN webhook_logs.endpoint IS 'Endpoint qui a reçu le webhook';
COMMENT ON COLUMN webhook_logs.event_type IS 'Type d''événement du webhook (ex: historical.data.water.created)';
COMMENT ON COLUMN webhook_logs.client_user_id IS 'UUID utilisateur Supabase lié au webhook';
COMMENT ON COLUMN webhook_logs.duration_ms IS 'Durée de traitement du webhook en millisecondes';
COMMENT ON COLUMN webhook_logs.payload IS 'Payload JSON complet du webhook';
