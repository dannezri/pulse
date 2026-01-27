"""
API Server Simplifié pour l'interface Ambient Concierge
Contient uniquement les endpoints essentiels pour le nouveau système
"""

from fastapi import FastAPI, Request, HTTPException, Header
from typing import Optional
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement depuis .env (optionnel)
try:
    load_dotenv()
    logger.info("Loaded .env file")
except Exception as e:
    logger.warning(f"Could not load .env file: {e}. Using system environment variables.")

from supabase_client import SupabaseClient
from correlation_engine import CorrelationEngine
from llm_client import LLMClient
from priority_engine import PriorityEngine

app = FastAPI(title="Pulse - Ambient Concierge API")

# Initialiser les clients
supabase_client = SupabaseClient(
    supabase_url=os.getenv("SUPABASE_URL"),
    supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
)

# Correlation Engine pour le MVP
llm_client = LLMClient()
correlation_engine = CorrelationEngine(
    supabase_client=supabase_client,
    llm_client=llm_client
)

# Priority Engine pour l'interface Ambient Concierge
priority_engine = PriorityEngine(supabase_client=supabase_client)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Pulse - Ambient Concierge API",
        "version": "1.0.0"
    }


@app.get("/api/baselines/{user_id}")
async def get_user_baselines(user_id: str):
    """
    Retourne les baselines (μ, σ, poids) pour chaque métrique de l'utilisateur
    Utilisé par le mobile pour calculer les Z-Scores en temps réel
    
    Calcule sur les 14 derniers jours par défaut
    """
    try:
        logger.info(f"Fetching baselines for user {user_id}")
        
        baselines = priority_engine.calculate_baselines(user_id)
        
        if not baselines:
            # Retourner 200 avec objet vide si pas de données (pas d'erreur)
            return {
                "status": "success",
                "user_id": user_id,
                "baselines": {},
                "message": "No data available to calculate baselines"
            }
        
        return {
            "status": "success",
            "user_id": user_id,
            "baselines": baselines,
            "lookback_days": 14
        }
        
    except Exception as e:
        logger.error(f"Error fetching baselines for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/insights/prioritized")
