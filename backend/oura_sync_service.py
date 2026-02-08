"""
Oura Sync Service - Synchronisation automatique quotidienne
============================================================
Récupère les données Oura (readiness, HRV, sleep) et les injecte dans health_profiles
pour alimenter le modèle Pulse Energy Decay.

Auteur : Claude
Date : 31 Janvier 2026
Version : 1.0
"""

import logging
from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Optional, Tuple
import statistics

from oura_client import get_oura_client
from supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


class OuraSyncService:
    """Service de synchronisation automatique des données Oura"""
    
    def __init__(self, supabase_client: SupabaseClient):
        self.supabase = supabase_client
    
    async def sync_user(self, user_id: str, target_date: Optional[date] = None) -> Dict:
        """
        Synchronise les données Oura d'un utilisateur pour une date donnée
        
        Args:
            user_id: UUID Supabase de l'utilisateur
            target_date: Date à synchroniser (défaut: aujourd'hui)
            
        Returns:
            Dict avec status, data, errors
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            # 1. Récupérer le token Oura de l'utilisateur
            oura_token = await self._get_user_oura_token(user_id)
            
            if not oura_token:
                return {
                    "status": "error",
                    "message": "No Oura token found for user. Connect your Oura account first.",
                    "data": None
                }
            
            # 2. Initialiser le client Oura
            oura = get_oura_client(oura_token)
            
            # 3. Récupérer les données du jour
            date_str = target_date.strftime('%Y-%m-%d')
            
            # Pour /sleep, utiliser une plage de 7 jours (l'API ne fonctionne pas avec un seul jour)
            start_date_for_sleep = (target_date - timedelta(days=3)).strftime('%Y-%m-%d')
            end_date_for_sleep = (target_date + timedelta(days=3)).strftime('%Y-%m-%d')
            
            logger.info(f"[OuraSync] Fetching data for user {user_id}, date {date_str}")
            
            daily_readiness = oura.get_daily_readiness(date_str, date_str)
            daily_sleep = oura.get_daily_sleep(date_str, date_str)
            sleep_sessions = oura.get_sleep_sessions(start_date_for_sleep, end_date_for_sleep)  # ✅ Plage de 7 jours
            daily_activity = oura.get_daily_activity(date_str, date_str)
            
            # 4. Extraire les métriques pertinentes
            current_metrics = {}
            anomalies = []
            
            # Readiness (priorité absolue)
            if daily_readiness and len(daily_readiness) > 0:
                readiness = daily_readiness[0]
                current_metrics['readiness_score'] = readiness.get('score', 0)
                
                contributors = readiness.get('contributors', {})
                current_metrics['temperature_deviation'] = contributors.get('body_temperature', 0)
                current_metrics['activity_balance'] = contributors.get('activity_balance', 0)
                current_metrics['recovery_index'] = contributors.get('recovery_index', 0)
                
                logger.info(f"[OuraSync] Readiness score: {current_metrics['readiness_score']}")
            
            # Sleep
            if daily_sleep and len(daily_sleep) > 0:
                sleep = daily_sleep[0]
                current_metrics['sleep_score'] = sleep.get('score', 0)
                current_metrics['total_sleep_duration'] = sleep.get('total_sleep_duration', 0) / 60  # en minutes
                current_metrics['sleep_efficiency'] = sleep.get('efficiency', 0)
                current_metrics['deep_sleep_duration'] = sleep.get('deep_sleep_duration', 0) / 60
                current_metrics['rem_sleep_duration'] = sleep.get('rem_sleep_duration', 0) / 60
                current_metrics['restless_periods'] = sleep.get('restless_periods', 0)
                
                logger.info(f"[OuraSync] Sleep score: {current_metrics['sleep_score']}")
            
            # HRV depuis les sessions détaillées (sleep_sessions contient average_hrv)
            # Filtrer pour ne garder que la session du jour cible
            if sleep_sessions and len(sleep_sessions) > 0:
                # Trouver la session correspondant au target_date
                target_session = None
                for session in sleep_sessions:
                    session_day = session.get('day')
                    if session_day == date_str:
                        target_session = session
                        break
                
                if target_session:
                    hrv_ms = target_session.get('average_hrv')
                    lowest_hr = target_session.get('lowest_heart_rate')
                    
                    # HRV
                    if hrv_ms is not None:
                        current_metrics['hrv_ms'] = hrv_ms
                        
                        # ✅ Insérer le HRV dans la table biometrics
                        await self._insert_hrv_to_biometrics(user_id, target_date, hrv_ms, target_session)
                        
                        logger.info(f"[OuraSync] HRV: {hrv_ms} ms (from detailed session)")
                    else:
                        logger.warning(f"[OuraSync] No HRV data found in sleep session for {date_str}")
                    
                    # RHR (Resting Heart Rate)
                    if lowest_hr is not None and lowest_hr > 0:
                        current_metrics['resting_hr'] = lowest_hr
                        
                        # ✅ Insérer le RHR dans la table biometrics
                        await self._insert_rhr_to_biometrics(user_id, target_date, lowest_hr, target_session)
                        
                        logger.info(f"[OuraSync] RHR: {lowest_hr} bpm (from detailed session)")
                    else:
                        logger.warning(f"[OuraSync] No RHR data found in sleep session for {date_str}")
                else:
                    logger.warning(f"[OuraSync] No sleep session found for {date_str} in the retrieved range")
            
            # Activity
            if daily_activity and len(daily_activity) > 0:
                activity = daily_activity[0]
                current_metrics['activity_score'] = activity.get('score', 0)
                current_metrics['steps'] = activity.get('steps', 0)
                current_metrics['active_calories'] = activity.get('active_calories', 0)
                current_metrics['total_calories'] = activity.get('total_calories', 0)
                
                logger.info(f"[OuraSync] Activity score: {current_metrics['activity_score']}")
            
            # 5. Détecter les anomalies
            anomalies = await self._detect_anomalies(user_id, current_metrics)
            
            # 6. Mettre à jour health_profiles
            await self._update_health_profile(user_id, target_date, current_metrics, anomalies)
            
            return {
                "status": "success",
                "message": f"Oura data synced successfully for {date_str}",
                "data": {
                    "current_metrics": current_metrics,
                    "anomalies": anomalies,
                    "synced_at": datetime.now(timezone.utc).isoformat()
                }
            }
        
        except Exception as e:
            logger.error(f"[OuraSync] Error syncing user {user_id}: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Sync failed: {str(e)}",
                "data": None
            }
    
    async def sync_all_active_users(self, target_date: Optional[date] = None) -> Dict:
        """
        Synchronise tous les utilisateurs ayant un compte Oura actif
        
        Args:
            target_date: Date à synchroniser (défaut: aujourd'hui)
            
        Returns:
            Dict avec status, success_count, errors
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            # Récupérer tous les utilisateurs avec provider_system='oura' et is_active=true
            result = self.supabase.client.from_('external_identities') \
                .select('supabase_user_id') \
                .eq('provider_system', 'oura') \
                .eq('is_active', True) \
                .execute()
            
            users = result.data if result.data else []
            
            logger.info(f"[OuraSync] Found {len(users)} active Oura users")
            
            success_count = 0
            errors = []
            
            for user in users:
                user_id = user['supabase_user_id']
                
                try:
                    sync_result = await self.sync_user(user_id, target_date)
                    
                    if sync_result['status'] == 'success':
                        success_count += 1
                    else:
                        errors.append({
                            "user_id": user_id,
                            "error": sync_result['message']
                        })
                
                except Exception as e:
                    logger.error(f"[OuraSync] Error syncing user {user_id}: {e}")
                    errors.append({
                        "user_id": user_id,
                        "error": str(e)
                    })
            
            return {
                "status": "success",
                "total_users": len(users),
                "success_count": success_count,
                "error_count": len(errors),
                "errors": errors,
                "synced_at": datetime.now(timezone.utc).isoformat()
            }
        
        except Exception as e:
            logger.error(f"[OuraSync] Error syncing all users: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "total_users": 0,
                "success_count": 0,
                "error_count": 0
            }
    
    async def _get_user_oura_token(self, user_id: str) -> Optional[str]:
        """Récupère le token Oura d'un utilisateur depuis external_identities"""
        try:
            result = self.supabase.client.from_('external_identities') \
                .select('metadata') \
                .eq('supabase_user_id', user_id) \
                .eq('provider_system', 'oura') \
                .eq('is_active', True) \
                .single() \
                .execute()
            
            if result.data:
                # Le token peut être stocké dans metadata.access_token
                metadata = result.data.get('metadata', {})
                return metadata.get('access_token')
            
            return None
        
        except Exception as e:
            logger.error(f"[OuraSync] Error getting Oura token: {e}")
            return None
    
    async def _detect_anomalies(self, user_id: str, current_metrics: Dict) -> List[Dict]:
        """
        Détecte les anomalies biométriques en comparant aux baselines
        
        Returns:
            Liste d'anomalies détectées
        """
        anomalies = []
        
        try:
            # Récupérer les baselines de l'utilisateur
            result = self.supabase.client.from_('user_baselines') \
                .select('baseline_type, baseline_data') \
                .eq('user_id', user_id) \
                .eq('status', 'ok') \
                .execute()
            
            baselines = {b['baseline_type']: b['baseline_data'] for b in result.data} if result.data else {}
            
            # Vérifier HRV
            if 'hrv_ms' in current_metrics and 'hrv' in baselines:
                hrv_value = current_metrics['hrv_ms']
                hrv_baseline = baselines['hrv']
                
                normal_min = hrv_baseline.get('normal_range', {}).get('min', 0)
                normal_max = hrv_baseline.get('normal_range', {}).get('max', 100)
                baseline_mean = hrv_baseline.get('value', 50)
                
                # Calculer Z-Score approximatif
                # Z = (X - μ) / σ
                # σ ≈ (P75 - P25) / 1.35 (approximation IQR)
                details = hrv_baseline.get('details', {})
                iqr = details.get('iqr', 10)
                sigma = iqr / 1.35
                
                z_score = (hrv_value - baseline_mean) / sigma if sigma > 0 else 0
                
                # Anomalie si Z-Score < -1.5 (forte baisse)
                if z_score < -1.5:
                    anomalies.append({
                        "type": "hrv_drop",
                        "severity": "high" if z_score < -2.0 else "medium",
                        "z_score": round(z_score, 2),
                        "detected_at": datetime.now(timezone.utc).isoformat(),
                        "current_value": hrv_value,
                        "baseline_value": baseline_mean
                    })
                    
                    logger.warning(f"[OuraSync] HRV anomaly detected: z_score={z_score:.2f}, value={hrv_value}, baseline={baseline_mean}")
            
            # Vérifier température corporelle
            if 'temperature_deviation' in current_metrics:
                temp_dev = current_metrics['temperature_deviation']
                
                # Oura donne body_temperature en centièmes de degrés (ex: 100 = +1.00°C)
                # Anomalie si > 0.5°C d'écart
                if abs(temp_dev) > 50:
                    anomalies.append({
                        "type": "temp_spike" if temp_dev > 0 else "temp_drop",
                        "severity": "medium",
                        "value": temp_dev / 100,  # Convertir en degrés
                        "detected_at": datetime.now(timezone.utc).isoformat()
                    })
                    
                    logger.warning(f"[OuraSync] Temperature anomaly: {temp_dev/100:.2f}°C")
            
            # Vérifier RHR (Resting Heart Rate)
            if 'resting_hr' in current_metrics:
                rhr = current_metrics['resting_hr']
                
                # Récupérer baseline_resting_hr depuis profiles
                profile_result = self.supabase.client.from_('profiles') \
                    .select('baseline_resting_hr') \
                    .eq('id', user_id) \
                    .single() \
                    .execute()
                
                if profile_result.data and profile_result.data.get('baseline_resting_hr'):
                    baseline_rhr = profile_result.data['baseline_resting_hr']
                    
                    # Anomalie si > 10 bpm d'écart
                    if abs(rhr - baseline_rhr) > 10:
                        anomalies.append({
                            "type": "rhr_elevated" if rhr > baseline_rhr else "rhr_low",
                            "severity": "medium",
                            "current_value": rhr,
                            "baseline_value": baseline_rhr,
                            "detected_at": datetime.now(timezone.utc).isoformat()
                        })
                        
                        logger.warning(f"[OuraSync] RHR anomaly: {rhr} vs baseline {baseline_rhr}")
        
        except Exception as e:
            logger.error(f"[OuraSync] Error detecting anomalies: {e}")
        
        return anomalies
    
    async def _update_health_profile(
        self,
        user_id: str,
        profile_date: date,
        current_metrics: Dict,
        anomalies: List[Dict]
    ):
        """Met à jour ou crée le health_profile du jour"""
        try:
            data = {
                'user_id': user_id,
                'date': profile_date.isoformat(),
                'profile_data': {},  # Requis mais non utilisé
                'current_metrics': current_metrics,
                'anomalies': anomalies
            }
            
            # Upsert (INSERT ON CONFLICT UPDATE)
            result = self.supabase.client.from_('health_profiles').upsert(
                data,
                on_conflict='user_id,date'
            ).execute()
            
            logger.info(f"[OuraSync] health_profile updated for user {user_id}, date {profile_date}")
        
        except Exception as e:
            logger.error(f"[OuraSync] Error updating health_profile: {e}", exc_info=True)
            raise
    
    async def _insert_hrv_to_biometrics(
        self,
        user_id: str,
        recorded_date: date,
        hrv_ms: int,
        session: Dict
    ):
        """
        Insère le HRV dans la table biometrics
        
        Args:
            user_id: UUID de l'utilisateur
            recorded_date: Date d'enregistrement
            hrv_ms: Valeur HRV en millisecondes
            session: Session de sommeil complète (pour metadata)
        """
        try:
            # Utiliser bedtime_end comme timestamp de mesure
            bedtime_end = session.get('bedtime_end')
            if bedtime_end:
                recorded_at = bedtime_end
            else:
                # Fallback: utiliser la date à 12:00 UTC
                recorded_at = f"{recorded_date.isoformat()}T12:00:00Z"
            
            # Préparer les métadonnées
            metadata = {
                'source': 'oura_api',
                'session_id': session.get('id'),
                'bedtime_start': session.get('bedtime_start'),
                'bedtime_end': session.get('bedtime_end'),
                'hrv_samples': len([x for x in session.get('hrv', {}).get('items', []) if x is not None])
            }
            
            # Insérer dans biometrics
            data = {
                'user_id': user_id,
                'metric_type': 'hrv',
                'value': float(hrv_ms),  # ✅ Correction: 'value' au lieu de 'metric_value'
                'recorded_at': recorded_at,
                'source': 'oura_ring',
                'metadata': metadata
            }
            
            # Vérifier si une entrée existe déjà pour ce jour
            existing = self.supabase.client.from_('biometrics') \
                .select('id') \
                .eq('user_id', user_id) \
                .eq('metric_type', 'hrv') \
                .gte('recorded_at', f"{recorded_date.isoformat()}T00:00:00Z") \
                .lte('recorded_at', f"{recorded_date.isoformat()}T23:59:59Z") \
                .execute()
            
            if existing.data and len(existing.data) > 0:
                # Mettre à jour l'entrée existante
                biometric_id = existing.data[0]['id']
                result = self.supabase.client.from_('biometrics') \
                    .update(data) \
                    .eq('id', biometric_id) \
                    .execute()
                logger.info(f"[OuraSync] Updated HRV in biometrics for {recorded_date}: {hrv_ms} ms")
            else:
                # Créer une nouvelle entrée
                result = self.supabase.client.from_('biometrics').insert(data).execute()
                logger.info(f"[OuraSync] Inserted HRV into biometrics for {recorded_date}: {hrv_ms} ms")
        
        except Exception as e:
            logger.error(f"[OuraSync] Error inserting HRV to biometrics: {e}", exc_info=True)
            # Ne pas lever l'exception pour ne pas bloquer le reste de la sync
    
    async def _insert_rhr_to_biometrics(
        self,
        user_id: str,
        recorded_date: date,
        rhr_bpm: int,
        sleep_data: Dict
    ):
        """
        Insère le RHR (Resting Heart Rate) dans la table biometrics
        
        Args:
            user_id: UUID de l'utilisateur
            recorded_date: Date d'enregistrement
            rhr_bpm: Valeur RHR en battements par minute
            sleep_data: Données de sommeil complètes (pour metadata)
        """
        try:
            # Utiliser la date à 06:00 (heure typique du réveil)
            recorded_at = f"{recorded_date.isoformat()}T06:00:00Z"
            
            # Préparer les métadonnées
            metadata = {
                'source': 'oura_api',
                'sleep_id': sleep_data.get('id'),
                'measurement_type': 'lowest_heart_rate'
            }
            
            # Insérer dans biometrics
            data = {
                'user_id': user_id,
                'metric_type': 'hr',  # Utiliser 'hr' comme metric_type
                'value': float(rhr_bpm),
                'recorded_at': recorded_at,
                'source': 'oura_ring',
                'metadata': metadata
            }
            
            # Vérifier si une entrée existe déjà pour ce jour
            existing = self.supabase.client.from_('biometrics') \
                .select('id') \
                .eq('user_id', user_id) \
                .eq('metric_type', 'hr') \
                .gte('recorded_at', f"{recorded_date.isoformat()}T00:00:00Z") \
                .lte('recorded_at', f"{recorded_date.isoformat()}T23:59:59Z") \
                .execute()
            
            if existing.data and len(existing.data) > 0:
                # Mettre à jour l'entrée existante
                biometric_id = existing.data[0]['id']
                result = self.supabase.client.from_('biometrics') \
                    .update(data) \
                    .eq('id', biometric_id) \
                    .execute()
                logger.info(f"[OuraSync] Updated RHR in biometrics for {recorded_date}: {rhr_bpm} bpm")
            else:
                # Créer une nouvelle entrée
                result = self.supabase.client.from_('biometrics').insert(data).execute()
                logger.info(f"[OuraSync] Inserted RHR into biometrics for {recorded_date}: {rhr_bpm} bpm")
        
        except Exception as e:
            logger.error(f"[OuraSync] Error inserting RHR to biometrics: {e}", exc_info=True)
            # Ne pas lever l'exception pour ne pas bloquer le reste de la sync


# ============================================
# Helper Functions
# ============================================

async def sync_user_oura_data(user_id: str, supabase: SupabaseClient, target_date: Optional[date] = None) -> Dict:
    """
    Helper function pour synchroniser un utilisateur
    
    Usage:
        from oura_sync_service import sync_user_oura_data
        result = await sync_user_oura_data("user-uuid", supabase)
    """
    service = OuraSyncService(supabase)
    return await service.sync_user(user_id, target_date)


async def sync_all_oura_users(supabase: SupabaseClient, target_date: Optional[date] = None) -> Dict:
    """
    Helper function pour synchroniser tous les utilisateurs
    
    Usage:
        from oura_sync_service import sync_all_oura_users
        result = await sync_all_oura_users(supabase)
    """
    service = OuraSyncService(supabase)
    return await service.sync_all_active_users(target_date)
