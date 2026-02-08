#!/usr/bin/env python3
"""
Test de la migration des tokens Oura vers Supabase
==================================================

Ce script vérifie que:
1. Les tokens peuvent être stockés dans Supabase
2. Les tokens peuvent être récupérés depuis Supabase
3. Tous les scripts utilisent bien Supabase pour les tokens

Usage:
    python test_oura_token_migration.py
"""

import os
import sys
from dotenv import load_dotenv
from supabase_client import SupabaseClient
from oura_token_utils import get_user_oura_token, update_user_oura_token

load_dotenv()

# Configuration
from user_config import get_test_user_uuid

TEST_USER_ID = get_test_user_uuid()
TEST_TOKEN = "IX6RMKRCMIJOVZMIB2IKVL2PWUQOCNNI"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ SUPABASE_URL et SUPABASE_SERVICE_KEY doivent être définis")
    sys.exit(1)


def test_get_token():
    """Test 1: Récupérer un token depuis Supabase"""
    print("\n" + "=" * 70)
    print("TEST 1: Récupération du token Oura depuis Supabase")
    print("=" * 70)
    
    supabase = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
    token = get_user_oura_token(supabase, TEST_USER_ID)
    
    if token:
        print(f"✅ Token récupéré: {token[:20]}...")
        return True
    else:
        print("❌ Aucun token trouvé")
        return False


def test_update_token():
    """Test 2: Mettre à jour un token dans Supabase"""
    print("\n" + "=" * 70)
    print("TEST 2: Mise à jour du token Oura dans Supabase")
    print("=" * 70)
    
    supabase = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
    success = update_user_oura_token(supabase, TEST_USER_ID, TEST_TOKEN)
    
    if success:
        print("✅ Token mis à jour avec succès")
        
        # Vérifier que le token a bien été mis à jour
        new_token = get_user_oura_token(supabase, TEST_USER_ID)
        if new_token == TEST_TOKEN:
            print("✅ Vérification: le token est bien stocké")
            return True
        else:
            print("❌ Erreur: le token récupéré ne correspond pas")
            return False
    else:
        print("❌ Échec de la mise à jour")
        return False


def test_external_identities_structure():
    """Test 3: Vérifier la structure de external_identities"""
    print("\n" + "=" * 70)
    print("TEST 3: Vérification de la structure external_identities")
    print("=" * 70)
    
    supabase = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        result = supabase.client.from_('external_identities') \
            .select('*') \
            .eq('supabase_user_id', TEST_USER_ID) \
            .eq('provider_system', 'oura') \
            .single() \
            .execute()
        
        if result.data:
            data = result.data
            print(f"✅ Entrée trouvée:")
            print(f"   - supabase_user_id: {data.get('supabase_user_id')}")
            print(f"   - provider_system: {data.get('provider_system')}")
            print(f"   - external_user_id: {data.get('external_user_id')}")
            print(f"   - is_active: {data.get('is_active')}")
            
            metadata = data.get('metadata', {})
            print(f"   - metadata keys: {list(metadata.keys())}")
            
            if 'access_token' in metadata:
                print(f"   - access_token: {metadata['access_token'][:20]}...")
                print("✅ Le token est bien stocké dans metadata.access_token")
                return True
            else:
                print("❌ Le token n'est pas dans metadata.access_token")
                return False
        else:
            print("❌ Aucune entrée trouvée")
            return False
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_scripts_compatibility():
    """Test 4: Vérifier que les scripts utilisent bien oura_token_utils"""
    print("\n" + "=" * 70)
    print("TEST 4: Vérification de la compatibilité des scripts")
    print("=" * 70)
    
    scripts_to_check = [
        "import_oura_data.py",
        "import_oura_data_full.py",
        "force_sync_oura_today.py",
        "test_oura_sync.py",
        "register_oura_user.py"
    ]
    
    all_ok = True
    
    for script in scripts_to_check:
        script_path = os.path.join(os.path.dirname(__file__), script)
        
        if not os.path.exists(script_path):
            print(f"⚠️  {script}: fichier non trouvé")
            continue
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Vérifier que le script utilise oura_token_utils ou register_oura_user
        uses_utils = 'oura_token_utils' in content or 'get_user_oura_token' in content
        uses_register = 'register_oura_user' in content
        has_hardcoded_token = 'IX6RMKRCMIJOVZMIB2IKVL2PWUQOCNNI' in content
        
        if uses_utils or uses_register:
            if has_hardcoded_token and script != "register_oura_user.py":
                print(f"⚠️  {script}: utilise oura_token_utils mais contient encore un token hardcodé")
                all_ok = False
            else:
                print(f"✅ {script}: utilise oura_token_utils")
        else:
            print(f"❌ {script}: n'utilise pas oura_token_utils")
            all_ok = False
    
    return all_ok


def main():
    """Fonction principale"""
    print("\n" + "=" * 70)
    print("🧪 TEST DE LA MIGRATION DES TOKENS OURA VERS SUPABASE")
    print("=" * 70)
    print(f"\nUser ID: {TEST_USER_ID}")
    print(f"Supabase URL: {SUPABASE_URL}")
    
    results = []
    
    # Test 1: Récupérer le token
    results.append(("Récupération du token", test_get_token()))
    
    # Test 2: Mettre à jour le token
    results.append(("Mise à jour du token", test_update_token()))
    
    # Test 3: Vérifier la structure
    results.append(("Structure external_identities", test_external_identities_structure()))
    
    # Test 4: Compatibilité des scripts
    results.append(("Compatibilité des scripts", test_scripts_compatibility()))
    
    # Résumé
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"Total: {passed} tests réussis, {failed} tests échoués")
    print("=" * 70)
    
    if failed == 0:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS !")
        print("✅ La migration des tokens Oura vers Supabase est terminée.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {failed} test(s) ont échoué.")
        print("Veuillez corriger les erreurs avant de continuer.")
        sys.exit(1)


if __name__ == "__main__":
    main()
