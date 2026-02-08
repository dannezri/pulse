"""
Script de synchronisation des entrées alimentaires FatSecret vers Supabase
Usage: python sync_fatsecret_food_entries.py [--days-back N] [--user-id UUID]

Ce script:
1. Récupère tous les utilisateurs avec un profil FatSecret actif
2. Pour chaque utilisateur, récupère les entrées alimentaires des N derniers jours
3. Upsert les données dans Supabase (table food_entries_raw)
"""

import os
import sys
import argparse
import datetime as dt
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

from supabase_client import SupabaseClient
from fatsecret_client import get_fatsecret_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def upsert_entries(
    supabase: SupabaseClient,
    user_id: str,
    date: dt.date,
    entries: List[Dict]
) -> int:
    """
    Upsert les entrées alimentaires dans Supabase
    
    Args:
        supabase: Client Supabase
        user_id: UUID de l'utilisateur
        date: Date des entrées
        entries: Liste des entrées à insérer
    
    Returns:
        Nombre d'entrées insérées/mises à jour
    """
    if not entries:
        return 0
    
    rows = []
    for entry in entries:
        food_entry_id = entry.get("food_entry_id")
        if food_entry_id is None:
            continue
        
        # Construire la ligne à insérer
        row = {
            "user_id": user_id,
            "fatsecret_food_entry_id": int(food_entry_id),
            "entry_date": date.isoformat(),
            "meal": entry.get("meal") or "other",
            "description": entry.get("food_entry_description"),
            "food_id": int(entry["food_id"]) if entry.get("food_id") is not None else None,
            "serving_id": int(entry["serving_id"]) if entry.get("serving_id") is not None else None,
            "number_of_units": float(entry["number_of_units"]) if entry.get("number_of_units") else None,
            "raw": entry
        }
        rows.append(row)
    
    if not rows:
        return 0
    
    try:
        # Upsert basé sur la contrainte unique (user_id, fatsecret_food_entry_id)
        result = supabase.client.table("food_entries_raw").upsert(
            rows,
            on_conflict="user_id,fatsecret_food_entry_id"
        ).execute()
        
        logger.info(f"Upserted {len(rows)} entries for {date}")
        return len(rows)
        
    except Exception as e:
        logger.error(f"Error upserting entries: {e}")
        raise


def sync_user_date_range(
    supabase: SupabaseClient,
    user_id: str,
    oauth_token: str,
    oauth_token_secret: str,
    days_back: int = 7
) -> Dict[str, int]:
    """
    Synchronise les entrées alimentaires d'un utilisateur pour une plage de dates
    
    Args:
        supabase: Client Supabase
        user_id: UUID de l'utilisateur
        oauth_token: Token OAuth FatSecret (auth_token du profil)
        oauth_token_secret: Secret OAuth FatSecret (auth_secret du profil)
        days_back: Nombre de jours à synchroniser (défaut: 7)
    
    Returns:
        Dict avec statistiques (total_entries, days_synced)
    """
    logger.info(f"Starting sync for user {user_id} (last {days_back} days)")
    
    # Initialiser le client FatSecret avec les tokens du profil
    client = get_fatsecret_client(
        oauth_token=oauth_token,
        oauth_secret=oauth_token_secret
    )
    
    today = dt.date.today()
    start_date = today - dt.timedelta(days=days_back)
    
    total_entries = 0
    days_synced = 0
    
    # Synchroniser jour par jour
    current_date = start_date
    while current_date <= today:
        try:
            # Récupérer les entrées pour cette date
            payload = client.get_food_entries_for_date(current_date)
            entries = client.parse_food_entries(payload)
            
            # Upsert dans Supabase
            count = upsert_entries(supabase, user_id, current_date, entries)
            total_entries += count
            days_synced += 1
            
            if count > 0:
                logger.info(f"  {current_date}: {count} entries")
            
        except Exception as e:
            logger.error(f"Error syncing {current_date}: {e}")
        
        current_date += dt.timedelta(days=1)
    
    # Mettre à jour last_synced_date
    try:
        supabase.client.table("fatsecret_connections").update({
            "last_synced_date": today.isoformat()
        }).eq("user_id", user_id).execute()
    except Exception as e:
        logger.warning(f"Could not update last_synced_date: {e}")
    
    logger.info(f"Sync complete for user {user_id}: {total_entries} entries over {days_synced} days")
    
    return {
        "total_entries": total_entries,
        "days_synced": days_synced
    }


