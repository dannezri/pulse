# 📊 Analyse de la Page Énergie - Pulse Mobile

## Vue d'ensemble

La page **Analyse Énergétique** (`mobile/app/(tabs)/energie.tsx`) est un écran sophistiqué qui affiche une analyse complète de l'énergie de l'utilisateur en temps réel, avec apprentissage machine adaptatif.

---

## 🏗️ Architecture du Flux de Données

### 1. **Flux de Récupération des Données**

```
┌─────────────┐
│  energie.tsx│
└──────┬──────┘
       │ useBriefData(userId)
       ▼
┌──────────────────┐
│ useBriefData.ts  │
└──────┬───────────┘
       │ generateBrief()
       ▼
┌──────────────────┐
│  briefApi.ts     │
└──────┬───────────┘
       │ POST /api/v1/generate-brief
       ▼
┌──────────────────────────────┐
│  Backend (api_server.py)     │
│  - Récupère biométriques     │
│  - Calcule Pulse Score       │
│  - Génère forecast énergie   │
│  - Génère insights IA        │
└──────────────────────────────┘
```

### 2. **Structure des Données Reçues**

```typescript
{
  pulseScore: number,           // Score global 0-100
  state: 'good' | 'warning' | 'critical',
  cards: BriefCard[],          // Cartes d'insight IA
  lastUpdated: Date,
  intraday_energy_forecast: {  // ⭐ Clé pour la page Énergie
    type: "forecast_v2",
    model_version: "2.0",
    generated_at: string,
    forecast_date: string,
    current_energy: number,    // Énergie actuelle (0-100)
    
    forecast_curve: [          // Points de la courbe
      {
        time: string,          // ISO timestamp
        value: number          // Énergie prédite (0-100)
      }
    ],
    
    influencers: [             // Facteurs d'influence
      {
        name: string,          // Ex: "Sertraline 50mg"
        type: "medication" | "condition" | "oura",
        code: string,          // Code ATC ou ICD-11
        impact: string,        // Ex: "-12%" ou "+8%"
        status: "positive" | "negative"
      }
    ],
    
    notes: string[]            // Explications textuelles
  }
}
```

---

## 📱 Composants de la Page

### **1. Header avec Actions**
```tsx
- Titre: "Analyse Énergétique"
- Bouton Refresh (🔄) : Force le recalcul via l'API
- Bouton Debug (🔬) : Affiche les métadonnées techniques
```

### **2. Score Actuel (Card Principale)**
```tsx
{Math.round(currentEnergy)}%
```
- **Couleur dynamique** selon le score :
  - `< 20%` : "Repos nécessaire" (rouge)
  - `20-40%` : "Énergie basse" (orange)
  - `40-60%` : "Énergie modérée" (jaune)
  - `60-80%` : "Bonne énergie" (vert clair)
  - `>= 80%` : "Énergie excellente" (vert foncé)

- **Badge de fallback** : Si `forecast_curve` est vide, affiche :
  ```
  📊 Basé sur votre Pulse Score
  ```

### **3. Graphique de Courbe Prédictive**
```tsx
LineChart from 'react-native-gifted-charts'
```

**Caractéristiques :**
- **Filtrage intelligent** : Affiche uniquement les points depuis l'heure de réveil (récupérée depuis `biometrics.metadata.bedtime_end`)
- **Échantillonnage** : Prend un point sur deux pour éviter la surcharge visuelle
- **Fallback** : Si pas de données, génère une courbe plate basée sur le `pulseScore`
- **Style** :
  - Courbe lissée (`curved`)
  - Gradient de remplissage violet (`#8B5CF6`)
  - Points de données visibles (rayon 4px)
  - Axe X : Heures (ex: "7h", "14h", "21h")
  - Axe Y : 0-100%

**Code clé :**
```tsx
const allPoints = forecast.forecast_curve || forecast.points || [];
const wakeHour = wakeTime !== null ? wakeTime : 7;

const chartData = allPoints
  .filter((point) => {
    const pointTime = new Date(point.time);
    const pointHour = pointTime.getHours();
    return pointHour >= wakeHour && pointHour < 24;
  })
  .filter((_, i) => i % 2 === 0) // 1 point sur 2
  .map((point) => ({
    value: point.value ?? point.energy ?? fallbackValue,
    label: `${pointTime.getHours()}h`
  }));
```

### **4. Balance Énergétique**

Barre de comparaison visuelle entre facteurs positifs et négatifs :

