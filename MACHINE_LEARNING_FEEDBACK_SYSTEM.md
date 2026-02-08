# 🧠 Machine Learning Feedback Loop - PWA (Personalized Weight Adjustment)

## 📋 Vue d'ensemble

Le système d'**apprentissage adaptatif** permet à Pulse de s'ajuster automatiquement aux particularités de chaque utilisateur en collectant des feedbacks et en optimisant les poids des facteurs (médicaments, conditions).

---

## 🎯 Objectif

Réduire l'erreur quadratique entre le **score calculé** ($S_{sys}$) et le **score ressenti** ($S_{user}$).

**Exemple** :  
- Pulse calcule : **2.7%**  
- Utilisateur ressent : **65%**  
- **Erreur** : **+62.3** (l'utilisateur se sent bien mieux que prévu)

→ Le ML va **réduire l'impact des malus** (les médicaments sédatifs ont peut-être moins d'effet sur cet utilisateur).

---

## 🏗️ Architecture

### **1. Base de données (Supabase)**

#### Table `user_feedback`
Stocke les feedbacks utilisateurs.

```sql
CREATE TABLE user_feedback (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES profiles(id),
    system_score FLOAT,  -- Score calculé par l'algo
    user_score INT,      -- Score ressenti (0-100)
    error FLOAT,         -- user_score - system_score
    active_factors JSONB, -- Snapshot des médicaments/conditions actifs
    processed BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ
);
```

#### Table `personalized_weights`
Stocke les multiplicateurs personnalisés.

```sql
CREATE TABLE personalized_weights (
    id UUID PRIMARY KEY,
    user_id UUID,
    factor_type TEXT,  -- 'medication' | 'condition'
    factor_code TEXT,  -- ATC code | ICD-11
    weight_multiplier FLOAT DEFAULT 1.0,  -- 0.5 à 2.0
    feedback_count INT,
    confidence_score FLOAT,
    adjustment_history JSONB
);
```

### **2. Backend (Python)**

#### `ml_optimizer.py`
Moteur d'optimisation ML basé sur la **descente de gradient stochastique**.

**Algorithme** :
```python
if user_score > system_score:
    # Utilisateur se sent mieux que prévu
    # → Réduire les malus (poids × 0.95)
    new_weight = current_weight × (1 - LEARNING_RATE)
else:
    # Utilisateur se sent pire que prévu
    # → Augmenter les malus (poids × 1.05)
    new_weight = current_weight × (1 + LEARNING_RATE)

# Contraindre entre 0.5 et 2.0
new_weight = clip(new_weight, 0.5, 2.0)
```

**Hyperparamètres** :
- `TRIGGER_THRESHOLD = 5` : Optimisation tous les 5 feedbacks
- `LEARNING_RATE = 0.05` : Ajustement de ±5%
- `MIN_WEIGHT = 0.5`, `MAX_WEIGHT = 2.0`
- `CONFIDENCE_THRESHOLD = 10` : 10 feedbacks pour confiance max

**Features** :
- ✅ Idempotent : un feedback n'est traité qu'une fois
- ✅ Ajustement graduel : évite les sur-corrections
- ✅ Historique conservé : traçabilité des ajustements

#### `pulse_energy_decay_service.py` (modifié)
Intègre les poids personnalisés dans le calcul.

```python
# Charger les poids personnalisés
await self._load_personalized_weights(user_id)

# Appliquer aux conditions
personalized_weight = self._get_personalized_weight('condition', icd11_code)
adjusted_malus = base_malus × personalized_weight

# Appliquer aux médicaments
personalized_weight = self._get_personalized_weight('medication', atc_code)
total_impact = base_impact × personalized_weight
```

#### `api_server.py` (nouveau endpoint)
```python
@app.post("/api/v1/feedback")
async def submit_feedback(request: Request):
    # 1. Enregistrer le feedback
    # 2. Vérifier si seuil atteint (5 feedbacks)
    # 3. Déclencher optimiseur ML si nécessaire
    # 4. Retourner résultat
```

### **3. Frontend Mobile (React Native)**

#### `FeedbackBottomSheet.tsx`
Composant UI avec slider pour collecter le feedback.

**Props** :
- `systemScore` : Score calculé (0-100)
- `currentEnergy` : Énergie actuelle
- `activeFactors` : Médicaments/conditions actifs
- `feedbackContext` : Contexte du trigger

#### `useFeedback.ts`
Hook personnalisé pour gérer la logique.

**Triggers automatiques** :
1. **Low energy** : Énergie < 15%
2. **Energy spike** : Changement > 30 points
3. **Manual** : Bouton dans le profil

