# ✅ FIX FINAL : Extraction des données biométriques

## 🔍 Problème racine identifié

Les tables `sleep_data`, `readiness_data`, et `activity_data` **n'existent PAS** dans Supabase !

Le code essayait de récupérer des données depuis des tables inexistantes, d'où les erreurs 404 et les données toujours `None`.

## ✅ Solution appliquée

### 1. **Réécriture complète de `_get_biometrics()`**

**AVANT** (tables inexistantes) :
```python
sleep_result = self.supabase.client.table("sleep_data")  # ❌ N'existe pas !
readiness_result = self.supabase.client.table("readiness_data")  # ❌ N'existe pas !
activity_result = self.supabase.client.table("activity_data")  # ❌ N'existe pas !
```

**APRÈS** (table réelle `biometrics`) :
```python
bio_result = self.supabase.client.table("biometrics") \
    .select("metric_type, value") \
    .eq("user_id", user_id) \
    .gte("recorded_at", start_of_day) \
    .lte("recorded_at", end_of_day) \
    .execute()

# Mapper les métriques par type
for row in bio_result.data:
    metric_type = row.get("metric_type")
    value = row.get("value")
    
    if metric_type == "hrv" or metric_type == "hrv_night":
        biometrics["hrv_night"] = value
    elif metric_type == "hr" or metric_type == "rhr":
        biometrics["rhr_night"] = value
    # etc.
```

### 2. **Nouvelle structure de retour (plate)**

```python
biometrics = {
    "hrv_night": 45,  # Directement accessible
    "rhr_night": 65,
    "sleep_score": 85,
    "readiness_score": 72,
    "activity_score": 80,
    "steps": 8579,
    "hrv_baseline": 50,
    "rhr_baseline": 60,
}
```

### 3. **Mise à jour de `_build_prompt()`**

**AVANT** (structure imbriquée) :
```python
sleep_data = biometrics.get("sleep", {})
hrv_night = sleep_data.get("hrv_night")
```

**APRÈS** (structure plate) :
```python
hrv_night = biometrics.get("hrv_night")
```

### 4. **Baselines depuis `user_baselines`**

```python
baseline_result = self.supabase.client.table("user_baselines") \
    .select("baseline_type, baseline_data") \
    .eq("user_id", user_id) \
    .execute()

for row in baseline_result.data:
    if baseline_type == "hrv":
        biometrics["hrv_baseline"] = baseline_data.get("value")
```

## 📊 Résultat attendu

Après redémarrage du backend, les logs devraient afficher :

```
[explain_service] 📊 Biometrics extracted: HRV=45, RHR=65, Sleep=85, Readiness=72, Steps=8579
[explain_service] 📊 Baselines: HRV_baseline=50, RHR_baseline=60
```

Et Gemini **ne dira plus** :
> "Je remarque immédiatement qu'il nous manque tes données physiologiques..."

Mais dira plutôt :
> "Ton HRV de 45ms est en dessous de ta baseline de 50ms, ce qui explique..."

## 🚀 Action requise

**Redémarrer le backend** (terminal 235) :
```bash
Ctrl+C
./restart_api_server.sh
```

Puis dans l'app :
1. Appuyer sur le bouton **🧹** (orange, 4ème en haut)
2. Regarder les logs

## ✅ Toutes les corrections appliquées

1. ✅ Prompt corrigé (supprimé "au format JSON")
2. ✅ Fonction `_clean_json_response()` pour nettoyer le JSON automatiquement
3. ✅ **Extraction HRV/RHR réécrite pour utiliser la table `biometrics` réelle**
4. ✅ **Baselines extraits depuis `user_baselines`**
5. ✅ Logs ajoutés pour debugging

**Le texte sera propre ET les données seront présentes !** 🎉
