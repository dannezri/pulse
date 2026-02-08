"""
Daily Energy Engine - Score d'énergie unique lifestyle

Consolide recovery, sleep_debt, overtrain, infection en 1 score compréhensible
avec label, raisons, action clé, et prédiction de creux.

Output JSON stable (prêt UI + LLM):
{
  "energy_score": 0.78,
  "label": "Bonne journée",
  "confidence": 0.82,
  "reasons": [
    {"key":"recovery_good", "text":"Récupération correcte"},
    {"key":"sleep_debt_low", "text":"Dette de sommeil faible"}
  ],
  "primary_action": {
    "key":"deep_work_morning",
    "title":"Planifie tes tâches importantes ce matin",
    "why":"Ton énergie est meilleure en début de journée."
  },
  "risk_windows": [
    {"from":"16:00", "to":"18:00", "risk":"dip", "text":"Baisse d'énergie probable"}
  ]
}

Usage: Appelé par /api/brief après calcul des états latents
"""

import os
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from supabase import create_client, Client

# Initialize Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)

# Pondérations V1 (MVP - robuste et explicable)
WEIGHT_RECOVERY = 0.45
WEIGHT_SLEEP_DEBT = 0.25
WEIGHT_OVERTRAIN = 0.20
WEIGHT_INFECTION = 0.10


def compute_daily_energy(
    states: Dict,
    user_id: str = None,
    target_date: str = None
) -> Dict:
    """
    Calcule le score d'énergie quotidien à partir des états latents
    
    Args:
        states: Dict avec recovery, sleep_debt, overtrain, infection_like
        user_id: UUID utilisateur (optionnel, pour enrichissement agenda dans risk windows)
        target_date: Date ISO (optionnel, défaut = aujourd'hui)
    
    Returns:
        Dict avec energy_score, label, confidence, reasons, primary_action, risk_windows
    """
    
    # 1. Extraire les états latents
    recovery = states.get('recovery', {})
    sleep_debt = states.get('sleep_debt', {})
    overtrain = states.get('overtrain', {})
    infection = states.get('infection_like', {})
    
    recovery_score = recovery.get('smoothed_score', 0.5)
    sleep_debt_score = sleep_debt.get('smoothed_score', 0.5)
    overtrain_score = overtrain.get('smoothed_score', 0.3)
    infection_score = infection.get('smoothed_score', 0.2)
    
    # Metadata utiles
    debt_hours = sleep_debt.get('metadata', {}).get('debt_hours', 0)
    persistent = infection.get('metadata', {}).get('persistent', False)
    
    # 2. Normaliser en "bon" (plus haut = mieux)
    recovery_good = recovery_score  # Déjà 0-1, haut = bon
    sleep_debt_good = 1 - sleep_debt_score  # Inverser: bas = bon
    overtrain_good = 1 - overtrain_score  # Inverser: bas = bon
    
    # Infection: seulement si persistante (sinon trop de faux positifs)
    infection_adjusted = infection_score * (1.0 if persistent else 0.35)
    infection_good = 1 - infection_adjusted
    
    # 3. Calcul énergie V1 (pondéré)
    energy = (
        WEIGHT_RECOVERY * recovery_good +
        WEIGHT_SLEEP_DEBT * sleep_debt_good +
        WEIGHT_OVERTRAIN * overtrain_good +
        WEIGHT_INFECTION * infection_good
    )
    
    # 4. Pénalités simples
    if debt_hours > 3:
        energy -= 0.05
    
    if overtrain_score > 0.75:
        energy -= 0.05
    
    # Clamp [0, 1]
    energy = max(0.0, min(1.0, energy))
    
    # 5. Label lifestyle
    label = get_energy_label(energy)
    
    # 6. Confidence globale
    confidence = compute_confidence(states)
    
    # 7. Raisons (2-3 max, les plus contributeurs)
    reasons = generate_reasons(
        recovery_score, 
        sleep_debt_score, 
        debt_hours, 
        overtrain_score, 
        infection_score, 
        persistent
    )
    
    # 8. Action clé unique (table de règles)
    primary_action = generate_primary_action(
        energy,
        recovery_score,
        debt_hours,
        overtrain_score,
        infection_score,
        persistent
    )
    
    # 9. Risk windows (prédiction creux d'énergie avec enrichissement agenda)
    risk_windows = generate_risk_windows(
        energy, 
        debt_hours, 
        recovery_score,
        user_id=user_id,
        target_date=target_date
    )
    
    return {
        'energy_score': round(energy, 2),
        'label': label,
        'confidence': round(confidence, 2),
        'reasons': reasons,
        'primary_action': primary_action,
        'risk_windows': risk_windows,
        'components': {
            'recovery': round(recovery_good, 2),
            'sleep_debt': round(sleep_debt_good, 2),
            'overtrain': round(overtrain_good, 2),
            'infection': round(infection_good, 2)
        }
    }


