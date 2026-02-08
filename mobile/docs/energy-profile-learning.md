# Profil Énergétique Personnel - Documentation

## Vue d'ensemble

Le **Profil Énergétique Personnel** est un système de machine learning qui analyse l'historique long terme (60-90 jours) pour identifier les patterns personnels de chaque utilisateur.

**Objectif** : Passer des insights génériques ("Le sommeil est important") aux insights personnels ("**Tu** récupères mieux avec 7h45 de sommeil").

---

## Format d'affichage

```
┌─────────────────────────────────────────┐
│ ✨ Ton Profil Énergétique               │
│ 3 traits personnels découverts          │
│                                          │
│ 💤 Sommeil                               │
│ ┌─────────────────────────────┐         │
│ │ Sommeil optimal: 7h45  [85%]│         │
│ │ Tu récupères mieux avec      │         │
│ │ 7h45 de sommeil (82% vs 68%) │         │
│ │ 25 points • +14%             │         │
│ └─────────────────────────────┘         │
│                                          │
│ 🏃 Exercice                              │
│ ┌─────────────────────────────┐         │
│ │ Sport tardif réduit HRV[78%]│         │
│ │ Sport après 19h réduit ta    │         │
│ │ HRV de 12% le lendemain      │         │
│ │ 18 points • -12%             │         │
│ └─────────────────────────────┘         │
│                                          │
│ 🍎 Nutrition                             │
│ ┌─────────────────────────────┐         │
│ │ Protéines optimales: 80g+[82%]│        │
│ │ Ta récupération est meilleure │        │
│ │ avec au moins 80g/jour        │        │
│ │ 20 points • +11%              │        │
│ └─────────────────────────────┘         │
└─────────────────────────────────────────┘
```

---

## Types de Traits Détectés

### 1. 💤 Sommeil optimal (`optimal_sleep_duration`)

**Ce qui est analysé** :
- Durée de sommeil (heures) × Score de récupération (0-100%)
- Historique : 90 jours
- Minimum : 15 points de données

**Algorithme** :
```python
# Grouper par tranches de 30 min
sleep_bins = {}
for entry in paired_data:
    bin_key = round(entry['sleep_hours'] * 2) / 2  # 7h, 7.5h, 8h, etc.
    sleep_bins[bin_key].append(entry['recovery'])

# Trouver la durée avec meilleure recovery moyenne
best_duration = max(sleep_bins, key=lambda d: mean(sleep_bins[d]))

# Calculer amélioration vs autres durées
improvement = ((best_recovery - avg_other) / avg_other) * 100
```

**Confidence** :
```
confidence = 0.60 + (sample_size / 50) * 0.20 + (improvement / 100)
Max: 0.95
```

**Exemple** :
```
Titre: "Sommeil optimal: 7h45"
Description: "Tu récupères mieux avec 7h45 de sommeil 
(récupération moyenne: 82% vs 68% pour autres durées)"
Confidence: 0.85 (85%)
Support: 25 points de données, +14% amélioration
```

---

### 2. 🏃 Impact sport tardif (`late_exercise_impact`)

**Ce qui est analysé** :
- Activité intense (>300 kcal) après 19h × HRV du lendemain
- Historique : 90 jours
- Minimum : 5 jours de sport tardif

**Algorithme** :
```python
# Identifier jours sport tardif
late_exercise_days = set()
for activity in activity_data:
    if activity.hour >= 19 and activity.value > 300:
        late_exercise_days.add(activity.date)

# Comparer HRV lendemain sport tardif vs jours normaux
hrv_after_late = [hrv for date in late_exercise_days if date+1 in hrv_data]
hrv_normal = [hrv for date in normal_days]

impact_percent = ((avg_hrv_late - avg_hrv_normal) / avg_hrv_normal) * 100

# Test statistique
t_stat, p_value = stats.ttest_ind(hrv_after_late, hrv_normal)
```

**Confidence** :
```
confidence = 0.65 + (sample_size / 30) * 0.20
Si p_value > 0.05: confidence *= 0.7
```

**Exemple** :
```
Titre: "Sport tardif réduit HRV"
Description: "Le sport après 19h réduit ta HRV de 12% 
le lendemain (48ms vs 54ms)"
Confidence: 0.78 (78%)
Support: 18 jours, p-value=0.03
```

