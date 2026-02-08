"""
Intraday Energy Forecast Service - Prévision d'énergie reste de la journée

Génère une courbe d'énergie de maintenant → fin de journée avec:
- Points toutes les 15-30 minutes
- Événements du calendrier avec impact estimé
- Fenêtres de risque (creux prévus)
- Notes explicatives

Heuristiques V1 (MVP - simple et explicable):
- Base: score daily_energy du jour
- Décroissance naturelle dans la journée
- Impact des événements calendrier (réunion, sport, déplacement)
- Modulation selon recovery, sleep_debt, chronotype

Usage: Appelé par GET /api/energy/intraday et intégré dans /api/brief
"""

import os
from datetime import datetime, time, timedelta, date, timezone
from typing import Dict, List, Optional, Tuple
from supabase import create_client, Client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)

# Configuration
INTERVAL_MINUTES = 30  # Points toutes les 30 minutes
MIN_CONFIDENCE = 0.50  # Confiance minimale pour stocker


def classify_event_type(event: Dict) -> Tuple[str, List[str]]:
    """
    Classifie un événement calendrier selon son titre/description
    
    Returns:
        (type, tags) où type = 'meeting' | 'sport' | 'travel' | 'focus' | 'social' | 'other'
        tags = liste de tags descriptifs
    """
    title = event.get('title', '').lower()
    notes = event.get('notes', '').lower()
    location = event.get('location', '').lower()
    
    text = f"{title} {notes} {location}"
    
    # Keywords par catégorie
    meeting_keywords = ['réunion', 'meeting', 'call', 'visio', 'conf', 'présentation', 'rdv', 'rendez-vous']
    sport_keywords = ['sport', 'gym', 'course', 'running', 'yoga', 'fitness', 'training', 'entraînement']
    travel_keywords = ['vol', 'flight', 'train', 'avion', 'déplacement', 'voyage', 'trajet']
    focus_keywords = ['focus', 'deep work', 'coding', 'dev', 'écriture', 'rédaction', 'projet']
    social_keywords = ['dîner', 'déjeuner', 'lunch', 'dinner', 'apéro', 'café', 'social']
    
    # Classification
    if any(kw in text for kw in sport_keywords):
        return 'sport', ['sport', 'physical']
    elif any(kw in text for kw in travel_keywords):
        return 'travel', ['travel', 'logistics']
    elif any(kw in text for kw in focus_keywords):
        return 'focus', ['focus', 'deep_work']
    elif any(kw in text for kw in social_keywords):
        return 'social', ['social', 'low_stress']
    elif any(kw in text for kw in meeting_keywords):
        # Sous-classification meeting
        if any(word in text for word in ['client', 'important', 'stratégique', 'board']):
            return 'meeting', ['meeting', 'high_focus', 'high_stress']
        else:
            return 'meeting', ['meeting', 'moderate_focus']
    else:
        return 'other', ['other']


def estimate_event_impact(
    event: Dict,
    event_type: str,
    tags: List[str],
    base_energy: float,
    recovery: float,
    sleep_debt: float
) -> Tuple[int, float]:
    """
    Estime l'impact d'un événement sur l'énergie
    
    Args:
        event: Événement calendrier
        event_type: Type d'événement (meeting, sport, etc.)
        tags: Tags descriptifs
        base_energy: Énergie de base (0-100)
        recovery: Score de récupération (0-1)
        sleep_debt: Score de dette de sommeil (0-1)
    
    Returns:
        (impact, confidence) où impact = -20 à +10, confidence = 0-1
    """
    # Durée de l'événement
    start = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
    end = datetime.fromisoformat(event['end_time'].replace('Z', '+00:00'))
    duration_minutes = (end - start).total_seconds() / 60
    
    # Impact de base selon type
    base_impacts = {
        'meeting': -5,
        'sport': -8,
        'travel': -6,
        'focus': -4,
        'social': -2,
        'other': -3,
    }
    
    impact = base_impacts.get(event_type, -3)
    
    # Modulation selon durée
    if duration_minutes > 120:  # > 2h
        impact *= 1.5
    elif duration_minutes > 60:  # > 1h
        impact *= 1.2
    elif duration_minutes < 30:  # < 30min
        impact *= 0.7
    
    # Modulation selon tags
    if 'high_stress' in tags or 'high_focus' in tags:
        impact *= 1.3
    if 'low_stress' in tags:
        impact *= 0.7
    
    # Modulation selon état de l'utilisateur
    if recovery < 0.5:  # Mauvaise récupération
        impact *= 1.2
    if sleep_debt > 0.6:  # Dette de sommeil élevée
        impact *= 1.15
    
    # Sport: impact négatif immédiat, mais rebound positif après 1h
    # (géré dans generate_curve)
    
    # Clamp impact
    impact = max(-20, min(10, int(impact)))
    
    # Confiance (plus élevée pour types bien identifiés)
    confidence = 0.75 if event_type in ['meeting', 'sport', 'travel'] else 0.55
    
    return impact, confidence