def get_energy_label(energy: float) -> str:
    """Traduit score en label lifestyle"""
    if energy >= 0.80:
        return "Excellente journée"
    elif energy >= 0.65:
        return "Bonne journée"
    elif energy >= 0.50:
        return "Journée moyenne"
    else:
        return "Journée fragile"


def compute_confidence(states: Dict) -> float:
    """Calcule confidence globale (moyenne pondérée des states)"""
    recovery = states.get('recovery', {})
    sleep_debt = states.get('sleep_debt', {})
    overtrain = states.get('overtrain', {})
    infection = states.get('infection_like', {})
    
    c_recovery = recovery.get('confidence', 0.5)
    c_sleep = sleep_debt.get('confidence', 0.5)
    c_overtrain = overtrain.get('confidence', 0.5)
    c_infection = infection.get('confidence', 0.5)
    
    # Moyenne pondérée
    conf = (
        0.40 * c_recovery +
        0.25 * c_sleep +
        0.20 * c_overtrain +
        0.15 * c_infection
    )
    
    # Data quality factor (si métrique manquante)
    # TODO: Détecter métriques manquantes via metadata
    data_quality_factor = 1.0  # Assume full data pour MVP
    
    return conf * data_quality_factor


def generate_reasons(
    recovery: float,
    sleep_debt: float,
    debt_hours: float,
    overtrain: float,
    infection: float,
    persistent: bool
) -> List[Dict]:
    """
    Génère 2-3 raisons claires (les plus gros contributeurs)
    
    Règles:
    - recovery < 0.45 → "Récupération incomplète"
    - debt_hours > 2 → "Dette de sommeil en cours"
    - overtrain > 0.70 → "Charge physique élevée"
    - infection > 0.60 && persistent → "Signaux de surcharge"
    - Si tout bon → raisons positives
    """
    
    reasons = []
    
    # Scoring des facteurs (poids * écart à l'optimal)
    factors = []
    
    # Recovery (optimal = 1.0)
    recovery_gap = 1.0 - recovery
    factors.append(('recovery', recovery_gap * WEIGHT_RECOVERY, recovery))
    
    # Sleep debt (optimal = 0.0)
    sleep_debt_gap = sleep_debt
    factors.append(('sleep_debt', sleep_debt_gap * WEIGHT_SLEEP_DEBT, sleep_debt))
    
    # Overtrain (optimal = 0.0)
    overtrain_gap = overtrain
    factors.append(('overtrain', overtrain_gap * WEIGHT_OVERTRAIN, overtrain))
    
    # Infection (optimal = 0.0, mais seulement si persistent)
    if persistent:
        infection_gap = infection
        factors.append(('infection', infection_gap * WEIGHT_INFECTION, infection))
    
    # Trier par gap (plus gros problèmes en premier)
    factors.sort(key=lambda x: x[1], reverse=True)
    
    # Générer raisons pour top 2-3 facteurs
    count = 0
    for factor_type, gap, score in factors:
        if count >= 3:
            break
        
        if factor_type == 'recovery':
            if score < 0.45:
                reasons.append({
                    'key': 'recovery_low',
                    'text': 'Récupération incomplète'
                })
                count += 1
            elif score >= 0.75:
                reasons.append({
                    'key': 'recovery_good',
                    'text': 'Excellente récupération'
                })
                count += 1
        
        elif factor_type == 'sleep_debt':
            if debt_hours > 2:
                reasons.append({
                    'key': 'sleep_debt_high',
                    'text': f'Dette de sommeil en cours ({debt_hours:.1f}h)'
                })
                count += 1
            elif debt_hours < 1:
                reasons.append({
                    'key': 'sleep_debt_low',
                    'text': 'Dette de sommeil faible'
                })
                count += 1
        
        elif factor_type == 'overtrain':
            if score > 0.70:
                reasons.append({
                    'key': 'overtrain_high',
                    'text': 'Charge physique élevée'
                })
                count += 1
            elif score < 0.30:
                reasons.append({
                    'key': 'overtrain_low',
                    'text': 'Charge physique maîtrisée'
                })
                count += 1
        
        elif factor_type == 'infection':
            if score > 0.60:
                reasons.append({
                    'key': 'infection_warning',
                    'text': 'Signaux de surcharge/infection'
                })
                count += 1
    
    # Si pas assez de raisons (tout optimal), ajouter raisons positives
    if count < 2:
        if recovery >= 0.70:
            reasons.append({
                'key': 'recovery_good',
                'text': 'Bonne récupération'
            })
        if debt_hours < 1.5:
            reasons.append({
                'key': 'sleep_good',
                'text': 'Sommeil suffisant'
            })
    
    return reasons[:3]  # Max 3


