"""
Test rapide du service Pulse Energy Decay
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Ajouter le backend au path
sys.path.insert(0, os.path.dirname(__file__))

from pulse_energy_decay_service import PulseEnergyDecayService
from supabase_client import SupabaseClient

async def test_pulse_energy_decay():
    """Test du service avec l'utilisateur de test"""
    
    # Initialiser Supabase
    supabase = SupabaseClient(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    # Initialiser le service
    service = PulseEnergyDecayService(supabase_client=supabase.client)
    
    # User ID de test
    user_id = "c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd"
    
    print("=" * 60)
    print("TEST: Pulse Energy Decay Service")
    print("=" * 60)
    
    # Générer la prévision
    print(f"\n📊 Génération de la prévision pour user: {user_id}\n")
    
    forecast = await service.generate_forecast(user_id=user_id, force_refresh=True)
    
    if not forecast:
        print("❌ ÉCHEC: Aucune prévision générée")
        return
    
    print("✅ SUCCÈS: Prévision générée\n")
    
    print(f"📅 Date: {forecast.date}")
    print(f"🕐 Généré à: {forecast.generated_at}")
    print(f"🔧 Modèle: {forecast.calculation_model}")
    print(f"⚡ Énergie actuelle: {forecast.current_energy:.1f}%")
    print(f"🎯 Confiance: {forecast.confidence:.2f}")
    
    print(f"\n📈 Courbe ({len(forecast.forecast_curve)} points):")
    for i, point in enumerate(forecast.forecast_curve[:10]):  # Premiers 10 points
        event_str = f" → {point.event}" if point.event else ""
        print(f"  {i+1}. {point.time[-8:-3]} : {point.value:.1f}%{event_str}")
    if len(forecast.forecast_curve) > 10:
        print(f"  ... et {len(forecast.forecast_curve) - 10} autres points")
    
    print(f"\n🎯 Influencers ({len(forecast.influencers)}):")
    for inf in forecast.influencers:
        emoji = "✅" if inf.status == "positive" else "❌" if inf.status == "negative" else "⚪"
        print(f"  {emoji} {inf.name}: {inf.impact}")
    
    if forecast.windows:
        print(f"\n⚠️ Risk Windows ({len(forecast.windows)}):")
        for win in forecast.windows:
            print(f"  • {win['from']} → {win['to']}: {win['label']}")
    
    if forecast.notes:
        print(f"\n📝 Notes ({len(forecast.notes)}):")
        for note in forecast.notes:
            print(f"  • {note}")
    
    print("\n" + "=" * 60)
    print("TEST TERMINÉ")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_pulse_energy_decay())
