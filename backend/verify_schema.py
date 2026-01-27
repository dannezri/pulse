"""
Script pour vérifier que le schéma Supabase correspond à ce que le code attend

Ce script compare :
1. Les champs utilisés dans le code
2. Les types de données attendus
3. Les contraintes nécessaires
"""

import os
from dotenv import load_dotenv
from supabase import create_client
from typing import Dict, List, Optional
import json

load_dotenv()

def check_table_structure(client, table_name: str, expected_fields: Dict[str, str]) -> Dict:
    """
    Vérifie la structure d'une table
    expected_fields: {"field_name": "expected_type"}
    """
    print(f"\n{'='*60}")
    print(f"Vérification de la table: {table_name}")
    print(f"{'='*60}")
    
    try:
        # Essayer de récupérer les colonnes en faisant une requête SELECT limitée
        # Note: Supabase ne fournit pas directement les métadonnées de schéma via l'API
        # On va tester en insérant une donnée de test puis en la supprimant
        
        # Pour vérifier, on va essayer de faire une requête SELECT avec tous les champs
        response = client.table(table_name).select("*").limit(1).execute()
        
        if response.data:
            actual_fields = set(response.data[0].keys())
        else:
            # Si pas de données, on ne peut pas vérifier directement
            print(f"⚠️  Aucune donnée dans la table, impossible de vérifier la structure")
            print(f"   Champs attendus: {', '.join(expected_fields.keys())}")
            return {"status": "unknown", "message": "No data to verify"}
        
        expected_field_names = set(expected_fields.keys())
        missing_fields = expected_field_names - actual_fields
        extra_fields = actual_fields - expected_field_names
        
        if missing_fields:
            print(f"❌ Champs manquants: {', '.join(missing_fields)}")
        else:
            print(f"✅ Tous les champs attendus sont présents")
        
        if extra_fields:
            print(f"ℹ️  Champs supplémentaires (non utilisés par le code): {', '.join(extra_fields)}")
        
        print(f"\nChamps trouvés: {', '.join(sorted(actual_fields))}")
        
        return {
            "status": "ok" if not missing_fields else "error",
            "missing": list(missing_fields),
            "extra": list(extra_fields),
            "found": list(actual_fields)
        }
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return {"status": "error", "message": str(e)}


def test_biometrics_insert(client) -> bool:
    """Teste l'insertion dans la table biometrics"""
    print(f"\n{'='*60}")
    print("Test d'insertion dans biometrics")
    print(f"{'='*60}")
    
    try:
        # Créer un enregistrement de test
        test_data = {
            "user_id": "00000000-0000-0000-0000-000000000000",  # UUID de test
            "metric_type": "test_metric",
            "value": 100.0,
            "recorded_at": "2024-01-01T00:00:00Z",
            "raw_data": {"test": True},
            "source": "test"
        }
        
        response = client.table("biometrics").insert(test_data).execute()
        
        if response.data:
            print("✅ Insertion réussie")
            # Nettoyer - supprimer l'enregistrement de test
            test_id = response.data[0].get("id")
            if test_id:
                try:
                    client.table("biometrics").delete().eq("id", test_id).execute()
                    print("✅ Nettoyage réussi")
                except:
                    pass
            return True
        else:
            print("❌ Insertion échouée - pas de données retournées")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'insertion: {e}")
        error_str = str(e)
        
        # Analyser l'erreur pour donner des conseils
        if "column" in error_str.lower() and "does not exist" in error_str.lower():
            print("\n💡 Suggestion: Vérifiez que tous les champs existent dans la table")
        elif "null value" in error_str.lower() or "not null" in error_str.lower():
            print("\n💡 Suggestion: Vérifiez les contraintes NOT NULL")
        elif "foreign key" in error_str.lower():
            print("\n💡 Suggestion: Vérifiez que l'utilisateur existe dans la table profiles")
        
        return False