def generate_primary_action(
    energy: float,
    recovery: float,
    debt_hours: float,
    overtrain: float,
    infection: float,
    persistent: bool
) -> Dict:
    """
    Génère 1 action clé via table de règles (priorité décroissante)
    
    Priorités:
    1. Infection persistante → Repos
    2. Recovery très bas → Réduire intensité
    3. Dette sommeil haute → Coucher plus tôt
    4. Overtrain élevé → Récup active
    5. Énergie élevée → Tâches importantes
    6. Défaut → Journée low friction
    """
    
    # 1. Infection persistante (priorité absolue)
    if infection > 0.60 and persistent:
        return {
            'key': 'rest_hydrate',
            'title': 'Repos + hydratation',
            'why': 'Ton corps montre des signaux de surcharge. Journée légère recommandée.'
        }
    
    # 2. Recovery très bas (risque santé)
    if recovery < 0.45:
        return {
            'key': 'reduce_intensity',
            'title': 'Réduis l\'intensité aujourd\'hui',
            'why': 'Ta récupération est incomplète. Prévois des pauses régulières.'
        }
    
    # 3. Dette sommeil haute (impact énergie)
    if debt_hours > 3:
        return {
            'key': 'sleep_earlier',
            'title': 'Couche-toi 1h plus tôt ce soir',
            'why': f'Tu as {debt_hours:.1f}h de dette de sommeil à combler.'
        }
    
    # 4. Overtrain élevé (risque blessure)
    if overtrain > 0.70:
        return {
            'key': 'active_recovery',
            'title': 'Récup active : marche ou mobilité',
            'why': 'Ta charge physique est élevée. Évite les entraînements intenses.'
        }
    
    # 5. Énergie élevée (optimisation performance)
    if energy >= 0.70:
        return {
            'key': 'deep_work_morning',
            'title': 'Planifie tes tâches importantes ce matin',
            'why': 'Ton énergie est excellente. Profites-en en début de journée.'
        }
    
    # 6. Défaut (journée moyenne/fragile)
    return {
        'key': 'low_friction_day',
        'title': 'Journée "low friction" : petites tâches + marche',
        'why': 'Ton énergie est modérée. Économise-toi pour les priorités.'
    }


