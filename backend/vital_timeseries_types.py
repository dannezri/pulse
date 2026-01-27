"""
Vital Timeseries Types - Mapping complet des 52+ types de données Vital
Basé sur la documentation officielle Vital
"""

from typing import Dict, Optional

# Mapping des types Vital vers types de métriques normalisés
VITAL_TIMESERIES_TYPES: Dict[str, Dict[str, any]] = {
    # ========== ACTIVITY ==========
    "calories_active": {
        "metric_type": "active_calories",
        "category": "activity",
        "unit": "kcal",
        "value_field": "value"
    },
    "calories_basal": {
        "metric_type": "basal_calories",
        "category": "activity",
        "unit": "kcal",
        "value_field": "value"
    },
    "distance": {
        "metric_type": "distance",
        "category": "activity",
        "unit": "m",  # Convertir en km si > 1000
        "value_field": "value"
    },
    "fall": {
        "metric_type": "fall",
        "category": "activity",
        "unit": "count",
        "value_field": "value"
    },
    "floors_climbed": {
        "metric_type": "floors_climbed",
        "category": "activity",
        "unit": "count",
        "value_field": "value"
    },
    "stand_duration": {
        "metric_type": "stand_duration",
        "category": "activity",
        "unit": "minutes",
        "value_field": "value"
    },
    "stand_hour": {
        "metric_type": "stand_hour",
        "category": "activity",
        "unit": "hours",
        "value_field": "value"
    },
    "steps": {
        "metric_type": "steps",
        "category": "activity",
        "unit": "count",
        "value_field": "value"
    },
    "vo2_max": {
        "metric_type": "vo2_max",
        "category": "activity",
        "unit": "mL/kg/min",
        "value_field": "value"
    },
    "wheelchair_push": {
        "metric_type": "wheelchair_push",
        "category": "activity",
        "unit": "count",
        "value_field": "value"
    },
    "workout_duration": {
        "metric_type": "workout_duration",
        "category": "activity",
        "unit": "minutes",
        "value_field": "value"
    },
    
    # ========== BODY ==========
    "basal_body_temperature": {
        "metric_type": "basal_body_temperature",
        "category": "body",
        "unit": "°C",
        "value_field": "value"
    },
    "body_mass_index": {
        "metric_type": "bmi",
        "category": "body",
        "unit": "kg/m²",
        "value_field": "value"
    },
    "body_temperature": {
        "metric_type": "body_temperature",
        "category": "body",
        "unit": "°C",
        "value_field": "value"
    },
    "body_temperature_delta": {
        "metric_type": "body_temperature_delta",
        "category": "body",
        "unit": "°C",
        "value_field": "value"
    },
    "fat": {
        "metric_type": "body_fat",
        "category": "body",
        "unit": "%",
        "value_field": "value"
    },
    "lean_body_mass": {
        "metric_type": "lean_body_mass",
        "category": "body",
        "unit": "kg",
        "value_field": "value"
    },
    "waist_circumference": {
        "metric_type": "waist_circumference",
        "category": "body",
        "unit": "cm",
        "value_field": "value"
    },
    "weight": {
        "metric_type": "weight",
        "category": "body",
        "unit": "kg",
        "value_field": "value"
    },
    
    # ========== VITALS ==========
    "afib_burden": {
        "metric_type": "afib_burden",
        "category": "vitals",
        "unit": "%",
        "value_field": "value"
    },
    "blood_oxygen": {
        "metric_type": "spo2",
        "category": "vitals",
        "unit": "%",
        "value_field": "value"
    },
    "blood_pressure": {
        "metric_type": "blood_pressure",
        "category": "vitals",
        "unit": "mmHg",
        "value_field": "systolic",
        "extra_fields": {"diastolic": "diastolic"}
    },
    "cholesterol": {
        "metric_type": "cholesterol",
        "category": "vitals",
        "unit": "mg/dL",
        "value_field": "value"
    },
    "electrocardiogram_voltage": {
        "metric_type": "ecg_voltage",
        "category": "vitals",
        "unit": "mV",
        "value_field": "value"
    },
    "force_expiratory_volume_1": {
        "metric_type": "fev1",
        "category": "vitals",
        "unit": "L",
        "value_field": "value"
    },
    "forced_vital_capacity": {
        "metric_type": "fvc",
        "category": "vitals",
        "unit": "L",
        "value_field": "value"
    },
    "glucose": {
        "metric_type": "glucose",
        "category": "vitals",
        "unit": "mg/dL",
        "value_field": "value"
    },
    "heart_rate_alert": {
        "metric_type": "heart_rate_alert",
        "category": "vitals",
        "unit": "bpm",
        "value_field": "bpm"
    },
    "heart_rate_recovery_one_minute": {
        "metric_type": "hr_recovery_1min",
        "category": "vitals",
        "unit": "bpm",
        "value_field": "value"
    },
    "heartrate": {
        "metric_type": "heart_rate",
        "category": "vitals",
        "unit": "bpm",
        "value_field": "bpm"
    },
    "hrv": {
        "metric_type": "hrv",
        "category": "vitals",
        "unit": "ms",
        "value_field": "value"
    },
    "ige": {
        "metric_type": "ige",
        "category": "vitals",
        "unit": "IU/mL",
        "value_field": "value"
    },
    "igg": {
        "metric_type": "igg",
        "category": "vitals",
        "unit": "mg/dL",
        "value_field": "value"
    },
    "inhaler_usage": {
        "metric_type": "inhaler_usage",
        "category": "vitals",
        "unit": "count",
        "value_field": "value"
    },
    "insulin_injection": {
        "metric_type": "insulin",
        "category": "vitals",
        "unit": "units",
        "value_field": "value"
    },
    "peak_expiratory_flow_rate": {
        "metric_type": "pef",
        "category": "vitals",
        "unit": "L/min",
        "value_field": "value"
    },
    "respiratory_rate": {
        "metric_type": "respiratory_rate",
        "category": "vitals",
        "unit": "breaths/min",
        "value_field": "value"
    },
    
    # ========== WELLNESS ==========
    "daylight_exposure": {
        "metric_type": "daylight_exposure",
        "category": "wellness",
        "unit": "minutes",
        "value_field": "value"
    },
    "handwashing": {
        "metric_type": "handwashing",
        "category": "wellness",
        "unit": "count",
        "value_field": "value"
    },
    "mindfulness_minutes": {
        "metric_type": "mindfulness",
        "category": "wellness",
        "unit": "minutes",
        "value_field": "value"
    },
    "sleep_apnea_alert": {
        "metric_type": "sleep_apnea",
        "category": "wellness",
        "unit": "events",
        "value_field": "value"
    },
    "sleep_breathing_disturbance": {
        "metric_type": "sleep_breathing_disturbance",
        "category": "wellness",
        "unit": "events",
        "value_field": "value"
    },
    "stress_level": {
        "metric_type": "stress",
        "category": "wellness",
        "unit": "score",
        "value_field": "value"
    },
    "uv_exposure": {
        "metric_type": "uv_exposure",
        "category": "wellness",
        "unit": "index",
        "value_field": "value"
    },
    
    # ========== NUTRITION ==========
    "caffeine": {
        "metric_type": "caffeine",
        "category": "nutrition",
        "unit": "mg",
        "value_field": "value"
    },
    "carbohydrates": {
        "metric_type": "carbs",
        "category": "nutrition",
        "unit": "g",
        "value_field": "value"
    },
    "water": {
        "metric_type": "water",
        "category": "nutrition",
        "unit": "mL",
        "value_field": "value"
    },
    
    # ========== DIARY ==========
    "note": {
        "metric_type": "note",
        "category": "diary",
        "unit": "text",
        "value_field": "text"
    },
    
    # ========== WORKOUT STREAM ==========
    "workout_distance": {
        "metric_type": "workout_distance",
        "category": "workout",
        "unit": "m",
        "value_field": "value"
    },
    "workout_swimming_stroke": {
        "metric_type": "swimming_stroke",
        "category": "workout",
        "unit": "count",
        "value_field": "value"
    }
}


def get_metric_config(timeseries_type: str) -> Optional[Dict]:
    """
    Récupère la configuration pour un type timeseries Vital
    
    Args:
        timeseries_type: Type de données Vital (ex: "heartrate", "steps")
    
    Returns:
        Dict avec metric_type, category, unit, value_field
    """
    return VITAL_TIMESERIES_TYPES.get(timeseries_type)


def is_supported_type(timeseries_type: str) -> bool:
    """
    Vérifie si un type timeseries est supporté
    """
    return timeseries_type in VITAL_TIMESERIES_TYPES


def get_all_supported_types() -> list:
    """
    Retourne la liste de tous les types supportés
    """
    return list(VITAL_TIMESERIES_TYPES.keys())


def get_types_by_category(category: str) -> list:
    """
    Retourne tous les types d'une catégorie
    """
    return [
        ts_type 
        for ts_type, config in VITAL_TIMESERIES_TYPES.items() 
        if config["category"] == category
    ]
