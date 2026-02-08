"""
Service pour peupler automatiquement l'historique des médicaments.

Ce script génère automatiquement des entrées d'historique pour tous les médicaments
actifs d'un utilisateur, depuis leur date de début jusqu'à aujourd'hui.
"""

import os
import sys
from datetime import datetime, timedelta, time
from typing import List, Dict, Any
from supabase import create_client, Client
import logging

# Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def get_active_medications(user_id: str) -> List[Dict[str, Any]]:
    """Récupère tous les médicaments actifs d'un utilisateur."""
    response = supabase.table("user_medications").select("*").eq("user_id", user_id).eq("is_active", True).execute()
    
    if response.data:
        logger.info(f"✅ Found {len(response.data)} active medications for user {user_id}")
        return response.data
    return []


def generate_intake_entries(medication: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Génère les entrées d'historique pour un médicament donné.
    
    Crée une entrée par jour depuis start_date jusqu'à aujourd'hui,
    pour chaque heure de prise prévue.
    """
    entries = []
    
    med_id = medication["id"]
    user_id = medication["user_id"]
    start_date = datetime.fromisoformat(medication["start_date"]).date() if isinstance(medication["start_date"], str) else medication["start_date"]
    end_date = datetime.fromisoformat(medication["end_date"]).date() if medication.get("end_date") and isinstance(medication["end_date"], str) else None
    intake_times = medication.get("intake_times") or []
    pills_per_intake = medication.get("pills_per_intake") or 1
    
    # Si pas d'heure de prise, on prend 12:00 par défaut
    if not intake_times:
        intake_times = ["12:00"]
    
    # Date de fin = aujourd'hui ou end_date si défini
    today = datetime.now().date()
    final_date = end_date if end_date and end_date < today else today
    
    logger.info(f"📅 Generating entries for {medication['medication_name']}: {start_date} → {final_date}")
    
    # Générer une entrée par jour
    current_date = start_date
    while current_date <= final_date:
        for intake_time_str in intake_times:
            # Parser l'heure
            try:
                intake_hour, intake_minute = map(int, intake_time_str.split(":"))
                intake_time_obj = time(intake_hour, intake_minute)
            except:
                intake_time_obj = time(12, 0)
            
            # Créer le timestamp complet
            taken_at = datetime.combine(current_date, intake_time_obj)
            
            entry = {
                "user_id": user_id,
                "medication_id": med_id,
                "taken_at": taken_at.isoformat(),
                "intake_date": current_date.isoformat(),
                "intake_time": intake_time_obj.isoformat(),
                "scheduled_time": intake_time_obj.isoformat(),
                "was_on_time": True,  # Par défaut on considère que c'est pris à l'heure
                "pills_taken": int(pills_per_intake),
                "status": "taken",
                "notes": "Généré automatiquement",
            }
            entries.append(entry)
        
        current_date += timedelta(days=1)
    
    logger.info(f"✅ Generated {len(entries)} entries for {medication['medication_name']}")
    return entries


def insert_intake_entries(entries: List[Dict[str, Any]]) -> int:
    """Insère les entrées dans la base de données."""
    if not entries:
        return 0
    
    try:
        # Insérer par batch de 100 pour éviter les timeouts
        batch_size = 100
        total_inserted = 0
        
        for i in range(0, len(entries), batch_size):
            batch = entries[i:i + batch_size]
            response = supabase.table("medication_intake_history").insert(batch).execute()
            total_inserted += len(batch)
            logger.info(f"📊 Inserted batch {i // batch_size + 1}: {len(batch)} entries")
        
        logger.info(f"✅ Total inserted: {total_inserted} entries")
        return total_inserted
        
    except Exception as e:
        logger.error(f"❌ Error inserting entries: {e}")
        raise


def auto_populate_history(user_id: str, dry_run: bool = False) -> int:
    """
    Peuple automatiquement l'historique pour un utilisateur donné.
    
    Args:
        user_id: ID de l'utilisateur
        dry_run: Si True, ne fait qu'afficher ce qui serait inséré sans vraiment insérer
    
    Returns:
        Nombre d'entrées créées
    """
    logger.info(f"🚀 Starting auto-populate for user {user_id}")
    
    # 1. Récupérer les médicaments actifs
    medications = get_active_medications(user_id)
    
    if not medications:
        logger.warning(f"⚠️ No active medications found for user {user_id}")
        return 0
    
    # 2. Générer les entrées
    all_entries = []
    for med in medications:
        entries = generate_intake_entries(med)
        all_entries.extend(entries)
    
    logger.info(f"📊 Total entries to insert: {len(all_entries)}")
    
    # 3. Insérer (sauf en dry-run)
    if dry_run:
        logger.info("🔍 DRY RUN mode - No data will be inserted")
        logger.info(f"Would insert {len(all_entries)} entries")
        # Afficher un échantillon
        if all_entries:
            logger.info("Sample entry:")
            logger.info(all_entries[0])
        return 0
    else:
        return insert_intake_entries(all_entries)


def clear_history(user_id: str) -> int:
    """Supprime tout l'historique d'un utilisateur (utile pour reset)."""
    response = supabase.table("medication_intake_history").delete().eq("user_id", user_id).execute()
    deleted_count = len(response.data) if response.data else 0
    logger.info(f"🗑️ Deleted {deleted_count} entries for user {user_id}")
    return deleted_count


def main():
    """Script principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto-populate medication intake history")
    parser.add_argument("--user-id", required=True, help="User ID (UUID)")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode (no insertion)")
    parser.add_argument("--clear", action="store_true", help="Clear existing history before populating")
    
    args = parser.parse_args()
    
    try:
        # Clear si demandé
        if args.clear and not args.dry_run:
            clear_history(args.user_id)
        
        # Peupler l'historique
        count = auto_populate_history(args.user_id, dry_run=args.dry_run)
        
        logger.info(f"🎉 SUCCESS: {count} entries created")
        
    except Exception as e:
        logger.error(f"❌ FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
