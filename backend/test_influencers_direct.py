#!/usr/bin/env python3
"""
Test direct de la génération des influencers
"""

import sys
import os

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv()

# Importer la fonction
from intraday_energy_service import generate_influencers_heuristic
import json

def test_influencers():
    # Test avec l'utilisateur défini dans DEV_USER_UUID
    from user_config import get_dev_user_uuid
    user_id = get_dev_user_uuid()
    
    print(f"🧪 Test des influencers pour l'utilisateur {user_id}")
    print("=" * 80)
    
    try:
        influencers = generate_influencers_heuristic(
            user_id=user_id,
            base_energy=50.0,
            recovery=0.45,
            sleep_debt=0.88,
            overtrain=0.32,
            infection=0.95
        )
        
        print(f"\n✅ Nombre d'influencers générés: {len(influencers)}")
        print("\n📊 Détail des influencers:")
        print(json.dumps(influencers, indent=2, ensure_ascii=False))
        
        # Compter par type
        by_type = {}
        for inf in influencers:
            inf_type = inf.get('type', 'unknown')
            by_type[inf_type] = by_type.get(inf_type, 0) + 1
        
        print(f"\n📈 Répartition par type:")
        for inf_type, count in by_type.items():
            print(f"  - {inf_type}: {count}")
        
        return influencers
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la génération: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_influencers()