def enrich_risk_window_with_calendar(risk_window: Dict, user_id: str, target_date: str) -> Dict:
    """
    Enrichit un risk window avec des recommandations basées sur les événements du calendrier
    
    Logique:
    1. Récupère les événements du jour (target_date)
    2. Identifie ceux qui tombent dans le risk window
    3. Classe par importance (pro/meeting > personnel > autre)
    4. Génère recommandation intelligente :
       - Déplacer l'événement (si possible)
       - Prendre une pause/boost avant (café, marche, snack)
       - Accepter la baisse de performance (si critique, informer)
    
    Args:
        risk_window: Dict avec 'from', 'to', 'risk', 'text'
        user_id: UUID utilisateur
        target_date: Date ISO (YYYY-MM-DD)
    
    Returns:
        risk_window enrichi avec 'conflicting_events' et 'recommendation'
    """
    from datetime import datetime, time
    
    try:
        # Utiliser le client Supabase global déjà initialisé
        global supabase
        
        # 1. Récupérer les événements du jour
        start_of_day = f"{target_date}T00:00:00Z"
        end_of_day = f"{target_date}T23:59:59Z"
        
        events_response = supabase.table("calendar_events").select(
            "id, title, start_time, end_time, location, notes"
        ).eq("user_id", user_id).gte(
            "start_time", start_of_day
        ).lte(
            "start_time", end_of_day
        ).order("start_time", desc=False).execute()
        
        if not events_response.data:
            # Pas d'événements → retourner risk_window tel quel
            return risk_window
        
        # 2. Parser les heures du risk window
        risk_from = datetime.strptime(risk_window['from'], '%H:%M').time()
        risk_to = datetime.strptime(risk_window['to'], '%H:%M').time()
        
        # 3. Identifier les événements qui tombent dans le creux
        conflicting_events = []
        for event in events_response.data:
            event_start = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
            event_time = event_start.time()
            
            # Vérifier si l'événement tombe dans le risk window
            if risk_from <= event_time <= risk_to:
                # Classifier l'importance (basé sur keywords)
                importance = classify_event_importance(event)
                conflicting_events.append({
                    'title': event['title'],
                    'start': event['start_time'],
                    'importance': importance
                })
        
        # 4. Si pas de conflit, retourner tel quel
        if not conflicting_events:
            return risk_window
        
        # 5. Générer recommandation intelligente
        most_important = max(conflicting_events, key=lambda e: e['importance'])
        
        recommendation = generate_calendar_recommendation(
            most_important,
            risk_window,
            len(conflicting_events)
        )
        
        # 6. Enrichir le risk_window
        risk_window['conflicting_events'] = conflicting_events
        risk_window['recommendation'] = recommendation
        risk_window['has_conflict'] = True
        
        # Mettre à jour le texte pour alerter
        event_titles = [e['title'] for e in conflicting_events[:2]]  # Max 2 pour lisibilité
        if len(conflicting_events) == 1:
            risk_window['text'] = f"⚠️ {event_titles[0]} prévu durant ce creux d'énergie"
        else:
            risk_window['text'] = f"⚠️ {len(conflicting_events)} événements prévus durant ce creux"
        
        return risk_window
    
    except Exception as e:
        print(f"[RISK WINDOW ENRICHMENT] Error: {e}")
        # En cas d'erreur, retourner le risk_window original (fail-safe)
        return risk_window


def classify_event_importance(event: Dict) -> int:
    """
    Classifie l'importance d'un événement (0-3)
    
    Basé sur keywords dans title/notes :
    - 3 (critique) : réunion, meeting, client, présentation, entretien, interview
    - 2 (important) : call, appel, rendez-vous, démo, review
    - 1 (normal) : sport, gym, workout, pause, break
    - 0 (personnel) : lunch, déjeuner, dîner, café
    
    Args:
        event: Dict avec title, location, notes
    
    Returns:
        Score d'importance (0-3)
    """
    title_lower = event.get('title', '').lower()
    notes_lower = event.get('notes', '').lower()
    combined = f"{title_lower} {notes_lower}"
    
    # Keywords par niveau
    critical_keywords = ['réunion', 'meeting', 'client', 'présentation', 'entretien', 'interview', 'board']
    important_keywords = ['call', 'appel', 'rendez-vous', 'démo', 'review', 'sync', '1:1']
    normal_keywords = ['sport', 'gym', 'workout', 'training', 'course']
    personal_keywords = ['lunch', 'déjeuner', 'dîner', 'café', 'pause', 'break']
    
    if any(keyword in combined for keyword in critical_keywords):
        return 3
    elif any(keyword in combined for keyword in important_keywords):
        return 2
    elif any(keyword in combined for keyword in normal_keywords):
        return 1
    elif any(keyword in combined for keyword in personal_keywords):
        return 0
    else:
        # Par défaut, considérer comme important (principe de précaution)
        return 2


