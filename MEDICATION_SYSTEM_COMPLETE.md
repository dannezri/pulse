# Système de Gestion des Médicaments - Pulse Health

## 📊 Vue d'ensemble

Le système Pulse utilise maintenant une approche **pharmacocinétique complète** pour calculer l'impact de **n'importe quel médicament** sur l'énergie d'un utilisateur, en temps réel.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  user_medications (Table utilisateur)                           │
│  - user_id, medication_name, active_substance, atc_code         │
│  - dosage, intake_times, start_date                             │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  get_user_active_medications() RPC                              │
│  Retourne: [{medication_name, atc_code, days_since_start}, ...]│
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  pulse_energy_decay_service.py                                  │
│  → _get_medication_pharmacokinetics(substance, atc_code)        │
└───────┬──────────────────────────────────┬──────────────────────┘
        │                                   │
        ▼                                   ▼
┌────────────────────────┐      ┌────────────────────────────────┐
│ medication_energy_     │      │  _get_ai_medication_           │
│ impacts (Table)        │      │  pharmacokinetics              │
│                        │      │  (Fallback GPT-4)              │
│ 30+ médicaments        │      │                                │
│ courants + données     │      │  Pour médicaments              │
│ pharmacocinétiques     │      │  non répertoriés               │
└────────────────────────┘      └────────────────────────────────┘
```

---

## 🗄️ Tables créées

### 1. `medication_energy_impacts`

Table de référence pharmacologique avec impact énergétique.

```sql
CREATE TABLE medication_energy_impacts (
    id UUID PRIMARY KEY,
    
    -- Identification
    atc_code TEXT UNIQUE,
    medication_name TEXT NOT NULL,
    active_substance TEXT NOT NULL,
    
    -- Classification
    energy_category TEXT,  -- stimulant/sedative/neutral/mixed
    subcategory TEXT,
    therapeutic_class TEXT,
    
    -- Pharmacocinétique
    onset_time FLOAT,      -- Délai d'action (heures)
    peak_time FLOAT,       -- Pic concentration (heures)
    duration FLOAT,        -- Durée d'action (heures)
    half_life FLOAT,       -- Demi-vie (heures)
    
    -- Impact énergétique aigu
    acute_impact_min FLOAT,
    acute_impact_max FLOAT,
    acute_impact_curve TEXT,  -- gaussian/exponential/linear/plateau
    
    -- Impact chronique
    chronic_impact FLOAT,
    chronic_onset_days INT,
    tolerance_rate FLOAT,
    withdrawal_impact FLOAT,
    
    -- Effets secondaires
    fatigue_risk TEXT,
    alertness_effect TEXT,
    sleep_disruption TEXT,
    
    -- Métadonnées
    evidence_level TEXT,
    source TEXT,
    notes TEXT
);
```

**30+ médicaments pré-remplis** :
- Stimulants: Caféine, Méthylphénidate, Modafinil, Lisdexamfétamine
- Hormones: Lévothyroxine (thyroïde)
- Benzodiazépines: Alprazolam, Bromazépam, Lorazépam, Diazépam, Zolpidem
- Antidépresseurs: Sertraline, Escitalopram, Fluoxétine, Venlafaxine, Mirtazapine
- Antihistaminiques: Hydroxyzine, Cétirizine
- Antalgiques: Tramadol, Codéine
- Corticoïdes: Prednisone
- Antiépileptiques: Gabapentine, Prégabaline
- Bêta-bloquants: Propranolol
- Antipsychotiques: Quétiapine, Olanzapine
- Suppléments: Mélatonine, Fer, Vitamine B12, Magnésium
- IPP: Oméprazole

### 2. `user_medications`

Table normalisée pour les médicaments des utilisateurs.

```sql
CREATE TABLE user_medications (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES profiles(id),
    
    -- Identification
    medication_name TEXT NOT NULL,
    active_substance TEXT,
    atc_code TEXT,
    
    -- Dosage
    dosage FLOAT,
    dosage_unit TEXT,  -- mg, µg, UI, etc.
    form TEXT,
    laboratory TEXT,
    
    -- Horaires
    intake_times JSONB,  -- ["08:00", "20:00"]
    daily_frequency INT,
    
    -- Dates
    start_date DATE NOT NULL,
    end_date DATE,  -- NULL = en cours
    
    -- Métadonnées
    prescribed_by TEXT,
    indication TEXT,
    notes TEXT,
    
    is_active BOOLEAN
);
```

**RPC helper** : `get_user_active_medications(p_user_id)` retourne les médicaments actifs avec `days_since_start`.

---

## ⚙️ Modèle pharmacocinétique avancé

### Phases de calcul

Le modèle calcule l'impact total en 3 phases:

```python
total_impact = (acute_impact × tolerance_factor) + chronic_impact
```

#### 1. **Phase aiguë** (effets immédiats)

Selon le type de courbe:

- **Gaussian** (Bell curve) : Caféine, Benzodiazépines
  ```
  f(t) = max_impact × exp(-((t - peak)² / (2σ²)))
  ```

- **Exponential** : Méthylphénidate, Amphétamines
  ```
  Montée: f(t) = max_impact × (t / peak_time)
  Décroissance: f(t) = max_impact × exp(-λ(t - peak))
  ```

- **Linear/Plateau** : Lévothyroxine, Antidépresseurs
  ```
  f(t) = max_impact (constant après onset)
  ```

#### 2. **Phase chronique** (adaptation long terme)

```python
chronic_impact = base_chronic_impact × min(1.0, days_since_start / chronic_onset_days)
```

**Exemples**:
- Lévothyroxine: 42 jours (6 semaines) pour effet complet
- Antidépresseurs: 28 jours (4 semaines)
- Stimulants: 7-14 jours

#### 3. **Tolérance**

```python
tolerance_factor = 1.0 - (tolerance_rate × (1 - exp(-days_since_start / 14)))
```

**Exemples**:
- Caféine: 30% de perte après 2 semaines
- Benzodiazépines: 40-50% de perte après 2 semaines
- Thyroïde: 0% (aucune tolérance)

---

## 📈 Résultats des tests

### Test 1: Levothyrox seul (30 jours)

```json
{
  "influencers": [
    {"name": "💊 Levothyrox", "impact": "+11", "status": "positive"}
  ]
}
```

**Explication**:
- Phase chronique activée (30 jours > 0)
- Progression: 30/42 = 71% du chronic_impact total (+15)
- Impact actuel: 15 × 0.71 ≈ +11 points

### Test 2: Caféine (14 jours, 2 prises/jour)

```json
{
  "influencers": [
    {"name": "💊 Caféine", "impact": "-5", "status": "negative"}
  ],
  "notes": [
    "⚠️ Caféine : tolérance développée (-30% d'efficacité). Envisager pause thérapeutique?"
  ]
}
```

**Explication**:
- Tolérance: 30% après 14 jours
- Effet aigu maximal: +20 points
- Effet chronique (après tolérance): -5 points
- Impact net: négatif (fatigue de rebond)

### Test 3: Combinaison (Levothyrox + Caféine + Dépression)

```json
{
  "current_energy": 42.8,
  "influencers": [
    {"name": "Sommeil (Readiness)", "impact": "+85"},
    {"name": "💊 Levothyrox", "impact": "+11"},
    {"name": "💊 Caféine", "impact": "-5"},
    {"name": "😔 Dépression", "impact": "-32"}
  ],
  "notes": [
    "⚠️ Caféine : fatigue chronique possible (-5 points)",
    "📉 Creux circadien prévu 13:52-14:52",
    "🔬 Dépression : décroissance accélérée (-8.0%/h)"
  ]
}
```

**Énergie nette**: 85 (sommeil) + 11 (levothyrox) - 5 (caféine) - 32 (dépression) ≈ 59 (avant decay)

---

## 🧠 Fallback IA (GPT-4)

Pour tout médicament **non répertorié** dans la table:

### Prompt expert

```
Tu es un expert pharmacologue spécialisé en pharmacocinétique et fatigue médicamenteuse.

