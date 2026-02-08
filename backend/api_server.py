"""
API Server pour exposer les endpoints webhook et de synchronisation
Utilise FastAPI pour une intégration facile avec les services serverless
"""

from fastapi import FastAPI, Request, HTTPException, Header, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional, List
from pydantic import BaseModel
import os
import logging
import asyncio
from datetime import date, datetime, timezone
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

from legacy.open_wearables_integration import OpenWearablesIntegration
from legacy.data_normalizer import DataNormalizer
from supabase_client import SupabaseClient
from legacy.webhook_receiver import WebhookReceiver
from legacy.main import DataPipeline
from correlation_engine import CorrelationEngine
from llm_client import LLMClient
from gemini_client import GeminiThinkingClient
from priority_engine import PriorityEngine
from services.ai_service import AIAnalysisService
from services.food_log_service import FoodLogService
from services.photo_service import PhotoService
from baseline_calculator import BaselineCalculator
from icd11_client import get_icd11_client
from jwt_auth import verify_jwt_token
from fatsecret_client import get_fatsecret_client
from fatsecret_client_v2 import FatSecretClient
from ml_optimizer import MLOptimizer
from explain_service import EnergyExplainService
from medication_analysis_service import MedicationAnalysisService
from medication_comparative_analysis_service import MedicationComparativeAnalysisService
from giygas_medication_service import GiygasMedicationService

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

# ML Optimizer pour l'apprentissage adaptatif
ml_optimizer = MLOptimizer(supabase_client=supabase_client.client)

# Giygas Medication Service (API Giygas - source unique pour médicaments)
medication_service = GiygasMedicationService(supabase_client=supabase_client)

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

# Correlation Engine pour le nouveau MVP (utilise encore GPT-4o)
llm_client = LLMClient()
correlation_engine = CorrelationEngine(
    supabase_client=supabase_client,
    llm_client=llm_client
)

# Gemini Client pour le Why-Stack avec mode thinking
try:
    gemini_client = GeminiThinkingClient()
    logger.info("✅ Gemini client initialized for Energy Explain Service")
except Exception as e:
    logger.warning(f"⚠️ Could not initialize Gemini client: {e}")
    logger.info("📝 Make sure GOOGLE_API_KEY is set in environment")
    gemini_client = None

# Energy Explain Service pour le Why-Stack (utilise Gemini avec mode thinking)
if gemini_client:
    energy_explain_service = EnergyExplainService(
        supabase_client=supabase_client,
        gemini_client=gemini_client
    )
    logger.info("✅ Energy Explain Service initialized with Gemini Thinking mode")
else:
    logger.warning("⚠️ Energy Explain Service not available (missing Gemini client)")
    energy_explain_service = None

# Medication Analysis Service (utilise Gemini 3 Pro pour analyser les médicaments)
if gemini_client:
    medication_analysis_service = MedicationAnalysisService(
        supabase_client=supabase_client,
        gemini_client=gemini_client
    )
    logger.info("✅ Medication Analysis Service initialized with Gemini 3 Pro")
    
    # Medication Comparative Analysis Service pour analyse détaillée des changements
    medication_comparative_service = MedicationComparativeAnalysisService(
        supabase_client=supabase_client.client,
        gemini_client=gemini_client
    )
    logger.info("✅ Medication Comparative Analysis Service initialized")
else:
    logger.warning("⚠️ Medication Analysis Service not available (missing Gemini client)")
    medication_analysis_service = None
    medication_comparative_service = None

# Priority Engine pour l'interface Ambient Concierge
priority_engine = PriorityEngine(supabase_client=supabase_client)

# AI Analysis Service pour le Smart Cache
ai_service = AIAnalysisService(
    supabase_client=supabase_client,
    llm_client=llm_client
)

# Baseline Calculator pour les baselines personnelles
baseline_calculator = BaselineCalculator(supabase_client=supabase_client)

# ICD-11 Client pour la terminologie médicale
icd11_client = get_icd11_client(supabase_client=supabase_client)

# Food Log Service pour le journal alimentaire MVP
fatsecret_v2_client = FatSecretClient(
    client_id=os.getenv("FATSECRET_CONSUMER_KEY"),
    client_secret=os.getenv("FATSECRET_CONSUMER_SECRET")
)
food_log_service = FoodLogService(
    supabase=supabase_client.client,
    fatsecret=fatsecret_v2_client
)

# Photo Service pour les photos de repas
photo_service = PhotoService(
    supabase=supabase_client.client,
    fatsecret=fatsecret_v2_client,
    storage_bucket="food-photos"
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "Bio-Feedback IA Data Infrastructure"}


@app.get("/health")
async def health_check():
    """Health check endpoint (alias)"""
    return {"status": "healthy", "service": "Bio-Feedback IA"}


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


@app.post("/api/v1/analyze-event")
async def analyze_event(request: Request):
    """
    Analyse IA d'un événement du calendrier avec Smart Cache
    
    Body:
    {
        "user_id": "uuid",
        "event": {
            "title": "Réunion",
            "start": "2024-01-15T10:00:00Z",
            "end": "2024-01-15T11:00:00Z",
            "location": "Bureau",
            "notes": "..."
        },
        "force_refresh": false
    }
    
    Retourne:
    {
        "status": "success",
        "insight": "# Diagnostic Flash...",
        "cached": false,
        "analyzed_at": "2024-01-15T09:30:00Z",
        "biometrics_ref_at": "2024-01-15T09:25:00Z"
    }
    
    Logique de Smart Cache :
    - Si force_refresh=False ET insight existe ET pas de nouvelles données biométriques
      → Retourne le cache (instantané, 0€)
    - Sinon → Appel OpenAI et sauvegarde (quelques secondes, ~0.01€)
    """
    try:
        payload = await request.json()
        
        # Validation
        user_id = payload.get("user_id")
        event_data = payload.get("event", {})
        force_refresh = payload.get("force_refresh", False)
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        if not event_data.get("title") or not event_data.get("start"):
            raise HTTPException(status_code=400, detail="event.title and event.start are required")
        
        logger.info(f"[analyze-event] user={user_id}, event={event_data.get('title')}, force={force_refresh}")
        
        # Timeout de 15 secondes pour éviter blocage
        try:
            # Appel synchrone dans un executor pour éviter de bloquer
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    ai_service.analyze_event,
                    user_id,
                    event_data,
                    force_refresh
                ),
                timeout=15.0
            )
        except asyncio.TimeoutError:
            logger.error(f"[analyze-event] Timeout après 15 secondes pour user {user_id}")
            raise HTTPException(
                status_code=504,
                detail="L'analyse a pris trop de temps. Réessayez dans quelques instants."
            )
        
        # Si erreur dans le service, retourner 500
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message", "Unknown error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[analyze-event] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/generate-brief")
async def generate_brief(request: Request):
    """
    Génère le Brief quotidien avec le Wellness Coach IA
    
    Body:
    {
        "user_id": "uuid",
        "force_refresh": false
    }
    
    Retourne:
    {
        "status": "success",
        "cards": [
            {
                "id": "verdict",
                "type": "verdict",
                "title": "Le bilan du coach",
                "content": "Message en Markdown...",
                "state": "optimal" | "warning" | "alert" | "neutral",
                "iconName": "Activity",
                "badge": 58,
                "priority": 100,
                "actionButton": {
                    "label": "Voir détails",
                    "action": "view_details"
                }
            }
        ],
        "pulseScore": 58,
        "cached": false,
        "analyzed_at": "2024-01-15T09:30:00Z"
    }
    
    Logique de Smart Cache :
    - Si force_refresh=False ET brief existe pour aujourd'hui ET pas de nouvelles données biométriques
      → Retourne le cache (instantané, 0€)
    - Sinon → Appel OpenAI et sauvegarde (quelques secondes, ~0.01€)
    """
    try:
        payload = await request.json()
        
        # Validation
        user_id = payload.get("user_id")
        force_refresh = payload.get("force_refresh", False)
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        logger.info(f"[generate-brief] user={user_id}, force={force_refresh}")
        
        # Timeout de 45 secondes pour le Brief complet (incluant appel OpenAI)
        try:
            # Appel synchrone dans un executor pour éviter de bloquer
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    ai_service.generate_brief,
                    user_id,
                    force_refresh
                ),
                timeout=45.0
            )
        except asyncio.TimeoutError:
            logger.error(f"[generate-brief] Timeout après 45 secondes pour user {user_id}")
            raise HTTPException(
                status_code=504,
                detail="La génération du Brief a pris trop de temps (>45s). Réessayez dans quelques instants."
            )
        
        # Si erreur dans le service, retourner 500
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message", "Unknown error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[generate-brief] Error: {e}")
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


