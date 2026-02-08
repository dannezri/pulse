#!/usr/bin/env python3
"""
Test de l'API FatSecret avec OAuth 2.0 Client Credentials
FatSecret supporte maintenant OAuth 2.0 pour les applications serveur
"""

import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

CONSUMER_KEY = os.getenv("FATSECRET_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("FATSECRET_CONSUMER_SECRET")

def test_oauth2_client_credentials():
    """
    Test avec OAuth 2.0 Client Credentials Flow
    Documentation: https://platform.fatsecret.com/api/Default.aspx?screen=rapiauth2
    """
    print("=" * 70)
    print("TEST FATSECRET OAUTH 2.0 CLIENT CREDENTIALS")
    print("=" * 70)
    print()
    
    if not CONSUMER_KEY or not CONSUMER_SECRET:
        print("❌ Credentials manquantes")
        return False
    
    print(f"✅ Consumer Key: {CONSUMER_KEY[:20]}...")
    print(f"✅ Consumer Secret: {CONSUMER_SECRET[:20]}...")
    print()
    
    # OAuth 2.0 Token endpoint
    token_url = "https://oauth.fatsecret.com/connect/token"
    
    # Créer les credentials en Base64
    credentials = f"{CONSUMER_KEY}:{CONSUMER_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    print("🔑 Obtention du token OAuth 2.0...")
    print()
    
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "client_credentials",
        "scope": "basic"
    }
    
    try:
        response = requests.post(token_url, headers=headers, data=data, timeout=30)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        print()
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            
            print("=" * 70)
            print("✅ SUCCÈS ! OAuth 2.0 fonctionne !")
            print("=" * 70)
            print()
            print(f"Access Token: {access_token[:30]}...")
            print(f"Token Type: {token_data.get('token_type')}")
            print(f"Expires in: {token_data.get('expires_in')} seconds")
            print()
            
            # Test d'une requête API
            print("🧪 Test d'une requête API...")
            test_api_call(access_token)
            
            return True
        else:
            print("=" * 70)
            print("❌ Échec OAuth 2.0")
            print("=" * 70)
            print()
            print("Erreur détaillée:")
            try:
                error_data = response.json()
                print(f"  Error: {error_data.get('error')}")
                print(f"  Description: {error_data.get('error_description')}")
            except:
                print(f"  {response.text}")
            
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_api_call(access_token):
    """Test un appel API avec le token"""
    # Test avec l'endpoint de recherche d'aliments
    api_url = "https://platform.fatsecret.com/rest/server.api"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    params = {
        "method": "foods.search",
        "search_expression": "apple",
        "format": "json"
    }
    
    try:
        response = requests.get(api_url, headers=headers, params=params, timeout=30)
        print(f"   API Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API fonctionne ! Résultats trouvés.")
            # print(f"   Données: {str(data)[:100]}...")
        else:
            print(f"   ❌ API Error: {response.text[:100]}")
            
    except Exception as e:
        print(f"   ❌ Exception API: {e}")

if __name__ == "__main__":
    success = test_oauth2_client_credentials()
    
    if success:
        print()
        print("=" * 70)
        print("✨ FatSecret utilise OAuth 2.0 Client Credentials !")
        print("=" * 70)
        print()
        print("Action requise:")
        print("  → Le fatsecret_client.py doit être réécrit pour OAuth 2.0")
        print("  → OAuth 1.0a n'est plus supporté (ou pas pour ce type d'app)")
        print()
    else:
        print()
        print("=" * 70)
        print("⚠️  OAuth 2.0 n'a pas fonctionné non plus")
        print("=" * 70)
        print()
        print("Vérifications:")
        print("  1. Sur https://platform.fatsecret.com/api/")
        print("  2. Vérifiez le type de votre application")
        print("  3. Vérifiez que l'application est 'Active'")
        print("  4. Copiez/collez à nouveau les credentials")
        print()