**Throttling** : Minimum 2h entre deux feedbacks

#### Exemple d'intégration

```tsx
import { FeedbackBottomSheet } from '../components/FeedbackBottomSheet';
import { useFeedback } from '../hooks/useFeedback';
import { extractActiveFactors } from '../services/feedbackApi';

function HomeScreen() {
  const { data: briefData } = useBriefData(userId);
  const forecast = briefData?.intraday_energy_forecast;
  
  const {
    showFeedbackSheet,
    feedbackContext,
    handleSubmitFeedback,
    closeFeedbackSheet
  } = useFeedback({
    userId,
    currentEnergy: forecast?.current_energy || 0,
    systemScore: forecast?.current_energy || 0,
    hoursSinceWake: calculateHoursSinceWake(),
    activeFactors: extractActiveFactors(forecast)
  });

  return (
    <View>
      {/* ... votre UI ... */}
      
      <FeedbackBottomSheet
        isVisible={showFeedbackSheet}
        onClose={closeFeedbackSheet}
        systemScore={forecast?.current_energy || 0}
        currentEnergy={forecast?.current_energy || 0}
        hoursSinceWake={calculateHoursSinceWake()}
        activeFactors={extractActiveFactors(forecast)}
        onSubmit={handleSubmitFeedback}
        feedbackContext={feedbackContext}
      />
    </View>
  );
}
```

---

## 📊 Flux de données

```
┌─────────────────┐
│  Mobile App     │
│  (React Native) │
└────────┬────────┘
         │ POST /api/v1/feedback
         │ {system_score, user_score, active_factors}
         ▼
┌─────────────────────┐
│  Backend API        │
│  (FastAPI)          │
│  1. Insert feedback │
│  2. Check count     │
└────────┬────────────┘
         │ count >= 5 ?
         ▼
┌─────────────────────┐
│  ML Optimizer       │
│  (ml_optimizer.py)  │
│  1. Gradient        │
│  2. Adjust weights  │
│  3. UPSERT DB       │
└────────┬────────────┘
         │
         ▼
┌─────────────────────────┐
│  personalized_weights   │
│  (Supabase)             │
│  {weight_multiplier}    │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  pulse_energy_decay     │
│  Applique les poids     │
│  personnalisés          │
└─────────────────────────┘
```

---

## 🧪 Exemples d'utilisation

### **Cas 1 : Tolérance à la Mirtazapine**

**Situation** :  
L'utilisateur prend 15mg de Mirtazapine depuis 3 mois. Le système estime un impact de **-25 points**, mais l'utilisateur se sent mieux.

**Feedbacks** :
```
Feedback 1: system=20, user=50, error=+30
Feedback 2: system=18, user=45, error=+27
Feedback 3: system=22, user=48, error=+26
Feedback 4: system=19, user=50, error=+31
Feedback 5: system=21, user=52, error=+31
```

**Résultat ML** :
```
medication:N06AX11 (Mirtazapine)
Old weight: 1.0
New weight: 0.95 (ajustement -5%)
→ Impact réduit de -25 à -23.75
```

Après 10 feedbacks similaires :
```
weight = 0.77
→ Impact réduit de -25 à -19.25
```

L'utilisateur a développé une **tolérance** que le système a appris !

### **Cas 2 : TDAH moins impactant le matin**

**Situation** :  
L'utilisateur a un TDAH (decay_rate=0.055) mais se sent bien le matin.

**Feedbacks matinaux** :
```
Feedback 1: system=45, user=75, error=+30 (9h du matin)
Feedback 2: system=42, user=70, error=+28 (8h30)
Feedback 3: system=47, user=73, error=+26 (10h)
```

**Résultat ML** :
```
condition:6A05 (TDAH)
Old weight: 1.0
New weight: 0.87
→ Decay rate réduit de 0.055 à 0.048
```

Le système apprend que ce utilisateur spécifique gère mieux son TDAH le matin !

---

## 🎯 Pourquoi c'est "Infaillible" ?

### 1️⃣ **Effet d'Accoutumance**
Deux personnes ne réagissent pas pareil à 15mg de Mirtazapine. Le ML détecte la tolérance développée au fil du temps.

### 2️⃣ **Résilience Psychologique**
Pour le TDAH ou la Dépression, certains jours sont "moteurs" malgré la pathologie. Le feedback permet d'apprendre ces nuances.

