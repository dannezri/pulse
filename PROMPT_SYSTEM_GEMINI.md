# 🧠 Prompt Système Gemini - "Pourquoi ce score ?"

## Vue d'ensemble

Le prompt système utilisé par Gemini 2.0 Flash Thinking pour générer les explications du score d'énergie a été optimisé pour fournir des analogies ultra-pédagogiques et empathiques.

---

## 🎯 Philosophie du Prompt

### Ton et Approche

- **Empathique** : Valide la fatigue comme une réalité biologique, jamais culpabilisant
- **Professionnel** : Expert en bio-feedback et pharmacocinétique
- **Ultra-pédagogique** : Rend la science accessible avec des analogies du quotidien

### Objectif Principal

Déchiffrer le score d'énergie en utilisant **3 analogies obligatoires** pour réduire la charge mentale :

1. 🔌 **Le Câblage (HRV)** - La transmission de l'énergie
2. ⛽ **Le Réservoir (Sommeil)** - Le stock de carburant
3. 🚦 **Le Limiteur de Vitesse (Chimie)** - Les freins sur le moteur

---

## 📊 Données Contextuelles

Le prompt a accès à :

- **Énergie Actuelle** : Score final calculé (ex: 34%)
- **Récupération (Recovery)** : Score % (ex: 19%)
- **Biométrie** : HRV, RHR, Sommeil, Dette de sommeil
- **Chimie** : Liste des médicaments actifs et impacts calculés
- **Pathologies** : Conditions actives (ex: TDAH, Dépression, Sinus)

---

## 🎨 Les 3 Analogies Obligatoires

### 1. 🔌 Le Câblage (HRV)

**Concept** : Le HRV est la capacité du système nerveux à transmettre l'énergie

**Analogie** :
> "Un HRV bas = un câble de charge endommagé qui ne peut pas transmettre l'électricité efficacement. Même si le réservoir est plein, un câble défectueux empêche la recharge."

**Exemple d'utilisation** :
```
"Ton câblage nerveux est endommagé. Même avec du repos (réservoir plein), 
l'énergie ne circule plus correctement. C'est comme essayer de charger ton 
téléphone avec un câble USB effiloché : HRV 25ms vs 50ms baseline."
```

**Quand l'utiliser** :
- HRV bas (< 50% de la baseline)
- Récupération faible malgré sommeil correct
- Système nerveux parasympathique défaillant

---

### 2. ⛽ Le Réservoir (Sommeil)

**Concept** : Le sommeil représente le stock de carburant

**Analogie** :
> "Une dette de sommeil = un réservoir percé qui fuit en permanence. Peu importe ce qu'on met dedans, ça ne se remplit jamais complètement."

**Exemple d'utilisation** :
```
"Ton réservoir fuit en permanence à cause de la dette de sommeil. 
Tu dors 6h mais ton corps en a besoin de 8h : c'est 2h de carburant 
qui s'évaporent chaque nuit. Impossible de faire le plein."
```

**Quand l'utiliser** :
- Dette de sommeil > 2h
- Sommeil insuffisant (< 7h)
- Score de sommeil bas (< 70)

---

### 3. 🚦 Le Limiteur de Vitesse (Chimie/Conditions)

**Concept** : Les médicaments sédatifs ou la charge mentale sont des "brides" sur le moteur

**Analogie** :
> "Ils empêchent d'utiliser tout le carburant disponible. C'est comme avoir un moteur puissant mais bridé à 50 km/h par le logiciel."

**Exemple d'utilisation** :
```
"Tu as un pied sur l'accélérateur (Sertraline +15%) et l'autre sur 
le frein (Mirtazapine -25%). Ton moteur veut avancer mais le limiteur 
de vitesse est activé. Résultat net : -10% d'énergie disponible."
```

**Quand l'utiliser** :
- Médicaments sédatifs actifs
- Médicaments contradictoires (booster vs frein)
- Conditions chroniques (dépression, TDAH)

---

## 📋 Structure Obligatoire des Cartes

### Carte 1 : Le Diagnostic (type: "nervous")

**Focus** : Corrélation HRV ↔ Récupération

**Question clé** : Pourquoi le repos ne "charge" pas ?

