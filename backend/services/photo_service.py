"""
PhotoService - Upload et gestion des photos de repas
Supabase Storage + analyse IA optionnelle (FatSecret Image Recognition)
"""
import logging
import os
import uuid
from typing import Dict, Any, Optional, BinaryIO
from datetime import datetime

from supabase import Client as SupabaseClient
from fatsecret_client_v2 import FatSecretClient

logger = logging.getLogger(__name__)


class PhotoService:
    """Service pour upload et analyse des photos de repas"""
    
    def __init__(
        self,
        supabase: SupabaseClient,
        fatsecret: Optional[FatSecretClient] = None,
        storage_bucket: str = "food-photos"
    ):
        self.supabase = supabase
        self.fatsecret = fatsecret
        self.storage_bucket = storage_bucket
    
    # =====================================================
    # UPLOAD PHOTO
    # =====================================================
    
    def upload_food_photo(
        self,
        user_id: str,
        food_log_id: str,
        file_data: BinaryIO,
        filename: str,
        mime_type: str = "image/jpeg",
        analyze: bool = False
    ) -> Dict[str, Any]:
        """
        Upload une photo de repas dans Supabase Storage
        
        Args:
            user_id: UUID utilisateur
            food_log_id: UUID du food_log associé
            file_data: Données binaires du fichier
            filename: Nom du fichier original
            mime_type: Type MIME
            analyze: Si True, lance l'analyse IA
        
        Returns:
            {
                "photo_id": "...",
                "storage_path": "...",
                "public_url": "...",
                "analysis_status": "pending|success|skipped"
            }
        """
        logger.info(f"Uploading photo for food_log {food_log_id}")
        
        # Générer path unique
        ext = self._get_file_extension(filename, mime_type)
        photo_id = str(uuid.uuid4())
        storage_path = f"{user_id}/{food_log_id}/{photo_id}{ext}"
        
        # Upload vers Supabase Storage
        try:
            # Lire les données du fichier
            file_bytes = file_data.read() if hasattr(file_data, 'read') else file_data
            file_size = len(file_bytes)
            
            # Upload
            self.supabase.storage.from_(self.storage_bucket).upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": mime_type}
            )
            
            logger.info(f"Photo uploaded: {storage_path} ({file_size} bytes)")
            
        except Exception as e:
            logger.error(f"Failed to upload photo: {e}")
            raise ValueError(f"Upload failed: {e}")
        
        # Créer entrée dans food_photos
        photo_data = {
            "id": photo_id,
            "food_log_id": food_log_id,
            "user_id": user_id,
            "storage_path": storage_path,
            "storage_bucket": self.storage_bucket,
            "file_size_bytes": file_size,
            "mime_type": mime_type,
            "taken_at": datetime.utcnow().isoformat(),
            "analysis_status": "pending" if analyze else "skipped"
        }
        
        self.supabase.table("food_photos").insert(photo_data).execute()
        
        # Obtenir URL publique
        public_url = self._get_public_url(storage_path)
        
        # Lancer analyse IA si demandé
        analysis_result = None
        if analyze and self.fatsecret:
            try:
                analysis_result = self._analyze_photo(photo_id, file_bytes)
            except Exception as e:
                logger.error(f"Photo analysis failed: {e}")
        
        return {
            "photo_id": photo_id,
            "storage_path": storage_path,
            "public_url": public_url,
            "file_size_bytes": file_size,
            "analysis_status": photo_data["analysis_status"],
            "analysis": analysis_result
        }
    
    def _get_file_extension(self, filename: str, mime_type: str) -> str:
        """Détermine l'extension du fichier"""
        # Essayer depuis filename
        if "." in filename:
            return filename[filename.rfind("."):]
        
        # Fallback depuis mime_type
        mime_to_ext = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "image/heic": ".heic",
            "image/heif": ".heif"
        }
        return mime_to_ext.get(mime_type, ".jpg")
    
    def _get_public_url(self, storage_path: str) -> str:
        """Génère l'URL publique Supabase Storage"""
        try:
            return self.supabase.storage.from_(self.storage_bucket).get_public_url(storage_path)
        except Exception as e:
            logger.warning(f"Could not get public URL: {e}")
            return f"{self.storage_bucket}/{storage_path}"
    
    # =====================================================
    # ANALYSE IA (FATSECRET IMAGE RECOGNITION)
    # =====================================================
    
    def _analyze_photo(self, photo_id: str, image_data: bytes) -> Dict[str, Any]:
        """
        Analyse une photo avec FatSecret Image Recognition API
        
        Note: Nécessite un plan FatSecret avec accès à l'API d'analyse d'images
        Endpoint : image.recognition (non documenté publiquement, peut nécessiter contact FatSecret)
        
        Pour MVP : retourne un placeholder, à implémenter si accès disponible
        
        Returns:
            {"items": [...], "confidence": 0.85, "provider": "fatsecret"}
        """
        logger.info(f"Analyzing photo {photo_id} (placeholder)")
        
        # TODO: Implémenter appel réel à FatSecret Image Recognition API
        # Format attendu de la réponse :
        # {
        #     "recognized_foods": [
        #         {"food_name": "Apple", "food_id": 35718, "confidence": 0.92},
        #         {"food_name": "Banana", "food_id": 36121, "confidence": 0.87}
        #     ]
        # }
        
        # Pour l'instant, marquer comme "skipped" (pas d'API disponible en MVP)
        self.supabase.table("food_photos").update({
            "analysis_status": "skipped",
            "analysis": {
                "message": "Image recognition not available in current FatSecret plan",
                "provider": "fatsecret"
            }
        }).eq("id", photo_id).execute()
        
        return {
            "status": "skipped",
            "message": "Image recognition requires FatSecret Premium plan"
        }
    
    def analyze_existing_photo(self, photo_id: str) -> Dict[str, Any]:
        """
        Analyse a posteriori une photo déjà uploadée
        Utile si analyse initiale a échoué ou si fonctionnalité activée plus tard
        """
        logger.info(f"Analyzing existing photo {photo_id}")
        
        # Récupérer photo
        photo = self.supabase.table("food_photos")\
            .select("*")\
            .eq("id", photo_id)\
            .single()\
            .execute()
        
        if not photo.data:
            raise ValueError(f"Photo not found: {photo_id}")
        
        # Télécharger depuis Storage
        storage_path = photo.data["storage_path"]
        try:
            file_bytes = self.supabase.storage.from_(self.storage_bucket)\
                .download(storage_path)
            
            # Analyser
            result = self._analyze_photo(photo_id, file_bytes)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze photo {photo_id}: {e}")
            raise
    
    # =====================================================
    # RÉCUPÉRATION
    # =====================================================
    
    def get_photo_url(self, photo_id: str, expires_in: int = 3600) -> str:
        """
        Génère une URL signée pour accès photo
        
        Args:
            photo_id: UUID de la photo
            expires_in: Durée validité en secondes (défaut 1h)
        
        Returns:
            URL signée temporaire
        """
        photo = self.supabase.table("food_photos")\
            .select("storage_path")\
            .eq("id", photo_id)\
            .single()\
            .execute()
        
        if not photo.data:
            raise ValueError(f"Photo not found: {photo_id}")
        
        storage_path = photo.data["storage_path"]
        
        try:
            # Supabase Storage signed URL
            signed_url = self.supabase.storage.from_(self.storage_bucket)\
                .create_signed_url(storage_path, expires_in)
            return signed_url["signedURL"]
        except Exception as e:
            logger.warning(f"Could not create signed URL: {e}")
            # Fallback : public URL (si bucket est public)
            return self._get_public_url(storage_path)
    
    def delete_photo(self, photo_id: str, user_id: str) -> bool:
        """
        Supprime une photo (Storage + DB)
        Vérifie que l'utilisateur est propriétaire
        """
        logger.info(f"Deleting photo {photo_id}")
        
        # Récupérer photo et vérifier ownership
        photo = self.supabase.table("food_photos")\
            .select("*")\
            .eq("id", photo_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        
        if not photo.data:
            raise ValueError(f"Photo not found or unauthorized: {photo_id}")
        
        storage_path = photo.data["storage_path"]
        
        # Supprimer de Storage
        try:
            self.supabase.storage.from_(self.storage_bucket).remove([storage_path])
            logger.info(f"Photo deleted from storage: {storage_path}")
        except Exception as e:
            logger.error(f"Failed to delete photo from storage: {e}")
        
        # Supprimer de DB
        self.supabase.table("food_photos").delete().eq("id", photo_id).execute()
        
        return True
    
    # =====================================================
    # ALTERNATIVE : ANALYSE IA EXTERNE (FUTURE)
    # =====================================================
    
    def analyze_with_external_service(
        self,
        photo_id: str,
        provider: str = "passio"
    ) -> Dict[str, Any]:
        """
        Analyse photo avec un service externe (Passio, LogMeal, Clarifai...)
        
        À implémenter si FatSecret Image Recognition non disponible
        
        Providers possibles :
        - Passio Nutrition AI (https://www.passiolife.com/)
        - LogMeal Food Recognition API (https://logmeal.com/)
        - Clarifai Food Model (https://www.clarifai.com/)
        - Google Cloud Vision API (labels génériques)
        
        Returns:
            {"items": [...], "confidence": 0.85, "provider": "passio"}
        """
        logger.info(f"External analysis not implemented (provider: {provider})")
        
        # Placeholder pour future implémentation
        self.supabase.table("food_photos").update({
            "analysis_status": "skipped",
            "analysis": {
                "message": f"External provider '{provider}' not configured",
                "provider": provider
            }
        }).eq("id", photo_id).execute()
        
        return {
            "status": "skipped",
            "message": f"External analysis provider '{provider}' not configured"
        }
