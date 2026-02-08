"""
FoodLogService - Orchestration journal alimentaire
Gère création/lecture/sync des repas entre Supabase ↔ FatSecret
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import date, datetime, timedelta
from uuid import UUID

from supabase import Client as SupabaseClient
from fatsecret_client_v2 import FatSecretClient

logger = logging.getLogger(__name__)


class FoodLogService:
    """Service d'orchestration pour le journal alimentaire MVP"""
    
    def __init__(self, supabase: SupabaseClient, fatsecret: FatSecretClient):
        self.supabase = supabase
        self.fatsecret = fatsecret
    
    # =====================================================
    # PROVISION PROFIL FATSECRET
    # =====================================================
    
    def provision_fatsecret_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Crée automatiquement un profil FatSecret si absent
        
        Returns:
            {"status": "ok|exists", "fatsecret_profile": "active|created"}
        """
        logger.info(f"Provisioning FatSecret profile for user {user_id}")
        
        # Vérifier si profil existe déjà
        existing = self.supabase.table("fatsecret_profiles")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("is_active", True)\
            .execute()
        
        if existing.data:
            logger.info(f"Profile already exists for user {user_id}")
            return {
                "status": "exists",
                "fatsecret_profile": "active"
            }
        
        # Créer profil FatSecret
        profile = self.fatsecret.create_profile(user_id=user_id)
        
        # Stocker dans Supabase
        self.supabase.table("fatsecret_profiles").insert({
            "user_id": user_id,
            "oauth_token": profile["auth_token"],
            "oauth_token_secret": profile["auth_secret"],
            "is_active": True,
            "metadata": {"profile_id": profile.get("profile_id")}
        }).execute()
        
        logger.info(f"Profile created for user {user_id}")
        return {
            "status": "created",
            "fatsecret_profile": "active"
        }
    
    # =====================================================
    # RECHERCHE ALIMENTS
    # =====================================================
    
    def search_foods(self, query: str, page: int = 0, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Recherche d'aliments (wrapper UI-ready)
        
        Returns:
            [{"fs_food_id": 123, "name": "Pâtes complètes", "brand": null, "description": "..."}]
        """
        logger.info(f"Searching foods: '{query}' (page {page})")
        
        results = self.fatsecret.search_foods(query, page=page)
        
        # Parser et normaliser
        foods_raw = results.get("foods", {}).get("food", [])
        if isinstance(foods_raw, dict):
            foods_raw = [foods_raw]
        
        foods = []
        for f in foods_raw[:max_results]:
            foods.append({
                "fs_food_id": int(f.get("food_id", 0)),
                "name": f.get("food_name", ""),
                "brand": f.get("brand_name"),
                "description": f.get("food_description", ""),
                "type": f.get("food_type", "generic")
            })
        
        logger.info(f"Found {len(foods)} foods")
        return foods
    
    def get_food_details(self, food_id: int) -> Dict[str, Any]:
        """
        Détails aliment + servings (pour UI portion picker)
        
        Returns:
            {"food_id": 123, "name": "...", "servings": [{...}], "nutrition": {...}}
        """
        logger.info(f"Fetching food details: {food_id}")
        
        result = self.fatsecret.get_food(food_id)
        
        # Parser servings
        food_data = result.get("food", {})
        servings_raw = food_data.get("servings", {}).get("serving", [])
        if isinstance(servings_raw, dict):
            servings_raw = [servings_raw]
        
        servings = []
        for s in servings_raw:
            servings.append({
                "serving_id": int(s.get("serving_id", 0)),
                "serving_description": s.get("serving_description", ""),
                "metric_serving_amount": s.get("metric_serving_amount"),
                "metric_serving_unit": s.get("metric_serving_unit"),
                "calories": s.get("calories"),
                "protein": s.get("protein"),
                "carbohydrate": s.get("carbohydrate"),
                "fat": s.get("fat"),
                "fiber": s.get("fiber")
            })
        
        return {
            "food_id": int(food_data.get("food_id", 0)),
            "fs_food_id": int(food_data.get("food_id", 0)),  # Pour cohérence avec search
            "name": food_data.get("food_name", ""),
            "brand": food_data.get("brand_name"),
            "servings": servings,
            "raw": food_data
        }
    
    # =====================================================
    # AJOUTER REPAS (CREATE LOG + SYNC FATSECRET)
    # =====================================================
    
    def create_food_log(
        self,
        user_id: str,
        logged_at: datetime,
        meal_type: str,
        items: List[Dict[str, Any]],
        note: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        source: str = "search"
    ) -> Dict[str, Any]:
        """
        Créer un repas (log Supabase + sync FatSecret)
        
        Args:
            user_id: UUID utilisateur
            logged_at: Timestamp du repas
            meal_type: breakfast|lunch|dinner|snack
            items: [{"fs_food_id":123, "fs_serving_id":456, "quantity":1.5, "name":"..."}]
            note: Note utilisateur optionnelle
            context: Contexte personnalisé (hunger, mood, location...)
            source: search|manual|photo|import
        
        Returns:
            {"food_log_id": "...", "items_count": 3, "fs_sync_status": "synced"}
        """
        logger.info(f"Creating food log for user {user_id}: {meal_type} with {len(items)} items")
        
        # 1. Créer food_log dans Supabase
        log_data = {
            "user_id": user_id,
            "logged_at": logged_at.isoformat(),
            "meal_type": meal_type,
            "source": source,
            "note": note,
            "context": context or {},
            "fs_sync_status": "pending"
        }
        
        log_result = self.supabase.table("food_logs").insert(log_data).execute()
        food_log_id = log_result.data[0]["id"]
        
        # 2. Créer food_log_items
        items_data = []
        for item in items:
            items_data.append({
                "food_log_id": food_log_id,
                "name": item.get("name", "Unknown"),
                "quantity": item.get("quantity", 1.0),
                "unit": item.get("unit", "serving"),
                "fs_food_id": item.get("fs_food_id"),
                "fs_serving_id": item.get("fs_serving_id"),
                "nutrition": item.get("nutrition", {}),
                "raw": item.get("raw", {})
            })
        
        self.supabase.table("food_log_items").insert(items_data).execute()
        
        # 3. Sync FatSecret (best effort)
        fs_status = "pending"
        fs_entry_ids = []
        fs_error = None
        
        try:
            fs_entry_ids = self._sync_log_to_fatsecret(
                user_id=user_id,
                logged_at=logged_at,
                meal_type=meal_type,
                items=items
            )
            fs_status = "synced"
            logger.info(f"FatSecret sync successful: {len(fs_entry_ids)} entries")
        except Exception as e:
            fs_status = "error"
            fs_error = str(e)
            logger.error(f"FatSecret sync failed: {e}")
        
        # 4. Update sync status
        self.supabase.table("food_logs").update({
            "fs_sync_status": fs_status,
            "fs_food_entry_ids": fs_entry_ids,
            "fs_synced_at": datetime.utcnow().isoformat() if fs_status == "synced" else None,
            "fs_error": fs_error
        }).eq("id", food_log_id).execute()
        
        return {
            "food_log_id": food_log_id,
            "items_count": len(items),
            "fs_sync_status": fs_status,
            "fs_entry_ids": fs_entry_ids
        }
    
    def _sync_log_to_fatsecret(
        self,
        user_id: str,
        logged_at: datetime,
        meal_type: str,
        items: List[Dict[str, Any]]
    ) -> List[int]:
        """
        Crée les entrées FatSecret pour un log
        Retourne les food_entry_id FatSecret créés
        """
        # Récupérer tokens OAuth du profil
        profile = self.supabase.table("fatsecret_profiles")\
            .select("oauth_token, oauth_token_secret")\
            .eq("user_id", user_id)\
            .eq("is_active", True)\
            .single()\
            .execute()
        
        if not profile.data:
            raise ValueError(f"No active FatSecret profile for user {user_id}")
        
        auth_token = profile.data["oauth_token"]
        auth_secret = profile.data["oauth_token_secret"]
        
        # Créer client authentifié
        user_client = FatSecretClient(
            client_id=self.fatsecret.client_id,
            client_secret=self.fatsecret.client_secret,
            oauth_token=auth_token,
            oauth_secret=auth_secret
        )
        
        # Créer une entrée FatSecret par item
        entry_ids = []
        for item in items:
            if not item.get("fs_food_id") or not item.get("fs_serving_id"):
                logger.warning(f"Skipping item without FatSecret IDs: {item.get('name')}")
                continue
            
            try:
                entry = user_client.create_food_entry(
                    food_id=int(item["fs_food_id"]),
                    serving_id=int(item["fs_serving_id"]),
                    num_servings=float(item.get("quantity", 1.0)),
                    meal=meal_type,
                    date=logged_at.date()
                )
                
                if entry.get("food_entry_id"):
                    entry_ids.append(int(entry["food_entry_id"]))
            except Exception as e:
                logger.error(f"Failed to create FatSecret entry for item {item.get('name')}: {e}")
        
        return entry_ids
    
    # =====================================================
    # LIRE JOURNAL (SOURCE SUPABASE + OPTION SYNC FS)
    # =====================================================
    
    def get_food_diary(
        self,
        user_id: str,
        date_obj: date,
        force_sync: bool = False
    ) -> Dict[str, Any]:
        """
        Récupère le journal alimentaire d'une date
        Priorise Supabase (rapide), option force_sync pour rafraîchir depuis FatSecret
        
        Returns:
            {
                "date": "2026-01-29",
                "meals": {
                    "breakfast": [{log}, ...],
                    "lunch": [...],
                    "dinner": [...],
                    "snack": [...]
                },
                "total_nutrition": {...},
                "source": "cache|fatsecret"
            }
        """
        logger.info(f"Fetching diary for user {user_id} on {date_obj} (force_sync={force_sync})")
        
        # Si force_sync, récupérer depuis FatSecret et mettre à jour cache
        if force_sync:
            self._sync_diary_from_fatsecret(user_id, date_obj)
        
        # Lire depuis Supabase
        start_dt = datetime.combine(date_obj, datetime.min.time())
        end_dt = datetime.combine(date_obj, datetime.max.time())
        
        logs = self.supabase.table("food_logs")\
            .select("*, food_log_items(*), food_photos(*)")\
            .eq("user_id", user_id)\
            .gte("logged_at", start_dt.isoformat())\
            .lte("logged_at", end_dt.isoformat())\
            .order("logged_at")\
            .execute()
        
        # Organiser par type de repas
        meals = {
            "breakfast": [],
            "lunch": [],
            "dinner": [],
            "snack": []
        }
        
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        
        for log in logs.data:
            meal_type = log["meal_type"]
            
            # Calculer nutrition totale du log
            log_nutrition = {"calories": 0, "protein": 0, "carbohydrate": 0, "fat": 0}
            for item in log.get("food_log_items", []):
                item_nutrition = item.get("nutrition", {})
                log_nutrition["calories"] += float(item_nutrition.get("calories", 0))
                log_nutrition["protein"] += float(item_nutrition.get("protein", 0))
                log_nutrition["carbohydrate"] += float(item_nutrition.get("carbohydrate", 0))
                log_nutrition["fat"] += float(item_nutrition.get("fat", 0))
            
            total_calories += log_nutrition["calories"]
            total_protein += log_nutrition["protein"]
            total_carbs += log_nutrition["carbohydrate"]
            total_fat += log_nutrition["fat"]
            
            meals[meal_type].append({
                "id": log["id"],
                "logged_at": log["logged_at"],
                "note": log.get("note"),
                "context": log.get("context", {}),
                "items": log.get("food_log_items", []),
                "photos": log.get("food_photos", []),
                "nutrition": log_nutrition,
                "fs_sync_status": log.get("fs_sync_status")
            })
        
        return {
            "date": date_obj.isoformat(),
            "meals": meals,
            "total_nutrition": {
                "calories": round(total_calories, 1),
                "protein": round(total_protein, 1),
                "carbohydrate": round(total_carbs, 1),
                "fat": round(total_fat, 1)
            },
            "source": "fatsecret" if force_sync else "cache"
        }
    
    def _sync_diary_from_fatsecret(self, user_id: str, date_obj: date):
        """
        Récupère les entrées FatSecret et met à jour le cache Supabase
        (Pour réconciliation / rafraîchissement)
        """
        logger.info(f"Syncing diary from FatSecret for user {user_id} on {date_obj}")
        
        # Récupérer profile
        profile = self.supabase.table("fatsecret_profiles")\
            .select("oauth_token, oauth_token_secret")\
            .eq("user_id", user_id)\
            .eq("is_active", True)\
            .single()\
            .execute()
        
        if not profile.data:
            logger.warning(f"No active FatSecret profile for user {user_id}")
            return
        
        auth_token = profile.data["oauth_token"]
        auth_secret = profile.data["oauth_token_secret"]
        
        # Client authentifié
        user_client = FatSecretClient(
            client_id=self.fatsecret.client_id,
            client_secret=self.fatsecret.client_secret,
            oauth_token=auth_token,
            oauth_secret=auth_secret
        )
        
        # Récupérer entrées FatSecret
        entries_data = user_client.get_food_entries_for_date(date_obj)
        entries = user_client.parse_food_entries(entries_data)
        
        logger.info(f"Found {len(entries)} entries on FatSecret for {date_obj}")
        
        # TODO: Implémenter logique de réconciliation intelligente
        # Pour MVP, on met juste à jour food_entries_raw
        for entry in entries:
            self.supabase.table("food_entries_raw").upsert({
                "user_id": user_id,
                "fatsecret_food_entry_id": entry.get("food_entry_id"),
                "entry_date": date_obj.isoformat(),
                "meal": entry.get("meal", "other"),
                "description": entry.get("food_entry_description"),
                "food_id": entry.get("food_id"),
                "serving_id": entry.get("serving_id"),
                "number_of_units": entry.get("number_of_units"),
                "raw": entry
            }).execute()
    
    # =====================================================
    # RÉCONCILIATION (CRON / RETRY FAILED SYNCS)
    # =====================================================
    
    def reconcile_pending_syncs(self, user_id: Optional[str] = None, days_back: int = 7) -> Dict[str, Any]:
        """
        Réessaie les syncs FatSecret en erreur ou pending
        
        Args:
            user_id: Si spécifié, uniquement pour cet utilisateur
            days_back: Nombre de jours à réconcilier
        
        Returns:
            {"reconciled": 5, "failed": 1, "users": [...]}
        """
        logger.info(f"Starting reconciliation (user_id={user_id}, days_back={days_back})")
        
        # Récupérer les logs à réconcilier
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        
        query = self.supabase.table("food_logs")\
            .select("*, food_log_items(*)")\
            .in_("fs_sync_status", ["pending", "error"])\
            .gte("logged_at", cutoff.isoformat())
        
        if user_id:
            query = query.eq("user_id", user_id)
        
        logs = query.execute()
        
        reconciled = 0
        failed = 0
        users_affected = set()
        
        for log in logs.data:
            try:
                # Réessayer sync
                fs_entry_ids = self._sync_log_to_fatsecret(
                    user_id=log["user_id"],
                    logged_at=datetime.fromisoformat(log["logged_at"]),
                    meal_type=log["meal_type"],
                    items=log["food_log_items"]
                )
                
                # Update status
                self.supabase.table("food_logs").update({
                    "fs_sync_status": "synced",
                    "fs_food_entry_ids": fs_entry_ids,
                    "fs_synced_at": datetime.utcnow().isoformat(),
                    "fs_error": None
                }).eq("id", log["id"]).execute()
                
                reconciled += 1
                users_affected.add(log["user_id"])
                logger.info(f"Reconciled log {log['id']}")
                
            except Exception as e:
                # Update error
                self.supabase.table("food_logs").update({
                    "fs_error": str(e)
                }).eq("id", log["id"]).execute()
                
                failed += 1
                logger.error(f"Failed to reconcile log {log['id']}: {e}")
        
        result = {
            "reconciled": reconciled,
            "failed": failed,
            "users": list(users_affected)
        }
        
        logger.info(f"Reconciliation complete: {result}")
        return result
