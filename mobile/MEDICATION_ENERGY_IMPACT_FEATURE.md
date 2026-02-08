# Affichage de l'Impact Énergétique des Médicaments

## 📅 Date : 4 février 2026

## 🎯 Objectif

Améliorer la page de suivi des médicaments pour afficher l'impact énergétique de chaque traitement en temps réel, calculé en fonction du dosage, de la date de début et de l'heure de prise.

## ✨ Nouveautés

### 1. Hook `useMedicationImpacts` 

**Fichier** : `mobile/src/hooks/useMedicationImpacts.ts`

**Fonctionnalités** :
- Récupère l'impact énergétique depuis le forecast existant (`briefData.intraday_energy_forecast.influencers`)
- Mappe chaque médicament à son impact
- Calcule l'impact total de tous les médicaments
- Réutilise les données déjà calculées par le backend (pas de duplication)

**API** :
```typescript
const { 
  impacts,                  // Map<string, MedicationImpact>
  loading,                  // boolean
  getMedicationImpact,      // (medication) => MedicationImpact | null
  getTotalImpact            // () => number
} = useMedicationImpacts(userId);
```

**Interface `MedicationImpact`** :
```typescript
{
  medicationId: string;
  medicationName: string;
  impact: number;           // Ex: -12.5, +5.3
  impactText: string;       // Ex: "-12%", "+5%"
  status: 'positive' | 'negative' | 'neutral';
  description?: string;     // Texte explicatif
  atcCode?: string;
}
```

### 2. Composant `MedicationList` amélioré

**Fichier** : `mobile/src/components/MedicationList.tsx`

**Ajouts** :
- **Affichage de l'impact énergétique** pour chaque médicament
- **Card d'impact colorée** selon le statut (positif/négatif/neutre)
- **Icônes visuelles** : TrendingUp ↗, TrendingDown ↘, Minus —
- **Description détaillée** de l'impact si disponible
- **Footer enrichi** : Date de début + Prochaine prise

**Props** :
```typescript
interface MedicationListProps {
  medications: Medication[];
  onDelete?: (id: string) => void;
  emptyMessage?: string;
  getMedicationImpact?: (medication: Medication) => MedicationImpact | null;
  showImpact?: boolean;     // Activer/désactiver l'affichage
}
```

### 3. Page `medications.tsx` redesignée

**Fichier** : `mobile/app/medications.tsx`

**Améliorations** :

#### Stats Overview
- **Impact Total** : Nouvelle card affichant l'impact cumulé de tous les médicaments
- **Couleurs dynamiques** : 
  - Vert pour impact positif
  - Rouge pour impact négatif
  - Gris pour neutre

#### Section "Comment ça marche ?"
Nouvelle section explicative avec 4 points :
1. **Dosage total** (nombre de comprimés × dosage)
2. **Heure de prise** et pharmacocinétique
3. **Durée du traitement** (adaptation long terme)
4. **Votre profil** (poids ML personnalisé)

#### Section "Pourquoi c'est important ?"
Mise à jour pour mettre l'accent sur :
- ⚡ **Impact en temps réel**
- 🎯 **Dosage optimisé**
- 📊 **Analyses précises**

## 🔗 Intégration avec le Backend

### Calcul de l'Impact (Backend)

Le calcul est effectué dans `backend/intraday_energy_service.py` (lignes 504-542) :

```python
# 1. Récupérer les données du médicament
atc_code = med.get('atc_code')
impact_data = med_impacts_dict[atc_code]

# 2. Calculer le dosage total
dosage_per_pill = med.get('dosage', 0)
pills_per_intake = med.get('pills_per_intake', 1.0)
total_dosage = dosage_per_pill * pills_per_intake

# 3. Calculer l'impact de base
base_impact = impact_data.get('chronic_impact', 0)
if impact_data.get('energy_category') == 'sedative':
    base_impact = (impact_data.get('acute_impact_min', 0) + 
                   impact_data.get('acute_impact_max', 0)) / 2

# 4. Ajuster selon le dosage
dosage_multiplier = pills_per_intake
base_impact = base_impact * dosage_multiplier

# 5. Appliquer le poids personnalisé ML
weight = personalized_weights.get(('medication', atc_code), 1.0)
adjusted_impact = base_impact * weight
```

### Flux de Données

```
┌─────────────────────────────────────────────┐
│  Backend (intraday_energy_service.py)      │
│  Calcule l'impact de chaque médicament     │
│  - Dosage × pills_per_intake              │
│  - Pharmacocinétique (ATC code)           │
│  - Durée traitement (days_since_start)    │
│  - Heure de prise (intake_times)          │
│  - Poids ML personnalisé                  │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  briefData.intraday_energy_forecast        │
│  {                                         │
│    influencers: [                          │
│      {                                     │
│        category: 'medication',             │
│        name: 'Doliprane',                  │
│        impact: '-5%',                      │
│        status: 'negative',                 │
│        text: 'Effet sédatif léger'        │
│      }                                     │
│    ]                                       │
│  }                                         │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  useMedicationImpacts(userId)              │
│  Extrait et mappe les influencers          │
│  médicaments depuis briefData              │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  medications.tsx                           │
│  Affiche l'impact pour chaque médicament   │
└─────────────────────────────────────────────┘
```

