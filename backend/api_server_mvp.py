"""
API Server MVP v2.0 - Minimal FastAPI pour le Nouveau MVP
Endpoints:
- POST /api/webhooks/vital : Reçoit les webhooks Vital API
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
from vital_webhook import VitalWebhookHandler
from vital_webhook_v2 import VitalWebhookHandlerV2
from jwt_auth import verify_jwt_or_uuid_token
from vital_client import get_vital_client
from webhook_logger import WebhookLogger, get_user_webhook_logs, get_all_webhook_logs
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pulse MVP v2.0 API",
    description="API minimal pour le Nouveau MVP (Vital flux + Apple Health context + LLM correlation)",
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

# Vital Client
try:
    vital_client = get_vital_client()
    logger.info("Vital client initialized")
except Exception as e:
    logger.warning(f"Vital client not initialized: {e}")
    vital_client = None

# Vital Webhook Handlers (V1 et V2)
vital_handler = VitalWebhookHandler(supabase_client)  # Ancien format (rétrocompatibilité)
vital_handler_v2 = VitalWebhookHandlerV2(supabase_client, vital_client)  # Format officiel Vital

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


@app.post("/")
async def root_webhook(request: Request):
    """
    Endpoint racine pour les webhooks (fallback)
    Redirige vers le handler Vital
    
    Certains services (comme Svix utilisé par Vital) envoient parfois 
    les webhooks à la racine. Cet endpoint les traite.
    """
    logger.info("Webhook received at root (/), processing as Vital webhook")
    
    try:
        payload = await request.json()
        
        # Détecter le format du webhook
        if "event_type" in payload and ("client_user_id" in payload or "user_id" in payload):
            # Format officiel Vital (V2)
            logger.info(f"Processing Vital webhook V2 at root: {payload.get('event_type')}")
            result = vital_handler_v2.process_webhook(payload)
        else:
            # Ancien format (V1) pour rétrocompatibilité
            logger.info("Processing Vital webhook V1 (legacy format) at root")
            result = vital_handler.process_webhook(payload)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        elif result["status"] == "accepted":
            # 202 Accepted: webhook accepté mais utilisateur non trouvé
            return {"status": "accepted", "message": result["message"]}
        
        return {"status": "success", "message": result["message"]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vital webhook error at root: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/webhooks/vital")
async def vital_webhook(request: Request):
    """
    Endpoint pour recevoir les webhooks Vital API
    
    Format officiel Vital:
    {
        "event_type": "historical.data.water.created",
        "user_id": "vital_user_id",
        "client_user_id": "supabase_uuid",
        "team_id": "team_id",
        "data": {
            "provider": "fitbit",
            "start_date": "2025-12-29T00:00:00+00:00",
            "end_date": "2026-01-27T23:59:59+00:00",
            "is_final": true
        }
    }
    
    Processus:
    1. Détecte le format (V1 ancien ou V2 officiel)
    2. Route vers le bon handler
    3. Process et log l'événement
    
    Returns:
        - 200: Succès
        - 202: Accepté mais utilisateur non trouvé (webhook accepté mais non traité)
        - 400: Payload invalide
        - 500: Erreur serveur
    """
    start_time = datetime.utcnow()
    log_id = None
    
    try:
        payload = await request.json()
        
        # Logger le webhook reçu
        event_type = payload.get("event_type")
        user_id = payload.get("user_id")
        client_user_id = payload.get("client_user_id")
        
        log_id = webhook_logger.log_webhook(
            endpoint="/api/webhooks/vital",
            payload=payload,
            event_type=event_type,
            user_id=user_id,
            client_user_id=client_user_id,
            method="POST",
            start_time=start_time
        )
        
        # Détecter le format du webhook
        if "event_type" in payload and "client_user_id" in payload:
            # Format officiel Vital (V2)
            logger.info(f"Processing Vital webhook V2: {payload.get('event_type')}")
            result = vital_handler_v2.process_webhook(payload)
        else:
            # Ancien format (V1) pour rétrocompatibilité
            logger.info("Processing Vital webhook V1 (legacy format)")
            result = vital_handler.process_webhook(payload)
        
        # Calculer la durée
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Mettre à jour le log
        if result["status"] == "error":
            webhook_logger.update_webhook_log(
                log_id=log_id,
                status_code=400,
                response_message=result["message"],
                error=result["message"],
                duration_ms=duration_ms
            )
            raise HTTPException(status_code=400, detail=result["message"])
        elif result["status"] == "accepted":
            webhook_logger.update_webhook_log(
                log_id=log_id,
                status_code=202,
                response_message=result["message"],
                duration_ms=duration_ms
            )
            # 202 Accepted: webhook accepté mais utilisateur non trouvé
            return {"status": "accepted", "message": result["message"]}
        
        # Succès
        webhook_logger.update_webhook_log(
            log_id=log_id,
            status_code=200,
            response_message=result["message"],
            duration_ms=duration_ms
        )
        
        return {"status": "success", "message": result["message"]}
        
    except HTTPException as http_exc:
        # Mettre à jour le log si erreur HTTP
        if log_id:
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            webhook_logger.update_webhook_log(
                log_id=log_id,
                status_code=http_exc.status_code,
                error=http_exc.detail,
                duration_ms=duration_ms
            )
        raise
    except Exception as e:
        logger.error(f"Vital webhook error: {e}")
        # Mettre à jour le log si erreur générique
        if log_id:
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            webhook_logger.update_webhook_log(
                log_id=log_id,
                status_code=500,
                error=str(e),
                duration_ms=duration_ms
            )
        raise HTTPException(status_code=500, detail=str(e))


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


# ============================================================================
# VITAL API ENDPOINTS
# ============================================================================

@app.post("/api/vital/create-user")
async def create_vital_user(
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    Crée un utilisateur Vital et enregistre l'identité externe
    
    Protégé par JWT Supabase (header Authorization: Bearer <token>)
    
    Processus:
    1. Vérifie le token JWT et extrait user_id
    2. Crée l'utilisateur Vital via l'API
    3. Enregistre l'identité dans external_identities (provider_system="vital")
    
    Returns:
        - 200: Utilisateur créé avec vital_user_id
        - 401: Token invalide ou manquant
        - 500: Erreur serveur
    """
    try:
        if not vital_client:
            raise HTTPException(status_code=503, detail="Vital client not configured")
        
        # Vérifier le token JWT et extraire user_id
        user_id = verify_jwt_or_uuid_token(authorization)
        
        # Vérifier si l'utilisateur Vital existe déjà
        existing_identity = supabase_client.get_user_by_external_id(
            external_user_id=user_id,
            provider_system="vital"
        )
        
        if existing_identity:
            # Récupérer l'user Vital existant
            vital_user = vital_client.get_user_by_client_id(user_id)
            if vital_user:
                return {
                    "status": "success",
                    "message": "Vital user already exists",
                    "vital_user_id": vital_user["user_id"],
                    "client_user_id": vital_user["client_user_id"]
                }
        
        # Créer l'utilisateur Vital
        vital_user = vital_client.create_user(client_user_id=user_id)
        vital_user_id = vital_user["user_id"]
        
        # Enregistrer dans external_identities
        from uuid import uuid4
        identity_data = {
            "id": str(uuid4()),
            "supabase_user_id": user_id,
            "provider_system": "vital",
            "external_user_id": vital_user_id,
            "is_active": True
        }
        
        supabase_client.client.table("external_identities").insert(identity_data).execute()
        
        logger.info(f"Vital user created: {vital_user_id} for Supabase user: {user_id}")
        
        return {
            "status": "success",
            "vital_user_id": vital_user_id,
            "client_user_id": vital_user["client_user_id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Vital user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vital/link-token")
async def generate_vital_link_token(
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    Génère un token Vital Link pour connecter des sources
    
    Protégé par JWT Supabase (header Authorization: Bearer <token>)
    
    Processus:
    1. Vérifie le token JWT et extrait user_id
    2. Récupère le vital_user_id depuis external_identities
    3. Génère un link token via l'API Vital
    
    Returns:
        - 200: Token généré avec link_token et expires_at
        - 401: Token invalide ou manquant
        - 404: Utilisateur Vital non trouvé
        - 500: Erreur serveur
    """
    try:
        if not vital_client:
            raise HTTPException(status_code=503, detail="Vital client not configured")
        
        # Vérifier le token JWT et extraire user_id
        user_id = verify_jwt_or_uuid_token(authorization)
        
        # Récupérer le vital_user_id depuis external_identities
        response = supabase_client.client.table("external_identities").select("external_user_id").eq("supabase_user_id", user_id).eq("provider_system", "vital").eq("is_active", True).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Vital user not found. Please create a Vital user first.")
        
        vital_user_id = response.data[0]["external_user_id"]
        
        # Générer le link token
        link_data = vital_client.generate_link_token(vital_user_id)
        
        logger.info(f"Link token generated for Supabase user: {user_id}, Vital user: {vital_user_id}")
        
        return {
            "status": "success",
            "link_token": link_data["link_token"],
            "expires_at": link_data.get("expires_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating link token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vital/connections")
async def get_vital_connections(
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    Liste les sources connectées pour l'utilisateur
    
    Protégé par JWT Supabase (header Authorization: Bearer <token>)
    
    Processus:
    1. Vérifie le token JWT et extrait user_id
    2. Récupère le vital_user_id depuis external_identities
    3. Liste les connexions via l'API Vital
    
    Returns:
        - 200: Liste des providers connectés
        - 401: Token invalide ou manquant
        - 404: Utilisateur Vital non trouvé
        - 500: Erreur serveur
    """
    try:
        if not vital_client:
            raise HTTPException(status_code=503, detail="Vital client not configured")
        
        # Vérifier le token JWT et extraire user_id
        user_id = verify_jwt_or_uuid_token(authorization)
        
        # Récupérer le vital_user_id depuis external_identities
        response = supabase_client.client.table("external_identities").select("external_user_id").eq("supabase_user_id", user_id).eq("provider_system", "vital").eq("is_active", True).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Vital user not found. Please create a Vital user first.")
        
        vital_user_id = response.data[0]["external_user_id"]
        
        # Récupérer les connexions
        connections = vital_client.get_user_connections(vital_user_id)
        
        logger.info(f"Retrieved {len(connections)} connections for Supabase user: {user_id}")
        
        return {
            "status": "success",
            "providers": connections
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/vital/connections/{provider_slug}")
async def disconnect_vital_provider(
    provider_slug: str,
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    Déconnecte une source pour l'utilisateur
    
    Protégé par JWT Supabase (header Authorization: Bearer <token>)
    
    Args:
        provider_slug: Slug du provider (ex: "apple_health", "fitbit")
    
    Returns:
        - 200: Provider déconnecté
        - 401: Token invalide ou manquant
        - 404: Utilisateur Vital non trouvé
        - 500: Erreur serveur
    """
    try:
        if not vital_client:
            raise HTTPException(status_code=503, detail="Vital client not configured")
        
        # Vérifier le token JWT et extraire user_id
        user_id = verify_jwt_or_uuid_token(authorization)
        
        # Récupérer le vital_user_id depuis external_identities
        response = supabase_client.client.table("external_identities").select("external_user_id").eq("supabase_user_id", user_id).eq("provider_system", "vital").eq("is_active", True).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Vital user not found")
        
        vital_user_id = response.data[0]["external_user_id"]
        
        # Déconnecter le provider
        vital_client.deregister_provider(vital_user_id, provider_slug)
        
        logger.info(f"Provider {provider_slug} disconnected for Supabase user: {user_id}")
        
        return {
            "status": "success",
            "message": f"Provider {provider_slug} disconnected"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vital/connect-demo/{provider_slug}")
async def connect_demo_provider(
    provider_slug: str,
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    Connecte un provider en mode demo/sandbox (pour tests)
    
    Disponible uniquement en sandbox. Génère des données de test.
    
    Protégé par JWT Supabase (header Authorization: Bearer <token>)
    
    Args:
        provider_slug: Slug du provider (ex: "apple_health", "fitbit", "oura")
    
    Returns:
        - 200: Provider connecté en mode demo
        - 400: Pas en environnement sandbox
        - 401: Token invalide ou manquant
        - 404: Utilisateur Vital non trouvé
        - 500: Erreur serveur
    """
    try:
        if not vital_client:
            raise HTTPException(status_code=503, detail="Vital client not configured")
        
        # Vérifier le token JWT et extraire user_id
        user_id = verify_jwt_or_uuid_token(authorization)
        
        # Récupérer le vital_user_id depuis external_identities
        response = supabase_client.client.table("external_identities").select("external_user_id").eq("supabase_user_id", user_id).eq("provider_system", "vital").eq("is_active", True).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Vital user not found. Please create a Vital user first.")
        
        vital_user_id = response.data[0]["external_user_id"]
        
        # Connecter le provider en mode demo
        result = vital_client.connect_demo_provider(vital_user_id, provider_slug)
        
        logger.info(f"Demo provider {provider_slug} connected for Supabase user: {user_id}")
        
        return {
            "status": "success",
            "message": f"Provider {provider_slug} connected in demo mode",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting demo provider: {e}")
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


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 9000))
    
    print(f"🚀 Démarrage du serveur Pulse MVP v2.0 sur http://0.0.0.0:{port}")
    print(f"📡 Endpoint webhook Vital: http://localhost:{port}/api/webhooks/vital")
    print(f"📡 Endpoint webhook logs: http://localhost:{port}/api/webhooks/logs")
    print(f"📡 Endpoint cron insight: http://localhost:{port}/api/cron/daily-insight")
    print(f"📡 Endpoint insights latest: http://localhost:{port}/api/insights/latest")
    print(f"📡 Vital endpoints:")
    print(f"   - POST /api/vital/create-user")
    print(f"   - POST /api/vital/link-token")
    print(f"   - GET /api/vital/connections")
    print(f"   - DELETE /api/vital/connections/{{provider_slug}}")
    print(f"   - POST /api/vital/connect-demo/{{provider_slug}} (sandbox only)")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
