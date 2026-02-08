"""
Service d'Analyse de Médicaments avec Gemini
Génère des analyses détaillées pour chaque médicament avec explications humaines
"""

import logging
import hashlib
import json
from typing import Dict, List, Optional
from datetime import date, datetime, timedelta
from gemini_client import GeminiThinkingClient
from supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


class MedicationAnalysisService:
    """
    Service qui génère des analyses détaillées de médicaments
    en utilisant Gemini 3 Pro pour créer des explications vulgarisées et actionnables.
    """
    
    def __init__(self, supabase_client: SupabaseClient, gemini_client: GeminiThinkingClient):
        self.supabase = supabase_client
        self.gemini = gemini_client
        self.cache_enabled = True  # Activer/désactiver le cache
        self.cache_ttl_hours = 168  # 7 jours (les médicaments changent peu)
        logger.info("✅ MedicationAnalysisService initialized with Gemini 3 Pro")
    
    def _get_history_summary(self, user_id: str) -> Dict:
        """
        Récupère un résumé de l'historique des prises pour inclure dans le hash.
        Retourne le nombre total d'entrées et la date de la dernière prise.
        """
        try:
            result = self.supabase.client.table("medication_intake_history") \
                .select("intake_date") \
                .eq("user_id", user_id) \
                .order("intake_date", desc=True) \
                .limit(1) \
                .execute()
            
            # Compter le total d'entrées
            count_result = self.supabase.client.table("medication_intake_history") \
                .select("id", count="exact") \
                .eq("user_id", user_id) \
                .execute()
            
            last_date = result.data[0]["intake_date"] if result.data else None
            total_count = count_result.count if hasattr(count_result, 'count') else 0
            
            return {
                "last_intake_date": last_date,
                "total_intakes": total_count,
            }
        except Exception as e:
            logger.warning(f"[history] Could not fetch history summary: {e}")
            return {
                "last_intake_date": None,
                "total_intakes": 0,
            }
    
    def _compute_medications_hash(self, medications: List[Dict], user_id: str) -> str:
        """
        Calcule un hash MD5 des médicaments + historique pour le cache.
        Le hash est basé sur: médicaments + dernière date d'historique + nombre total d'entrées
        Cela permet de régénérer l'analyse seulement quand l'historique change.
        """
        # Récupérer le résumé de l'historique
        history_summary = self._get_history_summary(user_id)
        
        # Créer une représentation stable des médicaments
        meds_data = []
        for med in medications:
            meds_data.append({
                "name": med.get("medication_name", ""),
                "dosage": med.get("dosage", 0),
                "unit": med.get("dosage_unit", ""),
                "pills_per_intake": med.get("pills_per_intake", 1),
                "intake_times": sorted(med.get("intake_times", [])),
                "start_date": med.get("start_date", ""),
                "atc_code": med.get("atc_code", ""),
            })
        
        # Trier pour avoir un hash stable
        meds_data_sorted = sorted(meds_data, key=lambda x: x["name"])
        
        # Combiner médicaments + historique
        cache_data = {
            "medications": meds_data_sorted,
            "history": history_summary,
        }
        
        # Sérialiser en JSON
        data_json = json.dumps(cache_data, sort_keys=True)
        
        # Calculer le hash MD5
        hash_value = hashlib.md5(data_json.encode()).hexdigest()
        
        logger.info(f"[cache] 🔑 Hash computed with history (last: {history_summary['last_intake_date']}, total: {history_summary['total_intakes']})")
        
        return hash_value
    
    async def _get_cached_analysis(self, user_id: str, medications_hash: str) -> Optional[Dict]:
        """
        Récupère une analyse depuis le cache si elle existe et est valide.
        """
        if not self.cache_enabled:
            return None
        
        try:
            result = self.supabase.client.table("medication_analysis_cache") \
                .select("analysis, generated_at") \
                .eq("user_id", user_id) \
                .eq("medications_hash", medications_hash) \
                .gte("expires_at", datetime.now().isoformat()) \
                .order("generated_at", desc=True) \
                .limit(1) \
                .execute()
            
            if result.data and len(result.data) > 0:
                cached = result.data[0]
                logger.info(f"[cache] ✅ Cache HIT for {user_id} (hash: {medications_hash[:8]}...)")
                logger.info(f"[cache] 📅 Generated at: {cached['generated_at']}")
                return cached["analysis"]
            else:
                logger.info(f"[cache] ❌ Cache MISS for {user_id}")
                return None
        
        except Exception as e:
            logger.error(f"[cache] Error reading cache: {e}")
            return None
    
    async def _store_cached_analysis(self, user_id: str, medications_hash: str, analysis: Dict):
        """
        Stocke une analyse dans le cache avec une date d'expiration.
        """
        if not self.cache_enabled:
            return
        
        try:
            expires_at = datetime.now() + timedelta(hours=self.cache_ttl_hours)
            
            cache_entry = {
                "user_id": user_id,
                "medications_hash": medications_hash,
                "analysis": analysis,
                "generated_at": datetime.now().isoformat(),
                "expires_at": expires_at.isoformat(),
            }
            
            # Upsert pour éviter les doublons
            self.supabase.client.table("medication_analysis_cache") \
                .upsert(cache_entry, on_conflict="user_id,medications_hash") \
                .execute()
            
            logger.info(f"[cache] 💾 Stored analysis in cache (expires: {expires_at.isoformat()})")
        
        except Exception as e:
            logger.error(f"[cache] Error storing cache: {e}")
    
    async def _get_user_medications(self, user_id: str) -> List[Dict]:
        """
        Récupère les médicaments actifs de l'utilisateur depuis Supabase.
        """
        try:
            result = self.supabase.client.table("user_medications") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("is_active", True) \
                .order("start_date", desc=True) \
                .execute()
            
            if result.data:
                logger.info(f"📥 Retrieved {len(result.data)} active medications for user {user_id}")
                return result.data
            else:
                logger.warning(f"No active medications found for user {user_id}")
                return []
        
        except Exception as e:
            logger.error(f"Error retrieving medications: {e}")
            return []
    
    def _build_analysis_prompt(self, medications: List[Dict]) -> str:
        """
        Construit le prompt pour Gemini avec la liste des médicaments.
        """
        # Préparer la liste des médicaments pour le prompt
        meds_list = []
        for med in medications:
            # Calculer le dosage total (gérer les valeurs None)
            dosage = med.get("dosage") or 0
            pills_per_intake = med.get("pills_per_intake") or 1
            unit = med.get("dosage_unit") or "mg"
            total_dosage = float(dosage) * float(pills_per_intake)
            
            # Calculer les jours depuis le début
            start_date_str = med.get("start_date")
            days_since_start = 0
            if start_date_str:
                try:
                    start_date = datetime.fromisoformat(start_date_str).date()
                    days_since_start = (date.today() - start_date).days
                except:
                    days_since_start = 0
            
            # Heures de prise
            intake_times = med.get("intake_times", [])
            intake_times_str = ", ".join(intake_times) if intake_times else "non spécifié"
            
            # Format: "Nom dosage, heures de prise, début J+X"
            med_name = med.get('medication_name', 'Inconnu')
            
            # Ajouter le dosage seulement s'il est présent
            if total_dosage > 0:
                med_str = f"{med_name} {total_dosage:.1f}{unit}"
            else:
                med_str = f"{med_name}"
            
            if intake_times:
                med_str += f", {intake_times_str}"
            if days_since_start > 0:
                med_str += f", début J+{days_since_start}"
            
            meds_list.append(med_str)
        
        # Construire le prompt
        medications_formatted = "\n".join([f"- {med}" for med in meds_list])
        
        prompt = f"""Médicaments à analyser :

{medications_formatted}

Pour chaque médicament, analyse-le et fournis les informations suivantes :

1. **Intro explicative** : Une phrase courte mais précise qui explique la fonction du médicament et son mécanisme d'action principal de manière accessible. Utilise des termes scientifiques vulgarisés.
   Exemple: "C'est un antidépresseur de la famille des ISRS qui aide à réguler la sérotonine, le neurotransmetteur de l'humeur et du bien-être."

2. **Impact sur le corps** : Explique en 2-3 phrases comment la molécule agit physiologiquement sur le long terme. Sois pédagogique : explique le mécanisme, le délai d'action, et les effets biologiques concrets sur l'organisme.
   Exemple: "Grâce à sa libération prolongée, il diffuse lentement pour rééquilibrer en douceur votre humeur et votre énergie au fil des semaines. La molécule agit progressivement sur les niveaux de sérotonine dans le cerveau, ce qui améliore l'humeur, réduit l'anxiété et stabilise les émotions. L'effet complet se développe sur 2 à 4 semaines."

3. **Impact sur la journée** : Décris en 2-3 phrases ce que l'utilisateur peut concrètement ressentir au quotidien, en tenant compte de l'heure de prise indiquée, de la pharmacocinétique (pic, durée d'action), et des jours depuis le début. Sois spécifique et rassurant.
   Exemple: "En le prenant le soir vers 23h, vous limitez les nausées fréquentes au début, et le pic d'action arrive pendant votre sommeil. Le matin, l'effet est stable et vous pouvez vaquer à vos activités normalement. Soyez patient si votre sommeil est un peu léger ces premiers jours, c'est normal."

4. **Observation** : Fournis un conseil personnalisé ou une note de vigilance spécifique à la durée du traitement (phase aiguë J+0-7, adaptation J+7-30, chronique J+30+) ou au dosage. Sois empathique et donnez des repères temporels concrets.
   Exemple: "Vous êtes au tout début (J+3) : les vrais bienfaits mettent 2 à 4 semaines à arriver, tenez bon si vous ressentez de petits inconforts transitoires. Ne modifiez jamais la dose sans avis médical, même si vous vous sentez mieux."

5. **Labels du graphique** : Fournis des labels CONCRETS orientés "impact sur la journée" (pas de termes médicaux abstraits).
   
   RÈGLE IMPORTANTE : Les labels doivent répondre à "Comment je vais me sentir ?" et "Qu'est-ce que je vais ressentir concrètement ?".
   
   Exemples BONS (orientés vie quotidienne) :
   - Pour un antidépresseur : 
     * label_concentration="Dosage actif" (pas "Niveau sanguin")
     * label_efficacite="Sérénité et bien-être" (pas "Effet anxiolytique")
     * label_effets_secondaires="Fatigue et nausées" (pas "Inconfort transitoire")
   
   - Pour un stimulant :
     * label_concentration="Présence du produit"
     * label_efficacite="Concentration mentale"
     * label_effets_secondaires="Agitation et nervosité"
   
   - Pour un sédatif/anxiolytique :
     * label_concentration="Effet actif"
     * label_efficacite="Apaisement et calme"
     * label_effets_secondaires="Somnolence"
   
   - Pour une hormone thyroïde :
     * label_concentration="Hormone disponible"
     * label_efficacite="Énergie et métabolisme"
     * label_effets_secondaires="Palpitations"
   
   INTERDITS : "Niveau sanguin", "Effet thérapeutique", "Inconfort", "Impact physiologique"
   AUTORISÉS : "Bien-être", "Sérénité", "Énergie", "Calme", "Concentration", "Fatigue", "Agitation"

6. **Effets horaires** : Génère un profil horaire sur 24h avec 12 points clés (toutes les 2 heures) COMMENÇANT À L'HEURE DE PRISE.
   
   Structure : Commence toujours par l'heure de prise indiquée, puis continue toutes les 2h en faisant le tour de 24h.
   Exemple : Si prise à 23h → [23:00, 01:00, 03:00, 05:00, 07:00, 09:00, 11:00, 13:00, 15:00, 17:00, 19:00, 21:00]
   
   Pour chaque heure, fournis :
   - **concentration** (0-100) : Niveau du principe actif dans le sang
   - **efficacite** (0-100) : Efficacité thérapeutique selon le label_efficacite
   - **effets_secondaires** (0-100) : Intensité selon le label_effets_secondaires
   - **description** (3-5 mots max) : Ressenti à cette heure
   
   Prends en compte :
   - Commence TOUJOURS par l'heure de prise (c'est l'heure 0)
   - La demi-vie du médicament (ex: LP = libération prolongée sur 8-12h)
   - Les jours depuis le début (J+0-7 = montée en charge, J+30+ = effet stabilisé)
   - Les pics et creux d'efficacité selon la pharmacocinétique

Ton style doit être :
- **Pédagogique et précis** : Explique les mécanismes avec des termes scientifiques vulgarisés (ex: "neurotransmetteur", "libération prolongée", "demi-vie")
- **Empathique et rassurant** : Utilise un ton bienveillant qui rassure l'utilisateur sur les effets normaux
- **Concret et actionnable** : Donne des repères temporels précis (J+3, 2-4 semaines, etc.) et des sensations concrètes
- **Adapté à la durée du traitement** : Distingue phase aiguë (J+0-7), adaptation (J+7-30), chronique (J+30+)
- **Détaillé** : 2-3 phrases par section pour bien expliquer (sauf descriptions horaires qui restent courtes)

Réponds UNIQUEMENT au format JSON suivant (pas de texte avant ou après, PAS DE COMMENTAIRES) :

{{
  "analyse_traitements": [
    {{
      "nom": "Nom du médicament",
      "intro_explicative": "...",
      "impact_corps": "...",
      "impact_journee": "...",
      "observation": "...",
      "label_concentration": "Dosage actif",
      "label_efficacite": "Sérénité et bien-être",
      "label_effets_secondaires": "Fatigue et nausées",
      "heure_prise": "23:00",
      "effets_horaires": [
        {{
          "heure": "00:00",
          "concentration": 85,
          "efficacite": 90,
          "effets_secondaires": 10,
          "description": "Effet stable pendant la nuit"
        }},
        {{
          "heure": "02:00",
          "concentration": 82,
          "efficacite": 88,
          "effets_secondaires": 8,
          "description": "Effet stable"
        }},
        {{
          "heure": "04:00",
          "concentration": 78,
          "efficacite": 85,
          "effets_secondaires": 5,
          "description": "Légère baisse"
        }}
        (continuer pour 12 heures COMMENÇANT par l'heure de prise, puis toutes les 2h)
      ]
    }}
  ]
}}

IMPORTANT: 
- Fournis EXACTEMENT 12 heures COMMENÇANT par l'heure de prise, puis toutes les 2h (ex: si prise à 23h → 23:00, 01:00, 03:00, etc.)
- Inclus les labels adaptatifs ORIENTÉS VIE QUOTIDIENNE (pas de termes médicaux abstraits)
  * label_concentration : Comment le produit est présent (ex: "Dosage actif", "Présence du produit")
  * label_efficacite : Comment ça améliore la vie (ex: "Sérénité et bien-être", "Énergie et vitalité", "Calme mental")
  * label_effets_secondaires : Ce qu'on peut ressentir de désagréable (ex: "Fatigue et nausées", "Agitation", "Somnolence")
- Inclus l'heure de prise (heure_prise) au format "HH:00"
- Descriptions COURTES (3-5 mots maximum)
- PAS de commentaires dans le JSON
- PAS de retours à la ligne dans les strings
- PAS de texte explicatif avant ou après
- JSON valide uniquement
"""
        
        return prompt
    
    def _build_system_prompt(self) -> str:
        """
        Construit le prompt système pour Gemini.
        """
        return """Tu es un expert en pharmacologie vulgarisée et un coach bien-être.

Ton objectif est d'expliquer les traitements de manière simple, humaine et structurée.

RÈGLES IMPORTANTES :
1. Utilise un langage simple et accessible
2. Sois empathique et rassurant
3. Reste factuel mais vulgarise les concepts médicaux
4. Évite le jargon médical complexe
5. Fournis des informations actionnables
6. Ne donne jamais de conseil médical (ex: "consultez votre médecin" plutôt que "arrêtez le traitement")

FORMAT DE SORTIE :
- Réponds UNIQUEMENT en JSON valide
- Pas de texte avant ou après le JSON
- Pas de markdown (```json)
- PAS DE COMMENTAIRES dans le JSON (pas de //, pas de ...)
- PAS DE RETOURS À LA LIGNE dans les strings JSON
- Descriptions COURTES (3-5 mots maximum)
- Structure exacte demandée dans le prompt utilisateur
- Pour les effets horaires: fournis EXACTEMENT 12 heures (toutes les 2h de 00:00 à 22:00) pour chaque médicament
"""
    
    async def generate_medication_analysis(self, user_id: str) -> Dict:
        """
        Génère une analyse détaillée pour tous les médicaments actifs de l'utilisateur.
        
        Args:
            user_id: ID de l'utilisateur
        
        Returns:
            Dict avec l'analyse de chaque médicament
        """
        try:
            # 1. Récupérer les médicaments actifs
            medications = await self._get_user_medications(user_id)
            
            if not medications or len(medications) == 0:
                logger.warning(f"No medications to analyze for user {user_id}")
                return {
                    "analyse_traitements": [],
                    "message": "Aucun médicament actif à analyser"
                }
            
            # 2. Calculer le hash pour le cache (inclut l'historique)
            medications_hash = self._compute_medications_hash(medications, user_id)
            logger.info(f"[generate_analysis] 🔑 Medications + History hash: {medications_hash[:16]}...")
            
            # 3. Vérifier le cache
            cached_analysis = await self._get_cached_analysis(user_id, medications_hash)
            if cached_analysis:
                logger.info(f"[generate_analysis] 🚀 Returning cached analysis (saved ~$0.02-0.05)")
                return cached_analysis
            
            logger.info(f"[generate_analysis] 🧠 Cache miss, calling Gemini 3 Pro...")
            
            # 4. Construire le prompt
            user_prompt = self._build_analysis_prompt(medications)
            system_prompt = self._build_system_prompt()
            
            logger.info(f"[generate_analysis] 📝 Analyzing {len(medications)} medications...")
            logger.debug(f"Prompt length: {len(user_prompt)} chars")
            
            # 5. Appeler Gemini avec thinking mode
            result = self.gemini.generate_insight(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,  # Plus déterministe pour JSON valide
                max_tokens=8000,  # Augmenter pour 12h × 2 médicaments + textes
                thinking_level="medium"  # Medium pour économiser un peu
            )
            
            # 6. Parser la réponse
            raw_response = result.get("raw_response", "{}")
            
            try:
                analysis = json.loads(raw_response)
                
                # Valider la structure
                if "analyse_traitements" not in analysis:
                    logger.error("❌ Missing 'analyse_traitements' field in Gemini response")
                    raise ValueError("Missing 'analyse_traitements' field")
                
                # Valider que chaque analyse a les champs requis
                for i, med_analysis in enumerate(analysis["analyse_traitements"]):
                    required_fields = ["nom", "intro_explicative", "impact_corps", "impact_journee", "observation"]
                    for field in required_fields:
                        if field not in med_analysis:
                            logger.error(f"❌ Missing required field '{field}' in medication {i}")
                            # Ajouter un placeholder si manquant
                            med_analysis[field] = "Information non disponible"
                
                # Ajouter des métadonnées
                analysis["_generated_at"] = datetime.now().isoformat()
                analysis["_medications_count"] = len(medications)
                
                # Log du coût
                if result.get("usage", {}).get("estimated_cost_usd"):
                    cost = result["usage"]["estimated_cost_usd"]
                    analysis["_cost"] = cost
                    logger.info(f"💰 Cost: ${cost:.4f} USD")
                
                # Log du thinking process
                if result.get("thinking"):
                    logger.info(f"💭 Thinking process (first 200 chars): {result['thinking'][:200]}...")
                
                logger.info(f"✅ Generated analysis for {len(analysis['analyse_traitements'])} medications")
                
                # 7. Stocker dans le cache
                await self._store_cached_analysis(user_id, medications_hash, analysis)
                
                return analysis
            
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON from Gemini: {e}")
                logger.debug(f"Raw response: {raw_response[:500]}")
                
                # Retourner une réponse de fallback
                return {
                    "analyse_traitements": [],
                    "error": "Erreur de parsing de la réponse Gemini",
                    "message": "Une erreur s'est produite lors de l'analyse. Veuillez réessayer."
                }
        
        except Exception as e:
            logger.error(f"❌ Error generating medication analysis: {e}", exc_info=True)
            raise


# Exemple d'utilisation
if __name__ == "__main__":
    import asyncio
    import sys
    
    async def test():
        try:
            from supabase_client import get_supabase_client
            from gemini_client import GeminiThinkingClient
            
            supabase = get_supabase_client()
            gemini = GeminiThinkingClient()
            
            service = MedicationAnalysisService(supabase, gemini)
            
            # Test avec un user_id (à remplacer)
            user_id = "test-user-123"
            
            result = await service.generate_medication_analysis(user_id)
            
            print("✅ Test réussi!")
            print(f"Nombre de médicaments analysés: {len(result.get('analyse_traitements', []))}")
            if result.get('_cost'):
                print(f"Coût estimé: ${result['_cost']:.4f} USD")
            
            # Afficher les analyses
            for med in result.get('analyse_traitements', []):
                print(f"\n📊 {med.get('nom')}:")
                print(f"  Intro: {med.get('intro_explicative', 'N/A')}")
                print(f"  Impact corps: {med.get('impact_corps', 'N/A')[:80]}...")
            
        except Exception as e:
            print(f"❌ Test échoué: {e}")
            sys.exit(1)
    
    asyncio.run(test())
