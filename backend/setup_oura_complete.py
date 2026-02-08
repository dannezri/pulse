"""
Script complet pour configurer un utilisateur Oura
- Enregistre l'utilisateur dans external_identities
- Import toutes les données disponibles
- Affiche un résumé

Usage: python setup_oura_complete.py
"""

import os
import sys
from datetime import datetime
from supabase_client import SupabaseClient
from oura_client import get_oura_client
from import_oura_data import OuraDataImporter
from register_oura_user import register_oura_user
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner():
    """Affiche une bannière"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🔵  PULSE × OURA RING INTEGRATION  🔵                ║
║                                                              ║
║  Configuration complète et import des données Oura          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def verify_data_import(supabase: SupabaseClient, user_id: str):
    """
    Vérifie et affiche un résumé des données importées
    
    Args:
        supabase: Client Supabase
        user_id: UUID de l'utilisateur
    """
    try:
        logger.info("Verifying imported data...")
        
        # Requête pour récupérer les stats
        response = supabase.client.table("biometrics").select(
            "metric_type, recorded_at, value"
        ).eq("user_id", user_id).eq("source", "oura").execute()
        
        if not response.data:
            logger.warning("No Oura data found in database")
            return
        
        # Organiser par type de métrique
        metrics_by_type = {}
        for record in response.data:
            metric_type = record["metric_type"]
            if metric_type not in metrics_by_type:
                metrics_by_type[metric_type] = []
            metrics_by_type[metric_type].append(record)
        
        # Afficher le résumé
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DES DONNÉES IMPORTÉES")
        print("=" * 80)
        print(f"\n✅ Total de {len(response.data)} métriques importées depuis Oura")
        print(f"🎯 {len(metrics_by_type)} types de métriques différents\n")
        
        # Détails par métrique
        print("Détails par métrique :")
        print("-" * 80)
        for metric_type, records in sorted(metrics_by_type.items()):
            values = [r["value"] for r in records]
            avg_value = sum(values) / len(values) if values else 0
            
            # Emoji selon le type
            emoji_map = {
                "sleep_score": "😴",
                "activity_score": "🏃",
                "steps": "👣",
                "readiness_score": "⚡",
                "spo2": "💨",
                "hr": "❤️",
                "hrv": "💓",
                "active_calories": "🔥",
                "total_calories": "🍽️"
            }
            emoji = emoji_map.get(metric_type, "📈")
            
            print(f"{emoji} {metric_type:30s} : {len(records):3d} records | Moyenne: {avg_value:.1f}")
        
        print("=" * 80 + "\n")
        
    except Exception as e:
        logger.error(f"Error verifying data: {e}")


def main():
    """Fonction principale"""
    print_banner()
    
    # Configuration
    print("📝 Configuration...")
    OURA_TOKEN = "IX6RMKRCMIJOVZMIB2IKVL2PWUQOCNNI"  # Token hardcodé pour setup initial
    
    from user_config import get_dev_user_uuid
    USER_UUID = get_dev_user_uuid()
    
    # Charger les credentials Supabase depuis l'environnement
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("❌ SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment")
        sys.exit(1)
    
    print(f"   User UUID: {USER_UUID}")
    print(f"   Supabase URL: {SUPABASE_URL}")
    print()
    
    # Étape 1 : Enregistrer l'utilisateur (stocke le token dans Supabase)
    print("🔐 ÉTAPE 1/3 : Enregistrement de l'utilisateur Oura")
    print("-" * 80)
    success = register_oura_user(
        supabase_user_id=USER_UUID,
        oura_token=OURA_TOKEN,
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_KEY
    )
    
    if not success:
        logger.error("❌ Failed to register user. Aborting.")
        sys.exit(1)
    
    print()
    
    # Étape 2 : Importer les données (utilise le token stocké)
    print("📥 ÉTAPE 2/3 : Import des données Oura (90 derniers jours)")
    print("-" * 80)
    
    importer = OuraDataImporter(
        oura_token=OURA_TOKEN,  # Utilise le même token pour l'import initial
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_KEY
    )
    
    importer.import_all_data(
        user_id=USER_UUID,
        days_back=90
    )
    
    print()
    
    # Étape 3 : Vérification
    print("✓ ÉTAPE 3/3 : Vérification des données")
    print("-" * 80)
    
    supabase = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
    verify_data_import(supabase, USER_UUID)
    
    # Message de succès final
    print("\n" + "=" * 80)
    print("🎉 CONFIGURATION TERMINÉE AVEC SUCCÈS !")
    print("=" * 80)
    print("\n✅ L'utilisateur Oura est maintenant configuré et ses données sont importées.")
    print("✅ Vous pouvez maintenant utiliser ces données dans l'application Pulse.")
    print("\n💡 Pour importer de nouvelles données plus tard, exécutez :")
    print("   ./run_oura_import.sh")
    print("\n📚 Consultez OURA_INTEGRATION.md pour plus d'informations.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