**Contenu** :
- Analyse HRV actuel vs baseline
- Lien avec le score de récupération
- Utilise l'analogie du **Câblage**

**Exemple** :
```json
{
  "type": "nervous",
  "title": "🔌 Le câblage est défaillant",
  "text": "Ton HRV est à 25ms (baseline: 50ms). Ton système nerveux parasympathique ne transmet plus l'énergie efficacement, même après 8h de sommeil. C'est pour ça que ta récupération reste à 19%.",
  "analogy": "C'est comme charger ton téléphone avec un câble USB sectionné : l'électricité ne passe plus.",
  "metrics": {
    "primary": {"label": "HRV actuel", "value": 25, "unit": "ms"},
    "secondary": {"label": "HRV baseline", "value": 50, "unit": "ms"}
  }
}
```

---

### Carte 2 : Le Paradoxe (type: "chemistry")

**Focus** : Combat entre boosters et freins (médicaments)

**Question clé** : Comment les médicaments s'annulent ou se renforcent ?

**Contenu** :
- Liste des médicaments actifs
- Impact net calculé
- Utilise l'analogie du **Limiteur de Vitesse**

**Exemple** :
```json
{
  "type": "chemistry",
  "title": "🚦 Accélérateur ET frein activés",
  "text": "Tu prends Sertraline (+15% énergie) mais aussi Mirtazapine (-25% sédation). Ces deux médicaments se battent : l'un veut accélérer, l'autre ralentir. Résultat net : -10% d'énergie disponible.",
  "analogy": "C'est comme conduire avec un pied sur l'accélérateur et l'autre sur le frein. Le moteur chauffe mais tu n'avances pas.",
  "metrics": {
    "primary": {"label": "Impact net", "value": -10, "unit": "%"},
    "secondary": {"label": "Médicaments actifs", "value": 2, "unit": ""}
  }
}
```

---

### Carte 3 : La Charge Invisible (type: "load")

**Focus** : Impact des pathologies chroniques

**Question clé** : Quel est le coût énergétique caché ?

**Contenu** :
- Conditions actives (sinus, dépression, etc.)
- Impact sur l'oxygénation ou la charge mentale
- Analogie du **poids supplémentaire**

**Exemple** :
```json
{
  "type": "load",
  "title": "🎒 Le sac à dos invisible",
  "text": "Ta sinusite chronique force ton corps à dépenser de l'énergie juste pour compenser la mauvaise oxygénation. C'est un coût métabolique permanent que tu ne vois pas mais qui épuise tes réserves.",
  "analogy": "C'est comme porter un sac à dos de 10kg toute la journée sans t'en rendre compte. Ton corps travaille en permanence.",
  "metrics": {
    "primary": {"label": "Conditions actives", "value": 3, "unit": ""},
    "secondary": {"label": "Impact estimé", "value": -15, "unit": "%"}
  }
}
```

---

### Carte 4 : Conseils Actionnables (type: "activity", optionnelle)

**Focus** : 3 micro-actions concrètes

**Contenu** :
- Actions basées sur les anomalies détectées
- Mesurables et réalisables dans la journée
- Encouragement bienveillant

**Exemple** :
```json
{
  "type": "activity",
  "title": "⚡ 3 micro-actions aujourd'hui",
  "text": "1. 🌬️ 5 min de respiration nasale (sinus)\n2. ☀️ 15 min de lumière naturelle (médicaments)\n3. 💤 Sieste de 20 min max (dette sommeil)\n\nChaque micro-action compte. Commence par une seule aujourd'hui. 💚",
  "analogy": "Ton corps fait de son mieux avec les ressources disponibles. C'est déjà énorme.",
  "metrics": {}
}
```

---

## 🎨 Contraintes de Style

### Emojis Obligatoires

- 🔌 Câblage / HRV / Système nerveux
- ⛽ Réservoir / Sommeil / Carburant
- 🚦 Limiteur / Médicaments / Chimie
- 💊 Médicaments
- 🧠 Cerveau / Mental
- 💤 Sommeil
- 🎒 Charge / Poids
- 🌬️ Respiration / Oxygénation
- ☀️ Lumière / Circadien
- 💚 Encouragement

### Ton et Langage