---

### 3. 🍎 Apport protéique optimal (`protein_requirement`)

**Ce qui est analysé** :
- Protéines ingérées (g) × Récupération du lendemain (0-100%)
- Historique : 90 jours
- Minimum : 15 points de données

**Algorithme** :
```python
# Grouper par tranches de 20g
protein_bins = {}
for entry in paired_data:
    bin_key = (entry['protein'] // 20) * 20  # 60g, 80g, 100g, etc.
    protein_bins[bin_key].append(entry['recovery_next_day'])

# Trouver apport optimal (minimum 60g)
best_protein = max(
    [p for p in protein_bins if p >= 60],
    key=lambda p: mean(protein_bins[p])
)

improvement = ((best_recovery - avg_other) / avg_other) * 100
```

**Confidence** :
```
confidence = 0.60 + (sample_size / 40) * 0.20 + (improvement / 80)
Max: 0.90
```

**Exemple** :
```
Titre: "Protéines optimales: 80g+"
Description: "Ta récupération est meilleure avec au 
moins 80g de protéines par jour (78% vs 67% avec moins)"
Confidence: 0.82 (82%)
Support: 20 points, +11% amélioration
```

---

### 4. ☕ Cutoff caféine (`caffeine_cutoff`) - TODO

**Ce qui sera analysé** :
- Heure dernier café × Qualité sommeil
- Détectera l'heure limite personnelle (14h, 16h, 18h)

**Statut** : Non implémenté (nécessite tracking caféine)

---

### 5. 🍷 Sensibilité alcool (`alcohol_sensitivity`) - TODO

**Ce qui sera analysé** :
- Unités d'alcool × HRV / Recovery
- Détectera la tolérance personnelle

**Statut** : Non implémenté (nécessite tracking alcool)

---

## Architecture Technique

### Base de données

**Table** : `user_energy_profile`

```sql
CREATE TABLE user_energy_profile (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    trait_type TEXT NOT NULL,  -- 'optimal_sleep_duration', etc.
    category TEXT NOT NULL,     -- 'sleep', 'nutrition', 'exercise', etc.
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    value_numeric DECIMAL,
    value_text TEXT,
    confidence DECIMAL CHECK (confidence >= 0 AND confidence <= 1),
    support_data JSONB,         -- Métriques support (sample_size, etc.)
    discovered_at TIMESTAMP,
    last_validated TIMESTAMP,
    data_points_count INTEGER,
    is_active BOOLEAN,
    UNIQUE(user_id, trait_type)
);
```

**RPC Function** : `get_user_energy_profile(p_user_id UUID)`

---

### Backend Python

**Script** : `/backend/energy_profile_learning.py`

**Fonctions clés** :
```python
def analyze_optimal_sleep_duration(user_id: str) -> Optional[Dict]
def analyze_late_exercise_impact(user_id: str) -> Optional[Dict]
def analyze_protein_requirement(user_id: str) -> Optional[Dict]
def learn_energy_profile(user_id: str) -> Dict
def learn_all_users_profiles() -> List[Dict]
```

**Exécution** :
- Cron job hebdomadaire ou mensuel
- Commande : `python backend/energy_profile_learning.py`
- Ou pour un user : `python backend/energy_profile_learning.py <user_id>`

---

### Mobile

**Hook** : `useEnergyProfile(userId)`

```typescript
interface EnergyProfileTrait {
  id: string;
  trait_type: string;
  category: 'sleep' | 'nutrition' | 'exercise' | 'recovery' | 'stress' | 'timing';
  title: string;
  description: string;
  value_numeric?: number;
  value_text?: string;
  confidence: number; // 0-1
  support_data: {
    sample_size: number;
    improvement?: string;
    p_value?: number;
    [key: string]: any;
  };
  discovered_at: string;
  last_validated: string;
  data_points_count: number;
}

interface EnergyProfile {
  traits: EnergyProfileTrait[];
  hasData: boolean;
  traitsByCategory: Record<string, EnergyProfileTrait[]>;
  highConfidenceTraits: EnergyProfileTrait[]; // >= 80%
}
```