```
┌────────────────────────────────┐
│ +totalPositive │ -totalNegative│
└────────────────────────────────┘
   Vert (flex)     Rouge (flex)
```

**Statistiques :**
- Nombre de facteurs positifs
- Nombre de facteurs négatifs

### **5. Facteurs d'Influence Détaillés**

Liste des `influencers` groupés par type :

**Facteurs positifs** (vert) :
```
┌─────────────────────────────┐
│ 🏃 Activité modérée    +8% │
│ 😴 Sommeil excellent   +12%│
└─────────────────────────────┘
```

**Facteurs négatifs** (rouge) :
```
┌─────────────────────────────┐
│ 💊 Sertraline 50mg    -15% │
│ 🩺 Dépression légère   -8% │
└─────────────────────────────┘
```

**Format des cartes :**
- Bordure gauche colorée (3px)
- Fond semi-transparent
- Nom du facteur (gauche)
- Impact en % (droite)

### **6. Notes Explicatives**

Liste à puces des explications textuelles :
```
📝 Notes explicatives
• Votre sommeil profond est inférieur à la baseline
• Le médicament X est en phase d'adaptation (J+3)
• La récupération HRV suggère un stress élevé
```

### **7. Mode Debug (optionnel)**

Métadonnées techniques :
```
🔬 Mode Debug
Type de modèle     : forecast_v2
Version            : 2.0
Date de génération : 01/02/2026 21:35:42
Points de données  : 48
📋 Log JSON complet (bouton)
```

### **8. Footer Explicatif**

```
🧠 Comment ça marche ?
Le modèle Pulse Energy Decay V2 combine vos données Oura 
(sommeil, récupération) avec vos médicaments et conditions 
de santé pour prédire votre énergie tout au long de la journée.

Chaque facteur a un impact mesuré scientifiquement, et le 
système apprend de vos feedbacks pour s'adapter à VOTRE 
corps spécifiquement.
```

---

## 🤖 Système de Feedback ML (FeedbackSlider)

### **Apparition automatique**
```tsx
useEffect(() => {
  const timer = setTimeout(() => {
    if (forecast && !showFeedback) {
      setShowFeedback(true);
    }
  }, 15000); // 15 secondes après l'ouverture
}, [forecast, showFeedback]);
```

### **Composant FeedbackSlider**

Bottom sheet qui apparaît en bas de l'écran :

```
┌────────────────────────────────────┐
│ 📈 Comment vous sentez-vous ?   ✕ │
│                                    │
│ Pulse estime votre énergie à      │
│           52%                      │
│                                    │
│ Votre ressenti :                   │
│ 0% [━━━━●━━━━━━] 100%             │
│           65%                      │
│                                    │
│ Vous vous sentez mieux (+13%) 📈   │
│                                    │
│ [      📤 Envoyer       ]         │
│                                    │
│ Votre feedback aide Pulse à       │
│ apprendre votre métabolisme 🧠    │
└────────────────────────────────────┘
```

**Props :**
```tsx
{
  systemScore: number,           // Score calculé par le système
  activeMedications: string[],   // Codes ATC actifs
  activeConditions: string[],    // Codes ICD-11 actifs
  onSubmit: (userScore) => Promise<void>,
  onDismiss: () => void
}
```

**Flux de soumission :**
```
1. User ajuste le slider (0-100)
2. Clique sur "Envoyer"
3. onSubmit() appelé dans energie.tsx
4. useFeedback.submitFeedback() → POST /api/v1/feedback
5. Backend : ml_optimizer.process_feedback()
6. Calcul SGD : ajustement des poids personnalisés
7. Réponse : { error, adjustments_count, adjustments[] }
8. Animation de fermeture du slider
9. Haptic feedback (vibration)
```

---

## 🔬 Backend - Endpoint `/api/v1/feedback`

### **Payload**
```json
{
  "user_id": "uuid",
  "system_score": 52.3,
  "user_score": 65,
  "active_factors": {
    "medications": ["N06AB06", "N06AX11"],
    "conditions": ["6A70"]
  }
}
```

### **Traitement (ml_optimizer.py)**

