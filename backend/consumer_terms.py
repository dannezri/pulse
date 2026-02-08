"""
Consumer Terms Mapping - Termes grand public vers codes ICD-11

Objectif: Rendre la recherche de conditions de santé accessible aux non-professionnels
en proposant des termes simples et en filtrant le bruit clinique.
"""

from typing import Dict, List, Optional

# Mapping termes grand public → codes/patterns ICD-11
# Format: terme_simple: {label, codes, keywords, category}
CONSUMER_TERMS = {
    # Troubles mentaux
    "depression": {
        "label": "Dépression",
        "label_en": "Depression",
        "codes": ["6A70", "6A71"],  # Episode dépressif, Trouble dépressif récurrent
        "keywords": ["dépression", "dépressif", "depression", "depressive"],
        "category": "mental",
        "exclude_keywords": ["néonatal", "neonatal", "périnatal", "perinatal"]
    },
    "depression_persistante": {
        "label": "Dépression persistante (dysthymie)",
        "label_en": "Persistent depression (dysthymia)",
        "codes": ["6A72"],
        "keywords": ["dysthymie", "dysthymia", "persistant"],
        "category": "mental"
    },
    "depression_postpartum": {
        "label": "Dépression post-partum",
        "label_en": "Postpartum depression",
        "codes": ["6E20.1"],
        "keywords": ["post-partum", "postpartum", "périnatal"],
        "category": "mental"
    },
    "anxiete": {
        "label": "Anxiété généralisée",
        "label_en": "Generalized anxiety",
        "codes": ["6B00"],
        "keywords": ["anxiété", "anxiety", "anxieux"],
        "category": "mental",
        "exclude_keywords": ["panique", "panic", "social"]
    },
    "anxiete_depression": {
        "label": "Anxiété + dépression (mixte)",
        "label_en": "Mixed anxiety and depression",
        "codes": ["6A73"],
        "keywords": ["mixte", "mixed", "anxieux dépressif"],
        "category": "mental"
    },
    "tdah": {
        "label": "TDAH (Trouble de l'attention avec hyperactivité)",
        "label_en": "ADHD",
        "codes": ["6A05"],
        "keywords": ["tdah", "adhd", "attention", "hyperactivité", "hyperactivity"],
        "category": "mental"
    },
    "trouble_panique": {
        "label": "Trouble panique",
        "label_en": "Panic disorder",
        "codes": ["6B01"],
        "keywords": ["panique", "panic"],
        "category": "mental"
    },
    
    # Endocrinologie
    "diabete_type1": {
        "label": "Diabète de type 1",
        "label_en": "Type 1 diabetes",
        "codes": ["5A10"],
        "keywords": ["diabète type 1", "diabetes type 1"],
        "category": "endocrine"
    },
    "diabete_type2": {
        "label": "Diabète de type 2",
        "label_en": "Type 2 diabetes",
        "codes": ["5A11"],
        "keywords": ["diabète type 2", "diabetes type 2"],
        "category": "endocrine"
    },
    "diabete": {
        "label": "Diabète",
        "label_en": "Diabetes",
        "codes": ["5A10", "5A11"],
        "keywords": ["diabète", "diabetes"],
        "category": "endocrine",
        "exclude_keywords": ["néonatal", "neonatal", "gestationnel", "gestational"]
    },
    "sop": {
        "label": "Syndrome des ovaires polykystiques (SOP)",
        "label_en": "Polycystic ovary syndrome (PCOS)",
        "codes": ["GA34.3"],
        "keywords": ["ovaires polykystiques", "pcos", "sop", "polycystic"],
        "category": "reproductive"
    },
    "hypothyroidie": {
        "label": "Hypothyroïdie",
        "label_en": "Hypothyroidism",
        "codes": ["5A00"],
        "keywords": ["hypothyroïdie", "hypothyroidism", "thyroïde"],
        "category": "endocrine"
    },
    
    # Troubles du sommeil
    "insomnie": {
        "label": "Insomnie",
        "label_en": "Insomnia",
        "codes": ["7A00"],
        "keywords": ["insomnie", "insomnia", "sommeil"],
        "category": "sleep"
    },
    "apnee_sommeil": {
        "label": "Apnée du sommeil",
        "label_en": "Sleep apnea",
        "codes": ["7A40"],
        "keywords": ["apnée", "apnea"],
        "category": "sleep"
    },
    
    # Autres troubles courants
    "migraine": {
        "label": "Migraine",
        "label_en": "Migraine",
        "codes": ["8A80"],
        "keywords": ["migraine"],
        "category": "neurological"
    },
    "asthme": {
        "label": "Asthme",
        "label_en": "Asthma",
        "codes": ["CA23"],
        "keywords": ["asthme", "asthma"],
        "category": "respiratory"
    },
    "hypertension": {
        "label": "Hypertension artérielle",
        "label_en": "Hypertension",
        "codes": ["BA00"],
        "keywords": ["hypertension", "tension", "blood pressure"],
        "category": "cardiovascular"
    },
}


