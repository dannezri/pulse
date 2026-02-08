#!/usr/bin/env python3
"""Test du nettoyage automatique du JSON généré par Gemini"""

import re
import json

def _clean_json_response(text: str) -> str:
    """
    Nettoie la réponse de Gemini si elle contient du JSON malgré les instructions.
    Extrait le contenu textuel et le reformate en texte naturel.
    """
    # Vérifier si le texte contient du JSON markdown
    if "```json" in text or "```" in text:
        print("⚠️  Gemini generated JSON despite instructions, cleaning...")
        
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
                print("❌ No code fences found")
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
                print("✅ Successfully cleaned JSON response to natural text")
                return cleaned
            else:
                print("⚠️  Failed to extract content from JSON, returning original")
                return text
                
        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse JSON in response: {e}, returning original")
            return text
    
    # Pas de JSON détecté, retourner tel quel
    print("✅ No JSON detected, text is clean")
    return text


# Test avec le texte de l'utilisateur
test_text = """```json
[
  {
    "title": "🔋 Analyse Globale : 36%",
    "subtitle": "Journée Fragile",
    "content": "Aujourd'hui, ton score d'énergie est à 36%, ce qui classe ta journée comme 'Fragile'. Même si tu n'as pas de dette de sommeil apparente (100%), ton corps semble lutter pour convertir ce repos en énergie utilisable. C'est comme avoir fait le plein d'essence, mais avoir un moteur qui surchauffe : le carburant est là, mais la mécanique ne suit pas encore.",
    "type": "warning"
  },
  {
    "title": "⚠️ Surcharge Détectée",
    "subtitle": "Récupération : 19% | Surcharge : 13%",
    "content": "C'est le point critique du jour. Ton indicateur de récupération est très bas (19%) et le signal de surcharge est allumé (13%). Cela indique que ton système nerveux est sous tension, probablement dû à un stress cumulé ou une activité récente intense. Ton corps est en mode 'protection' et refuse de libérer de l'énergie pour ne pas s'épuiser davantage.",
    "type": "alert"
  },
  {
    "title": "💊 Le Cocktail Chimique",
    "subtitle": "Frein vs Accélérateur",
    "content": "Il y a un véritable bras de fer chimique en coulisses. D'un côté, la Sertraline (+28.5%) tente de booster ton énergie. De l'autre, la Mirtazapine et la Mélatonine agissent comme des freins nécessaires (-25.7% cumulés) pour stabiliser ton humeur et ton sommeil. Avec l'impact de la dépression (-9.5%), ton métabolisme travaille dur pour maintenir l'équilibre, ce qui consomme une part de ton énergie disponible.",
    "type": "info"
  },
  {
    "title": "🔍 Angle Mort",
    "subtitle": "Données biométriques manquantes",
    "content": "Note importante : Je n'ai pas reçu tes données cardiaques (HRV, RHR) ni tes scores de sommeil précis (valeurs 'None'). Mon indice de confiance n'est donc que de 27%. Sans ces données, je ne peux pas voir comment ton cœur réagit physiquement. Assure-toi que ton capteur est bien synchronisé pour que je puisse affiner cette analyse demain.",
    "type": "tip"
  }
]
```"""

print("=" * 80)
print("TEST : Nettoyage JSON Gemini")
print("=" * 80)
print("\n📥 INPUT (JSON avec balises):")
print(test_text[:200] + "...")
print("\n" + "=" * 80)
print("\n🔄 PROCESSING...")
print()

cleaned = _clean_json_response(test_text)

print("\n" + "=" * 80)
print("📤 OUTPUT (texte nettoyé):")
print("=" * 80)
print(cleaned)
print("\n" + "=" * 80)
print(f"✅ Longueur: {len(cleaned)} caractères")
print("=" * 80)
