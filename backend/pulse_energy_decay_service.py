"""
Pulse Energy Decay Service
===========================
Modèle mathématique précis de prévision d'énergie intraday basé sur :
- Readiness Score Oura
- Anomalies HRV (Z-Score)
- Pharmacocinétique des médicaments
- Conditions de santé (fatigue chronique, infection, etc.)

Formule : E(t) = E0 - D(t) + ΣM_adj(t)

Auteur : Claude
Date : 31 Janvier 2026
Version : 1.0
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
import math

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================
# Pydantic Models
# ============================================

class Medication(BaseModel):
    """Médicament avec pharmacocinétique"""
    name: str
    time: str  # Format "HH:MM"
    type: str  # "stimulant" ou "sedatif"
    dose: str


class Influencer(BaseModel):
    """Facteur d'influence sur l'énergie"""
    name: str
    impact: str  # Format "+15" ou "-12"
    status: str  # "positive", "negative", "neutral"


class ForecastPoint(BaseModel):
    """Point de la courbe d'énergie"""
    time: str  # ISO 8601
    value: float  # 0-100
    event: Optional[str] = ""


class PulseEnergyDecayForecast(BaseModel):
    """Prévision complète Pulse Energy Decay"""
    type: str = "pulse_energy_decay"
    date: str
    generated_at: str
    model_version: str = "pulse_energy_decay_v1"
    calculation_model: str = "pulse_energy_decay_v1"
    
    current_energy: float = Field(..., ge=0, le=100)
    
    forecast_curve: List[ForecastPoint]
    influencers: List[Influencer]
    
    # Compatibilité avec le format existant
    points: List[Dict[str, Any]]  # Format ancien: [{"t": "ISO", "energy": 72}]
    windows: List[Dict[str, Any]]
    events: List[Dict[str, Any]]
    notes: List[str]
    
    confidence: float = Field(default=0.85, ge=0, le=1)


# ============================================
# Service Principal
# ============================================