def generate_calendar_recommendation(event: Dict, risk_window: Dict, total_conflicts: int) -> Dict:
    """
    Génère une recommandation actionnable basée sur l'événement et le creux d'énergie
    
    Logique :
    - Importance 3 (critique) → Suggérer pause/boost avant OU déplacer si possible
    - Importance 2 (important) → Suggérer déplacer
    - Importance 1-0 (normal/personnel) → Suggérer déplacer ou accepter baisse
    
    Args:
        event: Dict avec title, importance, start
        risk_window: Dict avec from, to
        total_conflicts: Nombre total d'événements en conflit
    
    Returns:
        Dict avec type, action, reason
    """
    importance = event['importance']
    event_title = event['title']
    
    if importance == 3:
        # Événement critique → Ne pas déplacer, mais préparer
        return {
            'type': 'prepare',
            'action': f"Prends une pause 30 min avant '{event_title}'",
            'details': "15 min de marche + snack protéiné + hydratation. Ton énergie sera à {risk_window['from']}-{risk_window['to']}, donc prépare-toi.",
            'reason': 'Événement critique durant un creux d\'énergie prévu'
        }
    elif importance == 2:
        # Événement important → Proposer de déplacer
        return {
            'type': 'reschedule',
            'action': f"Déplace '{event_title}' hors du creux d'énergie",
            'details': f"Suggère 10h-12h ou 14h-{risk_window['from']} pour maximiser ta performance.",
            'reason': 'Timing sous-optimal pour un événement important'
        }
    else:
        # Événement normal/personnel → Accepter ou déplacer
        if total_conflicts > 1:
            return {
                'type': 'accept',
                'action': f"{total_conflicts} événements durant le creux : Accepte la baisse de rythme",
                'details': "Priorise l'essentiel, reporte ce qui peut l'être.",
                'reason': 'Trop d\'événements à déplacer'
            }
        else:
            return {
                'type': 'reschedule',
                'action': f"Déplace '{event_title}' en matinée si possible",
                'details': "Tu auras plus d'énergie avant 14h.",
                'reason': 'Optimisation simple possible'
            }


def generate_risk_windows(
    energy: float, 
    debt_hours: float, 
    recovery: float,
    user_id: str = None,
    target_date: str = None
) -> List[Dict]:
    """
    Prédit les creux d'énergie probables avec recommandations basées sur l'agenda
    
    Règles MVP:
    - Si énergie haute (≥0.75) → dip tardif (17-19h)
    - Si énergie moyenne (0.60-0.75) → dip moyen (16-18h)
    - Si énergie basse (<0.60) → dip précoce (14-16h)
    
    V2 (NEW): Croise les risk windows avec les événements du calendrier
    - Si événement important dans le creux → propose de déplacer OU pause avant
    - Transforme "info passive" en "assistant proactif"
    
    Args:
        energy: Score d'énergie (0-1)
        debt_hours: Heures de dette de sommeil
        recovery: Score de récupération (0-1)
        user_id: UUID utilisateur (optionnel, pour enrichissement agenda)
        target_date: Date cible ISO (optionnel, défaut = aujourd'hui)
    
    Returns:
        List de risk windows avec recommandations enrichies si agenda disponible
    """
    
    # 1. Déterminer le créneau à risque selon l'énergie
    if energy >= 0.75:
        # Énergie haute → dip tardif
        risk_window = {
            'from': '17:00',
            'to': '19:00',
            'risk': 'dip',
            'text': 'Baisse d\'énergie probable en fin d\'après-midi'
        }
    elif energy >= 0.60:
        # Énergie moyenne → dip moyen
        risk_window = {
            'from': '16:00',
            'to': '18:00',
            'risk': 'dip',
            'text': 'Baisse d\'énergie attendue en milieu d\'après-midi'
        }
    else:
        # Énergie basse → dip précoce
        risk_window = {
            'from': '14:00',
            'to': '16:00',
            'risk': 'dip',
            'text': 'Baisse d\'énergie probable dès 14h. Planifie une pause.'
        }
    
    # 2. Si user_id fourni, enrichir avec événements agenda
    if user_id:
        risk_window = enrich_risk_window_with_calendar(
            risk_window, 
            user_id, 
            target_date or datetime.now().date().isoformat()
        )
    
    return [risk_window]


