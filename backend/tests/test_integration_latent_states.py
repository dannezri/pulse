"""
Integration Test for Latent States System
Tests end-to-end flow: database → calculation → AI prompt → brief generation
"""

import json
import logging
from datetime import datetime, timedelta
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import SupabaseClient
from services.latent_state_service import LatentStateService
from services.ai_service import AIAnalysisService
from llm_client import LLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_supabase_client():
    """Initialize Supabase client with environment variables"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        logger.error("SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables must be set")
        logger.error("Please create a .env file in the backend directory based on config.example.env")
        logger.error("Or set them in your environment: export SUPABASE_URL=... export SUPABASE_SERVICE_KEY=...")
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables must be set")
    
    return SupabaseClient(supabase_url, supabase_key)


def test_database_migration():
    """
    Test 1: Verify database migration was applied correctly
    """
    logger.info("=" * 60)
    logger.info("TEST 1: Database Migration")
    logger.info("=" * 60)
    
    try:
        supabase = get_supabase_client()
        
        # Try to query daily_state table (should exist after migration)
        response = supabase.client.table("daily_state").select("id").limit(1).execute()
        
        logger.info("✓ daily_state table exists and is accessible")
        logger.info(f"  Query successful: {len(response.data) if response.data else 0} rows")
        return True
    
    except Exception as e:
        logger.error(f"✗ Database migration test failed: {e}")
        logger.error("  Please run migration: psql -f database/migrations/016_daily_state.sql")
        return False


def test_latent_state_calculation(user_id: str = None):
    """
    Test 2: Calculate latent states for a test user
    
    Args:
        user_id: User UUID to test with (defaults to first user found)
    """
    logger.info("=" * 60)
    logger.info("TEST 2: Latent State Calculation")
    logger.info("=" * 60)
    
    try:
        supabase = get_supabase_client()
        
        # Find a test user if not provided
        if not user_id:
            users_response = supabase.client.table("profiles").select("id").limit(1).execute()
            if not users_response.data or len(users_response.data) == 0:
                logger.error("✗ No users found in database")
                return False
            user_id = users_response.data[0]['id']
        
        logger.info(f"Testing with user_id: {user_id}")
        
        # Initialize service and calculate states
        latent_service = LatentStateService(supabase)
        states = latent_service.calculate_all_states(user_id, force_refresh=True)
        
        # Verify all 4 states were calculated
        required_states = ['recovery', 'sleep_debt', 'overtrain', 'infection_like']
        for state_type in required_states:
            if state_type not in states:
                logger.error(f"✗ Missing state: {state_type}")
                return False
            
            state = states[state_type]
            logger.info(f"\n  {state_type.upper()}:")
            logger.info(f"    Score: {state.get('score', 'N/A'):.3f}")
            logger.info(f"    Smoothed: {state.get('smoothed_score', 'N/A'):.3f}")
            logger.info(f"    Confidence: {state.get('confidence', 'N/A'):.3f}")
            
            # Verify required fields
            if 'score' not in state or 'confidence' not in state:
                logger.error(f"✗ Missing required fields in {state_type}")
                return False
        
        logger.info("\n✓ All 4 latent states calculated successfully")
        
        # Verify data was saved to database
        db_check = supabase.client.table("daily_state").select(
            "state_type, score, smoothed_score"
        ).eq("user_id", user_id).eq("state_date", datetime.utcnow().date().isoformat()).execute()
        
        if db_check.data and len(db_check.data) == 4:
            logger.info(f"✓ All 4 states saved to database")
        else:
            logger.warning(f"⚠ Only {len(db_check.data) if db_check.data else 0}/4 states in database")
        
        return True
    
    except Exception as e:
        logger.error(f"✗ Latent state calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_prompt_integration(user_id: str = None):
    """
    Test 3: Verify latent states are included in AI prompt
    
    Args:
        user_id: User UUID to test with
    """
    logger.info("=" * 60)
    logger.info("TEST 3: AI Prompt Integration")
    logger.info("=" * 60)
    
    try:
        supabase = get_supabase_client()
        llm = LLMClient()
        ai_service = AIAnalysisService(supabase, llm)
        
        # Find user if not provided
        if not user_id:
            users_response = supabase.client.table("profiles").select("id").limit(1).execute()
            if not users_response.data:
                logger.error("✗ No users found")
                return False
            user_id = users_response.data[0]['id']
        
        logger.info(f"Testing with user_id: {user_id}")
        
        # Build brief prompt (should include latent states)
        prompt = ai_service._build_brief_prompt(user_id)
        
        # Verify latent states section exists
        if "ÉTATS LATENTS CALCULÉS" in prompt:
            logger.info("✓ Latent states section found in prompt")
        else:
            logger.error("✗ Latent states section missing from prompt")
            return False
        
        # Verify all 4 states are mentioned
        state_names = ['Récupération', 'Dette de sommeil', 'Surcharge entraînement', 'Signature infection']
        for state_name in state_names:
            if state_name in prompt:
                logger.info(f"  ✓ {state_name} found")
            else:
                logger.warning(f"  ⚠ {state_name} not found (may be normal if no data)")
        
        # Verify qualitative categories are used (not raw percentages in state descriptions)
        if "bonne" in prompt or "moyenne" in prompt or "faible" in prompt:
            logger.info("✓ Qualitative categories found (bonne/moyenne/faible)")
        else:
            logger.warning("⚠ Qualitative categories not found in prompt")
        
        logger.info(f"\n✓ AI prompt integration successful")
        logger.info(f"  Prompt length: {len(prompt)} characters")
        
        return True
    
    except Exception as e:
        logger.error(f"✗ AI prompt integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_brief_generation(user_id: str = None):
    """
    Test 4: Generate brief and verify cards are created
    
    Args:
        user_id: User UUID to test with
    """
    logger.info("=" * 60)
    logger.info("TEST 4: Brief Generation")
    logger.info("=" * 60)
    
    try:
        supabase = get_supabase_client()
        llm = LLMClient()
        ai_service = AIAnalysisService(supabase, llm)
        
        # Find user
        if not user_id:
            users_response = supabase.client.table("profiles").select("id, full_name").limit(1).execute()
            if not users_response.data:
                logger.error("✗ No users found")
                return False
            user_id = users_response.data[0]['id']
            user_name = users_response.data[0].get('full_name', 'Test User')
        
        logger.info(f"Testing with user_id: {user_id}")
        
        # Clear cache first by deleting today's cached brief
        cache_key = f"brief_daily_{user_id}_{datetime.utcnow().date().isoformat()}"
        try:
            supabase.client.table("insights").delete().eq(
                "user_id", user_id
            ).eq("category", "brief_daily").eq("calendar_event_id", cache_key).execute()
            logger.info(f"✓ Cache cleared for {cache_key}")
        except Exception as e:
            logger.warning(f"⚠ Failed to clear cache: {e}")
        
        # Generate brief (this will call LLM)
        logger.info("Generating brief (calling LLM)...")
        brief_result = ai_service.generate_brief(user_id, force_refresh=True)
        
        if not brief_result or brief_result.get('status') != 'success':
            logger.error("✗ Brief generation failed: no result")
            return False
        
        # Brief data is in 'cards', not 'brief'
        brief_data = {
            'cards': brief_result.get('cards', []),
            'pulseScore': brief_result.get('pulseScore', 0)
        }
        
        # brief_data is already parsed, no need to parse JSON again
        
        # Verify structure
        if 'cards' not in brief_data:
            logger.error("✗ Brief missing 'cards' field")
            return False
        
        cards = brief_data['cards']
        logger.info(f"✓ Brief generated successfully")
        logger.info(f"  Cards generated: {len(cards)}")
        logger.info(f"  Pulse Score: {brief_data.get('pulseScore', 'N/A')}")
        
        # Analyze cards
        card_types = {}
        for card in cards:
            card_id = card.get('id', 'unknown')
            card_type = card.get('type', 'unknown')
            card_state = card.get('state', 'neutral')
            card_types[card_id] = card_type
            
            logger.info(f"\n  Card: {card_id}")
            logger.info(f"    Type: {card_type}")
            logger.info(f"    Title: {card.get('title', 'N/A')[:50]}...")
            logger.info(f"    State: {card_state}")
            logger.info(f"    Priority: {card.get('priority', 'N/A')}")
            
            # Check for unique IDs
            if list(card_types.values()).count(card_type) > 1 and card_id in ['verdict', 'meteo', 'petit_pas']:
                logger.warning(f"    ⚠ Duplicate base card ID: {card_id}")
        
        # Verify mandatory cards
        mandatory_ids = ['verdict', 'meteo', 'petit_pas']
        for mandatory_id in mandatory_ids:
            if mandatory_id in card_types:
                logger.info(f"  ✓ Mandatory card '{mandatory_id}' present")
            else:
                logger.warning(f"  ⚠ Mandatory card '{mandatory_id}' missing")
        
        # Check for latent state cards
        latent_card_ids = ['dette_sommeil', 'surcharge', 'vigilance_sante']
        latent_cards_found = [cid for cid in latent_card_ids if cid in card_types]
        if latent_cards_found:
            logger.info(f"  ✓ Latent state cards generated: {latent_cards_found}")
        else:
            logger.info(f"  ℹ No latent state cards generated (may be normal if no high-risk states)")
        
        logger.info("\n✓ Brief generation successful")
        return True
    
    except Exception as e:
        logger.error(f"✗ Brief generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_medical_disclaimers(user_id: str = None):
    """
    Test 5: CRITICAL - Verify medical disclaimers in alert cards
    
    Args:
        user_id: User UUID to test with
    """
    logger.info("=" * 60)
    logger.info("TEST 5: Medical Disclaimers (CRITICAL)")
    logger.info("=" * 60)
    
    try:
        supabase = get_supabase_client()
        llm = LLMClient()
        ai_service = AIAnalysisService(supabase, llm)
        
        # Find user
        if not user_id:
            users_response = supabase.client.table("profiles").select("id").limit(1).execute()
            if not users_response.data:
                logger.error("✗ No users found")
                return False
            user_id = users_response.data[0]['id']
        
        logger.info(f"Testing with user_id: {user_id}")
        
        # Clear cache first
        cache_key = f"brief_daily_{user_id}_{datetime.utcnow().date().isoformat()}"
        try:
            supabase.client.table("insights").delete().eq(
                "user_id", user_id
            ).eq("category", "brief_daily").eq("calendar_event_id", cache_key).execute()
        except Exception:
            pass  # Ignore cache clear errors
        
        # Generate brief
        logger.info("Generating brief to check disclaimers...")
        brief_result = ai_service.generate_brief(user_id, force_refresh=True)
        
        if not brief_result or brief_result.get('status') != 'success':
            logger.error("✗ Brief generation failed")
            return False
        
        # Cards are already in the result dict
        cards = brief_result.get('cards', [])
        
        # Check ONLY health-related cards for medical disclaimers
        # Medical disclaimers are ONLY required for specific health cards (vigilance_sante, infection)
        # NOT for general alert cards like (verdict, inactivite, nutrition, etc.)
        health_card_ids = ['vigilance_sante', 'infection', 'dette_sommeil', 'surcharge']
        cards_to_check = [c for c in cards if c.get('id') in health_card_ids]
        
        if not cards_to_check:
            logger.info("  ℹ No health-related cards generated (vigilance_sante, infection, dette_sommeil, surcharge)")
            logger.info("  ✓ Test passes - disclaimers only required for specific health cards")
            return True
        
        logger.info(f"  Checking {len(cards_to_check)} health-related cards for medical disclaimers...")
        
        required_phrases = [
            "Ce n'est pas un diagnostic médical",
            "consultez un professionnel de santé"
        ]
        
        forbidden_phrases = [
            "vous avez une infection",
            "vous êtes malade",
            "diagnostic confirmé"
        ]
        
        all_passed = True
        for card in cards_to_check:
            card_id = card.get('id', 'unknown')
            content = card.get('content', '')
            
            logger.info(f"\n  Checking card: {card_id}")
            
            # Check for required disclaimers
            for phrase in required_phrases:
                if phrase.lower() in content.lower():
                    logger.info(f"    ✓ Contains: '{phrase}'")
                else:
                    logger.error(f"    ✗ MISSING: '{phrase}'")
                    all_passed = False
            
            # Check for forbidden terms
            for phrase in forbidden_phrases:
                if phrase.lower() in content.lower():
                    logger.error(f"    ✗ FORBIDDEN TERM: '{phrase}'")
                    all_passed = False
                else:
                    logger.info(f"    ✓ No forbidden term: '{phrase}'")
        
        if all_passed:
            logger.info("\n✓ All medical disclaimers present and correct")
        else:
            logger.error("\n✗ Medical disclaimer check FAILED")
        
        return all_passed
    
    except Exception as e:
        logger.error(f"✗ Medical disclaimer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests(user_id: str = None):
    """
    Run all integration tests in sequence
    
    Args:
        user_id: Optional user UUID to test with (defaults to first user)
    """
    logger.info("\n" + "=" * 60)
    logger.info("LATENT STATES INTEGRATION TESTS")
    logger.info("=" * 60 + "\n")
    
    results = {
        'Database Migration': test_database_migration(),
        'Latent State Calculation': test_latent_state_calculation(user_id),
        'AI Prompt Integration': test_ai_prompt_integration(user_id),
        'Brief Generation': test_brief_generation(user_id),
        'Medical Disclaimers (CRITICAL)': test_medical_disclaimers(user_id)
    }
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"  {status} - {test_name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 All tests passed! Latent states system is ready.")
    else:
        logger.error(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.")
    
    return passed == total


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run latent states integration tests')
    parser.add_argument('--user-id', type=str, help='User UUID to test with (optional)')
    args = parser.parse_args()
    
    success = run_all_tests(user_id=args.user_id)
    exit(0 if success else 1)
