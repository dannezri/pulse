"""
API Server MVP v2.0 - Minimal FastAPI pour le Nouveau MVP
Endpoints:
- POST /api/cron/daily-insight : Génère les insights quotidiens (protégé par secret)
- GET /api/insights/latest : Récupère le dernier insight (protégé par JWT)
"""

from fastapi import FastAPI, Request, HTTPException, Header, Depends
from typing import Optional
import os
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

from supabase_client import SupabaseClient
from correlation_engine import CorrelationEngine
from llm_client import LLMClient
from jwt_auth import verify_jwt_or_uuid_token
from webhook_logger import WebhookLogger, get_user_webhook_logs, get_all_webhook_logs
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pulse MVP v2.0 API",
    description="API minimal pour le Nouveau MVP (Apple Health context + LLM correlation)",
    version="2.0.0"
)

# Initialiser les clients
supabase_client = SupabaseClient(
    supabase_url=os.getenv("SUPABASE_URL"),
    supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
)

# Correlation Engine pour le nouveau MVP
llm_client = LLMClient()
correlation_engine = CorrelationEngine(
    supabase_client=supabase_client,
    llm_client=llm_client
)

# Webhook Logger
webhook_logger = WebhookLogger(supabase_client)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Pulse MVP v2.0 API",
        "version": "2.0.0"
    }


