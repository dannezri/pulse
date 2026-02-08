"""
Energy Profile Learning - Système d'apprentissage de patterns personnels

Analyse l'historique d'un utilisateur (60-90 jours) pour identifier ses traits énergétiques uniques:
- Sommeil optimal personnel
- Timing caféine optimal
- Impact sport tardif
- Sensibilités individuelles

Exécution: Cron hebdomadaire ou mensuel
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy import stats
from supabase import create_client, Client

# Initialize Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)

# Minimum data points requis pour apprendre un pattern
MIN_SAMPLE_SIZE = 15

# Seuil de confiance minimum pour stocker un trait
MIN_CONFIDENCE = 0.60


def get_sleep_biometrics(user_id: str, days: int = 90) -> List[Dict]:
    """Récupère les données de sommeil sur N jours"""
    start_date = (datetime.now() - timedelta(days=days)).date()
    
    response = supabase.table('biometrics') \
        .select('date, value, metadata') \
        .eq('user_id', user_id) \
        .eq('metric_type', 'sleep_duration') \
        .gte('date', str(start_date)) \
        .execute()
    
    return response.data if response.data else []


def get_recovery_scores(user_id: str, days: int = 90) -> List[Dict]:
    """Récupère les scores de récupération sur N jours"""
    start_date = (datetime.now() - timedelta(days=days)).date()
    
    response = supabase.table('daily_state') \
        .select('state_date, smoothed_score, metadata') \
        .eq('user_id', user_id) \
        .eq('state_type', 'recovery') \
        .gte('state_date', str(start_date)) \
        .execute()
    
    return response.data if response.data else []


def get_hrv_data(user_id: str, days: int = 90) -> List[Dict]:
    """Récupère les données HRV sur N jours"""
    start_date = (datetime.now() - timedelta(days=days)).date()
    
    response = supabase.table('biometrics') \
        .select('date, value, timestamp, metadata') \
        .eq('user_id', user_id) \
        .eq('metric_type', 'hrv') \
        .gte('date', str(start_date)) \
        .execute()
    
    return response.data if response.data else []


def analyze_optimal_sleep_duration(user_id: str) -> Optional[Dict]:
    """
    Détecte la durée de sommeil optimale pour cet utilisateur
    Corrèle durée sommeil avec recovery/HRV
    """
    sleep_data = get_sleep_biometrics(user_id, 90)
    recovery_data = get_recovery_scores(user_id, 90)
    
    if len(sleep_data) < MIN_SAMPLE_SIZE or len(recovery_data) < MIN_SAMPLE_SIZE:
        return None
    
    # Joindre sommeil + recovery par date
    sleep_dict = {s['date']: s['value'] / 3600 for s in sleep_data}  # Convertir en heures
    recovery_dict = {r['state_date']: r['smoothed_score'] * 100 for r in recovery_data}
    
    paired_data = []
    for date in sleep_dict:
        if date in recovery_dict:
            paired_data.append({
                'sleep_hours': sleep_dict[date],
                'recovery': recovery_dict[date],
            })
    
    if len(paired_data) < MIN_SAMPLE_SIZE:
        return None
    
    # Grouper par tranches de sommeil (30 min)
    sleep_bins = {}
    for entry in paired_data:
        bin_key = round(entry['sleep_hours'] * 2) / 2  # Arrondir à 30 min près
        if bin_key not in sleep_bins:
            sleep_bins[bin_key] = []
        sleep_bins[bin_key].append(entry['recovery'])
    
    # Trouver la durée optimale (meilleure recovery moyenne)
    best_duration = None
    best_recovery = 0
    
    for duration, recoveries in sleep_bins.items():
        if len(recoveries) >= 3:  # Au moins 3 occurrences
            avg_recovery = np.mean(recoveries)
            if avg_recovery > best_recovery:
                best_recovery = avg_recovery
                best_duration = duration
    
    if best_duration is None:
        return None
    
    # Calculer confiance (basé sur sample size et écart avec autres durées)
    sample_size = len(sleep_bins[best_duration])
    other_recoveries = [r for d, rs in sleep_bins.items() if d != best_duration for r in rs]
    
    if len(other_recoveries) == 0:
        return None
    
    avg_other = np.mean(other_recoveries)
    improvement = ((best_recovery - avg_other) / avg_other) * 100
    
    confidence = min(0.95, 0.60 + (sample_size / 50) * 0.20 + (improvement / 100))
    
    if confidence < MIN_CONFIDENCE:
        return None
    
    # Formatter les heures/minutes
    hours = int(best_duration)
    minutes = int((best_duration - hours) * 60)
    
    return {
        'trait_type': 'optimal_sleep_duration',
        'category': 'sleep',
        'title': f'Sommeil optimal: {hours}h{minutes:02d}',
        'description': f'Tu récupères mieux avec {hours}h{minutes:02d} de sommeil (récupération moyenne: {best_recovery:.0f}% vs {avg_other:.0f}% pour autres durées)',
        'value_numeric': best_duration,
        'value_text': f'{hours}h{minutes:02d}',
        'confidence': confidence,
        'support_data': {
            'sample_size': sample_size,
            'average_recovery': round(best_recovery, 1),
            'other_average': round(avg_other, 1),
            'improvement': f'+{improvement:.0f}%',
            'analyzed_days': len(paired_data),
        },
        'data_points_count': sample_size,
    }


def analyze_caffeine_cutoff(user_id: str) -> Optional[Dict]:
    """
    Détecte l'heure limite de caféine pour préserver le sommeil
    Nécessite tracking caféine (TODO: implémenter si données disponibles)
    """
    # TODO: Implémenter quand tracking caféine sera disponible
    # Pour l'instant, retourner None
    return None


def analyze_late_exercise_impact(user_id: str) -> Optional[Dict]:
    """
    Analyse l'impact du sport tardif (>19h) sur HRV/sommeil
    """
    # Récupérer biometrics activité + HRV
    start_date = (datetime.now() - timedelta(days=90)).date()
    
    # Activité
    activity_response = supabase.table('biometrics') \
        .select('date, timestamp, value, metadata') \
        .eq('user_id', user_id) \
        .eq('metric_type', 'active_calories') \
        .gte('date', str(start_date)) \
        .execute()
    
    activity_data = activity_response.data if activity_response.data else []
    
    # HRV du jour suivant
    hrv_data = get_hrv_data(user_id, 90)
    
    if len(activity_data) < MIN_SAMPLE_SIZE or len(hrv_data) < MIN_SAMPLE_SIZE:
        return None
    
    # Identifier les jours avec sport tardif (>19h)
    late_exercise_days = set()
    for activity in activity_data:
        if activity.get('timestamp'):
            timestamp = datetime.fromisoformat(activity['timestamp'].replace('Z', '+00:00'))
            if timestamp.hour >= 19 and activity['value'] > 300:  # Sport intense après 19h
                late_exercise_days.add(activity['date'])
    
    if len(late_exercise_days) < 5:  # Besoin d'au moins 5 jours de sport tardif
        return None
    
    # Comparer HRV les jours suivant sport tardif vs autres jours
    hrv_by_date = {}
    for hrv in hrv_data:
        date = datetime.fromisoformat(hrv['date']).date()
        if date not in hrv_by_date:
            hrv_by_date[date] = []
        hrv_by_date[date].append(hrv['value'])
    
    hrv_after_late_exercise = []
    hrv_normal_days = []
    
    for date_str in late_exercise_days:
        next_day = datetime.fromisoformat(date_str).date() + timedelta(days=1)
        if next_day in hrv_by_date:
            hrv_after_late_exercise.extend(hrv_by_date[next_day])
    
    all_dates = set(hrv_by_date.keys())
    late_exercise_dates = {datetime.fromisoformat(d).date() + timedelta(days=1) for d in late_exercise_days}
    normal_dates = all_dates - late_exercise_dates
    
    for date in normal_dates:
        hrv_normal_days.extend(hrv_by_date[date])
    
    if len(hrv_after_late_exercise) < 5 or len(hrv_normal_days) < 10:
        return None
    
    avg_hrv_late = np.mean(hrv_after_late_exercise)
    avg_hrv_normal = np.mean(hrv_normal_days)
    
    impact_percent = ((avg_hrv_late - avg_hrv_normal) / avg_hrv_normal) * 100
    
    # Seulement signaler si impact négatif significatif
    if impact_percent > -5:  # Pas d'impact notable
        return None
    
    # Test statistique
    t_stat, p_value = stats.ttest_ind(hrv_after_late_exercise, hrv_normal_days)
    
    confidence = min(0.95, 0.65 + (len(hrv_after_late_exercise) / 30) * 0.20)
    if p_value > 0.05:  # Pas significatif statistiquement
        confidence *= 0.7
    
    if confidence < MIN_CONFIDENCE:
        return None
    
    return {
        'trait_type': 'late_exercise_impact',
        'category': 'exercise',
        'title': 'Sport tardif réduit HRV',
        'description': f'Le sport après 19h réduit ta HRV de {abs(impact_percent):.0f}% le lendemain ({avg_hrv_late:.0f}ms vs {avg_hrv_normal:.0f}ms)',
        'value_numeric': impact_percent,
        'value_text': f'{impact_percent:+.0f}%',
        'confidence': confidence,
        'support_data': {
            'sample_size': len(hrv_after_late_exercise),
            'late_exercise_days': len(late_exercise_days),
            'avg_hrv_late': round(avg_hrv_late, 1),
            'avg_hrv_normal': round(avg_hrv_normal, 1),
            'p_value': round(p_value, 3),
        },
        'data_points_count': len(hrv_after_late_exercise),
    }


def analyze_protein_requirement(user_id: str) -> Optional[Dict]:
    """
    Identifie l'apport protéique optimal pour la récupération
    """
    # Récupérer food_logs + recovery
    start_date = (datetime.now() - timedelta(days=90)).date()
    
    food_response = supabase.table('food_logs') \
        .select('log_date, total_protein') \
        .eq('user_id', user_id) \
        .gte('log_date', str(start_date)) \
        .execute()
    
    food_data = food_response.data if food_response.data else []
    recovery_data = get_recovery_scores(user_id, 90)
    
    if len(food_data) < MIN_SAMPLE_SIZE or len(recovery_data) < MIN_SAMPLE_SIZE:
        return None
    
    # Joindre protéines + recovery
    protein_dict = {f['log_date']: f['total_protein'] for f in food_data if f.get('total_protein')}
    recovery_dict = {r['state_date']: r['smoothed_score'] * 100 for r in recovery_data}
    
    paired_data = []
    for date in protein_dict:
        next_day = (datetime.fromisoformat(date).date() + timedelta(days=1)).isoformat()
        if next_day in recovery_dict:
            paired_data.append({
                'protein': protein_dict[date],
                'recovery': recovery_dict[next_day],
            })
    
    if len(paired_data) < MIN_SAMPLE_SIZE:
        return None
    
    # Grouper par tranches de protéines (20g)
    protein_bins = {}
    for entry in paired_data:
        bin_key = (entry['protein'] // 20) * 20  # Groupes de 20g
        if bin_key not in protein_bins:
            protein_bins[bin_key] = []
        protein_bins[bin_key].append(entry['recovery'])
    
    # Trouver l'apport optimal
    best_protein = None
    best_recovery = 0
    
    for protein, recoveries in protein_bins.items():
        if len(recoveries) >= 3:
            avg_recovery = np.mean(recoveries)
            if avg_recovery > best_recovery and protein >= 60:  # Minimum 60g
                best_recovery = avg_recovery
                best_protein = protein
    
    if best_protein is None:
        return None
    
    # Calculer confiance
    sample_size = len(protein_bins[best_protein])
    other_recoveries = [r for p, rs in protein_bins.items() if p != best_protein for r in rs]
    
    if len(other_recoveries) == 0:
        return None
    
    avg_other = np.mean(other_recoveries)
    improvement = ((best_recovery - avg_other) / avg_other) * 100
    
    confidence = min(0.90, 0.60 + (sample_size / 40) * 0.20 + (improvement / 80))
    
    if confidence < MIN_CONFIDENCE:
        return None
    
    return {
        'trait_type': 'protein_requirement',
        'category': 'nutrition',
        'title': f'Protéines optimales: {best_protein}g+',
        'description': f'Ta récupération est meilleure avec au moins {best_protein}g de protéines par jour ({best_recovery:.0f}% vs {avg_other:.0f}% avec moins)',
        'value_numeric': best_protein,
        'value_text': f'{best_protein}g+',
        'confidence': confidence,
        'support_data': {
            'sample_size': sample_size,
            'average_recovery': round(best_recovery, 1),
            'other_average': round(avg_other, 1),
            'improvement': f'+{improvement:.0f}%',
        },
        'data_points_count': sample_size,
    }


def save_energy_profile_trait(user_id: str, trait: Dict) -> bool:
    """Sauvegarde ou met à jour un trait dans user_energy_profile"""
    try:
        # Vérifier si le trait existe déjà
        existing = supabase.table('user_energy_profile') \
            .select('id') \
            .eq('user_id', user_id) \
            .eq('trait_type', trait['trait_type']) \
            .execute()
        
        trait_data = {
            'user_id': user_id,
            **trait,
            'last_validated': datetime.now().isoformat(),
            'is_active': True,
        }
        
        if existing.data and len(existing.data) > 0:
            # Update existing
            response = supabase.table('user_energy_profile') \
                .update(trait_data) \
                .eq('id', existing.data[0]['id']) \
                .execute()
        else:
            # Insert new
            response = supabase.table('user_energy_profile') \
                .insert(trait_data) \
                .execute()
        
        return True
    except Exception as e:
        print(f"Error saving trait {trait['trait_type']}: {e}")
        return False


def learn_energy_profile(user_id: str) -> Dict[str, any]:
    """
    Apprend le profil énergétique complet pour un utilisateur
    Retourne un résumé des traits découverts
    """
    discovered_traits = []
    
    # 1. Sommeil optimal
    sleep_trait = analyze_optimal_sleep_duration(user_id)
    if sleep_trait:
        if save_energy_profile_trait(user_id, sleep_trait):
            discovered_traits.append(sleep_trait['trait_type'])
    
    # 2. Sport tardif
    exercise_trait = analyze_late_exercise_impact(user_id)
    if exercise_trait:
        if save_energy_profile_trait(user_id, exercise_trait):
            discovered_traits.append(exercise_trait['trait_type'])
    
    # 3. Protéines
    protein_trait = analyze_protein_requirement(user_id)
    if protein_trait:
        if save_energy_profile_trait(user_id, protein_trait):
            discovered_traits.append(protein_trait['trait_type'])
    
    # TODO: Ajouter d'autres analyses
    # - Caféine cutoff (quand données disponibles)
    # - Sensibilité alcool
    # - Optimal meal timing
    # - Morning vs evening person
    
    return {
        'user_id': user_id,
        'analyzed_at': datetime.now().isoformat(),
        'traits_discovered': len(discovered_traits),
        'trait_types': discovered_traits,
    }


def learn_all_users_profiles():
    """Cron job: Apprend le profil énergétique pour tous les utilisateurs actifs"""
    # Récupérer tous les users avec au moins 30 jours de données
    response = supabase.table('profiles') \
        .select('id, created_at') \
        .execute()
    
    if not response.data:
        print("No users found")
        return
    
    results = []
    for profile in response.data:
        user_id = profile['id']
        created_at = datetime.fromisoformat(profile['created_at'].replace('Z', '+00:00'))
        days_since_signup = (datetime.now() - created_at).days
        
        if days_since_signup < 30:  # Besoin d'au moins 30 jours d'historique
            continue
        
        print(f"Learning profile for user {user_id}...")
        result = learn_energy_profile(user_id)
        results.append(result)
        print(f"  -> Discovered {result['traits_discovered']} traits")
    
    print(f"\nTotal: {len(results)} users analyzed")
    return results


if __name__ == '__main__':
    # Test sur un user spécifique
    import sys
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
        result = learn_energy_profile(user_id)
        print(result)
    else:
        # Apprendre pour tous les users
        learn_all_users_profiles()
