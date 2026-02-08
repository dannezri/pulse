# 🧪 Tests Unitaires - Extraction des Données Biométriques

**Date**: 3 février 2026  
**Objectif**: Valider que toutes les données nécessaires pour Gemini sont correctement récupérées

---

## 📋 Scripts de Test Créés

### 1. **`inspect_biometrics.py`** - Inspection des données disponibles
**Objectif**: Voir quels `metric_type` sont disponibles dans la table `biometrics`

```bash
cd /Users/dannezri/Desktop/Pulse/backend
python3 inspect_biometrics.py
```

**Ce qu'il fait**:
- Liste tous les `metric_type` disponibles pour aujourd'hui
- Affiche les baselines utilisateur
- Suggère les ajustements à faire dans `_get_biometrics()`

---

### 2. **`test_biometrics_extraction.py`** - Test complet de toutes les tables
**Objectif**: Vérifier toutes les sources de données (biometrics, baselines, états latents, energy, forecast)

```bash
cd /Users/dannezri/Desktop/Pulse/backend
python3 test_biometrics_extraction.py
```

**Ce qu'il fait**:
- ✅ Vérifie la table `biometrics`
- ✅ Vérifie la table `user_baselines`
- ✅ Vérifie la table `daily_state`
- ✅ Vérifie la table `daily_energy`
- ✅ Vérifie la table `intraday_energy_forecast`
- 📊 Affiche un résumé détaillé de ce qui est disponible/manquant

---

### 3. **`test_get_biometrics.py`** - Test de la fonction spécifique
**Objectif**: Tester directement la fonction `_get_biometrics()` modifiée

```bash
cd /Users/dannezri/Desktop/Pulse/backend
python3 test_get_biometrics.py
```

**Ce qu'il fait**:
- 🎯 Appelle directement `_get_biometrics()`
- 📊 Affiche les valeurs récupérées pour chaque champ
- ❌ Identifie les champs manquants
- 💡 Suggère des solutions

---

## 🚀 Procédure de Test Complète

### **Étape 1: Inspection des données**
```bash
cd /Users/dannezri/Desktop/Pulse/backend
python3 inspect_biometrics.py
```

👉 Cela vous montrera les noms exacts des `metric_type` dans votre base de données.

---

### **Étape 2: Test de l'extraction complète**
```bash
python3 test_biometrics_extraction.py
```

👉 Cela validera que toutes les tables contiennent des données pour aujourd'hui.

---

### **Étape 3: Test de la fonction spécifique**
```bash
python3 test_get_biometrics.py
```

👉 Cela vérifiera que `_get_biometrics()` récupère bien toutes les données.

---

### **Étape 4: Ajustements si nécessaire**

Si des données manquent, ajustez les noms de `metric_type` dans `explain_service.py` :

**Exemple actuel** (lignes 221-235) :
```python
# HRV
hrv_result = supabase.client.table("biometrics") \
    .select("value") \
    .eq("user_id", user_id) \
    .eq("metric_type", "hrv")  # ⚠️ Ajuster ce nom si nécessaire
    ...
```

**Remplacez** `"hrv"` par le nom exact trouvé à l'étape 1 (ex: `"heart_rate_variability"`, `"oura_hrv"`, etc.)

---

### **Étape 5: Redémarrer le backend**
```bash
cd /Users/dannezri/Desktop/Pulse
./restart_api_server.sh
```

---

## 📊 État Actuel des Données (d'après les logs)

| Donnée | Status | Valeur Actuelle |
|--------|--------|-----------------|
| Score d'énergie | ✅ | 36% |
| Confidence | ⚠️ | 27% (devrait être > 70%) |
| RHR nuit | ✅ | 92 bpm (baseline: 45 bpm) |
| HRV nuit | ❌ | Manquant |
| Sleep Score Oura | ❌ | Manquant |
| États latents | ✅ | Recovery: 19%, Sleep Debt: 100%, Overtrain: 13% |
| Médicaments | ✅ | 3 actifs |
| Conditions | ✅ | 1 active (Dépression) |

---

## 🎯 Objectif

**Augmenter la confidence de 27% à > 70%** en s'assurant que toutes les données biométriques sont correctement récupérées.

---

## 💡 Ce Qui Fonctionne Déjà

✅ **Backend**: Appelle correctement Gemini 3 Pro  
✅ **Gemini**: Génère du texte naturel avec Markdown  
✅ **Frontend**: Affiche le texte avec rendering Markdown (`**bold**`)  
✅ **Données**: RHR, états latents, médicaments, conditions récupérés  

---

## ⚠️ Ce Qui Manque

❌ **HRV nuit**: Non récupérée (cause probable: mauvais nom de `metric_type`)  
❌ **Sleep Score Oura**: Non récupéré (cause probable: mauvais nom de `metric_type`)  

---

## 📝 Notes

- Les scripts sont prêts à être exécutés
- Ils affichent des résultats colorés et détaillés
- Ils suggèrent automatiquement les corrections à apporter
- Aucune modification de code n'est nécessaire pour les tests

---

**Prochaine action**: Exécuter `inspect_biometrics.py` pour voir les noms exacts des metric_type disponibles.
