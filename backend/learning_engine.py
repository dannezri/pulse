"""
Learning Engine - Système d'Apprentissage Personnalisé

Analyse les patterns action → effet pour chaque utilisateur et adapte
les prédictions en fonction de ce qui fonctionne réellement.

Fonctionnalités :
1. Track feedback utilisateur (recommandation suivie ou ignorée)
2. Mesurer précision prédictions (prévu vs réel)
3. Identifier patterns personnels (ex: "coucher plus tôt = +15% énergie")
4. Ajuster poids du modèle prédictif par utilisateur
5. Améliorer recommandations futures

Exécution : Cron quotidien (après calcul daily_state, vers 6h du matin)
"""

import os
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from supabase import create_client, Client
import statistics

# Initialize Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)

# Seuils pour apprentissage
MIN_SAMPLES_FOR_LEARNING = 5  # Minimum d'échantillons pour ajuster poids
LEARNING_RATE = 0.1  # Vitesse d'ajustement des poids


def calculate_feedback_for_user(user_id: str, feedback_date: date) -> bool:
    """Calcule le feedback pour une prédiction (prévu vs réel)"""
    try:
        # Utiliser la RPC function pour calculer
        response = supabase.rpc(
            'calculate_forecast_feedback',
            {
                'p_user_id': user_id,
                'p_feedback_date': feedback_date.isoformat()
            }
        ).execute()
        
        return response.data if response.data else False
    
    except Exception as e:
        print(f"Error calculating feedback for {user_id}: {e}")
        return False


def analyze_recommendation_impact(user_id: str, recommendation_type: str) -> Dict:
    """
    Analyse l'impact d'un type de recommandation pour cet utilisateur
    
    Compare les journées où la recommandation a été suivie vs ignorée
    """
    
    # Récupérer tous les feedbacks avec cette recommandation
    response = supabase.table('forecast_feedback') \
        .select('*') \
        .eq('user_id', user_id) \
        .eq('recommendation_type', recommendation_type) \
        .execute()
    
    if not response.data:
        return {
            'recommendation_type': recommendation_type,
            'sample_size': 0,
            'avg_impact': 0,
            'success_rate': 0,
            'confidence': 'none'
        }
    
    # Séparer suivies vs ignorées
    followed = [f for f in response.data if f['recommendation_followed'] == True]
    ignored = [f for f in response.data if f['recommendation_followed'] == False]
    
    # Calculer impact moyen quand suivi
    impacts_followed = []
    for f in followed:
        # Impact = (réel - prévu)
        # Positif = meilleur que prévu, négatif = pire que prévu
        impact = f['actual_energy_score'] - f['predicted_energy_score']
        impacts_followed.append(impact)
    
    # Calculer impact moyen quand ignoré
    impacts_ignored = []
    for f in ignored:
        impact = f['actual_energy_score'] - f['predicted_energy_score']
        impacts_ignored.append(impact)
    
    avg_impact_followed = statistics.mean(impacts_followed) if impacts_followed else 0
    avg_impact_ignored = statistics.mean(impacts_ignored) if impacts_ignored else 0
    
    # Delta = différence entre suivre et ignorer
    delta = avg_impact_followed - avg_impact_ignored
    
    # Success rate = % de fois où suivre la recommandation a amélioré vs ignorer
    success_count = sum(1 for i, f in enumerate(followed) 
                       if impacts_followed[i] > avg_impact_ignored)
    success_rate = success_count / len(followed) if followed else 0
    
    # Confiance basée sur sample size
    sample_size = len(followed) + len(ignored)
    if sample_size >= 10:
        confidence = 'high'
    elif sample_size >= 5:
        confidence = 'medium'
    else:
        confidence = 'low'
    
    return {
        'recommendation_type': recommendation_type,
        'sample_size': sample_size,
        'avg_impact': round(delta, 1),
        'avg_impact_followed': round(avg_impact_followed, 1),
        'avg_impact_ignored': round(avg_impact_ignored, 1),
        'success_rate': round(success_rate, 2),
        'confidence': confidence,
        'samples_followed': len(followed),
        'samples_ignored': len(ignored),
    }


