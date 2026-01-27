"""
Système de Transformation Santé : Transforme les données unifiées d'Open Wearables
en métriques santé (unités, agrégats, baselines, anomalies, contexte)

═══════════════════════════════════════════════════════════════════════════════
SÉPARATION DES RESPONSABILITÉS
═══════════════════════════════════════════════════════════════════════════════

OPEN WEARABLES (Ingestion Engine) :
  ✅ Unifie les structures JSON (formats providers → format commun)
  ✅ Normalise les timestamps (ISO 8601)
  ✅ Mappe les champs (ex: "heartRate" → "hr", "heart_rate" → "hr")
  ✅ Format commun cohérent : {"hr": [...], "sleep": {...}, "steps": [...]}
  
  ❌ NE FAIT PAS :
     - Calcul de baselines
     - Détection d'anomalies
     - Agrégation par jour
     - Contexte santé
     - Conversion d'unités (reçoit déjà des unités cohérentes)

PULSE (DataNormalizer) :
  ✅ Transforme en métriques santé :
     - Unités standard (bpm, ms, minutes) si nécessaire
     - Agrégats (moyennes, min, max, resting)
     - Baselines avec fallback automatique (7j → 14j → 30j)
     - Anomalies avec niveau de confiance
     - Contexte santé (heure, jour, tendances)
     - Qualité des données (low/medium/high)
     - Profil santé JSON pour l'IA
  
  ❌ NE FAIT PAS :
     - Parsing des formats providers
     - Mapping des champs providers
     - Gestion des timestamps providers

Cette séparation garantit que la logique "santé" (baselines, anomalies, contexte)
est centralisée UNIQUEMENT dans Pulse. Open Wearables gère uniquement l'unification
structurelle des formats providers.

Règle d'or : Un seul endroit pour la logique "santé" = Pulse
═══════════════════════════════════════════════════════════════════════════════
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import logging

# Utiliser dateutil pour un parsing robuste des dates ISO
try:
    from dateutil import parser as date_parser
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataNormalizer:
    """
    Transforme les données unifiées d'Open Wearables en métriques santé.
    
    Responsabilité : Toute la logique "santé" (baselines, anomalies, contexte)
    est centralisée ici. Open Wearables gère uniquement l'unification structurelle.
    """
    
    # Versioning
    PROFILE_VERSION = 1  # Version du format JSON du profil
    NORMALIZER_VERSION = "1.0.0"  # Version du normalizer (semver)
    SCHEMA_VERSION = "1.0"  # Version du schéma de données source
    
    # Unités standard
    UNITS = {
        "hr": "bpm",  # Heart Rate en battements par minute
        "hrv": "ms",  # HRV en millisecondes
        "sleep_duration": "minutes",
        "steps": "count",
        "distance": "meters",
        "calories": "kcal"
    }
    
    def __init__(self):
        self.normalized_data = {}
    
    def normalize_open_wearables_data(self, raw_data: Dict) -> Dict:
        """
        Transforme les données unifiées d'Open Wearables en métriques santé.
        
        Open Wearables a déjà :
        - Unifié les structures JSON (formats providers → format commun)
        - Normalisé les timestamps (ISO 8601)
        - Mappé les champs (ex: "heart_rate" → "hr")
        
        Pulse transforme ce format unifié en :
        - Unités standard (bpm, ms, minutes)
        - Agrégats (moyennes, min, max)
        - Métriques santé prêtes pour baselines/anomalies
        
        Format attendu (unifié par Open Wearables):
        {
            "hr": [{"value": 72, "timestamp": "2024-01-15T10:00:00Z"}],
            "hrv": [{"value": 65, "timestamp": "2024-01-15T10:00:00Z"}],
            "sleep": {"duration_seconds": 28800, "start_time": "..."},
            "steps": [{"value": 8500, "timestamp": "..."}]
        }
        """
        normalized = {
            "source": "open_wearables",
            "date": raw_data.get("date", datetime.now().isoformat()),
            "metrics": {}
        }
        
        # Normalisation des données de sommeil
        # Open Wearables fournit déjà duration_seconds en format cohérent
        if "sleep" in raw_data and raw_data["sleep"]:
            sleep_data = raw_data["sleep"]
            if isinstance(sleep_data, dict):
                duration_seconds = sleep_data.get("duration_seconds") or sleep_data.get("duration", 0)
                normalized["metrics"]["sleep"] = {
                    "duration_minutes": self._convert_to_minutes(duration_seconds),
                    "quality_score": sleep_data.get("score") or sleep_data.get("quality_score", 0),
                    "deep_sleep_minutes": self._convert_to_minutes(sleep_data.get("deep_sleep_seconds", 0)),
                    "rem_sleep_minutes": self._convert_to_minutes(sleep_data.get("rem_sleep_seconds", 0)),
                    "light_sleep_minutes": self._convert_to_minutes(sleep_data.get("light_sleep_seconds", 0)),
                    "sleep_efficiency": sleep_data.get("efficiency", 0),
                    "bedtime": sleep_data.get("start_time", ""),
                    "wake_time": sleep_data.get("end_time", "")
                }
        
        # Normalisation des données de fréquence cardiaque
        # Open Wearables fournit déjà "hr" en format cohérent
        if "heart_rate" in raw_data and raw_data["heart_rate"]:
            hr_data = raw_data["heart_rate"]
            if isinstance(hr_data, list):
                hr_values = []
                for entry in hr_data:
                    hr_value = entry.get("value") or entry.get("hr") or entry.get("heart_rate")
                    if hr_value:
                        hr_values.append(float(hr_value))
                
                if hr_values:
                    normalized["metrics"]["heart_rate"] = {
                        "average_bpm": sum(hr_values) / len(hr_values),
                        "resting_bpm": min(hr_values) if hr_values else None,
                        "max_bpm": max(hr_values),
                        "min_bpm": min(hr_values)
                    }
        elif "hr" in raw_data and raw_data["hr"]:
            # Format direct "hr" (unifié par Open Wearables)
            hr_data = raw_data["hr"]
            if isinstance(hr_data, list):
                hr_values = []
                for entry in hr_data:
                    hr_value = entry.get("value") or entry.get("hr")
                    if hr_value:
                        hr_values.append(float(hr_value))
                
                if hr_values:
                    normalized["metrics"]["heart_rate"] = {
                        "average_bpm": sum(hr_values) / len(hr_values),
                        "resting_bpm": min(hr_values) if hr_values else None,
                        "max_bpm": max(hr_values),
                        "min_bpm": min(hr_values)
                    }
        
        # Normalisation des données HRV
        # Open Wearables fournit déjà "hrv" en format cohérent
        if "hrv" in raw_data and raw_data["hrv"]:
            hrv_data = raw_data["hrv"]
            if isinstance(hrv_data, list):
                hrv_values = []
                for entry in hrv_data:
                    hrv_value = entry.get("value") or entry.get("hrv")
                    if hrv_value:
                        hrv_values.append(float(hrv_value))
                
                if hrv_values:
                    normalized["metrics"]["hrv"] = {
                        "average_ms": sum(hrv_values) / len(hrv_values),
                        "max_ms": max(hrv_values),
                        "min_ms": min(hrv_values),
                        "latest_ms": hrv_values[-1] if hrv_values else None
                    }
        
        # Normalisation des données d'activité
        # Open Wearables fournit déjà "activity" ou "steps" en format cohérent
        if "activity" in raw_data and raw_data["activity"]:
            activity_data = raw_data["activity"]
            if isinstance(activity_data, dict):
                normalized["metrics"]["activity"] = {
                    "steps": activity_data.get("steps", 0),
                    "distance_meters": activity_data.get("distance_meters", 0),
                    "calories_kcal": activity_data.get("calories", 0),
                    "active_minutes": activity_data.get("active_minutes", 0)
                }
        elif "steps" in raw_data and raw_data["steps"]:
            # Format direct "steps" (unifié par Open Wearables)
            steps_data = raw_data["steps"]
            if isinstance(steps_data, list):
                # Somme des pas sur la journée
                total_steps = sum(entry.get("value", entry.get("steps", 0)) for entry in steps_data if isinstance(entry, dict))
                normalized["metrics"]["activity"] = {
                    "steps": total_steps,
                    "distance_meters": 0,
                    "calories_kcal": 0,
                    "active_minutes": 0
                }
            elif isinstance(steps_data, (int, float)):
                normalized["metrics"]["activity"] = {
                    "steps": int(steps_data),
                    "distance_meters": 0,
                    "calories_kcal": 0,
                    "active_minutes": 0
                }
        
        return normalized
    
    def _convert_to_minutes(self, seconds: float) -> int:
        """Convertit les secondes en minutes"""
        return int(seconds / 60) if seconds else 0
    
    def calculate_baseline(
        self,
        historical_data: List[Dict],
        metric_type: str,
        days: int = 7,
        min_data_points: int = 3
    ) -> Tuple[Optional[float], Dict]:
        """
        Calcule la baseline (moyenne glissante) avec fallback automatique
        en cas de trous dans les données.
        
        Args:
            historical_data: Données historiques
            metric_type: Type de métrique ('hrv', 'hr', 'sleep')
            days: Nombre de jours cible (7 par défaut)
            min_data_points: Nombre minimum de points de données requis
        
        Returns:
            Tuple (baseline_value, metadata) où metadata contient:
            - actual_days: Nombre de jours effectivement utilisés
            - data_points: Nombre de points de données
            - data_quality: 'high', 'medium', 'low'
            - fallback_used: True si fallback a été utilisé
        """
        if not historical_data:
            return None, {
                "actual_days": 0,
                "data_points": 0,
                "data_quality": "low",
                "fallback_used": False
            }
        
        # Stratégie de fallback : 7j → 14j → 30j
        fallback_periods = [7, 14, 30]
        metadata = {
            "actual_days": 0,
            "data_points": 0,
            "data_quality": "low",
            "fallback_used": False
        }
        
        # Essayer chaque période jusqu'à avoir assez de données
        for period_days in fallback_periods:
            if period_days < days:
                continue  # Ne pas utiliser une période plus courte que demandée
            
            cutoff_date = datetime.now() - timedelta(days=period_days)
            recent_data = []
            for d in historical_data:
                date_str = d.get("date", "")
                if not date_str:
                    continue
                try:
                    # Parser la date (peut être juste une date YYYY-MM-DD ou un datetime complet)
                    if DATEUTIL_AVAILABLE:
                        entry_date = date_parser.isoparse(date_str)
                    else:
                        # Fallback : essayer fromisoformat
                        entry_date = datetime.fromisoformat(date_str)
                    # Si c'est juste une date (sans heure), comparer avec la date de cutoff
                    if entry_date.date() >= cutoff_date.date():
                        recent_data.append(d)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse date '{date_str}': {e}")
                    continue
            
            if not recent_data:
                continue
            
            # Extraire les valeurs de la métrique
            values = []
            for entry in recent_data:
                metrics = entry.get("metrics", {})
                
                # Format brut (floats directement) - venant de get_historical_biometrics
                if metric_type == "hrv" and "hrv" in metrics:
                    hrv_value = metrics["hrv"]
                    if isinstance(hrv_value, (int, float)):
                        values.append(float(hrv_value))
                    elif isinstance(hrv_value, dict):
                        values.append(hrv_value.get("average_ms"))
                elif metric_type == "hr" and "hr" in metrics:
                    hr_value = metrics["hr"]
                    if isinstance(hr_value, (int, float)):
                        values.append(float(hr_value))
                    elif isinstance(hr_value, dict):
                        values.append(hr_value.get("resting_bpm"))
                elif metric_type == "sleep":
                    # Chercher sleep_duration (format brut) ou sleep (format normalisé)
                    if "sleep_duration" in metrics:
                        sleep_value = metrics["sleep_duration"]
                        if isinstance(sleep_value, (int, float)):
                            values.append(float(sleep_value))  # Déjà en minutes
                    elif "sleep" in metrics:
                        sleep_value = metrics["sleep"]
                        if isinstance(sleep_value, dict):
                            values.append(sleep_value.get("duration_minutes"))
                        elif isinstance(sleep_value, (int, float)):
                            values.append(float(sleep_value))
            
            # Filtrer les None
            values = [v for v in values if v is not None]
            
            # Si on a assez de données, utiliser cette période
            if len(values) >= min_data_points:
                baseline = sum(values) / len(values)
                metadata["actual_days"] = period_days
                metadata["data_points"] = len(values)
                metadata["fallback_used"] = period_days > days
                
                # Déterminer la qualité des données
                coverage_ratio = len(values) / period_days
                if coverage_ratio >= 0.7:  # ≥70% de couverture
                    metadata["data_quality"] = "high"
                elif coverage_ratio >= 0.4:  # ≥40% de couverture
                    metadata["data_quality"] = "medium"
                else:  # <40% de couverture
                    metadata["data_quality"] = "low"
                
                return baseline, metadata
        
        # Pas assez de données même avec fallback
        return None, metadata
    
    def create_health_profile(
        self,
        today_data: Dict,
        baseline_data: Dict,
        user_goal: str = "energy"
    ) -> Dict:
        """
        Crée le "Profil de Santé JSON" final pour l'IA
        C'est ce format qui sera envoyé au LLM
        
        Le profil inclut les métadonnées de version pour permettre
        l'évolution du schéma sans casser l'application.
        """
        # Calculer la qualité globale des données
        data_quality = self._calculate_overall_data_quality(today_data, baseline_data)
        
        # Détecter les anomalies avec confiance
        anomalies = self._detect_anomalies(today_data, baseline_data)
        
        profile = {
            "timestamp": datetime.now().isoformat(),
            "user_goal": user_goal,
            "current_metrics": today_data.get("metrics", {}),
            "baselines": baseline_data,
            "anomalies": anomalies,
            "context": self._build_context(today_data, baseline_data),
            "data_quality": data_quality,  # Qualité globale des données
            # Métadonnées de version
            "_version": {
                "profile_version": self.PROFILE_VERSION,
                "normalizer_version": self.NORMALIZER_VERSION,
                "schema_version": self.SCHEMA_VERSION
            }
        }
        
        return profile
    
    def get_version_info(self) -> Dict:
        """
        Retourne les informations de version du normalizer
        Utile pour le debugging et la traçabilité
        """
        return {
            "profile_version": self.PROFILE_VERSION,
            "normalizer_version": self.NORMALIZER_VERSION,
            "schema_version": self.SCHEMA_VERSION
        }
    
    def _calculate_overall_data_quality(
        self,
        today_data: Dict,
        baseline_data: Dict
    ) -> str:
        """
        Calcule la qualité globale des données (low/medium/high)
        Basé sur la disponibilité des métriques et la qualité des baselines
        """
        quality_scores = []
        
        # Vérifier la disponibilité des métriques du jour
        today_metrics = today_data.get("metrics", {})
        has_hr = "heart_rate" in today_metrics or "hr" in today_metrics
        has_hrv = "hrv" in today_metrics
        has_sleep = "sleep" in today_metrics
        has_activity = "activity" in today_metrics or "steps" in today_metrics
        
        metrics_count = sum([has_hr, has_hrv, has_sleep, has_activity])
        if metrics_count >= 3:
            quality_scores.append("high")
        elif metrics_count >= 2:
            quality_scores.append("medium")
        else:
            quality_scores.append("low")
        
        # Vérifier la qualité des baselines
        baseline_qualities = []
        if "hrv_baseline_metadata" in baseline_data:
            baseline_qualities.append(baseline_data["hrv_baseline_metadata"].get("data_quality", "low"))
        if "hr_baseline_metadata" in baseline_data:
            baseline_qualities.append(baseline_data["hr_baseline_metadata"].get("data_quality", "low"))
        if "sleep_baseline_metadata" in baseline_data:
            baseline_qualities.append(baseline_data["sleep_baseline_metadata"].get("data_quality", "low"))
        
        if baseline_qualities:
            avg_baseline_quality = sum(
                3 if q == "high" else 2 if q == "medium" else 1 
                for q in baseline_qualities
            ) / len(baseline_qualities)
            
            if avg_baseline_quality >= 2.5:
                quality_scores.append("high")
            elif avg_baseline_quality >= 1.5:
                quality_scores.append("medium")
            else:
                quality_scores.append("low")
        
        # Qualité globale = minimum des qualités (conservatif)
        if "high" in quality_scores and "low" not in quality_scores:
            return "high"
        elif "medium" in quality_scores and "low" not in quality_scores:
            return "medium"
        else:
            return "low"
    
    def _detect_anomalies(
        self,
        today_data: Dict,
        baseline_data: Dict
    ) -> List[Dict]:
        """
        Détecte les anomalies par rapport à la baseline avec niveau de confiance
        Ex: HRV qui chute de 30%, sommeil réduit de 2h
        
        Chaque anomalie inclut un champ "confidence" (low/high) basé sur
        la qualité des données utilisées pour la baseline.
        """
        anomalies = []
        today_metrics = today_data.get("metrics", {})
        
        # Anomalie HRV
        if "hrv" in today_metrics and "hrv_baseline" in baseline_data:
            current_hrv = today_metrics["hrv"].get("average_ms")
            baseline_hrv = baseline_data.get("hrv_baseline")
            baseline_metadata = baseline_data.get("hrv_baseline_metadata", {})
            
            if current_hrv and baseline_hrv:
                drop_percentage = ((baseline_hrv - current_hrv) / baseline_hrv) * 100
                if drop_percentage > 20:  # Chute de plus de 20%
                    # Confiance basée sur la qualité de la baseline
                    confidence = "high" if baseline_metadata.get("data_quality") == "high" else "low"
                    
                    anomalies.append({
                        "type": "hrv_drop",
                        "severity": "high" if drop_percentage > 30 else "medium",
                        "confidence": confidence,
                        "current": current_hrv,
                        "baseline": baseline_hrv,
                        "drop_percentage": round(drop_percentage, 2),
                        "baseline_quality": baseline_metadata.get("data_quality", "low"),
                        "baseline_data_points": baseline_metadata.get("data_points", 0)
                    })
        
        # Anomalie sommeil
        if "sleep" in today_metrics and "sleep_baseline" in baseline_data:
            current_sleep = today_metrics["sleep"].get("duration_minutes")
            baseline_sleep = baseline_data.get("sleep_baseline")
            baseline_metadata = baseline_data.get("sleep_baseline_metadata", {})
            
            if current_sleep and baseline_sleep:
                sleep_deficit = baseline_sleep - current_sleep
                if sleep_deficit > 60:  # Déficit de plus d'1h
                    confidence = "high" if baseline_metadata.get("data_quality") == "high" else "low"
                    
                    anomalies.append({
                        "type": "sleep_deficit",
                        "severity": "high" if sleep_deficit > 120 else "medium",
                        "confidence": confidence,
                        "current_minutes": current_sleep,
                        "baseline_minutes": baseline_sleep,
                        "deficit_minutes": sleep_deficit,
                        "baseline_quality": baseline_metadata.get("data_quality", "low"),
                        "baseline_data_points": baseline_metadata.get("data_points", 0)
                    })
        
        # Anomalie fréquence cardiaque au repos
        if "heart_rate" in today_metrics and "hr_baseline" in baseline_data:
            current_hr = today_metrics["heart_rate"].get("resting_bpm")
            baseline_hr = baseline_data.get("hr_baseline")
            baseline_metadata = baseline_data.get("hr_baseline_metadata", {})
            
            if current_hr and baseline_hr:
                hr_increase = current_hr - baseline_hr
                if hr_increase > 10:  # Augmentation de plus de 10 bpm
                    confidence = "high" if baseline_metadata.get("data_quality") == "high" else "low"
                    
                    anomalies.append({
                        "type": "elevated_resting_hr",
                        "severity": "medium",
                        "confidence": confidence,
                        "current_bpm": current_hr,
                        "baseline_bpm": baseline_hr,
                        "increase": hr_increase,
                        "baseline_quality": baseline_metadata.get("data_quality", "low"),
                        "baseline_data_points": baseline_metadata.get("data_points", 0)
                    })
        
        return anomalies
    
    def _build_context(
        self,
        today_data: Dict,
        baseline_data: Dict
    ) -> Dict:
        """
        Construit le contexte pour l'IA
        Inclut l'heure actuelle, les tendances, etc.
        """
        current_time = datetime.now()
        
        context = {
            "current_time": current_time.strftime("%H:%M"),
            "day_of_week": current_time.strftime("%A"),
            "is_weekend": current_time.weekday() >= 5,
            "time_of_day": self._get_time_of_day(current_time),
            "trends": self._calculate_trends(today_data, baseline_data)
        }
        
        return context
    
    def _get_time_of_day(self, dt: datetime) -> str:
        """Détermine la période de la journée"""
        hour = dt.hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"
    
    def _calculate_trends(
        self,
        today_data: Dict,
        baseline_data: Dict
    ) -> Dict:
        """Calcule les tendances (amélioration/dégradation)"""
        trends = {}
        today_metrics = today_data.get("metrics", {})
        
        # Tendance HRV
        if "hrv" in today_metrics and "hrv_baseline" in baseline_data:
            current = today_metrics["hrv"].get("average_ms")
            baseline = baseline_data.get("hrv_baseline")
            if current and baseline:
                trends["hrv"] = "improving" if current > baseline * 1.1 else "declining" if current < baseline * 0.9 else "stable"
        
        # Tendance sommeil
        if "sleep" in today_metrics and "sleep_baseline" in baseline_data:
            current = today_metrics["sleep"].get("duration_minutes")
            baseline = baseline_data.get("sleep_baseline")
            if current and baseline:
                trends["sleep"] = "improving" if current > baseline * 1.1 else "declining" if current < baseline * 0.9 else "stable"
        
        return trends
