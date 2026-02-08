# 🚀 Gemini 3 Pro Setup - Version Finale

## ⚠️ IMPORTANT : MODÈLE PAYANT

Gemini 3 Pro **n'a PAS de free tier**. Vous **devez activer la facturation** sur Google Cloud.

### 💰 Tarification

| Utilisation | Prix Entrée | Prix Sortie | Coût par Explication |
|-------------|-------------|-------------|----------------------|
| < 200k tokens | **2$ / 1M tokens** | **12$ / 1M tokens** | **~$0.03** |
| > 200k tokens | 4$ / 1M tokens | 18$ / 1M tokens | ~$0.05 |

**Estimation mensuelle** (100 explications/jour) :
- 💰 **$90 / mois** (3000 explications)

---

## ✅ Changements Effectués

### 1. Modèle Mis à Jour

```python
# Avant (gratuit)
model = "gemini-1.5-flash"

# Après (payant)
model = "gemini-3-pro-preview"
```

### 2. Mode Thinking Activé

```python
config = types.GenerateContentConfig(
    temperature=1.0,  # Gemini 3 recommande 1.0
    thinking_config=types.ThinkingConfig(
        thinking_level="high"  # low, medium, high
    )
)
```

### 3. Calcul du Coût Automatique

Chaque réponse inclut maintenant `estimated_cost_usd` :

```json
{
  "cards": [...],
  "_cost": 0.0324,
  "_thinking": "..."
}
```

---

## 🧪 Test (Dans Votre Terminal)

```bash
# 1. Installer google-genai (si pas déjà fait)
pip3 install google-genai

# 2. Configurer la clé API
export GOOGLE_API_KEY="AIzaSyAP9UbJfUJEsx-rBrVhWXcuA1sT6ctIj7c"

# 3. Tester
cd /Users/dannezri/Desktop/Pulse/backend
python3 test_gemini_thinking.py
```

**Résultat attendu** :
```
============================================================
🧠 TEST SUITE GEMINI THINKING MODE
============================================================

TEST 1: Initialisation du client Gemini
INFO:gemini_client:✅ Gemini client initialized with model: gemini-3-pro-preview
INFO:gemini_client:🧠 Thinking level: high
INFO:gemini_client:📦 Using google-genai package
WARNING:gemini_client:⚠️  Gemini 3 Pro is PAID (no free tier) - ~$0.03 per explanation
✅ Client Gemini initialisé avec succès

TEST 2: Génération simple
🧠 Appel à Gemini 3 Pro avec thinking_level=high...
💰 Estimated cost: $0.0324 USD
✅ Génération réussie!
   Cartes: 2-3
   Coût: $0.0324 USD

🎉 TOUS LES TESTS CRITIQUES SONT PASSÉS!
```

---

## ⚙️ Configuration

### Niveaux de Thinking

Vous pouvez ajuster le niveau de raisonnement :

```bash
# Dans .env ou start.sh
export GEMINI_THINKING_LEVEL="low"   # Rapide, moins cher (~$0.01)
export GEMINI_THINKING_LEVEL="high"  # Raisonnement profond (~$0.03)
```

| Niveau | Latence | Coût | Usage |
|--------|---------|------|-------|
| `low` | ⚡ Rapide | 💰 Bas | Chat simple, FAQ |
| `high` | 🐢 Lent | 💰💰 Élevé | Analyse complexe |

