"""
Service d'analyse comparative des traitements avec Gemini
Identifie les changements (ajouts, arrêts, modifications) et génère une analyse détaillée
"""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from supabase import Client
import logging

logger = logging.getLogger(__name__)


class MedicationComparativeAnalysisService:
    """
    Service pour générer une analyse comparative des traitements avec Gemini 3 Pro.
    """
    
    def __init__(self, supabase_client: Client, gemini_client):
        """
        Initialise le service avec les clients Supabase et Gemini.
        
        Args:
            supabase_client: Client Supabase pour accéder à la base de données
            gemini_client: Client Gemini (GeminiThinkingClient)
        """
        self.supabase = supabase_client
        self.gemini_client = gemini_client
        
        logger.info("[MedicationComparativeAnalysisService] ✅ Service initialized")
    
    def _get_current_medications(self, user_id: str) -> List[Dict]:
        """Récupère les médicaments actuellement actifs de l'utilisateur."""
        try:
            result = self.supabase.table('user_medications').select('*').eq('user_id', user_id).eq('is_active', True).execute()
            medications = result.data if result.data else []
            logger.info(f"[ComparativeAnalysis] Retrieved {len(medications)} active medications")
            for med in medications:
                logger.info(f"  - {med.get('medication_name')}: start_date={med.get('start_date')}, created_at={med.get('created_at')}")
            return medications
        except Exception as e:
            logger.error(f"Error fetching current medications: {e}")
            return []
    
    def _get_recent_history(self, user_id: str, days: int = 30) -> List[Dict]:
        """
        Récupère l'historique des prises récentes pour identifier les arrêts.
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            result = self.supabase.table('medication_intake_history') \
                .select('*, medication:medication_id(medication_name, dosage, dosage_unit)') \
                .eq('user_id', user_id) \
                .gte('taken_at', cutoff_date) \
                .order('taken_at', desc=True) \
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error fetching medication history: {e}")
            return []
    
    def _identify_changes(
        self, 
        current_medications: List[Dict], 
        history: List[Dict]
    ) -> Dict[str, List[Dict]]:
        """
        Identifie les changements dans le traitement :
        - Nouveaux médicaments (ajoutés récemment)
        - Médicaments arrêtés (présents dans l'historique mais plus actifs)
        - Modifications de dosage
        """
        changes = {
            'nouveaux': [],
            'arretes': [],
            'modifies': [],
            'inchanges': []
        }
        
        # Médicaments actifs
        current_names = {med['medication_name']: med for med in current_medications}
        
        # Médicaments dans l'historique
        history_names = set()
        for entry in history:
            if entry.get('medication') and entry['medication'].get('medication_name'):
                history_names.add(entry['medication']['medication_name'])
        
        # Identifier les changements
        for med in current_medications:
            # Calculer les jours depuis le début
            start_date_str = med.get('start_date')
            logger.info(f"[ComparativeAnalysis] Medication: {med.get('medication_name')}, start_date: {start_date_str}")
            
            if start_date_str:
                try:
                    # start_date est de type DATE (pas TIMESTAMP), format: "YYYY-MM-DD"
                    # On parse juste la date, puis on calcule la différence
                    if 'T' in start_date_str or 'Z' in start_date_str:
                        # Si c'est un timestamp complet
                        start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                    else:
                        # Si c'est juste une date (YYYY-MM-DD)
                        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                    
                    days_since_start = (datetime.now(timezone.utc) - start_date).days
                    logger.info(f"[ComparativeAnalysis]   → Calculated days_since_start: {days_since_start}")
                except Exception as e:
                    logger.error(f"[ComparativeAnalysis]   → Error parsing start_date '{start_date_str}': {e}")
                    days_since_start = 999  # Valeur par défaut si erreur de parsing
            else:
                logger.warning(f"[ComparativeAnalysis]   → No start_date, using default 999")
                days_since_start = 999
            
            # Récupérer l'heure de prise
            intake_times = med.get('intake_times', [])
            if isinstance(intake_times, list) and len(intake_times) > 0:
                frequence = intake_times[0]
            else:
                frequence = 'non spécifié'
            
            med_info = {
                'nom': med['medication_name'],
                'dose': f"{med.get('dosage', '')}{med.get('dosage_unit', '')}",
                'frequence': frequence,
                'jours': days_since_start
            }
            
            if days_since_start <= 30:
                med_info['statut'] = 'nouveau'
                changes['nouveaux'].append(med_info)
            else:
                med_info['statut'] = 'inchange'
                changes['inchanges'].append(med_info)
        
        # Identifier les arrêts (médicaments dans l'historique mais plus actifs)
        for med_name in history_names:
            if med_name not in current_names:
                # Trouver la dernière prise
                last_intake = None
                for entry in history:
                    if entry.get('medication') and entry['medication'].get('medication_name') == med_name:
                        last_intake = entry
                        break
                
                if last_intake:
                    med_data = last_intake['medication']
                    changes['arretes'].append({
                        'nom': med_name,
                        'dose': f"{med_data.get('dosage', '')}{med_data.get('dosage_unit', '')}",
                        'statut': 'arret',
                        'derniere_prise': last_intake.get('taken_at', '')
                    })
        
        return changes
    
    def _build_prompt(self, changes: Dict[str, List[Dict]]) -> str:
        """
        Construit le prompt pour Gemini selon les spécifications de l'utilisateur.
        """
        # Construire la liste des traitements actuels
        traitement_actuel = []
        for med in changes['nouveaux']:
            traitement_actuel.append(f"- {med['nom']} {med['dose']}, {med['frequence']}, début J+{med['jours']} (NOUVEAU)")
        for med in changes['modifies']:
            traitement_actuel.append(f"- {med['nom']} {med['dose']}, {med['frequence']} (MODIFIÉ)")
        for med in changes['inchanges'][:5]:  # Limiter à 5 pour ne pas surcharger
            traitement_actuel.append(f"- {med['nom']} {med['dose']}, {med['frequence']}, depuis J+{med['jours']}")
        
        # Construire l'historique récent
        historique_recent = []
        for med in changes['arretes']:
            historique_recent.append(f"- {med['nom']} {med['dose']} (ARRÊTÉ)")
        
        prompt = f"""Tu es un pharmacologue expert qui vulgarise avec impact. Ton rôle : décrypter ce traitement en quelques phrases claires et percutantes.

## TRAITEMENT ACTUEL
{chr(10).join(traitement_actuel) if traitement_actuel else "Aucun médicament actif"}

## CHANGEMENTS RÉCENTS (30 jours)
{chr(10).join(historique_recent) if historique_recent else "Aucun changement"}

## MISSION
Analyse ce traitement en **4 sections courtes et impactantes** :

### 1. Vue d'ensemble (2-3 phrases max)
- Résume l'objectif global du traitement
- Identifie les changements clés (ajouts/arrêts/modifications)
- Style : Direct, rassurant, sans jargon

### 2. Comment ça agit ? (3-4 bullets)
- Explique les mécanismes avec des **métaphores simples**
- Ex: "Agit comme un..." / "Restaure..." / "Régule..."
- Mentionne les neurotransmetteurs en termes accessibles

### 3. Impact au quotidien (3-4 bullets)
- Énergie, sommeil, digestion, poids
- **Prévisions concrètes** avec temporalité (J+7, semaine 2-3, etc.)
- Ce qui est normal vs ce qui nécessite vigilance

### 4. Conseils express (3 actions concrètes)
- Format : Verbe d'action + bénéfice immédiat
- Ex: "Hydrate-toi davantage → réduit nausées"
- Garde le ton motivant et bienveillant

## CONTRAINTES
- Markdown avec ## et ### pour titres, * pour listes
- **Gras** pour mots-clés importants
- 300-400 mots MAX (synthétique !)
- Ton : Empathique mais énergique
- Toujours finir par : "⚠️ En cas de symptômes inhabituels, contacte ton médecin."

Sois percutant, pas encyclopédique. L'utilisateur veut comprendre vite et bien.
"""
        return prompt
    
    def generate_comparative_analysis(self, user_id: str) -> Dict:
        """
        Génère une analyse comparative complète des traitements.
        
        Args:
            user_id: ID de l'utilisateur
        
        Returns:
            Dict avec l'analyse textuelle détaillée
        """
        try:
            logger.info(f"[ComparativeAnalysis] 🔄 Starting analysis for user {user_id}")
            
            # 1. Récupérer les données
            current_medications = self._get_current_medications(user_id)
            recent_history = self._get_recent_history(user_id, days=30)
            
            if not current_medications:
                return {
                    'analysis_text': 'Aucun médicament actif à analyser.',
                    'has_changes': False,
                    'medications_count': 0
                }
            
            # 2. Identifier les changements
            changes = self._identify_changes(current_medications, recent_history)
            
            has_changes = len(changes['nouveaux']) > 0 or len(changes['arretes']) > 0 or len(changes['modifies']) > 0
            
            logger.info(f"[ComparativeAnalysis] 📊 Changes detected: {len(changes['nouveaux'])} new, {len(changes['arretes'])} stopped, {len(changes['modifies'])} modified")
            
            # 3. Construire le prompt
            prompt = self._build_prompt(changes)
            
            # 4. Appeler Gemini via le client existant
            logger.info("[ComparativeAnalysis] 🧠 Calling Gemini 3 Pro...")
            
            # Utiliser generate_raw_text pour obtenir du texte brut (pas de JSON)
            analysis_text = self.gemini_client.generate_raw_text(
                prompt=prompt,
                temperature=0.8,
                thinking_level="medium"
            )
            
            logger.info(f"[ComparativeAnalysis] ✅ Analysis generated ({len(analysis_text)} chars)")
            
            return {
                'analysis_text': analysis_text,
                'has_changes': has_changes,
                'medications_count': len(current_medications),
                'new_medications': len(changes['nouveaux']),
                'stopped_medications': len(changes['arretes']),
                'modified_medications': len(changes['modifies']),
                '_generated_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"[ComparativeAnalysis] ❌ Error: {e}", exc_info=True)
            raise
