# Fix : Dosage Total des Médicaments (pills_per_intake)

## Date
2026-02-01 22:30

## 🐛 Problème Identifié

Les médicaments n'étaient **pas correctement dosés** dans les calculs d'impact énergétique et l'affichage.

### Exemple Concret : Sertraline

**En base de données** :
- `dosage` : 50 mg (dosage par comprimé)
- `pills_per_intake` : **3** (nombre de comprimés)
- **Dosage total réel** : 50 mg × 3 = **150 mg**

### ❌ Comportement Avant le Fix

1. **Affichage** : "💊 Sertraline **50mg**" (au lieu de 150mg)
2. **Impact** : Calculé sur 50mg (au lieu de 150mg)
3. **Résultat** : Impact sous-estimé de **66%** !

---

## 🔍 Cause Racine

### 1. ❌ `pills_per_intake` Non Récupéré

**Fichier** : `backend/intraday_energy_service.py` (ligne 395-397)

```python
# ❌ AVANT
medications_response = supabase.table("user_medications").select(
    "medication_name, active_substance, atc_code, dosage, dosage_unit, start_date"
    # pills_per_intake MANQUANT !
).eq("user_id", user_id).eq("is_active", True).execute()
```

### 2. ❌ Impact Non Ajusté par le Dosage Total

**Fichier** : `backend/intraday_energy_service.py` (ligne 502-512)

```python
# ❌ AVANT
base_impact = impact_data.get('chronic_impact', 0)  # Impact pour 1 pilule
# Pas de multiplication par pills_per_intake !
adjusted_impact = base_impact * weight  # ❌ Impact sous-estimé
```

### 3. ❌ Affichage du Dosage Incomplet

**Fichier** : `backend/intraday_energy_service.py` (ligne 534-536)

```python
# ❌ AVANT
dosage = med.get('dosage', '')  # Seulement le dosage par comprimé
full_name = f"{phase_emoji} {med_name} {dosage}{dosage_unit}"
# Affiche: "💊 Sertraline 50mg" au lieu de "💊 Sertraline 150mg"
```

---

## ✅ Corrections Apportées

### 1. ✅ Récupération de `pills_per_intake`

**Fichier** : `backend/intraday_energy_service.py` (ligne 395-397)

```python
# ✅ APRÈS
medications_response = supabase.table("user_medications").select(
    "medication_name, active_substance, atc_code, dosage, dosage_unit, pills_per_intake, start_date"
    # ✅ pills_per_intake AJOUTÉ
).eq("user_id", user_id).eq("is_active", True).execute()
```

### 2. ✅ Calcul du Dosage Total et Ajustement de l'Impact

**Fichier** : `backend/intraday_energy_service.py` (ligne 502-523)

```python
# ✅ APRÈS
# Calculer le dosage total (dosage par comprimé × nombre de comprimés)
dosage_per_pill = med.get('dosage', 0)
pills_per_intake = med.get('pills_per_intake', 1.0)
total_dosage = dosage_per_pill * pills_per_intake

# Calculer l'impact (utiliser chronic_impact pour simplifier dans V1)
base_impact = impact_data.get('chronic_impact', 0)

# Si le médicament est un sédatif, utiliser la fourchette négative
if impact_data.get('energy_category') == 'sedative':
    base_impact = (impact_data.get('acute_impact_min', 0) + impact_data.get('acute_impact_max', 0)) / 2

# ✅ Ajuster l'impact en fonction du dosage total
# L'impact de référence dans la DB est pour 1 pilule standard
# On multiplie proportionnellement l'impact par le nombre de pilules
dosage_multiplier = pills_per_intake
base_impact = base_impact * dosage_multiplier

# Appliquer le poids personnalisé ML
weight_key = ('medication', atc_code)
weight = personalized_weights.get(weight_key, 1.0)
adjusted_impact = base_impact * weight
```

### 3. ✅ Affichage du Dosage Total

**Fichier** : `backend/intraday_energy_service.py` (ligne 548-558)

```python
# ✅ APRÈS
# Nom complet avec dosage total
med_name = med.get('medication_name', 'Médicament')
dosage_unit = med.get('dosage_unit', '')

# Afficher le dosage total (dosage × pills_per_intake)
if total_dosage and dosage_unit:
    # Formater proprement (ex: 7.5mg, pas 7.5000mg)
    if total_dosage % 1 == 0:
        full_name = f"{phase_emoji} {med_name} {int(total_dosage)}{dosage_unit}"
    else:
        full_name = f"{phase_emoji} {med_name} {total_dosage:.1f}{dosage_unit}"
else:
    full_name = f"{phase_emoji} {med_name}"
```

---

## 📊 Impact des Corrections

### Exemple : Médicaments de l'Utilisateur

| Médicament | Dosage/comprimé | Comprimés | ❌ Avant | ✅ Après |
|------------|-----------------|-----------|----------|----------|
| **Sertraline** | 50 mg | **3** | "50mg" (impact ×1) | "**150mg**" (impact ×3) |
| **Mirtazapine** | 15 mg | **0.5** | "15mg" (impact ×1) | "**7.5mg**" (impact ×0.5) |
| **Melatonine** | 1 mg | **1** | "1mg" (impact ×1) | "**1mg**" (impact ×1) |

### Impact sur les Influencers

#### ❌ Avant le Fix

```
⚠️ Facteurs négatifs:
  • 💊 Sertraline 50mg: -12%    ❌ SOUS-ESTIMÉ
  • 💊 Mirtazapine 15mg: -10%   ❌ SUR-ESTIMÉ
  • 💊 Melatonine 1mg: -5%      ✅ OK
```

