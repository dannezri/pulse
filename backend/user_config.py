"""
Utilitaire pour récupérer l'UUID utilisateur de manière centralisée.
Tous les scripts doivent utiliser ce module au lieu de coder en dur les UUIDs.
"""
import os
import sys


def get_dev_user_uuid(required: bool = True) -> str | None:
    """
    Récupère l'UUID de l'utilisateur de développement depuis les variables d'environnement.
    
    Args:
        required: Si True, quitte le programme si l'UUID n'est pas défini
        
    Returns:
        L'UUID de l'utilisateur ou None si non défini et non requis
    """
    user_uuid = os.getenv("DEV_USER_UUID")
    
    if not user_uuid and required:
        print("❌ Erreur: DEV_USER_UUID doit être défini dans les variables d'environnement")
        print()
        print("Pour définir votre UUID utilisateur:")
        print("  export DEV_USER_UUID=votre-uuid-supabase")
        print()
        print("Exemple:")
        print("  export DEV_USER_UUID=bee9a055-9b10-47d7-b91d-d7f6081a63f1")
        print()
        sys.exit(1)
    
    return user_uuid


def get_test_user_uuid() -> str:
    """
    Récupère l'UUID pour les tests.
    Alias pour get_dev_user_uuid() pour plus de clarté dans les scripts de test.
    """
    return get_dev_user_uuid(required=True)
