#!/usr/bin/env python3
"""
Script interactif pour compléter le flux OAuth2 Oura pour un utilisateur

Usage:
    python3 oura_oauth2_flow.py --user-id bee9a055-9b10-47d7-b91d-d7f6081a63f1
"""

import os
import sys
import argparse
import webbrowser
from urllib.parse import urlencode, parse_qs, urlparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client
import requests

load_dotenv()


class OuraOAuth2Flow:
    """Gère le flux OAuth2 Oura en ligne de commande"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        
        # Charger les configs
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            print("❌ Variables d'environnement manquantes (SUPABASE_URL, SUPABASE_SERVICE_KEY)")
            sys.exit(1)
        
        self.client = create_client(self.supabase_url, self.supabase_key)
        
        # URLs Oura OAuth2
        self.auth_url = "https://cloud.ouraring.com/oauth/authorize"
        self.token_url = "https://api.ouraring.com/oauth/token"
        
        # Charger les credentials depuis Supabase ou .env
        self.load_credentials()
    
    def load_credentials(self):
        """Charge les credentials OAuth2 depuis Supabase ou .env"""
        
        print(f"\n{'='*60}")
        print(f"Chargement des credentials OAuth2 Oura")
        print(f"{'='*60}\n")
        
        # D'abord, essayer de charger depuis external_identities
        try:
            result = self.client.table("external_identities").select("metadata").eq("supabase_user_id", self.user_id).eq("provider_system", "oura").execute()
            
            if result.data:
                metadata = result.data[0].get('metadata', {})
                client_id = metadata.get('oauth2_client_id')
                client_secret = metadata.get('oauth2_client_secret')
                
                if client_id and client_secret:
                    self.client_id = client_id
                    self.client_secret = client_secret
                    print(f"✓ Credentials chargées depuis Supabase (utilisateur spécifique)")
                    print(f"  Client ID: {client_id}")
                    print(f"  Client Secret: {client_secret[:10]}...")
                    return
        except Exception as e:
            print(f"⚠️  Impossible de charger depuis Supabase: {e}")
        
        # Sinon, utiliser les credentials du .env
        self.client_id = os.getenv("OURA_CLIENT_ID")
        self.client_secret = os.getenv("OURA_CLIENT_SECRET")
        
        if not self.client_id or not self.client_secret:
            print("❌ Aucune credential OAuth2 trouvée")
            print("   Solutions:")
            print("   1. Ajouter dans .env: OURA_CLIENT_ID et OURA_CLIENT_SECRET")
            print(f"   2. Exécuter: python3 add_user_oura_credentials.py --user-id {self.user_id} --client-id ... --client-secret ...")
            sys.exit(1)
        
        print(f"✓ Credentials chargées depuis .env (globales)")
        print(f"  Client ID: {self.client_id}")
        print(f"  Client Secret: {self.client_secret[:10]}...")
    
    def generate_auth_url(self):
        """Génère l'URL d'autorisation OAuth2"""
        
        # Utiliser le redirect URI configuré dans l'application Oura
        redirect_uri = os.getenv("OURA_REDIRECT_URI", "http://localhost:9000/api/oura/callback")
        
        # Scopes Oura requis (séparés par des espaces)
        # Documentation: https://cloud.ouraring.com/v2/docs#section/Scopes
        scope = "email personal daily heartrate workout tag session spo2 rest_mode_period sleep_time ring_configuration"
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": f"user_{self.user_id[:8]}"  # État pour sécurité
        }
        
        auth_url = f"{self.auth_url}?{urlencode(params)}"
        return auth_url, redirect_uri
    
    def exchange_code_for_tokens(self, code: str, redirect_uri: str):
        """Échange le code d'autorisation contre des tokens"""
        
        print(f"\n{'='*60}")
        print(f"Échange du code contre les tokens")
        print(f"{'='*60}\n")
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            response = requests.post(self.token_url, data=data)
            response.raise_for_status()
            
            tokens = response.json()
            
            print(f"✅ Tokens obtenus avec succès!")
            print(f"   Access Token: {tokens['access_token'][:20]}...")
            print(f"   Refresh Token: {tokens.get('refresh_token', 'N/A')[:20]}...")
            print(f"   Expires In: {tokens.get('expires_in', 'N/A')} secondes")
            
            return tokens
            
        except requests.exceptions.HTTPError as e:
            print(f"❌ Erreur lors de l'échange du code: {e}")
            print(f"   Réponse: {e.response.text}")
            sys.exit(1)
    
    def save_tokens(self, tokens: dict):
        """Sauvegarde les tokens dans Supabase"""
        
        print(f"\n{'='*60}")
        print(f"Sauvegarde des tokens dans Supabase")
        print(f"{'='*60}\n")
        
        # Calculer la date d'expiration
        expires_in = tokens.get('expires_in', 86400)  # Par défaut 24h
        expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
        
        metadata = {
            "access_token": tokens['access_token'],
            "refresh_token": tokens.get('refresh_token'),
            "expires_at": expires_at,
            "token_type": tokens.get('token_type', 'Bearer'),
            "auth_method": "oauth2",
            "configured_at": datetime.utcnow().isoformat(),
            "oauth2_client_id": self.client_id,
            "oauth2_client_secret": self.client_secret
        }
        
        try:
            # Vérifier si une entrée existe déjà
            existing = self.client.table("external_identities").select("*").eq("supabase_user_id", self.user_id).eq("provider_system", "oura").execute()
            
            if existing.data:
                # Mettre à jour
                result = self.client.table("external_identities").update({
                    "metadata": metadata,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", existing.data[0]['id']).execute()
                
                print(f"✅ Tokens mis à jour dans external_identities")
            else:
                # Créer une nouvelle entrée
                external_user_id = f"oura_oauth_{self.user_id[:8]}"
                
                result = self.client.table("external_identities").insert({
                    "supabase_user_id": self.user_id,
                    "provider_system": "oura",
                    "external_user_id": external_user_id,
                    "metadata": metadata,
                    "is_active": True
                }).execute()
                
                print(f"✅ Nouvelle entrée créée dans external_identities")
            
            print(f"   User ID: {self.user_id}")
            print(f"   Access Token expire le: {expires_at}")
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def run(self):
        """Exécute le flux OAuth2 complet"""
        
        print(f"\n{'='*70}")
        print(f"  FLUX OAUTH2 OURA - CONFIGURATION INTERACTIVE")
        print(f"{'='*70}\n")
        print(f"User ID: {self.user_id}\n")
        
        # Étape 1 : Générer l'URL d'autorisation
        auth_url, redirect_uri = self.generate_auth_url()
        
        print(f"{'='*60}")
        print(f"ÉTAPE 1/3 : Autorisation Oura")
        print(f"{'='*60}\n")
        print(f"Je vais ouvrir votre navigateur sur la page d'autorisation Oura.")
        print(f"Si le navigateur ne s'ouvre pas, copiez cette URL :\n")
        print(f"{auth_url}\n")
        
        input("Appuyez sur ENTRÉE pour ouvrir le navigateur...")
        
        # Ouvrir le navigateur
        try:
            webbrowser.open(auth_url)
            print(f"✓ Navigateur ouvert")
        except:
            print(f"⚠️  Impossible d'ouvrir le navigateur automatiquement")
            print(f"   Ouvrez manuellement cette URL dans votre navigateur")
        
        print(f"\n{'='*60}")
        print(f"ÉTAPE 2/3 : Obtenir le code d'autorisation")
        print(f"{'='*60}\n")
        print(f"Après avoir autorisé l'accès sur Oura Cloud :")
        print(f"1. Vous serez redirigé vers une page d'erreur (c'est normal)")
        print(f"2. L'URL contiendra un paramètre 'code=' ")
        print(f"3. Exemple: http://localhost:8000/...?code=XXXXXXX")
        print(f"4. Copiez UNIQUEMENT la valeur du code\n")
        
        code = input("Collez le code ici : ").strip()
        
        if not code:
            print("❌ Code manquant")
            sys.exit(1)
        
        print(f"\n✓ Code reçu: {code[:20]}...")
        
        # Étape 2 : Échanger le code contre des tokens
        tokens = self.exchange_code_for_tokens(code, redirect_uri)
        
        # Étape 3 : Sauvegarder les tokens
        self.save_tokens(tokens)
        
        print(f"\n{'='*70}")
        print(f"✅ CONFIGURATION OAUTH2 TERMINÉE AVEC SUCCÈS!")
        print(f"{'='*70}\n")
        print(f"Prochaines étapes:")
        print(f"  python3 run_oura_sync.py --user-id {self.user_id}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Flux OAuth2 Oura interactif"
    )
    parser.add_argument(
        '--user-id',
        required=True,
        help='UUID de l\'utilisateur Supabase'
    )
    
    args = parser.parse_args()
    
    flow = OuraOAuth2Flow(user_id=args.user_id)
    flow.run()


if __name__ == "__main__":
    main()
