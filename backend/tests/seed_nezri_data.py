#!/usr/bin/env python3
"""
Génère des données de test propres pour l'utilisateur Nezri
"""
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import SupabaseClient
from datetime import datetime, timedelta
import random

def main():
    # Initialiser le client Supabase avec les variables d'environnement
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        print('❌ Variables d\'environnement SUPABASE_URL et SUPABASE_SERVICE_KEY requises')
        return
    
    supabase = SupabaseClient(supabase_url, supabase_key)
    
    # User ID Nezri
    user_id = '006b5096-1983-44ae-9fc5-a8431c9f40be'
    
    print(f'🗑️  Nettoyage des anciennes données pour Nezri...')
    
    # Supprimer anciennes données
    supabase.client.table('biometrics').delete().eq('user_id', user_id).execute()
    supabase.client.table('daily_context').delete().eq('user_id', user_id).execute()
    
    print(f'✅ Anciennes données supprimées')
    
    # Générer 90 jours de données de sommeil réalistes
    print(f'📊 Génération de 90 jours de sommeil...')
    end_date = datetime.now()
    biometrics_data = []
    
    for i in range(90):
        date = end_date - timedelta(days=i)
        
        # Sommeil réaliste: 7h-8h avec variation
        sleep_duration = random.randint(420, 490)  # 7h-8h10
        deep_sleep = random.randint(60, 120)
        rem_sleep = random.randint(90, 150)
        
        biometrics_data.append({
            'user_id': user_id,
            'metric_type': 'sleep_duration',
            'value': sleep_duration,
            'unit': 'minutes',
            'recorded_at': date.isoformat(),
            'measured_at': date.isoformat(),
            'source': 'test',
            'metadata': {
                'deep_sleep': deep_sleep,
                'rem_sleep': rem_sleep,
                'efficiency': random.uniform(85, 95)
            }
        })
    
    # Insérer par lots
    for i in range(0, len(biometrics_data), 20):
        batch = biometrics_data[i:i+20]
        result = supabase.client.table('biometrics').insert(batch).execute()
        if result.data:
            print(f'✓ Inséré lot sommeil {i//20 + 1}/5')
    
    # Générer 60 jours de HRV
    print(f'❤️  Génération de 60 jours de HRV...')
    hrv_data = []
    for i in range(60):
        date = end_date - timedelta(days=i)
        hrv_value = random.randint(55, 75)  # HRV réaliste
        
        hrv_data.append({
            'user_id': user_id,
            'metric_type': 'hrv',
            'value': hrv_value,
            'unit': 'ms',
            'recorded_at': date.isoformat(),
            'measured_at': date.isoformat(),
            'source': 'test'
        })
    
    for i in range(0, len(hrv_data), 20):
        batch = hrv_data[i:i+20]
        result = supabase.client.table('biometrics').insert(batch).execute()
        if result.data:
            print(f'✓ Inséré lot HRV {i//20 + 1}/3')
    
    # Générer quelques événements contexte
    print(f'☕ Génération d\'événements...')
    events = []
    for i in range(20):
        date = end_date - timedelta(days=i*2)
        events.append({
            'user_id': user_id,
            'category': 'caffeine',
            'logged_at': date.isoformat(),
            'details': {'amount': random.choice([1, 2]), 'type': 'coffee'}
        })
    
    result = supabase.client.table('daily_context').insert(events).execute()
    print(f'✓ Événements insérés: {len(events)}')
    
    print(f'\n✅ Données créées avec succès!')
    print(f'📊 90 nuits de sommeil + 60 jours HRV + 20 cafés')
    print(f'👤 User: Nezri ({user_id})')

if __name__ == '__main__':
    main()