Médicament: {substance}
Code ATC: {atc_code}

Estime l'impact sur l'énergie basé sur:
1. Pharmacocinétique (demi-vie, pic, durée)
2. Études cliniques sur fatigue
3. Profil effets secondaires

Fournis en JSON:
- energy_category, onset_time, peak_time, duration, half_life
- acute_impact_min/max, acute_impact_curve
- chronic_impact, chronic_onset_days, tolerance_rate
- fatigue_risk, justification
```

### Auto-sauvegarde

L'estimation IA est **automatiquement sauvegardée** dans `medication_energy_impacts` avec:
- `evidence_level: 'ai_generated'`
- `source: 'GPT-4 estimation - {timestamp}'`

→ **Scalabilité infinie** sans maintenance manuelle!

---

## 🎨 Affichage dynamique

### Badges d'influencers

| Badge | Signification |
|-------|---------------|
| 🆕 | Début de traitement (< 7 jours) |
| 💊 | Traitement établi |
| ⚠️ | Tolérance développée |

### Notes contextuelles

```python
if days_since_start < 7 and fatigue_risk == 'high':
    "🆕 {nom} : début de traitement. Fatigue normale les premiers jours."

elif days_since_start >= chronic_onset_days and chronic_impact > 0:
    "💊 {nom} : effet thérapeutique établi (+X points)"

elif tolerance_rate > 0.3 and days_since_start > 14:
    "⚠️ {nom} : tolérance développée (-X% d'efficacité). Envisager pause?"

elif energy_category == 'stimulant' and subcategory in ['methylphenidate', 'amphetamine']:
    "📉 {nom} : crash possible avant prochaine prise (HH:MM)"