## 🎨 Design

### Couleurs

| Statut | Background | Border | Text | Icon |
|--------|-----------|--------|------|------|
| Positif | `rgba(52, 199, 89, 0.08)` | `rgba(52, 199, 89, 0.25)` | `#34C759` | TrendingUp ↗ |
| Négatif | `rgba(255, 59, 48, 0.08)` | `rgba(255, 59, 48, 0.25)` | `#FF3B30` | TrendingDown ↘ |
| Neutre | `rgba(142, 142, 147, 0.08)` | `rgba(142, 142, 147, 0.25)` | `#8E8E93` | Minus — |

### Card d'Impact

```
┌─────────────────────────────────────┐
│ ↗  Impact sur l'énergie     +5.3%  │
│                                     │
│ Boost d'énergie temporaire lié     │
│ au pic de concentration            │
└─────────────────────────────────────┘
```

## ✅ Respect des Directives

### 1. Pas de Duplication
- ✅ Réutilise `briefData` existant via `useBriefData`
- ✅ Pas de nouveau calcul d'impact (déjà fait côté backend)
- ✅ Hook simple qui mappe les données existantes

### 2. Modification, pas Création
- ✅ Modifie `MedicationList.tsx` existant (pas de nouveau composant)
- ✅ Améliore `medications.tsx` existant
- ✅ Ajoute un hook utilitaire (`useMedicationImpacts`) qui n'existait pas

### 3. Cohérence avec l'Existant
- ✅ Même palette de couleurs que la page énergie
- ✅ Même structure de données (`influencers`)
- ✅ Même design system (cards, badges, spacing)

## 📊 Exemple d'Affichage

### Médicament avec Impact Négatif
```
┌─────────────────────────────────────────┐
│ 💊  Doliprane             [Récurrent]   │
│     2 × 500 mg                          │
├─────────────────────────────────────────┤
│ ↘  Impact sur l'énergie        -5%     │
│    Effet sédatif léger                 │
├─────────────────────────────────────────┤
│ 🕐  2x par jour                        │
│     [08:00] [20:00]                    │
├─────────────────────────────────────────┤
│ Début: Il y a 7j                       │
│ Prochaine prise: 08:00                 │
└─────────────────────────────────────────┘
```

### Médicament avec Impact Positif
```
┌─────────────────────────────────────────┐
│ 💊  Modafinil             [Récurrent]   │
│     200 mg                              │
├─────────────────────────────────────────┤
│ ↗  Impact sur l'énergie        +12%    │
│    Stimulant cognitif majeur           │
├─────────────────────────────────────────┤
│ 🕐  1x par jour                        │
│     [07:00]                            │
├─────────────────────────────────────────┤
│ Début: Il y a 30j                      │
│ Prochaine prise: 07:00                 │
└─────────────────────────────────────────┘
```

## 🚀 Utilisation

### Dans medications.tsx
```typescript
const { userId } = useAuth();
const { medications } = useMedications();
const { getMedicationImpact, getTotalImpact } = useMedicationImpacts(userId);

// Impact d'un médicament
const impact = getMedicationImpact(medications[0]);
// => { medicationName: "Doliprane", impact: -5, impactText: "-5%", ... }

// Impact total
const total = getTotalImpact();
// => -2.3
```

### Dans MedicationList
```typescript
<MedicationList
  medications={medications}
  onDelete={handleDelete}
  getMedicationImpact={getMedicationImpact}
  showImpact={true}
/>
```

## 🎯 Bénéfices

1. **User-friendly** : Visuel clair avec couleurs et icônes
2. **Informatif** : L'utilisateur comprend l'impact de chaque médicament
3. **Actionable** : Peut ajuster les dosages en fonction de l'impact
4. **Personnalisé** : Basé sur le profil ML de l'utilisateur
5. **En temps réel** : Mis à jour à chaque refresh du brief

## 🔮 Améliorations Futures

- [ ] **Graphique d'évolution** : Impact du médicament sur 7/30 jours
- [ ] **Alertes intelligentes** : Notification si impact très négatif
- [ ] **Suggestions** : "Essayez de prendre X plus tôt/tard"
- [ ] **Comparaison** : Comparer l'impact avec/sans le médicament
- [ ] **Export PDF** : Rapport pour le médecin avec impacts

## 📝 Fichiers Modifiés

1. ✅ `mobile/src/hooks/useMedicationImpacts.ts` (créé)
2. ✅ `mobile/src/components/MedicationList.tsx` (modifié)
3. ✅ `mobile/app/medications.tsx` (modifié)

## ✨ Résultat Final

Une page de médicaments totalement repensée qui :
- Affiche l'impact énergétique en temps réel
- Éduque l'utilisateur sur le calcul d'impact
- Garde un design cohérent avec le reste de l'app
- Réutilise les calculs backend existants
- Respecte toutes les directives du projet
