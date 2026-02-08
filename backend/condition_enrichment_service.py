"""
Service d'enrichissement des conditions de santé avec Smart Fallback GPT-4o

Stratégie:
1. Chercher dans condition_energy_impacts (cache local)
2. Si non trouvé → Appeler GPT-4o pour estimer l'impact
3. UPSERT automatiquement dans la DB pour future réutilisation
"""

import logging
import json
from typing import Dict, Optional
from datetime import datetime, timezone
from llm_client import LLMClient

logger = logging.getLogger(__name__)


class ConditionEnrichmentService:
    """
    Service pour enrichir les conditions de santé non répertoriées
    """
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    async def enrich_condition(
        self,
        condition_name: str,
        icd11_code: str,
        category: Optional[str] = None
    ) -> Dict:
        """
        Enrichit une condition avec Smart Fallback GPT-4o
        
        Workflow:
        1. Chercher dans condition_energy_impacts (cache)
        2. Si non trouvé → GPT-4o pour decay_rate + energy_malus
        3. UPSERT automatiquement dans DB
        
        Args:
            condition_name: Nom de la condition (ex: "Obstruction de sinus nasal")
            icd11_code: Code ICD-11
            category: Catégorie optionnelle
            
        Returns:
            Dict avec {decay_rate, energy_malus, severity, source, updated}
        """
        try:
            logger.info(f"[AI_ENRICHMENT] 🔍 Enrichissement condition: {condition_name}")
            
            # 1. Chercher d'abord dans la DB locale
            impact_data = await self._get_local_impact(icd11_code)
            
            if impact_data:
                logger.info(f"[AI_ENRICHMENT] ✅ Trouvé en DB: {condition_name}")
                return {
                    'condition_name': condition_name,
                    'icd11_code': icd11_code,
                    'decay_rate': impact_data['decay_rate'],
                    'energy_malus': impact_data['energy_malus'],
                    'severity': impact_data['severity'],
                    'source': 'local_database',
                    'updated': False
                }
            
            # 2. Pas trouvé → Appeler GPT-4o
            logger.info(f"[AI_ENRICHMENT] 🤖 Appel GPT-4o pour: {condition_name}")
            ai_data = await self._enrich_with_gpt4o(condition_name, icd11_code, category)
            
            if not ai_data or 'error' in ai_data:
                logger.error(f"[AI_ENRICHMENT] ❌ Échec enrichissement IA: {condition_name}")
                # Utiliser des valeurs neutres par défaut
                return {
                    'condition_name': condition_name,
                    'icd11_code': icd11_code,
                    'decay_rate': 0.04,  # Normal
                    'energy_malus': 0,
                    'severity': 'unknown',
                    'source': 'default_fallback',
                    'updated': False
                }
            
            # 3. UPSERT dans condition_energy_impacts
            await self._persist_condition_data(ai_data, icd11_code, category)
            logger.info(f"[AI_ENRICHMENT] 💾 Nouvelle donnée enregistrée pour : {condition_name}")
            
            return {
                'condition_name': condition_name,
                'icd11_code': icd11_code,
                'decay_rate': ai_data['decay_rate'],
                'energy_malus': ai_data['energy_malus'],
                'severity': ai_data['severity'],
                'source': 'ai_generated',
                'updated': True
            }
            
        except Exception as e:
            logger.error(f"[AI_ENRICHMENT] Erreur enrichissement condition: {e}")
            # Fallback sécurisé
            return {
                'condition_name': condition_name,
                'icd11_code': icd11_code,
                'decay_rate': 0.04,
                'energy_malus': 0,
                'severity': 'unknown',
                'source': 'error_fallback',
                'updated': False
            }
    
    async def _get_local_impact(self, icd11_code: str) -> Optional[Dict]:
        """
        Cherche l'impact dans condition_energy_impacts
        """
        try:
            result = self.supabase.client.table('condition_energy_impacts')\
                .select('*')\
                .eq('icd11_code', icd11_code)\
                .eq('is_active', True)\
                .maybe_single()\
                .execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.error(f"[AI_ENRICHMENT] Erreur recherche locale condition: {e}")
            return None
    
    async def _enrich_with_gpt4o(
        self,
        condition_name: str,
        icd11_code: str,
        category: Optional[str]
    ) -> Dict:
        """
        Enrichit une condition via GPT-4o
        
        Returns:
            Dict avec decay_rate, energy_malus, severity, justification
        """
        try:
            llm = LLMClient()
            
            prompt = f"""Tu es une base de connaissances médicale experte en fatigue et énergie clinique.

Condition: {condition_name}
Code ICD-11: {icd11_code}
Catégorie: {category or 'Non spécifiée'}

Analyse l'impact physiologique de cette condition sur l'énergie quotidienne.

Fournis en JSON UNIQUEMENT:
{{
  "decay_rate": "Taux de décroissance horaire (float, 0.04=normal, 0.05=légère, 0.06=modérée, 0.08=haute, 0.10=sévère)",
  "energy_malus": "Malus au réveil (int, 0 à -50, ex: -5 pour sinus bouchés, -10 pour inflammation modérée)",
  "variability": "Variabilité jour à jour (float, 0.0-1.0)",
  "severity": "low|moderate|high|severe",
  "category": "respiratory|inflammatory|chronic_pain|mental|neurological|metabolic|other",
  "justification": "2-3 phrases expliquant le raisonnement physiologique"
}}

Basé sur études cliniques, échelles de fatigue (FSS, FACIT-F), et physiologie."""

            response = llm.generate_insight(prompt, temperature=0.3, max_tokens=400)
            content = response.get('content', '{}')
            
            # Parse JSON
            ai_data = json.loads(content.strip())
            
            # Validation et ajustements
            ai_data['decay_rate'] = max(0.04, min(0.15, float(ai_data.get('decay_rate', 0.04))))
            ai_data['energy_malus'] = max(-50, min(0, int(ai_data.get('energy_malus', 0))))
            
            return ai_data
            
        except json.JSONDecodeError as e:
            logger.error(f"[AI_ENRICHMENT] JSON invalide de GPT-4o: {e}")
            return {'error': 'Invalid JSON from GPT-4o'}
        except Exception as e:
            logger.error(f"[AI_ENRICHMENT] Erreur GPT-4o condition: {e}")
            return {'error': str(e)}
    
    async def _persist_condition_data(
        self,
        ai_data: Dict,
        icd11_code: str,
        category: Optional[str]
    ):
        """
        UPSERT les données IA dans condition_energy_impacts
        """
        try:
            insert_data = {
                'icd11_code': icd11_code,
                'condition_name': ai_data.get('condition_name', 'Unknown'),
                'decay_rate': ai_data.get('decay_rate', 0.04),
                'energy_malus': ai_data.get('energy_malus', 0),
                'variability': ai_data.get('variability', 0.2),
                'severity': ai_data.get('severity', 'moderate'),
                'category': ai_data.get('category', category or 'other'),
                'evidence_level': 'ai_generated',
                'source': f'GPT-4o enrichment - {datetime.now(timezone.utc).isoformat()}',
                'notes': ai_data.get('justification', ''),
                'is_active': True
            }
            
            # UPSERT (ON CONFLICT icd11_code DO UPDATE)
            self.supabase.client.table('condition_energy_impacts')\
                .upsert(insert_data, on_conflict='icd11_code')\
                .execute()
            
            logger.info(f"[AI_ENRICHMENT] ✅ Persisté condition: {icd11_code}")
            
        except Exception as e:
            logger.error(f"[AI_ENRICHMENT] Erreur persistance condition: {e}")
            raise
