#!/usr/bin/env python3
"""
Script de test pour le service d'analyse de médicaments avec Gemini
"""

import asyncio
import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Charger les variables d'environnement depuis .env
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print(f"⚠️  No .env file found at {env_path}")
        print("Make sure SUPABASE_URL, SUPABASE_SERVICE_KEY, and GOOGLE_API_KEY are set in your environment")
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment variables")
    print("Install with: pip install python-dotenv")

from medication_analysis_service import MedicationAnalysisService
from gemini_client import GeminiThinkingClient
from supabase_client import SupabaseClient


async def test_medication_analysis():
    """
    Test du service d'analyse de médicaments
    """
    print("=" * 60)
    print("🧪 TEST: Medication Analysis Service with Gemini 3 Pro")
    print("=" * 60)
    print()
    
    # 1. Initialiser les clients
    print("📦 Initializing clients...")
    try:
        supabase_client = SupabaseClient(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
        )
        print("✅ Supabase client initialized")
        
        gemini_client = GeminiThinkingClient()
        print("✅ Gemini client initialized")
        
        service = MedicationAnalysisService(
            supabase_client=supabase_client,
            gemini_client=gemini_client
        )
        print("✅ Medication Analysis Service initialized")
        print()
    except Exception as e:
        print(f"❌ Error initializing clients: {e}")
        sys.exit(1)
    
    # 2. Demander l'user_id
    print("🔑 User ID required for testing")
    print("You can find your user_id in Supabase (auth.users table)")
    print()
    
    user_id = input("Enter user_id (or press Enter to use test data): ").strip()
    
    if not user_id:
        print("⚠️  No user_id provided, using mock data for prompt testing...")
        print()
        
        # Test avec données mockées
        mock_medications = [
            {
                "medication_name": "Doliprane",
                "dosage": 500,
                "dosage_unit": "mg",
                "pills_per_intake": 1,
                "intake_times": ["08:00", "20:00"],
                "start_date": (datetime.now() - timedelta(days=14)).isoformat(),
                "atc_code": "N02BE01",
            },
            {
                "medication_name": "Venlafaxine LP",
                "dosage": 37.5,
                "dosage_unit": "mg",
                "pills_per_intake": 1,
                "intake_times": ["11:00"],
                "start_date": (datetime.now() - timedelta(days=2)).isoformat(),
                "atc_code": "N06AX16",
            },
        ]
        
        print("📝 Building prompt with mock data...")
        prompt = service._build_analysis_prompt(mock_medications)
        system_prompt = service._build_system_prompt()
        
        print()
        print("=" * 60)
        print("SYSTEM PROMPT:")
        print("=" * 60)
        print(system_prompt)
        print()
        print("=" * 60)
        print("USER PROMPT:")
        print("=" * 60)
        print(prompt)
        print()
        
        print("🧠 Calling Gemini 3 Pro with mock data...")
        try:
            result = gemini_client.generate_insight(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.8,
                max_tokens=4096,
                thinking_level="medium"
            )
            
            print("✅ Gemini response received")
            print()
            print("=" * 60)
            print("RAW RESPONSE:")
            print("=" * 60)
            print(result.get("raw_response", ""))
            print()
            
            # Parser le JSON
            try:
                analysis = json.loads(result.get("raw_response", "{}"))
                
                print("=" * 60)
                print("PARSED ANALYSIS:")
                print("=" * 60)
                print(json.dumps(analysis, indent=2, ensure_ascii=False))
                print()
                
                # Afficher les analyses
                for med in analysis.get("analyse_traitements", []):
                    print(f"📊 {med.get('nom')}:")
                    print(f"  Intro: {med.get('intro_explicative', 'N/A')}")
                    print(f"  Impact corps: {med.get('impact_corps', 'N/A')[:80]}...")
                    print(f"  Impact journée: {med.get('impact_journee', 'N/A')[:80]}...")
                    print(f"  Observation: {med.get('observation', 'N/A')[:80]}...")
                    print()
                
                # Afficher le coût
                if result.get("usage", {}).get("estimated_cost_usd"):
                    print(f"💰 Estimated cost: ${result['usage']['estimated_cost_usd']:.4f} USD")
                
                if result.get("thinking"):
                    print(f"💭 Thinking process (first 200 chars): {result['thinking'][:200]}...")
                
                print()
                print("✅ Test completed successfully!")
                
            except json.JSONDecodeError as e:
                print(f"❌ Error parsing JSON: {e}")
                sys.exit(1)
        
        except Exception as e:
            print(f"❌ Error calling Gemini: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    else:
        # Test avec un vrai user_id
        print(f"🔍 Analyzing medications for user: {user_id}")
        print()
        
        try:
            # Générer l'analyse
            print("🧠 Calling Medication Analysis Service...")
            analysis = await service.generate_medication_analysis(user_id)
            
            print("✅ Analysis generated successfully!")
            print()
            print("=" * 60)
            print("ANALYSIS RESULT:")
            print("=" * 60)
            print(json.dumps(analysis, indent=2, ensure_ascii=False))
            print()
            
            # Afficher les analyses
            for med in analysis.get("analyse_traitements", []):
                print(f"📊 {med.get('nom')}:")
                print(f"  Intro: {med.get('intro_explicative', 'N/A')}")
                print(f"  Impact corps: {med.get('impact_corps', 'N/A')[:80]}...")
                print(f"  Impact journée: {med.get('impact_journee', 'N/A')[:80]}...")
                print(f"  Observation: {med.get('observation', 'N/A')[:80]}...")
                print()
            
            # Afficher les métadonnées
            if analysis.get("_cost"):
                print(f"💰 Cost: ${analysis['_cost']:.4f} USD")
            if analysis.get("_medications_count"):
                print(f"📊 Medications analyzed: {analysis['_medications_count']}")
            if analysis.get("_generated_at"):
                print(f"📅 Generated at: {analysis['_generated_at']}")
            
            print()
            print("✅ Test completed successfully!")
            
        except Exception as e:
            print(f"❌ Error generating analysis: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_medication_analysis())