def get_consumer_suggestion(query: str, lang: str = "fr") -> Optional[Dict]:
    """
    Trouve une suggestion "consommateur" pour une requête
    
    Args:
        query: Terme recherché (ex: "depression")
        lang: Langue (fr ou en)
    
    Returns:
        Dict avec label, codes, category ou None
    """
    query_lower = query.lower().strip()
    
    # Recherche exacte
    if query_lower in CONSUMER_TERMS:
        term = CONSUMER_TERMS[query_lower]
        return {
            "label": term["label"] if lang == "fr" else term.get("label_en", term["label"]),
            "codes": term["codes"],
            "category": term["category"],
            "kind": "consumer"
        }
    
    # Recherche par keywords
    for key, term in CONSUMER_TERMS.items():
        keywords = term.get("keywords", [])
        for keyword in keywords:
            if keyword.lower() in query_lower or query_lower in keyword.lower():
                return {
                    "label": term["label"] if lang == "fr" else term.get("label_en", term["label"]),
                    "codes": term["codes"],
                    "category": term["category"],
                    "kind": "consumer"
                }
    
    return None


def score_icd11_result(result: Dict, query: str) -> float:
    """
    Score un résultat ICD-11 pour le ranking
    
    Args:
        result: Résultat ICD-11 {code, display, category}
        query: Terme recherché
    
    Returns:
        Score (plus haut = meilleur)
    """
    score = 0.0
    display_lower = result.get("display", "").lower()
    code = result.get("code", "")
    category = result.get("category", "").lower()
    
    # +3 si le terme exact est dans le libellé
    if query.lower() in display_lower:
        score += 3.0
    
    # +2 si catégorie pertinente (mental, endocrine, etc.)
    if any(cat in category for cat in ["mental", "endocrin", "reproduct", "sleep"]):
        score += 2.0
    
    # -3 si "unspecified" ou "other"
    if any(word in display_lower for word in ["sans précision", "non précisé", "unspecified", "other", "autre"]):
        score -= 3.0
    
    # -3 si code contient "unspecified" patterns
    if any(pattern in code.lower() for pattern in ["z", "other", "unsp"]):
        score -= 2.0
    
    # -2 si contient des termes cliniques trop spécifiques
    clinical_terms = [
        "néonatal", "neonatal", "périnatal", "perinatal",
        "induit par", "induced by", "dû à", "due to",
        "avec caractéristiques", "with features"
    ]
    if any(term in display_lower for term in clinical_terms):
        score -= 2.0
    
    # -2 si libellé très long (> 80 caractères = trop clinique)
    if len(result.get("display", "")) > 80:
        score -= 2.0
    
    # -1 si libellé très court (< 10 caractères = trop vague)
    if len(result.get("display", "")) < 10:
        score -= 1.0
    
    return score


def filter_and_rank_results(
    results: List[Dict],
    query: str,
    max_results: int = 5
) -> List[Dict]:
    """
    Filtre et classe les résultats ICD-11
    
    Args:
        results: Liste de résultats ICD-11
        query: Terme recherché
        max_results: Nombre max de résultats (défaut: 5)
    
    Returns:
        Liste filtrée et classée
    """
    # Scorer chaque résultat
    scored_results = []
    for result in results:
        score = score_icd11_result(result, query)
        if score > -3.0:  # Filtrer les très mauvais scores
            scored_results.append({
                **result,
                "_score": score
            })
    
    # Trier par score décroissant
    scored_results.sort(key=lambda x: x["_score"], reverse=True)
    
    # Dédupliquer par display normalisé
    seen_displays = set()
    unique_results = []
    for result in scored_results:
        display_normalized = result["display"].lower().strip()
        if display_normalized not in seen_displays:
            seen_displays.add(display_normalized)
            unique_results.append(result)
    
    # Limiter au max
    return unique_results[:max_results]


def get_consumer_suggestions_for_query(query: str, lang: str = "fr") -> List[Dict]:
    """
    Obtient les suggestions "consommateur" pour une requête
    
    Args:
        query: Terme recherché
        lang: Langue
    
    Returns:
        Liste de suggestions consumer-friendly
    """
    suggestions = []
    query_lower = query.lower().strip()
    
    # Chercher les correspondances dans CONSUMER_TERMS
    for key, term in CONSUMER_TERMS.items():
        keywords = term.get("keywords", [])
        exclude_keywords = term.get("exclude_keywords", [])
        
        # Vérifier si match
        match = False
        for keyword in keywords:
            if keyword.lower() in query_lower or query_lower in keyword.lower():
                match = True
                break
        
        # Exclure si keyword à exclure
        if match:
            for exclude in exclude_keywords:
                if exclude.lower() in query_lower:
                    match = False
                    break
        
        if match:
            suggestions.append({
                "label": term["label"] if lang == "fr" else term.get("label_en", term["label"]),
                "codes": term["codes"],
                "category": term["category"],
                "kind": "consumer"
            })
    
    return suggestions[:5]  # Max 5 suggestions
