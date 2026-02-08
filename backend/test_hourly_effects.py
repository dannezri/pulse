#!/usr/bin/env python3
"""
Script de test pour vérifier la génération des effets horaires par Gemini
"""

import asyncio
import json
import os
import sys
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Ajouter le répertoire backend au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from medication_analysis_service import MedicationAnalysisService
from supabase_client import SupabaseClient
from gemini_client import GeminiClient

async def test_hourly_effects():
    """
    Teste la génération des effets horaires pour un utilisateur réel
    """
    # Configuration
    user_id = "c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd"
    
    print("=" * 80)
    print("🧪 TEST: Génération des effets horaires avec Gemini")
    print("=" * 80)
    
    # Initialiser les clients
    print("\n1️⃣ Initialisation des clients...")
    supabase_client = SupabaseClient()
    gemini_client = GeminiClient()
    
    if not gemini_client.client:
        print("❌ ERREUR: Gemini client non disponible. Vérifiez GOOGLE_API_KEY.")
        return
    
    print("✅ Clients initialisés")
    
    # Initialiser le service
    print("\n2️⃣ Initialisation du service d'analyse...")
    service = MedicationAnalysisService(
        supabase_client=supabase_client,
        gemini_client=gemini_client
    )
    print("✅ Service initialisé")
    
    # Générer l'analyse
    print(f"\n3️⃣ Génération de l'analyse pour user_id={user_id}...")
    try:
        result = await service.generate_medication_analysis(user_id)
        
        print("\n✅ Analyse générée avec succès!")
        print(f"   - Nombre de médicaments: {result.get('_medications_count', 0)}")
        print(f"   - Coût: ${result.get('_cost', 0):.4f} USD")
        print(f"   - Généré à: {result.get('_generated_at', 'N/A')}")
        
        # Vérifier la présence des effets horaires
        print("\n4️⃣ Vérification des effets horaires...")
        analyses = result.get('analyse_traitements', [])
        
        for i, med_analysis in enumerate(analyses, 1):
            med_name = med_analysis.get('nom', 'Inconnu')
            effets_horaires = med_analysis.get('effets_horaires', [])
            
            print(f"\n   📊 Médicament {i}: {med_name}")
            print(f"      - Nombre d'heures: {len(effets_horaires)}")
            
            if effets_horaires:
                # Afficher quelques exemples
                print(f"\n      Exemples d'effets horaires:")
                for hour_data in effets_horaires[:3]:  # 3 premières heures
                    print(f"      • {hour_data.get('heure', 'N/A')}: "
                          f"Concentration={hour_data.get('concentration', 0)}%, "
                          f"Efficacité={hour_data.get('efficacite', 0)}%, "
                          f"Effets 2nd={hour_data.get('effets_secondaires', 0)}%")
                    print(f"        → {hour_data.get('description', 'N/A')}")
                
                if len(effets_horaires) > 3:
                    print(f"      ... ({len(effets_horaires) - 3} autres heures)")
                
                # Vérifier que les données sont cohérentes
                has_all_fields = all(
                    'heure' in h and 'concentration' in h and 
                    'efficacite' in h and 'effets_secondaires' in h and 
                    'description' in h
                    for h in effets_horaires
                )
                
                if has_all_fields:
                    print(f"      ✅ Tous les champs requis sont présents")
                else:
                    print(f"      ⚠️ Certains champs sont manquants")
                
                # Vérifier que les valeurs sont dans les bonnes plages
                values_valid = all(
                    0 <= h.get('concentration', -1) <= 100 and
                    0 <= h.get('efficacite', -1) <= 100 and
                    0 <= h.get('effets_secondaires', -1) <= 100
                    for h in effets_horaires
                )
                
                if values_valid:
                    print(f"      ✅ Toutes les valeurs sont dans la plage 0-100")
                else:
                    print(f"      ⚠️ Certaines valeurs sont hors plage")
            else:
                print(f"      ❌ Aucun effet horaire généré!")
        
        # Sauvegarder le résultat complet dans un fichier
        output_file = "test_hourly_effects_output.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n5️⃣ Résultat complet sauvegardé dans: {output_file}")
        
    except Exception as e:
        print(f"\n❌ ERREUR lors de la génération: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 80)
    print("✅ Test terminé avec succès!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_hourly_effects())
