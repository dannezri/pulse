"""
Latent State Service - Orchestration des états latents
Gère la récupération des données, calculs et cache des états physiologiques
"""

import logging
import re
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
import json

# Import des calculators
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from latent_states import (
    calculate_recovery_state,
    calculate_sleep_debt_state,
    calculate_overtrain_state,
    calculate_infection_state
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_timestamp_robust(timestamp_str: str) -> datetime:
    """
    Parse un timestamp de manière robuste, gérant les différents formats Supabase.
    
    Formats gérés:
    - ISO 8601 standard: '2026-01-28T12:09:31.900000+00:00'
    - ISO avec une seule décimale: '2026-01-28T12:09:31.9+00:00'
    - ISO avec 'Z': '2026-01-28T12:09:31.900000Z'
    """
    # Remplacer Z par +00:00
    ts = timestamp_str.replace('Z', '+00:00')
    
    # Si le format a moins de 6 décimales, normaliser à 6 décimales
    # Regex: cherche un point suivi de 1-5 chiffres avant le timezone
    match = re.search(r'\.(\d{1,5})([+-]\d{2}:\d{2})', ts)
    if match:
        fractional = match.group(1)
        timezone = match.group(2)
        # Padder les décimales à 6 chiffres
        fractional_padded = fractional.ljust(6, '0')
        # Reconstruire le timestamp
        ts = ts[:match.start()] + f'.{fractional_padded}{timezone}'
    
    return datetime.fromisoformat(ts)


class LatentStateService:
    """
    Service d'orchestration pour calculer les 4 états latents MVP
    """
    
    MODEL_VERSION = 'latent_v1'  # Incrémenter quand poids/formules changent
    
    def __init__(self, supabase_client):
        """
        Initialize service with Supabase client
        
        Args:
            supabase_client: Client Supabase pour accès BDD
        """
        self.supabase = supabase_client
    
    def calculate_all_states(
        self,
        user_id: str,
        target_date: Optional[date] = None,
        force_refresh: bool = False
    ) -> Dict:
        """
        Calculate all 4 MVP latent states for a user.
        
        Args:
            user_id: UUID de l'utilisateur
            target_date: Date cible (défaut: aujourd'hui)
            force_refresh: Forcer recalcul même si cache valide
        
        Returns:
            Dict avec {recovery, sleep_debt, overtrain, infection_like}
        """
        if target_date is None:
            target_date = datetime.utcnow().date()
        
        logger.info(f"Calculating latent states for user {user_id}, date {target_date}")
        
        # 1. Check cache
        if not force_refresh:
            cached = self._get_cached_states(user_id, target_date)
            if cached:
                logger.info(f"Cache hit for user {user_id}, date {target_date}")
                return cached
        
        # 2. Fetch biometrics (3d, 7d, 28d windows)
        biometrics_data = self._fetch_biometrics(user_id, target_date)
        
        # 3. Fetch baselines
        baselines = self._fetch_baselines(user_id)
        
        # 4. Fetch previous day's smoothed_scores for EMA
        yesterday = target_date - timedelta(days=1)
        previous_states = self._get_cached_states(user_id, yesterday)
        
        # 5. Calculate states (ordre important pour confounding)
        
        # a. Recovery (independent)
        recovery = self._calculate_recovery(
            biometrics_data,
            baselines,
            previous_states.get('recovery', {}).get('smoothed_score') if previous_states else None
        )
        
        # b. Sleep debt (independent)
        sleep_debt = self._calculate_sleep_debt(
            biometrics_data,
            baselines,
            previous_states
        )
        
        # c. Overtrain (independent)
        overtrain = self._calculate_overtrain(
            biometrics_data,
            baselines,
            previous_states.get('overtrain', {}).get('smoothed_score') if previous_states else None
        )
        
        # d. Infection-like (depends on sleep_debt and overtrain)
        infection = self._calculate_infection(
            biometrics_data,
            baselines,
            sleep_debt_hours=sleep_debt.get('debt_hours', 0.0),
            overtrain_score=overtrain.get('smoothed_score', 0.0),
            previous_states=previous_states,
            target_date=target_date
        )
        
        # 6. Save to daily_state
        self._save_states(user_id, target_date, {
            'recovery': recovery,
            'sleep_debt': sleep_debt,
            'overtrain': overtrain,
            'infection_like': infection
        })
        
        # 7. Calculate and save daily_energy (agrégation des états latents)
        self._calculate_and_save_daily_energy(user_id, target_date, {
            'recovery': recovery,
            'sleep_debt': sleep_debt,
            'overtrain': overtrain,
            'infection_like': infection
        })
        
        # 8. Return results
        return {
            'recovery': recovery,
            'sleep_debt': sleep_debt,
            'overtrain': overtrain,
            'infection_like': infection
        }
    
    def _get_cached_states(self, user_id: str, target_date: date) -> Optional[Dict]:
        """
        Récupère états du cache (daily_state table)
        
        Returns:
            Dict avec les 4 états ou None si pas trouvé/invalide
        """
        try:
            response = self.supabase.client.table("daily_state").select(
                "state_type, score, smoothed_score, confidence, top_factors, metadata, model_version"
            ).eq("user_id", user_id).eq("state_date", target_date.isoformat()).execute()
            
            if not response.data or len(response.data) == 0:
                return None
            
            # Vérifier model_version
            if any(s['model_version'] != self.MODEL_VERSION for s in response.data):
                logger.info(f"Cache invalidated: model_version mismatch")
                return None
            
            # Reconstruire dict par state_type
            states = {}
            for row in response.data:
                state_type = row['state_type']
                states[state_type] = {
                    'state': state_type,
                    'score': row['score'],
                    'smoothed_score': row['smoothed_score'],
                    'confidence': row['confidence'],
                    'top_factors': row['top_factors'],
                    'metadata': row['metadata']
                }
                
                # Ajouter champs spécifiques selon type
                if state_type == 'sleep_debt':
                    states[state_type]['debt_hours'] = row['metadata'].get('ema', {}).get('current_debt', 0.0)
                elif state_type == 'overtrain':
                    states[state_type]['acwr'] = row['metadata'].get('load_windows', {}).get('acwr', 0.0)
                    states[state_type]['interpretation'] = self._interpret_overtrain(row['smoothed_score'])
                elif state_type == 'recovery':
                    states[state_type]['interpretation'] = self._interpret_recovery(row['smoothed_score'])
                elif state_type == 'infection_like':
                    states[state_type]['signals_triggered'] = row['metadata'].get('guard_rails', {}).get('signals_over_threshold', 0)
                    states[state_type]['persistent'] = row['metadata'].get('persistence', {}).get('days', 0) >= 2
            
            return states if len(states) == 4 else None
        
        except Exception as e:
            logger.error(f"Error fetching cached states: {e}")
            return None
    
    def _fetch_biometrics(self, user_id: str, target_date: date) -> Dict:
        """
        Fetch biometrics for required time windows (3d, 7d, 28d)
        
        Returns:
            Dict avec métriques organisées par période
        """
        logger.info(f"Fetching biometrics for user {user_id}")
        
        # Dates de fenêtres
        date_3d_ago = target_date - timedelta(days=3)
        date_7d_ago = target_date - timedelta(days=7)
        date_28d_ago = target_date - timedelta(days=28)
        
        # Fetch toutes les biométries des 28 derniers jours
        response = self.supabase.client.table("biometrics").select(
            "metric_type, value, recorded_at"
        ).eq("user_id", user_id).gte(
            "recorded_at", date_28d_ago.isoformat()
        ).order("recorded_at", desc=False).execute()
        
        biometrics = response.data if response.data else []
        logger.info(f"Fetched {len(biometrics)} biometric records")
        
        # Organiser par métrique
        data = {
            'hrv_night_recent': [],
            'rhr_night_recent': [],
            'sleep_duration_7d': [],
            'sleep_fragmentation_recent': [],
            'steps_28d': [],
            'active_minutes_28d': []
        }
        
        for bio in biometrics:
            metric_type = bio['metric_type']
            value = bio['value']
            recorded_at = parse_timestamp_robust(bio['recorded_at'])
            
            # HRV nocturne (3 derniers jours)
            if metric_type == 'hrv' and recorded_at.date() >= date_3d_ago:
                data['hrv_night_recent'].append(value)
            
            # RHR nocturne (3 derniers jours)
            if metric_type in ['hr', 'resting_hr'] and recorded_at.date() >= date_3d_ago:
                data['rhr_night_recent'].append(value)
            
            # Sleep duration (7 derniers jours)
            if metric_type == 'sleep_duration' and recorded_at.date() >= date_7d_ago:
                data['sleep_duration_7d'].append(value)
            
            # Sleep fragmentation (3 derniers jours)
            if metric_type in ['sleep_quality', 'sleep_fragmentation'] and recorded_at.date() >= date_3d_ago:
                # Si sleep_quality, inverser (100 - quality = fragmentation)
                frag = 100 - value if metric_type == 'sleep_quality' else value
                data['sleep_fragmentation_recent'].append(frag)
            
            # Steps (28 derniers jours)
            if metric_type == 'steps':
                data['steps_28d'].append({'date': recorded_at.date(), 'value': value})
            
            # Active minutes (28 derniers jours)
            if metric_type == 'active_minutes':
                data['active_minutes_28d'].append({'date': recorded_at.date(), 'value': value})
        
        # Calculer moyennes/dernières valeurs
        result = {
            'hrv_night': data['hrv_night_recent'][-1] if data['hrv_night_recent'] else None,
            'rhr_night': min(data['rhr_night_recent']) if data['rhr_night_recent'] else None,  # Min = repos
            'hrv_3d_avg': sum(data['hrv_night_recent']) / len(data['hrv_night_recent']) if data['hrv_night_recent'] else None,
            'rhr_3d_avg': sum(data['rhr_night_recent']) / len(data['rhr_night_recent']) if data['rhr_night_recent'] else None,
            'sleep_duration_7d': data['sleep_duration_7d'],
            'sleep_fragmentation': data['sleep_fragmentation_recent'][-1] if data['sleep_fragmentation_recent'] else None,
            'steps_28d': data['steps_28d'],
            'active_minutes_28d': data['active_minutes_28d']
        }
        
        logger.info(f"Processed biometrics: HRV={result['hrv_night']}, RHR={result['rhr_night']}, Sleep duration={len(result['sleep_duration_7d'])} days")
        
        return result
    
    def _fetch_baselines(self, user_id: str) -> Dict:
        """
        Fetch user baselines from user_baselines table
        
        Returns:
            Dict avec baselines (median, IQR pour chaque métrique)
        """
        try:
            response = self.supabase.client.table("user_baselines").select(
                "baseline_type, baseline_data"
            ).eq("user_id", user_id).execute()
            
            baselines = {}
            if response.data:
                for row in response.data:
                    baseline_type = row['baseline_type']
                    baseline_data = row['baseline_data']
                    
                    # Extraire median et IQR
                    if baseline_type == 'hrv':
                        baselines['baseline_hrv_median'] = baseline_data.get('median', 50.0)
                        baselines['baseline_hrv_iqr'] = baseline_data.get('iqr', 15.0)
                    elif baseline_type == 'sleep':
                        baselines['baseline_sleep_median'] = baseline_data.get('median', 7.5)
                        baselines['baseline_sleep_iqr'] = baseline_data.get('iqr', 1.0)
                        baselines['baseline_sleep_need'] = baseline_data.get('optimal', 8.0)
            
            # Fallbacks pour profil si pas dans user_baselines
            if 'baseline_hrv_median' not in baselines:
                profile_response = self.supabase.client.table("profiles").select(
                    "baseline_hrv, baseline_resting_hr"
                ).eq("id", user_id).single().execute()
                
                if profile_response.data:
                    baselines['baseline_hrv_median'] = profile_response.data.get('baseline_hrv', 50.0)
                    baselines['baseline_rhr_median'] = profile_response.data.get('baseline_resting_hr', 60.0)
            
            # Defaults
            baselines.setdefault('baseline_hrv_median', 50.0)
            baselines.setdefault('baseline_hrv_iqr', 15.0)
            baselines.setdefault('baseline_rhr_median', 60.0)
            baselines.setdefault('baseline_rhr_iqr', 5.0)
            baselines.setdefault('baseline_sleep_median', 7.5)
            baselines.setdefault('baseline_sleep_iqr', 1.0)
            baselines.setdefault('baseline_sleep_need', 8.0)
            baselines.setdefault('baseline_fragmentation_median', 20.0)
            baselines.setdefault('baseline_fragmentation_iqr', 10.0)
            
            logger.info(f"Fetched baselines: HRV={baselines['baseline_hrv_median']}, RHR={baselines['baseline_rhr_median']}")
            
            return baselines
        
        except Exception as e:
            logger.error(f"Error fetching baselines: {e}")
            # Return defaults
            return {
                'baseline_hrv_median': 50.0,
                'baseline_hrv_iqr': 15.0,
                'baseline_rhr_median': 60.0,
                'baseline_rhr_iqr': 5.0,
                'baseline_sleep_median': 7.5,
                'baseline_sleep_iqr': 1.0,
                'baseline_sleep_need': 8.0,
                'baseline_fragmentation_median': 20.0,
                'baseline_fragmentation_iqr': 10.0
            }
    
    def _calculate_training_load(self, steps: Optional[float], active_minutes: Optional[float]) -> float:
        """
        Calculate training load with cap to prevent outliers
        
        Args:
            steps: Steps count
            active_minutes: Active minutes
        
        Returns:
            Training load (capped)
        """
        if active_minutes is not None and active_minutes > 0:
            # Priorité aux active_minutes si disponible
            load = min(15.0, active_minutes / 10.0)
            logger.debug(f"Load from active_minutes: {load:.1f} (raw: {active_minutes})")
            return load
        elif steps is not None and steps > 0:
            # Fallback sur steps
            load = min(10.0, steps / 1000.0)
            logger.debug(f"Load from steps: {load:.1f} (raw: {steps})")
            return load
        else:
            return 0.0
    
    def _calculate_recovery(self, biometrics_data: Dict, baselines: Dict, previous_smoothed: Optional[float]) -> Dict:
        """Calculate recovery state"""
        return calculate_recovery_state(
            hrv_night=biometrics_data.get('hrv_night'),
            rhr_night=biometrics_data.get('rhr_night'),
            sleep_duration=biometrics_data.get('sleep_duration_7d', [None])[-1] if biometrics_data.get('sleep_duration_7d') else None,
            sleep_fragmentation=biometrics_data.get('sleep_fragmentation'),
            baselines=baselines,
            previous_smoothed=previous_smoothed
        )
    
    def _calculate_sleep_debt(self, biometrics_data: Dict, baselines: Dict, previous_states: Optional[Dict]) -> Dict:
        """Calculate sleep debt state"""
        previous_debt = 0.0
        previous_smoothed = None
        
        if previous_states and 'sleep_debt' in previous_states:
            previous_debt = previous_states['sleep_debt'].get('debt_hours', 0.0)
            previous_smoothed = previous_states['sleep_debt'].get('smoothed_score')
        
        return calculate_sleep_debt_state(
            sleep_history_7d=biometrics_data.get('sleep_duration_7d', []),
            baseline_sleep_need=baselines.get('baseline_sleep_need', 8.0),
            previous_debt=previous_debt,
            previous_smoothed=previous_smoothed
        )
    
    def _calculate_overtrain(self, biometrics_data: Dict, baselines: Dict, previous_smoothed: Optional[float]) -> Dict:
        """Calculate overtrain state"""
        # Calculer les loads depuis steps/active_minutes
        steps_data = biometrics_data.get('steps_28d', [])
        active_data = biometrics_data.get('active_minutes_28d', [])
        
        # Grouper par jour et calculer load
        daily_loads = {}
        
        for entry in steps_data:
            date_key = entry['date']
            if date_key not in daily_loads:
                daily_loads[date_key] = {'steps': entry['value'], 'active_minutes': None}
            else:
                daily_loads[date_key]['steps'] = entry['value']
        
        for entry in active_data:
            date_key = entry['date']
            if date_key not in daily_loads:
                daily_loads[date_key] = {'steps': None, 'active_minutes': entry['value']}
            else:
                daily_loads[date_key]['active_minutes'] = entry['value']
        
        # Calculer loads avec cap
        loads_with_dates = []
        for date_key, values in daily_loads.items():
            load = self._calculate_training_load(values['steps'], values['active_minutes'])
            loads_with_dates.append((date_key, load))
        
        # Trier par date
        loads_with_dates.sort(key=lambda x: x[0])
        all_loads = [load for _, load in loads_with_dates]
        
        # Fenêtres 7d et 28d
        load_7d = all_loads[-7:] if len(all_loads) >= 7 else all_loads
        load_28d = all_loads
        
        return calculate_overtrain_state(
            activity_load_7d=load_7d,
            activity_load_28d=load_28d,
            hrv_3d_avg=biometrics_data.get('hrv_3d_avg'),
            rhr_3d_avg=biometrics_data.get('rhr_3d_avg'),
            baselines=baselines,
            previous_smoothed=previous_smoothed
        )
    
    def _calculate_infection(
        self,
        biometrics_data: Dict,
        baselines: Dict,
        sleep_debt_hours: float,
        overtrain_score: float,
        previous_states: Optional[Dict],
        target_date: date
    ) -> Dict:
        """Calculate infection-like state"""
        # Check persistence (2 jours)
        persistent_2_days = False
        if previous_states and 'infection_like' in previous_states:
            prev_score = previous_states['infection_like'].get('smoothed_score', 0.0)
            # Si score précédent élevé, considérer persistant
            if prev_score > 0.5:
                persistent_2_days = True
        
        previous_smoothed = previous_states.get('infection_like', {}).get('smoothed_score') if previous_states else None
        
        return calculate_infection_state(
            rhr_night=biometrics_data.get('rhr_night'),
            hrv_night=biometrics_data.get('hrv_night'),
            sleep_fragmentation=biometrics_data.get('sleep_fragmentation'),
            baselines=baselines,
            persistent_2_days=persistent_2_days,
            sleep_debt_hours=sleep_debt_hours,
            overtrain_score=overtrain_score,
            previous_smoothed=previous_smoothed
        )
    
    def _save_states(self, user_id: str, target_date: date, states: Dict):
        """
        Save all states to daily_state table
        
        Args:
            user_id: User UUID
            target_date: Date
            states: Dict avec {recovery, sleep_debt, overtrain, infection_like}
        """
        try:
            for state_type, state_data in states.items():
                # Préparer l'enregistrement
                record = {
                    'user_id': user_id,
                    'state_type': state_type,
                    'state_date': target_date.isoformat(),
                    'score': state_data['score'],
                    'smoothed_score': state_data.get('smoothed_score'),
                    'confidence': state_data['confidence'],
                    'top_factors': json.dumps(state_data['top_factors']) if isinstance(state_data['top_factors'], list) else state_data['top_factors'],
                    'metadata': json.dumps(state_data['metadata']) if isinstance(state_data['metadata'], dict) else state_data['metadata'],
                    'model_version': self.MODEL_VERSION,
                    'calculated_at': datetime.utcnow().isoformat()
                }
                
                # Upsert (insert or update)
                self.supabase.client.table("daily_state").upsert(
                    record,
                    on_conflict='user_id,state_type,state_date'
                ).execute()
            
            logger.info(f"Saved {len(states)} states for user {user_id}, date {target_date}")
        
        except Exception as e:
            logger.error(f"Error saving states: {e}")
            raise
    
    def _calculate_and_save_daily_energy(self, user_id: str, target_date: date, states: Dict):
        """
        Calcule et sauvegarde le daily_energy à partir des états latents
        
        Args:
            user_id: User UUID
            target_date: Date
            states: Dict avec {recovery, sleep_debt, overtrain, infection_like}
        """
        try:
            # Import ici pour éviter circular import
            from daily_energy_engine import compute_daily_energy, save_daily_energy
            
            # Calculer le daily energy (avec enrichissement agenda dans risk_windows)
            energy_data = compute_daily_energy(
                states,
                user_id=user_id,
                target_date=target_date.isoformat()
            )
            
            # Sauvegarder en DB
            save_daily_energy(user_id, target_date.isoformat(), energy_data)
            
            logger.info(f"Calculated and saved daily_energy for user {user_id}, date {target_date}: score={energy_data['energy_score']:.2f}, label={energy_data['label']}")
        
        except Exception as e:
            logger.error(f"Error calculating/saving daily_energy: {e}")
            # Ne pas raise pour ne pas bloquer le calcul des états latents
            # Le daily_energy peut être recalculé plus tard si nécessaire
    
    @staticmethod
    def _interpret_recovery(score: float) -> str:
        """Interpret recovery score"""
        if score >= 0.75:
            return "bonne"
        elif score >= 0.50:
            return "moyenne"
        else:
            return "insuffisante"
    
    @staticmethod
    def _interpret_overtrain(score: float) -> str:
        """Interpret overtrain score"""
        if score >= 0.7:
            return "surcharge"
        elif score >= 0.4:
            return "surveiller"
        else:
            return "ok"