class PulseEnergyDecayService:
    """Service de calcul du modèle Pulse Energy Decay avec Smart Fallback"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        
        # Import enrichment services
        from medication_enrichment_service import MedicationEnrichmentService
        from condition_enrichment_service import ConditionEnrichmentService
        
        self.medication_enricher = MedicationEnrichmentService(supabase_client)
        self.condition_enricher = ConditionEnrichmentService(supabase_client)
        
        # Cache des poids personnalisés (chargé au début du calcul)
        self.personalized_weights = {}
        
        # Constantes du modèle
        self.DECAY_RATE_NORMAL = 0.04  # -4% par heure
        self.DECAY_RATE_FATIGUE = 0.07  # -7% par heure si fatigue chronique
        self.DECAY_RATE_ADHD = 0.055  # -5.5% par heure avec TDAH (fluctuations)
        self.DECAY_RATE_DEPRESSION = 0.08  # -8% par heure avec dépression
        self.POST_LUNCH_DIP_START = 7  # heures après réveil
        self.POST_LUNCH_DIP_END = 9
        self.POST_LUNCH_DIP_AMOUNT = 10  # -10 points forfaitaire
        
        # Pharmacocinétique
        self.STIMULANT_PEAK_HOURS = 1  # Pic à T+1h
        self.STIMULANT_DURATION_HOURS = 4
        self.STIMULANT_IMPACT = 15  # +15%
        
        self.SEDATIF_PEAK_HOURS = 2  # Pic à T+2h
        self.SEDATIF_DURATION_HOURS = 6
        self.SEDATIF_IMPACT = -20  # -20%
        
        # HRV Anomaly
        self.HRV_ANOMALY_THRESHOLD = -1.5  # Z-Score
        self.HRV_ANOMALY_MALUS = 15  # -15 points si anomalie
    
    async def generate_forecast(
        self,
        user_id: str,
        target_date_str: Optional[str] = None,
        force_refresh: bool = False
    ) -> Optional[PulseEnergyDecayForecast]:
        """
        Génère une prévision complète Pulse Energy Decay
        
        Args:
            user_id: UUID de l'utilisateur
            target_date_str: Date cible (YYYY-MM-DD), défaut = aujourd'hui
            force_refresh: Ignorer le cache
            
        Returns:
            PulseEnergyDecayForecast ou None
        """
        try:
            # 0. Charger les poids personnalisés ML
            await self._load_personalized_weights(user_id)
            
            # 1. Récupérer les données sources
            health_profile = await self._get_health_profile(user_id)
            medications = await self._get_medications(user_id)
            conditions = await self._get_conditions(user_id)
            
            # Vérifier si on a assez de données pour le modèle avancé
            if not health_profile or health_profile.get('readiness_score', 0) == 0:
                logger.warning(f"[PulseEnergyDecay] Pas de readiness_score pour {user_id}, fallback heuristique")
                return None
            
            # 2. Calculer E0 (Capital de départ)
            E0_base = self._calculate_E0(health_profile)
            
            # 3. Déterminer le taux de décroissance basé sur les conditions (dynamique)
            decay_rate = self.DECAY_RATE_NORMAL
            active_condition = None
            condition_impact = None
            energy_malus_total = 0
            
            # Récupérer l'impact de chaque condition et sélectionner la plus sévère
            if conditions:
                max_decay_rate = self.DECAY_RATE_NORMAL
                for condition in conditions:
                    condition_name = condition.get('display', '')
                    condition_code = condition.get('code', '')
                    
                    if not condition_code:
                        logger.warning(f"[PulseEnergyDecay] Condition sans code ICD-11: {condition_name}")
                        continue
                    
                    # Récupérer l'impact (DB ou IA)
                    impact = await self._get_condition_impact(condition_name, condition_code)
                    
                    # Appliquer le poids personnalisé (ML adaptatif)
                    personalized_weight = self._get_personalized_weight('condition', condition_code)
                    adjusted_decay_rate = impact['decay_rate'] * personalized_weight
                    adjusted_malus = impact['energy_malus'] * personalized_weight
                    
                    # Garder la condition avec le decay_rate le plus élevé
                    if adjusted_decay_rate > max_decay_rate:
                        max_decay_rate = adjusted_decay_rate
                        decay_rate = adjusted_decay_rate
                        active_condition = condition_name
                        condition_impact = impact
                    
                    # Cumuler les malus d'énergie (plafonné à -50)
                    energy_malus_total += adjusted_malus
                
                # Plafonner le malus total
                energy_malus_total = max(energy_malus_total, -50)
                logger.info(f"[PulseEnergyDecay] Condition la plus impactante: {active_condition} (decay_rate={decay_rate:.3f}, malus={energy_malus_total})")
            
            # Appliquer le malus d'énergie au capital de départ
            E0 = E0_base + energy_malus_total
            
            # 4. Récupérer l'heure de réveil depuis bedtime_end (données réelles Oura)
            now = datetime.now(timezone.utc)
            wake_time = None
            
            # Essayer de récupérer bedtime_end depuis health_profile (fourni par RPC)
            bedtime_end_str = health_profile.get('bedtime_end')
            
            if bedtime_end_str:
                try:
                    # Parser le timestamp ISO avec timezone
                    if isinstance(bedtime_end_str, str):
                        wake_time = datetime.fromisoformat(bedtime_end_str.replace('Z', '+00:00'))
                    else:
                        # Si c'est déjà un datetime
                        wake_time = bedtime_end_str
                    
                    logger.info(f"[PulseEnergyDecay] ✅ Wake time from Oura bedtime_end: {wake_time.isoformat()} ({wake_time.astimezone(timezone.utc).strftime('%H:%M')} UTC)")
                except Exception as e:
                    logger.warning(f"[PulseEnergyDecay] ⚠️ Could not parse bedtime_end: {e}")
                    wake_time = None
            
            # Fallback si pas de bedtime_end : 10h UTC = 11h Paris
            if not wake_time:
                wake_hour = 10  # Défaut : 10h UTC = 11h heure de Paris
                wake_time = now.replace(hour=wake_hour, minute=0, second=0, microsecond=0)
                if now < wake_time:
                    wake_time = wake_time - timedelta(days=1)
                logger.warning(f"[PulseEnergyDecay] ⚠️ No bedtime_end found, using default wake time: {wake_hour}h UTC")
            
            hours_since_wake_debug = (now - wake_time).total_seconds() / 3600
            logger.info(f"[PulseEnergyDecay] now={now.isoformat()}, wake_time={wake_time.isoformat()}, hours_since_wake={hours_since_wake_debug:.2f}h")
            
            # 5. Générer la courbe d'énergie (16h de prévision)
            forecast_curve = self._generate_energy_curve(
                E0=E0,
                wake_time=wake_time,
                now=now,
                decay_rate=decay_rate,
                medications=medications,
                active_condition=active_condition
            )
            
            # 6. Générer les influencers
            influencers = self._generate_influencers(
                health_profile=health_profile,
                medications=medications,
                active_condition=active_condition,
                condition_impact=condition_impact,
                E0=E0
            )
            
            # 7. Détecter les risk windows
            windows = self._detect_risk_windows(forecast_curve)
            
            # 8. Générer les notes
            notes = self._generate_notes(
                health_profile=health_profile,
                medications=medications,
                active_condition=active_condition,
                condition_impact=condition_impact,
                windows=windows
            )
            
            # 9. Construire la réponse
            # Trouver l'énergie actuelle (le point le plus proche de maintenant)
            current_energy = E0
            if forecast_curve:
                now_timestamp = now.replace(tzinfo=None)
                closest_point = min(
                    forecast_curve,
                    key=lambda p: abs(
                        (datetime.fromisoformat(p.time.replace('Z', '+00:00')).replace(tzinfo=None) - now_timestamp).total_seconds()
                    )
                )
                current_energy = closest_point.value
            
            # Conversion au format ancien (compatibilité)
            points = [{"t": p.time, "energy": p.value} for p in forecast_curve]
            
            forecast = PulseEnergyDecayForecast(
                date=target_date_str or now.strftime('%Y-%m-%d'),
                generated_at=now.isoformat(),
                current_energy=current_energy,
                forecast_curve=forecast_curve,
                influencers=influencers,
                points=points,
                windows=windows,
                events=[],  # TODO: Intégrer calendar events
                notes=notes,
                confidence=self._calculate_confidence(health_profile, medications)
            )
            
            # 10. Sauvegarder dans la DB
            await self._save_forecast(user_id, forecast)
            
            return forecast
            
        except Exception as e:
            logger.error(f"[PulseEnergyDecay] Error generating forecast: {e}", exc_info=True)
            return None
    
    def _calculate_E0(self, health_profile: Dict) -> float:
        """
        Calcul du capital de départ E0
        
        E0 = readiness_score - (malus HRV si anomalie)
        """
        readiness = health_profile.get('readiness_score', 70)
        anomalies = health_profile.get('anomalies', [])
        
        # Si readiness_score est 0, utiliser un minimum raisonnable basé sur les données disponibles
        if readiness == 0 or readiness is None:
            logger.warning(f"[PulseEnergyDecay] readiness_score is 0 or None, using minimum of 50")
            readiness = 50  # Minimum raisonnable
        
        E0 = float(readiness)
        
        # Vérifier les anomalies HRV
        for anomaly in anomalies:
            if anomaly.get('type') == 'hrv_drop':
                z_score = anomaly.get('z_score', 0)
                if z_score < self.HRV_ANOMALY_THRESHOLD:
                    E0 -= self.HRV_ANOMALY_MALUS
                    logger.info(f"[PulseEnergyDecay] HRV anomaly detected (z={z_score}), E0 malus: -{self.HRV_ANOMALY_MALUS}")
        
        # Clamp entre 0-100
        E0 = max(0, min(100, E0))
        
        logger.info(f"[PulseEnergyDecay] E0 calculated: {E0} (from readiness: {health_profile.get('readiness_score', 'N/A')})")
        return E0
    
    def _generate_energy_curve(
        self,
        E0: float,
        wake_time: datetime,
        now: datetime,
        decay_rate: float,
        medications: List[Dict],
        active_condition: Optional[str] = None
    ) -> List[ForecastPoint]:
        """
        Génère la courbe d'énergie avec décroissance et pharmacocinétique
        
        Points toutes les 30 minutes depuis le réveil jusqu'à minuit
        """
        points = []
        
        logger.info(f"[PulseEnergyDecay] Generating curve with E0={E0}, decay_rate={decay_rate}")
        
        # Calculer la fin de journée (minuit)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)
        
        # Calculer le nombre de points depuis le réveil jusqu'à minuit
        hours_until_end = (end_of_day - wake_time).total_seconds() / 3600
        num_points = int(hours_until_end * 2)  # 2 points par heure (toutes les 30min)
        
        logger.info(f"[PulseEnergyDecay] Generating {num_points} points from {wake_time.strftime('%H:%M')} to {end_of_day.strftime('%H:%M')}")
        
        # Générer les points depuis le réveil
        for i in range(num_points):
            t = wake_time + timedelta(minutes=i * 30)
            hours_since_wake = (t - wake_time).total_seconds() / 3600
            
            # Base : E0 - décroissance naturelle
            energy = E0 - (E0 * decay_rate * hours_since_wake)
            
            # Debug pour le premier point
            if i == 0:
                logger.info(f"[PulseEnergyDecay] First point: hours_since_wake={hours_since_wake:.2f}h, E0={E0}, decay={E0 * decay_rate * hours_since_wake:.2f}, energy={energy:.2f}")
            
            # Creux post-lunch (7h-9h après réveil)
            if self.POST_LUNCH_DIP_START <= hours_since_wake <= self.POST_LUNCH_DIP_END:
                dip_progress = (hours_since_wake - self.POST_LUNCH_DIP_START) / (self.POST_LUNCH_DIP_END - self.POST_LUNCH_DIP_START)
                # Bell curve pour le creux
                dip_factor = math.sin(dip_progress * math.pi)
                energy -= self.POST_LUNCH_DIP_AMOUNT * dip_factor
            
            # Appliquer l'impact des médicaments
            for med in medications:
                med_impact = self._calculate_medication_impact(med, t)
                energy += med_impact
            
            # Clamp avec minimum de 10% pour garder une courbe visible
            energy = max(10, min(100, energy))
            
            # Déterminer l'événement marquant
            event = self._detect_event(t, wake_time, hours_since_wake, medications)
            
            points.append(ForecastPoint(
                time=t.isoformat(),
                value=round(energy, 1),
                event=event
            ))
        
        if points:
            logger.info(f"[PulseEnergyDecay] Curve generated: {len(points)} points, first={points[0].value}%, last={points[-1].value}%")
        
        return points
    
    def _calculate_medication_impact(
        self,
        medication: Dict,
        current_time: datetime
    ) -> float:
        """
        Calcule l'impact énergétique d'un médicament à un instant t
        
        Prend en compte:
        - Phase aiguë (courbe de concentration)
        - Phase chronique (adaptation long terme)
        - Tolérance développée
        - Type de courbe (gaussian, exponential, linear, plateau)
        
        Args:
            medication: Dict avec 'pharmacokinetics', 'intake_times', 'days_since_start'
            current_time: Instant actuel
            
        Returns:
            Impact énergétique total
        """
        pharma = medication.get('pharmacokinetics')
        
        # Si pas de données pharmacocinétiques, retourner 0
        if not pharma:
            return 0.0
        
        # 1. Calculer l'impact AIGU (courbe de concentration)
        acute_impact = self._calculate_acute_phase(
            medication,
            current_time,
            pharma
        )
        
        # 2. Calculer l'impact CHRONIQUE (adaptation long terme)
        days_since_start = medication.get('days_since_start', 0)
        chronic_impact = self._calculate_chronic_phase(
            days_since_start,
            pharma
        )
        
        # 3. Appliquer la tolérance
        tolerance_factor = self._calculate_tolerance(
            days_since_start,
            pharma.get('tolerance_rate', 0)
        )
        
        # 4. Impact total
        total_impact = (acute_impact * tolerance_factor) + chronic_impact
        
        # 5. Appliquer le poids personnalisé (ML adaptatif)
        atc_code = medication.get('atc_code')
        if atc_code:
            personalized_weight = self._get_personalized_weight('medication', atc_code)
            total_impact *= personalized_weight
        
        return total_impact
    
    def _calculate_acute_phase(
        self,
        medication: Dict,
        current_time: datetime,
        pharma: Dict
    ) -> float:
        """
        Phase aiguë: calcul basé sur la courbe de concentration plasmatique
        """
        intake_times = medication.get('intake_times', [])
        if not intake_times:
            return 0.0
        
        # Trouver la dernière prise avant current_time
        time_since_dose = None
        for intake_time_str in intake_times:
            try:
                hour, minute = map(int, intake_time_str.split(':'))
                intake_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # Si l'heure de prise est dans le futur, c'était hier
                if intake_time > current_time:
                    intake_time = intake_time - timedelta(days=1)
                
                hours_since = (current_time - intake_time).total_seconds() / 3600
                
                # Garder la prise la plus récente
                if hours_since >= 0 and (time_since_dose is None or hours_since < time_since_dose):
                    time_since_dose = hours_since
                    
            except Exception as e:
                logger.warning(f"[PulseEnergyDecay] Invalid intake time: {intake_time_str}")
                continue
        
        if time_since_dose is None or time_since_dose < 0:
            return 0.0
        
        # Vérifier si l'effet est terminé
        duration = pharma.get('duration')
        if duration and time_since_dose > duration:
            return 0.0
        
        # Calculer selon le type de courbe
        curve_type = pharma.get('acute_impact_curve', 'gaussian')
        peak_time = pharma.get('peak_time', 1)
        max_impact = pharma.get('acute_impact_max', 0)
        onset_time = pharma.get('onset_time', 0)
        
        # Pas encore d'effet
        if time_since_dose < onset_time:
            return 0.0
        
        if curve_type == 'gaussian':
            # Bell curve (ex: caféine, benzodiazépines)
            sigma = peak_time / 2
            impact = max_impact * math.exp(
                -((time_since_dose - peak_time) ** 2) / (2 * sigma ** 2)
            )
        
        elif curve_type == 'exponential':
            # Montée rapide, décroissance exponentielle (ex: Ritalin)
            if time_since_dose < peak_time:
                # Montée linéaire
                impact = max_impact * (time_since_dose / peak_time)
            else:
                # Décroissance exponentielle
                half_life = pharma.get('half_life', peak_time * 2)
                decay_constant = math.log(2) / half_life
                impact = max_impact * math.exp(
                    -decay_constant * (time_since_dose - peak_time)
                )
        
        elif curve_type == 'linear' or curve_type == 'plateau':
            # Plateau constant (ex: thyroïde, antidépresseurs)
            if time_since_dose >= onset_time:
                impact = max_impact
            else:
                impact = 0.0
        
        else:
            # Par défaut: gaussian
            sigma = peak_time / 2
            impact = max_impact * math.exp(
                -((time_since_dose - peak_time) ** 2) / (2 * sigma ** 2)
            )
        
        return impact
    
    def _calculate_chronic_phase(self, days_since_start: int, pharma: Dict) -> float:
        """
        Phase chronique: adaptation métabolique à long terme
        Ex: thyroïde prend 4-6 semaines, antidépresseurs 2-4 semaines
        """
        chronic_impact = pharma.get('chronic_impact', 0)
        
        if chronic_impact == 0:
            return 0.0
        
        # Progression selon chronic_onset_days
        chronic_onset_days = pharma.get('chronic_onset_days', 0)
        
        if chronic_onset_days == 0:
            # Effet immédiat
            return chronic_impact
        
        # Progression linéaire jusqu'au plateau
        progression = min(1.0, days_since_start / chronic_onset_days)
        return chronic_impact * progression
    
    def _calculate_tolerance(self, days_since_start: int, tolerance_rate: float) -> float:
        """
        Calcule le facteur de tolérance développée
        Ex: caféine perd 30% d'efficacité après 2 semaines
        
        Returns:
            Facteur multiplicatif (0.3 à 1.0)
        """
        if tolerance_rate == 0:
            return 1.0  # Aucune tolérance
        
        # Courbe de tolérance (exponentielle décroissante)
        # tolerance_rate = 0.3 → perte de 30% après 14 jours
        tolerance_factor = 1.0 - (
            tolerance_rate * (1 - math.exp(-days_since_start / 14))
        )
        
        return max(0.3, tolerance_factor)  # Minimum 30% d'efficacité
        
        return impact
    
    def _detect_event(
        self,
        t: datetime,
        wake_time: datetime,
        hours_since_wake: float,
        medications: List[Dict]
    ) -> str:
        """Détecte les événements marquants à afficher sur la courbe"""
        
        # Réveil
        if abs((t - wake_time).total_seconds()) < 1800:  # ±30 min
            return "Wake up"
        
        # Creux post-lunch
        if self.POST_LUNCH_DIP_START <= hours_since_wake <= self.POST_LUNCH_DIP_END:
            return "Circadian Dip"
        
        # Médicaments (pic d'effet)
        for med in medications:
            med_time_str = med.get('time', '08:00')
            try:
                hour, minute = map(int, med_time_str.split(':'))
                med_time = t.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # Pic à T+1h (stimulant) ou T+2h (sédatif)
                peak_offset = 1 if med['type'] == 'stimulant' else 2
                peak_time = med_time + timedelta(hours=peak_offset)
                
                if abs((t - peak_time).total_seconds()) < 1800:  # ±30 min
                    return f"Medication: {med['name']}"
            except:
                pass
        
        # Fin de journée (22h)
        if t.hour == 22:
            return "Sleep Ready"
        
        return ""
    
    def _generate_influencers(
        self,
        health_profile: Dict,
        medications: List[Dict],
        active_condition: Optional[str],
        condition_impact: Optional[Dict],
        E0: float
    ) -> List[Influencer]:
        """Génère la liste des facteurs d'influence"""
        influencers = []
        
        # 1. Sommeil (Readiness)
        readiness = health_profile.get('readiness_score', 0)
        if readiness > 0:
            status = "positive" if readiness >= 70 else "negative" if readiness < 50 else "neutral"
            influencers.append(Influencer(
                name="Sommeil (Readiness)",
                impact=f"+{readiness}" if readiness >= 70 else f"{readiness - 70:+d}",
                status=status
            ))
        
        # 2. HRV Anomaly
        anomalies = health_profile.get('anomalies', [])
        for anomaly in anomalies:
            if anomaly.get('type') == 'hrv_drop':
                z_score = anomaly.get('z_score', 0)
                if z_score < self.HRV_ANOMALY_THRESHOLD:
                    influencers.append(Influencer(
                        name="HRV Anomaly",
                        impact=f"-{self.HRV_ANOMALY_MALUS}",
                        status="negative"
                    ))
        
        # 3. Médicaments (dynamique selon pharmacocinétique)
        now = datetime.now(timezone.utc)
        for med in medications:
            pharma = med.get('pharmacokinetics')
            if not pharma:
                continue
            
            # Calculer l'impact actuel
            current_impact = self._calculate_medication_impact(med, now)
            
            if abs(current_impact) < 1:
                continue  # Impact trop faible, ne pas afficher
            
            # Badge selon la phase
            days_since_start = med.get('days_since_start', 0)
            
            if days_since_start < 7:
                phase_emoji = "🆕"  # Début de traitement
            elif pharma.get('tolerance_rate', 0) > 0.2 and days_since_start > 14:
                phase_emoji = "⚠️"  # Tolérance développée
            else:
                phase_emoji = "💊"  # Traitement établi
            
            # Statut
            status = "positive" if current_impact > 0 else "negative" if current_impact < 0 else "neutral"
            
            med_name = med.get('medication_name', 'Médicament')
            
            influencers.append(Influencer(
                name=f"{phase_emoji} {med_name}",
                impact=f"{current_impact:+.0f}",
                status=status
            ))
        
        # 4. Condition de santé (dynamique depuis la table)
        if active_condition and condition_impact:
            decay_increase = (condition_impact['decay_rate'] - self.DECAY_RATE_NORMAL) * 100
            impact_on_8h = int(decay_increase * 8)  # Impact sur 8h
            
            # Emoji selon severity
            severity = condition_impact.get('severity', 'moderate')
            emoji_map = {
                'low': '⚠️',
                'moderate': '⚡',
                'high': '😔',
                'severe': '🚨'
            }
            emoji = emoji_map.get(severity, '⚠️')
            
            influencers.append(Influencer(
                name=f"{emoji} {active_condition.title()}",
                impact=f"-{impact_on_8h}",
                status="negative"
            ))
        
        return influencers
    
    def _detect_risk_windows(self, forecast_curve: List[ForecastPoint]) -> List[Dict]:
        """Détecte les fenêtres de risque (creux d'énergie)"""
        windows = []
        
        in_dip = False
        dip_start = None
        
        for i, point in enumerate(forecast_curve):
            if point.value < 50 and not in_dip:
                # Début d'un creux
                in_dip = True
                dip_start = point.time
            elif point.value >= 50 and in_dip:
                # Fin d'un creux
                in_dip = False
                if dip_start:
                    windows.append({
                        "from": datetime.fromisoformat(dip_start).strftime('%H:%M'),
                        "to": datetime.fromisoformat(point.time).strftime('%H:%M'),
                        "kind": "dip",
                        "label": "Creux probable"
                    })
        
        return windows
    
    def _generate_notes(
        self,
        health_profile: Dict,
        medications: List[Dict],
        active_condition: Optional[str],
        condition_impact: Optional[Dict],
        windows: List[Dict]
    ) -> List[str]:
        """Génère les notes explicatives"""
        notes = []
        
        # Anomalies HRV
        anomalies = health_profile.get('anomalies', [])
        for anomaly in anomalies:
            if anomaly.get('type') == 'hrv_drop':
                notes.append(f"⚠️ Anomalie HRV détectée ce matin (Z-Score: {anomaly.get('z_score', 0):.1f})")
        
        # Médicaments (notes contextuelles)
        now = datetime.now(timezone.utc)
        for med in medications:
            pharma = med.get('pharmacokinetics')
            if not pharma:
                continue
            
            med_name = med.get('medication_name', 'Médicament')
            days_since_start = med.get('days_since_start', 0)
            
            # Note selon la phase
            if days_since_start < 7:
                fatigue_risk = pharma.get('fatigue_risk')
                if fatigue_risk in ['high', 'severe']:
                    notes.append(
                        f"🆕 {med_name} : début de traitement. "
                        f"Fatigue normale les premiers jours."
                    )
            
            elif days_since_start >= pharma.get('chronic_onset_days', 28):
                chronic_impact = pharma.get('chronic_impact', 0)
                if chronic_impact > 0:
                    notes.append(
                        f"💊 {med_name} : effet thérapeutique établi "
                        f"({chronic_impact:+.0f} points)"
                    )
                elif chronic_impact < 0:
                    notes.append(
                        f"⚠️ {med_name} : fatigue chronique possible "
                        f"({chronic_impact:.0f} points)"
                    )
            
            # Alerte tolérance
            tolerance_rate = pharma.get('tolerance_rate', 0)
            if tolerance_rate > 0.3 and days_since_start > 14:
                tolerance_pct = int(tolerance_rate * 100)
                notes.append(
                    f"⚠️ {med_name} : tolérance développée "
                    f"(-{tolerance_pct}% d''efficacité). Envisager pause thérapeutique?"
                )
            
            # Alerte pic/crash pour stimulants
            if pharma.get('energy_category') == 'stimulant':
                intake_times = med.get('intake_times', [])
                if intake_times:
                    next_intake = self._get_next_intake_time(intake_times, now)
                    if next_intake:
                        subcategory = pharma.get('subcategory')
                        if subcategory in ['methylphenidate', 'amphetamine']:
                            notes.append(
                                f"📉 {med_name} : crash possible avant prochaine prise ({next_intake})"
                            )
        
        # Creux
        if windows:
            first_dip = windows[0]
            notes.append(f"📉 Creux circadien prévu {first_dip['from']}-{first_dip['to']}")
        
        # Condition (dynamique)
        if active_condition and condition_impact:
            decay_rate_pct = condition_impact['decay_rate'] * 100
            severity = condition_impact.get('severity', 'moderate')
            evidence = condition_impact.get('evidence_level', 'unknown')
            
            # Message selon niveau de preuve
            evidence_badge = {
                'clinical_study': '🔬',
                'expert_consensus': '👨‍⚕️',
                'estimated': '📊',
                'ai_generated': '🤖'
            }.get(evidence, '')
            
            notes.append(f"{evidence_badge} {active_condition.title()} : décroissance accélérée (-{decay_rate_pct:.1f}%/h)")
        
        return notes
    
    def _parse_time_and_add_hours(self, time_str: str, hours_to_add: float) -> str:
        """Parse HH:MM et ajoute des heures"""
        try:
            hour, minute = map(int, time_str.split(':'))
            result_hour = (hour + int(hours_to_add)) % 24
            return f"{result_hour:02d}:{minute:02d}"
        except:
            return "N/A"
    
    def _get_next_intake_time(self, intake_times: List[str], current_time: datetime) -> Optional[str]:
        """
        Trouve la prochaine heure de prise après current_time
        
        Args:
            intake_times: Liste d'heures ["08:00", "20:00"]
            current_time: Instant actuel
            
        Returns:
            Heure au format "HH:MM" ou None
        """
        if not intake_times:
            return None
        
        try:
            current_hour = current_time.hour
            current_minute = current_time.minute
            current_total_minutes = current_hour * 60 + current_minute
            
            next_intake = None
            min_diff = float('inf')
            
            for intake_time_str in intake_times:
                hour, minute = map(int, intake_time_str.split(':'))
                intake_total_minutes = hour * 60 + minute
                
                # Différence en minutes
                diff = intake_total_minutes - current_total_minutes
                
                # Si dans le futur aujourd'hui
                if diff > 0 and diff < min_diff:
                    min_diff = diff
                    next_intake = intake_time_str
            
            return next_intake
            
        except Exception as e:
            logger.warning(f"[PulseEnergyDecay] Error finding next intake time: {e}")
            return None
    
    def _calculate_confidence(self, health_profile: Dict, medications: List[Dict]) -> float:
        """Calcule la confiance du modèle"""
        confidence = 0.5  # Base
        
        # +0.3 si readiness_score présent
        if health_profile.get('readiness_score', 0) > 0:
            confidence += 0.3
        
        # +0.1 si HRV présent
        if health_profile.get('hrv_ms', 0) > 0:
            confidence += 0.1
        
        # +0.1 si médicaments documentés
        if medications:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    async def _get_health_profile(self, user_id: str) -> Dict:
        """Récupère le profil santé du jour"""
        try:
            result = self.supabase.client.rpc('get_today_health_profile', {'p_user_id': user_id}).execute()
            return result.data if result.data else {}
        except Exception as e:
            logger.error(f"[PulseEnergyDecay] Error fetching health_profile: {e}")
            return {}
    
    async def _get_medications(self, user_id: str) -> List[Dict]:
        """
        Récupère les médicaments actifs avec enrichissement pharmacocinétique AUTOMATIQUE
        
        Inclut Smart Fallback GPT-4o pour médicaments sans ATC code
        
        Returns:
            List[Dict]: [
                {
                    'medication_name': 'Levothyrox',
                    'active_substance': 'Lévothyroxine',
                    'atc_code': 'H03AA01',
                    'dosage': 50,
                    'dosage_unit': 'µg',
                    'intake_times': ['08:00'],
                    'start_date': '2024-01-01',
                    'days_since_start': 30,
                    'pharmacokinetics': {...}  # Données enrichies
                },
                ...
            ]
        """
        try:
            # Récupérer les médicaments depuis la nouvelle table
            result = self.supabase.client.rpc('get_user_active_medications', {'p_user_id': user_id}).execute()
            medications = result.data if isinstance(result.data, list) else []
            
            # Enrichir chaque médicament avec les données pharmacocinétiques
            enriched_medications = []
            for med in medications:
                medication_name = med.get('medication_name')
                atc_code = med.get('atc_code')
                medication_id = med.get('id')
                
                # SMART FALLBACK: Si pas d'ATC code, enrichir automatiquement
                if not atc_code:
                    logger.info(f"[AI_ENRICHMENT] Médicament sans ATC: {medication_name}, enrichissement automatique...")
                    enrichment_result = await self.medication_enricher.enrich_medication(
                        medication_name=medication_name,
                        user_id=user_id,
                        medication_id=medication_id,
                        dosage=f"{med.get('dosage')}{med.get('dosage_unit', '')}"
                    )
                    
                    # Mettre à jour avec le nouveau ATC code
                    if enrichment_result.get('atc_code'):
                        atc_code = enrichment_result['atc_code']
                        med['atc_code'] = atc_code
                        med['active_substance'] = enrichment_result.get('active_substance')
                
                # Récupérer pharmacocinétique (maintenant avec ATC code)
                pharma_data = await self._get_medication_pharmacokinetics(
                    med.get('active_substance', medication_name),
                    atc_code
                )
                
                enriched_medications.append({
                    **med,
                    'pharmacokinetics': pharma_data
                })
            
            logger.info(f"[PulseEnergyDecay] Retrieved {len(enriched_medications)} active medications")
            return enriched_medications
            
        except Exception as e:
            logger.error(f"[PulseEnergyDecay] Error fetching medications: {e}")
            return []
    
    async def _get_medication_pharmacokinetics(
        self,
        substance: str,
        atc_code: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Récupère les données pharmacocinétiques depuis medication_energy_impacts
        Avec fallback IA si non trouvé
        
        Returns:
            Dict ou None si non trouvé
        """
        try:
            # Chercher par code ATC d'abord
            if atc_code:
                result = self.supabase.client.table('medication_energy_impacts')\
                    .select('*')\
                    .eq('atc_code', atc_code)\
                    .eq('is_active', True)\
                    .maybe_single()\
                    .execute()
                
                if result.data:
                    logger.info(f"[PulseEnergyDecay] ✅ Pharmacokinétique trouvée en DB pour {substance} ({atc_code})")
                    return result.data
            
            # Sinon chercher par substance
            result = self.supabase.client.table('medication_energy_impacts')\
                .select('*')\
                .ilike('active_substance', f'%{substance}%')\
                .eq('is_active', True)\
                .limit(1)\
                .execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"[PulseEnergyDecay] ✅ Pharmacokinétique trouvée en DB pour {substance}")
                return result.data[0]
            
            # Pas trouvé → Fallback IA
            logger.info(f"[PulseEnergyDecay] 🤖 Médicament {substance} non répertorié, appel IA...")
            return await self._get_ai_medication_pharmacokinetics(substance, atc_code)
            
        except Exception as e:
            logger.error(f"[PulseEnergyDecay] Error fetching medication pharmacokinetics: {e}")
            return None
    
    async def _get_ai_medication_pharmacokinetics(
        self,
        substance: str,
        atc_code: Optional[str] = None
    ) -> Dict:
        """
        Utilise GPT-4 pour estimer la pharmacocinétique d'un médicament non répertorié
        Sauvegarde ensuite l'estimation dans la table
        """
        try:
            from llm_client import LLMClient
            
            llm = LLMClient()
            
            prompt = f"""Tu es un expert pharmacologue spécialisé en pharmacocinétique et fatigue médicamenteuse.

Médicament: {substance}
Code ATC: {atc_code or 'Inconnu'}

Estime l'impact de ce médicament sur l'énergie quotidienne, basé sur:
1. La pharmacocinétique (demi-vie, pic, durée d'action)
2. Les études cliniques sur la fatigue associée
3. Le profil d'effets secondaires

Fournis:
- energy_category: "stimulant", "sedative", "neutral", ou "mixed"
- onset_time: Délai d'action en heures
- peak_time: Pic de concentration en heures
- duration: Durée d'action en heures (null si effet continu)
- half_life: Demi-vie en heures
- acute_impact_min: Impact minimum sur 100 (-50 à +50)
- acute_impact_max: Impact maximum sur 100 (-50 à +50)
- acute_impact_curve: "gaussian", "exponential", "linear", ou "plateau"
- chronic_impact: Impact après adaptation long terme (-50 à +50)
- chronic_onset_days: Jours avant effet chronique (0 si immédiat)
- tolerance_rate: Vitesse de tolérance 0.0-1.0 (0=aucune, 0.5=forte)
- fatigue_risk: "none", "low", "moderate", "high", "severe"
- justification: 2-3 phrases expliquant

RÉPONDS UNIQUEMENT EN JSON:
{{
    "energy_category": "...",
    "onset_time": X.X,
    "peak_time": X.X,
    "duration": X.X,
    "half_life": X.X,
    "acute_impact_min": X,
    "acute_impact_max": X,
    "acute_impact_curve": "...",
    "chronic_impact": X,
    "chronic_onset_days": X,
    "tolerance_rate": X.X,
    "fatigue_risk": "...",
    "justification": "..."
}}"""

            response = llm.generate_insight(prompt, temperature=0.3, max_tokens=400)
            
            # Extraire le contenu et parser le JSON
            import json
            content = response.get('content', '{}')
            ai_pharma = json.loads(content.strip())
            
            # Ajouter métadonnées
            ai_pharma['evidence_level'] = 'ai_generated'
            ai_pharma['source'] = f'GPT-4 estimation - {datetime.now(timezone.utc).isoformat()}'
            ai_pharma['active_substance'] = substance
            ai_pharma['medication_name'] = substance
            
            # Sauvegarder dans la DB pour les prochaines fois
            try:
                insert_data = {
                    'atc_code': atc_code,
                    'medication_name': substance,
                    'active_substance': substance,
                    'energy_category': ai_pharma['energy_category'],
                    'onset_time': ai_pharma.get('onset_time'),
                    'peak_time': ai_pharma.get('peak_time'),
                    'duration': ai_pharma.get('duration'),
                    'half_life': ai_pharma.get('half_life'),
                    'acute_impact_min': ai_pharma.get('acute_impact_min', 0),
                    'acute_impact_max': ai_pharma.get('acute_impact_max', 0),
                    'acute_impact_curve': ai_pharma.get('acute_impact_curve', 'gaussian'),
                    'chronic_impact': ai_pharma.get('chronic_impact', 0),
                    'chronic_onset_days': ai_pharma.get('chronic_onset_days', 0),
                    'tolerance_rate': ai_pharma.get('tolerance_rate', 0),
                    'fatigue_risk': ai_pharma.get('fatigue_risk', 'moderate'),
                    'evidence_level': 'ai_generated',
                    'source': ai_pharma['source'],
                    'notes': ai_pharma.get('justification', ''),
                    'is_active': True
                }
                
                self.supabase.client.table('medication_energy_impacts')\
                    .insert(insert_data)\
                    .execute()
                
                logger.info(f"[PulseEnergyDecay] 💾 Pharmacokinétique IA sauvegardée pour {substance}")
            except Exception as save_error:
                logger.warning(f"[PulseEnergyDecay] Impossible de sauvegarder pharmacokinétique IA: {save_error}")
            
            return ai_pharma
            
        except Exception as e:
            logger.error(f"[PulseEnergyDecay] Erreur fallback IA médicament: {e}")
            # Fallback conservateur
            return {
                'energy_category': 'neutral',
                'onset_time': 1,
                'peak_time': 2,
                'duration': 6,
                'half_life': 6,
                'acute_impact_min': 0,
                'acute_impact_max': 0,
                'acute_impact_curve': 'gaussian',
                'chronic_impact': 0,
                'chronic_onset_days': 0,
                'tolerance_rate': 0,
                'fatigue_risk': 'moderate',
                'evidence_level': 'ai_error_fallback',
                'source': 'ai_error_fallback'
            }
    
    async def _get_conditions(self, user_id: str) -> List[Dict]:
        """
        Récupère les conditions de santé avec leurs codes ICD-11.
        
        Returns:
            List[Dict]: [{'display': 'depression', 'code': '6A70'}, ...]
        """
        try:
            result = self.supabase.client.rpc('get_health_conditions', {'p_user_id': user_id}).execute()
            return result.data if isinstance(result.data, list) else []
        except Exception as e:
            logger.error(f"[PulseEnergyDecay] Error fetching conditions: {e}")
            return []
    
    async def _load_personalized_weights(self, user_id: str):
        """
        Charge les poids personnalisés de l'utilisateur (ML adaptatif)
        
        Stocke dans self.personalized_weights avec clé "type:code"
        """
        try:
            result = self.supabase.client.table('personalized_weights')\
                .select('factor_type, factor_code, weight_multiplier, confidence_score')\
                .eq('user_id', user_id)\
                .eq('is_active', True)\
                .execute()
            
            if result.data:
                self.personalized_weights = {
                    f"{w['factor_type']}:{w['factor_code']}": {
                        'weight': w['weight_multiplier'],
                        'confidence': w['confidence_score']
                    }
                    for w in result.data
                }
                logger.info(f"[PulseEnergyDecay] ⚖️ {len(self.personalized_weights)} poids personnalisés chargés")
            else:
                self.personalized_weights = {}
                
        except Exception as e:
            logger.error(f"[PulseEnergyDecay] Erreur chargement poids personnalisés: {e}")
            self.personalized_weights = {}
    
    def _get_personalized_weight(self, factor_type: str, factor_code: str) -> float:
        """
        Récupère le poids personnalisé d'un facteur
        
        Returns:
            float: multiplicateur (0.5-2.0, défaut 1.0)
        """
        key = f"{factor_type}:{factor_code}"
        weight_data = self.personalized_weights.get(key)
        
        if weight_data:
            weight = weight_data['weight']
            confidence = weight_data['confidence']
            logger.debug(f"[PWA] {key}: weight={weight:.2f}, confidence={confidence:.2f}")
            return weight
        
        return 1.0  # Baseline
    
    async def _get_condition_impact(self, condition_name: str, icd11_code: str) -> Dict:
        """
        Récupère l'impact énergétique d'une condition depuis la table condition_energy_impacts.
        Si la condition n'existe pas dans la table, utilise le fallback IA.
        
        Returns:
            Dict avec: decay_rate, energy_malus, variability, severity, evidence_level
        """
        try:
            # Chercher par code ICD-11
            result = self.supabase.client.table('condition_energy_impacts')\
                .select('*')\
                .eq('icd11_code', icd11_code)\
                .eq('is_active', True)\
                .maybe_single()\
                .execute()
            
            if result and result.data:
                logger.info(f"[PulseEnergyDecay] ✅ Impact trouvé dans DB pour {condition_name} ({icd11_code})")
                return {
                    'decay_rate': result.data['decay_rate'],
                    'energy_malus': result.data['energy_malus'],
                    'variability': result.data['variability'],
                    'severity': result.data['severity'],
                    'category': result.data['category'],
                    'evidence_level': result.data['evidence_level'],
                    'source': 'database'
                }
            
            # Pas trouvé dans la DB → Smart Fallback avec enrichissement automatique
            logger.info(f"[AI_ENRICHMENT] 🤖 Condition {condition_name} non répertoriée, enrichissement automatique...")
            enrichment_result = await self.condition_enricher.enrich_condition(
                condition_name=condition_name,
                icd11_code=icd11_code,
                category=None
            )
            
            return {
                'decay_rate': enrichment_result['decay_rate'],
                'energy_malus': enrichment_result['energy_malus'],
                'variability': 0.2,
                'severity': enrichment_result['severity'],
                'category': enrichment_result.get('category', 'unknown'),
                'evidence_level': 'ai_generated',
                'source': enrichment_result['source']
            }
            
        except Exception as e:
            logger.error(f"[PulseEnergyDecay] Erreur récupération impact: {e}")
            # Fallback sécurisé
            return {
                'decay_rate': self.DECAY_RATE_NORMAL,
                'energy_malus': 0,
                'variability': 0.2,
                'severity': 'unknown',
                'category': 'unknown',
                'evidence_level': 'error_fallback',
                'source': 'error_fallback'
            }
    
    async def _get_ai_condition_impact(self, condition_name: str, icd11_code: str) -> Dict:
        """
        Utilise GPT-4 pour estimer l'impact énergétique d'une condition non répertoriée.
        Sauvegarde ensuite l'estimation dans la table pour les prochaines fois.
        """
        try:
            from llm_client import LLMClient
            
            llm = LLMClient()
            
            prompt = f"""Tu es un expert médical spécialisé en fatigue et énergie clinique.
            
Condition: {condition_name}
Code ICD-11: {icd11_code}

Estime l'impact de cette condition sur l'énergie quotidienne d'un patient, basé sur:
1. La littérature médicale sur la fatigue associée à cette condition
2. Les études de qualité de vie et d'énergie
3. Le consensus d'experts en médecine de la fatigue

Fournis:
- decay_rate: Taux de décroissance horaire (0.04 = normal, 0.06 = modéré, 0.08 = sévère, 0.11 = très sévère)
- energy_malus: Malus sur le capital de départ E0 (-50 à 0)
- variability: Variabilité jour à jour (0 = stable, 0.5 = variable, 1 = très variable)
- severity: "low", "moderate", "high", ou "severe"
- category: Type de condition (mental, neurological, autoimmune, etc.)
- justification: 2-3 phrases expliquant ton raisonnement

RÉPONDS UNIQUEMENT EN JSON:
{{
    "decay_rate": 0.XX,
    "energy_malus": -XX,
    "variability": 0.XX,
    "severity": "...",
    "category": "...",
    "justification": "..."
}}"""

            response = llm.generate_insight(prompt, temperature=0.3, max_tokens=300)
            
            # Extraire le contenu et parser le JSON
            import json
            content = response.get('content', '{}')
            ai_impact = json.loads(content.strip())
            
            # Ajouter métadonnées
            ai_impact['evidence_level'] = 'ai_generated'
            ai_impact['source'] = f'GPT-4 estimation - {datetime.now(timezone.utc).isoformat()}'
            
            # Sauvegarder dans la DB pour les prochaines fois
            try:
                insert_data = {
                    'icd11_code': icd11_code,
                    'condition_name': condition_name,
                    'decay_rate': ai_impact['decay_rate'],
                    'energy_malus': ai_impact['energy_malus'],
                    'variability': ai_impact['variability'],
                    'severity': ai_impact['severity'],
                    'category': ai_impact['category'],
                    'evidence_level': 'ai_generated',
                    'source': ai_impact['source'],
                    'notes': ai_impact.get('justification', ''),
                    'is_active': True
                }
                
                self.supabase.client.table('condition_energy_impacts')\
                    .insert(insert_data)\
                    .execute()
                
                logger.info(f"[PulseEnergyDecay] 💾 Impact IA sauvegardé pour {condition_name}")
            except Exception as save_error:
                logger.warning(f"[PulseEnergyDecay] Impossible de sauvegarder l'impact IA: {save_error}")
            
            return ai_impact
            
        except Exception as e:
            logger.error(f"[PulseEnergyDecay] Erreur fallback IA: {e}")
            # Fallback conservateur
            return {
                'decay_rate': 0.05,  # Légèrement au-dessus de normal
                'energy_malus': -5,
                'variability': 0.3,
                'severity': 'moderate',
                'category': 'unknown',
                'evidence_level': 'ai_error_fallback',
                'source': 'ai_error_fallback'
            }
    
    async def _save_forecast(self, user_id: str, forecast: PulseEnergyDecayForecast):
        """Sauvegarde la prévision dans la DB"""
        try:
            data = {
                'user_id': user_id,
                'forecast_date': forecast.date,
                'timezone': 'UTC',
                'generated_at': forecast.generated_at,
                'points': forecast.points,
                'windows': forecast.windows,
                'events': forecast.events,
                'notes': forecast.notes,
                'model_version': forecast.model_version,
                'confidence': forecast.confidence,
                'influencers': [inf.dict() for inf in forecast.influencers],
                'calculation_model': forecast.calculation_model
            }
            
            # Upsert (ON CONFLICT DO UPDATE)
            result = self.supabase.client.table('intraday_energy_forecast').upsert(
                data,
                on_conflict='user_id,forecast_date'
            ).execute()
            
            logger.info(f"[PulseEnergyDecay] Forecast saved for user {user_id}")
        except Exception as e:
            logger.error(f"[PulseEnergyDecay] Error saving forecast: {e}")
