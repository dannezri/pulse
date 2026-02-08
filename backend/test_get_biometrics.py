#!/usr/bin/env python3
"""
Test spécifique de la fonction _get_biometrics() modifiée
"""

import os
import sys
import asyncio
from datetime import date, datetime
from dotenv import load_dotenv

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from explain_service import EnergyExplainService
from supabase_client import SupabaseClient

# Charger les variables d'environnement
load_dotenv()

# ID utilisateur de test (Dan)
from user_config import get_test_user_uuid

TEST_USER_ID = get_test_user_uuid()
TEST_DATE = date.today()

async def test_get_biometrics():
    """Test la fonction _get_biometrics() réécrite"""
    print("=" * 80)
    print("🧪 TEST : Fonction _get_biometrics()")
    print("=" * 80)
    print(f"\n👤 User ID: {TEST_USER_ID}")
    print(f"📅 Date: {TEST_DATE}")
    print("\n" + "=" * 80)
    
    # Initialiser le service
    supabase = SupabaseClient()
    service = EnergyExplainService(supabase)
    
    # Appeler _get_biometrics()
    print("\n📊 Appel de _get_biometrics()...")
    print("-" * 80)
    
    try:
        biometrics = await service._get_biometrics(TEST_USER_ID, TEST_DATE)
        
        print("\n✅ Fonction exécutée avec succès")
        print("\n📋 Résultats:")
        print("-" * 80)
        
        # Afficher tous les champs
        fields = [
            ("HRV nuit", "hrv_night"),
            ("RHR nuit", "rhr_night"),
            ("Sleep Score", "sleep_score"),
            ("Readiness Score", "readiness_score"),
            ("Activity Score", "activity_score"),
            ("Steps", "steps"),
            ("HRV Baseline", "hrv_baseline"),
            ("RHR Baseline", "rhr_baseline"),
        ]
        
        missing = []
        present = []
        
        for name, key in fields:
            value = biometrics.get(key)
            if value is not None:
                print(f"✅ {name}: {value}")
                present.append(name)
            else:
                print(f"❌ {name}: None (MANQUANT)")
                missing.append(name)
        
        # Résumé
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ")
        print("=" * 80)
        print(f"\n✅ Données présentes: {len(present)}/{len(fields)}")
        for name in present:
            print(f"   - {name}")
        
        if missing:
            print(f"\n❌ Données manquantes: {len(missing)}/{len(fields)}")
            for name in missing:
                print(f"   - {name}")
            
            print("\n💡 Causes possibles:")
            print("   1. La bague Oura n'a pas synchronisé ces données")
            print("   2. Les données sont dans un format différent dans la table biometrics")
            print("   3. Les baselines n'ont pas été calculées")
        else:
            print("\n🎉 Toutes les données sont disponibles !")
        
        print("\n" + "=" * 80)
        
        # Recommandations
        if missing:
            print("\n💡 Actions recommandées:")
            print(f"   1. Vérifier la table biometrics pour {TEST_DATE}:")
            print(f"      SELECT metric_type, value FROM biometrics")
            print(f"      WHERE user_id = '{TEST_USER_ID}'")
            print(f"      AND recorded_at::date = '{TEST_DATE}'")
            print(f"\n   2. Vérifier la table user_baselines:")
            print(f"      SELECT baseline_type, baseline_data FROM user_baselines")
            print(f"      WHERE user_id = '{TEST_USER_ID}'")
        
    except Exception as e:
        print(f"\n❌ ERREUR lors de l'exécution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(test_get_biometrics())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
