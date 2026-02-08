#!/usr/bin/env python3
"""
Script de test des credentials FatSecret
Vérifie que les credentials sont valides en tentant d'obtenir un request token
"""

import os
import sys
from dotenv import load_dotenv

# Charger .env
load_dotenv()

print("=" * 70)
print("TEST DES CREDENTIALS FATSECRET")
print("=" * 70)
print()

# Vérifier que les variables existent
consumer_key = os.getenv("FATSECRET_CONSUMER_KEY")
consumer_secret = os.getenv("FATSECRET_CONSUMER_SECRET")

if not consumer_key:
    print("❌ FATSECRET_CONSUMER_KEY n'est pas définie dans .env")
    sys.exit(1)

if not consumer_secret:
    print("❌ FATSECRET_CONSUMER_SECRET n'est pas définie dans .env")
    sys.exit(1)

print(f"✅ Consumer Key trouvée: {consumer_key[:20]}... ({len(consumer_key)} caractères)")
print(f"✅ Consumer Secret trouvée: {consumer_secret[:20]}... ({len(consumer_secret)} caractères)")
print()

# Test de connexion
print("🔍 Test de connexion à l'API FatSecret...")
print()

try:
    from fatsecret_client import FatSecretClient
    
    client = FatSecretClient(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret
    )
    
    print("Tentative d'obtention d'un request token...")
    print()
    
    tokens = client.get_request_token()
    
    print("=" * 70)
    print("✅ SUCCÈS ! Les credentials sont valides.")
    print("=" * 70)
    print()
    print(f"Request token obtenu: {tokens.get('oauth_token', 'N/A')[:30]}...")
    print()
    print("Vous pouvez maintenant utiliser setup_fatsecret.py")
    print("=" * 70)
    
except Exception as e:
    print("=" * 70)
    print("❌ ÉCHEC - Les credentials ne fonctionnent pas")
    print("=" * 70)
    print()
    print(f"Erreur: {e}")
    print()
    print("Vérifications à faire:")
    print("1. Les credentials sont-ils corrects ?")
    print("   → Vérifiez sur https://platform.fatsecret.com/api/")
    print()
    print("2. Y a-t-il des espaces ou caractères invisibles ?")
    print("   → Dans .env, assurez-vous qu'il n'y a pas d'espaces:")
    print("   → FATSECRET_CONSUMER_KEY=votre_key (pas d'espaces)")
    print()
    print("3. L'application FatSecret est-elle active ?")
    print("   → Connectez-vous sur FatSecret Platform")
    print("   → Vérifiez que votre application est en statut 'Active'")
    print()
    print("=" * 70)
    sys.exit(1)
