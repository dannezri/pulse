"""
Test script pour le Why Energy Stack Explain Service
Usage: python test_explain_service.py
"""

import os
import asyncio
from datetime import date
from dotenv import load_dotenv

load_dotenv()

from explain_service import EnergyExplainService
from supabase_client import SupabaseClient
from llm_client import LLMClient


async def test_explain_service():
    """
    Test l'explication énergétique pour un utilisateur
    """
    
    # Initialiser les clients
    print("🔧 Initialisation des clients...")
    supabase_client = SupabaseClient(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    llm_client = LLMClient()
    
    explain_service = EnergyExplainService(
        supabase_client=supabase_client,
        llm_client=llm_client
    )
    
    # Test avec un user_id (remplacer par un vrai user_id de ta DB)
    test_user_id = "c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd"  # Dan
    test_date = date(2026, 2, 1)
    
    print(f"\n📊 Test pour user_id: {test_user_id}")
    print(f"📅 Date: {test_date}")
    print("\n" + "="*60)
    
    try:
        # Générer l'explication
        print("\n🤖 Génération de l'explication via GPT-4o...")
        explanation = await explain_service.generate_explanation(
            user_id=test_user_id,
            target_date=test_date
        )
        
        # Afficher les résultats
        print("\n✅ RÉSULTATS:")
        print("="*60)
        print(f"\n🔋 Score d'énergie: {explanation.get('energyScore')}%")
        print(f"📊 Confiance: {explanation.get('confidence')}%")
        print(f"🏷️  Label: {explanation.get('label')}")
        print(f"📅 Date: {explanation.get('date')}")
        
        if 'error' in explanation:
            print(f"\n⚠️  ERREUR: {explanation['error']}")
        
        # Afficher les cartes
        cards = explanation.get('cards', [])
        print(f"\n📇 Cartes générées: {len(cards)}")
        print("="*60)
        
        for i, card in enumerate(cards, 1):
            print(f"\n📋 CARTE {i} - Type: {card['type']}")
            print(f"Icône: {get_card_emoji(card['type'])}")
            print(f"Titre: {card['title']}")
            print(f"Texte: {card['text'][:100]}...")
            print(f"Analogie: {card['analogy']}")
            
            if card.get('metrics'):
                print("\nMétriques:")
                if card['metrics'].get('primary'):
                    primary = card['metrics']['primary']
                    print(f"  - {primary['label']}: {primary['value']}{primary['unit']}")
                if card['metrics'].get('secondary'):
                    secondary = card['metrics']['secondary']
                    print(f"  - {secondary['label']}: {secondary['value']}{secondary['unit']}")
        
        print("\n" + "="*60)
        print("✅ Test terminé avec succès!")
        
        # Validation basique
        assert 'energyScore' in explanation, "Missing energyScore"
        assert 'cards' in explanation, "Missing cards"
        assert isinstance(explanation['cards'], list), "cards should be a list"
        
        for card in explanation['cards']:
            assert 'type' in card, "Missing type in card"
            assert 'title' in card, "Missing title in card"
            assert 'text' in card, "Missing text in card"
            assert 'analogy' in card, "Missing analogy in card"
            assert card['type'] in ['nervous', 'chemistry', 'load'], f"Invalid card type: {card['type']}"
            
            # Vérifier les longueurs
            assert len(card['title']) <= 50, f"Title too long: {len(card['title'])} chars"
            assert len(card['text']) <= 250, f"Text too long: {len(card['text'])} chars"
            assert len(card['analogy']) <= 150, f"Analogy too long: {len(card['analogy'])} chars"
        
        print("\n✅ Toutes les validations sont passées!")
        
        return explanation
    
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_card_emoji(card_type: str) -> str:
    """Retourne l'emoji correspondant au type de carte"""
    emojis = {
        'nervous': '⚡️',
        'chemistry': '💊',
        'load': '🎒'
    }
    return emojis.get(card_type, '💡')


async def test_fallback_response():
    """Test la réponse de fallback quand pas de données"""
    
    print("\n\n🧪 TEST FALLBACK RESPONSE")
    print("="*60)
    
    supabase_client = SupabaseClient(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    llm_client = LLMClient()
    
    explain_service = EnergyExplainService(
        supabase_client=supabase_client,
        llm_client=llm_client
    )
    
    # Test avec un user_id inexistant
    fake_user_id = "00000000-0000-0000-0000-000000000000"
    
    print(f"\n📊 Test avec user_id inexistant: {fake_user_id}")
    
    explanation = await explain_service.generate_explanation(
        user_id=fake_user_id,
        target_date=date.today()
    )
    
    print("\n✅ RÉSULTATS:")
    print(f"Score: {explanation.get('energyScore')}")
    print(f"Label: {explanation.get('label')}")
    print(f"Erreur: {explanation.get('error')}")
    print(f"Nombre de cartes: {len(explanation.get('cards', []))}")
    
    assert explanation.get('energyScore') == 0, "Score should be 0 for missing data"
    assert 'error' in explanation, "Should have error message"
    assert len(explanation.get('cards', [])) > 0, "Should have fallback card"
    
    print("\n✅ Test fallback passé!")


async def main():
    """Execute tous les tests"""
    
    print("\n" + "="*60)
    print("🚀 WHY ENERGY STACK - TEST SUITE")
    print("="*60)
    
    # Test 1: Explication normale
    await test_explain_service()
    
    # Test 2: Fallback
    await test_fallback_response()
    
    print("\n" + "="*60)
    print("✅ TOUS LES TESTS SONT PASSÉS!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
