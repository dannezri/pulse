-- ============================================
-- SCHEMA SUPABASE : Bio-Feedback IA MVP
-- ============================================

-- 1. PROFILES : Informations utilisateur et réglages
CREATE TABLE IF NOT EXISTS profiles (
    id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
    full_name TEXT,
    health_goal TEXT DEFAULT 'energy', -- 'energy', 'sleep', 'weight', 'focus'
    baseline_hrv INTEGER, -- Moyenne HRV habituelle
    baseline_resting_hr INTEGER, -- Rythme cardiaque au repos habituel
    open_wearables_user_id TEXT UNIQUE, -- Identifiant unique du partenaire de données (Open Wearables)
    terra_user_id TEXT UNIQUE, -- Identifiant unique du partenaire de données (Terra/Vital) - DÉPRÉCIÉ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. BIOMETRICS : Stockage des données brutes des wearables
CREATE TABLE IF NOT EXISTS biometrics (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    metric_type TEXT NOT NULL, -- 'hr', 'hrv', 'sleep_score', 'steps', 'glucose', 'sleep_duration', 'sleep_quality'
    value FLOAT NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    raw_data JSONB, -- Stockage du JSON brut au cas où on aurait besoin d'analyser plus tard
    source TEXT, -- 'apple_health', 'garmin', 'oura', 'open_wearables', 'terra' (déprécié)
    source_event_id TEXT, -- ID unique de l'événement depuis la source (webhook/provider) pour idempotence
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. MEALS : Journal alimentaire via IA Vision
CREATE TABLE IF NOT EXISTS meals (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    image_url TEXT,
    description TEXT, -- Analyse générée par l'IA
    estimated_calories INTEGER,
    glycemic_impact TEXT, -- 'low', 'medium', 'high'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. INSIGHTS : Les consignes envoyées par l'IA (Le cœur du produit)
CREATE TABLE IF NOT EXISTS insights (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    instruction_text TEXT NOT NULL,
    category TEXT, -- 'movement', 'nutrition', 'recovery', 'stress'
    priority INTEGER DEFAULT 1, -- 1: Normal, 2: Urgent
    is_read BOOLEAN DEFAULT FALSE,
    user_feedback TEXT, -- 'followed', 'ignored', 'irrelevant'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. HEALTH_PROFILES : Profils de santé normalisés (cache pour l'IA)
CREATE TABLE IF NOT EXISTS health_profiles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    profile_data JSONB NOT NULL, -- Le "Profil de Santé JSON" normalisé
    date DATE NOT NULL, -- Date du profil (un par jour)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- ============================================
-- INDEXES pour la rapidité des requêtes
-- ============================================

CREATE INDEX IF NOT EXISTS idx_biometrics_user_date ON biometrics(user_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_biometrics_user_type ON biometrics(user_id, metric_type, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_biometrics_source_event_id ON biometrics(source_event_id) WHERE source_event_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS biometrics_user_source_event_unique ON biometrics(user_id, source, source_event_id) WHERE source_event_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_insights_user_unread ON insights(user_id) WHERE is_read = FALSE;
CREATE INDEX IF NOT EXISTS idx_health_profiles_user_date ON health_profiles(user_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_meals_user_date ON meals(user_id, created_at DESC);

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

-- Activer RLS sur toutes les tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE biometrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE meals ENABLE ROW LEVEL SECURITY;
ALTER TABLE insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_profiles ENABLE ROW LEVEL SECURITY;

-- Policies : Les utilisateurs ne peuvent voir que leurs propres données
CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can view own biometrics" ON biometrics
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service role can insert biometrics" ON biometrics
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can view own meals" ON meals
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own meals" ON meals
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own insights" ON insights
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own insights" ON insights
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own health profiles" ON health_profiles
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service role can insert health profiles" ON health_profiles
    FOR INSERT WITH CHECK (true);

-- ============================================
-- FUNCTIONS UTILES
-- ============================================

-- Fonction pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger pour profiles
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
