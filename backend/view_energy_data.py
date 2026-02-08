#!/usr/bin/env python3
"""
Script pour visualiser les données extraites de la page énergie
"""

import json
import sys
from datetime import datetime

def format_timestamp(ts_str):
    """Formate un timestamp ISO en format lisible"""
    try:
        dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        return dt.strftime('%d/%m/%Y %H:%M:%S')
    except:
        return ts_str

def print_section(title, symbol="📊"):
    """Affiche un titre de section"""
    print(f"\n{symbol} {title}")
    print("=" * 60)

def print_card(card):
    """Affiche une carte Brief"""
    state_emoji = {
        'optimal': '✅',
        'warning': '⚠️',
        'alert': '🚨',
        'neutral': '💬'
    }
    emoji = state_emoji.get(card.get('state', 'neutral'), '💬')
    
    print(f"\n{emoji} {card['title']}")
    print(f"   Type: {card['type']}")
    print(f"   État: {card['state']}")
    if 'badge' in card:
        unit = card.get('badgeUnit', '')
        print(f"   Badge: {card['badge']} {unit}")
    print(f"   Contenu: {card['content'][:100]}...")
    if 'actionButton' in card and card['actionButton']:
        print(f"   Action: {card['actionButton']['label']}")

def main():
    # Chercher le fichier le plus récent
    import glob
    import os
    
    pattern = "/Users/dannezri/Desktop/Pulse/energy_data_export_*.json"
    files = glob.glob(pattern)
    
    if not files:
        print(f"❌ Aucun fichier trouvé: {pattern}")
        sys.exit(1)
    
    latest_file = max(files, key=os.path.getctime)
    print(f"📂 Lecture: {os.path.basename(latest_file)}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # En-tête
    print("=" * 60)
    print("🔍 VISUALISATION DONNÉES PAGE ÉNERGIE")
    print("=" * 60)
    
    # Informations utilisateur
    print_section("Utilisateur", "👤")
    print(f"ID: {data['user_id']}")
    print(f"Extraction: {format_timestamp(data['extracted_at'])}")
    
    # Brief
    brief = data['brief']
    print_section("Brief Quotidien", "📋")
    print(f"Pulse Score: {brief['pulseScore']}%")
    print(f"Cached: {'Oui' if brief['cached'] else 'Non'}")
    print(f"Analysé à: {format_timestamp(brief['analyzed_at'])}")
    
    if 'usage' in brief:
        usage = brief['usage']
        print(f"\nUtilisation IA:")
        print(f"  - Prompt: {usage['prompt_tokens']} tokens")
        print(f"  - Complétion: {usage['completion_tokens']} tokens")
        print(f"  - Total: {usage['total_tokens']} tokens")
    
    # Cartes
    print_section(f"Cartes Brief ({len(brief['cards'])})", "🎴")
    for card in brief['cards']:
        print_card(card)
    
    # Prévision intraday
    if 'intraday_energy_forecast' in brief and brief['intraday_energy_forecast']:
        forecast = brief['intraday_energy_forecast']
        print_section("Prévision Énergétique Intraday", "⚡")
        print(f"Type: {forecast['type']}")
        print(f"Date: {forecast['date']}")
        print(f"Modèle: {forecast['model_version']}")
        print(f"Timezone: {forecast['timezone']}")
        print(f"Points: {len(forecast.get('points', []))}")
        print(f"Confidence: {forecast.get('confidence', 'N/A')}")
        
        # Afficher quelques points
        if 'points' in forecast and forecast['points']:
            print(f"\nÉchantillon de points (premiers 5):")
            for i, point in enumerate(forecast['points'][:5]):
                time = datetime.fromisoformat(point['t'].replace('Z', '+00:00')).strftime('%H:%M')
                print(f"  {time}: {point['energy']}%")
        
        # Influenceurs
        if 'influencers' in forecast and forecast['influencers']:
            print(f"\nInfluenceurs ({len(forecast['influencers'])}):")
            for inf in forecast['influencers']:
                status_emoji = '✅' if inf.get('status') == 'positive' else '🔻'
                print(f"  {status_emoji} {inf.get('name', 'N/A')}: {inf.get('impact', 'N/A')}")
        
        # Notes
        if 'notes' in forecast and forecast['notes']:
            print(f"\nNotes ({len(forecast['notes'])}):")
            for i, note in enumerate(forecast['notes'], 1):
                print(f"  {i}. {note}")
    
    # Biométriques
    biometrics = data['biometrics']
    print_section(f"Biométriques ({len(biometrics['all'])} enregistrements)", "📊")
    
    for metric_type, records in biometrics['by_type'].items():
        if records:
            values = [r['value'] for r in records]
            avg = sum(values) / len(values)
            min_val = min(values)
            max_val = max(values)
            print(f"\n{metric_type.upper()}:")
            print(f"  Valeurs: {len(records)}")
            print(f"  Moyenne: {avg:.1f}")
            print(f"  Min: {min_val:.1f}")
            print(f"  Max: {max_val:.1f}")
            
            # Dernière valeur
            latest = sorted(records, key=lambda x: x['recorded_at'], reverse=True)[0]
            print(f"  Dernière: {latest['value']:.1f} ({format_timestamp(latest['recorded_at'])})")
    
    # Médicaments
    print_section(f"Médicaments ({len(data['medications'])})", "💊")
    if data['medications']:
        for med in data['medications']:
            print(f"  - {med.get('name', 'N/A')}")
    else:
        print("  Aucun médicament enregistré")
    
    # Conditions
    print_section(f"Conditions de Santé ({len(data['conditions'])})", "🏥")
    if data['conditions']:
        for cond in data['conditions']:
            print(f"  - {cond.get('name', 'N/A')}")
    else:
        print("  Aucune condition enregistrée")
    
    # Feedbacks
    print_section(f"Feedbacks ({len(data['feedbacks'])})", "💬")
    if data['feedbacks']:
        for fb in data['feedbacks']:
            print(f"  - {fb.get('feedback_type', 'N/A')}: {fb.get('rating', 'N/A')}/5")
            print(f"    {fb.get('comment', '')[:80]}")
    else:
        print("  Aucun feedback soumis")
    
    # Profil énergétique
    print_section("Profil Énergétique Personnalisé", "🎯")
    if data['energy_profile']:
        profile = data['energy_profile']
        print(f"  Version: {profile.get('version', 'N/A')}")
        print(f"  Créé: {format_timestamp(profile.get('created_at', 'N/A'))}")
        if 'weights' in profile:
            print(f"  Poids personnalisés: {len(profile['weights'])} facteurs")
    else:
        print("  Aucun profil personnalisé (utilise les poids par défaut)")
    
    print("\n" + "=" * 60)
    print("✅ Visualisation terminée")
    print("=" * 60)

if __name__ == "__main__":
    main()
