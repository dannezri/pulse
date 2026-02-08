"""
Baseline Calculator - Calcul des baselines personnelles pour chaque utilisateur

Ce module implémente les calculs statistiques pour les différents types de baselines:
- Sommeil (sleep)
- HRV (hrv)
- Sensibilité caféine (caffeine_sensitivity)
- Sensibilité alcool (alcohol_sensitivity)
- Temps de récupération après sport (recovery_time)
- Impact des repas tardifs (late_meal_impact)
- Chronotype (chronotype)

Tous les calculs retournent une structure standardisée (enveloppe JSONB) avec:
- value, unit, normal_range, trend, details
- confidence (calculé de manière cohérente)
- status ('ok', 'insufficient_data', 'error')
- window_start, window_end
"""

import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from scipy.stats import linregress
import logging

logger = logging.getLogger(__name__)


class BaselineCalculator:
    """Calculateur de baselines personnelles"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    def _calculate_confidence(
        self,
        sample_size: int,
        required_samples: int,
        data_variance: float,
        variance_threshold: float,
        excluded_count: int,
        total_count: int,
        window_days: int,
        recommended_window_days: int
    ) -> float:
        """
        Calcul uniforme de la confiance pour toutes les baselines
        
        confidence = sample_factor * data_quality_factor * window_factor
        
        Args:
            sample_size: Nombre d'échantillons utilisés
            required_samples: Nombre minimum requis pour confiance pleine
            data_variance: Variance des données (normalisée)
            variance_threshold: Seuil de variance acceptable
            excluded_count: Nombre d'outliers/échantillons exclus
            total_count: Nombre total d'échantillons avant filtrage
            window_days: Durée de la fenêtre de données en jours
            recommended_window_days: Durée recommandée
        
        Returns:
            Score de confiance entre 0 et 1
        """
        # Facteur échantillon: ratio entre samples obtenus et requis
        sample_factor = min(1.0, sample_size / required_samples if required_samples > 0 else 0)
        
        # Facteur qualité des données
        # - Pénalité si variance élevée (données bruitées)
        variance_penalty = min(1.0, data_variance / variance_threshold if variance_threshold > 0 else 1)
        
        # - Pénalité si beaucoup d'outliers exclus
        exclusion_ratio = excluded_count / total_count if total_count > 0 else 0
        exclusion_penalty = exclusion_ratio * 0.5  # Max 50% de pénalité
        
        data_quality_factor = (1 - variance_penalty) * (1 - exclusion_penalty)
        data_quality_factor = max(0, min(1, data_quality_factor))  # Clamp entre 0 et 1
        
        # Facteur fenêtre temporelle
        window_factor = min(1.0, window_days / recommended_window_days if recommended_window_days > 0 else 1)
        
        # Confiance finale
        confidence = sample_factor * data_quality_factor * window_factor
        
        return round(max(0, min(1, confidence)), 3)  # Clamp et arrondir
    
    def _filter_atypical_nights(self, sleep_data: List[Dict]) -> List[Dict]:
        """
        Filtre les nuits atypiques (maladie, stress, voyage)
        Utilise HRV pour détecter les anomalies
        
        Args:
            sleep_data: Liste des nuits avec HRV
        
        Returns:
            Liste filtrée des nuits normales
        """
        if not sleep_data:
            return []
        
        # Extraire les HRV
        hrv_values = [night.get('hrv', 0) for night in sleep_data if night.get('hrv')]
        
        if len(hrv_values) < 5:
            # Pas assez de données pour filtrer
            return sleep_data
        
        # Calculer médiane et MAD (Median Absolute Deviation)
        median_hrv = np.median(hrv_values)
        mad = np.median(np.abs(hrv_values - median_hrv))
        
        if mad == 0:
            # Pas de dispersion, garder toutes les nuits
            return sleep_data
        
        # Filtrer: garder les nuits avec HRV dans [médiane - 2.5*MAD, médiane + 2.5*MAD]
        filtered = []
        for night in sleep_data:
            hrv = night.get('hrv', 0)
            if hrv == 0 or abs(hrv - median_hrv) <= 2.5 * mad:
                filtered.append(night)
        
        return filtered
    
    def _calculate_trend(self, data_points: List[Dict], metric_key: str) -> float:
        """
        Calcule la tendance (pente) d'une métrique sur une période
        
        Args:
            data_points: Liste de points de données avec 'date' et metric_key
            metric_key: Clé de la métrique à analyser
        
        Returns:
            Pente par semaine (variation moyenne par semaine)
        """
        if len(data_points) < 5:
            return 0.0
        
        # Convertir en timestamps numériques et valeurs
        try:
            timestamps = []
            values = []
            for point in data_points:
                if metric_key in point and point[metric_key] is not None:
                    date = point.get('date')
                    if isinstance(date, str):
                        date = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    elif isinstance(date, datetime):
                        pass
                    else:
                        continue
                    
                    timestamps.append(date.timestamp())
                    values.append(float(point[metric_key]))
            
            if len(timestamps) < 5:
                return 0.0
            
            # Régression linéaire
            slope, _, _, _, _ = linregress(timestamps, values)
            
            # Convertir en variation par semaine
            seconds_per_week = 7 * 24 * 60 * 60
            slope_per_week = slope * seconds_per_week
            
            return round(slope_per_week, 2)
        
        except Exception as e:
            logger.error(f"Error calculating trend: {e}")
            return 0.0
    
    def calculate_sleep_baseline(self, user_id: str) -> Dict[str, Any]:
        """
        Calcule la baseline de sommeil sur 30-60 jours
        
        Méthode:
        1. Récupérer sleep_duration depuis biometrics
        2. Filtrer nuits atypiques (HRV outliers)
        3. Trouver nuits avec meilleure énergie
        4. Calculer médiane + range
        5. Calculer tendance
        6. Calculer confiance avec formule cohérente
        
        Args:
            user_id: UUID de l'utilisateur
        
        Returns:
            Dict avec baseline_data, confidence, sample_size, status, etc.
        """
        try:
            window_end = datetime.now(timezone.utc)
            window_start = window_end - timedelta(days=60)
            
            # Récupérer les données de sommeil
            response = self.supabase.client.table('biometrics') \
                .select('recorded_at, metric_type, value, metadata') \
                .eq('user_id', user_id) \
                .eq('metric_type', 'sleep_duration') \
                .gte('recorded_at', window_start.isoformat()) \
                .lte('recorded_at', window_end.isoformat()) \
                .order('recorded_at', desc=False) \
                .execute()
            
            sleep_data = response.data if response.data else []
            
            # Enrichir avec HRV pour filtrage
            hrv_response = self.supabase.client.table('biometrics') \
                .select('recorded_at, value') \
                .eq('user_id', user_id) \
                .eq('metric_type', 'hrv') \
                .gte('recorded_at', window_start.isoformat()) \
                .lte('recorded_at', window_end.isoformat()) \
                .execute()
            
            # Construire un map par date (extraire la date du timestamp)
            hrv_map = {}
            for item in (hrv_response.data or []):
                date_key = datetime.fromisoformat(item['recorded_at'].replace('Z', '+00:00')).date()
                hrv_map[date_key] = item['value']
            
            # Construire liste de nuits avec HRV
            nights = []
            for item in sleep_data:
                recorded_date = datetime.fromisoformat(item['recorded_at'].replace('Z', '+00:00')).date()
                night = {
                    'date': recorded_date,
                    'duration': item['value'],  # en minutes
                    'hrv': hrv_map.get(recorded_date, 0)
                }
                nights.append(night)
            
            total_nights = len(nights)
            
            # Filtrer nuits atypiques
            filtered_nights = self._filter_atypical_nights(nights)
            sample_size = len(filtered_nights)
            
            if sample_size < 15:
                return {
                    'baseline_data': {
                        'value': 0,
                        'unit': 'minutes',
                        'normal_range': {'min': 0, 'max': 0},
                        'trend': {'slope_per_week': 0, 'direction': 'flat'},
                        'details': {}
                    },
                    'confidence': 0.0,
                    'sample_size': sample_size,
                    'status': 'insufficient_data',
                    'error_message': f'Seulement {sample_size} nuits disponibles (min: 15)',
                    'window_start': window_start.isoformat(),
                    'window_end': window_end.isoformat()
                }
            
            # Calculer médiane et percentiles
            durations = [n['duration'] for n in filtered_nights]
            median_duration = np.median(durations)
            p25 = np.percentile(durations, 25)
            p75 = np.percentile(durations, 75)
            
            # Calculer tendance
            trend_slope = self._calculate_trend(filtered_nights, 'duration')
            trend_direction = 'up' if trend_slope > 1 else ('down' if trend_slope < -1 else 'flat')
            
            # Calculer confiance
            variance = np.std(durations)
            cv = variance / np.mean(durations) if np.mean(durations) > 0 else 1
            
            confidence = self._calculate_confidence(
                sample_size=sample_size,
                required_samples=30,
                data_variance=cv,
                variance_threshold=0.2,  # 20% de coefficient de variation acceptable
                excluded_count=total_nights - sample_size,
                total_count=total_nights,
                window_days=(window_end - window_start).days,
                recommended_window_days=60
            )
            
            return {
                'baseline_data': {
                    'value': round(median_duration),
                    'unit': 'minutes',
                    'normal_range': {
                        'min': round(p25),
                        'max': round(p75)
                    },
                    'trend': {
                        'slope_per_week': trend_slope,
                        'direction': trend_direction
                    },
                    'details': {
                        'median_hours': round(median_duration / 60, 1),
                        'nights_analyzed': sample_size,
                        'nights_excluded': total_nights - sample_size
                    }
                },
                'confidence': confidence,
                'sample_size': sample_size,
                'status': 'ok' if confidence >= 0.3 else 'insufficient_data',
                'error_message': None if confidence >= 0.7 else (
                    'Confiance moyenne' if confidence >= 0.3 else 'Confiance faible'
                ),
                'window_start': window_start.isoformat(),
                'window_end': window_end.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error calculating sleep baseline for user {user_id}: {e}")
            return {
                'baseline_data': {
                    'value': 0,
                    'unit': 'minutes',
                    'normal_range': {'min': 0, 'max': 0},
                    'trend': {'slope_per_week': 0, 'direction': 'flat'},
                    'details': {}
                },
                'confidence': 0.0,
                'sample_size': 0,
                'status': 'error',
                'error_message': str(e),
                'window_start': datetime.now(timezone.utc).isoformat(),
                'window_end': datetime.now(timezone.utc).isoformat()
            }
    
    def calculate_hrv_baseline(self, user_id: str) -> Dict[str, Any]:
        """
        Calcule la baseline HRV avec IQR sur 45 jours
        
        Méthode:
        1. Récupérer HRV depuis biometrics
        2. Calculer médiane et IQR
        3. Calculer tendance
        4. Calculer confiance
        
        Args:
            user_id: UUID de l'utilisateur
        
        Returns:
            Dict avec baseline_data, confidence, sample_size, status, etc.
        """
        try:
            window_end = datetime.now(timezone.utc)
            window_start = window_end - timedelta(days=45)
            
            # Récupérer les données HRV
            response = self.supabase.client.table('biometrics') \
                .select('recorded_at, value') \
                .eq('user_id', user_id) \
                .eq('metric_type', 'hrv') \
                .gte('recorded_at', window_start.isoformat()) \
                .lte('recorded_at', window_end.isoformat()) \
                .order('recorded_at', desc=False) \
                .execute()
            
            # Convertir les données en incluant la date
            hrv_data = []
            for item in (response.data if response.data else []):
                hrv_data.append({
                    'date': datetime.fromisoformat(item['recorded_at'].replace('Z', '+00:00')),
                    'value': item['value']
                })
            sample_size = len(hrv_data)
            
            if sample_size < 30:
                return {
                    'baseline_data': {
                        'value': 0,
                        'unit': 'ms',
                        'normal_range': {'min': 0, 'max': 0},
                        'trend': {'slope_per_week': 0, 'direction': 'flat'},
                        'details': {}
                    },
                    'confidence': 0.0,
                    'sample_size': sample_size,
                    'status': 'insufficient_data',
                    'error_message': f'Seulement {sample_size} jours de HRV (min: 30)',
                    'window_start': window_start.isoformat(),
                    'window_end': window_end.isoformat()
                }
            
            # Extraire valeurs
            hrv_values = [item['value'] for item in hrv_data]
            
            # Calculer médiane et IQR
            median_hrv = np.median(hrv_values)
            p25 = np.percentile(hrv_values, 25)
            p75 = np.percentile(hrv_values, 75)
            iqr = p75 - p25
            
            # Calculer MAD pour la qualité
            mad = np.median(np.abs(hrv_values - median_hrv))
            
            # Calculer tendance
            trend_slope = self._calculate_trend(hrv_data, 'value')
            trend_direction = 'up' if trend_slope > 1 else ('down' if trend_slope < -1 else 'flat')
            
            # Calculer confiance
            mad_ratio = mad / median_hrv if median_hrv > 0 else 1
            
            confidence = self._calculate_confidence(
                sample_size=sample_size,
                required_samples=45,
                data_variance=mad_ratio,
                variance_threshold=0.15,  # 15% MAD/médiane acceptable
                excluded_count=0,  # Pas de filtrage pour HRV baseline
                total_count=sample_size,
                window_days=(window_end - window_start).days,
                recommended_window_days=45
            )
            
            return {
                'baseline_data': {
                    'value': round(median_hrv, 1),
                    'unit': 'ms',
                    'normal_range': {
                        'min': round(p25, 1),
                        'max': round(p75, 1)
                    },
                    'trend': {
                        'slope_per_week': trend_slope,
                        'direction': trend_direction
                    },
                    'details': {
                        'iqr': round(iqr, 1),
                        'mad': round(mad, 1),
                        'percentile_25': round(p25, 1),
                        'percentile_75': round(p75, 1)
                    }
                },
                'confidence': confidence,
                'sample_size': sample_size,
                'status': 'ok' if confidence >= 0.3 else 'insufficient_data',
                'error_message': None if confidence >= 0.7 else (
                    'Confiance moyenne' if confidence >= 0.3 else 'Confiance faible'
                ),
                'window_start': window_start.isoformat(),
                'window_end': window_end.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error calculating HRV baseline for user {user_id}: {e}")
            return {
                'baseline_data': {
                    'value': 0,
                    'unit': 'ms',
                    'normal_range': {'min': 0, 'max': 0},
                    'trend': {'slope_per_week': 0, 'direction': 'flat'},
                    'details': {}
                },
                'confidence': 0.0,
                'sample_size': 0,
                'status': 'error',
                'error_message': str(e),
                'window_start': datetime.now(timezone.utc).isoformat(),
                'window_end': datetime.now(timezone.utc).isoformat()
            }
    
    def calculate_caffeine_sensitivity(self, user_id: str) -> Dict[str, Any]:
        """
        Calcule la sensibilité à la caféine (régression robuste)
        
        Méthode avec garde-fous:
        1. Récupérer événements caféine depuis daily_context
        2. Filtrer événements "propres" (pas café + alcool même jour)
        3. Exclure nuits malades (HRV < baseline - 2*MAD)
        4. Minimum 10 échantillons (15 pour confiance pleine)
        5. Régression linéaire
        6. Confiance pénalisée si variance élevée
        
        Args:
            user_id: UUID de l'utilisateur
        
        Returns:
            Dict avec baseline_data, confidence, sample_size, status, etc.
        """
        try:
            window_end = datetime.now(timezone.utc)
            window_start = window_end - timedelta(days=90)  # 3 mois
            
            # Récupérer événements caféine
            caffeine_response = self.supabase.client.table('daily_context') \
                .select('logged_at, details') \
                .eq('user_id', user_id) \
                .eq('category', 'caffeine') \
                .gte('logged_at', window_start.isoformat()) \
                .lte('logged_at', window_end.isoformat()) \
                .execute()
            
            caffeine_events = caffeine_response.data if caffeine_response.data else []
            
            # Obtenir baseline HRV pour filtrage
            hrv_baseline_data = self.calculate_hrv_baseline(user_id)
            baseline_hrv = hrv_baseline_data['baseline_data']['value']
            mad = hrv_baseline_data['baseline_data']['details'].get('mad', 10)
            
            if baseline_hrv == 0:
                return {
                    'baseline_data': {
                        'value': 0,
                        'unit': 'ms per 100mg',
                        'normal_range': {'min': 0, 'max': 0},
                        'trend': {'slope_per_week': 0, 'direction': 'flat'},
                        'details': {}
                    },
                    'confidence': 0.0,
                    'sample_size': 0,
                    'status': 'insufficient_data',
                    'error_message': 'Baseline HRV non disponible',
                    'window_start': window_start.isoformat(),
                    'window_end': window_end.isoformat()
                }
            
            # Filtrer événements "propres" (pas d'alcool le même jour)
            clean_events = []
            for event in caffeine_events:
                event_date = datetime.fromisoformat(event['logged_at'].replace('Z', '+00:00')).date()
                
                # Vérifier absence d'alcool ce jour
                alcohol_check = self.supabase.client.table('daily_context') \
                    .select('id', count='exact') \
                    .eq('user_id', user_id) \
                    .eq('category', 'alcohol') \
                    .gte('logged_at', event_date.isoformat()) \
                    .lt('logged_at', (event_date + timedelta(days=1)).isoformat()) \
                    .execute()
                
                if alcohol_check.count == 0:
                    clean_events.append(event)
            
            # Construire échantillons avec HRV nuit suivante
            samples = []
            for event in clean_events:
                event_date = datetime.fromisoformat(event['logged_at'].replace('Z', '+00:00')).date()
                next_night = event_date + timedelta(days=1)
                
                # HRV nuit suivante - on cherche les valeurs enregistrées ce jour-là
                next_night_start = datetime.combine(next_night, datetime.min.time()).replace(tzinfo=timezone.utc)
                next_night_end = datetime.combine(next_night, datetime.max.time()).replace(tzinfo=timezone.utc)
                
                hrv_response = self.supabase.client.table('biometrics') \
                    .select('value') \
                    .eq('user_id', user_id) \
                    .eq('metric_type', 'hrv') \
                    .gte('recorded_at', next_night_start.isoformat()) \
                    .lte('recorded_at', next_night_end.isoformat()) \
                    .execute()
                
                if hrv_response.data:
                    hrv = hrv_response.data[0]['value']
                    
                    # Exclure nuits atypiques (maladie)
                    if hrv >= (baseline_hrv - 2 * mad):
                        amount_mg = event['details'].get('amount_mg', 0)
                        samples.append({
                            'caffeine_mg': amount_mg,
                            'hrv': hrv
                        })
            
            sample_size = len(samples)
            total_events = len(caffeine_events)
            
            if sample_size < 10:
                return {
                    'baseline_data': {
                        'value': 0,
                        'unit': 'ms per 100mg',
                        'normal_range': {'min': 0, 'max': 0},
                        'trend': {'slope_per_week': 0, 'direction': 'flat'},
                        'details': {'samples': sample_size, 'clean_samples': len(clean_events)}
                    },
                    'confidence': 0.0,
                    'sample_size': sample_size,
                    'status': 'insufficient_data',
                    'error_message': f'Seulement {sample_size} échantillons propres (min: 10)',
                    'window_start': window_start.isoformat(),
                    'window_end': window_end.isoformat()
                }
            
            # Régression linéaire
            X = np.array([s['caffeine_mg'] for s in samples])
            y = np.array([s['hrv'] for s in samples])
            
            slope, intercept, r_value, p_value, std_err = linregress(X, y)
            r_squared = r_value ** 2
            
            # Impact par 100mg
            impact_per_100mg = slope * 100
            
            # Calculer confiance
            residuals = y - (slope * X + intercept)
            variance = np.var(residuals)
            
            confidence = self._calculate_confidence(
                sample_size=sample_size,
                required_samples=15,
                data_variance=variance,
                variance_threshold=100,  # Variance résiduelle < 100
                excluded_count=total_events - sample_size,
                total_count=total_events,
                window_days=(window_end - window_start).days,
                recommended_window_days=90
            )
            
            # Bonus si R² élevé
            confidence = min(1.0, confidence * (1 + r_squared * 0.1))
            
            return {
                'baseline_data': {
                    'value': round(impact_per_100mg, 2),
                    'unit': 'ms per 100mg',
                    'normal_range': {
                        'min': round(impact_per_100mg - std_err * 100, 2),
                        'max': round(impact_per_100mg + std_err * 100, 2)
                    },
                    'trend': {'slope_per_week': 0, 'direction': 'flat'},
                    'details': {
                        'samples': sample_size,
                        'clean_samples': len(clean_events),
                        'total_events': total_events,
                        'excluded_confounders': total_events - len(clean_events),
                        'regression_r2': round(r_squared, 3),
                        'p_value': round(p_value, 4),
                        'variance': round(variance, 2)
                    }
                },
                'confidence': round(confidence, 3),
                'sample_size': sample_size,
                'status': 'ok' if confidence >= 0.3 else 'insufficient_data',
                'error_message': None if confidence >= 0.7 else (
                    'Confiance moyenne' if confidence >= 0.3 else 'Confiance faible'
                ),
                'window_start': window_start.isoformat(),
                'window_end': window_end.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error calculating caffeine sensitivity for user {user_id}: {e}")
            return {
                'baseline_data': {
                    'value': 0,
                    'unit': 'ms per 100mg',
                    'normal_range': {'min': 0, 'max': 0},
                    'trend': {'slope_per_week': 0, 'direction': 'flat'},
                    'details': {}
                },
                'confidence': 0.0,
                'sample_size': 0,
                'status': 'error',
                'error_message': str(e),
                'window_start': datetime.now(timezone.utc).isoformat(),
                'window_end': datetime.now(timezone.utc).isoformat()
            }
    
    def calculate_alcohol_sensitivity(self, user_id: str) -> Dict[str, Any]:
        """
        Calcule la sensibilité à l'alcool (même logique que caféine)
        
        Retourne impact sur HRV par unité d'alcool
        """
        # Pour l'instant, retourner "insufficient_data" (à implémenter similaire à caféine)
        return {
            'baseline_data': {
                'value': 0,
                'unit': 'ms per unit',
                'normal_range': {'min': 0, 'max': 0},
                'trend': {'slope_per_week': 0, 'direction': 'flat'},
                'details': {}
            },
            'confidence': 0.0,
            'sample_size': 0,
            'status': 'insufficient_data',
            'error_message': 'Pas encore implémenté',
            'window_start': datetime.now(timezone.utc).isoformat(),
            'window_end': datetime.now(timezone.utc).isoformat()
        }
    
    def calculate_recovery_time(self, user_id: str) -> Dict[str, Any]:
        """
        Calcule le temps de récupération après sport
        
        Retourne temps médian pour revenir à baseline HRV
        """
        return {
            'baseline_data': {
                'value': 0,
                'unit': 'hours',
                'normal_range': {'min': 0, 'max': 0},
                'trend': {'slope_per_week': 0, 'direction': 'flat'},
                'details': {}
            },
            'confidence': 0.0,
            'sample_size': 0,
            'status': 'insufficient_data',
            'error_message': 'Pas encore implémenté',
            'window_start': datetime.now(timezone.utc).isoformat(),
            'window_end': datetime.now(timezone.utc).isoformat()
        }
    
    def calculate_late_meal_impact(self, user_id: str) -> Dict[str, Any]:
        """
        Calcule l'impact des repas tardifs sur le sommeil
        
        Retourne delta HRV moyen pour repas < 2h avant coucher
        """
        return {
            'baseline_data': {
                'value': 0,
                'unit': 'ms',
                'normal_range': {'min': 0, 'max': 0},
                'trend': {'slope_per_week': 0, 'direction': 'flat'},
                'details': {}
            },
            'confidence': 0.0,
            'sample_size': 0,
            'status': 'insufficient_data',
            'error_message': 'Pas encore implémenté',
            'window_start': datetime.now(timezone.utc).isoformat(),
            'window_end': datetime.now(timezone.utc).isoformat()
        }
    
    def calculate_chronotype(self, user_id: str) -> Dict[str, Any]:
        """
        Calcule le chronotype (rythme naturel)
        
        Retourne mid_sleep et type (morning/evening)
        """
        return {
            'baseline_data': {
                'value': 0,
                'unit': 'hour',
                'normal_range': {'min': 0, 'max': 0},
                'trend': {'slope_per_week': 0, 'direction': 'flat'},
                'details': {}
            },
            'confidence': 0.0,
            'sample_size': 0,
            'status': 'insufficient_data',
            'error_message': 'Pas encore implémenté',
            'window_start': datetime.now(timezone.utc).isoformat(),
            'window_end': datetime.now(timezone.utc).isoformat()
        }