def get_daily_energy(user_id: str, date_str: str = None) -> Optional[Dict]:
    """
    Récupère le daily energy depuis la DB (si déjà calculé)
    
    Args:
        user_id: UUID de l'utilisateur
        date_str: Date au format ISO (YYYY-MM-DD), défaut = aujourd'hui
    
    Returns:
        Dict avec energy_score, label, confidence, reasons, primary_action, risk_windows, components
        ou None si pas trouvé
    """
    
    if not date_str:
        date_str = date.today().isoformat()
    
    try:
        response = supabase.table('daily_energy') \
            .select('*') \
            .eq('user_id', user_id) \
            .eq('energy_date', date_str) \
            .execute()
        
        if not response.data or len(response.data) == 0:
            return None
        
        record = response.data[0]
        
        # Retourner format identique à compute_daily_energy()
        return {
            'energy_score': record['energy_score'],
            'label': record['label'],
            'confidence': record['confidence'],
            'reasons': record['reasons'],
            'primary_action': record['primary_action'],
            'risk_windows': record['risk_windows'],
            'components': record['components'],
            'model_version': record['model_version'],
            'calculated_at': record['calculated_at']
        }
    
    except Exception as e:
        print(f"Error fetching daily energy: {e}")
        return None


def save_daily_energy(user_id: str, date_str: str, energy_data: Dict) -> bool:
    """
    Sauvegarde le daily energy en DB
    
    Args:
        user_id: UUID de l'utilisateur
        date_str: Date au format ISO (YYYY-MM-DD)
        energy_data: Dict retourné par compute_daily_energy()
    
    Returns:
        True si succès, False sinon
    """
    
    try:
        # Préparer l'enregistrement
        record = {
            'user_id': user_id,
            'energy_date': date_str,
            'energy_score': energy_data['energy_score'],
            'label': energy_data['label'],
            'confidence': energy_data['confidence'],
            'reasons': energy_data['reasons'],
            'primary_action': energy_data['primary_action'],
            'risk_windows': energy_data['risk_windows'],
            'components': energy_data['components'],
            'model_version': 'energy_v1',
            'calculated_at': datetime.utcnow().isoformat()
        }
        
        # Upsert (insert or update)
        supabase.table('daily_energy').upsert(
            record,
            on_conflict='user_id,energy_date'
        ).execute()
        
        print(f"✓ Saved daily_energy for user {user_id}, date {date_str}")
        return True
    
    except Exception as e:
        print(f"Error saving daily energy: {e}")
        return False


if __name__ == '__main__':
    # Test avec états fictifs
    test_states = {
        'recovery': {
            'smoothed_score': 0.72,
            'confidence': 0.85
        },
        'sleep_debt': {
            'smoothed_score': 0.35,
            'confidence': 0.90,
            'metadata': {
                'debt_hours': 2.3
            }
        },
        'overtrain': {
            'smoothed_score': 0.40,
            'confidence': 0.75
        },
        'infection_like': {
            'smoothed_score': 0.25,
            'confidence': 0.60,
            'metadata': {
                'persistent': False
            }
        }
    }
    
    print("=== Daily Energy Engine Test ===\n")
    
    energy = compute_daily_energy(test_states)
    
    print(f"Energy Score: {energy['energy_score']} ({energy['label']})")
    print(f"Confidence: {energy['confidence']:.0%}\n")
    
    print("Raisons:")
    for reason in energy['reasons']:
        print(f"  • {reason['text']}")
    
    print(f"\nAction clé:")
    print(f"  {energy['primary_action']['title']}")
    print(f"  → {energy['primary_action']['why']}\n")
    
    print("Risk windows:")
    for window in energy['risk_windows']:
        print(f"  {window['from']}-{window['to']}: {window['text']}")
    
    print(f"\nComponents:")
    for comp, val in energy['components'].items():
        print(f"  {comp}: {val:.2f}")
