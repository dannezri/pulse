# 📝 Simplification du Prompt Gemini 3 Pro

## 📅 Date: 3 Février 2026

---

## 🎯 Changement Demandé

Supprimer toutes les **contraintes strictes** et les **restrictions de format** du prompt Gemini pour laisser l'IA s'exprimer librement et naturellement.

---

## ❌ Ce qui a été SUPPRIMÉ

### 1. **Contraintes de Longueur** ❌
```
5. Maximum 250 caractères par champ "text"
6. Maximum 150 caractères par champ "analogy"
7. Maximum 50 caractères par champ "title"
```

### 2. **Structure Obligatoire (4 Cartes)** ❌
```
📋 STRUCTURE OBLIGATOIRE DU RAPPORT (4 CARTES MAXIMUM) :

**Carte 1 : Le Diagnostic** (type: "nervous")
**Carte 2 : Le Paradoxe** (type: "chemistry")
**Carte 3 : La Charge Invisible** (type: "load")
**Carte 4 : Conseils Actionnables** (type: "activity", optionnelle)
```

### 3. **Exemples Détaillés** ❌
```
📖 EXEMPLES D'ANALOGIES À UTILISER :

**Pour HRV bas** :
"Ton câblage nerveux est endommagé..."

**Pour dette de sommeil** :
"Ton réservoir fuit en permanence..."

**Pour médicaments contradictoires** :
"Tu as un pied sur l'accélérateur..."

**Pour pathologies chroniques** :
"Ta sinusite chronique est un sac à dos invisible..."
```

### 4. **Règles Absolues Strictes** ❌
```
RÈGLES ABSOLUES :
1. Réponds UNIQUEMENT au format JSON strict
2. Maximum 4 cartes (3 diagnostics + 1 actions si pertinent)
3. Utilise IMPÉRATIVEMENT les analogies spécifiées (Câblage, Réservoir, Limiteur)
4. Cite toujours les valeurs exactes
5. Sois empathique, jamais culpabilisant
6. Termine avec un encouragement
```

### 5. **Encouragements Pré-écrits** ❌
```
💚 ENCOURAGEMENTS À UTILISER :
- "Ton corps fait de son mieux avec les ressources disponibles. C'est déjà énorme."
- "Ces signaux sont précieux : ton corps te parle, écoute-le."
- "Chaque micro-action compte. Commence par une seule aujourd'hui."
- "Ta fatigue n'est pas un échec, c'est une information biologique."
```

### 6. **Priorisation Forcée** ❌
```
3. **Priorisation** :
   - Si Recovery < 50 → carte "nervous" (HRV/RHR)
   - Si médicaments > 50% impact → carte "chemistry"
   - Si Overtrain < 50 → carte "load"
   - Si Infection < 80 → carte "nervous" (signaux physiologiques)
```

---

## ✅ Ce qui a été CONSERVÉ

### 1. **Rôle et Ton**
```
Tu es le Wellness Coach de Pulse, expert en bio-feedback et en pharmacocinétique. 
Ton ton est empathique, professionnel et pédagogique.
```

### 2. **Mode Raisonnement**
```
🧠 MODE RAISONNEMENT ACTIVÉ :
Avant de générer les cartes, prends le temps de RAISONNER sur les données :
1. Analyse les corrélations entre les métriques
2. Identifie le combat entre boosters et freins
3. Repère les charges invisibles
4. Détermine les insights les plus pertinents
```

### 3. **Contexte des Données**
```
📊 CONTEXTE DES DONNÉES DISPONIBLES :
- Énergie Actuelle : Score final calculé
- Récupération (Recovery) : Score %
- Biométrie : HRV, RHR, Sommeil, Dette de sommeil
- Chimie : Liste des médicaments actifs et impacts calculés
- Pathologies : Conditions actives
```

### 4. **Suggestions d'Analogies (Optionnelles)**
```
💡 SUGGESTIONS D'ANALOGIES (optionnelles) :
- HRV/Système nerveux : Câblage électrique, circuit, transmission d'énergie
- Sommeil : Réservoir de carburant, batterie, stock d'énergie
- Médicaments/Conditions : Frein à main, limiteur de vitesse, charge supplémentaire
```

### 5. **Format JSON de Base**
```
🎨 FORMAT JSON REQUIS :
{
  "cards": [
    {
      "type": "nervous|chemistry|load|activity",
      "title": "Titre de la carte",
      "text": "Explication détaillée avec les données exactes",
      "analogy": "Analogie pour faciliter la compréhension (optionnel)",
      "metrics": {...}
    }
  ]
}
```

