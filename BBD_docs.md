Voici le schéma de base de données (SQL) optimisé pour Supabase. Ce design est pensé pour la performance : il permet de stocker des milliers de mesures par seconde tout en offrant à l'IA un accès rapide au contexte de l'utilisateur.

SQL
-- 1. PROFILES : Informations utilisateur et réglages
CREATE TABLE profiles (
    id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
    full_name TEXT,
    health_goal TEXT DEFAULT 'energy', -- 'energy', 'sleep', 'weight', 'focus'
    baseline_hrv INTEGER, -- Moyenne HRV habituelle
    baseline_resting_hr (INTEGER), -- Rythme cardiaque au repos habituel
    open_wearables_user_id TEXT UNIQUE, -- Identifiant unique du partenaire de données (Open Wearables)
    terra_user_id TEXT UNIQUE, -- Identifiant unique du partenaire de données (Terra/Vital) - DÉPRÉCIÉ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. BIOMETRICS : Stockage des données brutes des wearables
CREATE TABLE biometrics (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    metric_type TEXT NOT NULL, -- 'hr', 'hrv', 'sleep_score', 'steps', 'glucose'
    value FLOAT NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    raw_data JSONB, -- Stockage du JSON brut au cas où on aurait besoin d'analyser plus tard
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. MEALS : Journal alimentaire via IA Vision
CREATE TABLE meals (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    image_url TEXT,
    description TEXT, -- Analyse générée par l'IA
    estimated_calories INTEGER,
    glycemic_impact TEXT, -- 'low', 'medium', 'high'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. INSIGHTS : Les consignes envoyées par l'IA (Le cœur du produit)
CREATE TABLE insights (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    instruction_text TEXT NOT NULL,
    category TEXT, -- 'movement', 'nutrition', 'recovery', 'stress'
    priority INTEGER DEFAULT 1, -- 1: Normal, 2: Urgent
    is_read BOOLEAN DEFAULT FALSE,
    user_feedback TEXT, -- 'followed', 'ignored', 'irrelevant'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- INDEXES pour la rapidité des requêtes
CREATE INDEX idx_biometrics_user_date ON biometrics(user_id, recorded_at DESC);
CREATE INDEX idx_insights_user_unread ON insights(user_id) WHERE is_read = FALSE;
💡 Pourquoi ce schéma est efficace ?
Table biometrics : L'utilisation du type JSONB pour raw_data permet d'être "futur-proof". Si un nouveau capteur sort avec des données bizarres, tu ne casses pas ta base.

Table insights : Le champ user_feedback est crucial. C'est lui qui permettra à ton IA d'apprendre : si l'utilisateur ignore systématiquement les douches froides, l'IA finira par lui proposer autre chose pour réduire son stress.

Relation auth.users : En te liant au système d'authentification natif de Supabase, tu gères la sécurité des données de santé au niveau "Row Level Security" (RLS), ce qui est indispensable pour la confiance des utilisateurs.