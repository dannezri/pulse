# Profil Énergétique Personnel - Implémentation Complète

## 📋 Résumé

Système de **machine learning** qui analyse l'historique long terme (60-90 jours) pour identifier les patterns énergétiques uniques de chaque utilisateur.

**Objectif** : Transformer des insights génériques en recommendations **personnelles** basées sur les données réelles de l'utilisateur.

**Format** : "**Tu** récupères mieux avec 7h45 de sommeil" vs "Le sommeil est important"

---

## ✅ Fichiers Créés

### 1. Migration SQL - `025_energy_profile.sql`
**Localisation** : `/database/migrations/025_energy_profile.sql`

**Table créée** : `user_energy_profile`

```sql
CREATE TABLE user_energy_profile (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    trait_type TEXT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    value_numeric DECIMAL,
    value_text TEXT,
    confidence DECIMAL CHECK (confidence >= 0 AND confidence <= 1),
    support_data JSONB,
    discovered_at TIMESTAMP,
    last_validated TIMESTAMP,
    data_points_count INTEGER,
    is_active BOOLEAN,
    UNIQUE(user_id, trait_type)
);
```

**RPC Function** : `get_user_energy_profile(p_user_id UUID)`

**Policies RLS** :
- Users can view own profile
- System (service_role) can insert/update

---

### 2. Backend ML - `energy_profile_learning.py`
**Localisation** : `/backend/energy_profile_learning.py`

**Responsabilité** :
- Analyse historique 90 jours
- Détecte patterns personnels (3 types actuellement)
- Calcule score de confiance
- Stocke dans `user_energy_profile`

**Traits détectés** :
1. **Sommeil optimal** (`optimal_sleep_duration`)
   - Corrèle durée sommeil × recovery
   - Ex: "Tu récupères mieux avec 7h45"

2. **Impact sport tardif** (`late_exercise_impact`)
   - Corrèle sport >19h × HRV lendemain
   - Ex: "Sport tardif réduit HRV de 12%"

3. **Apport protéique** (`protein_requirement`)
   - Corrèle protéines × recovery
   - Ex: "Protéines optimales: 80g+"

**Fonctions clés** :
```python
def analyze_optimal_sleep_duration(user_id: str) -> Optional[Dict]
def analyze_late_exercise_impact(user_id: str) -> Optional[Dict]
def analyze_protein_requirement(user_id: str) -> Optional[Dict]
def learn_energy_profile(user_id: str) -> Dict
def learn_all_users_profiles() -> List[Dict]
```

**Exécution** :
```bash
# Tous les users
python backend/energy_profile_learning.py

# User spécifique
python backend/energy_profile_learning.py <user_id>
```

**Cron job recommandé** :
```bash
# Mensuel (1er à 2h)
0 2 1 * * python backend/energy_profile_learning.py
```

---

### 3. Hook React - `useEnergyProfile.ts`
**Localisation** : `/mobile/src/hooks/useEnergyProfile.ts`

**Responsabilité** :
- Fetch profil énergétique via RPC
- Groupe traits par catégorie
- Filtre traits haute confiance (≥80%)

**Interface** :
```typescript
export interface EnergyProfileTrait {
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
    [key: string]: any;
  };
  discovered_at: string;
  last_validated: string;
  data_points_count: number;
}

export interface EnergyProfile {
  traits: EnergyProfileTrait[];
  hasData: boolean;
  traitsByCategory: Record<TraitCategory, EnergyProfileTrait[]>;
  highConfidenceTraits: EnergyProfileTrait[]; // >= 80%
}
```

**Usage** :
```typescript
const { data: energyProfile, isLoading } = useEnergyProfile(userId);
```

---

### 4. Composant UI - `EnergyProfileCard.tsx`
**Localisation** : `/mobile/src/components/EnergyProfileCard.tsx`

**Responsabilité** :
- Affiche profil énergétique groupé par catégorie
- Badge de confiance coloré par trait
- État vide si < 30 jours d'historique

**Catégories** :
- 💤 Sommeil
- 🍎 Nutrition
- 🏃 Exercice
- ❤️ Récupération
- 🧠 Stress
- ⏰ Timing