def sync_all_users(
    supabase: SupabaseClient,
    days_back: int = 7,
    user_id_filter: Optional[str] = None
) -> Dict[str, int]:
    """
    Synchronise tous les utilisateurs ayant un profil FatSecret actif
    
    Args:
        supabase: Client Supabase
        days_back: Nombre de jours à synchroniser
        user_id_filter: UUID d'un utilisateur spécifique (optionnel)
    
    Returns:
        Dict avec statistiques globales
    """
    # Récupérer les profils actifs
    try:
        query = supabase.client.table("fatsecret_connections").select(
            "user_id, oauth_token, oauth_token_secret, last_synced_date"
        ).eq("is_active", True)
        
        if user_id_filter:
            query = query.eq("user_id", user_id_filter)
        
        result = query.execute()
        connections = result.data
        
        logger.info(f"Found {len(connections)} active FatSecret profile(s)")
        
    except Exception as e:
        logger.error(f"Error fetching connections: {e}")
        return {"users_synced": 0, "total_entries": 0}
    
    # Synchroniser chaque utilisateur
    stats = {
        "users_synced": 0,
        "total_entries": 0,
        "total_days": 0
    }
    
    for conn in connections:
        try:
            result = sync_user_date_range(
                supabase=supabase,
                user_id=conn["user_id"],
                oauth_token=conn["oauth_token"],
                oauth_token_secret=conn["oauth_token_secret"],
                days_back=days_back
            )
            
            stats["users_synced"] += 1
            stats["total_entries"] += result["total_entries"]
            stats["total_days"] += result["days_synced"]
            
        except Exception as e:
            logger.error(f"Error syncing user {conn['user_id']}: {e}")
            continue
    
    return stats


def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(
        description="Synchronise les entrées alimentaires FatSecret vers Supabase"
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=7,
        help="Nombre de jours à synchroniser (défaut: 7)"
    )
    parser.add_argument(
        "--user-id",
        type=str,
        help="UUID d'un utilisateur spécifique à synchroniser (optionnel)"
    )
    
    args = parser.parse_args()
    
    # Vérifier les variables d'environnement
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
    FATSECRET_KEY = os.getenv("FATSECRET_CONSUMER_KEY")
    FATSECRET_SECRET = os.getenv("FATSECRET_CONSUMER_SECRET")
    
    missing = []
    if not FATSECRET_KEY:
        missing.append("FATSECRET_CONSUMER_KEY")
    if not FATSECRET_SECRET:
        missing.append("FATSECRET_CONSUMER_SECRET")
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_KEY:
        missing.append("SUPABASE_SERVICE_ROLE_KEY or SUPABASE_SERVICE_KEY")
    
    if missing:
        logger.error(f"Missing environment variables: {', '.join(missing)}")
        sys.exit(1)
    
    # Initialiser Supabase
    supabase = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
    
    # Lancer la synchronisation
    logger.info("=" * 60)
    logger.info("FatSecret Food Entries Sync Starting")
    logger.info("=" * 60)
    
    stats = sync_all_users(
        supabase=supabase,
        days_back=args.days_back,
        user_id_filter=args.user_id
    )
    
    # Afficher les résultats
    logger.info("=" * 60)
    logger.info("Sync Complete!")
    logger.info(f"  Users synced: {stats['users_synced']}")
    logger.info(f"  Total entries: {stats['total_entries']}")
    logger.info(f"  Total days: {stats['total_days']}")
    logger.info("=" * 60)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
