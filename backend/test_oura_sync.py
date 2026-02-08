#!/usr/bin/env python3
"""
Test Oura Sync - Vérification de l'intégration complète
========================================================
Teste la synchronisation Oura avec mise à jour de health_profiles.

Usage:
    python3 test_oura_sync.py
"""

import asyncio
import os
import sys
from datetime import date
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from supabase_client import SupabaseClient
from oura_sync_service import sync_user_oura_data
from oura_token_utils import get_user_oura_token
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_oura_sync():
    """Test complet du sync Oura"""
    
    # Configuration
    from user_config import get_test_user_uuid
    USER_ID = get_test_user_uuid()
    
    print("=" * 70)
    print("TEST: Oura Sync Service")
    print("=" * 70)
    
    # Initialiser Supabase
    supabase = SupabaseClient(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    # 1. Récupérer le token Oura depuis Supabase
    print("\n📋 Étape 1: Récupération du token Oura depuis Supabase...")
    
    try:
        OURA_TOKEN = get_user_oura_token(supabase, USER_ID)
        
        if not OURA_TOKEN:
            print("❌ Aucun token Oura trouvé pour cet utilisateur")
            print("   → Exécutez d'abord: python3 register_oura_user.py")
            return
        
        print(f"✅ Token Oura récupéré avec succès")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return
    
    # 2. Synchroniser les données
    print("\n📊 Étape 2: Synchronisation des données Oura...")
    
    try:
        result = await sync_user_oura_data(USER_ID, supabase, date.today())
        
        if result['status'] == 'success':
            print(f"✅ Synchronisation réussie!")
            
            data = result['data']
            metrics = data['current_metrics']
            anomalies = data['anomalies']
            
            print("\n📈 Métriques récupérées:")
            print(f"  • Readiness Score: {metrics.get('readiness_score', 'N/A')}")
            print(f"  • Sleep Score: {metrics.get('sleep_score', 'N/A')}")
            print(f"  • Activity Score: {metrics.get('activity_score', 'N/A')}")
            print(f"  • HRV: {metrics.get('hrv_ms', 'N/A')} ms")
            print(f"  • Resting HR: {metrics.get('resting_hr', 'N/A')} bpm")
            print(f"  • Sleep Duration: {metrics.get('total_sleep_duration', 'N/A')} min")
            print(f"  • Deep Sleep: {metrics.get('deep_sleep_duration', 'N/A')} min")
            print(f"  • REM Sleep: {metrics.get('rem_sleep_duration', 'N/A')} min")
            print(f"  • Steps: {metrics.get('steps', 'N/A')}")
            print(f"  • Temperature Deviation: {metrics.get('temperature_deviation', 'N/A')}")
            
            if anomalies:
                print(f"\n⚠️  Anomalies détectées ({len(anomalies)}):")
                for anomaly in anomalies:
                    print(f"  • {anomaly['type']}: {anomaly.get('severity', 'N/A')}")
                    if 'z_score' in anomaly:
                        print(f"    Z-Score: {anomaly['z_score']}")
            else:
                print("\n✅ Aucune anomalie détectée")
        
        else:
            print(f"❌ Échec: {result['message']}")
    
    except Exception as e:
        print(f"❌ Erreur lors de la sync: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. Vérifier que health_profiles a été mis à jour
    print("\n🔍 Étape 3: Vérification de health_profiles...")
    
    try:
        result = supabase.client.from_('health_profiles') \
            .select('date, current_metrics, anomalies') \
            .eq('user_id', USER_ID) \
            .eq('date', date.today().isoformat()) \
            .single() \
            .execute()
        
        if result.data:
            print("✅ health_profiles mis à jour avec succès")
            print(f"   Date: {result.data['date']}")
            print(f"   Readiness: {result.data['current_metrics'].get('readiness_score', 'N/A')}")
        else:
            print("❌ health_profiles non trouvé")
    
    except Exception as e:
        print(f"⚠️  Erreur lors de la vérification: {e}")
    
    # 4. Tester le modèle Pulse Energy Decay avec les nouvelles données
    print("\n⚡ Étape 4: Test du modèle Pulse Energy Decay...")
    
    try:
        from pulse_energy_decay_service import PulseEnergyDecayService
        
        service = PulseEnergyDecayService(supabase_client=supabase.client)
        forecast = await service.generate_forecast(user_id=USER_ID, force_refresh=True)
        
        if forecast:
            print("✅ Prévision Pulse Energy Decay générée!")
            print(f"   Énergie actuelle: {forecast.current_energy:.1f}%")
            print(f"   Confiance: {forecast.confidence:.2f}")
            print(f"   Modèle: {forecast.calculation_model}")
            
            if forecast.influencers:
                print(f"\n🎯 Influencers ({len(forecast.influencers)}):")
                for inf in forecast.influencers:
                    emoji = "✅" if inf.status == "positive" else "❌" if inf.status == "negative" else "⚪"
                    print(f"   {emoji} {inf.name}: {inf.impact}")
        else:
            print("❌ Échec de la génération de prévision")
    
    except Exception as e:
        print(f"⚠️  Erreur modèle: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("TEST TERMINÉ")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_oura_sync())
