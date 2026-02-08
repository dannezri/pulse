# 🎯 Consumer Mapping - Implémentation Complète

## Vue d'ensemble

Système de **"consumer mapping"** pour rendre la recherche de conditions de santé accessible et intuitive, avec suggestions grand public et filtrage intelligent des résultats cliniques.

---

## ✅ Ce qui a été implémenté

### 1. Backend - Consumer Terms Database

**Fichier**: `backend/consumer_terms.py`

**Fonctionnalités**:
- ✅ Base de ~20 termes courants (extensible à 150+)
- ✅ Mapping termes simples → codes ICD-11
- ✅ Support multilingue (FR/EN)
- ✅ Keywords et exclude_keywords pour matching intelligent
- ✅ Catégorisation (mental, endocrine, sleep, etc.)

**Termes implémentés**:
- **Santé mentale**: Dépression, TDAH, Anxiété, Trouble panique, Dépression post-partum
- **Endocrinologie**: Diabète type 1/2, SOP, Hypothyroïdie
- **Sommeil**: Insomnie, Apnée du sommeil
- **Autres**: Migraine, Asthme, Hypertension

### 2. Système de Scoring et Ranking

**Fonction**: `score_icd11_result()`

**Règles de scoring**:
```python
+3  : Terme exact dans le libellé
+2  : Catégorie pertinente (mental, endocrine, etc.)
-3  : "sans précision", "unspecified", "other"
-2  : Termes trop cliniques (néonatal, induit par, etc.)
-2  : Libellé trop long (> 80 caractères)
-1  : Libellé trop court (< 10 caractères)
```

**Résultat**: Top 5 résultats les plus pertinents

### 3. Filtrage et Déduplication

**Fonction**: `filter_and_rank_results()`

**Actions**:
- ✅ Score chaque résultat
- ✅ Filtre les scores < -3.0
- ✅ Trie par score décroissant
- ✅ Déduplique par display normalisé
- ✅ Limite à max_results (défaut: 5)

### 4. Nouveau Format API

**Endpoint**: `GET /api/terminology/icd11/search?q=...&consumer_friendly=true`

**Ancienne réponse (legacy)**:
```json
{
  "system": "icd11",
  "query": "depression",
  "count": 20,
  "results": [...]
}
```

**Nouvelle réponse (consumer-friendly)**:
```json
{
  "system": "icd11",
  "query": "depression",
  "suggestions": [
    {
      "label": "Dépression",
      "codes": ["6A70", "6A71"],
      "category": "mental",
      "kind": "consumer"
    },
    {
      "label": "Dépression persistante (dysthymie)",
      "codes": ["6A72"],
      "category": "mental",
      "kind": "consumer"
    },
    {
      "label": "Anxiété + dépression (mixte)",
      "codes": ["6A73"],
      "category": "mental",
      "kind": "consumer"
    }
  ],
  "results": [
    {
      "code": "6A70",
      "display": "Épisode dépressif",
      "category": "Troubles mentaux",
      "_score": 5.0
    }
  ],
  "more_results": true
}
```

### 5. Client ICD-11 Amélioré

**Fichier**: `backend/icd11_client.py`

**Modifications**:
- ✅ Paramètre `consumer_friendly` (True par défaut)
- ✅ Fonction `_format_consumer_response()`
- ✅ Intégration avec `consumer_terms.py`
- ✅ Nettoyage HTML des résultats
- ✅ Compatible avec mode fallback

---

## 🎨 UX côté Mobile

### Format attendu

**Affichage en 2 sections**:

```
┌─────────────────────────────────────┐
│ 🔍 Recherche: "dépression"          │
├─────────────────────────────────────┤
│                                     │
│ ✨ SUGGESTIONS (Grand public)       │
│                                     │
│ ┌─────────────────────────────────┐│
│ │ 💭 Dépression                   ││
│ │ Condition courante              ││
│ │                          [+]    ││
│ └─────────────────────────────────┘│
│                                     │
│ ┌─────────────────────────────────┐│
│ │ 🧠 Dépression persistante       ││
│ │ (dysthymie)                     ││
│ │                          [+]    ││
│ └─────────────────────────────────┘│
│                                     │
│ ┌─────────────────────────────────┐│
│ │ 💫 Anxiété + dépression         ││
│ │ (mixte)                         ││
│ │                          [+]    ││
│ └─────────────────────────────────┘│
│                                     │
├─────────────────────────────────────┤
│                                     │
│ 📋 RÉSULTATS DÉTAILLÉS             │
│ (Cliquer pour voir plus)           │
│                              [▼]    │
│                                     │
└─────────────────────────────────────┘
```

---

## 🔄 Migration Mobile (À faire)

### Étape 1: Mettre à jour useConditions.ts

```typescript
export interface SearchResponse {
  query: string;
  suggestions: ConsumerSuggestion[];
  results: SearchResult[];
  more_results: boolean;
}

const searchConditions = async (query: string): Promise<SearchResponse> => {
  // Appeler avec consumer_friendly=true
  const response = await fetch(
    `${API_URL}/api/terminology/icd11/search?q=${q}&consumer_friendly=true`
  );
  return await response.json();
};
```

### Étape 2: Mettre à jour ConditionPicker.tsx

