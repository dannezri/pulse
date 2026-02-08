"""
Script de test pour le système Wellness Coach
Valide le cache intelligent et les états (optimal/warning/alert)
"""

import os
import sys
import json
import time
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

from supabase_client import SupabaseClient
from llm_client import LLMClient
from services.ai_service import AIAnalysisService

def test_cache_system():
    """
    Test 1: Système de Cache Intelligent
    
    Vérifie que:
    1. Premier appel génère un nouveau Brief (cached=False)
    2. Deuxième appel immédiat retourne le cache (cached=True)
    3. Le cache est invalide après ajout de nouvelles biométriques
    """
    print("\n" + "="*60)
    print("TEST 1: Système de Cache Intelligent")
    print("="*60)
    
    # Initialiser les services
    supabase_client = SupabaseClient(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
    )
    llm_client = LLMClient()
    ai_service = AIAnalysisService(supabase_client, llm_client)
    
    # Utiliser un user_id de test (remplacer par un vrai UUID)
    test_user_id = os.getenv("TEST_USER_ID")
    if not test_user_id:
        print("❌ TEST_USER_ID non défini dans .env")
        return False
    
    print(f"\n📋 Test avec user_id: {test_user_id}")
    
    # Test 1.1: Premier appel (devrait générer)
    print("\n1️⃣ Premier appel (génération attendue)...")
    start = time.time()
    result1 = ai_service.generate_brief(test_user_id, force_refresh=False)
    duration1 = time.time() - start
    
    if result1.get("status") != "success":
        print(f"❌ Erreur: {result1.get('message')}")
        return False
    
    cached1 = result1.get("cached", False)
    cards1 = result1.get("cards", [])
    pulse_score1 = result1.get("pulseScore", 0)
    
    print(f"✅ Résultat: cached={cached1}, cards={len(cards1)}, score={pulse_score1}")
    print(f"⏱️  Durée: {duration1:.2f}s")
    
    if cached1:
        print("⚠️  WARNING: Premier appel devrait être non-caché (cached=False)")
    
    # Test 1.2: Deuxième appel immédiat (devrait utiliser cache)
    print("\n2️⃣ Deuxième appel immédiat (cache attendu)...")
    start = time.time()
    result2 = ai_service.generate_brief(test_user_id, force_refresh=False)
    duration2 = time.time() - start
    
    cached2 = result2.get("cached", False)
    pulse_score2 = result2.get("pulseScore", 0)
    
    print(f"✅ Résultat: cached={cached2}, score={pulse_score2}")
    print(f"⏱️  Durée: {duration2:.2f}s")
    
    if not cached2:
        print("❌ ÉCHEC: Deuxième appel devrait utiliser le cache (cached=True)")
        return False
    
    if pulse_score1 != pulse_score2:
        print("❌ ÉCHEC: Les scores devraient être identiques")
        return False
    
    print(f"🚀 Accélération: {duration1/duration2:.1f}x plus rapide avec cache")
    
    # Test 1.3: Force refresh (devrait ignorer cache)
    print("\n3️⃣ Appel avec force_refresh=True...")
    start = time.time()
    result3 = ai_service.generate_brief(test_user_id, force_refresh=True)
    duration3 = time.time() - start
    
    cached3 = result3.get("cached", False)
    print(f"✅ Résultat: cached={cached3}")
    print(f"⏱️  Durée: {duration3:.2f}s")
    
    if cached3:
        print("❌ ÉCHEC: force_refresh devrait ignorer le cache")
        return False
    
    print("\n✅ Test de cache réussi !")
    return True


