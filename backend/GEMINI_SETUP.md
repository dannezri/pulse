# 🧠 Gemini Thinking Mode - Setup

## Vue d'ensemble

Le service d'explication énergétique (`/api/energy/explain`) utilise maintenant **Gemini 2.0 Flash avec mode raisonnement** pour générer la section "Pourquoi ce score ?" dans la page énergie.

---

## Configuration Requise

### 1. Clé API Google

Obtenir une clé API sur [Google AI Studio](https://makersuite.google.com/app/apikey)

### 2. Variables d'Environnement

```bash
# Obligatoire
export GOOGLE_API_KEY="votre-clé-api-google"

# Optionnel (modèle par défaut : gemini-2.0-flash-thinking-exp-01-21)
export GEMINI_MODEL="gemini-2.0-flash-thinking-exp-01-21"
```

### 3. Dépendances Python

```bash
pip install google-generativeai>=0.3.0
```

Ou installer toutes les dépendances :

```bash
pip install -r requirements.txt
```

---

## Test Rapide

```bash
python test_gemini_thinking.py
```

**Résultat attendu** :
```
🎉 TOUS LES TESTS CRITIQUES SONT PASSÉS!
✅ Gemini Thinking mode est prêt à être utilisé
```

---

## Utilisation

### Démarrage avec Gemini

```bash
# Option 1 : Script dédié
./start-with-gemini.sh

# Option 2 : Manuel
export GOOGLE_API_KEY="votre-clé"
python api_server.py
```

### Logs

Au démarrage, vous devriez voir :

```
[INFO] ✅ Gemini client initialized for Energy Explain Service
[INFO] ✅ Energy Explain Service initialized with Gemini Thinking mode
```

Lors d'une génération :

```
[INFO] 🧠 Calling Gemini 2.0 Flash Thinking for card generation...
[INFO] 💭 Gemini thinking process (first 300 chars): ...
[INFO] ✅ Generated 3 cards with Gemini thinking
```

---

## Endpoint API

### GET `/api/energy/explain/{user_id}`

**Headers** :
```
Authorization: Bearer <jwt_token>
```

**Query Parameters** :
- `date` (optionnel) : Date au format YYYY-MM-DD (défaut: aujourd'hui)

**Réponse** :
```json
{
  "energyScore": 38,
  "confidence": 62,
  "label": "Journée fragile",
  "date": "2026-02-03",
  "cards": [
    {
      "type": "nervous",
      "title": "Le câblage est saturé",
      "text": "Ton HRV est tombé à 25ms (baseline: 50ms)...",
      "analogy": "C'est comme charger ton téléphone avec un câble sectionné",
      "metrics": {
        "primary": {"label": "HRV actuel", "value": 25, "unit": "ms"},
        "secondary": {"label": "HRV baseline", "value": 50, "unit": "ms"}
      }
    }
  ]
}
```

---

## Avantages du Mode Thinking

1. **Raisonnement Explicite** : Gemini analyse les corrélations avant de répondre
2. **Meilleure Qualité** : Analogies plus contextualisées et personnalisées
3. **Débogage** : Le processus de raisonnement est loggé
4. **Coût** : ~50% moins cher que GPT-4o

---

## Troubleshooting

### Erreur : "GOOGLE_API_KEY must be set"

```bash
export GOOGLE_API_KEY="votre-clé"
```

### Erreur : "No module named 'google.generativeai'"

```bash
pip install google-generativeai
```

### Erreur : "Energy Explain Service not available"

Vérifier que la clé est définie et que le backend a redémarré :

```bash
echo $GOOGLE_API_KEY
python api_server.py
```

---

## Documentation

- **Guide complet** : `../GEMINI_THINKING_MIGRATION.md`
- **Quick Start** : `../QUICK_START_GEMINI.md`
- **Résumé** : `../RESUME_MIGRATION_GEMINI.md`

---

**Version** : Gemini Thinking v1.0  
**Date** : 2026-02-03
