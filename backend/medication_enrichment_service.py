"""
Service d'enrichissement des médicaments avec Smart Fallback GPT-4o
Stratégie:
1. Chercher dans medication_energy_impacts (cache local)
2. Si non trouvé → Appeler GPT-4o pour enrichir
3. UPSERT automatiquement dans la DB pour future réutilisation
"""

import logging
import httpx
import json
from typing import Dict, Optional, List
from datetime import datetime, timezone
from llm_client import LLMClient

logger = logging.getLogger(__name__)


class MedicationEnrichmentService:
    """
    Service pour enrichir les informations sur les médicaments
    
    Workflow:
    1. Validation du nom via API Médicaments FR
    2. Enrichissement pharmacocinétique via DB locale
    3. Fallback IA si médicament non répertorié
    """
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.api_base_url = "https://data.gouv.fr/api/1/datasets/base-de-donnees-publique-des-medicaments-1"
        # Alternative API REST moderne
        self.api_rest_url = "https://api-medicaments.fr"
    
    async def enrich_medication(
        self,
        medication_name: str,
        user_id: str,
        medication_id: Optional[str] = None,
        dosage: Optional[str] = None
    ) -> Dict:
        """
        Enrichit un médicament avec Smart Fallback GPT-4o
        
        Workflow:
        1. Chercher dans medication_energy_impacts (cache)
        2. Si non trouvé → GPT-4o pour ATC + pharmacocinétique
        3. UPSERT automatiquement dans DB
        4. UPDATE user_medications avec ATC code
        
        Args:
            medication_name: Nom du médicament (ex: "Sertraline")
            user_id: UUID utilisateur
            medication_id: UUID du médicament dans user_medications
            dosage: Dosage optionnel
            
        Returns:
            Dict avec {atc_code, pharmacokinetics, source, updated}
        """
        try:
            logger.info(f"[AI_ENRICHMENT] 🔍 Enrichissement: {medication_name}")
            
            # 1. Chercher d'abord dans la DB locale
            pharma_data = await self._get_local_pharmacokinetics_by_name(medication_name)
            
            if pharma_data:
                logger.info(f"[AI_ENRICHMENT] ✅ Trouvé en DB: {medication_name}")
                
                # Mettre à jour user_medications avec l'ATC code
                if medication_id and pharma_data.get('atc_code'):
                    await self._update_user_medication_atc(
                        medication_id,
                        pharma_data['atc_code'],
                        pharma_data['active_substance']
                    )
                
                return {
                    'medication_name': medication_name,
                    'atc_code': pharma_data.get('atc_code'),
                    'active_substance': pharma_data.get('active_substance'),
                    'pharmacokinetics': pharma_data,
                    'source': 'local_database',
                    'updated': True if medication_id else False
                }
            
            # 2. Pas trouvé → Appeler GPT-4o
            logger.info(f"[AI_ENRICHMENT] 🤖 Appel GPT-4o pour: {medication_name}")
            ai_data = await self._enrich_with_gpt4o(medication_name, dosage)
            
            if not ai_data or 'error' in ai_data:
                logger.error(f"[AI_ENRICHMENT] ❌ Échec enrichissement IA: {medication_name}")
                return {
                    'medication_name': medication_name,
                    'error': 'Enrichissement IA échoué',
                    'source': 'error'
                }
            
            # 3. UPSERT dans medication_energy_impacts
            await self._persist_medication_data(ai_data)
            logger.info(f"[AI_ENRICHMENT] 💾 Nouvelle donnée enregistrée pour : {medication_name}")
            
            # 4. UPDATE user_medications avec ATC
            if medication_id and ai_data.get('atc_code'):
                await self._update_user_medication_atc(
                    medication_id,
                    ai_data['atc_code'],
                    ai_data['active_substance']
                )
            
            return {
                'medication_name': medication_name,
                'atc_code': ai_data.get('atc_code'),
                'active_substance': ai_data.get('active_substance'),
                'pharmacokinetics': ai_data,
                'source': 'ai_generated',
                'updated': True
            }
            
        except Exception as e:
            logger.error(f"[AI_ENRICHMENT] Erreur enrichissement: {e}")
            return {
                'medication_name': medication_name,
                'error': str(e),
                'source': 'error'
            }
    
    async def _fetch_from_api_fr(self, medication_name: str) -> Optional[Dict]:
        """
        Appelle l'API Médicaments FR pour valider et obtenir les infos de base
        
        Note: L'API publique française est accessible mais peut nécessiter
        du scraping ou des endpoints non officiels. Pour un MVP, on peut
        utiliser une recherche locale enrichie.
        """
        try:
            # Pour MVP: recherche simplifiée (à améliorer avec vraie API)
            # L'API officielle nécessite souvent un accès spécifique
            
            # Stratégie alternative: chercher dans notre DB locale d'abord
            result = self.supabase.client.table('medication_energy_impacts')\
                .select('medication_name, active_substance, atc_code, therapeutic_class')\
                .ilike('medication_name', f'%{medication_name}%')\
                .limit(1)\
                .execute()
            
            if result.data and len(result.data) > 0:
                med = result.data[0]
                return {
                    'denomination': med['medication_name'],
                    'active_substance': med['active_substance'],
                    'atc_code': med.get('atc_code'),
                    'therapeutic_class': med.get('therapeutic_class'),
                    'source': 'local_db'
                }
            
            # Si pas trouvé, retourner None (à implémenter: vraie API)
            logger.warning(f"[MedEnrichment] Médicament {medication_name} non trouvé")
            return None
            
        except Exception as e:
            logger.error(f"[MedEnrichment] Erreur API FR: {e}")
            return None
    
    def _extract_active_substance(self, basic_info: Dict) -> str:
        """Extrait le principe actif (DCI) depuis les infos de base"""
        return basic_info.get('active_substance', basic_info.get('denomination', ''))
    
    async def _get_local_pharmacokinetics(
        self,
        active_substance: str,
        atc_code: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Récupère les données pharmacocinétiques depuis la DB locale
        
        Args:
            active_substance: Principe actif (DCI)
            atc_code: Code ATC optionnel
            
        Returns:
            Dict avec données pharmacocinétiques ou None
        """
        try:
            # Chercher par code ATC d'abord (plus précis)
            if atc_code:
                result = self.supabase.client.table('medication_energy_impacts')\
                    .select('*')\
                    .eq('atc_code', atc_code)\
                    .eq('is_active', True)\
                    .maybe_single()\
                    .execute()
                
                if result.data:
                    return self._format_pharmacokinetics(result.data)
            
            # Sinon chercher par substance active
            result = self.supabase.client.table('medication_energy_impacts')\
                .select('*')\
                .ilike('active_substance', f'%{active_substance}%')\
                .eq('is_active', True)\
                .limit(1)\
                .execute()
            
            if result.data and len(result.data) > 0:
                return self._format_pharmacokinetics(result.data[0])
            
            return None
            
        except Exception as e:
            logger.error(f"[MedEnrichment] Erreur récupération pharmacokinétique: {e}")
            return None
    
    def _format_pharmacokinetics(self, raw_data: Dict) -> Dict:
        """Formate les données pharmacocinétiques pour l'API"""
        return {
            'atc_code': raw_data.get('atc_code'),
            'energy_category': raw_data['energy_category'],
            'subcategory': raw_data.get('subcategory'),
            'therapeutic_class': raw_data.get('therapeutic_class'),
            
            # Pharmacocinétique
            'onset_time': raw_data.get('onset_time'),
            'peak_time': raw_data.get('peak_time'),
            'duration': raw_data.get('duration'),
            'half_life': raw_data.get('half_life'),
            
            # Impact énergétique
            'acute_impact_min': raw_data.get('acute_impact_min'),
            'acute_impact_max': raw_data.get('acute_impact_max'),
            'acute_impact_curve': raw_data.get('acute_impact_curve'),
            
            'chronic_impact': raw_data.get('chronic_impact'),
            'chronic_onset_days': raw_data.get('chronic_onset_days'),
            'tolerance_rate': raw_data.get('tolerance_rate'),
            'withdrawal_impact': raw_data.get('withdrawal_impact'),
            
            # Effets secondaires
            'fatigue_risk': raw_data.get('fatigue_risk'),
            'alertness_effect': raw_data.get('alertness_effect'),
            'sleep_disruption': raw_data.get('sleep_disruption'),
            
            # Métadonnées
            'evidence_level': raw_data.get('evidence_level'),
            'source': raw_data.get('source'),
            'notes': raw_data.get('notes'),
        }
    
    async def search_medications(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Recherche des médicaments dans la DB locale
        
        Args:
            query: Terme de recherche
            limit: Nombre de résultats max
            
        Returns:
            Liste de médicaments correspondants
        """
        try:
            result = self.supabase.client.table('medication_energy_impacts')\
                .select('medication_name, active_substance, atc_code, therapeutic_class, energy_category')\
                .or_(f'medication_name.ilike.%{query}%,active_substance.ilike.%{query}%')\
                .eq('is_active', True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"[MedEnrichment] Erreur recherche: {e}")
            return []
    
    async def _get_local_pharmacokinetics_by_name(self, medication_name: str) -> Optional[Dict]:
        """
        Cherche pharmacocinétique par nom de médicament (fuzzy match)
        """
        try:
            result = self.supabase.client.table('medication_energy_impacts')\
                .select('*')\
                .ilike('medication_name', f'%{medication_name}%')\
                .eq('is_active', True)\
                .limit(1)\
                .execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            
            return None
        except Exception as e:
            logger.error(f"[AI_ENRICHMENT] Erreur recherche locale: {e}")
            return None
    
    async def _enrich_with_gpt4o(self, medication_name: str, dosage: Optional[str]) -> Dict:
        """
        Enrichit un médicament via GPT-4o
        
        Returns:
            Dict avec atc_code, active_substance, energy_category, pharmacokinetics
        """
        try:
            llm = LLMClient()
            
            prompt = f"""Tu es un expert pharmacologue. Analyse le médicament suivant et fournis des données structurées.

Médicament: {medication_name}
Dosage: {dosage or 'Non spécifié'}

Fournis en JSON UNIQUEMENT:
{{
  "atc_code": "Code ATC officiel (ex: N06AB06 pour Sertraline)",
  "active_substance": "Substance active (DCI)",
  "medication_name": "Nom normalisé",
  "energy_category": "stimulant|sedative|neutral|mixed",
  "subcategory": "ssri|benzodiazepine|thyroid_hormone|etc",
  "therapeutic_class": "Classe thérapeutique",
  "indication": "Indication principale",
  "onset_time": "Délai d'action en heures (float)",
  "peak_time": "Pic concentration en heures (float)",
  "duration": "Durée d'action en heures (float, null si continu)",
  "half_life": "Demi-vie en heures (float)",
  "acute_impact_min": "Impact min sur 100 (-50 à +50, int)",
  "acute_impact_max": "Impact max sur 100 (-50 à +50, int)",
  "acute_impact_curve": "gaussian|exponential|linear|plateau",
  "chronic_impact": "Impact après adaptation (-50 à +50, int)",
  "chronic_onset_days": "Jours avant effet chronique (int)",
  "tolerance_rate": "Vitesse tolérance 0.0-1.0 (float)",
  "withdrawal_impact": "Impact sevrage (-50 à 0, int)",
  "fatigue_risk": "none|low|moderate|high|severe",
  "alertness_effect": "none|decrease|increase|mixed",
  "sleep_disruption": "none|insomnia|drowsiness|mixed",
  "justification": "2-3 phrases expliquant le raisonnement"
}}

Basé sur Vidal, FDA, littérature clinique."""

            response = llm.generate_insight(prompt, temperature=0.2, max_tokens=600)
            content = response.get('content', '{}')
            
            # Parse JSON
            ai_data = json.loads(content.strip())
            
            # Ajouter métadonnées
            ai_data['evidence_level'] = 'ai_generated'
            ai_data['source'] = f'GPT-4o enrichment - {datetime.now(timezone.utc).isoformat()}'
            ai_data['notes'] = ai_data.pop('justification', '')
            
            return ai_data
            
        except json.JSONDecodeError as e:
            logger.error(f"[AI_ENRICHMENT] JSON invalide de GPT-4o: {e}")
            return {'error': 'Invalid JSON from GPT-4o'}
        except Exception as e:
            logger.error(f"[AI_ENRICHMENT] Erreur GPT-4o: {e}")
            return {'error': str(e)}
    
    async def _persist_medication_data(self, ai_data: Dict):
        """
        UPSERT les données IA dans medication_energy_impacts
        """
        try:
            insert_data = {
                'atc_code': ai_data.get('atc_code'),
                'medication_name': ai_data.get('medication_name'),
                'active_substance': ai_data.get('active_substance'),
                'energy_category': ai_data.get('energy_category'),
                'subcategory': ai_data.get('subcategory'),
                'therapeutic_class': ai_data.get('therapeutic_class'),
                'indication': ai_data.get('indication'),
                'onset_time': ai_data.get('onset_time'),
                'peak_time': ai_data.get('peak_time'),
                'duration': ai_data.get('duration'),
                'half_life': ai_data.get('half_life'),
                'acute_impact_min': ai_data.get('acute_impact_min', 0),
                'acute_impact_max': ai_data.get('acute_impact_max', 0),
                'acute_impact_curve': ai_data.get('acute_impact_curve', 'gaussian'),
                'chronic_impact': ai_data.get('chronic_impact', 0),
                'chronic_onset_days': ai_data.get('chronic_onset_days', 0),
                'tolerance_rate': ai_data.get('tolerance_rate', 0),
                'withdrawal_impact': ai_data.get('withdrawal_impact', 0),
                'fatigue_risk': ai_data.get('fatigue_risk', 'moderate'),
                'alertness_effect': ai_data.get('alertness_effect', 'none'),
                'sleep_disruption': ai_data.get('sleep_disruption', 'none'),
                'evidence_level': 'ai_generated',
                'source': ai_data.get('source'),
                'notes': ai_data.get('notes', ''),
                'is_active': True
            }
            
            # UPSERT (ON CONFLICT atc_code DO UPDATE)
            self.supabase.client.table('medication_energy_impacts')\
                .upsert(insert_data, on_conflict='atc_code')\
                .execute()
            
            logger.info(f"[AI_ENRICHMENT] ✅ Persisté: {ai_data.get('medication_name')}")
            
        except Exception as e:
            logger.error(f"[AI_ENRICHMENT] Erreur persistance: {e}")
            raise
    
    async def _update_user_medication_atc(
        self,
        medication_id: str,
        atc_code: str,
        active_substance: str
    ):
        """
        Met à jour user_medications avec ATC code et substance active
        """
        try:
            self.supabase.client.table('user_medications')\
                .update({
                    'atc_code': atc_code,
                    'active_substance': active_substance
                })\
                .eq('id', medication_id)\
                .execute()
            
            logger.info(f"[AI_ENRICHMENT] ✅ user_medications mis à jour: {medication_id}")
            
        except Exception as e:
            logger.error(f"[AI_ENRICHMENT] Erreur update user_medications: {e}")
            # Ne pas bloquer si ça échoue
