#!/usr/bin/env python3
"""Test rapide du modèle Pulse Energy Decay (sans Oura sync)"""
import asyncio
import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from supabase_client import SupabaseClient
from pulse_energy_decay_service import PulseEnergyDecayService

async def main():
    print("=" * 60)
    print("TEST RAPIDE: Pulse Energy Decay")
    print("=" * 60)
    
    # Init Supabase
    supabase = SupabaseClient(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    # Init service
    service = PulseEnergyDecayService(supabase_client=supabase.client)
    
    # User ID
    user_id = "c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd"
    
    print(f"\n⚡ Génération de la prévision pour user: {user_id}")
    
    # Générer prévision
    forecast = await service.generate_forecast(user_id=user_id, force_refresh=True)
    
    if forecast:
        print("✅ SUCCÈS!\n")
        print(f"📊 Énergie actuelle: {forecast.current_energy:.1f}%")
        print(f"🎯 Confiance: {forecast.confidence:.2f}")
        print(f"🔧 Modèle: {forecast.calculation_model}")
        print(f"📈 Points de courbe: {len(forecast.forecast_curve)}")
        
        if forecast.influencers:
            print(f"\n🎯 Influencers ({len(forecast.influencers)}):")
            for inf in forecast.influencers:
                emoji = "✅" if inf.status == "positive" else "❌" if inf.status == "negative" else "⚪"
                print(f"  {emoji} {inf.name}: {inf.impact}")
        
        print("\n" + "=" * 60)
        print("✅ TEST RÉUSSI - Le modèle fonctionne!")
        print("=" * 60)
    else:
        print("❌ ÉCHEC - Aucune prévision générée")

if __name__ == "__main__":
    asyncio.run(main())
