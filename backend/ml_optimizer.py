"""
Machine Learning Optimizer - PWA (Personalized Weight Adjustment)

Ce service implémente une boucle d'apprentissage adaptatif pour ajuster
les poids des facteurs (médicaments, conditions) en fonction du feedback utilisateur.

Algorithme: Descente de gradient stochastique (SGD) simplifiée
Formule: W_new = W_old + η × (S_user - S_calc) × φ

Où:
- η (Learning Rate) = 0.05 (pour éviter les changements brusques)
- φ (Direction) = -1 pour les malus, +1 pour les bonus
- W_new est contraint dans [0.5, 2.0]
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from supabase import Client

logger = logging.getLogger(__name__)


class MLOptimizer:
    """
    Optimiseur ML pour ajuster les poids personnalisés en fonction du feedback utilisateur.
    """
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        
        # Hyperparamètres
        self.LEARNING_RATE = 0.05  # η
        self.MIN_WEIGHT = 0.5
        self.MAX_WEIGHT = 2.0
        self.MIN_FEEDBACKS_FOR_ADJUSTMENT = 3  # Nombre de feedbacks avant ajustement
        self.CONFIDENCE_THRESHOLD = 0.7  # Seuil de confiance pour appliquer un ajustement
    
    async def process_feedback(
        self,
        user_id: str,
        system_score: float,
        user_score: int,
        active_factors: Dict[str, List[str]]
    ) -> Dict:
        """
        Traite un feedback utilisateur et ajuste les poids si nécessaire.
        
        Args:
            user_id: UUID de l'utilisateur
            system_score: Score calculé par le système (0-100)
            user_score: Score ressenti par l'utilisateur (0-100)
            active_factors: Dict avec 'medications' et 'conditions' actifs
            
        Returns:
            Dict avec le statut du traitement et les ajustements effectués
        """
        try:
            # 1. Stocker le feedback
            feedback_id = await self._store_feedback(
                user_id, system_score, user_score, active_factors
            )
            
            logger.info(f"[MLOptimizer] 📝 Feedback reçu: user={user_id}, system={system_score:.1f}, user={user_score}")
            
            # 2. Calculer l'erreur
            error = user_score - system_score
            
            # Si l'erreur est faible (< 10%), pas besoin d'ajustement
            if abs(error) < 10:
                logger.info(f"[MLOptimizer] ✅ Erreur faible ({error:.1f}), pas d'ajustement nécessaire")
                return {
                    "status": "ok",
                    "error": error,
                    "adjustments": []
                }
            
            # 3. Ajuster les poids des facteurs actifs
            adjustments = []
            
            # Ajuster les médicaments
            for atc_code in active_factors.get('medications', []):
                adjustment = await self._adjust_weight(
                    user_id, 'medication', atc_code, error
                )
                if adjustment:
                    adjustments.append(adjustment)
            
            # Ajuster les conditions
            for icd_code in active_factors.get('conditions', []):
                adjustment = await self._adjust_weight(
                    user_id, 'condition', icd_code, error
                )
                if adjustment:
                    adjustments.append(adjustment)
            
            # 4. Marquer le feedback comme traité
            await self._mark_feedback_processed(feedback_id)
            
            logger.info(f"[MLOptimizer] ✅ {len(adjustments)} ajustements appliqués")
            
            return {
                "status": "ok",
                "error": error,
                "adjustments": adjustments
            }
            
        except Exception as e:
            logger.error(f"[MLOptimizer] ❌ Erreur traitement feedback: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _store_feedback(
        self,
        user_id: str,
        system_score: float,
        user_score: int,
        active_factors: Dict
    ) -> str:
        """
        Stocke le feedback dans la table user_feedback.
        """
        result = self.supabase.table('user_feedback').insert({
            'user_id': user_id,
            'system_score': system_score,
            'user_score': user_score,
            # 'error' est une colonne générée, ne pas l'insérer manuellement
            'active_factors': active_factors,
            'processed': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        }).execute()
        
        return result.data[0]['id']
    
    async def _adjust_weight(
        self,
        user_id: str,
        factor_type: str,
        factor_code: str,
        error: float
    ) -> Optional[Dict]:
        """
        Ajuste le poids d'un facteur spécifique en utilisant SGD.
        
        Formule: W_new = W_old + η × error × φ / 100
        
        Le diviseur 100 normalise l'erreur (qui est en 0-100) pour éviter
        des ajustements trop brusques.
        """
        try:
            # 1. Récupérer le poids actuel (ou créer une entrée)
            weight_entry = await self._get_or_create_weight(
                user_id, factor_type, factor_code
            )
            
            current_weight = weight_entry['weight_multiplier']
            feedback_count = weight_entry['feedback_count']
            
            # 2. Déterminer la direction φ
            # Pour les malus (médicaments sédatifs, conditions négatives), φ = -1
            # Si l'utilisateur se sent MIEUX que prévu (error > 0), on RÉDUIT le malus
            phi = -1.0  # Par défaut, les facteurs sont des malus
            
            # 3. Calculer le nouvel ajustement avec SGD
            # error / 100 normalise l'erreur (0-100) en (0-1)
            adjustment = self.LEARNING_RATE * (error / 100) * phi
            
            new_weight = current_weight + adjustment
            
            # 4. Appliquer les contraintes
            new_weight = max(self.MIN_WEIGHT, min(self.MAX_WEIGHT, new_weight))
            
            # 5. Calculer la confiance basée sur le nombre de feedbacks
            # Confiance = min(1.0, feedback_count / 10)
            confidence = min(1.0, (feedback_count + 1) / 10)
            
            # 6. Ne pas appliquer l'ajustement si pas assez de feedbacks
            if feedback_count < self.MIN_FEEDBACKS_FOR_ADJUSTMENT:
                logger.info(
                    f"[MLOptimizer] ⏸️ {factor_type}:{factor_code} - "
                    f"Pas assez de feedbacks ({feedback_count}/{self.MIN_FEEDBACKS_FOR_ADJUSTMENT})"
                )
                # Mettre à jour le compteur mais pas le poids
                await self._update_weight_count(weight_entry['id'], feedback_count + 1)
                return None
            
            # 7. Mettre à jour le poids dans la base
            await self._update_weight(
                weight_entry['id'],
                new_weight,
                feedback_count + 1,
                confidence,
                current_weight,
                adjustment
            )
            
            logger.info(
                f"[MLOptimizer] 🎯 {factor_type}:{factor_code} "
                f"weight: {current_weight:.3f} → {new_weight:.3f} "
                f"(Δ{adjustment:+.3f}, confidence={confidence:.2f})"
            )
            
            return {
                "factor_type": factor_type,
                "factor_code": factor_code,
                "old_weight": current_weight,
                "new_weight": new_weight,
                "adjustment": adjustment,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"[MLOptimizer] Erreur ajustement {factor_type}:{factor_code}: {e}")
            return None
    
    async def _get_or_create_weight(
        self,
        user_id: str,
        factor_type: str,
        factor_code: str
    ) -> Dict:
        """
        Récupère ou crée une entrée de poids personnalisé.
        """
        # Tenter de récupérer
        result = self.supabase.table('personalized_weights')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('factor_type', factor_type)\
            .eq('factor_code', factor_code)\
            .execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        
        # Créer si n'existe pas
        # Récupérer le nom du facteur
        factor_name = await self._get_factor_name(factor_type, factor_code)
        
        result = self.supabase.table('personalized_weights').insert({
            'user_id': user_id,
            'factor_type': factor_type,
            'factor_code': factor_code,
            'factor_name': factor_name,
            'weight_multiplier': 1.0,
            'feedback_count': 0,
            'confidence_score': 0.0,
            'is_active': True
        }).execute()
        
        return result.data[0]
    
    async def _get_factor_name(self, factor_type: str, factor_code: str) -> str:
        """
        Récupère le nom lisible d'un facteur depuis les tables de référence.
        """
        try:
            if factor_type == 'medication':
                result = self.supabase.table('medication_energy_impacts')\
                    .select('medication_name')\
                    .eq('atc_code', factor_code)\
                    .limit(1)\
                    .execute()
                if result.data:
                    return result.data[0]['medication_name']
            
            elif factor_type == 'condition':
                result = self.supabase.table('condition_energy_impacts')\
                    .select('condition_name')\
                    .eq('icd11_code', factor_code)\
                    .limit(1)\
                    .execute()
                if result.data:
                    return result.data[0]['condition_name']
        except:
            pass
        
        return factor_code
    
    async def _update_weight(
        self,
        weight_id: str,
        new_weight: float,
        feedback_count: int,
        confidence: float,
        old_weight: float,
        adjustment: float
    ):
        """
        Met à jour un poids personnalisé avec historique.
        """
        # Construire l'entrée d'historique
        history_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "old_weight": old_weight,
            "new_weight": new_weight,
            "adjustment": adjustment,
            "feedback_count": feedback_count
        }
        
        # Récupérer l'historique actuel
        result = self.supabase.table('personalized_weights')\
            .select('adjustment_history')\
            .eq('id', weight_id)\
            .execute()
        
        current_history = result.data[0].get('adjustment_history', [])
        current_history.append(history_entry)
        
        # Limiter l'historique aux 50 dernières entrées
        if len(current_history) > 50:
            current_history = current_history[-50:]
        
        # Mettre à jour
        self.supabase.table('personalized_weights').update({
            'weight_multiplier': new_weight,
            'feedback_count': feedback_count,
            'confidence_score': confidence,
            'adjustment_history': current_history,
            'last_adjustment': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', weight_id).execute()
    
    async def _update_weight_count(self, weight_id: str, feedback_count: int):
        """
        Met à jour uniquement le compteur de feedbacks (sans changer le poids).
        """
        self.supabase.table('personalized_weights').update({
            'feedback_count': feedback_count,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', weight_id).execute()
    
    async def _mark_feedback_processed(self, feedback_id: str):
        """
        Marque un feedback comme traité.
        """
        self.supabase.table('user_feedback').update({
            'processed': True,
            'processed_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', feedback_id).execute()
    
    async def get_adjustment_stats(self, user_id: str) -> Dict:
        """
        Récupère les statistiques d'ajustement pour un utilisateur.
        """
        result = self.supabase.table('personalized_weights')\
            .select('factor_type, factor_name, weight_multiplier, feedback_count, confidence_score')\
            .eq('user_id', user_id)\
            .eq('is_active', True)\
            .execute()
        
        return {
            "total_factors": len(result.data) if result.data else 0,
            "factors": result.data or []
        }