@app.post("/api/cron/daily-insight")
async def generate_daily_insight(
    request: Request,
    x_cron_secret: Optional[str] = Header(None, alias="X-Cron-Secret")
):
    """
    Endpoint pour générer les insights quotidiens (appelé par cron externe)
    
    Protégé par secret header X-Cron-Secret
    
    Format attendu:
    {
        "user_id": "uuid"
    }
    
    Processus:
    1. Vérifie le secret
    2. Génère un insight en corrélant:
       - 10 derniers biometrics (HR/HRV/Sleep)
       - 10 derniers daily_context (nutrition/medication/symptoms/stool)
    3. Appelle LLM (GPT-4o) via correlation_engine
    4. Insère dans insights
    
    Returns:
        - 200: Insight généré avec succès
        - 401: Secret invalide
        - 400: user_id manquant
        - 500: Erreur serveur
    """
    try:
        # Vérifier le secret
        expected_secret = os.getenv("CRON_SECRET")
        if expected_secret and x_cron_secret != expected_secret:
            raise HTTPException(status_code=401, detail="Invalid cron secret")
        
        payload = await request.json()
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        # Générer l'insight
        insight = correlation_engine.generate_correlated_insight(user_id)
        
        if not insight:
            return {
                "status": "error",
                "message": "Could not generate insight (insufficient data)"
            }
        
        # Insérer dans insights
        supabase_client.client.table("insights").insert({
            "user_id": user_id,
            "content": insight["content"],
            "instruction_text": insight["content"],  # Compatibilité
            "correlation_type": insight.get("correlation_type"),
            "priority": insight.get("priority", 1),
            "category": "general"
        }).execute()
        
        return {
            "status": "success",
            "insight": {
                "content": insight["content"],
                "correlation_type": insight.get("correlation_type"),
                "priority": insight.get("priority", 1)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Daily insight generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/insights/latest")
async def get_latest_insight(
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    Récupère le dernier insight pour l'utilisateur authentifié
    
    Protégé par JWT Supabase (header Authorization: Bearer <token>)
    
    Processus:
    1. Vérifie le token JWT
    2. Extrait user_id depuis le token
    3. Récupère le dernier insight via RPC
    
    Returns:
        - 200: Insight trouvé
        - 401: Token invalide ou manquant
        - 404: Aucun insight trouvé
        - 500: Erreur serveur
    """
    try:
        # Vérifier le token JWT et extraire user_id
        user_id = verify_jwt_or_uuid_token(authorization)
        
        # Récupérer via RPC
        response = supabase_client.client.rpc(
            "get_latest_insight",
            {"p_user_id": user_id}
        ).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="No insight found")
        
        return {
            "status": "success",
            "insight": response.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest insight: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/webhooks/logs")
async def get_webhook_logs(
    user_id: str,
    limit: int = 50
):
    """
    Récupère les logs de webhooks
    
    Query params:
        - user_id: UUID utilisateur (required)
        - limit: Nombre maximum de logs (default: 50)
    
    Returns:
        Liste des webhooks reçus avec détails
    """
    try:
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        logger.info(f"Fetching webhook logs for user {user_id}")
        
        # Récupérer les logs
        logs = get_user_webhook_logs(supabase_client, user_id, limit)
        
        return {
            "status": "success",
            "count": len(logs),
            "logs": logs
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching webhook logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/webhooks/logs/all")
async def get_all_webhooks_logs(
    limit: int = 100
):
    """
    Récupère tous les logs de webhooks (admin only)
    
    Query params:
        - limit: Nombre maximum de logs (default: 100)
    
    Returns:
        Liste de tous les webhooks reçus
        
    Note: Cet endpoint devrait être protégé par une authentification admin en production
    """
    try:
        logger.info(f"Fetching all webhook logs (limit: {limit})")
        
        # Récupérer tous les logs
        logs = get_all_webhook_logs(supabase_client, limit)
        
        return {
            "status": "success",
            "count": len(logs),
            "logs": logs
        }
        
    except Exception as e:
        logger.error(f"Error fetching all webhook logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/data/recent")
async def get_recent_data(
    user_id: str,
    limit: int = 50
):
    """
    Récupère les données récentes (biometrics, insights, meals) pour l'utilisateur
    
    Query params:
        - user_id: UUID de l'utilisateur (required)
        - limit: Nombre maximum d'entrées par type (default: 50)
    
    Returns:
        Liste combinée des dernières entrées avec type et métadonnées
    """
    try:
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        logger.info(f"Fetching recent data for user {user_id}")
        
        # Récupérer les biometrics récentes
        biometrics_response = supabase_client.client.table("biometrics")\
            .select("id, metric_type, value, recorded_at, source, created_at")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        # Récupérer les insights récentes
        insights_response = supabase_client.client.table("insights")\
            .select("id, instruction_text, category, priority, is_read, created_at")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        # Récupérer les meals récentes
        meals_response = supabase_client.client.table("meals")\
            .select("id, description, estimated_calories, glycemic_impact, created_at")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        # Combiner et formatter les données
        entries = []
        
        # Ajouter les biometrics
        for bio in biometrics_response.data:
            entries.append({
                "id": bio["id"],
                "type": "biometric",
                "subtype": bio["metric_type"],
                "value": bio["value"],
                "timestamp": bio["recorded_at"],
                "source": bio.get("source", "unknown"),
                "created_at": bio["created_at"]
            })
        
        # Ajouter les insights
        for insight in insights_response.data:
            entries.append({
                "id": insight["id"],
                "type": "insight",
                "subtype": insight.get("category", "general"),
                "content": insight["instruction_text"],
                "priority": insight.get("priority", 1),
                "is_read": insight.get("is_read", False),
                "created_at": insight["created_at"]
            })
        
        # Ajouter les meals
        for meal in meals_response.data:
            entries.append({
                "id": meal["id"],
                "type": "meal",
                "subtype": meal.get("glycemic_impact", "unknown"),
                "content": meal.get("description", "Repas"),
                "calories": meal.get("estimated_calories"),
                "created_at": meal["created_at"]
            })
        
        # Trier par created_at (plus récent d'abord)
        entries.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Limiter au total demandé
        entries = entries[:limit]
        
        return {
            "status": "success",
            "count": len(entries),
            "entries": entries
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recent data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 9000))
    
    print(f"🚀 Démarrage du serveur Pulse MVP v2.0 sur http://0.0.0.0:{port}")
    print(f"📡 Endpoint webhook logs: http://localhost:{port}/api/webhooks/logs")
    print(f"📡 Endpoint cron insight: http://localhost:{port}/api/cron/daily-insight")
    print(f"📡 Endpoint insights latest: http://localhost:{port}/api/insights/latest")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