def test_health_profiles_insert(client) -> bool:
    """Teste l'insertion dans la table health_profiles"""
    print(f"\n{'='*60}")
    print("Test d'insertion dans health_profiles")
    print(f"{'='*60}")
    
    try:
        test_data = {
            "user_id": "00000000-0000-0000-0000-000000000000",
            "profile_data": {"test": True, "timestamp": "2024-01-01T00:00:00Z"},
            "date": "2024-01-01"
        }
        
        response = client.table("health_profiles").upsert(test_data).execute()
        
        if response.data:
            print("✅ Upsert réussi")
            # Nettoyer
            try:
                client.table("health_profiles").delete().eq("user_id", test_data["user_id"]).eq("date", test_data["date"]).execute()
                print("✅ Nettoyage réussi")
            except:
                pass
            return True
        else:
            print("❌ Upsert échoué")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'upsert: {e}")
        return False


def test_profiles_query(client) -> bool:
    """Teste la requête sur la table profiles"""
    print(f"\n{'='*60}")
    print("Test de requête sur profiles")
    print(f"{'='*60}")
    
    try:
        # Tester la requête avec open_wearables_user_id
        response = client.table("profiles").select("id, open_wearables_user_id, health_goal, baseline_hrv, baseline_resting_hr").limit(1).execute()
        
        print("✅ Requête réussie")
        print(f"   Champs disponibles: {', '.join(response.data[0].keys()) if response.data else 'Aucune donnée'}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la requête: {e}")
        error_str = str(e)
        
        if "column" in error_str.lower() and "does not exist" in error_str.lower():
            print("\n💡 Suggestion: Le champ open_wearables_user_id n'existe peut-être pas")
            print("   Exécutez la migration SQL pour ajouter ce champ")
        
        return False


def generate_migration_sql() -> str:
    """Génère le SQL de migration pour corriger les problèmes"""
    sql = """
-- ============================================
-- MIGRATION : Correction du schéma Supabase
-- ============================================
-- À exécuter dans Supabase SQL Editor si des champs manquent

-- 1. Vérifier/Créer la table profiles avec tous les champs
DO $$ 
BEGIN
    -- Ajouter open_wearables_user_id s'il n'existe pas
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'profiles' AND column_name = 'open_wearables_user_id'
    ) THEN
        ALTER TABLE profiles ADD COLUMN open_wearables_user_id TEXT UNIQUE;
        CREATE INDEX IF NOT EXISTS idx_profiles_open_wearables_user_id ON profiles(open_wearables_user_id);
        RAISE NOTICE 'Colonne open_wearables_user_id ajoutée';
    END IF;
    
    -- Ajouter baseline_hrv s'il n'existe pas
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'profiles' AND column_name = 'baseline_hrv'
    ) THEN
        ALTER TABLE profiles ADD COLUMN baseline_hrv INTEGER;
        RAISE NOTICE 'Colonne baseline_hrv ajoutée';
    END IF;
    
    -- Ajouter baseline_resting_hr s'il n'existe pas
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'profiles' AND column_name = 'baseline_resting_hr'
    ) THEN
        ALTER TABLE profiles ADD COLUMN baseline_resting_hr INTEGER;
        RAISE NOTICE 'Colonne baseline_resting_hr ajoutée';
    END IF;
    
    -- Ajouter health_goal s'il n'existe pas
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'profiles' AND column_name = 'health_goal'
    ) THEN
        ALTER TABLE profiles ADD COLUMN health_goal TEXT DEFAULT 'energy';
        RAISE NOTICE 'Colonne health_goal ajoutée';
    END IF;
END $$;

-- 2. Vérifier la table biometrics
DO $$ 
BEGIN
    -- Vérifier que raw_data est de type JSONB
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'biometrics' 
        AND column_name = 'raw_data' 
        AND data_type != 'jsonb'
    ) THEN
        ALTER TABLE biometrics ALTER COLUMN raw_data TYPE JSONB USING raw_data::jsonb;
        RAISE NOTICE 'Colonne raw_data convertie en JSONB';
    END IF;
END $$;

-- 3. Vérifier la table health_profiles
DO $$ 
BEGIN
    -- Vérifier que profile_data est de type JSONB
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'health_profiles' 
        AND column_name = 'profile_data' 
        AND data_type != 'jsonb'
    ) THEN
        ALTER TABLE health_profiles ALTER COLUMN profile_data TYPE JSONB USING profile_data::jsonb;
        RAISE NOTICE 'Colonne profile_data convertie en JSONB';
    END IF;
    
    -- Ajouter la contrainte UNIQUE si elle n'existe pas
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'health_profiles_user_id_date_key'
    ) THEN
        ALTER TABLE health_profiles ADD CONSTRAINT health_profiles_user_id_date_key UNIQUE (user_id, date);
        RAISE NOTICE 'Contrainte UNIQUE ajoutée sur (user_id, date)';
    END IF;
END $$;

-- 4. Vérifier les index
CREATE INDEX IF NOT EXISTS idx_biometrics_user_date ON biometrics(user_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_biometrics_user_type ON biometrics(user_id, metric_type, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_health_profiles_user_date ON health_profiles(user_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_profiles_open_wearables_user_id ON profiles(open_wearables_user_id);

-- 5. Vérifier les politiques RLS pour le service role
-- (Ces politiques permettent au service role d'insérer des données)
DO $$ 
BEGIN
    -- Policy pour biometrics
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'biometrics' 
        AND policyname = 'Service role can insert biometrics'
    ) THEN
        CREATE POLICY "Service role can insert biometrics" ON biometrics
            FOR INSERT WITH CHECK (true);
        RAISE NOTICE 'Policy RLS ajoutée pour biometrics';
    END IF;
    
    -- Policy pour health_profiles
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'health_profiles' 
        AND policyname = 'Service role can insert health profiles'
    ) THEN
        CREATE POLICY "Service role can insert health profiles" ON health_profiles
            FOR INSERT WITH CHECK (true);
        RAISE NOTICE 'Policy RLS ajoutée pour health_profiles';
    END IF;
END $$;
"""
    return sql


