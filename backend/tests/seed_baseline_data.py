#!/usr/bin/env python3
"""
Script pour insérer des données de test réalistes pour les baselines

Insère:
- 60 jours de sommeil avec variabilité naturelle
- 60 jours de HRV avec tendance
- 20 événements café (avec jours propres et jours avec alcool)
- 10 événements alcool
- 15 sessions d'exercice

Usage:
    python seed_baseline_data.py <user_id>

Exemple:
    python seed_baseline_data.py "123e4567-e89b-12d3-a456-426614174000"
"""

import sys
import os
from datetime import datetime, timedelta, timezone
import random
import numpy as np
from dotenv import load_dotenv

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Charger les variables d'environnement
load_dotenv()

from supabase_client import SupabaseClient


def generate_sleep_data(user_id: str, days: int = 60) -> list:
    """
    Génère des données de sommeil réalistes sur N jours
    
    Durée moyenne: 7h30 (450 min) avec variabilité
    Quelques nuits courtes/longues pour tester la robustesse
    """
    data = []
    base_duration = 450  # 7h30 en minutes
    
    today = datetime.now(timezone.utc).date()
    
    for i in range(days):
        date = today - timedelta(days=days - i)
        
        # Variabilité naturelle
        noise = np.random.normal(0, 30)  # ±30 min std
        
        # Quelques outliers (10% de chances)
        if random.random() < 0.1:
            noise += random.choice([-90, 90])  # Nuits très courtes ou très longues
        
        duration = max(240, min(600, base_duration + noise))  # Entre 4h et 10h
        
        recorded_timestamp = datetime.combine(date, datetime.min.time()).replace(tzinfo=timezone.utc)
        data.append({
            'user_id': user_id,
            'metric_type': 'sleep_duration',
            'value': round(duration),
            'source': 'test_seed',
            'recorded_at': recorded_timestamp.isoformat(),
            'measured_at': recorded_timestamp.isoformat()
        })
    
    return data


def generate_hrv_data(user_id: str, days: int = 60) -> list:
    """
    Génère des données HRV réalistes sur N jours
    
    HRV médiane: 60 ms avec tendance légèrement croissante
    Variabilité: MAD ~ 8-10 ms
    """
    data = []
    base_hrv = 58  # Baseline de départ
    trend = 0.1  # Légère hausse de 0.1 ms/jour
    
    today = datetime.now(timezone.utc).date()
    
    for i in range(days):
        date = today - timedelta(days=days - i)
        
        # Tendance + variabilité
        hrv = base_hrv + (trend * i) + np.random.normal(0, 8)
        
        # Quelques jours de maladie/stress (HRV basse)
        if random.random() < 0.05:
            hrv -= 15
        
        hrv = max(30, min(100, hrv))  # Plage réaliste
        
        recorded_timestamp = datetime.combine(date, datetime.min.time()).replace(tzinfo=timezone.utc)
        data.append({
            'user_id': user_id,
            'metric_type': 'hrv',
            'value': round(hrv, 1),
            'source': 'test_seed',
            'recorded_at': recorded_timestamp.isoformat(),
            'measured_at': recorded_timestamp.isoformat()
        })
    
    return data


def generate_caffeine_events(user_id: str, count: int = 20) -> list:
    """
    Génère des événements caféine réalistes
    
    Quantités variables: 50-200mg
    Répartis sur les 90 derniers jours
    """
    events = []
    today = datetime.now(timezone.utc)
    
    for _ in range(count):
        # Date aléatoire dans les 90 derniers jours
        days_ago = random.randint(1, 90)
        event_date = today - timedelta(days=days_ago)
        
        # Heure matinale (7h-11h)
        hour = random.randint(7, 11)
        event_datetime = event_date.replace(hour=hour, minute=random.randint(0, 59))
        
        # Quantité de caféine
        amount_mg = random.choice([50, 80, 100, 120, 150, 200])
        
        events.append({
            'user_id': user_id,
            'category': 'caffeine',
            'details': {'amount_mg': amount_mg, 'time': event_datetime.isoformat()},
            'logged_at': event_datetime.isoformat(),
            'source': 'test_seed'
        })
    
    return events


