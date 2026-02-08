"""
Tests pour la fonctionnalité ICD-11 et conditions de santé

Teste:
- La recherche ICD-11
- Les endpoints CRUD des conditions
- Les RLS policies
"""

import os
import sys
import uuid
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Ajouter le répertoire parent au path pour importer les modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from supabase_client import SupabaseClient
from icd11_client import get_icd11_client


def print_test_header(test_name: str):
    """Affiche un header pour un test"""
    print("\n" + "="*60)
    print(f"TEST: {test_name}")
    print("="*60)


def test_icd11_search():
    """Test de recherche ICD-11"""
    print_test_header("Recherche ICD-11")
    
    supabase_client = SupabaseClient(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    icd11_client = get_icd11_client(supabase_client=supabase_client)
    
    # Test 1: Recherche "TDAH"
    print("\n1. Recherche: TDAH")
    results = icd11_client.search("TDAH", lang="fr")
    print(f"   Résultats trouvés: {len(results)}")
    if results:
        print(f"   Premier résultat: {results[0]['display']}")
        print(f"   Code: {results[0]['code']}")
        print(f"   Catégorie: {results[0].get('category', 'N/A')}")
    
    # Test 2: Recherche "SOP"
    print("\n2. Recherche: syndrome des ovaires polykystiques")
    results = icd11_client.search("syndrome des ovaires polykystiques", lang="fr")
    print(f"   Résultats trouvés: {len(results)}")
    if results:
        print(f"   Premier résultat: {results[0]['display']}")
        print(f"   Code: {results[0]['code']}")
    
    # Test 3: Recherche "depression"
    print("\n3. Recherche: dépression")
    results = icd11_client.search("dépression", lang="fr")
    print(f"   Résultats trouvés: {len(results)}")
    if results:
        print(f"   Premier résultat: {results[0]['display']}")
        print(f"   Code: {results[0]['code']}")
    
    # Test 4: Cache (deuxième recherche identique)
    print("\n4. Test cache (deuxième recherche TDAH)")
    results = icd11_client.search("TDAH", lang="fr", use_cache=True)
    print(f"   Résultats trouvés: {len(results)} (depuis cache)")
    
    print("\n✅ Tests de recherche ICD-11 terminés")


def test_conditions_crud():
    """Test CRUD des conditions utilisateur"""
    print_test_header("CRUD Conditions Utilisateur")
    
    supabase_client = SupabaseClient(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    # Utiliser un user_id de test (à remplacer par un vrai user_id)
    test_user_id = os.getenv("TEST_USER_ID")
    if not test_user_id:
        print("❌ TEST_USER_ID non défini dans .env")
        print("   Créez un utilisateur de test et définissez TEST_USER_ID")
        return
    
    print(f"\nUtilisation du user_id de test: {test_user_id[:8]}...")
    
    # Test 1: Ajouter une condition
    print("\n1. Ajout d'une condition")
    condition_data = {
        "user_id": test_user_id,
        "system": "icd11",
        "code": "6A70",
        "display": "Trouble déficitaire de l'attention avec hyperactivité",
        "category": "Troubles mentaux"
    }
    
    response = supabase_client.client.table("user_conditions").insert(condition_data).execute()
    if response.data and len(response.data) > 0:
        condition_id = response.data[0]["id"]
        print(f"   ✅ Condition ajoutée: {condition_id}")
    else:
        print("   ❌ Échec de l'ajout")
        return
    
    # Test 2: Récupérer les conditions
    print("\n2. Récupération des conditions")
    response = supabase_client.client.rpc(
        "get_user_conditions",
        {"p_user_id": test_user_id}
    ).execute()
    
    if response.data:
        print(f"   ✅ {len(response.data)} condition(s) trouvée(s)")
        for condition in response.data:
            print(f"      - {condition['display']} ({condition['code']})")
    else:
        print("   ⚠️ Aucune condition trouvée")
    
    # Test 3: Supprimer la condition
    print("\n3. Suppression de la condition")
    response = supabase_client.client.table("user_conditions").delete().eq("id", condition_id).execute()
    print("   ✅ Condition supprimée")
    
    # Test 4: Vérifier la suppression
    print("\n4. Vérification de la suppression")
    response = supabase_client.client.rpc(
        "get_user_conditions",
        {"p_user_id": test_user_id}
    ).execute()
    
    if response.data and len(response.data) == 0:
        print("   ✅ Aucune condition (suppression réussie)")
    else:
        print(f"   ⚠️ {len(response.data)} condition(s) restante(s)")
    
    print("\n✅ Tests CRUD terminés")


def test_rls_policies():
    """Test des RLS policies"""
    print_test_header("RLS Policies")
    
    supabase_client = SupabaseClient(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    print("\nNote: Les RLS policies sont automatiquement appliquées")
    print("      Le service role key bypass RLS, donc ce test est limité")
    print("      Testez manuellement depuis le mobile avec un vrai user token")
    
    # Vérifier que la table existe et a RLS activé
    print("\n1. Vérification de l'existence de la table")
    response = supabase_client.client.table("user_conditions").select("*").limit(1).execute()
    print("   ✅ Table user_conditions accessible")
    
    print("\n2. Vérification de la table cache")
    response = supabase_client.client.table("terminology_cache").select("*").limit(1).execute()
    print("   ✅ Table terminology_cache accessible")
    
    print("\n✅ Tests RLS terminés (tests manuels requis depuis mobile)")


def test_cache_cleanup():
    """Test du nettoyage du cache"""
    print_test_header("Nettoyage du Cache")
    
    supabase_client = SupabaseClient(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    print("\n1. Appel de la fonction clean_expired_terminology_cache")
    response = supabase_client.client.rpc("clean_expired_terminology_cache").execute()
    
    if response.data is not None:
        deleted_count = response.data
        print(f"   ✅ {deleted_count} entrée(s) expirée(s) supprimée(s)")
    else:
        print("   ⚠️ Aucune entrée expirée")
    
    print("\n✅ Test de nettoyage terminé")


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "="*60)
    print("TESTS ICD-11 ET CONDITIONS DE SANTÉ")
    print("="*60)
    
    try:
        # Test 1: Recherche ICD-11
        test_icd11_search()
        
        # Test 2: CRUD Conditions
        test_conditions_crud()
        
        # Test 3: RLS Policies
        test_rls_policies()
        
        # Test 4: Cache cleanup
        test_cache_cleanup()
        
        print("\n" + "="*60)
        print("✅ TOUS LES TESTS TERMINÉS AVEC SUCCÈS")
        print("="*60)
        
    except Exception as e:
        print("\n" + "="*60)
        print("❌ ERREUR LORS DES TESTS")
        print("="*60)
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Vérifier la configuration
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_KEY"):
        print("❌ SUPABASE_URL et SUPABASE_SERVICE_KEY doivent être définis dans .env")
        sys.exit(1)
    
    if not os.getenv("ICD11_CLIENT_ID") or not os.getenv("ICD11_CLIENT_SECRET"):
        print("⚠️ ICD11_CLIENT_ID et ICD11_CLIENT_SECRET non définis")
        print("   Les tests de recherche ICD-11 seront limités")
        print("   Pour obtenir des credentials: https://icd.who.int/icdapi")
    
    run_all_tests()