def generate_intraday_curve(
    user_id: str,
    target_date: str,
    base_energy: float,
    recovery: float,
    sleep_debt: float,
    overtrain: float,
    events: List[Dict]
) -> List[Dict]:
    """
    Génère la courbe d'énergie intraday (points toutes les 30 min)
    
    AMÉLIORATION: Commence au réveil pour montrer toute l'évolution de la journée.
    Permet de visualiser la "pente" énergétique depuis le matin.
    
    Args:
        user_id: UUID utilisateur
        target_date: Date ISO (YYYY-MM-DD)
        base_energy: Énergie de base du jour (0-100)
        recovery: Score de récupération (0-1)
        sleep_debt: Score de dette de sommeil (0-1)
        overtrain: Score de surmenage (0-1)
        events: Liste d'événements calendrier
    
    Returns:
        Liste de points [{"t": "ISO8601", "energy": 0-100}]
    """
    from zoneinfo import ZoneInfo
    
    # Utiliser le timezone France (Europe/Paris) pour l'utilisateur
    user_tz = ZoneInfo("Europe/Paris")
    now = datetime.now(user_tz)
    
    # Parser target_date en heure locale
    target_datetime = datetime.fromisoformat(f"{target_date}T00:00:00").replace(tzinfo=user_tz)
    
    # Si target_date n'est pas aujourd'hui, retourner vide
    if target_datetime.date() != now.date():
        return []
    
    # 1. Récupérer l'heure de réveil depuis les biométriques (heure locale)
    wake_time_hour = 7  # Défaut: 7h du matin heure locale
    
    try:
        # Chercher les données de sommeil récentes avec metadata
        sleep_response = supabase.table("biometrics").select(
            "metadata, recorded_at"
        ).eq("user_id", user_id).eq("metric_type", "sleep_duration").gte(
            "recorded_at", f"{target_date}T00:00:00Z"
        ).order("recorded_at", desc=True).limit(1).execute()
        
        if sleep_response.data and len(sleep_response.data) > 0:
            metadata = sleep_response.data[0].get('metadata')
            if metadata and isinstance(metadata, dict):
                bedtime_end = metadata.get('bedtime_end')
                if bedtime_end:
                    # Parser l'heure de réveil et convertir en heure locale
                    wake_dt = datetime.fromisoformat(bedtime_end.replace('Z', '+00:00')).astimezone(user_tz)
                    wake_time_hour = wake_dt.hour
                    logger.info(f"Wake time found: {wake_time_hour}h from bedtime_end")
    except Exception as e:
        logger.warning(f"Could not fetch wake time from biometrics: {e}")
    
    # 2. Définir le point de départ (réveil) et de fin (23:59) en heure locale
    wake_time = target_datetime.replace(hour=wake_time_hour, minute=0, second=0, microsecond=0)
    end_of_day = target_datetime.replace(hour=23, minute=59, second=59)
    
    # 3. Commencer la courbe au réveil (pas "maintenant")
    points = []
    current_time = wake_time
    
    # Arrondir à l'intervalle le plus proche
    minutes = (current_time.minute // INTERVAL_MINUTES) * INTERVAL_MINUTES
    current_time = current_time.replace(minute=minutes, second=0, microsecond=0)
    
    logger.info(f"Generating intraday curve from {current_time.strftime('%H:%M')} (wake) to 23:59")
    
    while current_time <= end_of_day:
        # Heure locale (pour calculs)
        hour = current_time.hour
        minute = current_time.minute
        
        # 1. Décroissance naturelle dans la journée
        # Modèle simple: énergie plus haute le matin, baisse progressive
        time_factor = 1.0
        
        if hour < 12:  # Matin
            time_factor = 1.0
        elif hour < 15:  # Début après-midi
            time_factor = 0.95
        elif hour < 18:  # Fin après-midi (creux naturel)
            time_factor = 0.85
        elif hour < 21:  # Soirée
            time_factor = 0.80
        else:  # Nuit
            time_factor = 0.70
        
        # 2. Modulation selon sleep_debt (creux plus tôt si dette)
        if sleep_debt > 0.6:
            if hour >= 14:  # Creux plus tôt
                time_factor *= 0.90
        
        # 3. Modulation selon recovery (amplitude creux)
        if recovery < 0.5:
            if hour >= 15:
                time_factor *= 0.92
        
        # 4. Modulation selon overtrain
        if overtrain > 0.7:
            time_factor *= 0.95
        
        # Calculer énergie du point
        energy = base_energy * time_factor
        
        # 5. Appliquer impact des événements
        for event in events:
            # Convertir les événements en heure locale pour comparaison
            event_start = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00')).astimezone(user_tz)
            event_end = datetime.fromisoformat(event['end_time'].replace('Z', '+00:00')).astimezone(user_tz)
            
            # Si le point est pendant l'événement
            if event_start <= current_time <= event_end:
                impact = event.get('impact', 0)
                energy += impact
            
            # Sport: rebound positif 1h après la fin
            if event.get('event_type') == 'sport':
                rebound_start = event_end
                rebound_end = event_end + timedelta(hours=1)
                if rebound_start <= current_time <= rebound_end:
                    energy += 5  # Boost post-sport
        
        # Clamp [0, 100]
        energy = max(0, min(100, int(energy)))
        
        # Marquer le point actuel (maintenant)
        is_current = abs((current_time - now).total_seconds()) < (INTERVAL_MINUTES * 60)
        
        point = {
            't': current_time.isoformat(),
            'energy': energy
        }
        
        # Ajouter flag si c'est le point actuel
        if is_current:
            point['is_now'] = True
        
        points.append(point)
        
        # Incrémenter
        current_time += timedelta(minutes=INTERVAL_MINUTES)
    
    return points


def generate_risk_windows_intraday(
    points: List[Dict],
    events: List[Dict]
) -> List[Dict]:
    """
    Génère les fenêtres de risque (creux) à partir de la courbe
    
    Returns:
        Liste de windows [{"from": "HH:MM", "to": "HH:MM", "kind": "dip", "label": "..."}]
    """
    if not points:
        return []
    
    windows = []
    
    # Détecter les creux (énergie < 70 pendant au moins 1h)
    dip_start = None
    dip_min_energy = 100
    
    for i, point in enumerate(points):
        energy = point['energy']
        
        if energy < 70:
            if dip_start is None:
                dip_start = point['t']
                dip_min_energy = energy
            else:
                dip_min_energy = min(dip_min_energy, energy)
        else:
            # Fin du creux
            if dip_start is not None:
                dip_end = points[i - 1]['t'] if i > 0 else point['t']
                
                # Vérifier durée (au moins 1h)
                start_dt = datetime.fromisoformat(dip_start)
                end_dt = datetime.fromisoformat(dip_end)
                duration_minutes = (end_dt - start_dt).total_seconds() / 60
                
                if duration_minutes >= 60:
                    # Formater heures locales
                    from_time = start_dt.strftime('%H:%M')
                    to_time = end_dt.strftime('%H:%M')
                    
                    # Label selon sévérité
                    if dip_min_energy < 50:
                        label = "Creux important - éviter tâches complexes"
                    elif dip_min_energy < 60:
                        label = "Creux modéré - privilégier tâches simples"
                    else:
                        label = "Baisse d'énergie légère"
                    
                    windows.append({
                        'from': from_time,
                        'to': to_time,
                        'kind': 'dip',
                        'label': label
                    })
                
                # Reset
                dip_start = None
                dip_min_energy = 100
    
    return windows


def generate_influencers_heuristic(
    user_id: str,
    base_energy: float,
    recovery: float,
    sleep_debt: float,
    overtrain: float,
    infection: float
) -> List[Dict]:
    """
    Génère les influencers (facteurs d'influence) pour le modèle heuristique
    
    Args:
        user_id: UUID utilisateur
        base_energy: Score d'énergie de base (0-100)
        recovery: Score de récupération (0-1)
        sleep_debt: Score de dette de sommeil (0-1)
        overtrain: Score de surcharge (0-1)
        infection: Score d'infection (0-1)
    
    Returns:
        Liste de dicts avec structure: {"name": str, "type": str, "code": str, "impact": str, "status": str}
    """
    influencers = []
    
    try:
        # 1. Récupérer les médicaments actifs de l'utilisateur
        medications_response = supabase.table("user_medications").select(
            "medication_name, active_substance, atc_code, dosage, dosage_unit, pills_per_intake, start_date"
        ).eq("user_id", user_id).eq("is_active", True).is_("end_date", "null").execute()
        
        medications = medications_response.data if medications_response.data else []
        logger.info(f"📊 [Influencers] Retrieved {len(medications)} medications for user {user_id}")
        if medications:
            logger.info(f"📊 [Influencers] Medications: {[m.get('medication_name') for m in medications]}")
        
        # 2. Récupérer les conditions actives de l'utilisateur
        conditions_response = supabase.table("user_conditions").select(
            "system, code, display, category, severity"
        ).eq("user_id", user_id).execute()
        
        conditions = conditions_response.data if conditions_response.data else []
        logger.info(f"📊 [Influencers] Retrieved {len(conditions)} conditions for user {user_id}")
        if conditions:
            logger.info(f"📊 [Influencers] Conditions: {[c.get('display') for c in conditions]}")
        
        # 3. Récupérer les impacts des médicaments depuis la table de référence
        if medications:
            atc_codes = [m['atc_code'] for m in medications if m.get('atc_code')]
            logger.info(f"📊 [Influencers] ATC codes to lookup: {atc_codes}")
            if atc_codes:
                med_impacts_response = supabase.table("medication_energy_impacts").select(
                    "atc_code, medication_name, energy_category, chronic_impact, acute_impact_min, acute_impact_max, fatigue_risk"
                ).in_("atc_code", atc_codes).eq("is_active", True).execute()
                
                med_impacts_dict = {
                    m['atc_code']: m for m in (med_impacts_response.data or [])
                }
                logger.info(f"📊 [Influencers] Found impacts for {len(med_impacts_dict)} medications")
            else:
                med_impacts_dict = {}
                logger.warning(f"⚠️ [Influencers] No ATC codes found in medications")
        else:
            med_impacts_dict = {}
            logger.warning(f"⚠️ [Influencers] No medications found for user")
        
        # 4. Récupérer les impacts des conditions depuis la table de référence
        if conditions:
            icd_codes = [c['code'] for c in conditions]
            logger.info(f"📊 [Influencers] ICD codes to lookup: {icd_codes}")
            cond_impacts_response = supabase.table("condition_energy_impacts").select(
                "icd11_code, condition_name, decay_rate, energy_malus, severity, category"
            ).in_("icd11_code", icd_codes).eq("is_active", True).execute()
            
            cond_impacts_dict = {
                c['icd11_code']: c for c in (cond_impacts_response.data or [])
            }
            logger.info(f"📊 [Influencers] Found impacts for {len(cond_impacts_dict)} conditions")
        else:
            cond_impacts_dict = {}
            logger.warning(f"⚠️ [Influencers] No conditions found for user")
        
        # 5. Récupérer les poids personnalisés ML
        personalized_weights_response = supabase.table("personalized_weights").select(
            "factor_type, factor_code, weight_multiplier"
        ).eq("user_id", user_id).eq("is_active", True).execute()
        
        personalized_weights = {}
        for pw in (personalized_weights_response.data or []):
            key = (pw['factor_type'], pw['factor_code'])
            personalized_weights[key] = pw['weight_multiplier']
        
        # 6. Générer les influencers pour les métriques Oura (recovery, sleep_debt)
        
        # Récupération
        if recovery < 0.4:
            recovery_impact = -15
            status = "negative"
        elif recovery > 0.7:
            recovery_impact = +15
            status = "positive"
        else:
            recovery_impact = 0
            status = "neutral"
        
        if recovery_impact != 0:
            influencers.append({
                "name": f"Récupération ({int(recovery * 100)}%)",
                "type": "oura",
                "code": "recovery",
                "impact": f"{recovery_impact:+d}%",
                "status": status
            })
        
        # Dette de sommeil
        if sleep_debt > 0.7:
            sleep_impact = +10
            status = "positive"
            influencers.append({
                "name": "Aucune dette de sommeil",
                "type": "oura",
                "code": "sleep_debt",
                "impact": f"{sleep_impact:+d}%",
                "status": status
            })
        elif sleep_debt < 0.5:
            sleep_impact = -10
            status = "negative"
            influencers.append({
                "name": f"Dette de sommeil ({int((1 - sleep_debt) * 8)}h)",
                "type": "oura",
                "code": "sleep_debt",
                "impact": f"{sleep_impact:+d}%",
                "status": status
            })
        
        # 7. Ajouter les médicaments avec leurs impacts
        from datetime import date as date_class
        today = date_class.today()
        
        for med in medications:
            atc_code = med.get('atc_code')
            if not atc_code or atc_code not in med_impacts_dict:
                continue
            
            impact_data = med_impacts_dict[atc_code]
            
            # Calculer le dosage total (dosage par comprimé × nombre de comprimés)
            dosage_per_pill = med.get('dosage', 0)
            pills_per_intake = med.get('pills_per_intake', 1.0)
            total_dosage = dosage_per_pill * pills_per_intake
            
            # Calculer l'impact (utiliser chronic_impact pour simplifier dans V1)
            base_impact = impact_data.get('chronic_impact', 0)
            
            # Si le médicament est un sédatif, utiliser la fourchette négative
            if impact_data.get('energy_category') == 'sedative':
                base_impact = (impact_data.get('acute_impact_min', 0) + impact_data.get('acute_impact_max', 0)) / 2
            
            # Ajuster l'impact en fonction du dosage total
            # L'impact de référence dans la DB est souvent pour un dosage "standard"
            # On multiplie proportionnellement l'impact par le ratio de dosage
            # Note: À améliorer en ajoutant un champ "standard_dosage" dans medication_energy_impacts
            dosage_multiplier = pills_per_intake  # Simplification: l'impact scale avec le nombre de pilules
            base_impact = base_impact * dosage_multiplier
            
            # Appliquer le poids personnalisé ML
            weight_key = ('medication', atc_code)
            weight = personalized_weights.get(weight_key, 1.0)
            adjusted_impact = base_impact * weight
            
            # Calculer les jours depuis le début
            start_date = med.get('start_date')
            if start_date:
                if isinstance(start_date, str):
                    from datetime import datetime as dt_class
                    start_dt = dt_class.fromisoformat(start_date).date()
                else:
                    start_dt = start_date
                days_since_start = (today - start_dt).days
            else:
                days_since_start = 999
            
            # Badge selon la phase
            if days_since_start < 7:
                phase_emoji = "🆕"
            else:
                phase_emoji = "💊"
            
            # Nom complet avec dosage total
            med_name = med.get('medication_name', 'Médicament')
            dosage_unit = med.get('dosage_unit', '')
            # Afficher le dosage total (dosage × pills_per_intake)
            if total_dosage and dosage_unit:
                # Formater proprement (ex: 7.5mg, pas 7.5000mg)
                if total_dosage % 1 == 0:
                    full_name = f"{phase_emoji} {med_name} {int(total_dosage)}{dosage_unit}"
                else:
                    full_name = f"{phase_emoji} {med_name} {total_dosage:.1f}{dosage_unit}"
            else:
                full_name = f"{phase_emoji} {med_name}"
            
            status = "positive" if adjusted_impact > 0 else "negative" if adjusted_impact < 0 else "neutral"
            
            if abs(adjusted_impact) >= 1:  # Seuil pour afficher
                influencers.append({
                    "name": full_name,
                    "type": "medication",
                    "code": atc_code,
                    "impact": f"{adjusted_impact:+.1f}%",
                    "status": status
                })
        
        # 8. Ajouter les conditions avec leurs impacts
        for cond in conditions:
            icd_code = cond.get('code')
            if not icd_code or icd_code not in cond_impacts_dict:
                continue
            
            impact_data = cond_impacts_dict[icd_code]
            
            # Malus fixe de la condition
            base_malus = impact_data.get('energy_malus', 0)
            
            # Appliquer le poids personnalisé ML
            weight_key = ('condition', icd_code)
            weight = personalized_weights.get(weight_key, 1.0)
            adjusted_malus = base_malus * weight
            
            # Emoji selon severity
            severity = impact_data.get('severity', 'moderate')
            emoji_map = {
                'low': '⚠️',
                'moderate': '⚡',
                'high': '😔',
                'severe': '🚨'
            }
            emoji = emoji_map.get(severity, '⚠️')
            
            cond_name = cond.get('display') or impact_data.get('condition_name', 'Condition')
            full_name = f"{emoji} {cond_name}"
            
            if adjusted_malus < 0:  # Seulement les impacts négatifs
                influencers.append({
                    "name": full_name,
                    "type": "condition",
                    "code": icd_code,
                    "impact": f"{adjusted_malus:+.1f}%",
                    "status": "negative"
                })
        
        # 9. Ajouter un facteur de sommeil positif si bon score
        # (basé sur les biométriques récentes)
        try:
            from datetime import datetime as dt_class
            two_days_ago = (dt_class.now() - timedelta(days=2)).isoformat()
            
            sleep_response = supabase.table("biometrics").select(
                "value"
            ).eq("user_id", user_id).eq("metric_type", "sleep_score").gte(
                "recorded_at", two_days_ago
            ).order("recorded_at", desc=True).limit(1).execute()
            
            if sleep_response.data and len(sleep_response.data) > 0:
                sleep_score = sleep_response.data[0]['value']
                
                if sleep_score >= 75:
                    influencers.append({
                        "name": f"😴 Sommeil de qualité ({int(sleep_score)}/100)",
                        "type": "oura",
                        "code": "sleep_score",
                        "impact": "+15%",
                        "status": "positive"
                    })
                elif sleep_score < 50:
                    influencers.append({
                        "name": f"😴 Sommeil insuffisant ({int(sleep_score)}/100)",
                        "type": "oura",
                        "code": "sleep_score",
                        "impact": "-15%",
                        "status": "negative"
                    })
        except Exception as e:
            logger.warning(f"Could not fetch sleep score: {e}")
        
        logger.info(f"✅ Generated {len(influencers)} influencers for user {user_id}")
        if influencers:
            logger.info(f"📊 [Influencers] Types: {[inf['type'] for inf in influencers]}")
            logger.info(f"📊 [Influencers] Names: {[inf['name'] for inf in influencers]}")
        else:
            logger.warning(f"⚠️ [Influencers] No influencers generated - this might be a problem!")
        return influencers
        
    except Exception as e:
        logger.error(f"❌ Error generating influencers: {e}", exc_info=True)
        return []


def generate_notes_intraday(
    base_energy: float,
    recovery: float,
    sleep_debt: float,
    events: List[Dict],
    windows: List[Dict],
    influencers: List[Dict] = None
) -> List[str]:
    """
    Génère des notes explicatives enrichies pour l'utilisateur
    
    Args:
        base_energy: Score d'énergie de base (0-100)
        recovery: Score de récupération (0-1)
        sleep_debt: Score de dette de sommeil (0-1)
        events: Événements du calendrier
        windows: Fenêtres de risque détectées
        influencers: Facteurs d'influence (médicaments, conditions, etc.)
    
    Returns:
        Liste de max 4 notes explicatives
    """
    notes = []
    influencers = influencers or []
    
    # 1. Note sur l'énergie de base avec contexte
    if base_energy < 30:
        notes.append(f"⚠️ Ton énergie de base est très faible aujourd'hui ({int(base_energy)}%)")
    elif base_energy < 60:
        notes.append(f"Ton énergie de base est faible aujourd'hui ({int(base_energy)}%)")
    elif base_energy > 80:
        notes.append(f"✨ Excellente énergie de base aujourd'hui ({int(base_energy)}%)")
    
    # 2. Note sur les médicaments dominants (sédatifs)
    sedative_meds = [inf for inf in influencers if inf.get('type') == 'medication' and inf.get('status') == 'negative']
    if len(sedative_meds) >= 2:
        # Plusieurs sédatifs → effet cumulatif
        med_names = []
        for inf in sedative_meds[:2]:
            name_parts = inf['name'].split(' ')
            if len(name_parts) > 1:
                med_names.append(name_parts[1])  # Retirer emoji
        if med_names:
            notes.append(f"💊 La combinaison {' + '.join(med_names)} a un effet cumulatif sur ta fatigue")
    elif len(sedative_meds) == 1:
        # Un seul sédatif dominant
        med = sedative_meds[0]
        name_parts = med['name'].split(' ')
        if len(name_parts) > 1:
            med_name = name_parts[1]
            impact = med['impact'].replace('%', '')
            notes.append(f"💊 Le {med_name} (sédatif) réduit ton énergie de {impact}%")
    
    # 3. Note sur le sommeil vs énergie (paradoxe)
    sleep_factors = [inf for inf in influencers if inf.get('code') == 'sleep_score' and inf.get('status') == 'positive']
    if sleep_factors and base_energy < 50:
        notes.append("😴 Ton sommeil est bon mais masqué par d'autres facteurs")
    
    # 4. Note sur creux d'énergie
    if windows:
        window = windows[0]
        notes.append(f"📉 Creux d'énergie prévu entre {window.get('from', '')} et {window.get('to', '')}")
    
    # 5. Note sur événements à risque
    high_impact_events = [e for e in events if e.get('impact', 0) < -10]
    if high_impact_events:
        event = high_impact_events[0]
        try:
            start_dt = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
            notes.append(f"📅 {event['title']} à {start_dt.strftime('%H:%M')} pourrait être coûteux")
        except:
            pass
    
    # Note sur récupération
    if recovery < 0.4:
        notes.append(f"Ta récupération est incomplète ({int(recovery * 100)}%)")
    elif recovery < 0.5:
        notes.append("Ta récupération est faible, ménage-toi")
    
    # Note sur dette sommeil
    if sleep_debt > 0.6:
        notes.append("Dette de sommeil élevée, creux plus tôt que d'habitude")
    
    return notes[:4]  # Max 4 notes (augmenté pour plus de contexte)


def generate_intraday_forecast(
    user_id: str,
    target_date: str = None
) -> Optional[Dict]:
    """
    Génère la prévision intraday complète
    
    Args:
        user_id: UUID utilisateur
        target_date: Date ISO (YYYY-MM-DD), défaut = aujourd'hui
    
    Returns:
        Dict avec structure complète ou None si impossible
    """
    if not target_date:
        target_date = date.today().isoformat()
    
    logger.info(f"Generating intraday forecast for user {user_id} on {target_date}")
    
    try:
        # 1. Récupérer daily_energy du jour
        from daily_energy_engine import get_daily_energy
        daily_energy = get_daily_energy(user_id, target_date)
        
        if not daily_energy:
            logger.warning(f"No daily_energy found for {user_id} on {target_date}")
            return None
        
        base_energy = daily_energy['energy_score'] * 100  # Convertir 0-1 → 0-100
        components = daily_energy.get('components', {})
        recovery = components.get('recovery', 0.5)
        sleep_debt = components.get('sleep_debt', 0.5)
        overtrain = components.get('overtrain', 0.3)
        
        # 2. Récupérer événements du calendrier (aujourd'hui, de maintenant → fin de journée)
        # Use timezone-aware datetime to avoid comparison errors
        now = datetime.now(timezone.utc)
        # Note: Python's fromisoformat doesn't support 'Z' suffix, use +00:00 instead
        end_of_day = datetime.fromisoformat(f"{target_date}T23:59:59+00:00")
        
        # Note: La table calendar_events n'existe pas encore dans le schema
        # Pour l'instant, on va simuler avec une liste vide
        # TODO: Créer table calendar_events ou utiliser API externe
        events_response = None
        try:
            events_response = supabase.table("calendar_events").select(
                "id, title, start_time, end_time, location, notes"
            ).eq("user_id", user_id).gte(
                "start_time", now.isoformat()
            ).lte(
                "start_time", end_of_day.isoformat()
            ).order("start_time", desc=False).execute()
        except Exception as e:
            logger.warning(f"Could not fetch calendar_events (table may not exist): {e}")
            events_response = None
        
        raw_events = events_response.data if events_response and events_response.data else []
        
        # 3. Classifier et enrichir événements
        enriched_events = []
        for event in raw_events:
            event_type, tags = classify_event_type(event)
            impact, confidence = estimate_event_impact(
                event, event_type, tags, base_energy, recovery, sleep_debt
            )
            
            enriched_events.append({
                'id': event['id'],
                'start': event['start_time'],
                'end': event['end_time'],
                'title': event['title'],
                'impact': impact,
                'confidence': confidence,
                'tags': tags,
                'event_type': event_type
            })
        
        # 4. Générer courbe
        points = generate_intraday_curve(
            user_id, target_date, base_energy, recovery, sleep_debt, overtrain, enriched_events
        )
        
        if not points:
            logger.warning(f"No points generated for {user_id} on {target_date}")
            return None
        
        # 5. Générer fenêtres de risque
        windows = generate_risk_windows_intraday(points, enriched_events)
        
        # 6. Générer influencers (facteurs d'influence)
        infection = components.get('infection', 0.5)
        influencers = generate_influencers_heuristic(
            user_id, base_energy, recovery, sleep_debt, overtrain, infection
        )
        
        # 7. Générer notes (avec influencers pour contexte enrichi)
        notes = generate_notes_intraday(base_energy, recovery, sleep_debt, enriched_events, windows, influencers)
        
        # 8. Récupérer les poids ML personnalisés
        ml_weights = []
        try:
            weights_response = supabase.table("personalized_weights").select(
                "factor_type, factor_code, weight_multiplier, updated_at"
            ).eq("user_id", user_id).eq("is_active", True).execute()
            
            if weights_response.data:
                ml_weights = weights_response.data
                logger.info(f"✓ Retrieved {len(ml_weights)} ML weights for user {user_id}")
        except Exception as e:
            logger.warning(f"Could not fetch ML weights: {e}")
        
        # 9. Calculer confiance globale
        confidence = daily_energy['confidence'] * 0.9  # Légèrement moins confiant que daily_energy
        
        # 10. Construire résultat
        result = {
            'type': 'intraday_energy',
            'date': target_date,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'model_version': 'intraday_v1',
            'calculation_model': 'heuristic_v1',
            'timezone': 'UTC',  # TODO: utiliser timezone utilisateur
            'points': points,
            'windows': windows,
            'events': [
                {k: v for k, v in e.items() if k != 'event_type'}  # Retirer event_type interne
                for e in enriched_events
            ],
            'influencers': influencers,  # ← AJOUT DES INFLUENCERS
            'notes': notes,
            'confidence': confidence,
            # Composants d'énergie (pour affichage détaillé dans l'UI)
            'components': {
                'recovery': recovery,
                'sleep_debt': sleep_debt,
                'overtrain': overtrain,
                'infection': infection,
                'base_energy': base_energy
            },
            # Poids ML personnalisés (pour mode Debug)
            'ml_weights': ml_weights
        }
        
        logger.info(f"✓ Generated intraday forecast with {len(points)} points, {len(enriched_events)} events")
        return result
    
    except Exception as e:
        logger.error(f"Error generating intraday forecast: {e}", exc_info=True)
        return None


def save_intraday_forecast(user_id: str, forecast: Dict) -> bool:
    """
    Sauvegarde la prévision intraday en DB
    
    Args:
        user_id: UUID utilisateur
        forecast: Dict retourné par generate_intraday_forecast()
    
    Returns:
        True si succès, False sinon
    """
    try:
        record = {
            'user_id': user_id,
            'forecast_date': forecast['date'],
            'timezone': forecast['timezone'],
            'generated_at': forecast['generated_at'],
            'points': forecast['points'],
            'windows': forecast['windows'],
            'events': forecast['events'],
            'influencers': forecast.get('influencers', []),  # Ajout des influencers
            'components': forecast.get('components', {}),  # Ajout des composants d'énergie
            'notes': forecast['notes'],
            'model_version': forecast['model_version'],
            'confidence': forecast['confidence'],
            'calculation_model': forecast.get('calculation_model', 'heuristic_v1')
        }
        
        # Upsert (insert or update)
        supabase.table('intraday_energy_forecast').upsert(
            record,
            on_conflict='user_id,forecast_date'
        ).execute()
        
        logger.info(f"✓ Saved intraday forecast for user {user_id}, date {forecast['date']}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving intraday forecast: {e}")
        return False


def get_intraday_forecast(user_id: str, target_date: str = None) -> Optional[Dict]:
    """
    Récupère la prévision intraday depuis la DB (si déjà calculée)
    
    Args:
        user_id: UUID utilisateur
        target_date: Date ISO (YYYY-MM-DD), défaut = aujourd'hui
    
    Returns:
        Dict avec structure complète ou None si pas trouvé
    """
    if not target_date:
        target_date = date.today().isoformat()
    
    try:
        response = supabase.table('intraday_energy_forecast') \
            .select('*') \
            .eq('user_id', user_id) \
            .eq('forecast_date', target_date) \
            .order('generated_at', desc=True) \
            .limit(1) \
            .execute()
        
        if not response.data or len(response.data) == 0:
            return None
        
        record = response.data[0]
        
        # Retourner format identique à generate_intraday_forecast()
        return {
            'type': 'intraday_energy',
            'date': record['forecast_date'],
            'generated_at': record['generated_at'],
            'model_version': record['model_version'],
            'timezone': record['timezone'],
            'points': record['points'],
            'windows': record['windows'],
            'events': record['events'],
            'notes': record['notes'],
            'confidence': record['confidence'],
            'influencers': record.get('influencers', [])  # ✅ Ajout des influencers
        }
    
    except Exception as e:
        logger.error(f"Error fetching intraday forecast: {e}")
        return None


if __name__ == '__main__':
    # Test avec un utilisateur fictif
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python intraday_energy_service.py <user_id>")
        sys.exit(1)
    
    test_user_id = sys.argv[1]
    
    print(f"Testing intraday forecast for user {test_user_id}")
    
    # Générer
    forecast = generate_intraday_forecast(test_user_id)
    
    if forecast:
        print(f"\n✓ Forecast generated:")
        print(f"  - {len(forecast['points'])} points")
        print(f"  - {len(forecast['events'])} events")
        print(f"  - {len(forecast['windows'])} risk windows")
        print(f"  - Confidence: {forecast['confidence']:.2f}")
        print(f"\nNotes:")
        for note in forecast['notes']:
            print(f"  - {note}")
        
        # Sauvegarder
        if save_intraday_forecast(test_user_id, forecast):
            print("\n✓ Forecast saved to DB")
    else:
        print("✗ Could not generate forecast")