**Composant** : `<EnergyProfileCard profile={energyProfile} />`

**Intégration** : Écran Profil (`/app/(tabs)/profil.tsx`)

---

## Niveaux de Confidence

| Plage | Label | Couleur | Interprétation |
|-------|-------|---------|----------------|
| 85-100% | Très fiable | Vert (#00FF41) | Pattern validé, beaucoup de données |
| 75-84% | Fiable | Cyan (#00C7BE) | Pattern cohérent |
| 65-74% | Modéré | Orange (#FF9500) | Pattern suggéré |
| 60-64% | En cours | Gris (#8E8E93) | Besoin de plus de données |
| <60% | ❌ Non stocké | - | Pas assez fiable |

**Seuil minimum** : 60% pour stocker un trait

---

## Flow de données

```
┌─────────────────────────────────────────┐
│ Supabase Database                       │
│ ├─ biometrics (90 jours)                │
│ ├─ daily_state (90 jours)               │
│ ├─ food_logs (90 jours)                 │
│ └─ user_baselines                       │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ Backend Python (Cron mensuel)           │
│ energy_profile_learning.py              │
├─────────────────────────────────────────┤
│ 1. Récupère historique 90J              │
│ 2. Corrèle sommeil × recovery           │
│ 3. Détecte pattern optimal               │
│ 4. Calcule confidence                    │
│ 5. Sauvegarde dans user_energy_profile   │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ Mobile App (React Native)               │
│ useEnergyProfile()                      │
├─────────────────────────────────────────┤
│ 1. Fetch RPC get_user_energy_profile    │
│ 2. Groupe par catégorie                 │
│ 3. Affiche dans EnergyProfileCard       │
└─────────────────────────────────────────┘
```

---

## Exemples de Support Data

### Sommeil optimal

```json
{
  "sample_size": 25,
  "average_recovery": 82.3,
  "other_average": 68.1,
  "improvement": "+14%",
  "analyzed_days": 87
}
```

### Sport tardif

```json
{
  "sample_size": 18,
  "late_exercise_days": 18,
  "avg_hrv_late": 48.2,
  "avg_hrv_normal": 54.5,
  "p_value": 0.028
}
```

### Protéines

```json
{
  "sample_size": 20,
  "average_recovery": 77.8,
  "other_average": 66.9,
  "improvement": "+11%"
}
```

---

## États d'affichage

### 1. État vide (< 30 jours d'historique)

```
┌─────────────────────────────────────────┐
│ ✨ Ton Profil Énergétique               │
│ Patterns personnels appris              │
│                                          │
│        📈 (icône)                        │
│   Apprentissage en cours                │
│                                          │
│   Nous analysons ton historique pour    │
│   identifier tes patterns personnels.   │
│                                          │
│   Continue à utiliser Pulse pendant     │
│   au moins 30 jours pour découvrir ce   │
│   qui fonctionne le mieux pour toi.     │
└─────────────────────────────────────────┘
```

### 2. État avec données (≥ 1 trait découvert)

```
┌─────────────────────────────────────────┐
│ ✨ Ton Profil Énergétique               │
│ 3 traits personnels découverts          │
│                                          │
│ ℹ️ 2 traits haute confiance             │
│ Ces patterns sont validés par beaucoup  │
│ de données et sont très fiables.        │
│                                          │
│ [Traits groupés par catégorie]          │
└─────────────────────────────────────────┘
```

---

## Cas Limites Gérés

### 1. Données insuffisantes

```python
if len(sleep_data) < MIN_SAMPLE_SIZE:
    return None  # Ne génère pas le trait
```

### 2. Pattern non significatif

```python
if improvement < 5:  # Amélioration < 5%
    return None  # Pas de bénéfice clair
```

### 3. Faible confidence

```python
if confidence < MIN_CONFIDENCE:  # < 60%
    return None  # Pas assez fiable pour afficher
```

### 4. Test statistique échoué

```python
t_stat, p_value = stats.ttest_ind(group_a, group_b)
if p_value > 0.05:
    confidence *= 0.7  # Réduit confidence
```

---

## Évolutions Futures

### Phase 2 : Plus de traits (Q2 2026)

- ☕ **Caféine cutoff** : "Pas de café après 15h pour toi"
- 🍷 **Sensibilité alcool** : "1 verre réduit ta HRV de 8%"
- ⏰ **Meal timing** : "Meilleure fenêtre repas: 12h-19h30"
- 🌅 **Morning/evening person** : "Tu es une personne du matin"
- 💧 **Hydratation threshold** : "Vise 2.5L+ les jours sport"

### Phase 3 : Interactions (Q3 2026)

- **Multi-facteurs** : "Sommeil 7h45 + protéines 80g → récup +22%"
- **Conditions** : "Alcool + sport tardif → impact ×2 sur HRV"
- **Contexte** : "En voyage, besoin de 8h+ de sommeil"

### Phase 4 : Prédictif (Q4 2026)

- **Recommandations proactives** : "Demain sport prévu → mange 100g+ protéines aujourd'hui"
- **Optimisation** : "Décale ton sport de 19h à 17h pour +10% HRV"
- **Notifications** : "Tu n'as dormi que 6h → journée légère recommandée"

---

## Tests de Validation

### Scénarios de test

| # | Trait | Données | Résultat attendu |
|---|-------|---------|------------------|
| 1 | Sommeil optimal | 7h45 → 82% récup, 8h → 68% | Trait créé, confidence 85% |
| 2 | Sport tardif | 18J sport >19h, HRV -12% | Trait créé, confidence 78% |
| 3 | Protéines | 80g+ → 77% récup, <80g → 67% | Trait créé, confidence 82% |
| 4 | Données insuffisantes | 8 points seulement | Aucun trait (< 15 min) |
| 5 | Pattern faible | Amélioration +2% | Aucun trait (< 5%) |
| 6 | Faible confidence | Sample size 3 | Aucun trait (< 60%) |

---

## Déploiement

### Checklist pré-production

- [x] Migration SQL 025 créée
- [x] Script Python energy_profile_learning.py
- [x] Hook useEnergyProfile
- [x] Composant EnergyProfileCard
- [x] Intégration dans écran Profil
- [x] Documentation complète
- [ ] Test manuel avec données réelles (90J+)
- [ ] Exécution cron job test
- [ ] Validation traits découverts
- [ ] Performance check (< 2s per user)

### Cron Setup

```bash
# Exécution mensuelle (1er du mois à 2h)
0 2 1 * * cd /app/backend && python energy_profile_learning.py >> /var/log/pulse/energy_learning.log 2>&1
```

---

## Métriques de Succès

### KPIs à surveiller

| Métrique | Baseline | Cible (3 mois) |
|----------|----------|----------------|
| % users avec ≥1 trait découvert | 0% | 70% |
| Traits moyens par user | 0 | 2-3 |
| Confidence moyenne | - | 80%+ |
| Actions suivies (ex: ajuster sommeil) | - | 40% |
| NPS "utilité profil énergétique" | - | 8/10 |

### Feedback attendu

- ✅ "Je savais pas que 7h45 était mieux que 8h pour moi !"
- ✅ "Maintenant je comprends pourquoi le sport tard me fatigue"
- ✅ "C'est personnalisé, pas des conseils génériques"
- ✅ "J'ai ajusté mon timing de repas grâce à ça"

---

## Références

### Fichiers du projet
- `/database/migrations/025_energy_profile.sql` - Schema DB
- `/backend/energy_profile_learning.py` - ML backend
- `/mobile/src/hooks/useEnergyProfile.ts` - Hook React
- `/mobile/src/components/EnergyProfileCard.tsx` - Composant UI
- `/mobile/app/(tabs)/profil.tsx` - Intégration

### Études scientifiques
- [Personalized sleep duration (2018)](https://pubmed.ncbi.nlm.nih.gov/30098269/)
- [Individual variability in HRV (2020)](https://pubmed.ncbi.nlm.nih.gov/32454852/)
- [Protein requirements athletes (2017)](https://pubmed.ncbi.nlm.nih.gov/28642676/)

---

**Version** : 1.0  
**Date** : 2026-01-30  
**Auteur** : Pulse Engineering Team  
**Status** : ✅ Implémenté, prêt pour cron job test