@app.post("/api/baselines/calculate/{user_id}")
async def calculate_user_baselines(
    user_id: str,
    x_cron_secret: Optional[str] = Header(None)
):
    """
    Calcule toutes les baselines pour un utilisateur
    
    Sécurité:
    - Si x_cron_secret fourni: vérifie le secret (appelé par cron)
    - Sinon: TODO vérifier JWT utilisateur
    
    Args:
        user_id: UUID de l'utilisateur
        x_cron_secret: Secret partagé pour authentification cron
    
    Returns:
        Dict avec status et baselines calculées
    """
    try:
        # Vérifier secret (si appelé par cron)
        if x_cron_secret:
            expected_secret = os.getenv("CRON_SECRET")
            if not expected_secret or x_cron_secret != expected_secret:
                raise HTTPException(status_code=403, detail="Invalid cron secret")
        else:
            # TODO: Implémenter vérification JWT si on permet aux users de déclencher
            pass
        
        logger.info(f"Calculating baselines for user {user_id}")
        
        # Calculer toutes les baselines
        results = {}
        baseline_types = [
            'sleep',
            'hrv',
            'caffeine_sensitivity',
            'alcohol_sensitivity',
            'recovery_time',
            'late_meal_impact',
            'chronotype'
        ]
        
        for baseline_type in baseline_types:
            method_name = f"calculate_{baseline_type}_baseline"
            if hasattr(baseline_calculator, method_name):
                method = getattr(baseline_calculator, method_name)
                results[baseline_type] = method(user_id)
            else:
                logger.warning(f"Method {method_name} not found")
                results[baseline_type] = {
                    'baseline_data': {
                        'value': 0,
                        'unit': '',
                        'normal_range': {'min': 0, 'max': 0},
                        'trend': {'slope_per_week': 0, 'direction': 'flat'},
                        'details': {}
                    },
                    'confidence': 0.0,
                    'sample_size': 0,
                    'status': 'error',
                    'error_message': f'Method {method_name} not implemented',
                    'window_start': '',
                    'window_end': ''
                }
        
        # Sauvegarder dans user_baselines (UPSERT)
        for baseline_type, data in results.items():
            try:
                supabase_client.client.table('user_baselines').upsert({
                    'user_id': user_id,
                    'baseline_type': baseline_type,
                    'baseline_data': data['baseline_data'],
                    'confidence': data.get('confidence', 0.0),
                    'sample_size': data.get('sample_size', 0),
                    'model_version': 'v1',
                    'window_start': data.get('window_start'),
                    'window_end': data.get('window_end'),
                    'status': data.get('status', 'ok'),
                    'error_message': data.get('error_message')
                }, on_conflict='user_id,baseline_type').execute()
                
                logger.info(f"Saved baseline {baseline_type} for user {user_id}: status={data['status']}")
            except Exception as e:
                logger.error(f"Error saving baseline {baseline_type} for user {user_id}: {e}")
        
        return {"status": "success", "baselines": results}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating baselines for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/baselines/recalculate-active")
async def recalculate_active_baselines(
    x_cron_secret: str = Header(None),
    batch_size: int = 50
):
    """
    Recalcule les baselines pour tous les utilisateurs actifs (endpoint batch)
    
    Recommandé pour production (scalable)
    Traite en batch pour éviter les timeouts
    
    Sécurité:
    - Nécessite X-Cron-Secret header
    
    Args:
        x_cron_secret: Secret partagé pour authentification cron
        batch_size: Nombre d'utilisateurs à traiter par batch
    
    Returns:
        Dict avec statistiques de traitement
    """
    try:
        # Vérifier secret
        expected_secret = os.getenv("CRON_SECRET")
        if not expected_secret or x_cron_secret != expected_secret:
            raise HTTPException(status_code=403, detail="Invalid cron secret")
        
        logger.info("Starting batch baseline recalculation for active users")
        
        # Récupérer tous les users actifs (ont des données récentes)
        # Pour l'instant: tous les users dans profiles
        response = supabase_client.client.table('profiles').select('id').execute()
        users = response.data if response.data else []
        
        results = {
            "total_users": len(users),
            "processed": 0,
            "failed": 0,
            "errors": []
        }
        
        # Traiter par batch
        for i in range(0, len(users), batch_size):
            batch = users[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} users")
            
            for user in batch:
                user_id = user['id']
                try:
                    # Calculer toutes les baselines pour cet utilisateur
                    baseline_types = [
                        'sleep',
                        'hrv',
                        'caffeine_sensitivity',
                        'alcohol_sensitivity',
                        'recovery_time',
                        'late_meal_impact',
                        'chronotype'
                    ]
                    
                    for baseline_type in baseline_types:
                        method_name = f"calculate_{baseline_type}_baseline"
                        if hasattr(baseline_calculator, method_name):
                            method = getattr(baseline_calculator, method_name)
                            data = method(user_id)
                            
                            # Sauvegarder
                            supabase_client.client.table('user_baselines').upsert({
                                'user_id': user_id,
                                'baseline_type': baseline_type,
                                'baseline_data': data['baseline_data'],
                                'confidence': data.get('confidence', 0.0),
                                'sample_size': data.get('sample_size', 0),
                                'model_version': 'v1',
                                'window_start': data.get('window_start'),
                                'window_end': data.get('window_end'),
                                'status': data.get('status', 'ok'),
                                'error_message': data.get('error_message')
                            }, on_conflict='user_id,baseline_type').execute()
                    
                    results['processed'] += 1
                    
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({
                        'user_id': user_id,
                        'error': str(e)
                    })
                    logger.error(f"Error processing user {user_id}: {e}")
            
            # Pause entre batches (éviter surcharge DB)
            if i + batch_size < len(users):
                await asyncio.sleep(1)
        
        logger.info(f"Batch recalculation complete: {results['processed']} processed, {results['failed']} failed")
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch baseline recalculation: {e}")
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


# ============================================
# ENDPOINTS TERMINOLOGIE MÉDICALE (ICD-11)
# ============================================

