-- ============================================
-- MIGRATION 004 : Table pour stocker les webhooks bruts
-- ============================================
-- Cette table permet de découpler la réception des webhooks de leur traitement

-- Table pour stocker les webhooks bruts en attente de traitement
CREATE TABLE IF NOT EXISTS webhook_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    open_wearables_user_id TEXT NOT NULL, -- ID utilisateur Open Wearables
    payload JSONB NOT NULL, -- Payload brut du webhook
    signature TEXT, -- Signature du webhook (si fournie)
    status TEXT DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    error_message TEXT, -- Message d'erreur si échec
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour les requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_webhook_events_status ON webhook_events(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_webhook_events_user ON webhook_events(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_webhook_events_pending ON webhook_events(status) WHERE status = 'pending';

-- RLS pour webhook_events
ALTER TABLE webhook_events ENABLE ROW LEVEL SECURITY;

-- Policy : Service role peut tout faire
CREATE POLICY "Service role can manage webhook events" ON webhook_events
    FOR ALL USING (true) WITH CHECK (true);

-- Policy : Utilisateurs peuvent voir leurs propres événements
CREATE POLICY "Users can view own webhook events" ON webhook_events
    FOR SELECT USING (auth.uid() = user_id);

COMMENT ON TABLE webhook_events IS 
    'Stocke les webhooks bruts en attente de traitement. Permet le découplage entre réception et normalisation.';

COMMENT ON COLUMN webhook_events.status IS 
    'pending: en attente de traitement, processing: en cours, completed: traité avec succès, failed: échec';