**Recommandation pour Pulse** : `high` (meilleure qualité d'explications)

---

## 🔧 Activer la Facturation

### Étape 1 : Accéder à Google Cloud Console

1. Allez sur https://console.cloud.google.com/
2. Sélectionnez votre projet (ou créez-en un)

### Étape 2 : Activer la Facturation

1. Menu **"Facturation"**
2. Cliquez **"Associer un compte de facturation"**
3. Ajoutez une carte de crédit

### Étape 3 : Activer l'API Gemini

1. Menu **"API et services"**
2. Cliquez **"Activer les API et les services"**
3. Recherchez **"Generative Language API"**
4. Cliquez **"Activer"**

### Étape 4 : Vérifier les Quotas

1. Menu **"API et services" > "Quotas"**
2. Recherchez "Gemini API"
3. Assurez-vous que les limites sont activées

---

## 💡 Avantages de Gemini 3 Pro

### vs Gemini 1.5 Flash (Gratuit)

| Aspect | Gemini 1.5 Flash | Gemini 3 Pro |
|--------|------------------|--------------|
| **Raisonnement** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Qualité** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Contexte** | Bon | Excellent |
| **Analogies** | Bonnes | Exceptionnelles |
| **Coût** | Gratuit | ~$0.03/explication |

### Pour Pulse

**Amélioration attendue** :
- ✅ **Analogies plus pertinentes** et contextualisées
- ✅ **Raisonnement explicite** (bloc `_thinking`)
- ✅ **Corrélations plus fines** (HRV ↔ médicaments ↔ sommeil)
- ✅ **Conseils plus actionnables**

**Exemple** :

**Gemini 1.5 Flash** :
```
🔌 Le câblage est défaillant
Ton HRV est bas. C'est comme un câble USB effiloché.
```

**Gemini 3 Pro** (attendu) :
```
🔌 Le câblage est défaillant

Ton HRV est à 25ms (baseline: 50ms). Malgré 8h de sommeil, 
ton système nerveux parasympathique ne transmet plus l'énergie 
efficacement. La Mirtazapine (sédatif) bloque potentiellement 
la récupération nocturne du HRV.

💡 C'est comme charger ton téléphone avec un câble USB effiloché 
ET en mode économie d'énergie : l'électricité arrive (tu dors), 
mais ne se stocke pas (récupération bloquée par les médicaments).

📊 HRV actuel: 25ms | Baseline: 50ms | Impact Mirtazapine: -15%

💭 Processus de raisonnement : J'ai analysé la corrélation entre 
la prise de Mirtazapine (23h), le sommeil (23h-7h) et la récupération 
HRV nocturne. La Mirtazapine inhibe la récupération parasympathique...
```

---

## 📊 Monitoring des Coûts

### Dans Google Cloud Console

1. **"Facturation" > "Rapports"**
2. Filtrez par **"Generative Language API"**
3. Surveillez les **coûts quotidiens**

### Alertes de Facturation

1. **"Facturation" > "Budgets et alertes"**
2. Créez un budget mensuel (ex: $100)
3. Configurez des alertes (ex: 50%, 90%, 100%)

### Dans le Code

Le coût est calculé automatiquement dans chaque réponse :

```python
result = client.generate_cards_explanation(...)
cost = result.get("_cost", 0)
print(f"Coût de cette explication : ${cost:.4f} USD")
```

---

## 🚨 Limiter les Coûts

### 1. Utiliser `thinking_level="low"` pour les requêtes simples

```python
# Pour FAQ, chat simple
client.generate_cards_explanation(
    prompt=prompt,
    thinking_level="low"  # ~$0.01 au lieu de $0.03
)
```

### 2. Cache les Contextes Répétés

Gemini 3 supporte la **mise en cache du contexte** (min 2048 tokens) :

```python
# Si vous envoyez souvent le même system_prompt
config = types.GenerateContentConfig(
    cached_content=cached_system_prompt  # Réutilise le cache
)
```

### 3. Limitez max_output_tokens

```python
config = types.GenerateContentConfig(
    max_output_tokens=4096  # Au lieu de 8192
)
```

---

## 🔄 Rollback vers Gratuit

Si les coûts sont trop élevés, revenez à Gemini 1.5 Flash :

```bash
export GEMINI_MODEL="gemini-1.5-flash"
```

Le code supporte les deux modèles automatiquement.

---

## 📖 Documentation Officielle

- **Gemini 3** : https://ai.google.dev/gemini-api/docs/gemini-3
- **Tarification** : https://ai.google.dev/pricing
- **Thinking Config** : https://ai.google.dev/gemini-api/docs/thinking

---

**Status** : ✅ **GEMINI 3 PRO CONFIGURÉ**  
**Modèle** : gemini-3-pro-preview  
**Thinking Level** : high  
**Package** : google-genai >= 0.2.0  
**Coût Estimé** : ~$0.03 / explication  
**Date** : 2026-02-03

---

**⚠️ RAPPEL : Activez la facturation avant de tester ! 💳**