def main():
    print("="*60)
    print("VÉRIFICATION DU SCHÉMA SUPABASE")
    print("="*60)
    
    # Charger les variables d'environnement
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Variables d'environnement manquantes")
        print("   Assurez-vous d'avoir SUPABASE_URL et SUPABASE_SERVICE_KEY dans votre .env")
        return
    
    try:
        client = create_client(supabase_url, supabase_key)
        print("✅ Connexion à Supabase réussie\n")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return
    
    # Définir les champs attendus pour chaque table
    expected_fields = {
        "profiles": {
            "id": "UUID",
            "open_wearables_user_id": "TEXT",
            "health_goal": "TEXT",
            "baseline_hrv": "INTEGER",
            "baseline_resting_hr": "INTEGER"
        },
        "biometrics": {
            "user_id": "UUID",
            "metric_type": "TEXT",
            "value": "FLOAT",
            "recorded_at": "TIMESTAMP",
            "raw_data": "JSONB",
            "source": "TEXT"
        },
        "health_profiles": {
            "user_id": "UUID",
            "profile_data": "JSONB",
            "date": "DATE"
        }
    }
    
    results = {}
    
    # Vérifier chaque table
    for table_name, fields in expected_fields.items():
        results[table_name] = check_table_structure(client, table_name, fields)
    
    # Tests fonctionnels
    print("\n" + "="*60)
    print("TESTS FONCTIONNELS")
    print("="*60)
    
    test_results = {
        "profiles_query": test_profiles_query(client),
        "biometrics_insert": test_biometrics_insert(client),
        "health_profiles_insert": test_health_profiles_insert(client)
    }
    
    # Résumé
    print("\n" + "="*60)
    print("RÉSUMÉ")
    print("="*60)
    
    all_ok = True
    for table, result in results.items():
        if result.get("status") == "error" or result.get("missing"):
            all_ok = False
            print(f"❌ {table}: Problèmes détectés")
        else:
            print(f"✅ {table}: OK")
    
    for test_name, result in test_results.items():
        if not result:
            all_ok = False
            print(f"❌ {test_name}: Échec")
        else:
            print(f"✅ {test_name}: OK")
    
    if not all_ok:
        print("\n" + "="*60)
        print("SQL DE MIGRATION GÉNÉRÉ")
        print("="*60)
        print("\nExécutez ce SQL dans Supabase SQL Editor pour corriger les problèmes:\n")
        print(generate_migration_sql())
        
        # Sauvegarder dans un fichier
        with open("migration_fix.sql", "w") as f:
            f.write(generate_migration_sql())
        print("\n✅ SQL sauvegardé dans migration_fix.sql")
    else:
        print("\n✅ Tous les tests sont passés ! Le schéma est correct.")


if __name__ == "__main__":
    main()
