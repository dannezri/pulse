"""
Service d'analyse IA avec Smart Cache
Évite de rappeler OpenAI si les données biométriques n'ont pas changé
"""

import hashlib
import logging
from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4
from services.latent_state_service import LatentStateService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIAnalysisService:
    """
    Service pour analyser les événements du calendrier avec cache intelligent
    """
    
    def __init__(self, supabase_client, llm_client):
        """
        Initialise le service d'analyse
        
        Args:
            supabase_client: Client Supabase pour accès BDD
            llm_client: Client LLM pour génération d'insights
        """
        self.supabase = supabase_client
        self.llm = llm_client
        self.latent_state_service = LatentStateService(supabase_client)
    
    def _generate_event_id(self, user_id: str, event_data: Dict) -> str:
        """
        Génère un ID stable pour un événement du calendrier
        
        Utilise un hash du user_id + title + start + end pour créer un ID unique
        qui reste identique même si l'ID natif du calendrier change
        
        Args:
            user_id: UUID de l'utilisateur
            event_data: Données de l'événement (title, start, end)
        
        Returns:
            UUID stable pour cet événement
        """
        # Créer une clé composite pour identifier l'événement de manière unique
        key = f"{user_id}_{event_data['title']}_{event_data['start']}_{event_data['end']}"
        # Hash pour garder un ID court et stable
        hash_digest = hashlib.sha256(key.encode()).hexdigest()[:16]
        # Formater comme UUID
        return f"{hash_digest[:8]}-{hash_digest[8:12]}-{hash_digest[12:16]}-{hash_digest[16:20]}-{hash_digest[20:32] if len(hash_digest) >= 32 else hash_digest[20:] + '0' * (32 - len(hash_digest))}"[:36]
    
    def _get_cached_insight(self, user_id: str, event_id: str) -> Optional[Dict]:
        """
        Cherche un insight en cache pour cet événement
        
        Args:
            user_id: UUID de l'utilisateur
            event_id: ID de l'événement
        
        Returns:
            Dict avec l'insight ou None si pas trouvé
        """
        try:
            response = self.supabase.client.table("insights").select(
                "id, instruction_text, created_at, biometrics_ref_at"
            ).eq("user_id", user_id).eq("calendar_event_id", event_id).order(
                "created_at", desc=True
            ).limit(1).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching cached insight: {e}")
            return None
    
    def _get_latest_biometric_timestamp(self, user_id: str) -> Optional[datetime]:
        """
        Récupère le timestamp de la dernière biométrie enregistrée
        
        Args:
            user_id: UUID de l'utilisateur
        
        Returns:
            datetime de la dernière biométrie ou None
        """
        try:
            response = self.supabase.client.table("biometrics").select(
                "recorded_at"
            ).eq("user_id", user_id).order("recorded_at", desc=True).limit(1).execute()
            
            if response.data and len(response.data) > 0:
                # Parser la date ISO
                from supabase_client import parse_iso_datetime
                return parse_iso_datetime(response.data[0]["recorded_at"])
            return None
        except Exception as e:
            logger.error(f"Error fetching latest biometric timestamp: {e}")
            return None
    
    @staticmethod
    def _categorize_score(score: float) -> str:
        """Convert score to qualitative category"""
        if score >= 0.75:
            return "bonne"
        if score >= 0.50:
            return "moyenne"
        return "faible"
    
    @staticmethod
    def _categorize_confidence(conf: float) -> str:
        """Convert confidence to qualitative category"""
        if conf >= 0.70:
            return "élevée"
        if conf >= 0.40:
            return "moyenne"
        return "faible"
    
    @staticmethod
    def _categorize_debt(hours: float) -> str:
        """Categorize sleep debt"""
        if hours >= 5:
            return "dette sévère"
        if hours >= 3:
            return "dette modérée"
        if hours >= 1:
            return "dette légère"
        return "pas de dette"
    
    @staticmethod
    def _categorize_infection(state: dict) -> str:
        """Categorize infection likelihood"""
        score = state.get('smoothed_score', 0.0)
        persistent = state.get('persistent', False)
        penalties = len(state.get('metadata', {}).get('confounding_states', {}).get('penalties_applied', []))
        
        if score >= 0.7 and persistent and penalties == 0:
            return "signature forte (vigilance)"
        if score >= 0.5 and penalties <= 1:
            return "signature modérée"
        return "signature faible (probablement autre cause)"
    
    @staticmethod
    def _format_top_factors(factors: list, max_factors: int = 2) -> str:
        """Format top N factors in human-readable format"""
        if not factors:
            return "N/A"
        top = factors[:max_factors]
        return ", ".join([f['factor'].replace('_', ' ') for f in top])
    
    @staticmethod
    def _format_penalties(penalties: list) -> str:
        """Format confounding penalties"""
        if not penalties:
            return "aucune"
        mapping = {"sleep_debt": "dette sommeil", "overtrain": "surcharge"}
        return ", ".join([mapping.get(p, p) for p in penalties])
    
    def _enforce_infection_disclaimer(self, user_id: str, brief_data: Dict) -> Dict:
        """
        ENFORCE le disclaimer médical pour toute carte liée à infection-like.
        Cette fonction garantit que le disclaimer est TOUJOURS présent quand nécessaire,
        indépendamment de ce que le LLM génère.
        
        Règles:
        - Si infection_like.smoothed_score > 0.3 ET une carte mentionne infection/santé/vigilance
        - Injecter automatiquement le disclaimer médical dans le content
        
        Args:
            user_id: UUID de l'utilisateur
            brief_data: Dict avec 'cards' et 'pulseScore'
        
        Returns:
            brief_data modifié avec disclaimers enforcés
        """
        try:
            # 1. Récupérer les états latents actuels
            from datetime import date
            today = date.today()
            
            cached_states_response = self.supabase.client.table("daily_state").select(
                "infection_like"
            ).eq("user_id", user_id).eq("state_date", today.isoformat()).execute()
            
            if not cached_states_response.data or len(cached_states_response.data) == 0:
                logger.info("[DISCLAIMER ENFORCEMENT] No daily_state found, skipping")
                return brief_data
            
            infection_state = cached_states_response.data[0].get('infection_like', {})
            infection_score = infection_state.get('smoothed_score', 0.0)
            
            logger.info(f"[DISCLAIMER ENFORCEMENT] Infection score: {infection_score:.3f}")
            
            # 2. Si score < 0.3, pas de disclaimer nécessaire
            if infection_score < 0.3:
                logger.info("[DISCLAIMER ENFORCEMENT] Score < 0.3, no disclaimer needed")
                return brief_data
            
            # 3. Chercher les cartes qui mentionnent infection/vigilance/santé
            cards = brief_data.get('cards', [])
            infection_keywords = [
                'infection', 'vigilance', 'santé', 'signature', 'inhabituel',
                'maladie', 'symptômes', 'physiologique', 'pattern', 'immune'
            ]
            
            # 4. Préparer le disclaimer selon le niveau de sévérité
            severity = 'high' if infection_score > 0.6 else 'moderate'
            
            disclaimer_text = "\n\n---\n\n⚠️ **Important**\n\n"
            if severity == 'high':
                disclaimer_text += "• **Ceci n'est PAS un diagnostic médical**, mais une observation de patterns physiologiques.\n\n"
                disclaimer_text += "• Si vous ressentez des symptômes importants ou persistants (fièvre, douleurs, fatigue intense), **consultez immédiatement un professionnel de santé**."
            else:
                disclaimer_text += "• **Ceci n'est PAS un diagnostic médical**, mais une observation de patterns physiologiques.\n\n"
                disclaimer_text += "• Si vous ressentez des symptômes importants ou persistants, **consultez un professionnel de santé**."
            
            # 5. Injecter le disclaimer dans toute carte pertinente
            modified_count = 0
            for card in cards:
                card_content = card.get('content', '').lower()
                card_title = card.get('title', '').lower()
                
                # Vérifier si la carte mentionne un mot-clé
                if any(keyword in card_content or keyword in card_title for keyword in infection_keywords):
                    # Vérifier si le disclaimer n'est pas déjà présent
                    if "ceci n'est pas un diagnostic médical" not in card.get('content', '').lower():
                        # Injecter le disclaimer
                        card['content'] = card.get('content', '') + disclaimer_text
                        modified_count += 1
                        logger.info(f"[DISCLAIMER ENFORCEMENT] Injected disclaimer in card '{card.get('title', 'N/A')}' (severity: {severity})")
            
            if modified_count > 0:
                logger.info(f"[DISCLAIMER ENFORCEMENT] ✅ Enforced disclaimer on {modified_count} card(s)")
            else:
                logger.info("[DISCLAIMER ENFORCEMENT] No relevant card found for disclaimer injection")
            
            return brief_data
        
        except Exception as e:
            logger.error(f"[DISCLAIMER ENFORCEMENT] Error: {e}")
            # En cas d'erreur, retourner les données non modifiées (fail-safe)
            return brief_data
    
    def _build_prompt(self, user_id: str, event_data: Dict) -> str:
        """
        Construit le prompt pour l'analyse IA
        
        Récupère les biométries récentes et le contexte quotidien
        pour créer un prompt complet
        
        Args:
            user_id: UUID de l'utilisateur
            event_data: Données de l'événement
        
        Returns:
            Prompt complet pour le LLM
        """
        # Section 1: Informations sur l'événement
        event_section = f"""ÉVÉNEMENT À ANALYSER :
Titre : {event_data.get('title', 'Sans titre')}
Heure : {event_data.get('start', '')} → {event_data.get('end', '')}
Lieu : {event_data.get('location', 'Non spécifié')}
Notes : {event_data.get('notes', 'Aucune')}
"""
        
        # Section 2: Données biométriques récentes
        try:
            bio_response = self.supabase.client.rpc(
                'get_recent_biometrics',
                {'p_user_id': user_id, 'p_limit': 50}
            ).execute()
            
            biometrics = bio_response.data if bio_response.data else []
            
            # Regrouper par type
            grouped = {}
            for bio in biometrics:
                metric_type = bio['metric_type']
                if metric_type not in grouped:
                    grouped[metric_type] = []
                grouped[metric_type].append(bio)
            
            bio_section = "ÉTAT BIOLOGIQUE (Dernières 24h) :\n"
            
            # HRV
            if 'hrv' in grouped and grouped['hrv']:
                hrv_value = round(grouped['hrv'][0]['value'])
                bio_section += f"- HRV : {hrv_value} ms\n"
            
            # Heart Rate
            if 'heart_rate' in grouped and grouped['heart_rate']:
                hr_value = round(grouped['heart_rate'][0]['value'])
                bio_section += f"- Rythme Cardiaque au Repos : {hr_value} bpm\n"
            
            # Sleep
            sleep_key = 'sleep_duration' if 'sleep_duration' in grouped else 'sleep'
            if sleep_key in grouped and grouped[sleep_key]:
                sleep_minutes = grouped[sleep_key][0]['value']
                hours = int(sleep_minutes // 60)
                minutes = int(sleep_minutes % 60)
                bio_section += f"- Sommeil : {hours}h{minutes:02d}\n"
            
            if len(grouped) == 0:
                bio_section += "Aucune donnée disponible\n"
        
        except Exception as e:
            logger.error(f"Error fetching biometrics for prompt: {e}")
            bio_section = "ÉTAT BIOLOGIQUE : Données non disponibles\n"
        
        # Section 3: Contexte quotidien
        try:
            context_response = self.supabase.client.rpc(
                'get_recent_daily_context',
                {'p_user_id': user_id, 'p_limit': 10}
            ).execute()
            
            contexts = context_response.data if context_response.data else []
            
            context_section = "CONTEXTE RÉCENT (Nutrition, Symptômes, etc.) :\n"
            
            if contexts:
                for ctx in contexts:
                    # Parser la date
                    from supabase_client import parse_iso_datetime
                    logged_at = parse_iso_datetime(ctx['logged_at'])
                    time_str = logged_at.strftime("%H:%M")
                    
                    category = ctx['category']
                    details = ctx.get('details', {})
                    
                    if category == 'nutrition':
                        calories = details.get('calories', 'N/A')
                        carbs = details.get('carbs', 'N/A')
                        context_section += f"[{time_str}] Repas : {calories} kcal, {carbs}g glucides\n"
                    elif category == 'symptoms':
                        symptom = details.get('symptom', 'N/A')
                        context_section += f"[{time_str}] Symptôme : {symptom}\n"
                    elif category == 'medication':
                        med = details.get('medication', 'N/A')
                        context_section += f"[{time_str}] Médicament : {med}\n"
                    else:
                        context_section += f"[{time_str}] {category}\n"
            else:
                context_section += "Aucune donnée de contexte\n"
        
        except Exception as e:
            logger.error(f"Error fetching context for prompt: {e}")
            context_section = "CONTEXTE RÉCENT : Données non disponibles\n"
        
        # Combiner tout
        full_prompt = f"""{event_section}

{bio_section}

{context_section}

MISSION :
Analyse l'état biologique de l'utilisateur et donne un avis tranché sur cet événement :
- 🟢 GO : Corps au top, fonce
- 🟡 VIGILANCE : Faisable mais avec stratégie d'économie
- 🔴 PIVOT : Corps pas prêt, propose une alternative

Structure ta réponse en Markdown avec :
1. # [🟢/🟡/🔴] Diagnostic Flash (verdict en une phrase)
2. ## 💡 Le "Pourquoi" (corrélation biométrie ↔ contexte, **gras** pour métriques)
3. ## ⚡ Actions Immédiates (3 blockquotes avec couleurs et icônes)

SYSTÈME DE COULEURS POUR BLOCKQUOTES (CRITIQUE) :
Chaque blockquote DOIT commencer par un emoji de couleur :
- 🔴 = URGENT/DANGER : "Avant l'événement", annulations, risques critiques
- 🟡 = VIGILANCE : "Pendant l'événement", surveillance active
- 🟢 = OK/RECOMMANDÉ : "Après l'événement", alternatives, récupération

ICÔNES CONTEXTUELLES (utilise-les dans les actions) :
💤 Sommeil | 🍽️ Nutrition | 💧 Hydratation | 🏃 Activité | 🧘 Récupération
⚡ Énergie | 💊 Médicaments | 📊 Métriques | 🚶 Marche | ⏱️ Timing

EXEMPLE DE BLOCKQUOTES AVEC COULEURS :
> 🔴 **Avant l'événement (URGENT)**
> - 💤 Annule si sommeil < 6h
> - 🍽️ 50g de glucides complexes

> 🟡 **Pendant (SI TU Y VAS)**
> - 💧 200ml/15min
> - 📊 FC max : 140 bpm

> 🟢 **Après (RÉCUPÉRATION)**
> - 🧘 15 min d'étirements
> - 🍽️ Repas protéiné sous 30 min

Ton ton : Direct, expert, pédagogique avec termes médicaux précis."""
        
        return full_prompt
    
    def analyze_event(
        self,
        user_id: str,
        event_data: Dict,
        force_refresh: bool = False
    ) -> Dict:
        """
        Analyse un événement du calendrier avec système de cache intelligent
        
        Logique :
        - Si force_refresh=False ET insight existe ET pas de nouvelles données bio
          → Retourne le cache (instantané, 0€)
        - Sinon → Appel OpenAI et sauvegarde (quelques secondes, ~0.01€)
        
        Args:
            user_id: UUID de l'utilisateur
            event_data: Dict avec title, start, end, location, notes
            force_refresh: Si True, ignore le cache et force un nouvel appel
        
        Returns:
            Dict avec insight (Markdown), cached (bool), timestamps
        """
        # 1. Générer un ID stable pour l'événement
        event_id = self._generate_event_id(user_id, event_data)
        logger.info(f"Analyzing event {event_id} for user {user_id}")
        
        # 2. Récupérer le timestamp de la dernière biométrie
        latest_bio_timestamp = self._get_latest_biometric_timestamp(user_id)
        
        # 3. Si force_refresh=False, chercher cache valide
        if not force_refresh:
            cached = self._get_cached_insight(user_id, event_id)
            
            if cached:
                # Parser les timestamps
                from supabase_client import parse_iso_datetime
                created_at = parse_iso_datetime(cached['created_at'])
                
                # Vérifier si le cache est encore valide
                # Cache valide = pas de nouvelles données bio depuis la création de l'insight
                if latest_bio_timestamp is None or created_at >= latest_bio_timestamp:
                    logger.info(f"Cache hit for event {event_id} (no new biometrics)")
                    return {
                        "status": "success",
                        "insight": cached['instruction_text'],
                        "cached": True,
                        "analyzed_at": cached['created_at'],
                        "biometrics_ref_at": cached.get('biometrics_ref_at', cached['created_at'])
                    }
                else:
                    logger.info(f"Cache expired for event {event_id} (new biometrics available)")
        
        # 4. Générer une nouvelle analyse
        logger.info(f"Generating fresh analysis for event {event_id}")
        
        try:
            # Construire le prompt
            prompt = self._build_prompt(user_id, event_data)
            
            # Appeler le LLM
            llm_response = self.llm.generate_event_analysis(
                prompt=prompt,
                temperature=0.7,
                max_tokens=800
            )
            
            insight_text = llm_response['insight']
            
            # 5. Sauvegarder dans la base
            now = datetime.utcnow()
            bio_ref = latest_bio_timestamp if latest_bio_timestamp else now
            
            insert_result = self.supabase.client.table("insights").insert({
                "user_id": user_id,
                "calendar_event_id": event_id,
                "instruction_text": insight_text,
                "biometrics_ref_at": bio_ref.isoformat(),
                "category": "event_analysis",
                "priority": 1
            }).execute()
            
            logger.info(f"Saved new analysis for event {event_id}")
            
            return {
                "status": "success",
                "insight": insight_text,
                "cached": False,
                "analyzed_at": now.isoformat(),
                "biometrics_ref_at": bio_ref.isoformat(),
                "usage": llm_response.get('usage', {})
            }
        
        except Exception as e:
            logger.error(f"Error generating analysis: {e}")
            return {
                "status": "error",
                "message": f"Erreur lors de l'analyse : {str(e)}",
                "cached": False
            }
    
    def generate_brief(self, user_id: str, force_refresh: bool = False) -> Dict:
        """
        Génère le Brief quotidien complet avec le Wellness Coach
        
        Utilise un système de cache intelligent similaire à analyze_event:
        - Cache valide si aucune nouvelle donnée biométrique depuis la dernière génération
        - Sinon, appel OpenAI avec le nouveau prompt Wellness Coach
        
        Args:
            user_id: UUID de l'utilisateur
            force_refresh: Si True, ignore le cache et force un nouvel appel
        
        Returns:
            Dict avec:
            - status: "success" | "error"
            - cards: List[Dict] avec structure BriefCard
            - pulseScore: int (0-100)
            - cached: bool
            - analyzed_at: ISO datetime
        """
        # 1. Générer une clé de cache basée sur user_id + date du jour
        today = datetime.utcnow().date().isoformat()
        cache_key = f"brief_daily_{user_id}_{today}"
        logger.info(f"Generating brief for user {user_id} (date: {today})")
        
        # 2. Récupérer le timestamp de la dernière biométrie
        latest_bio_timestamp = self._get_latest_biometric_timestamp(user_id)
        
        # 3. Si force_refresh=False, chercher cache valide
        if not force_refresh:
            try:
                response = self.supabase.client.table("insights").select(
                    "id, instruction_text, created_at, biometrics_ref_at"
                ).eq("user_id", user_id).eq("category", "brief_daily").eq(
                    "calendar_event_id", cache_key
                ).order("created_at", desc=True).limit(1).execute()
                
                if response.data and len(response.data) > 0:
                    cached = response.data[0]
                    from supabase_client import parse_iso_datetime
                    created_at = parse_iso_datetime(cached['created_at'])
                    
                    # Vérifier si le cache est encore valide
                    if latest_bio_timestamp is None or created_at >= latest_bio_timestamp:
                        logger.info(f"Cache hit for brief {cache_key} (no new biometrics)")
                        
                        # Parser le JSON stocké
                        import json
                        cached_data = json.loads(cached['instruction_text'])
                        
                        # Ajouter intraday_forecast même pour cache (toujours à jour)
                        intraday_forecast = None
                        try:
                            from intraday_energy_service import get_intraday_forecast, generate_intraday_forecast, save_intraday_forecast
                            
                            # Chercher en cache
                            intraday_forecast = get_intraday_forecast(user_id, today)
                            
                            # Si pas en cache, générer
                            if not intraday_forecast:
                                intraday_forecast = generate_intraday_forecast(user_id, today)
                                if intraday_forecast:
                                    save_intraday_forecast(user_id, intraday_forecast)
                        except Exception as e:
                            logger.warning(f"Could not include intraday forecast in cached brief: {e}")
                        
                        return {
                            "status": "success",
                            "cards": cached_data.get('cards', []),
                            "pulseScore": cached_data.get('pulseScore', 0),
                            "cached": True,
                            "analyzed_at": cached['created_at'],
                            "biometrics_ref_at": cached.get('biometrics_ref_at', cached['created_at']),
                            "intraday_energy_forecast": intraday_forecast  # ✅ Nouveau champ
                        }
                    else:
                        logger.info(f"Cache expired for brief {cache_key} (new biometrics available)")
            except Exception as e:
                logger.warning(f"Error checking cache: {e}")
        
        # 4. Générer une nouvelle analyse
        logger.info(f"Generating fresh brief for user {user_id}")
        
        try:
            # Construire le prompt avec les données utilisateur
            prompt = self._build_brief_prompt(user_id)
            
            # Appeler le LLM avec le prompt Wellness Coach
            llm_response = self.llm.generate_wellness_brief(
                prompt=prompt,
                temperature=0.8,  # Plus créatif pour les analogies
                max_tokens=1500  # Plus long pour générer plusieurs cartes
            )
            
            brief_data = llm_response['brief']
            
            # 4.5. ENFORCE disclaimer médical pour infection-like (sécurité produit)
            brief_data = self._enforce_infection_disclaimer(user_id, brief_data)
            
            # 5. Sauvegarder dans la base
            now = datetime.utcnow()
            bio_ref = latest_bio_timestamp if latest_bio_timestamp else now
            
            import json
            insert_result = self.supabase.client.table("insights").insert({
                "user_id": user_id,
                "calendar_event_id": cache_key,
                "instruction_text": json.dumps(brief_data, ensure_ascii=False),
                "biometrics_ref_at": bio_ref.isoformat(),
                "category": "brief_daily",
                "priority": 1
            }).execute()
            
            logger.info(f"Saved new brief for user {user_id}")
            
            # 6. Ajouter intraday_energy_forecast si disponible
            # Auto-select entre Pulse Energy Decay (V2) et Heuristic (V1)
            intraday_forecast = None
            try:
                # Vérifier si données Oura disponibles
                health_profile_result = self.supabase.client.rpc('get_today_health_profile', {'p_user_id': user_id}).execute()
                health_profile = health_profile_result.data if health_profile_result.data else {}
                has_readiness = health_profile.get('readiness_score', 0) > 0
                
                if has_readiness:
                    # Utiliser Pulse Energy Decay V2
                    logger.info(f"Using Pulse Energy Decay V2 for brief (has readiness_score)")
                    from pulse_energy_decay_service import PulseEnergyDecayService
                    import asyncio
                    
                    pulse_service = PulseEnergyDecayService(supabase_client=self.supabase)
                    
                    # Exécuter la coroutine async dans un contexte synchrone
                    try:
                        forecast_obj = asyncio.run(pulse_service.generate_forecast(user_id=user_id, target_date_str=today, force_refresh=force_refresh))
                        
                        if forecast_obj:
                            intraday_forecast = forecast_obj.dict()
                        else:
                            logger.warning("Pulse Energy Decay V2 returned None, falling back to V1")
                            has_readiness = False
                    except Exception as e:
                        logger.error(f"Error with Pulse Energy Decay V2: {e}")
                        has_readiness = False
                
                # Fallback vers Heuristic V1
                if not has_readiness or not intraday_forecast:
                    logger.info(f"Using Heuristic V1 for brief")
                    from intraday_energy_service import get_intraday_forecast, generate_intraday_forecast, save_intraday_forecast
                    
                    # Chercher en cache
                    intraday_forecast = get_intraday_forecast(user_id, today)
                    
                    # Si pas en cache, générer
                    if not intraday_forecast:
                        logger.info(f"Generating intraday forecast V1 for brief inclusion")
                        intraday_forecast = generate_intraday_forecast(user_id, today)
                        if intraday_forecast:
                            save_intraday_forecast(user_id, intraday_forecast)
            except Exception as e:
                logger.warning(f"Could not include intraday forecast in brief: {e}")
            
            return {
                "status": "success",
                "cards": brief_data.get('cards', []),
                "pulseScore": brief_data.get('pulseScore', 0),
                "cached": False,
                "analyzed_at": now.isoformat(),
                "biometrics_ref_at": bio_ref.isoformat(),
                "usage": llm_response.get('usage', {}),
                "intraday_energy_forecast": intraday_forecast  # ✅ Nouveau champ
            }
        
        except Exception as e:
            logger.error(f"Error generating brief: {e}")
            return {
                "status": "error",
                "message": f"Erreur lors de la génération du Brief : {str(e)}",
                "cached": False
            }
    
    def _build_brief_prompt(self, user_id: str) -> str:
        """
        Construit le prompt pour générer le Brief quotidien
        
        Récupère toutes les données nécessaires (biométries, profil, contexte, agenda)
        pour créer un prompt complet pour le Wellness Coach
        
        Args:
            user_id: UUID de l'utilisateur
        
        Returns:
            Prompt complet avec toutes les données formatées
        """
        # 1. Récupérer le profil utilisateur
        try:
            profile_response = self.supabase.client.table("profiles").select(
                "full_name, baseline_hrv, baseline_resting_hr"
            ).eq("id", user_id).single().execute()
            
            profile = profile_response.data if profile_response.data else {}
            first_name = profile.get('full_name', 'Utilisateur').split()[0] if profile.get('full_name') else 'Utilisateur'
            baseline_hrv = profile.get('baseline_hrv', 50)
            baseline_rhr = profile.get('baseline_resting_hr', 60)
        except Exception as e:
            logger.error(f"Error fetching profile: {e}")
            first_name = 'Utilisateur'
            baseline_hrv = 50
            baseline_rhr = 60
        
        # 2. Récupérer les biométries des dernières 24h
        try:
            # Récupérer les métriques fréquentes (HRV, HR)
            bio_response = self.supabase.client.rpc(
                'get_recent_biometrics',
                {'p_user_id': user_id, 'p_limit': 100}
            ).execute()
            
            biometrics = bio_response.data if bio_response.data else []
            
            # Récupérer les métriques de sommeil et readiness (une fois par jour)
            # On récupère les 3 derniers jours pour être sûr d'avoir les données
            from datetime import timedelta
            three_days_ago = datetime.utcnow() - timedelta(days=3)
            sleep_response = self.supabase.client.table("biometrics").select(
                "metric_type, value, recorded_at"
            ).eq("user_id", user_id).in_(
                "metric_type", 
                ['readiness_score', 'sleep_timing_score', 'sleep_deep_score', 'steps']
            ).gte("recorded_at", three_days_ago.isoformat()).order(
                "recorded_at", desc=True
            ).execute()
            
            # Fusionner les données
            if sleep_response.data:
                biometrics.extend(sleep_response.data)
            
            # Log des types de métriques disponibles
            available_metrics = set(b['metric_type'] for b in biometrics)
            logger.info(f"Available metric types: {available_metrics}")
            
            # Log spécifique pour les steps
            steps_data = [b for b in biometrics if b['metric_type'] == 'steps']
            logger.info(f"Steps data found: {len(steps_data)} entries")
            if steps_data:
                logger.info(f"Steps values: {[{'value': s['value'], 'date': s.get('recorded_at', 'N/A')} for s in steps_data[:3]]}")
            
            # Extraire les métriques clés
            hrv = next((b['value'] for b in biometrics if b['metric_type'] == 'hrv'), None)
            
            # CORRECTION CRITIQUE : Utiliser le MINIMUM des HR pour le RHR (repos), pas le dernier/maximum
            # Oura envoie des 'hr' multiples par jour, le RHR est le minimum pendant le sommeil/repos
            hr_values = [b['value'] for b in biometrics if b['metric_type'] in ['hr', 'resting_hr']]
            rhr = min(hr_values) if hr_values else None
            logger.info(f"RHR calculation: found {len(hr_values)} HR values, min={rhr}")
            
            readiness = next((b['value'] for b in biometrics if b['metric_type'] == 'readiness_score'), None)
            timing_score = next((b['value'] for b in biometrics if b['metric_type'] == 'sleep_timing_score'), None)
            deep_score = next((b['value'] for b in biometrics if b['metric_type'] == 'sleep_deep_score'), None)
            steps = next((b['value'] for b in biometrics if b['metric_type'] == 'steps'), None)
            
            logger.info(f"Extracted metrics - HRV: {hrv}, RHR: {rhr} (min of {len(hr_values)} values), Readiness: {readiness}, Timing: {timing_score}, Deep: {deep_score}, Steps: {steps}")
            
            # Calculer le Pulse Score (logique robuste)
            pulse_score = 0
            score_parts = []
            
            # HRV (40% du score)
            if hrv and baseline_hrv:
                hrv_part = min((hrv / baseline_hrv) * 40, 40)
                score_parts.append(hrv_part)
                logger.info(f"HRV part: {hrv_part:.1f} (HRV: {hrv}, baseline: {baseline_hrv})")
            else:
                logger.warning(f"Missing HRV data: hrv={hrv}, baseline={baseline_hrv}")
            
            # Sleep Timing (30% du score)
            if timing_score is not None:
                timing_part = (timing_score / 100) * 30
                score_parts.append(timing_part)
                logger.info(f"Timing part: {timing_part:.1f} (timing: {timing_score})")
            else:
                logger.warning(f"Missing timing_score")
            
            # Deep Sleep (20% du score)
            if deep_score is not None:
                deep_part = (deep_score / 100) * 20
                score_parts.append(deep_part)
                logger.info(f"Deep part: {deep_part:.1f} (deep: {deep_score})")
            else:
                logger.warning(f"Missing deep_score")
            
            # RHR (10% du score avec pénalité)
            if rhr and baseline_rhr:
                rhr_diff = rhr - baseline_rhr
                rhr_part = max(10 - (rhr_diff * 0.2), 0) if rhr_diff > 0 else 10
                score_parts.append(rhr_part)
                logger.info(f"RHR part: {rhr_part:.1f} (RHR: {rhr}, baseline: {baseline_rhr}, diff: {rhr_diff})")
            else:
                logger.warning(f"Missing RHR data: rhr={rhr}, baseline={baseline_rhr}")
            
            # Calculer le score total
            if len(score_parts) > 0:
                pulse_score = int(sum(score_parts))
                logger.info(f"Pulse Score calculated: {pulse_score} from {len(score_parts)}/4 metrics")
            else:
                logger.error("No metrics available to calculate Pulse Score")
            
            # Déterminer l'état
            state = 'optimal'
            if pulse_score < 50 or (timing_score and timing_score < 30):
                state = 'alert'
            elif pulse_score < 75:
                state = 'warning'
            
            # Identifier la métrique la plus faible
            weakest_metric = 'Timing'
            weakest_value = timing_score or 0
            if deep_score and deep_score < weakest_value:
                weakest_metric = 'Sommeil Profond'
                weakest_value = deep_score
        
        except Exception as e:
            logger.error(f"Error fetching biometrics: {e}")
            hrv, rhr, readiness, timing_score, deep_score, steps = None, None, None, None, None, None
            pulse_score, state, weakest_metric = 0, 'neutral', 'N/A'
        
        # 3. Récupérer le contexte récent (nutrition, etc.)
        try:
            context_response = self.supabase.client.rpc(
                'get_recent_daily_context',
                {'p_user_id': user_id, 'p_limit': 5}
            ).execute()
            
            contexts = context_response.data if context_response.data else []
            
            last_meal = "Aucun repas enregistré"
            calories = 0
            
            for ctx in contexts:
                if ctx['category'] == 'nutrition':
                    details = ctx.get('details', {})
                    calories = details.get('calories', 0)
                    last_meal = f"{calories} kcal"
                    break
        
        except Exception as e:
            logger.error(f"Error fetching context: {e}")
            last_meal = "Aucun repas enregistré"
            calories = 0
        
        # 4. Récupérer le prochain événement du calendrier (si disponible)
        next_event = "Aucun événement planifié"
        try:
            # Récupérer les événements futurs dans les prochaines 24h
            from datetime import timedelta
            tomorrow = datetime.utcnow() + timedelta(days=1)
            
            event_response = self.supabase.client.table("calendar_events").select(
                "title, start_time"
            ).eq("user_id", user_id).gte(
                "start_time", datetime.utcnow().isoformat()
            ).lte(
                "start_time", tomorrow.isoformat()
            ).order("start_time", desc=False).limit(1).execute()
            
            if event_response.data and len(event_response.data) > 0:
                event = event_response.data[0]
                next_event = event['title']
        except Exception as e:
            logger.error(f"Error fetching next event: {e}")
        
        # 5. Calculer les états latents
        latent_states = {}
        try:
            logger.info("Calculating latent states...")
            latent_states = self.latent_state_service.calculate_all_states(
                user_id=user_id,
                force_refresh=False
            )
            logger.info(f"Latent states calculated successfully: {list(latent_states.keys())}")
        except Exception as e:
            logger.error(f"Error calculating latent states: {e}")
            # Continue without latent states if error
        
        # 6. Construire le prompt complet avec toutes les variables
        prompt = f"""DONNÉES DE L'UTILISATEUR :
- Prénom : {first_name}
- Prochain événement : {next_event}

MÉTRIQUES PULSE :
- Score Pulse : {pulse_score}% (État: {state})
- Métrique la plus faible : {weakest_metric} (valeur: {int(weakest_value) if weakest_value else 'N/A'})
- Score Oura Readiness : {readiness or 'N/A'}%
- Sleep Timing : {timing_score or 'N/A'}/100
- Sleep Deep : {deep_score or 'N/A'}/100
- HRV : {int(hrv) if hrv else 'N/A'} ms (Baseline: {baseline_hrv} ms)
- RHR : {int(rhr) if rhr else 'N/A'} bpm (Baseline: {baseline_rhr} bpm)

CONTEXTE RÉCENT :
- Dernier repas : {last_meal}
- Pas aujourd'hui : {int(steps) if steps else 'Aucune donnée'}"""
        
        # Ajouter les états latents au prompt si disponibles
        if latent_states:
            prompt += """

ÉTATS LATENTS CALCULÉS (données scientifiques à intégrer):

"""
            # Recovery
            if 'recovery' in latent_states:
                rec = latent_states['recovery']
                prompt += f"""1. Récupération: {self._categorize_score(rec.get('smoothed_score', 0.0))}
   - Confiance: {self._categorize_confidence(rec.get('confidence', 0.0))}
   - Facteurs principaux: {self._format_top_factors(rec.get('top_factors', []))}
   - Note: {rec.get('interpretation', 'N/A')}

"""
            
            # Sleep Debt
            if 'sleep_debt' in latent_states:
                debt = latent_states['sleep_debt']
                debt_hours = debt.get('debt_hours', 0.0)
                prompt += f"""2. Dette de sommeil: {self._categorize_debt(debt_hours)}
   - Confiance: {self._categorize_confidence(debt.get('confidence', 0.0))}
   - Heures accumulées: {debt_hours:.1f}h (pour calcul, ne pas afficher tel quel)

"""
            
            # Overtrain
            if 'overtrain' in latent_states:
                over = latent_states['overtrain']
                prompt += f"""3. Surcharge entraînement: {over.get('interpretation', 'N/A')}
   - Confiance: {self._categorize_confidence(over.get('confidence', 0.0))}
   - Facteurs: {self._format_top_factors(over.get('top_factors', []))}

"""
            
            # Infection-like
            if 'infection_like' in latent_states:
                inf = latent_states['infection_like']
                penalties = inf.get('metadata', {}).get('confounding_states', {}).get('penalties_applied', [])
                prompt += f"""4. Signature infection: {self._categorize_infection(inf)}
   - Confiance: {self._categorize_confidence(inf.get('confidence', 0.0))}
   - Persistant: {"oui" if inf.get('persistent', False) else "non"}
   - Facteurs: {self._format_top_factors(inf.get('top_factors', []))}
   - Pénalités: {self._format_penalties(penalties)}

"""
            
            # Consignes pour utilisation des états latents
            prompt += """CONSIGNES (utilise les CATÉGORIES, pas les seuils numériques):
- Si dette = "modérée" ou "sévère": créer une carte "alert" dédiée
- Si surcharge = "surcharge": créer une carte "warning" avec recommandation de repos
- Si infection = "signature forte" ET persistant="oui" ET peu de pénalités: créer une carte "alert" de vigilance
- Si récupération = "faible": adapter le message du verdict pour expliquer la cause

"""
        
        # Continuer avec les instructions existantes
        prompt += """
INSTRUCTIONS :
Génère 4-6 cartes Brief dans le format JSON spécifié selon les données disponibles.

CARTES OBLIGATOIRES (3) :
1. "Le bilan du coach" (verdict, priority: 100) - Explique le lien entre comportement passé et état actuel
2. "Votre météo intérieure" (focus, priority: 90) - Prévision de l'impact sur la journée/événement
3. "Le petit pas du jour" (activity, priority: 80) - Action simple et motivante

CARTES CONTEXTUELLES (générer si pertinent) :
4. Si le prochain événement n'est pas "Aucun événement planifié" → Carte "agenda" (priority: 70)
   - Titre: "À venir" ou personnalisé selon l'événement
   - Conseils pour optimiser la performance lors de cet événement
   
5. Si Pas < 5000 ou "Aucune donnée" → Carte "activity" (priority: 65)
   - Titre: "Votre corps en veille"
   - Explique l'impact de l'inactivité sur le métabolisme et l'horloge interne
   - Badge: le nombre de pas actuel
   
6. Si Dernier repas = "Aucun repas enregistré" ou calories < 500 → Carte "focus" (priority: 60)
   - Titre: "Carburant manquant"
   - Explique l'impact du manque de nutrition sur l'énergie et la récupération
   - Icône: "Coffee" ou "UtensilsCrossed"

7. Si Sleep Deep < 60 → Carte "focus" (priority: 55)
   - Titre: "Sommeil léger"
   - Conseils pour améliorer la qualité du sommeil profond

Utilise le prénom {first_name} dans les messages. Si le Timing < 30 ou le Pulse Score < 60, utilise state="alert" pour les cartes critiques.
Inclus le pulseScore dans la réponse JSON.

INSTRUCTIONS :
Génère 4-6 cartes Brief dans le format JSON spécifié selon les données disponibles.

CARTES OBLIGATOIRES (3) :
1. "Le bilan du coach" (verdict, priority: 100) - Explique le lien entre comportement passé et état actuel
2. "Votre météo intérieure" (focus, priority: 90) - Prévision de l'impact sur la journée/événement
3. "Le petit pas du jour" (activity, priority: 80) - Action simple et motivante

CARTES CONTEXTUELLES (générer si pertinent) :
4. Si le prochain événement n'est pas "Aucun événement planifié" → Carte "agenda" (priority: 70)
   - Titre: "À venir" ou personnalisé selon l'événement
   - Conseils pour optimiser la performance lors de cet événement
   
5. Si Pas < 5000 ou "Aucune donnée" → Carte "activity" (priority: 65)
   - Titre: "Votre corps en veille"
   - Explique l'impact de l'inactivité sur le métabolisme et l'horloge interne
   - Badge: le nombre de pas actuel
   
6. Si Dernier repas = "Aucun repas enregistré" ou calories < 500 → Carte "focus" (priority: 60)
   - Titre: "Carburant manquant"
   - Explique l'impact du manque de nutrition sur l'énergie et la récupération
   - Icône: "Coffee" ou "UtensilsCrossed"

7. Si Sleep Deep < 60 → Carte "focus" (priority: 55)
   - Titre: "Sommeil léger"
   - Conseils pour améliorer la qualité du sommeil profond

Utilise le prénom {first_name} dans les messages. Si le Timing < 30 ou le Pulse Score < 60, utilise state="alert" pour les cartes critiques.
Inclus le pulseScore dans la réponse JSON."""
        
        return prompt