```python
async def process_feedback(user_id, system_score, user_score, active_factors):
    # 1. Stocker le feedback dans user_feedback
    feedback_id = await self._store_feedback(
        user_id, system_score, user_score, active_factors
    )
    
    # 2. Calculer l'erreur
    error = user_score - system_score  # +13 dans l'exemple
    
    # 3. Ajuster les poids via SGD
    adjustments = []
    for medication in active_factors['medications']:
        adj = await self._adjust_weight(
            user_id, 'medication', medication, error
        )
        adjustments.append(adj)
    
    for condition in active_factors['conditions']:
        adj = await self._adjust_weight(
            user_id, 'condition', condition, error
        )
        adjustments.append(adj)
    
    # 4. Marquer le feedback comme traité
    await self._mark_feedback_processed(feedback_id)
    
    return {
        'status': 'ok',
        'error': error,
        'adjustments': adjustments
    }
```

### **Algorithme SGD (Stochastic Gradient Descent)**

```python
# Formule : W_new = W_old + η × (error / 100) × φ

η = 0.05  # Learning rate
φ = -1.0  # Direction (malus pour médicaments/conditions)

# Si error = +13 (user se sent mieux que prévu)
# → On RÉDUIT le malus du médicament
adjustment = 0.05 × (13 / 100) × (-1) = -0.0065

# Exemple :
# Sertraline avait un poids de 1.0 (100% de l'impact)
# Nouveau poids : 1.0 - 0.0065 = 0.9935 (99.35%)
# → Le médicament aura moins d'impact négatif la prochaine fois
```

### **Réponse**
```json
{
  "status": "ok",
  "error": 13.0,
  "adjustments_count": 2,
  "adjustments": [
    {
      "factor_type": "medication",
      "factor_code": "N06AB06",
      "old_weight": 1.0,
      "new_weight": 0.9935,
      "adjustment": -0.0065,
      "confidence": 0.15
    },
    {
      "factor_type": "condition",
      "factor_code": "6A70",
      "old_weight": 1.0,
      "new_weight": 0.9942,
      "adjustment": -0.0058,
      "confidence": 0.12
    }
  ]
}
```

---

## 🔄 Gestion du Cache et Rafraîchissement

### **Stratégie de cache (React Query)**
```tsx
staleTime: 5 * 60 * 1000  // 5 minutes
```

### **Force Refresh**
```tsx
const refetchWithForce = async () => {
  setForceRefreshFlag(prev => prev + 1);
  // → Appel API avec ?force_refresh=true
  // → Recalcul complet backend (ignore le cache)
};
```

### **Backend - Cache intelligent**
```python
# Si cache récent (< 5 min) ET force_refresh=false
if recent_cache and not force_refresh:
    return cached_forecast

# Sinon : recalcul complet
forecast = await generate_intraday_forecast(user_id)
```

---

## 📊 Cas d'Usage et Scénarios

### **Scénario 1 : Données complètes**
```
✅ Oura connecté
✅ Sommeil récent synchronisé
✅ Médicaments actifs
✅ Conditions enregistrées

→ Affiche :
  - Score actuel : 68%
  - Courbe prédictive complète (48 points)
  - 5 influencers (3 positifs, 2 négatifs)
  - 4 notes explicatives
  - FeedbackSlider après 15s
```

### **Scénario 2 : Données partielles (nouveau user)**
```
❌ Pas de données Oura
✅ Pulse Score calculé (baseline)

→ Affiche :
  - Score actuel : 50% (pulseScore fallback)
  - Badge "📊 Basé sur votre Pulse Score"
  - Courbe plate (ligne droite à 50%)
  - Message : "🔄 Analyse en cours"
  - Footer explicatif
```

### **Scénario 3 : Énergie très basse**
```
Score actuel : 18%
→ Affiche : "Repos nécessaire" (rouge)
→ Facteurs négatifs dominants :
  - Sommeil insuffisant : -25%
  - Médicament sédatif : -18%
  - HRV basse : -12%
→ FeedbackSlider : Compare 18% vs ressenti utilisateur
```

### **Scénario 4 : Après feedback ML**
```
1. User donne feedback : 65% (système pensait 52%)
2. Error = +13% → User se sent mieux que prévu
3. Backend ajuste les poids :
   - Sertraline : 1.0 → 0.9935 (impact réduit)
   - Dépression : 1.0 → 0.9942 (impact réduit)
4. Prochaine prédiction : Score plus optimiste
5. Confiance augmente après plusieurs feedbacks
```

---

## 🐛 Points d'Attention et Bugs Potentiels

### **1. Format des données forecast (V1 vs V2)**
```tsx
// Support des deux formats legacy
const allPoints = forecast.forecast_curve || forecast.points || [];
const currentEnergy = forecast.current_energy 
  ?? forecast.points?.[0]?.energy 
  ?? fallbackEnergy;
```