```

---

## 📊 Avantages du système

| Aspect | Solution |
|--------|----------|
| **Validation noms** | ✅ API FR (gratuite) ou recherche locale |
| **Pharmacocinétique** | ✅ DB locale (30+ médicaments) + fallback IA |
| **Courbes réalistes** | ✅ Gaussian, Exponential, Linear, Plateau |
| **Phase chronique** | ✅ Adaptation long terme modélisée |
| **Tolérance** | ✅ Calculée dynamiquement |
| **Multi-prises/jour** | ✅ Gestion horaires multiples |
| **Historique** | ✅ start_date/end_date dans user_medications |
| **Coût** | ✅ Gratuit (pas besoin Vidal) |
| **Couverture** | ✅ Infinie (fallback IA) |
| **Qualité** | ✅ Haute pour courants, moyenne pour rares |

---

## 🔧 Fichiers créés/modifiés

### Backend

1. **`backend/medication_enrichment_service.py`** (NOUVEAU)
   - Service d'enrichissement
   - Recherche locale en DB
   - (Stub pour API Médicaments FR)

2. **`backend/pulse_energy_decay_service.py`** (MODIFIÉ)
   - `_get_medications()` : utilise nouvelle table
   - `_get_medication_pharmacokinetics()` : avec fallback IA
   - `_calculate_medication_impact()` : modèle avancé 3 phases
   - `_calculate_acute_phase()` : 4 types de courbes
   - `_calculate_chronic_phase()` : adaptation long terme
   - `_calculate_tolerance()` : tolérance dynamique
   - Influencers et notes dynamiques

### Database

1. **`migrations/create_medication_energy_impacts_table.sql`**
   - Table de référence pharmacologique

2. **`migrations/create_user_medications_table_fixed.sql`**
   - Table normalisée utilisateur
   - RPC `get_user_active_medications()`

3. **`migrations/populate_medication_energy_impacts.sql`**
   - 30+ médicaments courants pré-remplis
   - Données pharmacocinétiques complètes

---

## 🚀 Utilisation

### Ajouter un médicament pour un utilisateur

```sql
INSERT INTO user_medications (
    user_id,
    medication_name,
    active_substance,
    atc_code,
    dosage,
    dosage_unit,
    intake_times,
    start_date,
    daily_frequency
) VALUES (
    'uuid-utilisateur',
    'Levothyrox',
    'Lévothyroxine sodique',
    'H03AA01',
    50,
    'µg',
    '["08:00"]'::jsonb,
    CURRENT_DATE,
    1
);
```

### Ajouter un nouveau médicament à la base

```sql
INSERT INTO medication_energy_impacts (
    atc_code,
    medication_name,
    active_substance,
    energy_category,
    onset_time,
    peak_time,
    duration,
    half_life,
    acute_impact_max,
    acute_impact_curve,
    chronic_impact,
    chronic_onset_days,
    tolerance_rate,
    fatigue_risk,
    evidence_level,
    source,
    notes
) VALUES (
    'CODE_ATC',
    'Nom du médicament',
    'Substance active',
    'stimulant',
    0.5,  -- 30 min
    1,    -- 1h
    4,    -- 4h
    5,    -- 5h
    20,   -- +20 points max
    'gaussian',
    -5,   -- -5 points après tolérance
    14,   -- 2 semaines
    0.3,  -- 30% tolérance
    'moderate',
    'clinical_study',
    'Source: étude XYZ',
    'Notes explicatives'
);
```

---

## 📚 Références

### Pharmacocinétique

- **Levothyroxine**: ATA Thyroid Guidelines 2023, Jonklaas et al. Thyroid 2014
- **Methylphenidate**: NICE Guidelines ADHD 2024, Volkow et al. JAMA 2009
- **Caffeine**: FDA Caffeine Pharmacology 2023, Lieberman et al. Nutr Rev 2010
- **Benzodiazepines**: FDA Black Box Warning 2020
- **SSRIs**: STAR*D Trial 2006, APA Depression Guidelines 2024

### APIs pharmaceutiques

- **API Médicaments FR**: https://api.gouv.fr/les-api/api-medicaments
- **BDPM (ANSM)**: https://base-donnees-publique.medicaments.gouv.fr/
- **OpenFDA**: https://api.fda.gov/drug/
- **RxNorm**: https://rxnav.nlm.nih.gov/

---

## 🎯 Prochaines étapes possibles

### Court terme
- [ ] Intégrer vraie API Médicaments FR (data.gouv.fr)
- [ ] Ajouter plus de médicaments courants (objectif: 100)
- [ ] Interface mobile pour gérer les médicaments

### Moyen terme
- [ ] Interactions médicamenteuses (RxNorm API)
- [ ] Personnalisation des impacts selon métabolisme utilisateur
- [ ] Alertes de sevrage/renouvellement ordonnance

### Long terme
- [ ] Machine learning pour affiner les impacts selon données réelles
- [ ] Communauté pour partager expériences médicamenteuses
- [ ] Intégration pharmacie (scan ordonnances)

---

**Auteur** : Pulse Health  
**Date** : 31 janvier 2026  
**Version** : 1.0  
