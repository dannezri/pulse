#!/usr/bin/env python3
"""
Test manuel de l'API FatSecret OAuth avec construction manuelle de la signature
"""

import os
import time
import hashlib
import hmac
import base64
import urllib.parse
import requests
from dotenv import load_dotenv

load_dotenv()

CONSUMER_KEY = os.getenv("FATSECRET_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("FATSECRET_CONSUMER_SECRET")

def generate_oauth_signature(method, url, params, consumer_secret, token_secret=""):
    """Génère une signature OAuth 1.0 HMAC-SHA1"""
    # 1. Trier les paramètres
    sorted_params = sorted(params.items())
    
    # 2. Créer la chaîne de paramètres
    param_string = "&".join([f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in sorted_params])
    
    # 3. Créer la base string
    base_string = f"{method}&{urllib.parse.quote(url, safe='')}&{urllib.parse.quote(param_string, safe='')}"
    
    # 4. Créer la signing key
    signing_key = f"{urllib.parse.quote(consumer_secret, safe='')}&{urllib.parse.quote(token_secret, safe='')}"
    
    # 5. Calculer la signature
    signature = base64.b64encode(
        hmac.new(
            signing_key.encode(),
            base_string.encode(),
            hashlib.sha1
        ).digest()
    ).decode()
    
    return signature

def test_request_token():
    """Test d'obtention d'un request token avec construction manuelle"""
    print("=" * 70)
    print("TEST MANUEL FATSECRET OAUTH")
    print("=" * 70)
    print()
    
    if not CONSUMER_KEY or not CONSUMER_SECRET:
        print("❌ Credentials manquantes dans .env")
        return False
    
    print(f"✅ Consumer Key: {CONSUMER_KEY[:20]}...")
    print(f"✅ Consumer Secret: {CONSUMER_SECRET[:20]}...")
    print()
    
    # URL et méthode
    url = "https://authentication.fatsecret.com/oauth/request_token"
    method = "POST"
    
    # Paramètres OAuth
    oauth_params = {
        "oauth_consumer_key": CONSUMER_KEY,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_nonce": str(int(time.time() * 1000000)),
        "oauth_version": "1.0",
        "oauth_callback": "oob"
    }
    
    # Générer la signature
    signature = generate_oauth_signature(method, url, oauth_params, CONSUMER_SECRET)
    oauth_params["oauth_signature"] = signature
    
    print("📝 Paramètres OAuth:")
    for key, value in oauth_params.items():
        if key != "oauth_signature":
            print(f"   {key}: {value}")
    print(f"   oauth_signature: {signature[:30]}...")
    print()
    
    # Test 1: Paramètres dans l'URL (query string)
    print("🧪 Test 1: Paramètres dans l'URL (GET-style)")
    try:
        response = requests.post(url, params=oauth_params, timeout=30)
        print(f"   Status: {response.status_code}")
        print(f"   Body: {response.text[:100]}")
        if response.status_code == 200:
            print("   ✅ SUCCÈS !")
            return True
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    print()
    
    # Test 2: Paramètres dans le corps (form data)
    print("🧪 Test 2: Paramètres dans le corps (POST form)")
    # Recalculer la signature pour POST body
    signature_body = generate_oauth_signature(method, url, oauth_params, CONSUMER_SECRET)
    oauth_params["oauth_signature"] = signature_body
    
    try:
        response = requests.post(
            url,
            data=oauth_params,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        print(f"   Body: {response.text[:100]}")
        if response.status_code == 200:
            print("   ✅ SUCCÈS !")
            return True
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    print()
    
    # Test 3: Authorization header
    print("🧪 Test 3: Authorization header")
    oauth_header = 'OAuth ' + ', '.join([f'{k}="{urllib.parse.quote(str(v), safe="")}"' for k, v in oauth_params.items()])
    
    try:
        response = requests.post(
            url,
            headers={"Authorization": oauth_header},
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        print(f"   Body: {response.text[:100]}")
        if response.status_code == 200:
            print("   ✅ SUCCÈS !")
            print(f"   Response complète: {response.text}")
            return True
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    print()
    
    print("=" * 70)
    print("❌ Tous les tests ont échoué")
    print("=" * 70)
    return False

if __name__ == "__main__":
    test_request_token()