def generate_alcohol_events(user_id: str, count: int = 10) -> list:
    """
    Génère des événements alcool réalistes
    
    Quantités: 1-3 unités
    Répartis sur les 90 derniers jours
    """
    events = []
    today = datetime.now(timezone.utc)
    
    for _ in range(count):
        # Date aléatoire dans les 90 derniers jours
        days_ago = random.randint(1, 90)
        event_date = today - timedelta(days=days_ago)
        
        # Heure soirée (18h-23h)
        hour = random.randint(18, 23)
        event_datetime = event_date.replace(hour=hour, minute=random.randint(0, 59))
        
        # Quantité
        units = random.choice([1, 1.5, 2, 2.5, 3])
        alcohol_type = random.choice(['vin', 'bière', 'spiritueux'])
        
        events.append({
            'user_id': user_id,
            'category': 'alcohol',
            'details': {'units': units, 'type': alcohol_type, 'time': event_datetime.isoformat()},
            'logged_at': event_datetime.isoformat(),
            'source': 'test_seed'
        })
    
    return events


def generate_exercise_events(user_id: str, count: int = 15) -> list:
    """
    Génère des événements exercice réalistes
    
    Types: course, vélo, musculation, natation
    Durées: 20-90 minutes
    Intensités variées
    """
    events = []
    today = datetime.now(timezone.utc)
    
    exercise_types = ['course', 'vélo', 'musculation', 'natation', 'yoga']
    intensities = ['light', 'moderate', 'intense']
    
    for _ in range(count):
        # Date aléatoire dans les 60 derniers jours
        days_ago = random.randint(1, 60)
        event_date = today - timedelta(days=days_ago)
        
        # Heure (7h-20h)
        hour = random.randint(7, 20)
        event_datetime = event_date.replace(hour=hour, minute=random.randint(0, 59))
        
        # Détails exercice
        exercise_type = random.choice(exercise_types)
        duration = random.randint(20, 90)
        intensity = random.choice(intensities)
        calories = duration * random.randint(5, 12)  # Estimation calories
        
        events.append({
            'user_id': user_id,
            'category': 'exercise',
            'details': {
                'type': exercise_type,
                'duration_minutes': duration,
                'intensity': intensity,
                'calories': calories,
                'time': event_datetime.isoformat()
            },
            'logged_at': event_datetime.isoformat(),
            'source': 'test_seed'
        })
    
    return events


def main():
    if len(sys.argv) < 2:
        print("Usage: python seed_baseline_data.py <user_id>")
        print("Example: python seed_baseline_data.py '123e4567-e89b-12d3-a456-426614174000'")
        sys.exit(1)
    
    user_id = sys.argv[1]
    
    # Initialiser le client Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not all([supabase_url, supabase_key]):
        print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
        sys.exit(1)
    
    supabase = SupabaseClient(supabase_url, supabase_key)
    
    print(f"=== SEEDING TEST DATA FOR USER {user_id} ===\n")
    
    # Générer les données
    print("Génération des données de sommeil (60 jours)...")
    sleep_data = generate_sleep_data(user_id, days=60)
    
    print("Génération des données HRV (60 jours)...")
    hrv_data = generate_hrv_data(user_id, days=60)
    
    print("Génération des événements caféine (20)...")
    caffeine_events = generate_caffeine_events(user_id, count=20)
    
    print("Génération des événements alcool (10)...")
    alcohol_events = generate_alcohol_events(user_id, count=10)
    
    print("Génération des événements exercice (15)...")
    exercise_events = generate_exercise_events(user_id, count=15)
    
    # Insérer dans la base de données
    print("\nInsertion dans biometrics...")
    try:
        biometrics_data = sleep_data + hrv_data
        response = supabase.client.table('biometrics').insert(biometrics_data).execute()
        print(f"✓ {len(biometrics_data)} entrées biométriques insérées")
    except Exception as e:
        print(f"✗ Erreur insertion biometrics: {e}")
    
    print("\nInsertion dans daily_context...")
    try:
        context_data = caffeine_events + alcohol_events + exercise_events
        response = supabase.client.table('daily_context').insert(context_data).execute()
        print(f"✓ {len(context_data)} événements contextuels insérés")
    except Exception as e:
        print(f"✗ Erreur insertion daily_context: {e}")
    
    print("\n=== SEEDING TERMINÉ ===")
    print("\nPour calculer les baselines:")
    print(f"  python cron_calculate_baselines.py")
    print(f"  # ou")
    print(f"  curl -X POST http://localhost:9000/api/baselines/calculate/{user_id} \\")
    print(f"       -H 'X-Cron-Secret: YOUR_CRON_SECRET'")


if __name__ == "__main__":
    main()