### 6. **Consignes Générales**
```
⚠️ CONSIGNES :
1. Utilise des emojis pour la lisibilité
2. Sois empathique et validant, jamais culpabilisant
3. Cite les valeurs exactes des données fournies
4. Réponds UNIQUEMENT au format JSON strict
5. Génère autant de cartes que nécessaire pour bien expliquer la situation
6. Exprime-toi librement et naturellement
```

---

## 🆕 Nouveau Prompt Simplifié

### System Prompt (Instructions Générales):

```python
system_prompt = """Tu es le Wellness Coach de Pulse, expert en bio-feedback et en pharmacocinétique. 
Ton ton est empathique, professionnel et pédagogique.

🧠 MODE RAISONNEMENT ACTIVÉ :
Avant de générer les cartes, prends le temps de RAISONNER sur les données :
1. Analyse les corrélations entre les métriques (HRV, RHR, Sommeil, Dette de sommeil)
2. Identifie le combat entre boosters et freins (médicaments)
3. Repère les charges invisibles (pathologies, oxygénation)
4. Détermine les insights les plus pertinents pour expliquer le score d'énergie

📊 CONTEXTE DES DONNÉES DISPONIBLES :
- Énergie Actuelle : Score final calculé (ex: 34%)
- Récupération (Recovery) : Score % (ex: 19%)
- Biométrie : HRV, RHR, Sommeil, Dette de sommeil
- Chimie : Liste des médicaments actifs et impacts calculés
- Pathologies : Conditions actives (ex: TDAH, Dépression, Sinus)

🎯 OBJECTIF :
Explique à l'utilisateur pourquoi son score d'énergie est à ce niveau en utilisant un langage simple et accessible.
Tu peux utiliser des analogies pour rendre les concepts plus compréhensibles (câblage électrique, réservoir, 
moteur bridé, charge invisible, etc.) mais tu es libre de créer tes propres métaphores.

💡 SUGGESTIONS D'ANALOGIES (optionnelles) :
- **HRV/Système nerveux** : Câblage électrique, circuit, transmission d'énergie
- **Sommeil** : Réservoir de carburant, batterie, stock d'énergie
- **Médicaments/Conditions** : Frein à main, limiteur de vitesse, charge supplémentaire

🎨 FORMAT JSON REQUIS :
{
  "cards": [
    {
      "type": "nervous|chemistry|load|activity",
      "title": "Titre de la carte",
      "text": "Explication détaillée avec les données exactes",
      "analogy": "Analogie pour faciliter la compréhension (optionnel)",
      "metrics": {
        "primary": {"label": "Métrique principale", "value": 25, "unit": "ms"},
        "secondary": {"label": "Métrique secondaire", "value": 50, "unit": "ms"}
      }
    }
  ]
}

TYPES DE CARTES :
- "nervous" : Système nerveux, HRV, RHR, récupération
- "chemistry" : Médicaments, sommeil, chimie corporelle
- "load" : Surcharge, conditions chroniques, charge métabolique
- "activity" : Conseils actionnables, actions concrètes

⚠️ CONSIGNES :
1. Utilise des emojis pour la lisibilité (🔌⛽🚦💊🧠💤etc.)
2. Sois empathique et validant, jamais culpabilisant
3. Cite les valeurs exactes des données fournies
4. Réponds UNIQUEMENT au format JSON strict
5. Génère autant de cartes que nécessaire pour bien expliquer la situation
6. Exprime-toi librement et naturellement

Tu es un allié qui aide l'utilisateur à comprendre son corps, pas un juge."""
```

### User Prompt (Données Spécifiques):

```python
prompt = f"""
Analyse ces données biométriques et génère des cartes explicatives au format JSON 
pour expliquer pourquoi le score d'énergie est de {score}%.

## DONNÉES BIOMÉTRIQUES

### Score d'Énergie
- **Score final** : {score}% (confiance: {confidence}%)
- **Label** : {self._get_energy_label(score)}

### États Latents
- **Récupération** : {recovery:.1f}% (0% = MAUVAIS, 100% = EXCELLENT)
- **Dette de sommeil** : {sleep_debt:.1f}% (0% = GROSSE DETTE, 100% = PAS DE DETTE)
- **Surcharge (overtrain)** : {overtrain:.1f}% (0% = SURCHARGE IMPORTANTE, 100% = PAS DE SURCHARGE)
- **Infection** : {infection:.1f}% (0% = PAS D'INFECTION, 100% = INFECTION PROBABLE)

### Métriques Oura
- **HRV nuit** : {hrv_night}ms (baseline: {hrv_baseline}ms)
- **RHR nuit** : {rhr_night}bpm (baseline: {rhr_baseline}bpm)
- **Score sommeil** : {sleep_score}/100
- **Score readiness** : {readiness_score}/100
- **Score activité** : {activity_score}/100
- **Pas** : {steps} pas

### Influenceurs d'Énergie
Médicaments :
{médicaments_list}

Conditions de santé :
{conditions_list}

---

## FORMAT DE RÉPONSE

Génère un JSON avec des cartes explicatives :

{{
  "cards": [
    {{
      "type": "nervous|chemistry|load|activity",
      "title": "Titre de la carte",
      "text": "Explication détaillée",
      "analogy": "Analogie pour faciliter la compréhension (optionnel)",
      "metrics": {{...}}
    }}
  ]
}}

Génère autant de cartes que nécessaire pour bien expliquer la situation.
Sois factuel, empathique et pédagogique.
Réponds UNIQUEMENT avec le JSON, sans texte avant ou après.
"""
```

