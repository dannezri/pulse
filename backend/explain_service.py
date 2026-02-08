"""
Service d'Explication Énergétique - Le "Why-Stack"
Génère des cartes narratives pour expliquer le score d'énergie de manière pédagogique
"""

import logging
import hashlib
import json
from typing import Dict, List, Optional
from datetime import date, datetime, timedelta
from gemini_client import GeminiThinkingClient
from supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


class EnergyExplainService:
    """
    Service qui génère des explications narratives du score d'énergie
    en utilisant Gemini 2.0 Flash avec mode raisonnement pour créer des analogies pédagogiques.
    """
    
    def __init__(self, supabase_client: SupabaseClient, gemini_client: GeminiThinkingClient):
        self.supabase = supabase_client
        self.gemini = gemini_client
        self.cache_enabled = True  # Activer/désactiver le cache
        self.cache_ttl_hours = 24  # Durée de vie du cache en heures
        logger.info("✅ EnergyExplainService initialized with Gemini Thinking mode")
    
    def _compute_data_hash(self, energy_data: Dict, latent_states: Dict, 
                           forecast: Optional[Dict], biometrics: Dict) -> str:
        """
        Calcule un hash MD5 des données sources pour détecter les changements.
        Si les données changent, le hash change et le cache est invalidé.
        """
        # Créer une représentation stable des données
        data_repr = {
            "energy_score": energy_data.get("energy_score"),
            "confidence": energy_data.get("confidence"),
            "latent_states": {k: v.get("score") if isinstance(v, dict) else v 
                             for k, v in latent_states.items()},
            "biometrics": biometrics,
            "influencers_count": len(forecast.get("influencers", [])) if forecast else 0,
        }
        
        # Sérialiser en JSON triée pour avoir un hash stable
        data_json = json.dumps(data_repr, sort_keys=True)
        
        # Calculer le hash MD5
        return hashlib.md5(data_json.encode()).hexdigest()
    
    async def _get_cached_explanation(self, user_id: str, target_date: date, 
                                       data_hash: str) -> Optional[Dict]:
        """
        Récupère une explication depuis le cache si elle existe et est valide.
        """
        if not self.cache_enabled:
            return None
        
        try:
            result = self.supabase.client.table("gemini_explanations_cache") \
                .select("explanation, generated_at") \
                .eq("user_id", user_id) \
                .eq("target_date", target_date.isoformat()) \
                .eq("data_hash", data_hash) \
                .gte("expires_at", datetime.now().isoformat()) \
                .order("generated_at", desc=True) \
                .limit(1) \
                .execute()
            
            if result.data and len(result.data) > 0:
                cached = result.data[0]
                logger.info(f"[cache] ✅ Cache HIT for {user_id} on {target_date} (hash: {data_hash[:8]}...)")
                logger.info(f"[cache] 📅 Generated at: {cached['generated_at']}")
                return cached["explanation"]
            else:
                logger.info(f"[cache] ❌ Cache MISS for {user_id} on {target_date}")
                return None
        
        except Exception as e:
            logger.error(f"[cache] Error reading cache: {e}")
            return None
    
    async def _store_cached_explanation(self, user_id: str, target_date: date,
                                        data_hash: str, explanation: Dict):
        """
        Stocke une explication dans le cache avec une date d'expiration.
        """
        if not self.cache_enabled:
            return
        
        try:
            expires_at = datetime.now() + timedelta(hours=self.cache_ttl_hours)
            
            cache_entry = {
                "user_id": user_id,
                "target_date": target_date.isoformat(),
                "data_hash": data_hash,
                "explanation": explanation,
                "energy_score": explanation.get("energyScore"),
                "confidence": explanation.get("confidence"),
                "label": explanation.get("label"),
                "expires_at": expires_at.isoformat(),
            }
            
            # Upsert (insert ou update si existe déjà)
            self.supabase.client.table("gemini_explanations_cache") \
                .upsert(cache_entry, on_conflict="user_id,target_date,data_hash") \
                .execute()
            
            logger.info(f"[cache] 💾 Stored in cache for {user_id} on {target_date} (hash: {data_hash[:8]}...)")
            logger.info(f"[cache] ⏰ Expires at: {expires_at.isoformat()}")
        
        except Exception as e:
            logger.error(f"[cache] Error storing cache: {e}")
    
    async def generate_explanation(self, user_id: str, target_date: Optional[date] = None) -> Dict:
        """
        Génère une explication complète du score d'énergie avec des cartes narratives.
        
        Args:
            user_id: ID de l'utilisateur
            target_date: Date cible (par défaut: aujourd'hui)
        
        Returns:
            Dict avec structure:
            {
                "energyScore": 38,
                "confidence": 62,
                "label": "Journée fragile",
                "cards": [
                    {
                        "type": "nervous",
                        "title": "Le câblage est saturé",
                        "text": "...",
                        "analogy": "...",
                        "metrics": {...}
                    }
                ]
            }
        """
        if target_date is None:
            # Si aucune date spécifiée, chercher la dernière date avec des données d'énergie
            try:
                last_energy_result = self.supabase.client.table("daily_energy") \
                    .select("energy_date") \
                    .eq("user_id", user_id) \
                    .order("energy_date", desc=True) \
                    .limit(1) \
                    .execute()
                
                if last_energy_result.data and len(last_energy_result.data) > 0:
                    target_date = date.fromisoformat(last_energy_result.data[0]["energy_date"])
                    logger.info(f"[generate_explanation] 📅 Using last available date: {target_date}")
                else:
                    target_date = date.today()
                    logger.warning(f"[generate_explanation] ⚠️  No energy data found, using today: {target_date}")
            except Exception as e:
                logger.error(f"[generate_explanation] Error finding last energy date: {e}")
                target_date = date.today()
        
        try:
            # 1. Récupérer les données du calcul d'énergie
            energy_data = await self._get_energy_calculation(user_id, target_date)
            
            if not energy_data:
                logger.warning(f"No energy calculation found for user {user_id} on {target_date}")
                return self._generate_fallback_response()
            
            # 2. Récupérer les états latents
            latent_states = await self._get_latent_states(user_id, target_date)
            
            # 3. Récupérer l'intraday_energy_forecast (contient TOUT : médicaments, conditions, biométriques)
            forecast = await self._get_intraday_forecast(user_id, target_date)
            
            # Extraire les données enrichies du forecast
            medications = forecast.get("influencers", []) if forecast else []
            conditions = forecast.get("influencers", []) if forecast else []
            biometrics = await self._get_biometrics(user_id, target_date)
            
            # 4. Calculer le hash des données pour le cache
            data_hash = self._compute_data_hash(energy_data, latent_states, forecast, biometrics)
            logger.info(f"[generate_explanation] 🔑 Data hash: {data_hash[:16]}...")
            
            # 5. Vérifier le cache
            cached_explanation = await self._get_cached_explanation(user_id, target_date, data_hash)
            if cached_explanation:
                logger.info(f"[generate_explanation] 🚀 Returning cached explanation (saved ~$0.03 + 30-60s)")
                return cached_explanation
            
            logger.info(f"[generate_explanation] 🧠 Cache miss, calling Gemini 3 Pro...")
            
            # 6. Construire le prompt pour Gemini
            prompt = self._build_prompt(
                energy_data=energy_data,
                latent_states=latent_states,
                forecast=forecast,
                biometrics=biometrics
            )
            
            # 7. Appeler Gemini avec mode thinking pour générer les cartes
            explanation = await self._generate_cards(prompt)
            
            # 8. Enrichir avec les métadonnées
            energy_score_raw = energy_data.get("energy_score", 0)
            energy_score_pct = int(energy_score_raw * 100) if energy_score_raw <= 1.0 else int(energy_score_raw)
            
            explanation["energyScore"] = energy_score_pct
            explanation["confidence"] = int((energy_data.get("confidence", 0.6) * 100))
            explanation["label"] = energy_data.get("label", self._get_energy_label(energy_score_pct))
            explanation["date"] = target_date.isoformat()
            
            logger.info(f"[explain_service] ✅ Generated explanation with {len(explanation.get('cards', []))} cards for score {energy_score_pct}%")
            
            # 9. Stocker dans le cache pour réutilisation future
            await self._store_cached_explanation(user_id, target_date, data_hash, explanation)
            
            return explanation
        
        except Exception as e:
            logger.error(f"Error generating explanation for user {user_id}: {e}", exc_info=True)
            return self._generate_fallback_response()
    
    async def _get_energy_calculation(self, user_id: str, target_date: date) -> Optional[Dict]:
        """Récupère le dernier calcul d'énergie pour la date donnée"""
        try:
            result = self.supabase.client.table("daily_energy") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("energy_date", target_date.isoformat()) \
                .order("calculated_at", desc=True) \
                .limit(1) \
                .execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"[explain_service] ✅ Found daily_energy for {user_id} on {target_date}")
                return result.data[0]
            logger.warning(f"[explain_service] ⚠️ No daily_energy found for {user_id} on {target_date}")
            return None
        except Exception as e:
            logger.error(f"Error fetching energy calculation: {e}", exc_info=True)
            return None
    
    async def _get_intraday_forecast(self, user_id: str, target_date: date) -> Optional[Dict]:
        """Récupère l'intraday_energy_forecast (contient médicaments, conditions, HRV, etc.)"""
        try:
            result = self.supabase.client.table("intraday_energy_forecast") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("forecast_date", target_date.isoformat()) \
                .order("generated_at", desc=True) \
                .limit(1) \
                .execute()
            
            if result.data and len(result.data) > 0:
                forecast = result.data[0]
                # Les données sont directement dans les colonnes jsonb (influencers, points, etc.)
                # Pas de sous-champ "forecast_data"
                influencers = forecast.get("influencers", [])
                if influencers is None:
                    influencers = []
                logger.info(f"[explain_service] ✅ Found intraday_forecast with {len(influencers)} influencers")
                return forecast
            logger.warning(f"[explain_service] ⚠️ No intraday_forecast found for {user_id} on {target_date}")
            return None
        except Exception as e:
            logger.error(f"Error fetching intraday_forecast: {e}", exc_info=True)
            return None
    
    async def _get_latent_states(self, user_id: str, target_date: date) -> Dict:
        """Récupère les états latents pour la date donnée"""
        try:
            result = self.supabase.client.table("daily_state") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("state_date", target_date.isoformat()) \
                .execute()
            
            if result.data and len(result.data) > 0:
                # Organiser par type d'état
                states = {}
                for state in result.data:
                    states[state["state_type"]] = state
                logger.info(f"[explain_service] ✅ Found {len(states)} latent states for {user_id} on {target_date}: {list(states.keys())}")
                return states
            logger.warning(f"[explain_service] ⚠️ No latent states found for {user_id} on {target_date}")
            return {}
        except Exception as e:
            logger.error(f"Error fetching latent states: {e}", exc_info=True)
            return {}
    
    async def _get_active_medications(self, user_id: str, target_date: date) -> List[Dict]:
        """Récupère les médicaments actifs via RPC (même source que Pulse Energy Decay)"""
        try:
            result = self.supabase.client.rpc('get_user_active_medications', {'p_user_id': user_id}).execute()
            medications = result.data if isinstance(result.data, list) else []
            logger.info(f"[explain_service] ✅ Found {len(medications)} active medications for {user_id}")
            return medications
        except Exception as e:
            logger.error(f"Error fetching medications: {e}", exc_info=True)
            return []
    
    async def _get_active_conditions(self, user_id: str, target_date: date) -> List[Dict]:
        """Récupère les conditions de santé actives via RPC (même source que Pulse Energy Decay)"""
        try:
            result = self.supabase.client.rpc('get_health_conditions', {'p_user_id': user_id}).execute()
            conditions = result.data if isinstance(result.data, list) else []
            logger.info(f"[explain_service] ✅ Found {len(conditions)} active conditions for {user_id}")
            return conditions
        except Exception as e:
            logger.error(f"Error fetching conditions: {e}", exc_info=True)
            return []
    
    async def _get_biometrics(self, user_id: str, target_date: date) -> Dict:
        """
        Récupère les métriques biométriques depuis la table biometrics.
        Fait des requêtes CIBLÉES par metric_type pour éviter la limite de résultats.
        Cherche sur les 3 derniers jours pour compenser le délai de sync Oura.
        """
        from datetime import timedelta
        
        biometrics = {
            "hrv_night": None,
            "rhr_night": None,
            "sleep_score": None,
            "readiness_score": None,
            "activity_score": None,
            "steps": None,
            "hrv_baseline": None,
            "rhr_baseline": None,
        }
        
        try:
            # Chercher sur les 3 derniers jours (Oura sync peut avoir du délai)
            start_date = target_date - timedelta(days=2)  # J-2
            start_of_period = datetime.combine(start_date, datetime.min.time())
            end_of_day = datetime.combine(target_date, datetime.max.time())
            
            logger.info(f"[_get_biometrics] 🔍 Fetching biometrics from {start_date} to {target_date}")
            
            # Requêtes CIBLÉES par metric_type pour éviter la limite de 1000 résultats
            metrics_to_fetch = [
                ("hrv", "hrv_night"),
                ("hr", "rhr_night"),
                ("sleep_score", "sleep_score"),
                ("readiness_score", "readiness_score"),
                ("activity_score", "activity_score"),
                ("steps", "steps"),
            ]
            
            for metric_type, biometric_key in metrics_to_fetch:
                try:
                    result = self.supabase.client.table("biometrics") \
                        .select("value, recorded_at") \
                        .eq("user_id", user_id) \
                        .eq("metric_type", metric_type) \
                        .gte("recorded_at", start_of_period.isoformat()) \
                        .lte("recorded_at", end_of_day.isoformat()) \
                        .order("recorded_at", desc=True) \
                        .limit(1) \
                        .execute()
                    
                    if result.data and len(result.data) > 0:
                        value = result.data[0].get("value")
                        recorded_at = result.data[0].get("recorded_at", "")[:10]
                        biometrics[biometric_key] = value
                        logger.info(f"[_get_biometrics]   ✅ {biometric_key} = {value} (from {recorded_at}, type: {metric_type})")
                    else:
                        logger.debug(f"[_get_biometrics]   ⚠️  {metric_type} not found")
                except Exception as e:
                    logger.warning(f"[_get_biometrics]   ❌ Error fetching {metric_type}: {e}")
            
            # Baselines depuis user_baselines
            baseline_result = self.supabase.client.table("user_baselines") \
                .select("baseline_type, baseline_data") \
                .eq("user_id", user_id) \
                .execute()
            
            if baseline_result.data:
                logger.info(f"[_get_biometrics] 📊 Found {len(baseline_result.data)} baselines")
                
                for row in baseline_result.data:
                    baseline_type = row.get("baseline_type")
                    baseline_data = row.get("baseline_data", {})
                    
                    if baseline_type == "hrv":
                        biometrics["hrv_baseline"] = baseline_data.get("value")
                        logger.info(f"[_get_biometrics]   ✅ hrv_baseline = {biometrics['hrv_baseline']}")
                    elif baseline_type == "sleep":
                        biometrics["rhr_baseline"] = baseline_data.get("value")
                        logger.info(f"[_get_biometrics]   ✅ rhr_baseline = {biometrics['rhr_baseline']}")
            else:
                logger.warning(f"[_get_biometrics] ⚠️  No baselines found")
            
            # Log résumé
            available = sum(1 for v in [biometrics["hrv_night"], biometrics["rhr_night"], 
                                        biometrics["sleep_score"], biometrics["readiness_score"],
                                        biometrics["activity_score"], biometrics["steps"]] if v is not None)
            logger.info(f"[_get_biometrics] 📊 Summary: {available}/6 metrics available")
            
            return biometrics
        
        except Exception as e:
            logger.error(f"Error fetching biometrics: {e}")
            return biometrics
    
    def _build_prompt(
        self,
        energy_data: Dict,
        latent_states: Dict,
        forecast: Optional[Dict],
        biometrics: Dict
    ) -> str:
        """Construit le prompt pour Gemini 2.0 Flash Thinking avec toutes les données contextuelles"""
        
        # Extraire les métriques clés depuis daily_energy
        score = int((energy_data.get("energy_score", 0) * 100))  # Converti 0.0-1.0 en 0-100
        confidence = int((energy_data.get("confidence", 0.6) * 100))  # Converti 0.0-1.0 en 0-100
        logger.info(f"[explain_service] 📊 Building prompt with score={score}%, confidence={confidence}%")
        
        # États latents (organisés par type depuis daily_state)
        recovery_state = latent_states.get("recovery", {})
        recovery = int((recovery_state.get("score", 0) * 100)) if recovery_state else 0
        
        sleep_debt_state = latent_states.get("sleep_debt", {})
        sleep_debt = int((sleep_debt_state.get("score", 1.0) * 100)) if sleep_debt_state else 100
        
        overtrain_state = latent_states.get("overtrain", {})
        overtrain = int((overtrain_state.get("score", 1.0) * 100)) if overtrain_state else 100
        
        infection_state = latent_states.get("infection_like", {})
        infection = int((infection_state.get("score", 0) * 100)) if infection_state else 0
        
        logger.info(f"[explain_service] 🧠 Latent states: recovery={recovery}%, sleep_debt={sleep_debt}%, overtrain={overtrain}%, infection={infection}%")
        
        # ✅ Utiliser les influencers du forecast (même source que le brief !)
        influencers = forecast.get("influencers", []) if forecast else []
        med_summary = []
        cond_summary = []
        total_med_impact = 0
        
        for inf in influencers:
            name = inf.get("name", "")
            impact_str = inf.get("impact", "0")
            status = inf.get("status", "neutral")
            
            # Parser l'impact (format: "+10", "-24", etc.)
            try:
                impact_value = int(str(impact_str).replace("+", ""))
            except (ValueError, AttributeError):
                impact_value = 0
            
            if "💊" in name:  # Médicament
                med_summary.append(f"{name} (impact: {impact_str})")
                total_med_impact += impact_value
            elif name.startswith("😔") or name.startswith("🏥"):  # Condition
                cond_summary.append(f"{name} (impact: {impact_str})")
        
        logger.info(f"[explain_service] 💊 {len(med_summary)} medications from forecast: {', '.join(med_summary)} (total impact: {total_med_impact})")
        logger.info(f"[explain_service] 🏥 {len(cond_summary)} conditions from forecast: {', '.join(cond_summary)}")
        
        # Biométriques (depuis la nouvelle structure plate)
        current_energy = forecast.get("current_energy", 0) if forecast else 0
        
        # Extraire directement depuis le dict plat
        hrv_night = biometrics.get("hrv_night")
        rhr_night = biometrics.get("rhr_night")
        sleep_score = biometrics.get("sleep_score")
        readiness_score = biometrics.get("readiness_score")
        activity_score = biometrics.get("activity_score")
        steps = biometrics.get("steps")
        
        # Baselines
        hrv_baseline = biometrics.get("hrv_baseline")
        rhr_baseline = biometrics.get("rhr_baseline")
        
        logger.info(f"[explain_service] 📊 Biometrics extracted: HRV={hrv_night}, RHR={rhr_night}, Sleep={sleep_score}, Readiness={readiness_score}, Steps={steps}")
        logger.info(f"[explain_service] 📊 Baselines: HRV_baseline={hrv_baseline}, RHR_baseline={rhr_baseline}")
        
        prompt = f"""
Analyse ces données biométriques pour expliquer pourquoi le score d'énergie est de {score}%.

## DONNÉES BIOMÉTRIQUES

### Score d'Énergie
- **Score final** : {score}% (confiance: {confidence}%)
- **Label** : {self._get_energy_label(score)}

### États Latents
- **Récupération** : {recovery:.1f}% (0% = MAUVAIS, 100% = EXCELLENT) {'⚠️ FAIBLE' if recovery < 50 else '✅ Correct' if recovery < 75 else '✅ Excellent'}
- **Dette de sommeil** : {sleep_debt:.1f}% (0% = GROSSE DETTE, 100% = PAS DE DETTE) {'⚠️ GROSSE DETTE' if sleep_debt < 70 else '✅ Peu de dette'}
- **Surcharge (overtrain)** : {overtrain:.1f}% (0% = SURCHARGE IMPORTANTE, 100% = PAS DE SURCHARGE) {'⚠️ SURCHARGE DÉTECTÉE' if overtrain < 50 else '✅ Charge normale'}
- **Infection** : {infection:.1f}% (0% = PAS D'INFECTION, 100% = INFECTION PROBABLE) {'⚠️ Signaux présents' if infection > 20 else '✅ Pas de signaux'}

### Métriques Oura
- **HRV nuit** : {hrv_night}ms (baseline: {hrv_baseline}ms) {'⚠️ BAS' if hrv_night and hrv_baseline and hrv_night < hrv_baseline * 0.8 else ''}
- **RHR nuit** : {rhr_night}bpm (baseline: {rhr_baseline}bpm) {'⚠️ ÉLEVÉ' if rhr_night and rhr_baseline and rhr_night > rhr_baseline * 1.05 else ''}
- **Score sommeil** : {sleep_score}/100
- **Score readiness** : {readiness_score}/100
- **Score activité** : {activity_score}/100
- **Pas** : {steps} pas

### Influenceurs d'Énergie
Médicaments :
{chr(10).join(med_summary) if med_summary else "Aucun médicament actif"}

Conditions de santé :
{chr(10).join(cond_summary) if cond_summary else "Aucune condition active"}

---

## TA MISSION

Rédige un texte naturel et fluide qui explique à l'utilisateur pourquoi son score d'énergie est à ce niveau.

⚠️ IMPORTANT :
- ❌ NE GÉNÈRE PAS DE JSON
- ❌ NE GÉNÈRE PAS DE CODE
- ❌ N'utilise PAS de balises ```json ou ```
- ✅ ÉCRIS EN TEXTE NATUREL DIRECT

Commence directement par ton explication, comme si tu parlais à l'utilisateur.
Exemple : "Bonjour ! Ton score d'énergie aujourd'hui est de {score}%..."
"""
        
        return prompt
    
    async def _generate_cards(self, prompt: str) -> Dict:
        """Appelle Gemini 3 Pro pour générer une explication en texte naturel"""
        try:
            system_prompt = """Tu es le Wellness Coach de Pulse, expert en bio-feedback et en pharmacocinétique. 
Ton ton est empathique, professionnel et pédagogique.

🧠 MODE RAISONNEMENT ACTIVÉ :
Avant de répondre, prends le temps de RAISONNER sur les données :
1. Analyse les corrélations entre les métriques (HRV, RHR, Sommeil, Dette de sommeil)
2. Identifie le combat entre boosters et freins (médicaments)
3. Repère les charges invisibles (pathologies, oxygénation)
4. Détermine les insights les plus pertinents pour expliquer le score d'énergie

🎯 OBJECTIF :
Rédige un texte naturel et fluide qui explique à l'utilisateur pourquoi son score d'énergie est à ce niveau.

⚠️ CONSIGNES IMPORTANTES :
1. ❌ NE GÉNÈRE PAS DE JSON, NE GÉNÈRE PAS DE CODE, NE GÉNÈRE PAS DE STRUCTURE
2. ✅ ÉCRIS UN TEXTE NATUREL ET FLUIDE comme si tu parlais à un ami
3. ✅ Utilise des emojis pour la lisibilité (🔌⛽🚦💊🧠💤etc.)
4. ✅ Sois empathique et validant, jamais culpabilisant
5. ✅ Cite les valeurs exactes des données fournies
6. ✅ Utilise des analogies pour faciliter la compréhension (optionnel)
7. ✅ Structure ton texte avec des paragraphes et des sauts de ligne

💡 SUGGESTIONS D'ANALOGIES (optionnelles) :
- HRV/Système nerveux : Câblage électrique, circuit, transmission d'énergie
- Sommeil : Réservoir de carburant, batterie, stock d'énergie
- Médicaments/Conditions : Frein à main, limiteur de vitesse, charge supplémentaire

📝 FORMAT ATTENDU :
Un texte rédigé en langage naturel, structuré en paragraphes, facile à lire.
PAS DE JSON, PAS DE CODE, PAS DE BALISES MARKDOWN CODE FENCE (```).

Tu es un allié qui aide l'utilisateur à comprendre son corps, pas un juge."""

            logger.info("🧠 Calling Gemini 3 Pro for raw text generation...")
            
            # Utiliser la méthode generate_raw_text qui retourne du texte brut directement
            raw_text = self.gemini.generate_raw_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.8,
                thinking_level="high"
            )
            
            # Vérifier que le texte n'est pas vide
            if not raw_text or len(raw_text.strip()) == 0:
                logger.error("❌ Gemini returned empty text")
                return self._generate_fallback_cards()
            
            # ⚠️ Post-processing : Si Gemini génère du JSON malgré les instructions, le nettoyer
            cleaned_text = self._clean_json_response(raw_text)
            
            logger.info(f"✅ Generated raw text explanation with Gemini ({len(cleaned_text)} chars)")
            
            # Retourner le texte nettoyé dans une carte unique pour le frontend
            return {
                "cards": [
                    {
                        "type": "explanation",
                        "title": "💡 Analyse de ton énergie",
                        "text": cleaned_text,
                        "analogy": None,
                        "metrics": {}
                    }
                ]
            }
        
        except Exception as e:
            logger.error(f"❌ Error generating cards with Gemini: {e}", exc_info=True)
            return self._generate_fallback_cards()
    
    def _clean_json_response(self, text: str) -> str:
        """
        Nettoie la réponse de Gemini si elle contient du JSON malgré les instructions.
        Extrait le contenu textuel et le reformate en texte naturel.
        """
        import json
        import re
        
        # Vérifier si le texte contient du JSON markdown
        if "```json" in text or "```" in text:
            logger.warning("⚠️ Gemini generated JSON despite instructions, cleaning...")
            
            # Extraire le JSON entre les balises
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Essayer sans le tag "json"
                json_match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # Pas de balises trouvées, retourner tel quel
                    return text
            
            try:
                # Parser le JSON
                data = json.loads(json_str)
                
                # Extraire le contenu textuel
                paragraphs = []
                
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            # Extraire title, subtitle, content
                            title = item.get("title", "")
                            subtitle = item.get("subtitle", "")
                            content = item.get("content", "")
                            
                            if title:
                                paragraphs.append(f"\n{title}")
                            if subtitle:
                                paragraphs.append(f"({subtitle})")
                            if content:
                                paragraphs.append(content)
                
                # Rejoindre les paragraphes
                cleaned = "\n\n".join(p for p in paragraphs if p.strip())
                
                if cleaned:
                    logger.info("✅ Successfully cleaned JSON response to natural text")
                    return cleaned
                else:
                    logger.warning("⚠️ Failed to extract content from JSON, returning original")
                    return text
                    
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Failed to parse JSON in response: {e}, returning original")
                return text
        
        # Pas de JSON détecté, retourner tel quel
        return text
    
    def _get_energy_label(self, score: int) -> str:
        """Retourne le label textuel du score d'énergie"""
        if score >= 80:
            return "Journée excellente"
        elif score >= 65:
            return "Journée correcte"
        elif score >= 50:
            return "Journée modérée"
        elif score >= 35:
            return "Journée fragile"
        else:
            return "Journée très difficile"
    
    def _generate_fallback_response(self) -> Dict:
        """Génère une réponse de secours si les données ne sont pas disponibles"""
        return {
            "energyScore": 0,
            "confidence": 0,
            "label": "Données insuffisantes",
            "cards": self._generate_fallback_cards()["cards"],
            "error": "Impossible de générer l'explication. Données manquantes."
        }
    
    def _generate_fallback_cards(self) -> Dict:
        """Génère des cartes de secours si l'IA échoue"""
        return {
            "cards": [
                {
                    "type": "nervous",
                    "title": "Données insuffisantes",
                    "text": "Nous n'avons pas assez de données biométriques pour analyser ton état actuel. Porte ta bague Oura et synchronise tes données.",
                    "analogy": "C'est comme essayer de conduire sans voir le tableau de bord.",
                    "metrics": {}
                }
            ]
        }
