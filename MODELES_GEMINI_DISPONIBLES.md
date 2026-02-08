# 🤖 Modèles Gemini Disponibles

## Status : gemini-3-pro-preview UTILISÉ ✅

Le code utilise maintenant **`gemini-3-pro-preview`** qui est le modèle Gemini le plus récent avec les meilleures capacités de raisonnement.

---

## 📊 Modèles Testés

| Modèle | Status | Raison |
|--------|--------|--------|
| `gemini-3-pro-preview` | ✅ **FONCTIONNE** | **UTILISÉ** - Le plus récent |
| `gemini-1.5-pro` | ✅ Disponible | Alternative stable |
| `gemini-1.5-flash` | ✅ Disponible | Alternative rapide |
| `gemini-2.0-flash-exp` | ❌ N'existe pas | Erreur 404 |
| `gemini-pro` | ✅ Disponible | Legacy (v1.0) |

---

## 🎯 Modèle Configuré

### gemini-3-pro-preview

**Caractéristiques** :
- 💪 Le plus récent et performant de Gemini (v3)
- 🧠 Contexte : 1M+ tokens
- 📊 Capacités de raisonnement avancées
- 💰 Coût : À déterminer (preview)

**Parfait pour** :
- Explication détaillée du score d'énergie
- Génération d'analogies contextualisées
- Analyse de données biométriques complexes

---

## 🔄 Alternatives Disponibles

### gemini-1.5-pro (Plus Stable)

Si vous préférez un modèle **stable et éprouvé** :

```bash
export GEMINI_MODEL="gemini-1.5-pro"
```

**Caractéristiques** :
- ✅ Stable et bien documenté
- 🧠 Contexte : 1M tokens
- 💰 Coût connu : ~$0.0035/1k tokens

### gemini-1.5-flash (Plus Rapide)

Si vous voulez **plus de vitesse** et **moins de coût** :

```bash
export GEMINI_MODEL="gemini-1.5-flash"
```

**Caractéristiques** :
- ⚡ 2x plus rapide
- 💰 50% moins cher
- 🧠 Contexte : 1M tokens
- 📊 Légèrement moins précis

### gemini-pro (Legacy)

Ancien modèle Gemini 1.0 :

```bash
export GEMINI_MODEL="gemini-pro"
```

**Caractéristiques** :
- 🕰️ Legacy (v1.0)
- 🧠 Contexte : 32k tokens
- 📊 Moins performant que 1.5

---

## 🚀 Changer de Modèle

### Option 1 : Variable d'environnement

```bash
export GEMINI_MODEL="gemini-1.5-flash"
```

### Option 2 : Dans le code

```python
# backend/gemini_client.py ligne 36
self.model_name = model or os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
#                                                       ^^^^^^^^^^^^^^^^
#                                                       Changer ici
```

### Option 3 : Dans start.sh

```bash
export GEMINI_MODEL="gemini-1.5-flash"
```

---

## 📈 Comparaison Performance

| Critère | gemini-1.5-pro | gemini-1.5-flash |
|---------|----------------|------------------|
| **Qualité** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Vitesse** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Coût** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Contexte** | 1M tokens | 1M tokens |
| **Raisonnement** | Excellent | Très bon |

---

## 💡 Recommandation

### Pour Production : gemini-3-pro-preview ✅

**Raisons** :
- ✅ Modèle le plus récent (Gemini 3)
- ✅ Meilleures capacités de raisonnement
- ✅ Meilleures analogies (plus contextualisées)
- ✅ Performances optimales pour explications complexes

### Pour Dev/Test : gemini-1.5-flash

**Raisons** :
- ✅ Plus rapide (itérations rapides)
- ✅ Moins cher (économies en dev)
- ✅ Qualité suffisante pour tests

---

## 🔍 Vérifier les Modèles Disponibles

Pour lister tous les modèles disponibles avec votre clé API :

```bash
cd /Users/dannezri/Desktop/Pulse/backend
python3 test_list_models.py
```

---

## 📝 Note sur Gemini 2.0

**Gemini 2.0 n'est pas encore disponible publiquement.**

Les modèles `gemini-2.0-*` sont :
- ❌ En alpha/beta privée
- ❌ Pas accessible avec des clés API publiques
- ❌ Pas de date de sortie publique annoncée

**Quand Gemini 2.0 sortira** :
1. Mettre à jour `gemini_client.py` ligne 36
2. Changer le modèle par défaut
3. Tester avec le script `test_gemini_thinking.py`

---

**Status** : ✅ **gemini-3-pro-preview Configuré et Prêt**  
**Date** : 2026-02-03  
**Version** : v1.3 (Gemini 3 - Production Ready)
