# 🔧 Correction du Parsing JSON Gemini

## 🐛 Problème Identifié

**Erreur Backend** :
```
WARNING:gemini_client:⚠️ Gemini response is not valid JSON: Expecting value: line 194 column 1 (char 6964)
ERROR:medication_analysis_service:❌ Invalid JSON from Gemini: Expecting value: line 194 column 1 (char 6964)
```

**Erreur Mobile** :
```
LOG  [useMedicationAnalysis] ✅ Analysis received: {"analyse_traitements": [], "error": "Erreur de parsing de la réponse Gemini"}
```

**Cause** : Gemini génère du JSON avec des **commentaires JavaScript** (`// ...`) qui ne sont pas valides en JSON standard.

Exemple de ce que Gemini générait :
```json
{
  "effets_horaires": [
    {"heure": "00:00", ...},
    {"heure": "01:00", ...}
    // ... pour toutes les 24 heures (00:00 à 23:00)
  ]
}
```

## ✅ Corrections Appliquées

### 1. Nettoyage du JSON dans `gemini_client.py`

**Avant** (ligne 133) :
```python
parsed = json.loads(actual_content)
```

**Après** (ligne 133-145) :
```python
# Nettoyer le contenu avant parsing (enlever les commentaires JS)
cleaned_content = actual_content

# Supprimer les commentaires // en fin de ligne
import re
cleaned_content = re.sub(r'//[^\n]*', '', cleaned_content)

# Supprimer les virgules avant les accolades fermantes (trailing commas)
cleaned_content = re.sub(r',(\s*[}\]])', r'\1', cleaned_content)

# Parser le JSON de sortie
try:
    parsed = json.loads(cleaned_content)
```

### 2. Amélioration du Prompt dans `medication_analysis_service.py`

**Ajout dans le prompt utilisateur** (ligne 217) :
```python
IMPORTANT: 
- Fournis EXACTEMENT 24 heures (00:00 à 23:00) pour chaque médicament
- PAS de commentaires dans le JSON
- PAS de texte explicatif avant ou après
- JSON valide uniquement
```

**Ajout dans le prompt système** (ligne 263) :
```python
FORMAT DE SORTIE :
- Réponds UNIQUEMENT en JSON valide
- Pas de texte avant ou après le JSON
- Pas de markdown (```json)
- PAS DE COMMENTAIRES dans le JSON (pas de //, pas de ...)  ← NOUVEAU
- Structure exacte demandée dans le prompt utilisateur
- Pour les effets horaires: fournis EXACTEMENT 24 heures (00:00 à 23:00) pour chaque médicament  ← NOUVEAU
```

### 3. Suppression du Cache

```sql
DELETE FROM medication_analysis_cache
WHERE user_id = 'c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd';
```

✅ Cache supprimé pour forcer une nouvelle génération avec le prompt corrigé.

## 🔄 Prochaines Étapes

### 1️⃣ Redémarrer le Backend

**Option A** : Dans le terminal 2 (backend)
```bash
Ctrl+C  # Arrêter le serveur actuel
./restart_api_server.sh  # Redémarrer
```

**Option B** : Script de redémarrage forcé
```bash
cd /Users/dannezri/Desktop/Pulse/backend
chmod +x FORCE_RESTART.sh
./FORCE_RESTART.sh
```

### 2️⃣ Recharger l'App Mobile

Dans Metro (terminal 33), appuyez sur **`r`**

### 3️⃣ Vérifier les Logs

**Backend** devrait afficher :
```
INFO: Calling Gemini 3 Pro...
INFO: ✅ Generated analysis for 2 medications
INFO: 💰 Cost: $0.01XX USD
INFO: 💾 Stored analysis in cache
```

**Mobile** devrait afficher :
```
LOG  [useMedicationAnalysis] ✅ Analysis received: {"cost": 0.01XX, "medications_count": 2}
LOG  [Medications] 🔎 Recherche analyse pour "VENLAFAXINE...": ✅ Trouvée
```

### 4️⃣ Vérifier le Graphique

1. Ouvrir un médicament
2. Déplier la section complète
3. Scroller jusqu'à **"Profil d'efficacité sur 24h"**
4. Le graphique devrait s'afficher avec 24 heures de données

## 🎯 Résultat Attendu

```json
{
  "analyse_traitements": [
    {
      "nom": "VENLAFAXINE ARROW GENERIQUES LP 37,5 mg",
      "intro_explicative": "...",
      "impact_corps": "...",
      "impact_journee": "...",
      "observation": "...",
      "effets_horaires": [
        {"heure": "00:00", "concentration": 85, "efficacite": 90, "effets_secondaires": 10, "description": "..."},
        {"heure": "01:00", "concentration": 82, "efficacite": 88, "effets_secondaires": 8, "description": "..."},
        ... (22 autres heures)
      ]
    }
  ],
  "_cost": 0.015,
  "_generated_at": "2026-02-06T...",
  "_medications_count": 2
}
```

## 🐛 Si le Problème Persiste

### Vérifier que le code a été sauvegardé

```bash
cd /Users/dannezri/Desktop/Pulse/backend
grep -n "PAS DE COMMENTAIRES" medication_analysis_service.py
grep -n "cleaned_content" gemini_client.py
```

**Attendu** :
- `medication_analysis_service.py:262:- PAS DE COMMENTAIRES dans le JSON`
- `gemini_client.py:136:cleaned_content = actual_content`

### Logs de Debug

Si Gemini continue à générer du JSON invalide, ajouter ces logs dans `gemini_client.py` :

```python
logger.debug(f"Raw Gemini response: {actual_content}")
logger.debug(f"Cleaned content: {cleaned_content}")
```

Puis redémarrer et observer les logs.

## 📝 Fichiers Modifiés

1. ✅ `backend/gemini_client.py` - Nettoyage JSON (ligne 133-145)
2. ✅ `backend/medication_analysis_service.py` - Prompt amélioré (lignes 217, 262)
3. ✅ `mobile/src/hooks/useMedicationAnalysis.ts` - Query key v2 + staleTime 0
4. ✅ Cache Supabase supprimé

## ✅ Prêt à Tester !

**Redémarrez le backend maintenant** et rechargez l'app mobile. Le problème de parsing JSON devrait être résolu ! 🎉