def learn_user_patterns(user_id: str) -> Dict:
    """
    Apprend les patterns personnels de l'utilisateur
    
    Analyse tous les types de recommandations et leur efficacité
    """
    
    # Récupérer tous les types de recommandations pour cet utilisateur
    response = supabase.table('forecast_feedback') \
        .select('recommendation_type') \
        .eq('user_id', user_id) \
        .not_.is_('recommendation_type', 'null') \
        .execute()
    
    if not response.data:
        return {}
    
    # Types uniques
    rec_types = set(f['recommendation_type'] for f in response.data if f['recommendation_type'])
    
    # Analyser chaque type
    patterns = {}
    for rec_type in rec_types:
        analysis = analyze_recommendation_impact(user_id, rec_type)
        
        # Ne garder que si sample size suffisant
        if analysis['sample_size'] >= 3:
            patterns[rec_type] = {
                'avg_impact': analysis['avg_impact'],
                'success_rate': analysis['success_rate'],
                'sample_size': analysis['sample_size'],
                'confidence': analysis['confidence']
            }
    
    return patterns


def calculate_model_performance(user_id: str) -> Dict:
    """Calcule les métriques de performance du modèle prédictif"""
    
    # Récupérer tous les feedbacks
    response = supabase.table('forecast_feedback') \
        .select('prediction_error, predicted_energy_score, actual_energy_score') \
        .eq('user_id', user_id) \
        .execute()
    
    if not response.data or len(response.data) < 3:
        return {
            'mae': 0,
            'accuracy_rate': 0,
            'total_predictions': 0,
            'learning_iterations': 0
        }
    
    errors = [f['prediction_error'] for f in response.data if f['prediction_error'] is not None]
    
    # Mean Absolute Error
    mae = statistics.mean(errors) if errors else 0
    
    # Accuracy rate : % de prédictions dans ±10% de la réalité
    accurate_count = sum(1 for e in errors if e <= 10)
    accuracy_rate = accurate_count / len(errors) if errors else 0
    
    return {
        'mae': round(mae, 1),
        'accuracy_rate': round(accuracy_rate, 2),
        'total_predictions': len(response.data),
        'learning_iterations': len(response.data) // MIN_SAMPLES_FOR_LEARNING
    }


def adjust_user_weights(user_id: str) -> bool:
    """
    Ajuste les poids du modèle prédictif en fonction de l'apprentissage
    
    Utilise gradient descent simplifié basé sur les erreurs de prédiction
    """
    
    # Récupérer les poids actuels
    response = supabase.table('user_learning_weights') \
        .select('*') \
        .eq('user_id', user_id) \
        .execute()
    
    if response.data and len(response.data) > 0:
        current_weights = response.data[0]
    else:
        # Initialiser avec poids par défaut
        current_weights = {
            'user_id': user_id,
            'recovery_weight': 30.0,
            'sleep_debt_weight': -10.0,
            'overtrain_weight': -30.0,
            'infection_weight': -40.0,
            'activity_weight': -5.0,
        }
    
    # Analyser les patterns appris
    patterns = learn_user_patterns(user_id)
    
    # Calculer performance
    performance = calculate_model_performance(user_id)
    
    # Si pas assez de données, pas d'ajustement
    if performance['total_predictions'] < MIN_SAMPLES_FOR_LEARNING:
        print(f"[{user_id}] Not enough data for learning ({performance['total_predictions']} samples)")
        return False
    
    # Ajuster les poids en fonction des patterns
    # (Logique simplifiée : si une recommandation fonctionne bien, renforcer le poids du facteur associé)
    
    new_weights = {
        'recovery_weight': current_weights['recovery_weight'],
        'sleep_debt_weight': current_weights['sleep_debt_weight'],
        'overtrain_weight': current_weights['overtrain_weight'],
        'infection_weight': current_weights['infection_weight'],
        'activity_weight': current_weights['activity_weight'],
    }
    
    # Exemple d'ajustement :
    # Si "sleep_earlier" a un bon impact, renforcer sleep_debt_weight
    if 'sleep_earlier' in patterns and patterns['sleep_earlier']['success_rate'] > 0.7:
        adjustment = patterns['sleep_earlier']['avg_impact'] * LEARNING_RATE
        new_weights['sleep_debt_weight'] = current_weights['sleep_debt_weight'] + adjustment
    
    # Si "skip_workout" fonctionne bien, renforcer overtrain_weight
    if 'skip_workout' in patterns and patterns['skip_workout']['success_rate'] > 0.7:
        adjustment = patterns['skip_workout']['avg_impact'] * LEARNING_RATE
        new_weights['overtrain_weight'] = current_weights['overtrain_weight'] + adjustment
    
    # Sauvegarder les nouveaux poids
    data = {
        'user_id': user_id,
        **new_weights,
        'learned_patterns': patterns,
        'model_performance': performance,
        'last_updated': datetime.now().isoformat()
    }
    
    try:
        if response.data and len(response.data) > 0:
            # Update
            supabase.table('user_learning_weights') \
                .update(data) \
                .eq('user_id', user_id) \
                .execute()
        else:
            # Insert
            supabase.table('user_learning_weights') \
                .insert(data) \
                .execute()
        
        print(f"[{user_id}] Weights updated. MAE: {performance['mae']}, Accuracy: {performance['accuracy_rate']:.0%}")
        return True
    
    except Exception as e:
        print(f"Error updating weights for {user_id}: {e}")
        return False


