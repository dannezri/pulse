# 🧠 Système d'Apprentissage Adaptatif ML (PWA)

## 📋 Vue d'ensemble

Le **Personalized Weight Adjustment (PWA)** est un système de Machine Learning qui ajuste automatiquement les poids des facteurs (médicaments, conditions) en fonction du feedback utilisateur. Il transforme Pulse d'une calculatrice statique en une intelligence évolutive qui apprend le métabolisme unique de chaque utilisateur.

---

## 🎯 Objectif

Si le système prédit **12% d'énergie** alors que l'utilisateur ressent **30%**, l'algorithme doit réduire le poids des malus actifs (médicaments sédatifs, dépression) pour aligner les futures prédictions sur le ressenti réel.

---

## 🏗️ Architecture

### 1️⃣ Tables Supabase

#### **`user_feedback`** (Feedbacks utilisateurs)
```sql
CREATE TABLE user_feedback (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id),
  system_score FLOAT,           -- Score calculé (0-100)
  user_score INT,               -- Score ressenti (0-100)
  error FLOAT GENERATED AS (user_score - system_score),
  active_factors JSONB,         -- {"medications": [...], "conditions": [...]}
  processed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### **`personalized_weights`** (Poids personnalisés)
```sql
CREATE TABLE personalized_weights (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id),
  factor_type TEXT CHECK (factor_type IN ('medication', 'condition')),
  factor_code TEXT,             -- Code ATC ou ICD-11
  factor_name TEXT,
  weight_multiplier FLOAT DEFAULT 1.0 CHECK (weight_multiplier BETWEEN 0.5 AND 2.0),
  feedback_count INT DEFAULT 0,
  confidence_score FLOAT DEFAULT 0.0,
  adjustment_history JSONB DEFAULT '[]',
  last_adjustment TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### 2️⃣ Backend (`ml_optimizer.py`)

Le service `MLOptimizer` implémente une **Descente de Gradient Stochastique (SGD)** simplifiée :

```python
W_new = W_old + η × (error / 100) × φ
```

