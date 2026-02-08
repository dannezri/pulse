# 📱 Mise à jour mobile - Consumer Mapping

**Date**: 29 janvier 2026  
**Problème résolu**: "TDAH" retournait "Aucun résultat trouvé"

## 🔍 Diagnostic

L'API backend retournait correctement:
```json
{
  "suggestions": [{"label": "TDAH (...)", "codes": ["6A05"]}],
  "results": [],
  "more_results": true
}
```

Mais le mobile ne gérait que l'ancien format `{results: [...]}` et ignorait les **suggestions**.

## ✅ Corrections appliquées

### 1️⃣ Hook `useConditions.ts`

**Avant**:
```typescript
const searchConditions = async (...): Promise<SearchResult[]> => {
  const data = await response.json();
  return data.results || [];
}
```

**Après**:
```typescript
const searchConditions = async (...): Promise<any> => {
  const data = await response.json();
  return {
    suggestions: data.suggestions || [],
    results: data.results || [],
    more_results: data.more_results || false
  };
}
```

- ✅ Ajout du paramètre `&consumer_friendly=true` à l'URL
- ✅ Retour du format complet `{suggestions, results, more_results}`

### 2️⃣ Composant `ConditionPicker.tsx`

**Nouveaux states**:
```typescript
const [suggestions, setSuggestions] = useState<any[]>([]);
const [moreResults, setMoreResults] = useState(false);
```

**Gestion de la réponse**:
```typescript
const response = await searchConditions(searchQuery, 'fr');

if (response && 'suggestions' in response) {
  setSuggestions(response.suggestions || []);
  setSearchResults(response.results || []);
  setMoreResults(response.more_results || false);
  
  // Aucun résultat seulement si ni suggestions ni résultats
  if (response.suggestions.length === 0 && response.results.length === 0) {
    setSearchError('Aucun résultat trouvé');
  }
}
```

**Nouvelle UI à 2 niveaux**:

1. **Section "✨ Suggestions"** (prioritaire):
   - Affichée en premier avec badge orange `#FF9500`
   - Border et shadow colorés
   - Badge "Terme courant"
   - Pour les termes grand public (TDAH, dépression, diabète...)

2. **Section "Résultats détaillés"**:
   - Affichée en dessous
   - Pour les codes ICD-11 techniques
   - Avec indication `+ autres résultats` si `more_results: true`

## 🎨 Nouveaux styles

```typescript
suggestionCard: {
  backgroundColor: '#1C1C1E',
  borderRadius: 20,
  borderWidth: 2,
  borderColor: '#FF9500',      // Orange pour distinction
  shadowColor: '#FF9500',
  shadowOpacity: 0.2,
  // ...
}

suggestionBadge: {
  backgroundColor: '#FF950020',  // Orange semi-transparent
  // ...
}
```

## 🧪 Test

Pour vérifier que tout fonctionne:

1. Ouvrir l'app mobile
2. Aller dans **Profil** → **Conditions de santé**
3. Rechercher **"TDAH"**
4. Devrait afficher:
   - ✨ **Suggestions**: "TDAH (Trouble de l'attention...)" avec badge orange
   - 📋 **Résultats détaillés**: (vide ou autres résultats ICD-11)

5. Tester aussi: "dépression", "diabète", "SOP", "anxiété", "insomnie"

## 📊 Résultat attendu

- ✅ Recherche "TDAH" → Affiche la suggestion
- ✅ Recherche "dépression" → Affiche suggestions + résultats détaillés
- ✅ Recherche "xyz123" → "Aucun résultat trouvé"
- ✅ Clic sur suggestion → Ajoute la condition
- ✅ Badge "Ajouté" + ✓ vert après ajout

## 🔄 Prochaines étapes (optionnel)

- [ ] Accordéon pour "Résultats détaillés" (seulement si beaucoup de résultats)
- [ ] Animation de transition entre suggestions et détails
- [ ] Compteur de conditions ajoutées dans le header du modal