```typescript
const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);

// Afficher suggestions en premier
{searchResponse?.suggestions.map((suggestion) => (
  <SuggestionCard
    key={suggestion.label}
    suggestion={suggestion}
    onPress={() => handleAddSuggestion(suggestion)}
  />
))}

// Puis résultats détaillés dans accordéon
<Collapsible title="Résultats détaillés">
  {searchResponse?.results.map((result) => (
    <ResultCard... />
  ))}
</Collapsible>
```

---

## 📊 Exemples de Recherche

### Exemple 1: "dépression"

**Suggestions**:
1. Dépression
2. Dépression persistante (dysthymie)
3. Anxiété + dépression (mixte)
4. Dépression post-partum

**Résultats filtrés**:
1. Épisode dépressif (6A70) - Score: 5.0
2. Trouble dépressif récurrent (6A71) - Score: 4.0
3. Dysthymie (6A72) - Score: 3.0

**Exclus** (score trop bas):
- Dépression néonatale
- Dépression sans précision
- Dépression induite par substance

### Exemple 2: "TDAH"

**Suggestions**:
1. TDAH (Trouble de l'attention avec hyperactivité)

**Résultats filtrés**:
1. Trouble déficitaire de l'attention avec hyperactivité (6A05) - Score: 5.0

### Exemple 3: "diabète"

**Suggestions**:
1. Diabète
2. Diabète de type 1
3. Diabète de type 2

**Résultats filtrés**:
1. Diabète sucré de type 2 (5A11) - Score: 4.0
2. Diabète sucré de type 1 (5A10) - Score: 4.0

**Exclus**:
- Diabète néonatal
- Diabète gestationnel (sauf si recherche contient "grossesse")

---

## 🧪 Tests

### Test Backend

```bash
cd backend

# Test 1: Recherche consumer-friendly
curl "http://localhost:9000/api/terminology/icd11/search?q=depression&consumer_friendly=true" | python3 -m json.tool

# Attendu: suggestions + results + more_results

# Test 2: Recherche legacy (compatibilité)
curl "http://localhost:9000/api/terminology/icd11/search?q=depression&consumer_friendly=false" | python3 -m json.tool

# Attendu: format ancien (count + results)
```

### Test Scoring

```python
from consumer_terms import score_icd11_result

# Bon résultat
result = {
    "code": "6A70",
    "display": "Épisode dépressif",
    "category": "Troubles mentaux"
}
score = score_icd11_result(result, "depression")
# Attendu: ~5.0

# Mauvais résultat
result = {
    "code": "6A70.Z",
    "display": "Dépression sans précision néonatale induite par substance",
    "category": "Troubles mentaux"
}
score = score_icd11_result(result, "depression")
# Attendu: ~-5.0 (filtré)
```

---

## 🎯 Avantages UX

### Avant (Résultats bruts ICD-11)
```
20 résultats cliniques:
- Diabète sucré, type non précisé
- Diabète néonatal transitoire
- Diabète gestationnel
- Diabète induit par corticostéroïdes
- ...
```
❌ Complexe
❌ Trop de choix
❌ Termes techniques

### Après (Consumer mapping)
```
3-5 suggestions simples:
✅ Diabète
✅ Diabète de type 1
✅ Diabète de type 2

+ "Voir plus de résultats" si besoin
```
✅ Simple
✅ Rapide
✅ Grand public

---

## 📈 Métriques de succès

### KPIs attendus
- ⬆️ **+50%** d'utilisateurs ajoutant des conditions (grâce aux suggestions)
- ⬇️ **-70%** de temps de recherche (5-6 choix vs 20)
- ⬇️ **-60%** d'abandons (clarté accrue)
- ⬆️ **+40%** de satisfaction (feedback qualitatif)

### Logs à surveiller
```
INFO: Recherche "depression" → 3 suggestions, 5 résultats filtrés (12 exclus)
INFO: Utilisateur a sélectionné suggestion "Dépression" (consumer)
INFO: Utilisateur a étendu "Résultats détaillés" (2% des cas)
```

---

## 🔮 Évolutions futures

### Phase 2: Plus de termes
- Ajouter 100+ termes courants
- Maladies chroniques (arthrite, etc.)
- Troubles du sommeil avancés
- Allergies communes

### Phase 3: Personnalisation
- Suggestions basées sur l'historique
- Suggestions contextuelles (âge, genre)
- Apprentissage des préférences utilisateur

### Phase 4: Multi-langues
- Espagnol, allemand, italien
- Adaptation culturelle des termes

---

## ✅ Checklist d'implémentation

### Backend ✅
- [x] Créer `consumer_terms.py`
- [x] Ajouter scoring/ranking
- [x] Modifier `icd11_client.py`
- [x] Mettre à jour endpoint API
- [x] Tests unitaires
- [x] 0 erreur de lint

### Mobile 🔄 (En cours)
- [x] Mettre à jour interfaces TypeScript
- [ ] Modifier `searchConditions()` dans hook
- [ ] Créer composant `SuggestionCard`
- [ ] Ajouter section "Suggestions"
- [ ] Ajouter accordéon "Résultats détaillés"
- [ ] Gérer `more_results`
- [ ] Tests UI

---

## 📚 Ressources

- **Code**: `backend/consumer_terms.py`, `backend/icd11_client.py`
- **API**: `GET /api/terminology/icd11/search`
- **Docs ICD-11**: https://icd.who.int/
- **Ce document**: Source de vérité pour l'implémentation

---

**Date**: 29 janvier 2026  
**Status**: ✅ Backend complet, Mobile en cours  
**Impact**: 🚀 UX transformée (5-6 choix vs 20)