async def generate_prioritized_insight(request: Request):
    """
    Génère un insight "Concierge" ultra-court basé sur les top 3 anomalies
    
    Body attendu:
    {
        "user_id": "uuid",
        "anomalies": [
            {"metric": "hrv", "value": 45.2, "z_score": -2.35, "weight": 3, ...},
            ...
        ]
    }
    
    Retourne un insight style "Concierge" : cause probable + action immédiate
    """
    try:
        payload = await request.json()
        user_id = payload.get("user_id")
        anomalies = payload.get("anomalies", [])
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        logger.info(f"Generating prioritized insight for user {user_id} with {len(anomalies)} anomalies")
        
        # Si aucune anomalie, retourner un insight "calm"
        if not anomalies or len(anomalies) == 0:
            return {
                "status": "success",
                "insight": {
                    "content": "Votre corps est en parfaite homéostasie. Profitez de ce pic d'énergie.",
                    "state": "calm",
                    "priority": 1
                }
            }
        
        # Prendre les top 3 anomalies
        top_anomalies = anomalies[:3]
        
        # Construire le prompt pour le LLM
        anomalies_text = []
        for anomaly in top_anomalies:
            metric = anomaly.get("metric", "unknown")
            value = anomaly.get("value", 0)
            z_score = anomaly.get("z_score", 0)
            direction = anomaly.get("direction", "")
            baseline_mean = anomaly.get("baseline", {}).get("mean", 0)
            
            anomalies_text.append(
                f"- {metric}: {value} (baseline: {baseline_mean}, écart: {z_score:.1f}σ {direction})"
            )
        
        prompt = f"""Voici les 3 seules anomalies physiologiques détectées aujourd'hui :

{chr(10).join(anomalies_text)}

Ignore tout le reste. Rédige un conseil de concierge discret en français (max 150 caractères) qui :
1. Explique la cause la plus probable de ces anomalies
2. Donne UNE action immédiate et concrète

Style : Direct, bienveillant, actionnable. Pas de jargon médical."""
        
        # Appeler le LLM
        system_prompt = """Tu es un concierge de santé expert et discret. 
Tu communiques de manière ultra-concise, bienveillante et actionnable.
Tu n'expliques que l'essentiel et tu donnes des actions immédiates."""
        
        llm_response = llm_client.generate_insight(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=200
        )
        
        content = llm_response.get("content", "")
        
        # Déterminer la priorité et l'état selon les Z-Scores
        max_z = max([abs(a.get("z_score", 0)) for a in top_anomalies])
        max_weight = max([a.get("weight", 1) for a in top_anomalies])
        
        if max_z >= 3 and max_weight >= 3:
            state = "alert"
            priority = 2
        elif max_z >= 2.5 or max_weight >= 2:
            state = "warning"
            priority = 1
        else:
            state = "calm"
            priority = 1
        
        # Sauvegarder l'insight dans la base
        supabase_client.client.table("insights").insert({
            "user_id": user_id,
            "content": content,
            "instruction_text": content,  # Compatibilité
            "category": "concierge",
            "priority": priority,
            "correlation_type": "z_score_anomaly"
        }).execute()
        
        logger.info(f"Generated prioritized insight for user {user_id}: {content[:50]}...")
        
        return {
            "status": "success",
            "insight": {
                "content": content,
                "state": state,
                "priority": priority,
                "anomalies_count": len(top_anomalies)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating prioritized insight: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/insights/latest")
async def get_latest_insight(
    user_id: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """
    Récupère le dernier insight pour un utilisateur
    Peut être appelé depuis le mobile avec user_id en query param
    """
    try:
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        # Récupérer le dernier insight
        response = supabase_client.client.table("insights").select("*").eq(
            "user_id", user_id
        ).order("created_at", desc=True).limit(1).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="No insight found")
        
        return {"status": "success", "insight": response.data[0]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest insight: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health-profile/{user_id}")
async def get_health_profile(user_id: str):
    """
    Récupère le dernier profil de santé normalisé d'un utilisateur
    """
    try:
        profile = supabase_client.get_latest_health_profile(user_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Health profile not found")
        
        return {"status": "success", "profile": profile}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching health profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/webhooks/vital")
async def vital_webhook(request: Request):
    """
    Endpoint pour recevoir les webhooks Vital API (HR, HRV, Sleep, Steps, etc.)
    
    Format Vital webhook:
    {
        "event_type": "daily.data.steps.updated",
        "client_user_id": "uuid",
        "user_id": "vital_user_id",
        "data": {
            "data": [{"value": 7639, "timestamp": "...", ...}],
            "provider": {...},
            "source": {...}
        }
    }
    """
    try:
        payload = await request.json()
        logger.info(f"Received Vital webhook: {payload.get('event_type')}")
        
        # Extraire le client_user_id (notre UUID utilisateur)
        user_id = payload.get("client_user_id")
        
        if not user_id:
            logger.error("Missing client_user_id in Vital webhook")
            raise HTTPException(status_code=400, detail="client_user_id is required")
        
        event_type = payload.get("event_type", "")
        data = payload.get("data", {})
        data_points = data.get("data", [])
        
        if not data_points or not isinstance(data_points, list):
            logger.warning(f"No data points in Vital webhook for user {user_id}")
            return {"status": "success", "message": "No data to insert"}
        
        # Mapper l'event_type Vital vers nos metric_types
        metric_type_map = {
            "daily.data.steps.updated": "steps",
            "daily.data.distance.updated": "distance",
            "daily.data.calories.updated": "calories",
            "timeseries.heartrate.updated": "hr",
            "timeseries.hrv.updated": "hrv",
            "daily.data.sleep.updated": "sleep_duration",
        }
        
        metric_type = metric_type_map.get(event_type)
        
        if not metric_type:
            logger.warning(f"Unknown event_type: {event_type}")
            return {"status": "success", "message": f"Unsupported event_type: {event_type}"}
        
        # Insérer chaque data point
        inserted_count = 0
        for point in data_points:
            value = point.get("value")
            timestamp = point.get("timestamp") or point.get("start")
            
            if value is not None and timestamp:
                try:
                    # Parser le timestamp en datetime
                    if isinstance(timestamp, str):
                        # Supporte les formats ISO 8601 avec ou sans timezone
                        recorded_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    else:
                        recorded_at = timestamp
                    
                    # Construire un source_event_id unique
                    source_event_id = f"vital_{metric_type}_{timestamp}_{value}"
                    
                    supabase_client.insert_biometric(
                        user_id=user_id,
                        metric_type=metric_type,
                        value=float(value),
                        recorded_at=recorded_at,
                        source="vital",
                        source_event_id=source_event_id,
                        raw_data=point
                    )
                    inserted_count += 1
                except Exception as e:
                    logger.error(f"Error inserting data point: {e}")
                    continue
        
        logger.info(f"Inserted {inserted_count} data points for user {user_id}")
        
        return {
            "status": "success",
            "message": f"Inserted {inserted_count} data points",
            "metric_type": metric_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vital webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    import socket
    
    def find_free_port(start_port=9000, max_attempts=10):
        """Trouve un port disponible en commençant par start_port"""
        for i in range(max_attempts):
            port = start_port + i
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('', port))
                    return port
                except OSError:
                    continue
        raise RuntimeError(f"Impossible de trouver un port libre entre {start_port} et {start_port + max_attempts}")
    
    # Port configurable via variable d'environnement, sinon trouver un port libre
    try:
        port = int(os.getenv("PORT", find_free_port()))
    except (ValueError, RuntimeError):
        port = 9000  # Fallback
    
    print(f"🚀 Démarrage de Pulse - Ambient Concierge API sur http://0.0.0.0:{port}")
    print(f"📊 Endpoints disponibles:")
    print(f"   - GET  /api/baselines/{{user_id}}")
    print(f"   - POST /api/insights/prioritized")
    print(f"   - GET  /api/insights/latest")
    print(f"   - GET  /health-profile/{{user_id}}")
    print(f"   - POST /api/webhooks/vital")
    uvicorn.run(app, host="0.0.0.0", port=port)
