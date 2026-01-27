"""
API Server pour exposer les endpoints webhook et de synchronisation
Utilise FastAPI pour une intégration facile avec les services serverless
"""

from fastapi import FastAPI, Request, HTTPException, Header
from typing import Optional
import os
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

from open_wearables_integration import OpenWearablesIntegration
from data_normalizer import DataNormalizer
from supabase_client import SupabaseClient
from webhook_receiver import WebhookReceiver
from main import DataPipeline
from correlation_engine import CorrelationEngine
from llm_client import LLMClient
from priority_engine import PriorityEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Bio-Feedback IA - Data Infrastructure")

# Initialiser les clients
open_wearables_client = OpenWearablesIntegration(
    base_url=os.getenv("OPEN_WEARABLES_BASE_URL", "http://localhost:8080"),
    api_key=os.getenv("OPEN_WEARABLES_API_KEY")
)

normalizer = DataNormalizer()

supabase_client = SupabaseClient(
    supabase_url=os.getenv("SUPABASE_URL"),
    supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
)

# Webhook Receiver : enregistre brut et pousse un job (répond vite)
webhook_receiver = WebhookReceiver(
    open_wearables_client=open_wearables_client,
    supabase_client=supabase_client
)

pipeline = DataPipeline(
    open_wearables_base_url=os.getenv("OPEN_WEARABLES_BASE_URL", "http://localhost:8080"),
    open_wearables_api_key=os.getenv("OPEN_WEARABLES_API_KEY"),
    supabase_url=os.getenv("SUPABASE_URL"),
    supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
)

# Correlation Engine pour le nouveau MVP
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
    return {"status": "ok", "service": "Bio-Feedback IA Data Infrastructure"}


@app.post("/api/webhooks/wearables")
async def open_wearables_webhook(
    request: Request,
    x_signature: Optional[str] = Header(None, alias="X-Signature")
):
    """
    Endpoint pour recevoir les webhooks Open Wearables
    
    Pattern asynchrone :
    1. Valide la signature
    2. Enregistre le webhook brut dans webhook_events
    3. Pousse un job de normalisation dans la queue
    4. Répond 200 rapidement (sans attendre la normalisation)
    
    Le worker traitera la normalisation et la mise à jour du profil de santé en arrière-plan.
    """
    try:
        payload = await request.json()
        
        # Recevoir le webhook (validation + enregistrement brut + push job)
        result = webhook_receiver.receive_webhook(payload, x_signature)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        
        # Répondre 200 rapidement (le traitement se fait en arrière-plan)
        return result
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sync/{open_wearables_user_id}")
async def sync_user_data(open_wearables_user_id: str):
    """
    Endpoint pour forcer une synchronisation manuelle des données
    Utile pour les tests ou la récupération de données historiques
    """
    try:
        result = pipeline.sync_user_data(open_wearables_user_id)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
        
    except Exception as e:
        logger.error(f"Sync error: {e}")
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
    Endpoint pour recevoir les webhooks Vital API (HR, HRV, Sleep)
    
    Format attendu (exemple):
    {
        "user_id": "uuid",
        "data": {
            "hr": [{"value": 72, "timestamp": "2024-01-15T10:00:00Z"}],
            "hrv": [{"value": 65, "timestamp": "2024-01-15T10:00:00Z"}],
            "sleep": {"duration_seconds": 28800, "start_time": "2024-01-15T22:00:00Z"}
        }
    }
    
    TODO: Valider signature si disponible
    """
    try:
        payload = await request.json()
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        data = payload.get("data", {})
        
        # Insérer les données dans biometrics
        # HR
        if "hr" in data and isinstance(data["hr"], list):
            for hr_entry in data["hr"]:
                hr_value = hr_entry.get("value")
                timestamp = hr_entry.get("timestamp")
                if hr_value and timestamp:
                    supabase_client.insert_biometric(
                        user_id=user_id,
                        metric_type="hr",
                        value=float(hr_value),
                        recorded_at=timestamp,
                        source="vital",
                        source_event_id=f"vital_{timestamp}_{hr_value}"
                    )
        
        # HRV
        if "hrv" in data and isinstance(data["hrv"], list):
            for hrv_entry in data["hrv"]:
                hrv_value = hrv_entry.get("value")
                timestamp = hrv_entry.get("timestamp")
                if hrv_value and timestamp:
                    supabase_client.insert_biometric(
                        user_id=user_id,
                        metric_type="hrv",
                        value=float(hrv_value),
                        recorded_at=timestamp,
                        source="vital",
                        source_event_id=f"vital_{timestamp}_{hrv_value}"
                    )
        
        # Sleep
        if "sleep" in data and isinstance(data["sleep"], dict):
            sleep_data = data["sleep"]
            duration_seconds = sleep_data.get("duration_seconds", 0)
            start_time = sleep_data.get("start_time")
            if duration_seconds and start_time:
                duration_minutes = int(duration_seconds / 60)
                supabase_client.insert_biometric(
                    user_id=user_id,
                    metric_type="sleep_duration",
                    value=float(duration_minutes),
                    recorded_at=start_time,
                    raw_data=sleep_data,
                    source="vital",
                    source_event_id=f"vital_sleep_{start_time}"
                )
        
        return {"status": "success", "message": "Data inserted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vital webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cron/daily-insight")
async def generate_daily_insight(
    request: Request,
    x_cron_secret: Optional[str] = Header(None, alias="X-Cron-Secret")
):
    """
    Endpoint pour générer les insights quotidiens (appelé par cron externe)
    
    Protégé par secret header X-Cron-Secret
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
            return {"status": "error", "message": "Could not generate insight"}
        
        # Insérer dans insights
        supabase_client.client.table("insights").insert({
            "user_id": user_id,
            "content": insight["content"],
            "instruction_text": insight["content"],  # Compatibilité
            "correlation_type": insight.get("correlation_type"),
            "priority": insight.get("priority", 1),
            "category": "general"  # Peut être dérivé de correlation_type
        }).execute()
        
        return {"status": "success", "insight": insight}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Daily insight generation error: {e}")
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
        # TODO: Extraire user_id depuis le token JWT si authorization header présent
        # Pour l'instant, on utilise user_id en query param
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        # Récupérer via RPC
        response = supabase_client.client.rpc(
            "get_latest_insight",
            {"p_user_id": user_id}
        ).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="No insight found")
        
        return {"status": "success", "insight": response.data[0]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest insight: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    
    print(f"🚀 Démarrage du serveur Bio-Feedback IA sur http://0.0.0.0:{port}")
    print(f"📡 Endpoint webhook: http://localhost:{port}/api/webhooks/wearables")
    uvicorn.run(app, host="0.0.0.0", port=port)