**Rendu visuel** :
```
┌─────────────────────────────────────────┐
│ ✨ Ton Profil Énergétique               │
│ 3 traits personnels découverts          │
│                                          │
│ ℹ️ 2 traits haute confiance             │
│ Ces patterns sont très fiables.         │
│                                          │
│ 💤 Sommeil                               │
│ ┌─────────────────────────────┐         │
│ │ Sommeil optimal: 7h45  [85%]│         │
│ │ Tu récupères mieux avec      │         │
│ │ 7h45 de sommeil...           │         │
│ │ 25 points • +14%             │         │
│ └─────────────────────────────┘         │
│                                          │
│ 🏃 Exercice                              │
│ ┌─────────────────────────────┐         │
│ │ Sport tardif réduit HRV[78%]│         │
│ │ Sport après 19h réduit...    │         │
│ │ 18 points • -12%             │         │
│ └─────────────────────────────┘         │
└─────────────────────────────────────────┘
```

**Couleurs de confiance** :
- 85-100% : Vert (#00FF41) - Très fiable
- 75-84% : Cyan (#00C7BE) - Fiable
- 65-74% : Orange (#FF9500) - Modéré
- 60-64% : Gris (#8E8E93) - En cours

---

### 5. Documentation - `energy-profile-learning.md`
**Localisation** : `/mobile/docs/energy-profile-learning.md`

**Contenu** (500+ lignes) :
- Vue d'ensemble concept
- Format d'affichage
- Description détaillée de chaque trait
- Algorithmes ML expliqués
- Architecture technique complète
- Niveaux de confidence
- Flow de données
- États d'affichage
- Cas limites
- Évolutions futures (Phase 2-4)
- Tests de validation
- Déploiement

---

## 🔧 Fichiers Modifiés

### Écran Profil - `profil.tsx`
**Localisation** : `/mobile/app/(tabs)/profil.tsx`

**Modifications** :

#### Imports ajoutés
```typescript
import { useEnergyProfile } from '@/hooks/useEnergyProfile';
import { EnergyProfileCard } from '@/components/EnergyProfileCard';
```

#### Logique ajoutée
```typescript
// Profil énergétique personnel
const { data: energyProfile, isLoading: loadingEnergyProfile } = 
  useEnergyProfile(userProfile?.id || null);
```

#### Affichage ajouté
```typescript
{/* Après Wearable, avant Conditions de santé */}
{!loadingEnergyProfile && energyProfile && (
  <EnergyProfileCard profile={energyProfile} />
)}
```

**Position dans le layout** :
1. Informations utilisateur
2. Statut Wearable
3. **🆕 Profil Énergétique Personnel**
4. Conditions de santé
5. Baselines personnelles
6. Médicaments
7. Actions (logout, etc.)

---

## 🎯 Traits Détectés

### 1. Sommeil optimal

**Données analysées** :
- 90 jours d'historique
- `biometrics.sleep_duration` × `daily_state.recovery`
- Minimum 15 points

**Algorithme** :
- Groupe par tranches 30 min (7h, 7.5h, 8h...)
- Trouve durée avec meilleure recovery
- Calcule amélioration vs autres durées

**Confidence** :
```
0.60 + (sample_size / 50) × 0.20 + (improvement / 100)
Max: 0.95
```

**Exemple** :
```
Titre: "Sommeil optimal: 7h45"
Description: "Tu récupères mieux avec 7h45 de sommeil 
(82% vs 68% autres durées)"
Value: 7.75 heures
Confidence: 85%
Support: 25 points, +14%
```

---

### 2. Sport tardif

**Données analysées** :
- 90 jours d'historique
- `biometrics.active_calories` (>300, après 19h) × `biometrics.hrv` (lendemain)
- Minimum 5 jours sport tardif

**Algorithme** :
- Identifie jours sport >19h
- Compare HRV lendemain vs jours normaux
- Test statistique (t-test)

**Confidence** :
```
0.65 + (sample_size / 30) × 0.20
Si p_value > 0.05: × 0.7
```

**Exemple** :
```
Titre: "Sport tardif réduit HRV"
Description: "Sport après 19h réduit ta HRV de 12% 
le lendemain (48ms vs 54ms)"
Value: -12%
Confidence: 78%
Support: 18 jours, p=0.03
```

---

### 3. Protéines

**Données analysées** :
- 90 jours d'historique
- `food_logs.total_protein` × `daily_state.recovery` (lendemain)
- Minimum 15 points

**Algorithme** :
- Groupe par tranches 20g (60g, 80g, 100g...)
- Trouve apport optimal (≥60g minimum)
- Calcule amélioration vs autres apports

**Confidence** :
```
0.60 + (sample_size / 40) × 0.20 + (improvement / 80)
Max: 0.90
```

**Exemple** :
```
Titre: "Protéines optimales: 80g+"
Description: "Ta récupération est meilleure avec 
au moins 80g/jour (77% vs 67%)"
Value: 80g
Confidence: 82%
Support: 20 points, +11%
```

---

## 📊 Architecture Technique

### Flow de données

```
┌─────────────────────────────────────────┐
│ Supabase (90 jours d'historique)        │
├─────────────────────────────────────────┤
│ • biometrics (sommeil, HRV, activité)   │
│ • daily_state (recovery, energy)        │
│ • food_logs (protéines, glucides)       │
│ • user_baselines (HRV baseline)         │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ Backend Python (Cron mensuel)           │
│ energy_profile_learning.py              │
├─────────────────────────────────────────┤
│ 1. Fetch historique 90J                 │
│ 2. Corrélations statistiques            │
│    - Sommeil × Recovery                 │
│    - Sport tardif × HRV                 │
│    - Protéines × Recovery               │
│ 3. Calcul confidence (sample, impact)   │
│ 4. INSERT INTO user_energy_profile      │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ Mobile App (React Native)               │
│ useEnergyProfile()                      │
├─────────────────────────────────────────┤
│ 1. RPC get_user_energy_profile()        │
│ 2. Groupe par catégorie                 │
│ 3. Filtre haute confiance (≥80%)        │
│ 4. <EnergyProfileCard> dans Profil      │
└─────────────────────────────────────────┘
```

---

## 🔬 Niveaux de Confidence

| Plage | Label | Couleur | Signification |
|-------|-------|---------|---------------|
| 85-100% | Très fiable | 🟢 Vert | Pattern validé, nombreuses données |
| 75-84% | Fiable | 🔵 Cyan | Pattern cohérent |
| 65-74% | Modéré | 🟠 Orange | Pattern suggéré |
| 60-64% | En cours | ⚪ Gris | Besoin plus de données |
| <60% | ❌ Non stocké | - | Pas assez fiable |

**Seuil minimum** : 60% pour stocker un trait dans la DB

---

## 🚀 Déploiement

### Checklist pré-production

- [x] Migration SQL 025 créée
- [x] Backend Python energy_profile_learning.py
- [x] Hook useEnergyProfile
- [x] Composant EnergyProfileCard
- [x] Intégration écran Profil
- [x] Documentation complète
- [x] Vérification linter (0 erreur)
- [ ] Exécuter migration SQL sur prod
- [ ] Test cron job sur staging
- [ ] Validation avec données réelles (90J+)
- [ ] Performance check (<2s par user)
- [ ] Setup cron production

### Commandes de déploiement

```bash
# 1. Migration DB
psql -h <supabase_host> -U postgres -d postgres -f database/migrations/025_energy_profile.sql

# 2. Test script Python (staging)
python backend/energy_profile_learning.py <test_user_id>

# 3. Cron setup (production)
# Ajouter au crontab:
0 2 1 * * cd /app/backend && python energy_profile_learning.py >> /var/log/pulse/energy_learning.log 2>&1
```

---

## 📈 Métriques de Succès

### KPIs à surveiller (3 mois post-deploy)

| Métrique | Baseline | Cible |
|----------|----------|-------|
| % users avec ≥1 trait | 0% | 70% |
| Traits moyens par user | 0 | 2-3 |
| Confidence moyenne | - | 80%+ |
| Actions suivies | - | 40% |
| NPS "profil énergétique" | - | 8/10 |
| Temps exécution ML | - | <2s/user |

### Feedback attendu

- ✅ "Je savais pas que 7h45 était optimal pour moi !"
- ✅ "C'est personnalisé, pas des conseils génériques"
- ✅ "J'ai ajusté mon timing sport grâce à ça"
- ✅ "Le score de confiance me rassure sur la fiabilité"

---

## 🔮 Évolutions Futures

### Phase 2 : Plus de traits (Q2 2026)

**Nouveaux traits à implémenter** :
- ☕ **Caféine cutoff** : "Pas de café après 15h pour toi"
- 🍷 **Sensibilité alcool** : "1 verre réduit ta HRV de 8%"
- ⏰ **Meal timing** : "Meilleure fenêtre: 12h-19h30"
- 🌅 **Chronotype** : "Tu es une personne du matin"
- 💧 **Hydratation** : "Vise 2.5L+ les jours sport"
- 🌡️ **Sensibilité température** : "Meilleure récup à 18°C"

**Implémentation** :
- Nouvelles fonctions dans energy_profile_learning.py
- Tracking additionnel (caféine, alcool)

---

### Phase 3 : Interactions complexes (Q3 2026)

**Multi-facteurs** :
- "Sommeil 7h45 + protéines 80g → récup +22%"
- "Alcool + sport tardif → impact ×2 sur HRV"

**Contexte** :
- "En voyage: besoin 8h+ sommeil"
- "Stress élevé: réduis sport intense"

**Implémentation** :
- Modèles ML plus sophistiqués (régression multiple)
- Intégration contexte (voyage, stress, etc.)

---

### Phase 4 : Prédictif (Q4 2026)

**Recommandations proactives** :
- "Demain sport prévu → mange 100g+ protéines aujourd'hui"
- "Tu as mal dormi → journée légère recommandée"

**Optimisation** :
- "Décale sport de 19h à 17h pour +10% HRV"
- "Si tu manges avant 19h30, sommeil +8% qualité"

**Notifications push** :
- "Rappel: couche-toi avant 23h (ton optimal)"
- "Tu n'as pas assez de protéines aujourd'hui"

---

## 🧪 Tests de Validation

### Scénarios de test clés

| # | Scénario | Input | Output attendu |
|---|----------|-------|----------------|
| 1 | Sommeil optimal | 7h45→82%, 8h→68% (25pts) | Trait créé, conf 85% |
| 2 | Sport tardif | 18J >19h, HRV -12% | Trait créé, conf 78% |
| 3 | Protéines | 80g→77%, <80g→67% (20pts) | Trait créé, conf 82% |
| 4 | Données insuffisantes | 8 points seulement | Aucun trait (<15 min) |
| 5 | Pattern faible | Amélioration +2% | Aucun trait (<5%) |
| 6 | Faible confidence | Sample 3, p=0.15 | Aucun trait (<60%) |
| 7 | Nouveau user | <30 jours historique | État vide UI |
| 8 | User actif | 90J données, 3 patterns | 3 traits affichés |

---

## 📚 Références

### Fichiers du projet
- `/database/migrations/025_energy_profile.sql` - Schema DB
- `/backend/energy_profile_learning.py` - ML backend
- `/mobile/src/hooks/useEnergyProfile.ts` - Hook React
- `/mobile/src/components/EnergyProfileCard.tsx` - Composant UI
- `/mobile/app/(tabs)/profil.tsx` - Intégration
- `/mobile/docs/energy-profile-learning.md` - Documentation technique

### Dépendances Python
```
numpy>=1.21.0
scipy>=1.7.0
supabase>=0.7.0
```

### Études scientifiques
- [Personalized sleep duration (2018)](https://pubmed.ncbi.nlm.nih.gov/30098269/)
- [Individual HRV variability (2020)](https://pubmed.ncbi.nlm.nih.gov/32454852/)
- [Protein requirements athletes (2017)](https://pubmed.ncbi.nlm.nih.gov/28642676/)

---

**Version** : 1.0  
**Date d'implémentation** : 2026-01-30  
**Auteur** : Pulse Engineering Team  
**Status** : ✅ Implémenté, prêt pour déploiement production