@app.get("/api/terminology/icd11/search")
async def search_icd11(
    q: str,
    lang: str = "fr",
    consumer_friendly: bool = True
):
    """
    Recherche de codes ICD-11 par mot-clé
    
    Args:
        q: Terme de recherche (ex: "depression", "TDAH", "SOP")
        lang: Code langue (fr, en) - défaut: fr
        consumer_friendly: Retourner format grand public avec suggestions (défaut: True)
    
    Returns (si consumer_friendly=True):
        {
            "system": "icd11",
            "query": "depression",
            "suggestions": [
                {
                    "label": "Dépression",
                    "codes": ["6A70", "6A71"],
                    "category": "mental",
                    "kind": "consumer"
                }
            ],
            "results": [
                {
                    "code": "6A70",
                    "display": "Épisode dépressif",
                    "category": "Troubles mentaux"
                }
            ],
            "more_results": true
        }
        
    Returns (si consumer_friendly=False):
        {
            "system": "icd11",
            "query": "depression",
            "count": 5,
            "results": [...]
        }
    """
    try:
        if not q or len(q.strip()) < 2:
            raise HTTPException(
                status_code=400, 
                detail="Query must be at least 2 characters"
            )
        
        search_result = icd11_client.search(
            query=q,
            lang=lang,
            use_cache=True,
            consumer_friendly=consumer_friendly
        )
        
        # Si consumer_friendly, le résultat est déjà formaté
        if consumer_friendly:
            return {
                "system": "icd11",
                **search_result
            }
        else:
            # Format legacy
            return {
                "system": "icd11",
                "query": q,
                "count": len(search_result),
                "results": search_result
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching ICD-11: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profile/conditions")
async def get_user_conditions(
    authorization: Optional[str] = Header(None)
):
    """
    Récupère les conditions de santé de l'utilisateur connecté
    
    Returns:
        {
            "status": "success",
            "count": 2,
            "conditions": [
                {
                    "id": "uuid",
                    "system": "icd11",
                    "code": "6A70",
                    "display": "TDAH",
                    "category": "Troubles mentaux",
                    "severity": null,
                    "diagnosed": null,
                    "noted_at": "2026-01-29T12:00:00Z"
                },
                ...
            ]
        }
    """
    try:
        # Vérifier le token JWT et extraire user_id
        user_id = verify_jwt_token(authorization=authorization)
        
        # Récupérer les conditions via RPC
        response = supabase_client.client.rpc(
            "get_user_conditions",
            {"p_user_id": user_id}
        ).execute()
        
        conditions = response.data if response.data else []
        
        return {
            "status": "success",
            "count": len(conditions),
            "conditions": conditions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user conditions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/profile/conditions")
async def add_user_condition(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Ajoute une condition de santé pour l'utilisateur connecté
    
    Body:
        {
            "system": "icd11",
            "code": "6A70",
            "display": "Trouble déficitaire de l'attention avec hyperactivité",
            "category": "Troubles mentaux",
            "severity": "moderate",  // optional: "mild", "moderate", "severe"
            "diagnosed": true  // optional
        }
    
    Returns:
        {
            "status": "success",
            "condition": { ... }
        }
    """
    try:
        # Vérifier le token JWT et extraire user_id
        user_id = verify_jwt_token(authorization=authorization)
        
        # Parser le body
        body = await request.json()
        
        # Validation
        system = body.get("system")
        code = body.get("code")
        display = body.get("display")
        
        if not system or not code or not display:
            raise HTTPException(
                status_code=400,
                detail="system, code, and display are required"
            )
        
        # Limiter à 20 conditions par utilisateur (soft limit)
        existing_conditions = supabase_client.client.table("user_conditions").select("id").eq("user_id", user_id).execute()
        if existing_conditions.data and len(existing_conditions.data) >= 20:
            raise HTTPException(
                status_code=400,
                detail="Maximum 20 conditions per user"
            )
        
        # Insérer la condition
        condition_data = {
            "user_id": user_id,
            "system": system,
            "code": code,
            "display": display,
            "category": body.get("category"),
            "severity": body.get("severity"),
            "diagnosed": body.get("diagnosed")
        }
        
        response = supabase_client.client.table("user_conditions").insert(condition_data).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=500, detail="Failed to insert condition")
        
        return {
            "status": "success",
            "condition": response.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding user condition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/profile/conditions/{condition_id}")
async def delete_user_condition(
    condition_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Supprime une condition de santé de l'utilisateur connecté
    
    Args:
        condition_id: UUID de la condition à supprimer
    
    Returns:
        {
            "status": "success",
            "message": "Condition deleted"
        }
    """
    try:
        # Vérifier le token JWT et extraire user_id
        user_id = verify_jwt_token(authorization=authorization)
        
        # Vérifier que la condition appartient à l'utilisateur avant de supprimer
        # RLS s'occupe de ça, mais on peut vérifier explicitement
        condition = supabase_client.client.table("user_conditions").select("*").eq("id", condition_id).eq("user_id", user_id).execute()
        
        if not condition.data or len(condition.data) == 0:
            raise HTTPException(
                status_code=404,
                detail="Condition not found or does not belong to user"
            )
        
        # Supprimer la condition
        supabase_client.client.table("user_conditions").delete().eq("id", condition_id).eq("user_id", user_id).execute()
        
        return {
            "status": "success",
            "message": "Condition deleted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user condition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# FatSecret Integration Endpoints
# =====================================================

@app.post("/api/fatsecret/connect")
async def fatsecret_connect(
    authorization: Optional[str] = Header(None)
):
    """
    Crée un profil FatSecret pour l'utilisateur
    
    Returns:
        {
            "status": "success",
            "message": "FatSecret profile created"
        }
    """
    try:
        # Vérifier le token JWT et extraire user_id
        user_id = verify_jwt_token(authorization=authorization)
        
        # Vérifier si un profil existe déjà
        existing = supabase_client.client.table("fatsecret_connections").select("*").eq(
            "user_id", user_id
        ).execute()
        
        if existing.data and len(existing.data) > 0:
            return {
                "status": "success",
                "message": "FatSecret profile already exists"
            }
        
        # Initialiser le client FatSecret
        client = get_fatsecret_client()
        
        # Créer un profil
        profile = client.create_profile(user_id=user_id)
        
        auth_token = profile["auth_token"]
        auth_secret = profile["auth_secret"]
        
        # Stocker dans Supabase
        connection_data = {
            "user_id": user_id,
            "oauth_token": auth_token,
            "oauth_token_secret": auth_secret,
            "is_active": True,
            "metadata": {
                "profile_type": "created",
                "source": "api"
            }
        }
        
        supabase_client.client.table("fatsecret_connections").insert(
            connection_data
        ).execute()
        
        logger.info(f"FatSecret profile created for user {user_id}")
        
        return {
            "status": "success",
            "message": "FatSecret profile created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating FatSecret profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/fatsecret/disconnect")
async def fatsecret_disconnect(
    authorization: Optional[str] = Header(None)
):
    """
    Déconnecte le compte FatSecret de l'utilisateur
    
    Returns:
        {
            "status": "success",
            "message": "FatSecret disconnected"
        }
    """
    try:
        # Vérifier le token JWT et extraire user_id
        user_id = verify_jwt_token(authorization=authorization)
        
        # Désactiver la connexion
        result = supabase_client.client.table("fatsecret_connections").update({
            "is_active": False
        }).eq("user_id", user_id).execute()
        
        logger.info(f"FatSecret disconnected for user {user_id}")
        
        return {
            "status": "success",
            "message": "FatSecret disconnected"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting FatSecret: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/fatsecret/status")
async def fatsecret_status(
    authorization: Optional[str] = Header(None)
):
    """
    Vérifie le statut de connexion FatSecret de l'utilisateur
    
    Returns:
        {
            "connected": true/false,
            "connected_at": "...",
            "last_synced_date": "..."
        }
    """
    try:
        # Vérifier le token JWT et extraire user_id
        user_id = verify_jwt_token(authorization=authorization)
        
        # Récupérer la connexion
        result = supabase_client.client.table("fatsecret_connections").select(
            "connected_at, last_synced_date, is_active"
        ).eq("user_id", user_id).execute()
        
        if not result.data or len(result.data) == 0:
            return {
                "connected": False
            }
        
        conn = result.data[0]
        
        return {
            "connected": conn.get("is_active", False),
            "connected_at": conn.get("connected_at"),
            "last_synced_date": conn.get("last_synced_date")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking FatSecret status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/fatsecret/search-foods")
async def search_foods(
    query: str,
    page: int = 0,
    authorization: Optional[str] = Header(None)
):
    """
    Recherche des aliments dans la base FatSecret
    
    Query params:
        - query: Terme de recherche
        - page: Numéro de page (défaut: 0)
    
    Returns:
        {
            "status": "success",
            "foods": [...]
        }
    """
    try:
        # Vérifier le token JWT
        verify_jwt_token(authorization=authorization)
        
        # Initialiser le client FatSecret
        client = get_fatsecret_client()
        
        # Rechercher
        result = client.search_foods(query, page)
        
        # Parser les résultats
        foods = result.get("foods", {}).get("food", [])
        if isinstance(foods, dict):
            foods = [foods]
        
        return {
            "status": "success",
            "foods": foods
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching foods: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/fatsecret/add-food-entry")
async def add_food_entry(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Ajoute une entrée alimentaire pour l'utilisateur
    
    Body:
        {
            "food_id": 123,
            "serving_id": 456,
            "num_servings": 1.0,
            "meal": "breakfast",  // breakfast, lunch, dinner, snack, other
            "date": "2026-01-29"
        }
    
    Returns:
        {
            "status": "success",
            "message": "Food entry added"
        }
    """
    try:
        # Vérifier le token JWT et extraire user_id
        user_id = verify_jwt_token(authorization=authorization)
        
        # Parser le body
        body = await request.json()
        
        food_id = body.get("food_id")
        serving_id = body.get("serving_id")
        num_servings = body.get("num_servings", 1.0)
        meal = body.get("meal", "other")
        date_str = body.get("date")
        
        if not food_id or not serving_id or not date_str:
            raise HTTPException(
                status_code=400,
                detail="food_id, serving_id, and date are required"
            )
        
        # Parse date
        import datetime as dt
        date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Récupérer les credentials FatSecret de l'utilisateur
        conn = supabase_client.client.table("fatsecret_connections").select(
            "oauth_token, oauth_token_secret"
        ).eq("user_id", user_id).eq("is_active", True).execute()
        
        if not conn.data or len(conn.data) == 0:
            raise HTTPException(
                status_code=404,
                detail="FatSecret profile not found. Please connect first."
            )
        
        credentials = conn.data[0]
        
        # Créer l'entrée via FatSecret API
        client = get_fatsecret_client(
            oauth_token=credentials["oauth_token"],
            oauth_secret=credentials["oauth_token_secret"]
        )
        
        result = client.create_food_entry(
            food_id=int(food_id),
            serving_id=int(serving_id),
            num_servings=float(num_servings),
            meal=meal,
            date=date
        )
        
        logger.info(f"Food entry added for user {user_id}: food_id={food_id}, date={date}")
        
        return {
            "status": "success",
            "message": "Food entry added successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding food entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/fatsecret/food-entries")
async def get_food_entries(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """
    Récupère les entrées alimentaires de l'utilisateur depuis Supabase
    
    Query params:
        - start_date: Date de début (YYYY-MM-DD)
        - end_date: Date de fin (YYYY-MM-DD)
    
    Returns:
        {
            "status": "success",
            "entries": [...]
        }
    """
    try:
        # Vérifier le token JWT et extraire user_id
        user_id = verify_jwt_token(authorization=authorization)
        
        # Construire la requête
        query = supabase_client.client.table("food_entries_raw").select(
            "*"
        ).eq("user_id", user_id).order("entry_date", desc=True).order("inserted_at", desc=True)
        
        if start_date:
            query = query.gte("entry_date", start_date)
        
        if end_date:
            query = query.lte("entry_date", end_date)
        
        # Limiter à 100 entrées pour éviter les réponses trop volumineuses
        query = query.limit(100)
        
        result = query.execute()
        
        return {
            "status": "success",
            "entries": result.data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching food entries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/fatsecret/food-entry/{food_entry_id}")
async def delete_food_entry(
    food_entry_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Supprime une entrée alimentaire
    
    Args:
        food_entry_id: ID FatSecret de l'entrée (fatsecret_food_entry_id)
    
    Returns:
        {
            "status": "success",
            "message": "Food entry deleted"
        }
    """
    try:
        # Vérifier le token JWT et extraire user_id
        user_id = verify_jwt_token(authorization=authorization)
        
        # Vérifier que l'entrée appartient à l'utilisateur
        entry = supabase_client.client.table("food_entries_raw").select(
            "*"
        ).eq("fatsecret_food_entry_id", int(food_entry_id)).eq("user_id", user_id).execute()
        
        if not entry.data or len(entry.data) == 0:
            raise HTTPException(
                status_code=404,
                detail="Food entry not found or does not belong to user"
            )
        
        # Récupérer les credentials FatSecret
        conn = supabase_client.client.table("fatsecret_connections").select(
            "oauth_token, oauth_token_secret"
        ).eq("user_id", user_id).eq("is_active", True).execute()
        
        if not conn.data or len(conn.data) == 0:
            raise HTTPException(status_code=404, detail="FatSecret profile not found")
        
        credentials = conn.data[0]
        
        # Supprimer via FatSecret API
        client = get_fatsecret_client(
            oauth_token=credentials["oauth_token"],
            oauth_secret=credentials["oauth_token_secret"]
        )
        
        client.delete_food_entry(int(food_entry_id))
        
        # Supprimer de Supabase également
        supabase_client.client.table("food_entries_raw").delete().eq(
            "fatsecret_food_entry_id", int(food_entry_id)
        ).eq("user_id", user_id).execute()
        
        logger.info(f"Food entry {food_entry_id} deleted for user {user_id}")
        
        return {
            "status": "success",
            "message": "Food entry deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting food entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# PYDANTIC MODELS - FOOD DIARY MVP
# =====================================================

class FoodLogItemRequest(BaseModel):
    """Item alimentaire dans un repas"""
    name: str
    fs_food_id: Optional[int] = None
    fs_serving_id: Optional[int] = None
    quantity: float = 1.0
    unit: str = "serving"
    nutrition: Optional[dict] = None
    raw: Optional[dict] = None


class CreateFoodLogRequest(BaseModel):
    """Requête pour créer un repas"""
    logged_at: str  # ISO datetime
    meal_type: str  # breakfast|lunch|dinner|snack
    items: List[FoodLogItemRequest]
    note: Optional[str] = None
    context: Optional[dict] = None
    source: str = "search"  # search|manual|photo|import


# =====================================================
# ENDPOINTS - FOOD DIARY MVP
# =====================================================

@app.post("/api/food-diary/provision")
async def provision_fatsecret_profile_endpoint(
    authorization: Optional[str] = Header(None)
):
    """
    Créé automatiquement un profil FatSecret si absent
    (Auto-provisioning transparent pour l'utilisateur)
    """
    try:
        user_id = verify_jwt_token(authorization=authorization)
        
        result = food_log_service.provision_fatsecret_profile(user_id)
        
        return JSONResponse(content=result, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error provisioning FatSecret profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/foods/search")
async def search_foods_endpoint(
    q: str,
    page: int = 0,
    authorization: Optional[str] = Header(None)
):
    """
    Recherche d'aliments (barre de recherche)
    
    Args:
        q: Terme de recherche
        page: Page de résultats (0-based)
    
    Returns:
        [{"fs_food_id": 123, "name": "...", "brand": "...", ...}]
    """
    try:
        user_id = verify_jwt_token(authorization=authorization)
        
        results = food_log_service.search_foods(query=q, page=page)
        
        return JSONResponse(content={"foods": results}, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching foods: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/foods/{food_id}")
async def get_food_details_endpoint(
    food_id: int,
    authorization: Optional[str] = Header(None)
):
    """
    Détails aliment + servings (pour portion picker)
    
    Returns:
        {"food_id": 123, "name": "...", "servings": [{...}], ...}
    """
    try:
        user_id = verify_jwt_token(authorization=authorization)
        
        details = food_log_service.get_food_details(food_id)
        
        return JSONResponse(content=details, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching food details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/food-logs")
async def create_food_log_endpoint(
    request: CreateFoodLogRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Ajouter un repas (crée log Supabase + sync FatSecret)
    
    Body:
        {
            "logged_at": "2026-01-29T12:30:00Z",
            "meal_type": "lunch",
            "items": [{"fs_food_id": 123, "fs_serving_id": 456, "quantity": 1.5, "name": "..."}],
            "note": "Déj rapide",
            "context": {"hunger": 7, "mood": "ok"}
        }
    
    Returns:
        {"food_log_id": "...", "items_count": 3, "fs_sync_status": "synced"}
    """
    try:
        user_id = verify_jwt_token(authorization=authorization)
        
        # Parser datetime
        logged_at = datetime.fromisoformat(request.logged_at.replace("Z", "+00:00"))
        
        # Convertir items
        items = [item.dict() for item in request.items]
        
        result = food_log_service.create_food_log(
            user_id=user_id,
            logged_at=logged_at,
            meal_type=request.meal_type,
            items=items,
            note=request.note,
            context=request.context,
            source=request.source
        )
        
        return JSONResponse(content=result, status_code=201)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating food log: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/food-diary")
async def get_food_diary_endpoint(
    date_str: str,
    force_sync: bool = False,
    authorization: Optional[str] = Header(None)
):
    """
    Lire journal alimentaire d'une date
    Priorise Supabase (cache rapide), option force_sync pour rafraîchir
    
    Args:
        date_str: Date au format YYYY-MM-DD
        force_sync: Si True, rafraîchit depuis FatSecret
    
    Returns:
        {
            "date": "2026-01-29",
            "meals": {
                "breakfast": [...],
                "lunch": [...],
                "dinner": [...],
                "snack": [...]
            },
            "total_nutrition": {...}
        }
    """
    try:
        user_id = verify_jwt_token(authorization=authorization)
        
        # Parser date
        date_obj = date.fromisoformat(date_str)
        
        diary = food_log_service.get_food_diary(
            user_id=user_id,
            date_obj=date_obj,
            force_sync=force_sync
        )
        
        return JSONResponse(content=diary, status_code=200)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Error fetching food diary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/food-logs/{food_log_id}/photo")
async def upload_food_photo_endpoint(
    food_log_id: str,
    file: UploadFile = File(...),
    analyze: bool = Form(False),
    authorization: Optional[str] = Header(None)
):
    """
    Upload une photo de repas
    
    Args:
        food_log_id: UUID du food_log
        file: Fichier image
        analyze: Si True, lance l'analyse IA (optionnel)
    
    Returns:
        {"photo_id": "...", "storage_path": "...", "analysis_status": "..."}
    """
    try:
        user_id = verify_jwt_token(authorization=authorization)
        
        # Vérifier que le food_log existe et appartient à l'utilisateur
        log = supabase_client.client.table("food_logs")\
            .select("*")\
            .eq("id", food_log_id)\
            .eq("user_id", user_id)\
            .execute()
        
        if not log.data:
            raise HTTPException(
                status_code=404,
                detail="Food log not found or unauthorized"
            )
        
        # Lire fichier
        file_bytes = await file.read()
        
        # Upload
        result = photo_service.upload_food_photo(
            user_id=user_id,
            food_log_id=food_log_id,
            file_data=file_bytes,
            filename=file.filename,
            mime_type=file.content_type or "image/jpeg",
            analyze=analyze
        )
        
        return JSONResponse(content=result, status_code=201)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading photo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/food-photos/{photo_id}/url")
async def get_photo_url_endpoint(
    photo_id: str,
    expires_in: int = 3600,
    authorization: Optional[str] = Header(None)
):
    """
    Génère une URL signée pour accéder à une photo
    
    Args:
        photo_id: UUID de la photo
        expires_in: Durée validité en secondes (défaut 1h)
    
    Returns:
        {"url": "https://..."}
    """
    try:
        user_id = verify_jwt_token(authorization=authorization)
        
        url = photo_service.get_photo_url(photo_id, expires_in)
        
        return JSONResponse(content={"url": url}, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting photo URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/reconcile-food-logs")
async def reconcile_food_logs_endpoint(
    user_id: Optional[str] = None,
    days_back: int = 7,
    authorization: Optional[str] = Header(None)
):
    """
    Endpoint admin : réconcilie les syncs FatSecret en erreur/pending
    
    Args:
        user_id: Si spécifié, uniquement pour cet utilisateur
        days_back: Nombre de jours à réconcilier (défaut 7)
    
    Returns:
        {"reconciled": 5, "failed": 1, "users": [...]}
    """
    try:
        # TODO: Ajouter vérification role admin
        admin_user_id = verify_jwt_token(authorization=authorization)
        
        result = food_log_service.reconcile_pending_syncs(
            user_id=user_id,
            days_back=days_back
        )
        
        return JSONResponse(content=result, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reconciling food logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/energy/daily")
async def get_daily_energy_endpoint(
    date: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """
    Récupère le daily energy (score d'énergie consolidé) pour un utilisateur
    
    ✅ CONVENTION API : Scores en 0-100 (cohérence avec energy_forecast)
    
    Args:
        date: Date au format YYYY-MM-DD (défaut: aujourd'hui)
        authorization: JWT token dans le header Authorization
    
    Returns:
        {
            "energy_score": 78,          # ✅ 0-100 (converti depuis 0-1 en DB)
            "label": "Bonne journée",
            "confidence": 82,            # ✅ 0-100 (converti depuis 0-1 en DB)
            "reasons": [...],
            "primary_action": {...},
            "risk_windows": [...],
            "components": {              # ✅ 0-100 (convertis depuis 0-1 en DB)
                "recovery": 72,
                "sleep_debt": 65,
                "overtrain": 60,
                "infection": 75
            }
        }
    """
    try:
        user_id = verify_jwt_token(authorization=authorization)
        
        # Import ici pour éviter circular import
        from daily_energy_engine import get_daily_energy
        
        # Récupérer le daily_energy depuis la DB (en 0-1)
        energy = get_daily_energy(user_id, date)
        
        if not energy:
            raise HTTPException(
                status_code=404, 
                detail="Daily energy not found. Please wait for calculation or ensure daily states are available."
            )
        
        # ✅ CONVERSION 0-1 → 0-100 pour l'API (cohérence avec forecast)
        energy_api = {
            'energy_score': round(energy['energy_score'] * 100),  # 0.78 → 78
            'label': energy['label'],
            'confidence': round(energy['confidence'] * 100),      # 0.82 → 82
            'reasons': energy['reasons'],
            'primary_action': energy['primary_action'],
            'risk_windows': energy['risk_windows'],
            'components': {
                'recovery': round(energy['components']['recovery'] * 100),
                'sleep_debt': round(energy['components']['sleep_debt'] * 100),
                'overtrain': round(energy['components']['overtrain'] * 100),
                'infection': round(energy['components']['infection'] * 100),
            },
            'model_version': energy.get('model_version', 'energy_v1'),
            'calculated_at': energy.get('calculated_at'),
        }
        
        return JSONResponse(content=energy_api, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching daily energy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/energy/intraday")
async def get_intraday_energy_endpoint(
    date: Optional[str] = None,
    force_refresh: bool = False,
    model: Optional[str] = "auto",  # "auto", "heuristic", "pulse_energy_decay"
    authorization: Optional[str] = Header(None)
):
    """
    Récupère la prévision d'énergie intraday (reste de la journée)
    
    **Modèles disponibles:**
    - `auto` (défaut): Pulse Energy Decay si données Oura disponibles, sinon heuristique
    - `heuristic`: Modèle V1 simple (daily_energy + events)
    - `pulse_energy_decay`: Modèle V2 mathématique (readiness Oura + pharmacocinétique)
    
    Retourne une courbe d'énergie de maintenant → fin de journée avec:
    - Points toutes les 30 minutes
    - Événements du calendrier avec impact estimé
    - Fenêtres de risque (creux prévus)
    - Notes explicatives
    - Influencers (V2 uniquement)
    
    Args:
        date: Date au format YYYY-MM-DD (défaut: aujourd'hui)
        force_refresh: Si True, recalcule même si cache existe
        model: Modèle à utiliser ("auto", "heuristic", "pulse_energy_decay")
        authorization: JWT token dans le header Authorization
    
    Returns:
        {
            "type": "intraday_energy" | "pulse_energy_decay",
            "date": "2026-01-31",
            "generated_at": "2026-01-31T12:00:00Z",
            "model_version": "intraday_v1" | "pulse_energy_decay_v1",
            "calculation_model": "heuristic_v1" | "pulse_energy_decay_v1",
            "current_energy": 72,
            "forecast_curve": [  // V2 uniquement
                {"time": "08:00", "value": 92, "event": "Wake up"}
            ],
            "influencers": [  // V2 uniquement
                {"name": "Sommeil", "impact": "+85", "status": "positive"}
            ],
            "points": [
                {"t": "2026-01-31T09:15:00Z", "energy": 78}
            ],
            "windows": [
                {"from": "16:00", "to": "18:00", "kind": "dip", "label": "Creux probable"}
            ],
            "events": [],
            "notes": ["Creux attendu en fin d'après-midi"],
            "confidence": 0.85
        }
    """
    try:
        user_id = verify_jwt_token(authorization=authorization)
        
        # Déterminer quel modèle utiliser
        use_advanced_model = False
        
        if model == "pulse_energy_decay":
            use_advanced_model = True
        elif model == "auto":
            # Auto: vérifier si l'utilisateur a des données Oura
            try:
                result = supabase_client.client.rpc('get_today_health_profile', {'p_user_id': user_id}).execute()
                health_profile = result.data if result.data else {}
                has_readiness = health_profile.get('readiness_score', 0) > 0
                use_advanced_model = has_readiness
                logger.info(f"[Intraday] Auto-select: {'advanced' if use_advanced_model else 'heuristic'} (has_readiness={has_readiness})")
            except Exception as e:
                logger.warning(f"[Intraday] Could not check health_profile, defaulting to heuristic: {e}")
                use_advanced_model = False
        
        # ========================================
        # MODÈLE AVANCÉ: Pulse Energy Decay V2
        # ========================================
        if use_advanced_model:
            logger.info(f"[Intraday] Using Pulse Energy Decay model for user {user_id}")
            
            from pulse_energy_decay_service import PulseEnergyDecayService
            
            pulse_service = PulseEnergyDecayService(supabase_client=supabase_client)
            forecast = await pulse_service.generate_forecast(
                user_id=user_id,
                target_date_str=date,
                force_refresh=force_refresh
            )
            
            if not forecast:
                # Fallback vers heuristique si échec
                logger.warning(f"[Intraday] Pulse Energy Decay failed, falling back to heuristic")
                use_advanced_model = False
            else:
                return JSONResponse(content=forecast.dict(), status_code=200)
        
        # ========================================
        # MODÈLE SIMPLE: Heuristique V1
        # ========================================
        if not use_advanced_model:
            logger.info(f"[Intraday] Using heuristic model for user {user_id}")
            
            # Import ici pour éviter circular import
            from intraday_energy_service import (
                get_intraday_forecast,
                generate_intraday_forecast,
                save_intraday_forecast
            )
            
            # Si force_refresh, régénérer
            if force_refresh:
                logger.info(f"Force refresh intraday forecast for user {user_id}")
                forecast = generate_intraday_forecast(user_id, date)
                
                if forecast:
                    save_intraday_forecast(user_id, forecast)
                    return JSONResponse(content=forecast, status_code=200)
                else:
                    raise HTTPException(
                        status_code=404,
                        detail="Could not generate intraday forecast. Ensure daily_energy is calculated."
                    )
            
            # Sinon, chercher en cache
            forecast = get_intraday_forecast(user_id, date)
            
            if forecast:
                return JSONResponse(content=forecast, status_code=200)
            
            # Pas en cache → générer
            logger.info(f"No cached intraday forecast, generating for user {user_id}")
            forecast = generate_intraday_forecast(user_id, date)
            
            if not forecast:
                raise HTTPException(
                    status_code=404,
                    detail="Could not generate intraday forecast. Ensure daily_energy is calculated."
                )
            
            # Sauvegarder en cache
            save_intraday_forecast(user_id, forecast)
            
            return JSONResponse(content=forecast, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching intraday energy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/energy/explain/{user_id}")
async def explain_energy(
    user_id: str,
    date: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """
    Génère une explication narrative du score d'énergie avec des cartes pédagogiques.
    
    Ce endpoint utilise Gemini 3 Pro avec mode raisonnement pour générer des analogies 
    simples et percutantes qui expliquent pourquoi le score d'énergie est à son niveau actuel.
    
    Le "Why-Stack" transforme les données brutes (HRV, RHR, médicaments, conditions)
    en récit empathique avec 4 types de cartes:
    - **nervous**: Système nerveux (Le Câblage - HRV, transmission énergie)
    - **chemistry**: Chimie corporelle (Le Paradoxe - médicaments boosters vs freins)
    - **load**: Charge/Effort (La Charge Invisible - sinus, dépression)
    - **action**: Conseils Actionnables (3 micro-actions concrètes)
    
    Args:
        user_id: ID de l'utilisateur
        date: Date au format YYYY-MM-DD (défaut: aujourd'hui)
        authorization: JWT token dans le header Authorization
    
    Returns:
        {
            "energyScore": 38,
            "confidence": 62,
            "label": "Journée fragile",
            "date": "2026-02-01",
            "cards": [
                {
                    "type": "nervous",
                    "title": "Le câblage est saturé",
                    "text": "Ton HRV est tombé à 20ms...",
                    "analogy": "C'est comme charger ton téléphone avec un câble sectionné",
                    "metrics": {
                        "primary": {"label": "HRV actuel", "value": 20, "unit": "ms"},
                        "secondary": {"label": "HRV baseline", "value": 30, "unit": "ms"}
                    }
                }
            ]
        }
    
    Example:
        GET /api/energy/explain/user123?date=2026-02-01
        Authorization: Bearer <jwt_token>
    """
    try:
        # Vérifier l'authentification
        authenticated_user_id = verify_jwt_token(authorization=authorization)
        
        # Vérifier que l'utilisateur peut accéder à ces données
        if authenticated_user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="You can only access your own energy explanation"
            )
        
        # Parser la date
        from datetime import date as date_type
        target_date = None
        if date:
            try:
                target_date = date_type.fromisoformat(date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use YYYY-MM-DD"
                )
        
        logger.info(f"[explain-energy] user={user_id}, date={target_date or 'today'}")
        
        # Vérifier que le service est disponible
        if not energy_explain_service:
            raise HTTPException(
                status_code=503,
                detail="Energy Explain Service not available. Please configure GOOGLE_API_KEY."
            )
        
        # Générer l'explication avec Gemini Thinking mode
        explanation = await energy_explain_service.generate_explanation(
            user_id=user_id,
            target_date=target_date
        )
        
        # ✅ Toujours renvoyer 200 si on a des données à afficher
        # Même "Données insuffisantes" est une réponse valide avec des cartes
        return JSONResponse(content=explanation, status_code=200)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating energy explanation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/medications/analyze/{user_id}")
async def analyze_medications(
    user_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Génère une analyse détaillée de tous les médicaments actifs de l'utilisateur.
    
    Utilise Gemini 3 Pro pour générer des explications vulgarisées et actionnables
    pour chaque médicament :
    - **Intro explicative** : Fonction simple du médicament
    - **Impact sur le corps** : Action physiologique long terme
    - **Impact sur la journée** : Ressenti quotidien selon l'heure de prise
    - **Observation** : Conseil ou vigilance selon dosage/durée
    
    Args:
        user_id: ID de l'utilisateur
        authorization: JWT token dans le header Authorization
    
    Returns:
        {
            "analyse_traitements": [
                {
                    "nom": "Doliprane",
                    "intro_explicative": "Antalgique qui réduit la douleur et la fièvre",
                    "impact_corps": "Agit sur le système nerveux central...",
                    "impact_journee": "Effet ressenti 30min après la prise...",
                    "observation": "Respecter les doses maximales..."
                }
            ],
            "_generated_at": "2026-02-04T...",
            "_medications_count": 3,
            "_cost": 0.0234
        }
    
    Example:
        GET /api/medications/analyze/user123
        Authorization: Bearer <jwt_token>
    """
    try:
        # Vérifier l'authentification
        authenticated_user_id = verify_jwt_token(authorization=authorization)
        
        # Vérifier que l'utilisateur peut accéder à ces données
        if authenticated_user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="You can only access your own medication analysis"
            )
        
        logger.info(f"[analyze-medications] user={user_id}")
        
        # Vérifier que le service est disponible
        if not medication_analysis_service:
            raise HTTPException(
                status_code=503,
                detail="Medication Analysis Service not available. Please configure GOOGLE_API_KEY."
            )
        
        # Générer l'analyse avec Gemini 3 Pro
        analysis = await medication_analysis_service.generate_medication_analysis(
            user_id=user_id
        )
        
        return JSONResponse(content=analysis, status_code=200)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating medication analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/medications/comparative-analysis/{user_id}")
async def comparative_analysis_medications(
    user_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Génère une analyse comparative détaillée des traitements (changements, ajouts, arrêts).
    
    Utilise Gemini 3 Pro pour analyser :
    - Les molécules ajoutées, supprimées ou modifiées
    - Les mécanismes d'action sur les neurotransmetteurs
    - L'impact métabolique (énergie, poids, sommeil, digestion)
    - Des conseils pratiques de mode de vie
    - Une clause de sécurité
    
    Args:
        user_id: ID de l'utilisateur
        authorization: JWT token dans le header Authorization
    
    Returns:
        {
            "analysis_text": "Texte d'analyse détaillée formaté avec titres et listes",
            "has_changes": true,
            "medications_count": 3,
            "new_medications": 1,
            "stopped_medications": 1,
            "modified_medications": 0,
            "_generated_at": "2026-02-06T..."
        }
    
    Example:
        GET /api/medications/comparative-analysis/user123
        Authorization: Bearer <jwt_token>
    """
    try:
        # Vérifier l'authentification
        authenticated_user_id = verify_jwt_token(authorization=authorization)
        
        # Vérifier que l'utilisateur peut accéder à ces données
        if authenticated_user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="You can only access your own medication analysis"
            )
        
        logger.info(f"[comparative-analysis] user={user_id}")
        
        # Vérifier que le service est disponible
        if not medication_comparative_service:
            raise HTTPException(
                status_code=503,
                detail="Medication Comparative Analysis Service not available. Please configure GOOGLE_API_KEY."
            )
        
        # Générer l'analyse comparative avec Gemini 3 Pro
        analysis = medication_comparative_service.generate_comparative_analysis(
            user_id=user_id
        )
        
        return JSONResponse(content=analysis, status_code=200)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating comparative analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# OURA SYNC ENDPOINTS
# ============================================

@app.post("/api/oura/sync")
async def sync_oura_data(
    date: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """
    Synchronise les données Oura pour l'utilisateur connecté
    
    Récupère les dernières données depuis Oura (readiness, sleep, activity)
    et met à jour health_profiles.current_metrics pour alimenter le modèle
    Pulse Energy Decay.
    
    Args:
        date: Date à synchroniser (YYYY-MM-DD), défaut = aujourd'hui
        authorization: JWT token
    
    Returns:
        {
            "status": "success",
            "message": "Oura data synced successfully",
            "data": {
                "current_metrics": {...},
                "anomalies": [...],
                "synced_at": "ISO8601"
            }
        }
    """
    try:
        user_id = verify_jwt_token(authorization=authorization)
        
        from oura_sync_service import sync_user_oura_data
        from datetime import date as date_type
        
        target_date = None
        if date:
            try:
                target_date = date_type.fromisoformat(date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        result = await sync_user_oura_data(user_id, supabase, target_date)
        
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result['message'])
        
        return JSONResponse(content=result, status_code=200)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing Oura data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/oura/sync-all")
async def sync_all_oura_users_endpoint(
    date: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """
    Synchronise tous les utilisateurs Oura actifs
    
    **ADMIN ONLY** - Endpoint utilisé par le cron quotidien
    
    Args:
        date: Date à synchroniser (YYYY-MM-DD), défaut = aujourd'hui
        authorization: JWT token (doit être admin)
    
    Returns:
        {
            "status": "success",
            "total_users": 10,
            "success_count": 9,
            "error_count": 1,
            "errors": [...]
        }
    """
    try:
        # TODO: Vérifier que l'utilisateur est admin
        # user_id = verify_jwt_token(authorization=authorization)
        # if not is_admin(user_id):
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        from oura_sync_service import sync_all_oura_users
        from datetime import date as date_type
        
        target_date = None
        if date:
            try:
                target_date = date_type.fromisoformat(date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        result = await sync_all_oura_users(supabase, target_date)
        
        return JSONResponse(content=result, status_code=200)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing all Oura users: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/oura/status")
async def get_oura_status(authorization: Optional[str] = Header(None)):
    """
    Vérifie le statut de la connexion Oura de l'utilisateur
    
    Returns:
        {
            "connected": true,
            "last_sync": "2026-01-31T08:00:00Z",
            "has_readiness_data": true
        }
    """
    try:
        user_id = verify_jwt_token(authorization=authorization)
        
        # Vérifier si l'utilisateur a un compte Oura
        result = supabase.from_('external_identities') \
            .select('is_active, metadata, created_at') \
            .eq('supabase_user_id', user_id) \
            .eq('provider_system', 'oura') \
            .single() \
            .execute()
        
        if not result.data:
            return JSONResponse(content={
                "connected": False,
                "message": "No Oura account connected"
            }, status_code=200)
        
        # Vérifier la dernière sync
        health_result = supabase.from_('health_profiles') \
            .select('date, current_metrics, created_at') \
            .eq('user_id', user_id) \
            .order('date', desc=True) \
            .limit(1) \
            .execute()
        
        has_readiness = False
        last_sync = None
        
        if health_result.data and len(health_result.data) > 0:
            profile = health_result.data[0]
            metrics = profile.get('current_metrics', {})
            has_readiness = metrics.get('readiness_score', 0) > 0
            last_sync = profile.get('created_at')
        
        return JSONResponse(content={
            "connected": result.data['is_active'],
            "last_sync": last_sync,
            "has_readiness_data": has_readiness,
            "connected_at": result.data['created_at']
        }, status_code=200)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking Oura status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/oura/connect")
async def connect_oura_account(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Connecte un compte Oura à l'utilisateur
    
    Body:
        {
            "access_token": "IX6RMKRCMIJOVZMIB2IKVL2PWUQOCNNI"
        }
    
    Returns:
        {
            "status": "success",
            "message": "Oura account connected successfully",
            "external_user_id": "user@example.com"
        }
    """
    try:
        user_id = verify_jwt_token(authorization=authorization)
        data = await request.json()
        
        oura_token = data.get('access_token')
        if not oura_token:
            raise HTTPException(status_code=400, detail="access_token is required")
        
        # Utiliser register_oura_user pour enregistrer le compte
        from register_oura_user import register_oura_user
        
        success = register_oura_user(
            supabase_user_id=user_id,
            oura_token=oura_token,
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to connect Oura account. Please check your token."
            )
        
        # Récupérer l'external_user_id
        result = supabase.from_('external_identities') \
            .select('external_user_id') \
            .eq('supabase_user_id', user_id) \
            .eq('provider_system', 'oura') \
            .single() \
            .execute()
        
        external_user_id = result.data.get('external_user_id') if result.data else None
        
        return JSONResponse(content={
            "status": "success",
            "message": "Oura account connected successfully",
            "external_user_id": external_user_id
        }, status_code=200)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting Oura account: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/oura/disconnect")
async def disconnect_oura_account(authorization: Optional[str] = Header(None)):
    """
    Déconnecte le compte Oura de l'utilisateur
    
    Returns:
        {
            "status": "success",
            "message": "Oura account disconnected"
        }
    """
    try:
        user_id = verify_jwt_token(authorization=authorization)
        
        # Désactiver le compte Oura
        result = supabase.from_('external_identities') \
            .update({'is_active': False}) \
            .eq('supabase_user_id', user_id) \
            .eq('provider_system', 'oura') \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=404,
                detail="No Oura account found to disconnect"
            )
        
        return JSONResponse(content={
            "status": "success",
            "message": "Oura account disconnected"
        }, status_code=200)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting Oura account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/feedback")
async def submit_feedback(request: Request):
    """
    Enregistre un feedback utilisateur pour le ML adaptatif (PWA)
    
    Body:
    {
        "user_id": "uuid",
        "system_score": 12.5,
        "user_score": 30,
        "active_factors": {
            "medications": ["N06AB06", "N06AX11"],
            "conditions": ["6A70", "6A05"]
        }
    }
    
    Traite immédiatement le feedback via SGD et ajuste les poids personnalisés
    """
    try:
        data = await request.json()
        user_id = data.get('user_id')
        system_score = data.get('system_score')
        user_score = data.get('user_score')
        active_factors = data.get('active_factors', {})
        
        if not user_id or system_score is None or user_score is None:
            raise HTTPException(
                status_code=400,
                detail="user_id, system_score et user_score sont requis"
            )
        
        # Traiter le feedback via ML Optimizer
        result = await ml_optimizer.process_feedback(
            user_id=user_id,
            system_score=float(system_score),
            user_score=int(user_score),
            active_factors=active_factors
        )
        
        if result['status'] == 'error':
            raise HTTPException(status_code=500, detail=result['error'])
        
        return JSONResponse(content={
            "status": "ok",
            "error": result['error'],
            "adjustments_count": len(result['adjustments']),
            "adjustments": result['adjustments']
        }, status_code=201)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Feedback] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# OURA OAUTH2 ENDPOINTS
# ============================================

@app.get("/api/oura/oauth/authorize")
async def oura_oauth_authorize(authorization: Optional[str] = Header(None)):
    """
    Génère l'URL d'autorisation OAuth2 pour Oura
    
    L'utilisateur doit être redirigé vers cette URL pour autoriser l'accès
    
    Returns:
        {
            "auth_url": "https://cloud.ouraring.com/oauth/authorize?...",
            "state": "random_state_string"
        }
    """
    try:
        user_id = verify_jwt_token(authorization=authorization)
        
        from oura_oauth2_service import OuraOAuth2Service
        
        oauth_service = OuraOAuth2Service(supabase)
        
        # Générer un state unique pour la sécurité CSRF
        import secrets
        state = secrets.token_urlsafe(32)
        
        # Stocker le state temporairement (dans une vraie app, utiliser Redis ou session)
        # Pour l'instant, on le retourne et l'app mobile devra le vérifier
        
        auth_url = oauth_service.generate_auth_url(state=state)
        
        return JSONResponse(content={
            "auth_url": auth_url,
            "state": state
        }, status_code=200)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating OAuth2 auth URL: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/oura/oauth/callback")
async def oura_oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None
):
    """
    Callback OAuth2 pour Oura
    
    Oura redirige vers cette URL après que l'utilisateur ait autorisé l'accès
    
    Query params:
        code: Code d'autorisation (si succès)
        state: État CSRF
        error: Code d'erreur (si échec)
        error_description: Description de l'erreur
    
    Returns:
        Redirection vers l'app mobile avec le résultat
    """
    try:
        # Gérer les erreurs
        if error:
            logger.error(f"OAuth2 error: {error} - {error_description}")
            # Rediriger vers l'app mobile avec l'erreur
            return RedirectResponse(
                url=f"pulse://oura/callback?error={error}&error_description={error_description}"
            )
        
        if not code:
            raise HTTPException(status_code=400, detail="Missing authorization code")
        
        # TODO: Vérifier le state pour la sécurité CSRF
        # Dans une vraie app, comparer avec le state stocké
        
        from oura_oauth2_service import OuraOAuth2Service
        
        oauth_service = OuraOAuth2Service(supabase)
        
        # Échanger le code contre des tokens
        tokens = await oauth_service.exchange_code_for_tokens(code)
        
        if not tokens:
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")
        
        # Pour l'instant, retourner les tokens en JSON
        # Dans une vraie app, stocker les tokens et rediriger vers l'app mobile
        return JSONResponse(content={
            "status": "success",
            "message": "OAuth2 authorization successful",
            "tokens": {
                "access_token": tokens['access_token'][:20] + "...",  # Tronqué pour la sécurité
                "expires_in": tokens['expires_in']
            }
        }, status_code=200)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in OAuth2 callback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/oura/oauth/complete")
async def oura_oauth_complete(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Complète le flux OAuth2 en stockant les tokens
    
    Cette route est appelée par l'app mobile après avoir reçu les tokens
    
    Body:
        {
            "code": "authorization_code_from_oura"
        }
    
    Returns:
        {
            "status": "success",
            "message": "Oura account connected via OAuth2"
        }
    """
    try:
        user_id = verify_jwt_token(authorization=authorization)
        data = await request.json()
        
        code = data.get('code')
        if not code:
            raise HTTPException(status_code=400, detail="code is required")
        
        from oura_oauth2_service import OuraOAuth2Service
        
        oauth_service = OuraOAuth2Service(supabase)
        
        # Échanger le code contre des tokens
        tokens = await oauth_service.exchange_code_for_tokens(code)
        
        if not tokens:
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")
        
        # Stocker les tokens
        success = await oauth_service.store_tokens(
            user_id=user_id,
            access_token=tokens['access_token'],
            refresh_token=tokens['refresh_token'],
            expires_in=tokens['expires_in']
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to store tokens")
        
        return JSONResponse(content={
            "status": "success",
            "message": "Oura account connected via OAuth2",
            "expires_in": tokens['expires_in']
        }, status_code=200)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing OAuth2 flow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ENDPOINTS MÉDICAMENTS ET TRAITEMENTS
# ============================================

@app.get("/api/medications/search")
async def search_medications(
    q: str,
    limit: int = 10,
    authorization: Optional[str] = Header(None)
):
    """
    Recherche de médicaments via API Giygas
    
    Query params:
        q: Terme de recherche (min 2 caractères)
        limit: Nombre max de résultats (défaut: 10, max: 20)
    
    Returns:
        {
            "query": "doliprane",
            "results": [
                {
                    "cis": "60001551",
                    "name": "DOLIPRANE 500 mg, comprimé",
                    "form": "comprimé",
                    "laboratory": "OPELLA HEALTHCARE FRANCE SAS",
                    "active_substance": "PARACETAMOL",
                    "source": "giygas"
                }
            ],
            "count": 2
        }
    """
    # Vérifier JWT (optionnel pour la recherche)
    user_id = None
    if authorization:
        try:
            token_data = verify_jwt_token(authorization=authorization)
            user_id = token_data
        except:
            pass  # Recherche accessible sans auth
    
    if not q or len(q) < 2:
        raise HTTPException(status_code=400, detail="Query trop courte (minimum 2 caractères)")
    
    # Limiter à 20 résultats max
    limit = min(limit, 20)
    
    try:
        results = medication_service.search_medications(q, limit=limit)
        
        return {
            "query": q,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Erreur recherche médicaments: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la recherche")


@app.get("/api/medications/{medication_id}")
async def get_medication_details(
    medication_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Récupère les détails complets d'un médicament via API Giygas
    
    Args:
        medication_id: CIS du médicament (ex: "60001551") OU UUID catalog
    
    Returns:
        {
            "cis": "60001551",
            "name": "DOLIPRANE 500 mg, comprimé",
            "form": "comprimé",
            "laboratory": "OPELLA HEALTHCARE FRANCE SAS",
            "active_substance": "PARACETAMOL",
            "composition": [{"substance": "PARACETAMOL", "dosage": "500", "unite": "mg"}],
            "generics": [{"cis": "...", "name": "...", "laboratory": "..."}],
            "presentations": [{"cip13": "...", "cip7": "...", "price": 2.50, "reimbursement_rate": 65}],
            "conditions": {...}
        }
    """
    # Vérifier JWT (optionnel)
    user_id = None
    if authorization:
        try:
            token_data = verify_jwt_token(authorization=authorization)
            user_id = token_data
        except:
            pass
    
    try:
        # Essayer d'abord de récupérer par CIS directement
        med_data = medication_service.get_by_cis(medication_id)
        
        # Si pas trouvé, essayer comme UUID catalog (fallback)
        if not med_data:
            result = supabase_client.client.table("medications_catalog")\
                .select("external_id")\
                .eq("id", medication_id)\
                .single()\
                .execute()
            
            if result.data:
                cis = result.data["external_id"]
                med_data = medication_service.get_by_cis(cis)
        
        if not med_data:
            raise HTTPException(status_code=404, detail="Médicament non trouvé")
        
        # Retourner les données complètes (composition, génériques, présentations, conditions)
        return med_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération médicament {medication_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")


@app.post("/api/treatments")
async def create_treatment(
    request: Request,
    authorization: str = Header(...)
):
    """
    Créer un nouveau traitement médicamenteux
    
    Body:
        {
            "medication_id": "uuid",  // ID du médicament (catalog) - optionnel
            "medication_name": "Doliprane 500mg",  // Nom - requis
            "dosage": "500",
            "unit": "mg",
            "pills_per_intake": 1,
            "schedule_type": "recurring",  // 'once' ou 'recurring'
            "weekdays": [1, 2, 3, 4, 5],  // Jours (1=lun, 7=dim) - si recurring
            "intake_times": ["08:00", "20:00"],  // Heures - si recurring
            "start_date": "2026-02-04",  // Date de début (YYYY-MM-DD)
            "end_mode": "until_date",  // 'indefinite', 'until_date', 'duration_days'
            "end_date": "2026-03-04",  // Si end_mode='until_date'
            "duration_days": 30,  // Si end_mode='duration_days'
            "notes": "Avec repas"
        }
    
    Returns:
        {"id": "uuid", "message": "Traitement créé"}
    """
    # Vérifier JWT
    user_id = verify_jwt_token(authorization=authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Non authentifié")
    
    # Parser le body
    body = await request.json()
    
    # Validation
    required = ["medication_name", "start_date"]
    for field in required:
        if field not in body:
            raise HTTPException(status_code=400, detail=f"Champ requis manquant: {field}")
    
    schedule_type = body.get("schedule_type", "recurring")
    
    if schedule_type == "recurring":
        if not body.get("intake_times") or len(body.get("intake_times", [])) == 0:
            raise HTTPException(status_code=400, detail="intake_times requis pour récurrence")
    
    end_mode = body.get("end_mode", "indefinite")
    if end_mode == "until_date" and not body.get("end_date"):
        raise HTTPException(status_code=400, detail="end_date requis si end_mode=until_date")
    if end_mode == "duration_days" and not body.get("duration_days"):
        raise HTTPException(status_code=400, detail="duration_days requis si end_mode=duration_days")
    
    # Si medication_id est fourni, vérifier qu'il existe
    medication_catalog_id = body.get("medication_id")
    if medication_catalog_id:
        try:
            check = supabase_client.client.table("medications_catalog")\
                .select("id")\
                .eq("id", medication_catalog_id)\
                .execute()
            
            if not check.data or len(check.data) == 0:
                medication_catalog_id = None
        except:
            medication_catalog_id = None
    
    # Insérer dans user_treatments
    try:
        treatment_data = {
            "user_id": user_id,
            "medication_catalog_id": medication_catalog_id,
            "name": body["medication_name"],
            "dosage": body.get("dosage"),
            "unit": body.get("unit"),
            "pills_per_intake": body.get("pills_per_intake", 1),
            "schedule_type": schedule_type,
            "weekdays": body.get("weekdays") if schedule_type == "recurring" else None,
            "intake_times": body.get("intake_times", []),
            "daily_frequency": len(body.get("intake_times", [])),
            "start_date": body["start_date"],
            "end_mode": end_mode,
            "end_date": body.get("end_date"),
            "duration_days": body.get("duration_days"),
            "notes": body.get("notes"),
            "is_active": True
        }
        
        result = supabase_client.client.table("user_treatments")\
            .insert(treatment_data)\
            .execute()
        
        if result.data and len(result.data) > 0:
            treatment_id = result.data[0]["id"]
            logger.info(f"Traitement créé: {treatment_id} pour user {user_id}")
            return {"id": treatment_id, "message": "Traitement créé avec succès"}
        else:
            raise HTTPException(status_code=500, detail="Erreur création traitement")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur création traitement: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@app.get("/api/treatments")
async def get_user_treatments(
    authorization: str = Header(...),
    active_only: bool = True
):
    """
    Liste des traitements de l'utilisateur
    
    Query params:
        active_only: Filtrer uniquement les traitements actifs (défaut: true)
    
    Returns:
        {
            "treatments": [
                {
                    "id": "uuid",
                    "name": "Doliprane 500mg",
                    "dosage": "500",
                    "unit": "mg",
                    "schedule_type": "recurring",
                    "intake_times": ["08:00", "20:00"],
                    "weekdays": [1, 2, 3, 4, 5],
                    "start_date": "2026-02-04",
                    "end_mode": "indefinite",
                    ...
                }
            ],
            "count": 5
        }
    """
    # Vérifier JWT
    user_id = verify_jwt_token(authorization=authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Non authentifié")
    
    try:
        query = supabase_client.client.table("user_treatments")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("start_date", desc=True)
        
        if active_only:
            query = query.eq("is_active", True)
        
        result = query.execute()
        
        return {
            "treatments": result.data or [],
            "count": len(result.data) if result.data else 0
        }
        
    except Exception as e:
        logger.error(f"Erreur récupération traitements: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")


@app.delete("/api/treatments/{treatment_id}")
async def delete_treatment(
    treatment_id: str,
    authorization: str = Header(...)
):
    """
    Supprime (soft delete) un traitement
    
    Args:
        treatment_id: UUID du traitement
    
    Returns:
        {"message": "Traitement supprimé"}
    """
    # Vérifier JWT
    user_id = verify_jwt_token(authorization=authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Non authentifié")
    
    try:
        # Soft delete (is_active = false)
        result = supabase_client.client.table("user_treatments")\
            .update({"is_active": False, "updated_at": datetime.now().isoformat()})\
            .eq("id", treatment_id)\
            .eq("user_id", user_id)\
            .execute()
        
        if result.data and len(result.data) > 0:
            logger.info(f"Traitement supprimé: {treatment_id} pour user {user_id}")
            return {"message": "Traitement supprimé avec succès"}
        else:
            raise HTTPException(status_code=404, detail="Traitement non trouvé")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur suppression traitement: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")


@app.patch("/api/medications/{medication_id}/dosage")
async def update_medication_dosage(
    medication_id: str,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Modifie la posologie d'un médicament à partir d'une date donnée
    
    Body:
        {
            "new_dosage": "150",
            "new_dosage_unit": "mg",
            "new_pills_per_intake": 1.5,
            "effective_date": "2026-02-06T00:00:00Z"
        }
    """
    try:
        # Vérifier JWT
        user_id = verify_jwt_token(authorization=authorization)
        
        body = await request.json()
        new_dosage = body.get("new_dosage")
        new_dosage_unit = body.get("new_dosage_unit", "mg")
        new_pills_per_intake = body.get("new_pills_per_intake", 1.0)
        effective_date = body.get("effective_date")
        
        if not new_dosage or not effective_date:
            raise HTTPException(status_code=400, detail="new_dosage et effective_date requis")
        
        # Récupérer le médicament pour vérifier qu'il appartient à l'utilisateur
        med_response = supabase_client.client.table('user_medications') \
            .select('*') \
            .eq('id', medication_id) \
            .eq('user_id', user_id) \
            .execute()
        
        if not med_response.data or len(med_response.data) == 0:
            raise HTTPException(status_code=404, detail="Médicament non trouvé")
        
        # Mettre à jour le médicament
        update_response = supabase_client.client.table('user_medications') \
            .update({
                'dosage': str(new_dosage),
                'dosage_unit': new_dosage_unit,
                'pills_per_intake': float(new_pills_per_intake),
                'updated_at': effective_date
            }) \
            .eq('id', medication_id) \
            .execute()
        
        logger.info(f"✅ Posologie modifiée pour le médicament {medication_id}")
        
        return JSONResponse(
            content={
                "success": True,
                "medication_id": medication_id,
                "new_dosage": new_dosage,
                "new_dosage_unit": new_dosage_unit,
                "new_pills_per_intake": new_pills_per_intake,
                "effective_date": effective_date
            },
            status_code=200
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de la modification de posologie: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/medications/scan")
async def scan_medication_barcode(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Scan de code-barres GS1 DataMatrix (boîte de médicament)
    
    Convertit un code GTIN en CIP13 puis récupère le médicament
    
    Body:
        {
            "gtin": "34009300015517",  // Code GTIN (13 ou 14 chiffres)
            "barcode_type": "gs1_datamatrix"  // Type de code-barres (optionnel)
        }
    
    Returns:
        {
            "gtin": "34009300015517",
            "cip13": "3400930001551",
            "medication": {
                "cis": "60001551",
                "name": "DOLIPRANE 500 mg, comprimé",
                ...
            }
        }
    """
    # Vérifier JWT (optionnel)
    user_id = None
    if authorization:
        try:
            token_data = verify_jwt_token(authorization=authorization)
            user_id = token_data
        except:
            pass
    
    try:
        body = await request.json()
        gtin = body.get("gtin")
        
        if not gtin:
            raise HTTPException(status_code=400, detail="GTIN requis")
        
        # Convertir GTIN → CIP13
        cip13 = medication_service.parse_gtin_to_cip13(gtin)
        
        if not cip13:
            raise HTTPException(
                status_code=400, 
                detail=f"GTIN invalide ou non convertible en CIP13: {gtin}"
            )
        
        logger.info(f"[Scan] GTIN {gtin} → CIP13 {cip13}")
        
        # Récupérer le médicament par CIP13
        medication = medication_service.get_by_cip13(cip13)
        
        if not medication:
            # Fallback 1 : chercher dans les présentations connues (cache Supabase)
            pres_result = supabase_client.client.table("drug_presentations")\
                .select("*, medications_catalog!inner(external_id)")\
                .eq("cip13", cip13)\
                .limit(1)\
                .execute()
            
            if pres_result.data and len(pres_result.data) > 0:
                cis = pres_result.data[0]["medications_catalog"]["external_id"]
                logger.info(f"[Scan] CIP13 {cip13} → CIS {cis} (depuis cache Supabase)")
                medication = medication_service.get_by_cis(cis)
        
        if not medication:
            # Fallback 2 : Recherche dans la base ANSM par CIP13
            logger.info(f"[Scan] Recherche CIP13 {cip13} dans base ANSM...")
            
            ansm_result = supabase_client.client.table("ansm_presentations")\
                .select("cis, libelle, statut")\
                .eq("cip13", cip13)\
                .limit(1)\
                .execute()
            
            if ansm_result.data and len(ansm_result.data) > 0:
                ansm_data = ansm_result.data[0]
                cis = ansm_data.get("cis")
                libelle = ansm_data.get("libelle", "")
                statut = ansm_data.get("statut", "")
                
                logger.info(f"[Scan] ✅ CIP13 {cip13} trouvé dans ANSM → CIS: {cis}")
                logger.info(f"[Scan] Libellé: {libelle}")
                
                # Récupérer les détails complets depuis Giygas si possible
                medication = medication_service.get_by_cis(cis)
                
                if not medication:
                    # Si pas dans Giygas, rechercher par nom dans le fichier CIS_MITM
                    logger.info(f"[Scan] CIS {cis} non trouvé dans Giygas, recherche du nom...")
                    
                    # Récupérer le nom depuis medications_catalog si déjà en base
                    med_catalog = supabase_client.client.table("medications_catalog")\
                        .select("name, form, laboratory")\
                        .eq("external_id", cis)\
                        .eq("source", "giygas")\
                        .limit(1)\
                        .execute()
                    
                    if med_catalog.data and len(med_catalog.data) > 0:
                        catalog_data = med_catalog.data[0]
                        medication = {
                            "cis": cis,
                            "name": catalog_data.get("name", f"Médicament {cis}"),
                            "form": catalog_data.get("form"),
                            "laboratory": catalog_data.get("laboratory"),
                            "presentations": [{
                                "cip13": cip13,
                                "label": libelle
                            }],
                            "source": "ansm"
                        }
                        logger.info(f"[Scan] ✅ Médicament créé depuis catalog: {medication['name']}")
        
        if not medication:
            raise HTTPException(
                status_code=404, 
                detail=f"Médicament non trouvé pour CIP13: {cip13}"
            )
        
        return {
            "gtin": gtin,
            "cip13": cip13,
            "medication": medication
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur scan code-barres: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


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