#### ✅ Après le Fix

```
⚠️ Facteurs négatifs:
  • 💊 Sertraline 150mg: -36%   ✅ CORRECT (×3)
  • 💊 Mirtazapine 7.5mg: -5%   ✅ CORRECT (×0.5)
  • 💊 Melatonine 1mg: -5%      ✅ CORRECT (×1)
```

---

## 🎯 Validation

### 1. Vérifier les Données en DB

```sql
SELECT 
  medication_name,
  dosage,
  dosage_unit,
  pills_per_intake,
  (dosage * pills_per_intake) AS total_dosage
FROM user_medications
WHERE user_id = 'c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd'
  AND is_active = true;
```

**Résultat attendu** :

| medication_name | dosage | dosage_unit | pills_per_intake | total_dosage |
|-----------------|--------|-------------|------------------|--------------|
| Sertraline | 50 | mg | 3 | **150** |
| Mirtazapine | 15 | mg | 0.5 | **7.5** |
| Melatonine | 1 | mg | 1 | **1** |

### 2. Vérifier les Influencers Générés

Après redémarrage du backend et refresh de l'app :

```javascript
// Console Expo
[EnergyAnalysis] Influencers:
[
  {
    name: "💊 Sertraline 150mg",  // ✅ Dosage total affiché
    impact: "-36%",                // ✅ Impact ajusté (×3)
    status: "negative"
  },
  {
    name: "💊 Mirtazapine 7.5mg",  // ✅ Dosage total affiché
    impact: "-5%",                 // ✅ Impact ajusté (×0.5)
    status: "negative"
  }
]
```

### 3. Vérifier le Rapport Partagé

Le rapport partagé doit afficher les dosages totaux :

```
⚠️ Facteurs négatifs:
  • 💊 Sertraline 150mg: -36%   ✅
  • 💊 Mirtazapine 7.5mg: -5%   ✅
  • 💊 Melatonine 1mg: -5%      ✅
```

---

## ⚠️ Actions Requises

### 1. Redémarrer le Backend

**Terminal 235** :

```bash
# 1. Arrêter le backend (Ctrl+C)

# 2. Redémarrer
cd /Users/dannezri/Desktop/Pulse/backend
./restart_api_server.sh
```

### 2. Recharger l'App Mobile

1. Ouvrir l'app Pulse
2. Aller sur "Analyse Énergétique"
3. Cliquer sur **🔄** (force refresh)
4. Attendre 2-3 secondes
5. Vérifier les dosages affichés

### 3. Tester le Partage

1. Cliquer sur **📤**
2. Vérifier que le rapport contient les dosages totaux
3. Vérifier que les impacts sont cohérents

---

## 🔬 Logs de Debug

### Backend

Après redémarrage, vérifier dans les logs :

```
INFO:intraday_energy_service:Generating influencers for user ...
INFO:intraday_energy_service:✓ Medication: Sertraline 150mg, impact: -36%
INFO:intraday_energy_service:✓ Medication: Mirtazapine 7.5mg, impact: -5%
```

### Mobile

Console Expo :

```javascript
[EnergyAnalysis] Has influencers: 7
[EnergyAnalysis] Influencers with dosage:
  - Sertraline 150mg: -36%  ✅
  - Mirtazapine 7.5mg: -5%  ✅
```

---

## 📈 Amélioration Future (Optionnel)

### Ajout d'un `standard_dosage` dans la DB

Actuellement, on multiplie l'impact proportionnellement au nombre de pilules. Cela peut être imprécis pour certains médicaments dont l'effet n'est pas linéaire.

**Amélioration** : Ajouter une colonne `standard_dosage` dans `medication_energy_impacts` :

```sql
ALTER TABLE medication_energy_impacts
ADD COLUMN standard_dosage DOUBLE PRECISION DEFAULT 1.0;

COMMENT ON COLUMN medication_energy_impacts.standard_dosage IS 
  'Dosage standard en mg pour lequel les impacts sont définis';
```

Puis ajuster l'impact avec un ratio plus précis :

```python
# Ratio de dosage par rapport au standard
standard_dosage = impact_data.get('standard_dosage', dosage_per_pill)
dosage_ratio = total_dosage / standard_dosage
base_impact = base_impact * dosage_ratio
```

---

## 📝 Résumé des Modifications

| Fichier | Ligne | Changement |
|---------|-------|------------|
| **backend/intraday_energy_service.py** | 396 | Ajout `pills_per_intake` dans SELECT |
| **backend/intraday_energy_service.py** | 502-520 | Calcul dosage total et ajustement impact |
| **backend/intraday_energy_service.py** | 548-558 | Affichage dosage total dans le nom |
| **Cache** | Supabase | Suppression forecast 2026-02-01 |

---

## 🎯 Checklist de Validation

- [x] `pills_per_intake` ajouté au SELECT
- [x] Dosage total calculé (`dosage × pills_per_intake`)
- [x] Impact ajusté par le dosage total
- [x] Affichage du dosage total dans le nom
- [x] Formatage propre (7.5mg, pas 7.5000mg)
- [x] Cache invalidé
- [ ] Backend redémarré (action utilisateur)
- [ ] App rechargée (action utilisateur)
- [ ] Validation visuelle (action utilisateur)

---

**Auteur** : Assistant AI  
**Date** : 2026-02-01 22:30  
**Status** : ⚠️ EN ATTENTE REDÉMARRAGE BACKEND  
**Impact** : 🔴 CRITIQUE (calculs d'énergie incorrects)  
**Tags** : #fix #medication #dosage #pills_per_intake #critical
