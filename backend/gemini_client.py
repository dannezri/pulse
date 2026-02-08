"""
Client Gemini 3 Pro avec mode raisonnement (thinking mode)
Utilise le package google-genai avec Gemini 3 Pro Preview.

⚠️ ATTENTION : Gemini 3 Pro est PAYANT (pas de free tier)
Tarif : 2$ / 12$ pour < 200k tokens (entrée/sortie)
"""

import os
import json
import logging
from typing import Dict, Optional
from google import genai
from google.genai import types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiThinkingClient:
    """
    Client pour appeler Gemini 3 Pro avec mode thinking activé
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialise le client Gemini 3 Pro
        
        Args:
            api_key: Clé API Google (ou depuis env GOOGLE_API_KEY)
            model: Modèle à utiliser (défaut: gemini-3-pro-preview)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY must be set in environment or passed as parameter")
        
        # Configurer le client avec le nouveau package
        self.client = genai.Client(api_key=self.api_key)
        
        # Utiliser Gemini 3 Pro Preview (PAYANT - pas de free tier)
        self.model_name = model or os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")
        
        # Niveau de thinking par défaut (low/medium/high)
        self.thinking_level = os.getenv("GEMINI_THINKING_LEVEL", "high")
        
        logger.info(f"✅ Gemini client initialized with model: {self.model_name}")
        logger.info(f"🧠 Thinking level: {self.thinking_level}")
        logger.info("📦 Using google-genai package")
        logger.warning("⚠️  Gemini 3 Pro is PAID (no free tier) - ~$0.03 per explanation")
    
    def generate_insight(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 1.0,  # Gemini 3 recommande 1.0 par défaut
        max_tokens: int = 8192,
        thinking_level: Optional[str] = None
    ) -> Dict:
        """
        Génère un insight en appelant Gemini 3 Pro avec thinking mode
        
        Args:
            prompt: Prompt utilisateur avec contexte
            system_prompt: Prompt système (instructions générales)
            temperature: Température (Gemini 3 recommande 1.0 par défaut)
            max_tokens: Nombre maximum de tokens en sortie
            thinking_level: Niveau de raisonnement (low/medium/high)
        
        Returns:
            Dict avec 'content', 'raw_response', 'model', 'thinking'
        """
        try:
            # Construire le prompt complet
            full_prompt = ""
            if system_prompt:
                full_prompt = f"INSTRUCTIONS:\n{system_prompt}\n\n---\n\n{prompt}"
            else:
                full_prompt = prompt
            
            # Utiliser le thinking_level fourni ou celui par défaut
            actual_thinking_level = thinking_level or self.thinking_level
            
            # Configuration pour cet appel
            # Note: Gemini 3 Pro utilise thinking_level="high" par défaut
            # Si on veut low, on doit le spécifier explicitement
            config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            
            # Ajouter thinking_config seulement si on veut "low" (pour économiser)
            if actual_thinking_level == "low":
                try:
                    config = types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                        thinking_config=types.ThinkingConfig(mode="low")
                    )
                except Exception as e:
                    logger.warning(f"⚠️ thinking_config not supported, using defaults: {e}")
                    # Fallback sans thinking_config
                    config = types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    )
            
            logger.info(f"🧠 Calling Gemini 3 Pro (thinking_level={actual_thinking_level} - default: high)...")
            logger.debug(f"Prompt length: {len(full_prompt)} chars")
            
            # Générer la réponse avec Gemini 3 Pro
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=config
            )
            
            # Extraire le contenu
            content = response.text if hasattr(response, 'text') else str(response)
            
            # Gemini 3 peut inclure un bloc de "thinking" séparé
            thinking_content = ""
            actual_content = content
            
            # Vérifier si le modèle a généré du raisonnement explicite
            if "<thinking>" in content and "</thinking>" in content:
                import re
                thinking_match = re.search(r'<thinking>(.*?)</thinking>', content, re.DOTALL)
                if thinking_match:
                    thinking_content = thinking_match.group(1).strip()
                    actual_content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL).strip()
            
            # Nettoyer le contenu avant parsing
            import re
            cleaned_content = actual_content
            
            # 1. Supprimer les commentaires // en fin de ligne
            cleaned_content = re.sub(r'//[^\n]*', '', cleaned_content)
            
            # 2. Remplacer les retours à la ligne dans les strings par des espaces
            # (cherche les strings entre guillemets et remplace \n par espace)
            def fix_strings(match):
                string_content = match.group(1)
                # Remplacer les retours à la ligne par des espaces
                fixed = string_content.replace('\n', ' ').replace('\r', ' ')
                # Supprimer les doubles espaces
                fixed = re.sub(r'\s+', ' ', fixed)
                return f'"{fixed}"'
            
            cleaned_content = re.sub(r'"([^"]*)"', fix_strings, cleaned_content)
            
            # 3. Supprimer les virgules avant les accolades fermantes (trailing commas)
            # Gérer les cas avec beaucoup d'espaces/retours à la ligne
            cleaned_content = re.sub(r',\s*([}\]])', r'\1', cleaned_content)
            
            # Parser le JSON de sortie
            try:
                parsed = json.loads(cleaned_content)
                
                # Extraire les métadonnées d'usage
                usage_metadata = {}
                if hasattr(response, 'usage_metadata'):
                    usage_metadata = {
                        "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                        "completion_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                        "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0),
                    }
                    
                    # Calculer le coût approximatif
                    prompt_tokens = usage_metadata.get("prompt_tokens", 0)
                    completion_tokens = usage_metadata.get("completion_tokens", 0)
                    
                    # Tarif Gemini 3 Pro : 2$ / 12$ pour < 200k tokens
                    input_cost = (prompt_tokens / 1_000_000) * 2.0
                    output_cost = (completion_tokens / 1_000_000) * 12.0
                    total_cost = input_cost + output_cost
                    
                    usage_metadata["estimated_cost_usd"] = round(total_cost, 4)
                    
                    logger.info(f"💰 Estimated cost: ${total_cost:.4f} USD")
                else:
                    usage_metadata = {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                        "estimated_cost_usd": 0.0
                    }
                
                result = {
                    "content": parsed.get("insight", actual_content),
                    "raw_response": actual_content,
                    "thinking": thinking_content,
                    "model": self.model_name,
                    "usage": usage_metadata
                }
                
                if thinking_content:
                    logger.info(f"💭 Thinking process (first 200 chars): {thinking_content[:200]}...")
                
                logger.info(f"✅ Gemini 3 Pro response generated successfully")
                return result
                
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Gemini response is not valid JSON: {e}")
                logger.error(f"Raw content (first 1000 chars): {actual_content[:1000]}")
                logger.error(f"Cleaned content (first 1000 chars): {cleaned_content[:1000]}")
                logger.error(f"Content around error position (chars 4600-4800): {cleaned_content[4600:4800] if len(cleaned_content) > 4600 else 'N/A'}")
                
                usage_metadata = {}
                if hasattr(response, 'usage_metadata'):
                    usage_metadata = {
                        "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                        "completion_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                        "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0),
                    }
                    
                    # Calculer le coût
                    prompt_tokens = usage_metadata.get("prompt_tokens", 0)
                    completion_tokens = usage_metadata.get("completion_tokens", 0)
                    input_cost = (prompt_tokens / 1_000_000) * 2.0
                    output_cost = (completion_tokens / 1_000_000) * 12.0
                    usage_metadata["estimated_cost_usd"] = round(input_cost + output_cost, 4)
                else:
                    usage_metadata = {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                        "estimated_cost_usd": 0.0
                    }
                
                return {
                    "content": actual_content,
                    "raw_response": actual_content,
                    "thinking": thinking_content,
                    "model": self.model_name,
                    "usage": usage_metadata
                }
        
        except Exception as e:
            logger.error(f"❌ Error calling Gemini 3 Pro: {e}")
            raise
    
    def generate_raw_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 1.0,
        thinking_level: Optional[str] = None
    ) -> str:
        """
        Génère du texte brut sans parsing JSON avec Gemini 3 Pro
        
        Args:
            prompt: Prompt avec les données de l'utilisateur
            system_prompt: Instructions système
            temperature: Température de génération (1.0 recommandé)
            thinking_level: Niveau de raisonnement (low/medium/high)
        
        Returns:
            Texte brut généré par Gemini
        """
        try:
            # Construire le prompt complet
            full_prompt = ""
            if system_prompt:
                full_prompt = f"INSTRUCTIONS:\n{system_prompt}\n\n---\n\n{prompt}"
            else:
                full_prompt = prompt
            
            # Utiliser le thinking_level fourni ou celui par défaut
            actual_thinking_level = thinking_level or self.thinking_level
            
            # Configuration pour cet appel
            config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=8192,
            )
            
            logger.info(f"🧠 Calling Gemini 3 Pro for raw text (thinking_level={actual_thinking_level})...")
            logger.debug(f"Prompt length: {len(full_prompt)} chars")
            
            # Générer la réponse avec Gemini 3 Pro
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=config
            )
            
            # Extraire le contenu
            content = response.text if hasattr(response, 'text') else str(response)
            
            # Gemini 3 peut inclure un bloc de "thinking" séparé
            thinking_content = ""
            actual_content = content
            
            # Vérifier si le modèle a généré du raisonnement explicite
            if "<thinking>" in content and "</thinking>" in content:
                import re
                thinking_match = re.search(r'<thinking>(.*?)</thinking>', content, re.DOTALL)
                if thinking_match:
                    thinking_content = thinking_match.group(1).strip()
                    actual_content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL).strip()
            
            # Log des métadonnées d'usage
            if hasattr(response, 'usage_metadata'):
                usage_metadata = {
                    "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                    "completion_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                    "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0),
                }
                
                # Calculer le coût approximatif
                prompt_tokens = usage_metadata.get("prompt_tokens", 0)
                completion_tokens = usage_metadata.get("completion_tokens", 0)
                
                # Tarif Gemini 3 Pro : 2$ / 12$ pour < 200k tokens
                input_cost = (prompt_tokens / 1_000_000) * 2.0
                output_cost = (completion_tokens / 1_000_000) * 12.0
                total_cost = input_cost + output_cost
                
                logger.info(f"💰 Estimated cost: ${total_cost:.4f} USD")
                logger.info(f"📊 Tokens: {prompt_tokens} in, {completion_tokens} out")
            
            if thinking_content:
                logger.info(f"💭 Thinking process (first 200 chars): {thinking_content[:200]}...")
            
            logger.info(f"✅ Generated {len(actual_content)} chars of raw text")
            return actual_content
        
        except Exception as e:
            logger.error(f"❌ Error generating raw text with Gemini 3 Pro: {e}", exc_info=True)
            raise
    
    def generate_cards_explanation(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 1.0,
        thinking_level: Optional[str] = None
    ) -> Dict:
        """
        Génère les cartes d'explication du score d'énergie avec Gemini 3 Pro
        
        Args:
            prompt: Prompt avec les données de l'utilisateur
            system_prompt: Instructions système
            temperature: Température de génération (1.0 recommandé)
            thinking_level: Niveau de raisonnement (low/medium/high)
        
        Returns:
            Dict avec les cartes générées et le raisonnement
        """
        try:
            result = self.generate_insight(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=8192,
                thinking_level=thinking_level
            )
            
            # Extraire et valider les cartes
            content = result.get("raw_response", "{}")
            
            try:
                parsed = json.loads(content)
                
                # Valider la structure
                if "cards" not in parsed:
                    logger.error("❌ Missing 'cards' field in Gemini response")
                    raise ValueError("Missing 'cards' field")
                
                # Valider que chaque carte a les champs requis
                for i, card in enumerate(parsed["cards"]):
                    required_fields = ["type", "title", "text", "analogy"]
                    for field in required_fields:
                        if field not in card:
                            logger.error(f"❌ Missing required field '{field}' in card {i}")
                            raise ValueError(f"Missing required field '{field}' in card {i}")
                
                # Ajouter le raisonnement et le coût aux métadonnées
                if result.get("thinking"):
                    parsed["_thinking"] = result.get("thinking")
                    logger.info(f"💭 Thinking process included in response metadata")
                
                if result.get("usage", {}).get("estimated_cost_usd"):
                    parsed["_cost"] = result.get("usage", {}).get("estimated_cost_usd")
                    logger.info(f"💰 Cost: ${parsed['_cost']:.4f} USD")
                
                logger.info(f"✅ Generated {len(parsed['cards'])} cards with Gemini 3 Pro")
                return parsed
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"❌ Invalid JSON from Gemini: {e}")
                logger.debug(f"Raw response: {content[:500]}")
                raise ValueError(f"Invalid response from Gemini: {str(e)}")
        
        except Exception as e:
            logger.error(f"❌ Error generating cards with Gemini 3 Pro: {e}")
            raise


# Alias pour compatibilité
GeminiClient = GeminiThinkingClient


# Exemple d'utilisation
if __name__ == "__main__":
    import sys
    
    try:
        client = GeminiThinkingClient()
        
        test_prompt = """
        Génère 2 cartes d'explication pour un score d'énergie de 45%.
        
        Données:
        - HRV: 25ms (baseline: 50ms)
        - RHR: 65bpm (baseline: 60bpm)
        - Sommeil: 5h30 (besoin: 8h)
        
        Format JSON avec champs: type, title, text, analogy, metrics
        """
        
        system_prompt = """Tu es un expert en wellness. Génère des explications claires et empathiques.
        Réponds au format JSON strict avec un champ "cards" contenant un tableau de cartes."""
        
        result = client.generate_cards_explanation(
            prompt=test_prompt,
            system_prompt=system_prompt,
            thinking_level="high"
        )
        
        print("✅ Test réussi!")
        print(f"Nombre de cartes: {len(result.get('cards', []))}")
        print(f"Coût estimé: ${result.get('_cost', 0):.4f} USD")
        if result.get('_thinking'):
            print(f"Raisonnement: {result['_thinking'][:200]}...")
        
    except Exception as e:
        print(f"❌ Test échoué: {e}")
        sys.exit(1)