**✅ À FAIRE** :
- Valider la fatigue comme réalité biologique
- Expliquer les mécanismes physiologiques simplement
- Citer les valeurs exactes avec unités
- Terminer par un encouragement

**❌ À ÉVITER** :
- Être punitif ou culpabilisant
- Utiliser du jargon médical sans explication
- Donner des conseils génériques
- Ignorer les médicaments ou pathologies

### Encouragements Recommandés

- "Ton corps fait de son mieux avec les ressources disponibles. C'est déjà énorme."
- "Ces signaux sont précieux : ton corps te parle, écoute-le."
- "Chaque micro-action compte. Commence par une seule aujourd'hui."
- "Ta fatigue n'est pas un échec, c'est une information biologique."

---

## 📏 Limites de Longueur

| Champ | Limite | Raison |
|-------|--------|--------|
| `title` | 50 caractères | Lisibilité mobile |
| `text` | 250 caractères | Attention span |
| `analogy` | 150 caractères | Impact mémoriel |

---

## 🧠 Mode Thinking

Avant de générer les cartes, Gemini doit **raisonner** :

1. **Analyser** les corrélations (HRV, RHR, Sommeil, Dette)
2. **Identifier** le combat boosters vs freins (médicaments)
3. **Repérer** les charges invisibles (pathologies)
4. **Prioriser** les 3 insights les plus impactants

Ce raisonnement est loggé dans les logs backend :

```
[INFO] 💭 Gemini thinking process (first 300 chars):
       L'utilisateur a un HRV très bas (25ms vs 50ms baseline) malgré 
       8h de sommeil. Le câblage nerveux est défaillant. En plus, il 
       prend Mirtazapine (-25%) qui bride encore plus l'énergie...
```

---

## 🎯 Exemples Complets

### Cas 1 : HRV Bas + Dette Sommeil

**Données** :
- Énergie : 34%
- HRV : 25ms (baseline: 50ms)
- Sommeil : 6h (besoin: 8h)
- Dette : 2h

**Cartes générées** :

1. **Le Diagnostic** : Câblage défaillant (HRV bas)
2. **Le Réservoir** : Dette de sommeil qui fuit
3. **Conseils** : Sieste + respiration + lumière

---

### Cas 2 : Médicaments Contradictoires

**Données** :
- Énergie : 42%
- Médicaments : Sertraline (+15%), Mirtazapine (-25%)
- Conditions : Dépression, Anxiété

**Cartes générées** :

1. **Le Diagnostic** : Récupération faible malgré repos
2. **Le Paradoxe** : Accélérateur ET frein (médicaments)
3. **La Charge Invisible** : Coût métabolique de la dépression

---

### Cas 3 : Pathologies Multiples

**Données** :
- Énergie : 28%
- Conditions : Sinus, TDAH, Dépression
- HRV : 30ms (baseline: 55ms)

**Cartes générées** :

1. **Le Diagnostic** : Câblage surchargé (HRV + conditions)
2. **La Charge Invisible** : Sac à dos de 3 pathologies
3. **Conseils** : Respiration nasale + gestion TDAH + repos

---

## 🔧 Personnalisation

Le prompt s'adapte automatiquement aux données disponibles :

- **Si HRV bas** → Carte "Câblage"
- **Si dette sommeil** → Carte "Réservoir"
- **Si médicaments** → Carte "Paradoxe"
- **Si pathologies** → Carte "Charge Invisible"
- **Toujours** → Encouragement final

---

## 📖 Fichiers Associés

- **Implémentation** : `backend/explain_service.py` (ligne 468-523)
- **Client Gemini** : `backend/gemini_client.py`
- **Tests** : `backend/test_gemini_thinking.py`
- **Documentation** : `GEMINI_THINKING_MIGRATION.md`

---

## ✅ Validation

Pour tester le prompt :

```bash
cd backend
python test_gemini_thinking.py
```

Le test génère des cartes avec des données fictives et valide :
- Structure JSON correcte
- Présence des analogies obligatoires
- Respect des limites de longueur
- Ton empathique

---

**Version** : Gemini Thinking v1.1 (Prompt Optimisé)  
**Date** : 2026-02-03  
**Auteur** : Assistant AI

---

**Les 3 analogies sont maintenant au cœur du système ! 🔌⛽🚦**
