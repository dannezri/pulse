#!/usr/bin/env python3
"""
Script pour forcer la synchronisation HRV et RHR depuis Oura vers biometrics.
Utilise l'API Oura v2 pour récupérer les données Sleep et les insérer dans biometrics.
"""
import os
import sys
import asyncio
from datetime import date, timedelta
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Importer les services nécessaires
from supabase_client import SupabaseClient
from oura_sync_service import OuraSyncService
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Force la synchronisation HRV/RHR pour un utilisateur"""
    
    # User ID de Alyson
    user_id = "bee9a055-9b10-47d7-b91d-d7f6081a63f1"
    
    logger.info(f"🔄 Début de la synchronisation HRV/RHR pour {user_id}")
    
    # Initialiser le client Supabase
    supabase = SupabaseClient(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    # Initialiser le service Oura
    oura_service = OuraSyncService(supabase_client=supabase)
    
    # Synchroniser les 7 derniers jours
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    
    logger.info(f"📅 Période: {start_date} → {end_date}")
    
    # Synchroniser chaque jour
    current_date = start_date
    success_count = 0
    error_count = 0
    
    while current_date <= end_date:
        try:
            logger.info(f"\n📊 Synchronisation du {current_date}")
            result = await oura_service.sync_user(user_id, target_date=current_date)
            
            if result.get("success"):
                metrics = result.get("metrics", {})
                hrv = metrics.get("hrv_ms")
                rhr = metrics.get("lowest_heart_rate")
                
                logger.info(f"  ✅ Succès:")
                logger.info(f"     HRV: {hrv} ms" if hrv else "     ⚠️  HRV: non disponible")
                logger.info(f"     RHR: {rhr} bpm" if rhr else "     ⚠️  RHR: non disponible")
                
                success_count += 1
            else:
                logger.warning(f"  ⚠️  Échec: {result.get('error')}")
                error_count += 1
                
        except Exception as e:
            logger.error(f"  ❌ Erreur: {e}", exc_info=True)
            error_count += 1
        
        current_date += timedelta(days=1)
    
    logger.info(f"\n📈 Résultat:")
    logger.info(f"  ✅ Réussis: {success_count}")
    logger.info(f"  ❌ Échecs: {error_count}")
    
    # Vérifier les données insérées
    logger.info(f"\n🔍 Vérification des données dans biometrics...")
    
    result = supabase.client.table("biometrics") \
        .select("metric_type, value, recorded_at") \
        .eq("user_id", user_id) \
        .in_("metric_type", ["hrv", "hr", "resting_hr"]) \
        .gte("recorded_at", start_date.isoformat()) \
        .order("recorded_at", desc=True) \
        .limit(20) \
        .execute()
    
    if result.data:
        logger.info(f"  ✅ Trouvé {len(result.data)} entrées HRV/HR:")
        for row in result.data[:10]:
            logger.info(f"     {row['metric_type']:12} : {row['value']:6.1f} ({row['recorded_at'][:10]})")
    else:
        logger.warning(f"  ⚠️  Aucune donnée HRV/HR trouvée dans biometrics")
    
    logger.info("\n✅ Synchronisation terminée")


if __name__ == "__main__":
    asyncio.run(main())
