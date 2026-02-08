#!/usr/bin/env python3
"""
Test du client Gemini avec mode thinking
Vérifie que la configuration est correcte et que le modèle fonctionne
"""

import os
import sys
import json
from datetime import date

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gemini_client import GeminiThinkingClient
from supabase_client import SupabaseClient
from explain_service import EnergyExplainService


def test_gemini_client():
    """Test 1: Vérifier que le client Gemini s'initialise correctement"""
    print("\n" + "="*60)
    print("TEST 1: Initialisation du client Gemini")
    print("="*60)
    
    try:
        client = GeminiThinkingClient()
        print("✅ Client Gemini initialisé avec succès")
        print(f"   Modèle: {client.model_name}")
        return client
    except ValueError as e:
        print(f"❌ Erreur de configuration: {e}")
        print("\n💡 Solution:")
        print("   export GOOGLE_API_KEY='votre-clé-api'")
        print("   ou ajouter dans .env: GOOGLE_API_KEY=votre-clé-api")
        return None
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return None


def test_simple_generation(client):
    """Test 2: Génération simple pour vérifier que l'API fonctionne"""
    print("\n" + "="*60)
    print("TEST 2: Génération simple")
    print("="*60)
    
    if not client:
        print("⏭️  Test ignoré (client non initialisé)")
        return False
    
    try:
        prompt = """
Génère 2 cartes d'explication pour un score d'énergie de 45%.

Données:
- HRV: 25ms (baseline: 50ms)
- RHR: 65bpm (baseline: 60bpm)
- Sommeil: 5h30 (besoin: 8h)

Réponds au format JSON avec cette structure:
{
  "cards": [
    {
      "type": "nervous",
      "title": "Titre court",
      "text": "Explication détaillée",
      "analogy": "Analogie simple",
      "metrics": {
        "primary": {"label": "HRV actuel", "value": 25, "unit": "ms"}
      }
    }
  ]
}
"""
        
        system_prompt = """Tu es un expert en wellness. Génère des explications claires et empathiques.
Réponds UNIQUEMENT au format JSON strict."""
        
        print("🧠 Appel à Gemini en cours...")
        result = client.generate_cards_explanation(
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        print("✅ Génération réussie!")
        print(f"   Nombre de cartes: {len(result.get('cards', []))}")
        
        if result.get('_thinking'):
            thinking = result['_thinking']
            print(f"   Raisonnement (premiers 200 chars): {thinking[:200]}...")
        
        # Afficher les cartes générées
        print("\n📋 Cartes générées:")
        for i, card in enumerate(result.get('cards', []), 1):
            print(f"\n   Carte {i}:")
            print(f"   - Type: {card.get('type')}")
            print(f"   - Titre: {card.get('title')}")
            print(f"   - Analogie: {card.get('analogy', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_explain_service():
    """Test 3: Test du service complet (optionnel, nécessite un user_id valide)"""
    print("\n" + "="*60)
    print("TEST 3: Service d'explication complet (optionnel)")
    print("="*60)
    
    # Vérifier les variables d'environnement nécessaires
    required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_KEY", "GOOGLE_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⏭️  Test ignoré (variables manquantes: {', '.join(missing_vars)})")
        return None
    
    test_user_id = os.getenv("TEST_USER_ID")
    if not test_user_id:
        print("⏭️  Test ignoré (TEST_USER_ID non défini)")
        print("   Pour tester avec un vrai user: export TEST_USER_ID='votre-user-id'")
        return None
    
    try:
        # Initialiser les clients
        supabase_client = SupabaseClient(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
        )
        gemini_client = GeminiThinkingClient()
        
        # Initialiser le service
        explain_service = EnergyExplainService(
            supabase_client=supabase_client,
            gemini_client=gemini_client
        )
        
        print(f"🧪 Test avec user_id: {test_user_id}")
        print("🧠 Génération de l'explication...")
        
        # Générer l'explication
        import asyncio
        explanation = asyncio.run(
            explain_service.generate_explanation(
                user_id=test_user_id,
                target_date=date.today()
            )
        )
        
        print("✅ Explication générée avec succès!")
        print(f"   Score d'énergie: {explanation.get('energyScore')}%")
        print(f"   Confiance: {explanation.get('confidence')}%")
        print(f"   Label: {explanation.get('label')}")
        print(f"   Nombre de cartes: {len(explanation.get('cards', []))}")
        
        # Afficher les cartes
        print("\n📋 Cartes générées:")
        for i, card in enumerate(explanation.get('cards', []), 1):
            print(f"\n   Carte {i}:")
            print(f"   - Type: {card.get('type')}")
            print(f"   - Titre: {card.get('title')}")
            print(f"   - Texte: {card.get('text', '')[:100]}...")
            print(f"   - Analogie: {card.get('analogy', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test du service: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Exécuter tous les tests"""
    print("\n" + "="*60)
    print("🧠 TEST SUITE GEMINI THINKING MODE")
    print("="*60)
    
    results = {
        "client_init": False,
        "simple_generation": False,
        "explain_service": None  # None = non testé
    }
    
    # Test 1: Initialisation
    client = test_gemini_client()
    results["client_init"] = client is not None
    
    # Test 2: Génération simple
    if client:
        results["simple_generation"] = test_simple_generation(client)
    
    # Test 3: Service complet (optionnel)
    results["explain_service"] = test_explain_service()
    
    # Résumé
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*60)
    
    print(f"\n✅ Initialisation client: {'PASS' if results['client_init'] else 'FAIL'}")
    print(f"✅ Génération simple: {'PASS' if results['simple_generation'] else 'FAIL'}")
    
    if results['explain_service'] is None:
        print(f"⏭️  Service complet: SKIPPED")
    else:
        print(f"✅ Service complet: {'PASS' if results['explain_service'] else 'FAIL'}")
    
    # Déterminer le statut global
    critical_tests = [results["client_init"], results["simple_generation"]]
    all_critical_pass = all(critical_tests)
    
    print("\n" + "="*60)
    if all_critical_pass:
        print("🎉 TOUS LES TESTS CRITIQUES SONT PASSÉS!")
        print("="*60)
        print("\n✅ Gemini Thinking mode est prêt à être utilisé")
        print("\n📝 Prochaines étapes:")
        print("   1. Démarrer le backend: python api_server.py")
        print("   2. Tester l'endpoint: GET /api/energy/explain/{user_id}")
        print("   3. Vérifier dans l'app mobile (onglet Énergie)")
        return 0
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("="*60)
        print("\n💡 Vérifiez:")
        print("   - GOOGLE_API_KEY est définie")
        print("   - google-generativeai est installé (pip install -r requirements.txt)")
        print("   - Votre clé API est valide")
        print("\n📖 Documentation: GEMINI_THINKING_MIGRATION.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())
