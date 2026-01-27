"""
Client LLM pour génération d'insights
Abstraction pour appeler GPT-4o (ou autre provider configurable)
"""

import os
import json
import logging
from typing import Dict, Optional
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client pour appeler un LLM (GPT-4o par défaut)
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialise le client LLM
        
        Args:
            api_key: Clé API OpenAI (ou depuis env OPENAI_API_KEY)
            model: Modèle à utiliser (défaut: gpt-4o)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY must be set in environment or passed as parameter")
        
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.client = OpenAI(api_key=self.api_key)
    
    def generate_insight(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> Dict:
        """
        Génère un insight en appelant le LLM
        
        Args:
            prompt: Prompt utilisateur avec contexte
            system_prompt: Prompt système (instructions générales)
            temperature: Température pour la génération (0.0-2.0)
            max_tokens: Nombre maximum de tokens en sortie
        
        Returns:
            Dict avec 'content' (texte généré) et 'metadata' (infos supplémentaires)
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}  # Forcer JSON en sortie
            )
            
            content = response.choices[0].message.content
            
            # Parser le JSON en sortie
            try:
                parsed = json.loads(content)
                return {
                    "content": parsed.get("insight", content),  # Fallback si pas de champ "insight"
                    "raw_response": content,
                    "model": self.model,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
            except json.JSONDecodeError:
                # Si le JSON n'est pas valide, retourner le texte brut
                logger.warning(f"LLM response is not valid JSON, using raw content: {content[:100]}")
                return {
                    "content": content,
                    "raw_response": content,
                    "model": self.model,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
        
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            raise