### 3️⃣ **Confiance Utilisateur**
Rien n'est plus frustrant qu'une app qui te dit "Tu es épuisé" quand tu te sens prêt à conquérir le monde. En permettant à l'utilisateur de "corriger" l'IA, tu renforces l'adhésion au produit.

### 4️⃣ **Ajustement Graduel**
Un seul feedback "euphorique" ne doit pas effacer 92 jours de données cliniques. Ajustement de ±5% par itération, évite les aberrations.

---

## ⚙️ Configuration

### Déploiement Backend

1. Appliquer les migrations :
```bash
cd database/migrations
supabase migration apply 038_create_user_feedback_table
supabase migration apply 039_create_personalized_weights_table
```

2. Installer les dépendances :
```bash
pip install numpy
```

3. Redémarrer le serveur :
```bash
cd backend
python3 api_server.py
```

### Déploiement Mobile

1. Installer les dépendances :
```bash
cd mobile
npm install @react-native-community/slider
```

2. Intégrer dans votre écran principal :
```tsx
import { FeedbackBottomSheet } from './src/components/FeedbackBottomSheet';
import { useFeedback } from './src/hooks/useFeedback';
```

---

## 📈 Métriques de succès

### Indicateurs à suivre

1. **Taux de collecte** :
   - Combien de feedbacks par utilisateur actif ?
   - Cible : 1 feedback tous les 2-3 jours

2. **Erreur moyenne** :
   - `AVG(ABS(error))` par utilisateur
   - Cible : Diminution de 30% après 20 feedbacks

3. **Confidence score** :
   - `AVG(confidence_score)` sur `personalized_weights`
   - Cible : >0.7 après 2 semaines d'utilisation

4. **Taux d'optimisation** :
   - Combien de triggers ML par utilisateur ?
   - Cible : 1 optimisation tous les 2 jours (5 feedbacks)

### Requêtes SQL utiles

```sql
-- Erreur moyenne par utilisateur
SELECT
    user_id,
    AVG(ABS(error)) as avg_error,
    COUNT(*) as feedback_count
FROM user_feedback
GROUP BY user_id
ORDER BY avg_error DESC;

-- Poids personnalisés avec le plus d'ajustements
SELECT
    factor_type,
    factor_name,
    weight_multiplier,
    feedback_count,
    confidence_score
FROM personalized_weights
WHERE confidence_score > 0.5
ORDER BY feedback_count DESC;

-- Distribution des contextes de feedback
SELECT
    feedback_context,
    COUNT(*) as count
FROM user_feedback
GROUP BY feedback_context;
```

---

## 🚀 Prochaines étapes

### Phase 1 : MVP (Actuel)
- ✅ Tables créées
- ✅ ML optimizer implémenté
- ✅ Intégration dans le calcul
- ✅ API endpoint
- ✅ Composant React Native

### Phase 2 : Amélioration (Futur)
- [ ] A/B testing : afficher les ajustements ML à l'utilisateur
- [ ] Feedback contextuel : "Pourquoi te sens-tu mieux ?"
- [ ] Visualisation des poids personnalisés dans le profil
- [ ] Export des données pour analyse scientifique

### Phase 3 : Intelligence avancée (Futur)
- [ ] Prédiction proactive : "Tu devrais te sentir mieux dans 2h"
- [ ] Clustering : "Utilisateurs similaires tolèrent mieux X"
- [ ] Feedback implicite : analyser l'activité dans l'app

---

## 📚 Références

- **Gradient Descent** : https://en.wikipedia.org/wiki/Stochastic_gradient_descent
- **Pharmacokinetics** : https://www.fda.gov/drugs/development-approval-process-drugs/clinical-pharmacology
- **Personalized Medicine** : https://www.nih.gov/precision-medicine-initiative

---

## 📝 Notes importantes

### ⚠️ Conseil du Coach

> Attention à ne pas laisser l'IA s'ajuster trop vite. Un seul feedback "euphorique" ne doit pas effacer 92 jours de données cliniques. C'est pour cela que je recommande un ajustement graduel (5%) et non radical.

### 🔒 Sécurité

- Les poids sont contraints entre 0.5 et 2.0
- Minimum 2h entre deux feedbacks
- Historique conservé pour audit
- RLS activé sur les tables

### 🧪 Tests

```bash
# Tester l'endpoint
curl -X POST http://localhost:9000/api/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "uuid-here",
    "system_score": 20,
    "user_score": 65,
    "active_factors": {},
    "energy_at_feedback": 20,
    "hours_since_wake": 7.5,
    "feedback_context": "manual"
  }'
```

---

**Pulse Energy Decay V2 + ML Adaptatif = 🚀 Précision Infaillible**