Où :
- **η** (Learning Rate) = 0.05 (pour éviter les changements brusques)
- **error** = `user_score - system_score` (en %)
- **φ** (Direction) = -1.0 pour les malus (plus l'utilisateur se sent mieux, plus on réduit le malus)
- **W_new** est contraint dans [0.5, 2.0]

**Exemple concret :**
- Utilisateur avec Mirtazapine (malus -25%)
- System score = 12%, User score = 30% → error = +18%
- W_old = 1.0, adjustment = 0.05 × (18/100) × (-1) = -0.009
- W_new = 1.0 - 0.009 = 0.991
- Après 5 feedbacks similaires, W ≈ 0.8
- Nouveau malus = -25% × 0.8 = -20% ✅

### 3️⃣ API Endpoint

**POST** `/api/v1/feedback`

**Body :**
```json
{
  "user_id": "c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd",
  "system_score": 12.5,
  "user_score": 30,
  "active_factors": {
    "medications": ["N06AB06", "N06AX11"],
    "conditions": ["6A70", "6A05"]
  }
}
```

**Response :**
```json
{
  "status": "ok",
  "error": 17.5,
  "adjustments_count": 2,
  "adjustments": [
    {
      "factor_type": "medication",
      "factor_code": "N06AX11",
      "old_weight": 1.0,
      "new_weight": 0.991,
      "adjustment": -0.009,
      "confidence": 0.4
    }
  ]
}
```

### 4️⃣ Intégration dans le moteur d'énergie

Le fichier `pulse_energy_decay_service.py` charge automatiquement les poids personnalisés :

```python
async def _load_personalized_weights(self, user_id: str):
    result = self.supabase.client.table('personalized_weights')\
        .select('factor_type, factor_code, weight_multiplier, confidence_score')\
        .eq('user_id', user_id)\
        .eq('is_active', True)\
        .execute()
    
    self.personalized_weights = {
        f"{w['factor_type']}:{w['factor_code']}": {
            'weight': w['weight_multiplier'],
            'confidence': w['confidence_score']
        }
        for w in result.data
    }
```

Les poids sont appliqués lors du calcul :

```python
# Pour les conditions
adjusted_decay_rate = impact['decay_rate'] * personalized_weight
adjusted_malus = impact['energy_malus'] * personalized_weight

# Pour les médicaments
total_impact *= personalized_weight
```

### 5️⃣ Composant Mobile (`FeedbackSlider.tsx`)

Le composant apparaît discrètement sur le Dashboard :

```tsx
<FeedbackSlider
  systemScore={12.5}
  activeMedications={["N06AB06", "N06AX11"]}
  activeConditions={["6A70", "6A05"]}
  onSubmit={async (userScore) => {
    await submitFeedback({
      user_id,
      system_score: 12.5,
      user_score: userScore,
      active_factors: { medications, conditions }
    });
  }}
  onDismiss={() => setShowFeedback(false)}
/>
```

---

## 🧮 Fonctionnement Mathématique

### Étape 1 : Collecte de l'erreur

L'utilisateur indique son ressenti via un slider (0-100%).

```
Error = User_Score - System_Score
```

### Étape 2 : Ajustement des poids

Pour chaque facteur actif (médicament ou condition), on applique la formule SGD :

```
adjustment = learning_rate × (error / 100) × direction
W_new = clamp(W_old + adjustment, 0.5, 2.0)
```

**Direction (φ) :**
- Facteurs négatifs (malus) : φ = -1.0
  - Si error > 0 (utilisateur se sent mieux), on RÉDUIT le malus
  - Si error < 0 (utilisateur se sent moins bien), on AUGMENTE le malus

### Étape 3 : Confiance progressive

La confiance augmente avec le nombre de feedbacks :

```
Confidence = min(1.0, feedback_count / 10)
```

Les ajustements ne sont appliqués qu'après **3 feedbacks minimum** pour éviter la sur-adaptation.

### Étape 4 : Historique et traçabilité

Chaque ajustement est stocké dans `adjustment_history` :

```json
[
  {
    "timestamp": "2026-01-31T20:00:00Z",
    "old_weight": 1.0,
    "new_weight": 0.991,
    "adjustment": -0.009,
    "feedback_count": 4
  }
]
```

---

## 📊 Exemple Complet

### Cas : Mirtazapine (N06AX11) chez Dan

**Données initiales :**
- Malus clinique : -25%
- Poids initial : 1.0
- Malus appliqué : -25% × 1.0 = -25%

**Feedback 1 :**
- System score : 12%, User score : 28% → error = +16%
- adjustment = 0.05 × (16/100) × (-1) = -0.008
- W_new = 1.0 - 0.008 = 0.992
- ⏸️ Pas appliqué (feedback_count = 1 < 3)

**Feedback 2 :**
- System score : 11%, User score : 25% → error = +14%
- adjustment = 0.05 × (14/100) × (-1) = -0.007
- W_new = 0.992 - 0.007 = 0.985
- ⏸️ Pas appliqué (feedback_count = 2 < 3)

**Feedback 3 :**
- System score : 13%, User score : 30% → error = +17%
- adjustment = 0.05 × (17/100) × (-1) = -0.0085
- W_new = 0.985 - 0.0085 = 0.9765
- ✅ Appliqué ! (feedback_count = 3)
- Nouveau malus : -25% × 0.9765 = -24.4%

**Après 10 feedbacks similaires :**
- W_new ≈ 0.82
- Nouveau malus : -25% × 0.82 = -20.5%
- **Le système a appris que Dan tolère mieux la Mirtazapine que la moyenne !**

---

## 🎯 Bénéfices

### 1. Précision Chirurgicale
Le système apprend la **tolérance individuelle** aux médicaments et l'impact réel des pathologies.

### 2. Confiance Utilisateur
L'application **écoute** l'utilisateur et s'adapte à lui, plutôt que d'imposer une moyenne statistique mondiale.

### 3. Engagement
Demander un feedback renforce l'**adhérence**. L'utilisateur se sent actif dans son parcours.

### 4. Traçabilité
L'historique permet de suivre l'évolution des poids et de détecter les dérives.

---

## 🔬 Validation

### Dashboard ML (à venir)

Endpoint pour consulter les ajustements :

**GET** `/api/v1/users/{user_id}/ml-stats`

```json
{
  "total_factors": 5,
  "factors": [
    {
      "factor_type": "medication",
      "factor_name": "Mirtazapine",
      "weight_multiplier": 0.82,
      "feedback_count": 12,
      "confidence_score": 1.0
    },
    {
      "factor_type": "condition",
      "factor_name": "Dépression",
      "weight_multiplier": 0.95,
      "feedback_count": 8,
      "confidence_score": 0.8
    }
  ]
}
```

---

## 🚀 Utilisation

### Backend

```bash
cd /Users/dannezri/Desktop/Pulse/backend
./restart_api_server.sh
```

Le service `MLOptimizer` est automatiquement initialisé.

### Mobile

Intégrer `FeedbackSlider` dans votre page d'énergie :

```tsx
import { FeedbackSlider } from '../src/components/FeedbackSlider';
import { useFeedback } from '../src/hooks/useFeedback';

const [showFeedback, setShowFeedback] = useState(false);
const { submitFeedback } = useFeedback();

// Afficher le slider si l'écart est > 15%
useEffect(() => {
  if (Math.abs(userScore - systemScore) > 15) {
    setShowFeedback(true);
  }
}, [userScore, systemScore]);

return (
  <>
    {/* Votre UI */}
    {showFeedback && (
      <FeedbackSlider
        systemScore={systemScore}
        activeMedications={medications}
        activeConditions={conditions}
        onSubmit={async (score) => {
          await submitFeedback({
            user_id,
            system_score: systemScore,
            user_score: score,
            active_factors: { medications, conditions }
          });
        }}
        onDismiss={() => setShowFeedback(false)}
      />
    )}
  </>
);
```

---

## 📝 TODO

- [ ] Dashboard web pour visualiser les ajustements ML
- [ ] Export des poids personnalisés (pour backup/migration)
- [ ] A/B testing : comparer prédictions avant/après ML
- [ ] Détection d'anomalies (poids qui dérivent trop)
- [ ] Recommandations automatiques basées sur les patterns

---

## 🔗 Fichiers clés

| Fichier | Description |
|---------|-------------|
| `backend/ml_optimizer.py` | Service d'optimisation ML (SGD) |
| `backend/api_server.py` | Endpoint `/api/v1/feedback` |
| `backend/pulse_energy_decay_service.py` | Application des poids personnalisés |
| `mobile/src/components/FeedbackSlider.tsx` | Composant de capture |
| `mobile/src/hooks/useFeedback.ts` | Hook de soumission |

---

**Pulse ne prétend pas savoir mieux que vous. Il apprend de vous pour devenir votre miroir parfait. 🪞🧠**