### **2. Fallback intelligent**
```tsx
// Si tous les points sont à 0 (bug backend)
if (value === 0) {
  value = Math.max(briefData?.pulseScore ?? 50, 40);
}
```

### **3. Erreur colonne générée (CORRIGÉE)**
```python
# ❌ AVANT (causait l'erreur)
result = supabase.table('user_feedback').insert({
    'error': user_score - system_score,  # ← INTERDIT
    ...
})

# ✅ MAINTENANT
result = supabase.table('user_feedback').insert({
    # 'error' est calculé automatiquement par PostgreSQL
    ...
})
```

### **4. Codes ATC/ICD-11 manquants**
```tsx
// Extraction robuste depuis influencers
const medications = forecast.influencers
  ?.filter((i: any) => i.type === 'medication')
  .map((i: any) => i.code) || [];
```

---

## 📈 Métriques de Performance

### **Temps de chargement typiques**
- Depuis cache : `< 100ms`
- Avec recalcul : `1-3s`
- Avec génération IA : `5-10s`

### **Consommation réseau**
- Brief complet : `~15-30 KB`
- Forecast seul : `~5-10 KB`

### **Interactions utilisateur**
- Scroll fluide (ScrollView optimisé)
- Haptic feedback sur actions
- Animation du FeedbackSlider (300ms)
- Debounce sur refresh (500ms)

---

## 🚀 Améliorations Futures

### **1. Prédictions horaires avec notifications**
```
"Dans 2h, votre énergie devrait baisser à 35%.
Planifiez une pause ou une collation maintenant."
```

### **2. Comparaison historique**
```
Votre énergie aujourd'hui vs :
- Hier : +12%
- Moyenne 7j : +5%
- Même jour semaine dernière : -3%
```

### **3. Insights IA contextuels**
```
"Votre énergie est 20% plus basse que d'habitude 
après avoir dormi < 6h. Priorisez le repos ce soir."
```

### **4. Export PDF du rapport**
```
Rapport hebdomadaire :
- Courbes d'énergie 7 jours
- Facteurs dominants
- Ajustements ML appliqués
- Recommandations
```

---

## ✅ Validation du Flux Complet

**Test manuel recommandé :**

1. ✅ Ouvrir l'onglet "Énergie"
2. ✅ Vérifier le score actuel affiché
3. ✅ Vérifier la courbe prédictive (smooth et complète)
4. ✅ Vérifier les influencers (positifs/négatifs)
5. ✅ Attendre 15s → FeedbackSlider apparaît
6. ✅ Ajuster le slider et envoyer
7. ✅ Vérifier les logs : `[useFeedback] ✅ Feedback envoyé`
8. ✅ Vérifier backend : `INFO:ml_optimizer:[MLOptimizer] ✅ Feedback traité`
9. ✅ Vérifier database : `SELECT * FROM user_feedback ORDER BY created_at DESC LIMIT 1;`
10. ✅ Vérifier ajustements : `SELECT * FROM personalized_weights WHERE user_id = '...'`

---

## 📚 Fichiers Impliqués

### **Mobile**
```
mobile/app/(tabs)/energie.tsx              (504 lignes) ← Page principale
mobile/src/hooks/useBriefData.ts           (133 lignes) ← Hook data
mobile/src/hooks/useFeedback.ts            (171 lignes) ← Hook feedback
mobile/src/components/FeedbackSlider.tsx   (321 lignes) ← UI feedback
mobile/src/services/briefApi.ts                         ← API calls
mobile/src/types/brief.ts                               ← Types TypeScript
```

### **Backend**
```
backend/api_server.py                      (ligne 2353-2406) ← Endpoint feedback
backend/ml_optimizer.py                    (ligne 90-360)    ← ML logic
backend/services/ai_service.py                               ← Génération forecast
database/migrations/038_create_user_feedback_table.sql       ← Schema DB
```

---

## 🎯 Conclusion

La page **Analyse Énergétique** est une **fonctionnalité clé de Pulse** qui combine :

- **Visualisation intuitive** (graphique interactif)
- **Explications transparentes** (influencers détaillés)
- **Apprentissage adaptatif** (ML via feedback utilisateur)
- **Architecture robuste** (fallbacks intelligents)

Le système évolue avec chaque utilisateur grâce au **feedback ML**, rendant les prédictions de plus en plus précises au fil du temps. 🧠✨
