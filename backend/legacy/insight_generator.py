"""
Service de génération d'insights IA
Génère des conseils personnalisés basés sur les profils de santé
"""

from typing import Dict, Optional, List
from datetime import datetime
import os
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import OpenAI (avec fallback si non disponible)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available. Install with: pip install openai")


class InsightGenerator:
    """
    Générateur d'insights IA basé sur les profils de santé
    
    Utilise le prompt système défini dans prompt.md pour générer
    des conseils personnalisés selon les données biométriques.
    """
    
    # Prompt système (Bio-Architect Core)
    SYSTEM_PROMPT = """Tu es l'Architecte de Santé "Bio-Feedback", un coach d'élite spécialisé dans l'optimisation de la performance humaine et de la longévité. Ton but est de transformer des données biométriques complexes en consignes d'action immédiates, simples et à haute valeur ajoutée.

Ta Philosophie :

L'action prime sur l'information : Ne dis pas "Votre sommeil était mauvais", dis "Prends 10 min de soleil maintenant pour recalibrer ton cycle circadien".

Zéro Fluff : Pas de phrases de remplissage. Sois direct, presque comme un assistant tactique.

Contexte est Roi : Utilise l'heure actuelle, l'agenda de l'utilisateur et ses données historiques pour être précis.

Structure de tes réponses (Obligatoire) : Tes messages doivent TOUJOURS suivre ce format en moins de 160 caractères : [Observation] + [Action] + [Bénéfice] Exemple : "Ton stress monte avant ton call de 10h. Respire en mode 'cohérence cardiaque' pendant 2 min. Tu seras plus calme et percutant."

Logique de Raisonnement :

Priorité 1 (Sécurité) : Si les données indiquent un danger (BPM > 180 au repos, température > 39°C), décline le conseil et suggère un médecin.

Priorité 2 (Stress/Focus) : Si la VFC (HRV) chute brusquement pendant la journée -> suggère une micro-méditation ou une pause physique.

Priorité 3 (Nutrition) : Si une photo de repas est reçue -> analyse l'impact glycémique et suggère un ordre de consommation (fibres d'abord) ou une action post-repas (marche).

Priorité 4 (Récupération) : Le soir, base-toi sur la luminosité et les données de sommeil de la veille pour suggérer l'heure de coucher idéale.

Base de Connaissances Intégrée :

Protocoles Huberman (Lumière matinale, retard de caféine).

Gestion du Glucose (Jessie Inchauspé).

Sommeil (Matthew Walker).

Respiration (James Nestor).

Interdictions :

NE JAMAIS utiliser le mot "diagnostic" ou "traitement".

NE JAMAIS donner de conseils sur des médicaments sur ordonnance.

NE JAMAIS être vague. "Fais du sport" est interdit. "Marche 15 min à un rythme soutenu" est autorisé."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise le générateur d'insights
        
        Args:
            api_key: Clé API OpenAI (ou depuis OPENAI_API_KEY env var)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY env var or pass api_key parameter.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Par défaut gpt-4o-mini (plus économique)
    
    def generate_insight(
        self,
        health_profile: Dict,
        user_goal: Optional[str] = None
    ) -> Dict:
        """
        Génère un insight basé sur un profil de santé
        
        Args:
            health_profile: Profil de santé JSON (depuis health_profiles)
            user_goal: Objectif utilisateur (depuis health_profile si non fourni)
        
        Returns:
            Dict avec:
            - instruction_text: Le conseil généré
            - category: 'movement', 'nutrition', 'recovery', 'stress'
            - priority: 1 (normal) ou 2 (urgent)
        """
        try:
            # Extraire l'objectif utilisateur
            goal = user_goal or health_profile.get("user_goal", "energy")
            
            # Construire le message utilisateur avec le profil
            user_message = self._build_user_message(health_profile, goal)
            
            # Appeler l'API OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=200  # Limite pour rester concis (< 160 caractères recommandé)
            )
            
            instruction_text = response.choices[0].message.content.strip()
            
            # Déterminer la catégorie et la priorité
            category = self._categorize_insight(health_profile, instruction_text)
            priority = self._determine_priority(health_profile)
            
            return {
                "instruction_text": instruction_text,
                "category": category,
                "priority": priority
            }
            
        except Exception as e:
            logger.error(f"Error generating insight: {e}")
            raise
    
    def _build_user_message(self, health_profile: Dict, user_goal: str) -> str:
        """
        Construit le message utilisateur pour l'IA à partir du profil de santé
        """
        current_time = datetime.now().strftime("%H:%M")
        day_of_week = datetime.now().strftime("%A")
        # Traduire le jour en français pour le contexte
        days_fr = {
            "Monday": "lundi",
            "Tuesday": "mardi",
            "Wednesday": "mercredi",
            "Thursday": "jeudi",
            "Friday": "vendredi",
            "Saturday": "samedi",
            "Sunday": "dimanche"
        }
        day_of_week_fr = days_fr.get(day_of_week, day_of_week)
        
        # Extraire les métriques actuelles
        metrics = health_profile.get("current_metrics", {})
        baselines = health_profile.get("baselines", {})
        anomalies = health_profile.get("anomalies", [])
        context = health_profile.get("context", {})
        data_quality = health_profile.get("data_quality", "medium")
        
        # Construire le message structuré
        message_parts = [
            f"Contexte actuel : {current_time}, {day_of_week_fr}",
            f"Objectif utilisateur : {user_goal}",
            f"Qualité des données : {data_quality}",
            "",
            "IMPORTANT : Compare TOUJOURS les valeurs actuelles avec les baselines personnelles de l'utilisateur.",
            "Utilise les pourcentages de variation et mentionne le jour de la semaine pour personnaliser.",
            "",
            "Métriques actuelles (avec contraste baseline) :"
        ]
        
        # Heart Rate (avec contraste baseline)
        if "heart_rate" in metrics:
            hr = metrics["heart_rate"]
            hr_baseline = baselines.get("hr_baseline")
            resting_hr = hr.get('resting_bpm')
            
            if resting_hr and hr_baseline:
                # Calculer la variation en pourcentage
                variation = ((resting_hr - hr_baseline) / hr_baseline) * 100
                if variation > 0:
                    variation_str = f"+{variation:.1f}%"
                    contrast = f"({variation_str} vs ta baseline de {hr_baseline} bpm)"
                elif variation < 0:
                    variation_str = f"{variation:.1f}%"
                    contrast = f"({variation_str} vs ta baseline de {hr_baseline} bpm)"
                else:
                    contrast = f"(identique à ta baseline de {hr_baseline} bpm)"
                message_parts.append(
                    f"- Rythme cardiaque au repos : {resting_hr} bpm {contrast}"
                )
            else:
                message_parts.append(
                    f"- Rythme cardiaque : {hr.get('average_bpm', 'N/A')} bpm (repos: {resting_hr or 'N/A'} bpm)"
                )
                if hr_baseline:
                    message_parts.append(f"  Baseline : {hr_baseline} bpm")
        
        # HRV (avec contraste baseline)
        if "hrv" in metrics:
            hrv = metrics["hrv"]
            hrv_baseline = baselines.get("hrv_baseline")
            current_hrv = hrv.get('average_ms') or hrv.get('latest_ms')
            
            if current_hrv and hrv_baseline:
                # Calculer la variation en pourcentage
                variation = ((current_hrv - hrv_baseline) / hrv_baseline) * 100
                if variation > 0:
                    variation_str = f"+{variation:.1f}%"
                    contrast = f"({variation_str} vs ta baseline de {hrv_baseline} ms)"
                elif variation < 0:
                    variation_str = f"{variation:.1f}%"
                    contrast = f"({variation_str} vs ta baseline de {hrv_baseline} ms)"
                else:
                    contrast = f"(identique à ta baseline de {hrv_baseline} ms)"
                message_parts.append(
                    f"- HRV : {current_hrv} ms {contrast}"
                )
            else:
                message_parts.append(
                    f"- HRV : {current_hrv or 'N/A'} ms (dernier: {hrv.get('latest_ms', 'N/A')} ms)"
                )
                if hrv_baseline:
                    message_parts.append(f"  Baseline : {hrv_baseline} ms")
        
        # Sommeil (avec contraste baseline)
        if "sleep" in metrics:
            sleep = metrics["sleep"]
            sleep_baseline = baselines.get("sleep_baseline")
            sleep_duration = sleep.get('duration_minutes')
            
            if sleep_duration and sleep_baseline:
                # Calculer la variation en pourcentage
                variation = ((sleep_duration - sleep_baseline) / sleep_baseline) * 100
                if variation > 0:
                    variation_str = f"+{variation:.1f}%"
                    contrast = f"({variation_str} vs ta baseline de {sleep_baseline} min)"
                elif variation < 0:
                    variation_str = f"{variation:.1f}%"
                    contrast = f"({variation_str} vs ta baseline de {sleep_baseline} min)"
                else:
                    contrast = f"(identique à ta baseline de {sleep_baseline} min)"
                message_parts.append(
                    f"- Sommeil : {sleep_duration} min {contrast} (qualité: {sleep.get('quality_score', 'N/A')}/100)"
                )
            else:
                message_parts.append(
                    f"- Sommeil : {sleep_duration or 'N/A'} min (qualité: {sleep.get('quality_score', 'N/A')}/100)"
                )
                if sleep_baseline:
                    message_parts.append(f"  Baseline : {sleep_baseline} min")
        
        # Activité
        if "activity" in metrics:
            activity = metrics["activity"]
            message_parts.append(
                f"- Activité : {activity.get('steps', 'N/A')} pas, {activity.get('distance_meters', 'N/A')} m"
            )
        
        # Anomalies (seulement celles avec confidence = high)
        high_confidence_anomalies = [a for a in anomalies if a.get("confidence") == "high"]
        if high_confidence_anomalies:
            message_parts.append("")
            message_parts.append("⚠️ Anomalies détectées (haute confiance) - À mentionner dans le conseil :")
            for anomaly in high_confidence_anomalies:
                if anomaly["type"] == "hrv_drop":
                    drop_pct = anomaly.get('drop_percentage', 0)
                    message_parts.append(
                        f"- HRV chute de {drop_pct:.1f}% vs baseline ({anomaly.get('current', 'N/A')} ms vs {anomaly.get('baseline', 'N/A')} ms)"
                    )
                    message_parts.append(
                        f"  → Formulation suggérée : 'Ton HRV est {drop_pct:.0f}% plus bas que ta moyenne du {day_of_week_fr}'"
                    )
                elif anomaly["type"] == "sleep_deficit":
                    deficit_min = anomaly.get('deficit_minutes', 0)
                    deficit_pct = (deficit_min / anomaly.get('baseline_minutes', 1)) * 100 if anomaly.get('baseline_minutes') else 0
                    message_parts.append(
                        f"- Déficit de sommeil : {deficit_min} min ({deficit_pct:.1f}% de moins) vs baseline"
                    )
                    message_parts.append(
                        f"  → Formulation suggérée : 'Tu as dormi {deficit_min} min de moins que ta moyenne du {day_of_week_fr}'"
                    )
                elif anomaly["type"] == "elevated_resting_hr":
                    increase = anomaly.get('increase', 0)
                    increase_pct = (increase / anomaly.get('baseline_bpm', 1)) * 100 if anomaly.get('baseline_bpm') else 0
                    message_parts.append(
                        f"- Rythme cardiaque au repos élevé : +{increase} bpm ({increase_pct:.1f}% de plus) vs baseline"
                    )
                    message_parts.append(
                        f"  → Formulation suggérée : 'Ton rythme cardiaque est {increase_pct:.0f}% plus élevé que ta moyenne du {day_of_week_fr}'"
                    )
        
        # Contexte
        if context:
            message_parts.append("")
            message_parts.append("Contexte :")
            if "time_of_day" in context:
                message_parts.append(f"- Moment de la journée : {context['time_of_day']}")
            if "trends" in context:
                trends = context["trends"]
                if trends:
                    message_parts.append(f"- Tendances : {json.dumps(trends, ensure_ascii=False)}")
        
        return "\n".join(message_parts)
    
    def _categorize_insight(self, health_profile: Dict, instruction_text: str) -> str:
        """
        Détermine la catégorie de l'insight basé sur le profil et le texte
        """
        instruction_lower = instruction_text.lower()
        
        # Vérifier les anomalies pour déterminer la catégorie
        anomalies = health_profile.get("anomalies", [])
        high_confidence_anomalies = [a for a in anomalies if a.get("confidence") == "high"]
        
        for anomaly in high_confidence_anomalies:
            if anomaly["type"] == "hrv_drop" or anomaly["type"] == "elevated_resting_hr":
                if "stress" in instruction_lower or "respiration" in instruction_lower or "méditation" in instruction_lower:
                    return "stress"
            elif anomaly["type"] == "sleep_deficit":
                return "recovery"
        
        # Catégorisation par mots-clés dans le texte
        if any(word in instruction_lower for word in ["marche", "sport", "exercice", "squat", "mouvement"]):
            return "movement"
        elif any(word in instruction_lower for word in ["repas", "manger", "nutrition", "glucose", "fibre"]):
            return "nutrition"
        elif any(word in instruction_lower for word in ["sommeil", "dormir", "coucher", "récupération"]):
            return "recovery"
        elif any(word in instruction_lower for word in ["stress", "respiration", "calme", "méditation"]):
            return "stress"
        
        # Par défaut
        return "recovery"
    
    def _determine_priority(self, health_profile: Dict) -> int:
        """
        Détermine la priorité de l'insight (1: normal, 2: urgent)
        """
        anomalies = health_profile.get("anomalies", [])
        high_confidence_anomalies = [a for a in anomalies if a.get("confidence") == "high"]
        
        # Priorité urgente si anomalies sévères
        for anomaly in high_confidence_anomalies:
            if anomaly.get("severity") == "high":
                return 2
        
        return 1