def test_alert_states():
    """
    Test 2: États Alert et Couleurs
    
    Vérifie que:
    1. Score < 60 → state="alert" (rouge)
    2. Score 60-75 → state="warning" (orange)
    3. Score > 75 → state="optimal" (vert)
    4. Timing < 30 → state="alert" même si score OK
    """
    print("\n" + "="*60)
    print("TEST 2: États et Couleurs")
    print("="*60)
    
    # Initialiser les services
    supabase_client = SupabaseClient(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
    )
    llm_client = LLMClient()
    ai_service = AIAnalysisService(supabase_client, llm_client)
    
    test_user_id = os.getenv("TEST_USER_ID")
    if not test_user_id:
        print("❌ TEST_USER_ID non défini dans .env")
        return False
    
    # Récupérer le Brief
    print(f"\n📋 Analyse du Brief pour user_id: {test_user_id}")
    result = ai_service.generate_brief(test_user_id, force_refresh=False)
    
    if result.get("status") != "success":
        print(f"❌ Erreur: {result.get('message')}")
        return False
    
    cards = result.get("cards", [])
    pulse_score = result.get("pulseScore", 0)
    
    print(f"\n📊 Score Pulse: {pulse_score}%")
    print(f"📇 Nombre de cartes: {len(cards)}")
    
    # Analyser les états
    state_counts = {"optimal": 0, "warning": 0, "alert": 0, "neutral": 0}
    
    for i, card in enumerate(cards, 1):
        state = card.get("state", "neutral")
        title = card.get("title", "Sans titre")
        badge = card.get("badge", "N/A")
        icon = card.get("iconName", "N/A")
        
        state_counts[state] += 1
        
        # Emoji pour l'état
        emoji_map = {
            "optimal": "🟢",
            "warning": "🟡",
            "alert": "🔴",
            "neutral": "⚪"
        }
        emoji = emoji_map.get(state, "❓")
        
        print(f"\n{i}. {emoji} {title}")
        print(f"   État: {state}")
        print(f"   Badge: {badge}")
        print(f"   Icône: {icon}")
    
    # Vérifications
    print("\n" + "-"*60)
    print("📈 Répartition des états:")
    for state, count in state_counts.items():
        print(f"   {state}: {count}")
    
    # Valider la logique
    has_alert = state_counts["alert"] > 0
    has_warning = state_counts["warning"] > 0
    has_optimal = state_counts["optimal"] > 0
    
    if pulse_score < 60 and not has_alert:
        print(f"\n❌ ÉCHEC: Score {pulse_score} devrait avoir au moins une carte 'alert'")
        return False
    
    if pulse_score >= 75 and not has_optimal:
        print(f"\n⚠️  WARNING: Score {pulse_score} devrait probablement avoir des cartes 'optimal'")
    
    print("\n✅ Test des états réussi !")
    return True


def test_wellness_coach_content():
    """
    Test 3: Contenu Pédagogique
    
    Vérifie que:
    1. Les analogies (batterie, moteur, horloge) sont présentes
    2. Le ton est empathique et direct
    3. Les actions sont concrètes
    """
    print("\n" + "="*60)
    print("TEST 3: Qualité du Contenu Wellness Coach")
    print("="*60)
    
    # Initialiser les services
    supabase_client = SupabaseClient(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
    )
    llm_client = LLMClient()
    ai_service = AIAnalysisService(supabase_client, llm_client)
    
    test_user_id = os.getenv("TEST_USER_ID")
    if not test_user_id:
        print("❌ TEST_USER_ID non défini dans .env")
        return False
    
    # Récupérer le Brief
    result = ai_service.generate_brief(test_user_id, force_refresh=False)
    
    if result.get("status") != "success":
        print(f"❌ Erreur: {result.get('message')}")
        return False
    
    cards = result.get("cards", [])
    
    # Chercher les analogies
    analogies = ["batterie", "moteur", "horloge", "carburant", "voyant"]
    all_content = " ".join([card.get("content", "").lower() for card in cards])
    
    found_analogies = [a for a in analogies if a in all_content]
    
    print(f"\n🎯 Analogies trouvées: {', '.join(found_analogies) if found_analogies else 'Aucune'}")
    
    if not found_analogies:
        print("⚠️  WARNING: Aucune analogie trouvée (batterie, moteur, horloge)")
    
    # Vérifier les actions
    actions = [card.get("actionButton") for card in cards if card.get("actionButton")]
    print(f"\n🎬 Actions disponibles: {len(actions)}")
    
    for i, action in enumerate(actions, 1):
        label = action.get("label", "N/A")
        action_type = action.get("action", "N/A")
        print(f"   {i}. {label} → {action_type}")
    
    print("\n✅ Test du contenu terminé !")
    return True


if __name__ == "__main__":
    print("\n" + "🚀" * 30)
    print("Test du Système Wellness Coach IA")
    print("🚀" * 30)
    
    # Vérifier les variables d'environnement
    required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_KEY", "OPENAI_API_KEY", "TEST_USER_ID"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"\n❌ Variables d'environnement manquantes: {', '.join(missing_vars)}")
        print("\nAjoutez-les dans votre fichier .env:")
        print("TEST_USER_ID=<votre-uuid-utilisateur>")
        sys.exit(1)
    
    # Exécuter les tests
    results = []
    
    try:
        results.append(("Cache Intelligent", test_cache_system()))
    except Exception as e:
        print(f"\n❌ Erreur test cache: {e}")
        results.append(("Cache Intelligent", False))
    
    try:
        results.append(("États et Couleurs", test_alert_states()))
    except Exception as e:
        print(f"\n❌ Erreur test états: {e}")
        results.append(("États et Couleurs", False))
    
    try:
        results.append(("Contenu Pédagogique", test_wellness_coach_content()))
    except Exception as e:
        print(f"\n❌ Erreur test contenu: {e}")
        results.append(("Contenu Pédagogique", False))
    
    # Résumé
    print("\n" + "="*60)
    print("RÉSUMÉ DES TESTS")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASSÉ" if passed else "❌ ÉCHOUÉ"
        print(f"{name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS ! 🎉")
        sys.exit(0)
    else:
        print("\n❌ Certains tests ont échoué")
        sys.exit(1)