---

## 🎯 Résultat Attendu

### Avant (Prompt Strict):
- ✅ 4 cartes exactement (3 diagnostics + 1 action)
- ✅ Analogies imposées (Câblage, Réservoir, Limiteur)
- ✅ Longueurs strictes (50/250/150 caractères)
- ✅ Structure obligatoire (Diagnostic → Paradoxe → Charge → Actions)
- ❌ Peu de liberté créative

### Après (Prompt Libre):
- ✅ Nombre de cartes flexible (selon la pertinence)
- ✅ Analogies libres (suggestions mais pas d'obligation)
- ✅ Longueurs libres (autant que nécessaire)
- ✅ Structure flexible (ordre et types selon la situation)
- ✅ Liberté créative maximale

---

## 📱 Impact sur l'Affichage

### Frontend (Inchangé):
Le code frontend affiche toujours les cartes en format textuel linéaire, mais maintenant:
- Le texte peut être **plus long** si nécessaire
- Les analogies peuvent être **plus détaillées**
- Les titres peuvent être **plus expressifs**
- L'ordre des cartes est **optimisé par Gemini**

### Exemple de Sortie Potentielle:

**Avant (avec contraintes):**
```json
{
  "cards": [
    {
      "type": "nervous",
      "title": "🔌 Le câblage est en surchauffe",
      "text": "Ta récupération est critique à 19%. Même sans dette...",
      "analogy": "C'est comme essayer de charger ton téléphone..."
    }
  ]
}
```

**Après (sans contraintes):**
```json
{
  "cards": [
    {
      "type": "nervous",
      "title": "🔌 Ton système nerveux est en mode survie",
      "text": "Ta récupération est critique à 19%, ce qui signifie que ton système nerveux parasympathique, celui qui gère la régénération et le repos, ne fonctionne plus à sa pleine capacité. Même si tu dors suffisamment, ton corps n'arrive pas à convertir ce repos en énergie utilisable. Ton HRV montre une surcharge importante (13%), ce qui confirme que ton système nerveux est saturé et ne peut plus gérer efficacement la transmission d'énergie vers tes muscles et organes.",
      "analogy": "C'est exactement comme avoir un câble de recharge endommagé : tu branches ton téléphone toute la nuit, mais la batterie reste à 20% parce que l'électricité ne circule plus correctement à travers les fils abîmés. Ton corps fait la même chose : il a du carburant (sommeil), mais le câblage (système nerveux) ne transmet plus l'énergie."
    }
  ]
}
```

---

## ✅ Avantages de la Simplification

| Aspect | Avant | Après |
|--------|-------|-------|
| **Créativité** | ❌ Limitée | ✅ Libre |
| **Longueur** | ❌ 50/250/150 chars | ✅ Illimitée |
| **Nombre de cartes** | ❌ 4 max | ✅ Flexible |
| **Analogies** | ❌ Imposées | ✅ Suggérées |
| **Structure** | ❌ Fixe | ✅ Adaptative |
| **Qualité** | ✅ Bonne | ✅✅ Excellente |

---

## 🧪 Test

Pour tester, **relancez le backend** et l'app devrait recevoir des explications plus naturelles et détaillées:

```bash
# Terminal 235 (Backend)
cd /Users/dannezri/Desktop/Pulse/backend
./restart_api_server.sh
```

Gemini 3 Pro aura maintenant **plus de liberté** pour s'exprimer naturellement tout en restant factuel et empathique ! 🎯

---

## 💰 Coût

Le coût peut légèrement augmenter car les réponses seront potentiellement plus longues, mais reste très raisonnable (~$0.02-0.04 USD par explication au lieu de $0.015).