def process_daily_learning():
    """
    Cron quotidien : Traite l'apprentissage pour tous les utilisateurs
    
    1. Calcule feedback hier (prévu vs réel)
    2. Analyse patterns
    3. Ajuste poids modèle
    """
    
    # Récupérer tous les users
    response = supabase.table('profiles') \
        .select('id') \
        .execute()
    
    if not response.data:
        print("No users found")
        return
    
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    
    results = {
        'feedback_calculated': 0,
        'weights_adjusted': 0,
        'errors': 0
    }
    
    for profile in response.data:
        user_id = profile['id']
        
        try:
            print(f"\n[{user_id}] Processing learning...")
            
            # 1. Calculer feedback pour hier
            if calculate_feedback_for_user(user_id, date.today() - timedelta(days=1)):
                results['feedback_calculated'] += 1
                print(f"  ✓ Feedback calculated for {yesterday}")
            
            # 2. Ajuster poids (si assez de données)
            if adjust_user_weights(user_id):
                results['weights_adjusted'] += 1
                print(f"  ✓ Weights adjusted")
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results['errors'] += 1
    
    print(f"\n=== Learning Summary ===")
    print(f"Feedback calculated: {results['feedback_calculated']}")
    print(f"Weights adjusted: {results['weights_adjusted']}")
    print(f"Errors: {results['errors']}")


def get_user_stats(user_id: str) -> Dict:
    """Récupère les statistiques d'apprentissage pour un utilisateur"""
    
    try:
        response = supabase.rpc(
            'get_user_learning_stats',
            {'p_user_id': user_id}
        ).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        
        return {
            'total_recommendations': 0,
            'followed_count': 0,
            'follow_rate': 0,
            'avg_prediction_error': 0,
            'best_recommendation': None,
            'best_impact': 0
        }
    
    except Exception as e:
        print(f"Error getting stats for {user_id}: {e}")
        return {}


if __name__ == '__main__':
    # Test sur un user spécifique ou tous les users
    import sys
    
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
        
        print(f"\n=== Learning Engine Test for {user_id} ===\n")
        
        # Calculer feedback hier
        yesterday = date.today() - timedelta(days=1)
        feedback = calculate_feedback_for_user(user_id, yesterday)
        print(f"Feedback calculated: {feedback}")
        
        # Analyser patterns
        patterns = learn_user_patterns(user_id)
        print(f"\nLearned patterns:")
        for rec_type, data in patterns.items():
            print(f"  {rec_type}: impact={data['avg_impact']:+.1f}, success_rate={data['success_rate']:.0%}, n={data['sample_size']}")
        
        # Calculer performance
        performance = calculate_model_performance(user_id)
        print(f"\nModel performance:")
        print(f"  MAE: {performance['mae']:.1f}")
        print(f"  Accuracy: {performance['accuracy_rate']:.0%}")
        print(f"  Total predictions: {performance['total_predictions']}")
        
        # Ajuster poids
        weights_adjusted = adjust_user_weights(user_id)
        print(f"\nWeights adjusted: {weights_adjusted}")
        
        # Stats globales
        stats = get_user_stats(user_id)
        print(f"\nUser stats:")
        print(f"  Total recommendations: {stats.get('total_recommendations', 0)}")
        print(f"  Follow rate: {stats.get('follow_rate', 0):.0%}")
        print(f"  Best recommendation: {stats.get('best_recommendation', 'N/A')} (impact: {stats.get('best_impact', 0):+.1f})")
    
    else:
        # Traiter tous les users
        print("Processing daily learning for all users...")
        process_daily_learning()
