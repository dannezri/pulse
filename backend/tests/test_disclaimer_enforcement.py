"""
Test d'intégration pour l'enforcement du disclaimer médical infection-like

Ces tests vérifient que le disclaimer est TOUJOURS injecté quand nécessaire,
indépendamment de ce que le LLM génère.

Criticité: HAUTE (médico-légal)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai_service import AIAnalysisService
from supabase_client import get_supabase_client
import logging
from datetime import date, datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_disclaimer_enforcement_high_score():
    """
    Test: Score infection > 0.6 doit déclencher disclaimer HIGH
    """
    logger.info("\n=== TEST: Disclaimer HIGH (score > 0.6) ===")
    
    # Setup
    supabase = get_supabase_client()
    ai_service = AIAnalysisService(supabase)
    
    # Mock user_id (remplacer par un vrai user_id en test)
    user_id = "test-user-id-placeholder"
    
    # Mock brief data avec une carte infection
    mock_brief = {
        "pulseScore": 65,
        "cards": [
            {
                "id": "vigilance_sante",
                "type": "focus",
                "title": "Vigilance santé",
                "content": "Votre **signature physiologique** montre des marqueurs inhabituels. RHR élevé de +8 bpm, HRV supprimé de -15 ms. Pattern persistent depuis 2 jours.",
                "state": "alert",
                "iconName": "AlertTriangle",
                "priority": 95
            }
        ]
    }
    
    # Mock infection_like state avec score > 0.6
    today = date.today()
    try:
        supabase.client.table("daily_state").upsert({
            "user_id": user_id,
            "state_date": today.isoformat(),
            "infection_like": {
                "smoothed_score": 0.75,
                "confidence": 0.82,
                "persistent": True,
                "signals_triggered": 3
            }
        }).execute()
        logger.info(f"✅ Mocked infection state with score 0.75")
    except Exception as e:
        logger.error(f"❌ Failed to mock state: {e}")
        return False
    
    # Execute enforcement
    enforced_brief = ai_service._enforce_infection_disclaimer(user_id, mock_brief)
    
    # Verify
    enforced_card = enforced_brief['cards'][0]
    disclaimer_present = "ceci n'est pas un diagnostic médical" in enforced_card['content'].lower()
    high_severity = "immédiatement" in enforced_card['content'].lower()
    
    if disclaimer_present and high_severity:
        logger.info("✅ PASS: Disclaimer HIGH correctement injecté")
        logger.info(f"   Content length: {len(enforced_card['content'])} chars")
        return True
    else:
        logger.error("❌ FAIL: Disclaimer manquant ou incorrect")
        logger.error(f"   Disclaimer present: {disclaimer_present}")
        logger.error(f"   High severity: {high_severity}")
        return False


def test_disclaimer_enforcement_moderate_score():
    """
    Test: Score infection 0.3-0.6 doit déclencher disclaimer MODERATE
    """
    logger.info("\n=== TEST: Disclaimer MODERATE (0.3 < score < 0.6) ===")
    
    supabase = get_supabase_client()
    ai_service = AIAnalysisService(supabase)
    user_id = "test-user-id-placeholder"
    
    mock_brief = {
        "pulseScore": 72,
        "cards": [
            {
                "id": "pattern_inhabituel",
                "type": "focus",
                "title": "Pattern inhabituel détecté",
                "content": "Vos métriques montrent une signature légèrement atypique. HRV en baisse, RHR stable.",
                "state": "warning",
                "iconName": "TrendingDown",
                "priority": 80
            }
        ]
    }
    
    # Mock infection state avec score moderate
    today = date.today()
    try:
        supabase.client.table("daily_state").upsert({
            "user_id": user_id,
            "state_date": today.isoformat(),
            "infection_like": {
                "smoothed_score": 0.45,
                "confidence": 0.65,
                "persistent": False,
                "signals_triggered": 2
            }
        }).execute()
        logger.info(f"✅ Mocked infection state with score 0.45")
    except Exception as e:
        logger.error(f"❌ Failed to mock state: {e}")
        return False
    
    enforced_brief = ai_service._enforce_infection_disclaimer(user_id, mock_brief)
    
    enforced_card = enforced_brief['cards'][0]
    disclaimer_present = "ceci n'est pas un diagnostic médical" in enforced_card['content'].lower()
    moderate_severity = "immédiatement" not in enforced_card['content'].lower()
    
    if disclaimer_present and moderate_severity:
        logger.info("✅ PASS: Disclaimer MODERATE correctement injecté")
        return True
    else:
        logger.error("❌ FAIL: Disclaimer manquant ou incorrect")
        return False


def test_disclaimer_no_enforcement_low_score():
    """
    Test: Score infection < 0.3 NE doit PAS déclencher disclaimer
    """
    logger.info("\n=== TEST: No Disclaimer (score < 0.3) ===")
    
    supabase = get_supabase_client()
    ai_service = AIAnalysisService(supabase)
    user_id = "test-user-id-placeholder"
    
    mock_brief = {
        "pulseScore": 78,
        "cards": [
            {
                "id": "verdict",
                "type": "focus",
                "title": "Le bilan du coach",
                "content": "Votre récupération est bonne aujourd'hui. Continuez ainsi !",
                "state": "optimal",
                "iconName": "CheckCircle",
                "priority": 100
            }
        ]
    }
    
    # Mock infection state avec score < 0.3
    today = date.today()
    try:
        supabase.client.table("daily_state").upsert({
            "user_id": user_id,
            "state_date": today.isoformat(),
            "infection_like": {
                "smoothed_score": 0.15,
                "confidence": 0.45,
                "persistent": False,
                "signals_triggered": 1
            }
        }).execute()
        logger.info(f"✅ Mocked infection state with score 0.15")
    except Exception as e:
        logger.error(f"❌ Failed to mock state: {e}")
        return False
    
    enforced_brief = ai_service._enforce_infection_disclaimer(user_id, mock_brief)
    
    enforced_card = enforced_brief['cards'][0]
    disclaimer_present = "ceci n'est pas un diagnostic médical" in enforced_card['content'].lower()
    
    if not disclaimer_present:
        logger.info("✅ PASS: Aucun disclaimer injecté (score < 0.3)")
        return True
    else:
        logger.error("❌ FAIL: Disclaimer injecté alors que score < 0.3")
        return False


def test_disclaimer_no_duplicate():
    """
    Test: Si disclaimer déjà présent (ajouté par LLM), ne pas dupliquer
    """
    logger.info("\n=== TEST: No Duplicate Disclaimer ===")
    
    supabase = get_supabase_client()
    ai_service = AIAnalysisService(supabase)
    user_id = "test-user-id-placeholder"
    
    mock_brief = {
        "pulseScore": 68,
        "cards": [
            {
                "id": "vigilance_sante",
                "type": "focus",
                "title": "Vigilance santé",
                "content": "Pattern inhabituel détecté.\n\n---\n\n⚠️ Important\n\n• Ceci n'est PAS un diagnostic médical, mais une observation de patterns physiologiques.\n\n• Si vous ressentez des symptômes importants, consultez un professionnel de santé.",
                "state": "alert",
                "iconName": "AlertTriangle",
                "priority": 95
            }
        ]
    }
    
    # Mock infection state avec score > 0.3
    today = date.today()
    try:
        supabase.client.table("daily_state").upsert({
            "user_id": user_id,
            "state_date": today.isoformat(),
            "infection_like": {
                "smoothed_score": 0.55,
                "confidence": 0.70,
                "persistent": True,
                "signals_triggered": 2
            }
        }).execute()
        logger.info(f"✅ Mocked infection state with score 0.55")
    except Exception as e:
        logger.error(f"❌ Failed to mock state: {e}")
        return False
    
    original_content = mock_brief['cards'][0]['content']
    enforced_brief = ai_service._enforce_infection_disclaimer(user_id, mock_brief)
    enforced_content = enforced_brief['cards'][0]['content']
    
    # Compter occurrences du disclaimer
    disclaimer_count = enforced_content.lower().count("ceci n'est pas un diagnostic médical")
    
    if disclaimer_count == 1:
        logger.info("✅ PASS: Disclaimer non dupliqué")
        return True
    else:
        logger.error(f"❌ FAIL: Disclaimer dupliqué ({disclaimer_count} occurrences)")
        return False


def test_disclaimer_keywords_detection():
    """
    Test: Vérifier que tous les keywords déclenchent l'enforcement
    """
    logger.info("\n=== TEST: Keywords Detection ===")
    
    supabase = get_supabase_client()
    ai_service = AIAnalysisService(supabase)
    user_id = "test-user-id-placeholder"
    
    # Mock infection state avec score > 0.3
    today = date.today()
    try:
        supabase.client.table("daily_state").upsert({
            "user_id": user_id,
            "state_date": today.isoformat(),
            "infection_like": {
                "smoothed_score": 0.50,
                "confidence": 0.68,
                "persistent": False,
                "signals_triggered": 2
            }
        }).execute()
    except Exception as e:
        logger.error(f"❌ Failed to mock state: {e}")
        return False
    
    keywords_to_test = [
        'infection', 'vigilance', 'santé', 'signature', 
        'inhabituel', 'symptômes', 'physiologique'
    ]
    
    all_passed = True
    for keyword in keywords_to_test:
        mock_brief = {
            "pulseScore": 70,
            "cards": [
                {
                    "id": f"test_{keyword}",
                    "type": "focus",
                    "title": f"Test {keyword}",
                    "content": f"Votre pattern montre une {keyword} particulière.",
                    "state": "warning",
                    "priority": 80
                }
            ]
        }
        
        enforced_brief = ai_service._enforce_infection_disclaimer(user_id, mock_brief)
        disclaimer_present = "ceci n'est pas un diagnostic médical" in enforced_brief['cards'][0]['content'].lower()
        
        if disclaimer_present:
            logger.info(f"   ✅ Keyword '{keyword}' déclenche enforcement")
        else:
            logger.error(f"   ❌ Keyword '{keyword}' NE déclenche PAS enforcement")
            all_passed = False
    
    if all_passed:
        logger.info("✅ PASS: Tous les keywords déclenchent enforcement")
        return True
    else:
        logger.error("❌ FAIL: Certains keywords ne déclenchent pas enforcement")
        return False


def run_all_tests():
    """
    Execute tous les tests de disclaimer enforcement
    """
    logger.info("\n" + "="*60)
    logger.info("🧪 DISCLAIMER ENFORCEMENT TEST SUITE")
    logger.info("="*60)
    
    tests = [
        ("Disclaimer HIGH (score > 0.6)", test_disclaimer_enforcement_high_score),
        ("Disclaimer MODERATE (0.3-0.6)", test_disclaimer_enforcement_moderate_score),
        ("No Disclaimer (score < 0.3)", test_disclaimer_no_enforcement_low_score),
        ("No Duplicate Disclaimer", test_disclaimer_no_duplicate),
        ("Keywords Detection", test_disclaimer_keywords_detection),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} | {test_name}")
    
    logger.info("-"*60)
    logger.info(f"Total: {passed}/{total} passed ({100*passed//total}%)")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED - Disclaimer enforcement is SOLID")
    else:
        logger.error("⚠️ SOME TESTS FAILED - FIX REQUIRED BEFORE DEPLOY")
    
    return passed == total


if __name__ == "__main__":
    # Note: Ces tests nécessitent un user_id réel pour fonctionner
    # Remplacer "test-user-id-placeholder" par un vrai UUID en DB
    
    logger.info("⚠️ IMPORTANT: Remplacer 'test-user-id-placeholder' par un vrai user_id avant exécution")
    logger.info("   Utiliser un user avec des données daily_state existantes")
    logger.info("")
    
    # Uncomment pour exécuter:
    # run_all_tests()
    
    logger.info("Tests prêts. Décommenter run_all_tests() pour exécuter.")
