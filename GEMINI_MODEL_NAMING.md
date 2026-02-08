# 🏷️ Convention de Nommage des Modèles Gemini

## ⚠️ IMPORTANT : Suffixe `-latest` Requis

Avec le package `google.genai`, les modèles nécessitent le suffixe **`-latest`** :

| ❌ Ancien (ne fonctionne pas) | ✅ Nouveau (fonctionne) |
|-------------------------------|-------------------------|
| `gemini-1.5-flash` | `gemini-1.5-flash-latest` |
| `gemini-1.5-pro` | `gemini-1.5-pro-latest` |
| `gemini-pro` | `gemini-pro-latest` |

---

## 🎯 Modèle Configuré : gemini-1.5-flash-latest

**Pourquoi ce modèle ?**
- ✅ **Gratuit** en free tier
- ⚡ **Rapide** (2x plus rapide que Pro)
- 💰 **Économique** (50% moins cher)
- 🧠 **Performant** pour les explications

---

## ❌ Modèles NON Disponibles en Free Tier

| Modèle | Erreur | Raison |
|--------|--------|--------|
| `gemini-3-pro-preview` | 429 RESOURCE_EXHAUSTED | `limit: 0` → Payant uniquement |
| `gemini-3-pro` | 429 RESOURCE_EXHAUSTED | `limit: 0` → Payant uniquement |
| `gemini-2.0-*` | 404 ou 429 | Pas encore public ou payant |

---

## 📊 Comparaison Modèles Gratuits

### gemini-1.5-flash-latest ✅ (UTILISÉ)

**Gratuit** :
- ✅ Requests: 15 RPM, 1500 RPD
- ✅ Tokens: 1M TPM, 15M TPD

**Caractéristiques** :
- ⚡ Vitesse: **Excellente**
- 💡 Qualité: **Très bonne**
- 🧠 Contexte: **1M tokens**
- 💰 Coût production: **$0.075/1M tokens**

**Parfait pour** : Pulse (explications rapides et empathiques)

### gemini-1.5-pro-latest

**Gratuit** :
- ✅ Requests: 2 RPM, 50 RPD
- ✅ Tokens: 32k TPM, 50k TPD

**Caractéristiques** :
- ⚡ Vitesse: Moyenne
- 💡 Qualité: **Excellente**
- 🧠 Contexte: **2M tokens**
- 💰 Coût production: **$1.25/1M tokens**

**Limites** : Quotas très bas en free tier (2 RPM = 1 requête toutes les 30s)

---

## 🚀 Configuration Actuelle

```python
# backend/gemini_client.py ligne 36
self.model_name = model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest")
```

---

## 🔄 Changer de Modèle

### Option 1 : Variable d'environnement

```bash
# Plus performant mais quotas bas
export GEMINI_MODEL="gemini-1.5-pro-latest"

# Recommandé : rapide et quotas hauts
export GEMINI_MODEL="gemini-1.5-flash-latest"
```

### Option 2 : Modifier le code

```python
# backend/gemini_client.py ligne 36
self.model_name = model or os.getenv("GEMINI_MODEL", "gemini-1.5-pro-latest")
#                                                       ^^^^^^^^^^^^^^^^^^^^^
#                                                       Changer ici
```

---

## 📈 Recommandation

### ✅ Pour Free Tier : gemini-1.5-flash-latest

**Raisons** :
- ✅ 15 RPM (vs 2 RPM pour Pro)
- ✅ 1500 RPD (vs 50 RPD pour Pro)
- ✅ Vitesse 2x supérieure
- ✅ Qualité excellente pour Pulse
- ✅ Coût 15x moins cher en production

### 💰 Pour Production Payante : gemini-1.5-flash-latest

**Raisons** :
- ✅ 2000 RPM (vs 360 RPM pour Pro)
- ✅ Pas de limite quotidienne
- ✅ $0.075/1M tokens (vs $1.25/1M pour Pro)
- ✅ ROI optimal pour Pulse

**Quand utiliser Pro ?**
- Seulement si la qualité de Flash est insuffisante
- Pour des analyses ultra-complexes
- Budget non contraint

---

## 🧪 Test du Modèle

```bash
export GOOGLE_API_KEY="AIzaSyAP9UbJfUJEsx-rBrVhWXcuA1sT6ctIj7c"
cd /Users/dannezri/Desktop/Pulse/backend
python3 test_gemini_thinking.py
```

**Résultat attendu** :
```
✅ Client Gemini initialisé avec succès
   Modèle: gemini-1.5-flash-latest
✅ Génération réussie!
   Cartes: 2-3
🎉 TOUS LES TESTS CRITIQUES SONT PASSÉS!
```

---

## 📖 Documentation Officielle

- **Modèles disponibles** : https://ai.google.dev/gemini-api/docs/models
- **Quotas free tier** : https://ai.google.dev/gemini-api/docs/rate-limits
- **Pricing** : https://ai.google.dev/pricing

---

**Status** : ✅ **gemini-1.5-flash-latest Configuré**  
**Date** : 2026-02-03  
**Version** : v1.4 (Final - avec suffixe -latest)

---

**Testez maintenant ! 🚀**

```bash
python3 /Users/dannezri/Desktop/Pulse/backend/test_gemini_thinking.py
```
