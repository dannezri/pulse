#!/usr/bin/env python3
"""
Script de réimport des timestamps de sommeil Oura (bedtime_start, bedtime_end)

Ce script récupère les données de sommeil Oura des 30 derniers jours et
réimporte les timestamps bedtime_start et bedtime_end qui n'avaient pas été
parsés auparavant.

Usage:
    python reimport_oura_sleep_times.py --user-id <uuid> [--days 30]
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    logger.error("SUPABASE_URL or SUPABASE_SERVICE_KEY not found")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def get_oura_token(user_id: str) -> Optional[str]:
    """Récupère le token Oura de l'utilisateur depuis Supabase"""
    try:
        # Récupérer depuis external_identities avec provider_system = 'oura'
        result = supabase.table("external_identities").select("metadata").eq(
            "supabase_user_id", user_id
        ).eq("provider_system", "oura").eq("is_active", True).execute()
        
        if result.data and len(result.data) > 0:
            metadata = result.data[0].get("metadata", {})
            # Le token Oura est dans metadata->access_token
            oura_token = metadata.get("access_token")
            if oura_token:
                logger.info(f"✅ Oura token found for user {user_id}")
                return oura_token
            else:
                logger.error(f"No access_token found in metadata for user {user_id}")
                logger.error(f"Metadata keys: {list(metadata.keys())}")
                return None
        
        logger.error(f"No active Oura connection found for user {user_id}")
        return None
    except Exception as e:
        logger.error(f"Error fetching Oura token: {e}")
        return None


def fetch_oura_sleep_data(access_token: str, start_date: str, end_date: str) -> list:
    """Récupère les données de sommeil depuis l'API Oura"""
    url = "https://api.ouraring.com/v2/usercollection/sleep"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "start_date": start_date,
        "end_date": end_date
    }
    
    try:
        logger.info(f"Fetching Oura sleep data from {start_date} to {end_date}")
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        logger.error(f"Error fetching Oura sleep data: {e}")
        return []


def insert_bedtime_metric(
    user_id: str,
    metric_type: str,
    timestamp: datetime,
    source_event_id: str
):
    """Insère un timestamp de sommeil dans la table biometrics"""
    try:
        # Calculer la valeur (heure décimale)
        value = timestamp.hour + (timestamp.minute / 60.0)
        
        # Vérifier si déjà existant
        existing = supabase.table("biometrics").select("id").eq(
            "user_id", user_id
        ).eq("source_event_id", source_event_id).execute()
        
        if existing.data and len(existing.data) > 0:
            logger.debug(f"  ⏭️  {metric_type} already exists: {source_event_id}")
            return False
        
        # Insérer
        supabase.table("biometrics").insert({
            "user_id": user_id,
            "metric_type": metric_type,
            "value": value,
            "recorded_at": timestamp.isoformat(),
            "source": "oura",
            "source_event_id": source_event_id,
            "raw_data": {metric_type: timestamp.isoformat(), "source": "oura"}
        }).execute()
        
        logger.info(f"  ✅ Inserted {metric_type}: {timestamp.isoformat()} (hour: {timestamp.hour})")
        return True
    except Exception as e:
        logger.error(f"  ❌ Error inserting {metric_type}: {e}")
        return False


def reimport_sleep_times(user_id: str, days: int = 30):
    """Réimporte les timestamps de sommeil pour un utilisateur"""
    logger.info("="*60)
    logger.info(f"🔄 RÉIMPORT DES TIMESTAMPS DE SOMMEIL OURA")
    logger.info("="*60)
    logger.info(f"User ID: {user_id}")
    logger.info(f"Period: Last {days} days")
    logger.info("")
    
    # 1. Récupérer le token Oura
    oura_token = get_oura_token(user_id)
    if not oura_token:
        logger.error("Cannot proceed without Oura token")
        return
    
    # 2. Calculer les dates
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    # 3. Récupérer les données de sommeil
    sleep_records = fetch_oura_sleep_data(
        oura_token,
        start_date.isoformat(),
        end_date.isoformat()
    )
    
    if not sleep_records:
        logger.warning("No sleep records found")
        return
    
    logger.info(f"Found {len(sleep_records)} sleep records")
    logger.info("")
    
    # 4. Parser et insérer les timestamps
    inserted_count = 0
    skipped_count = 0
    
    for record in sleep_records:
        record_id = record.get("id")
        day = record.get("day")
        
        if not record_id or not day:
            continue
        
        logger.info(f"📅 Processing sleep record for {day} (ID: {record_id[:8]}...)")
        
        # bedtime_start
        bedtime_start = record.get("bedtime_start")
        if bedtime_start:
            try:
                bedtime_start_dt = datetime.fromisoformat(bedtime_start.replace("Z", "+00:00"))
                if insert_bedtime_metric(
                    user_id,
                    "bedtime_start",
                    bedtime_start_dt,
                    f"oura_bedtime_start_{record_id}"
                ):
                    inserted_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                logger.error(f"  ❌ Error parsing bedtime_start: {e}")
        
        # bedtime_end (heure de réveil)
        bedtime_end = record.get("bedtime_end")
        if bedtime_end:
            try:
                bedtime_end_dt = datetime.fromisoformat(bedtime_end.replace("Z", "+00:00"))
                if insert_bedtime_metric(
                    user_id,
                    "bedtime_end",
                    bedtime_end_dt,
                    f"oura_bedtime_end_{record_id}"
                ):
                    inserted_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                logger.error(f"  ❌ Error parsing bedtime_end: {e}")
        
        logger.info("")
    
    # 5. Résumé
    logger.info("="*60)
    logger.info("✅ RÉIMPORT TERMINÉ")
    logger.info("="*60)
    logger.info(f"Sleep records processed: {len(sleep_records)}")
    logger.info(f"Timestamps inserted: {inserted_count}")
    logger.info(f"Timestamps skipped (already exist): {skipped_count}")
    logger.info("")


def main():
    parser = argparse.ArgumentParser(description="Réimporter les timestamps de sommeil Oura")
    parser.add_argument("--user-id", required=True, help="UUID de l'utilisateur Supabase")
    parser.add_argument("--days", type=int, default=30, help="Nombre de jours à réimporter (défaut: 30)")
    
    args = parser.parse_args()
    
    reimport_sleep_times(args.user_id, args.days)


if __name__ == "__main__":
    main()
