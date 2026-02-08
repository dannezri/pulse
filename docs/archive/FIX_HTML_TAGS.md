# 🔧 Correction: Affichage HTML dans les résultats

## 🐛 Problème identifié

Les résultats de recherche ICD-11 affichaient du HTML brut:

```
❌ Avant:
<em class='found'>Diabète</em> sucré, type non précisé
<em class='found'>Diabète</em> sucré néonatal, sans précision
```

## ✅ Solution appliquée

Ajout d'une fonction de nettoyage HTML dans `icd11_client.py`:

```python
def _clean_html(self, text: str) -> str:
    """
    Nettoie les balises HTML d'un texte
    """
    if not text:
        return ""
    
    # Supprimer toutes les balises HTML
    clean_text = re.sub(r'<[^>]+>', '', text)
    
    # Décoder les entités HTML courantes
    clean_text = clean_text.replace('&amp;', '&')
    clean_text = clean_text.replace('&lt;', '<')
    clean_text = clean_text.replace('&gt;', '>')
    clean_text = clean_text.replace('&quot;', '"')
    clean_text = clean_text.replace('&#39;', "'")
    
    return clean_text.strip()
```

## 📊 Résultat

```
✅ Après:
Diabète sucré, type non précisé
Diabète sucré néonatal, sans précision
```

## 🔄 Changements appliqués

### 1. Import ajouté
```python
import re  # Pour regex de nettoyage HTML
```

### 2. Fonction de nettoyage créée
- Supprime toutes les balises HTML (`<em>`, `<span>`, `<strong>`, etc.)
- Décode les entités HTML (`&amp;`, `&quot;`, etc.)
- Trim les espaces

### 3. Application dans la normalisation
```python
# Récupérer le titre
title = item.get("title", "")

# Nettoyer le HTML du titre
title = self._clean_html(title)
```

## 🧪 Tests

### Test 1: Balises simples
```python
Input:  "<em class='found'>Diabète</em>"
Output: "Diabète"
```

### Test 2: Balises multiples
```python
Input:  "<em>Trouble</em> <strong>déficitaire</strong>"
Output: "Trouble déficitaire"
```

### Test 3: Entités HTML
```python
Input:  "L&#39;anxiété &amp; la dépression"
Output: "L'anxiété & la dépression"
```

### Test 4: Mode dégradé (fallback)
Les données de secours sont déjà propres, pas de HTML dedans.

## 📱 Impact mobile

**Avant:**
```
┌─────────────────────────────────────┐
│ <em class='found'>Diabète</em>     │
│ sucré, type non précisé             │
│                                     │
│ • 05                                │
│ Code ICD-11: 1697306310             │
└─────────────────────────────────────┘
```

**Après:**
```
┌─────────────────────────────────────┐
│ Diabète sucré, type non précisé     │
│                                     │
│ ┌──────────────────────┐           │
│ │ 🟣 Endocrinologie    │           │
│ └──────────────────────┘           │
│ Code ICD-11: 5A11                   │
│                              ┌───┐  │
│                              │ + │  │
│                              └───┘  │
└─────────────────────────────────────┘
```

## ✅ Validation

- [x] Import `re` ajouté
- [x] Fonction `_clean_html()` créée
- [x] Appliquée dans `search()`
- [x] 0 erreur de lint
- [x] Import du module réussi
- [x] Compatible avec mode dégradé

## 🚀 Déploiement

**Action requise:** Redémarrer le serveur backend

```bash
# 1. Arrêter le serveur (Ctrl+C)
# 2. Redémarrer
cd /Users/dannezri/Desktop/Pulse/backend
python3 api_server.py
```

Après redémarrage:
- Les nouvelles recherches afficheront du texte propre
- Le cache existant continuera d'afficher du HTML (vidé après 7 jours)
- Pour forcer le nettoyage du cache:
  ```sql
  DELETE FROM terminology_cache;
  ```

## 📋 Notes techniques

### Pourquoi l'API ICD-11 retourne du HTML?

L'API met en évidence (`<em class='found'>`) les termes de recherche trouvés dans les résultats. C'est utile pour une interface web, mais pas pour une app mobile.

### Alternatives considérées

1. ❌ **Afficher le HTML tel quel** → Mauvaise UX
2. ❌ **Parser le HTML avec BeautifulSoup** → Dépendance lourde
3. ✅ **Regex simple** → Léger, rapide, suffisant pour ce cas

### Regex utilisée

```python
re.sub(r'<[^>]+>', '', text)
```

**Explication:**
- `<` : Match un chevron ouvrant
- `[^>]+` : Match tout sauf un chevron fermant (1+ fois)
- `>` : Match un chevron fermant
- `''` : Remplace par rien (supprime)

---

**Date**: 29 janvier 2026  
**Fix**: Nettoyage HTML dans résultats ICD-11  
**Status**: ✅ Corrigé (nécessite redémarrage serveur)
