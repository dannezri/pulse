# 🚀 Guide de Déploiement du Système ML

## ✅ Ce qui est déjà fait

### Backend ✅
- ✅ Tables Supabase (`user_feedback`, `personalized_weights`)
- ✅ Service ML Optimizer (`ml_optimizer.py`)
- ✅ Endpoint API `/api/v1/feedback`
- ✅ Intégration dans `pulse_energy_decay_service.py`

### Mobile ✅
- ✅ Composant `FeedbackSlider.tsx`
- ✅ Hook `useFeedback.ts`

---

## 📋 Étapes de déploiement

### 1️⃣ Backend : Redémarrer le serveur API

```bash
cd /Users/dannezri/Desktop/Pulse/backend
./restart_api_server.sh
```

**Vérification dans les logs :**
```
🚀 Démarrage du serveur Bio-Feedback IA sur http://0.0.0.0:9000
[MLOptimizer] ⚖️ Poids personnalisés chargés
```

### 2️⃣ Mobile : Intégrer le FeedbackSlider

**Étape A : Ouvrir la page énergie**

Fichier : `/Users/dannezri/Desktop/Pulse/mobile/app/(tabs)/energie.tsx`

**Étape B : Ajouter les imports**

```tsx
import { useState } from 'react';
import { FeedbackSlider } from '../../src/components/FeedbackSlider';
import { useFeedback } from '../../src/hooks/useFeedback';
```

**Étape C : Extraire les données nécessaires**

```tsx
const EnergyAnalysisScreen = () => {
  const { user } = useAuth();
  const { briefData } = useBriefData();
  const { submitFeedback } = useFeedback();
  
  // État pour afficher/masquer le slider
  const [showFeedback, setShowFeedback] = useState(false);
  
  // Extraire les scores
  const systemScore = briefData?.intraday_energy_forecast?.current_energy || 0;
  const pulseScore = briefData?.pulseScore || 0;
  
  // Extraire les facteurs actifs
  const activeMedications = briefData?.intraday_energy_forecast?.influencers
    ?.filter(i => i.type === 'medication')
    .map(i => i.code) || [];
  
  const activeConditions = briefData?.intraday_energy_forecast?.influencers
    ?.filter(i => i.type === 'condition')
    .map(i => i.code) || [];
  
  // Afficher le slider après 10 secondes (ou selon votre logique)
  useEffect(() => {
    const timer = setTimeout(() => {
      setShowFeedback(true);
    }, 10000); // 10 secondes après l'ouverture
    
    return () => clearTimeout(timer);
  }, []);
  
  return (
    <SafeAreaView>
      {/* Votre UI existante */}
      
      {/* Feedback Slider */}
      {showFeedback && user && (
        <FeedbackSlider
          systemScore={systemScore || pulseScore}
          activeMedications={activeMedications}
          activeConditions={activeConditions}
          onSubmit={async (userScore) => {
            await submitFeedback({
              user_id: user.id,
              system_score: systemScore || pulseScore,
              user_score: userScore,
              active_factors: {
                medications: activeMedications,
                conditions: activeConditions,
              },
            });
          }}
          onDismiss={() => setShowFeedback(false)}
        />
      )}
    </SafeAreaView>
  );
};
```

### 3️⃣ Test du système

**Scénario de test :**

1. **Ouvrir l'app Pulse** sur votre device
2. **Naviguer vers l'onglet "Énergie"**
3. **Attendre 10 secondes** (le slider apparaît)
4. **Observer le score système** (ex: 29%)
5. **Ajuster le slider** pour indiquer votre ressenti (ex: 45%)
6. **Appuyer sur "Envoyer"**

**Logs attendus (Backend) :**
```
[MLOptimizer] 📝 Feedback reçu: user=..., system=29.0, user=45
[MLOptimizer] 🎯 medication:N06AX11 weight: 1.000 → 0.992 (Δ-0.008, confidence=0.30)
[MLOptimizer] ✅ 2 ajustements appliqués
```

**Logs attendus (Mobile) :**
```
[useFeedback] 📤 Envoi feedback: {...}
[useFeedback] ✅ Feedback envoyé: error=16.0%, adjustments=2
[useFeedback] 🎯 Ajustements ML appliqués:
  - medication:N06AX11: 1.00 → 0.99 (confidence=0.30)
```

---

## 🧪 Validation de l'apprentissage

### Après 3 feedbacks similaires

1. **Vérifier dans Supabase** :

```sql
SELECT 
  factor_name,
  weight_multiplier,
  feedback_count,
  confidence_score
FROM personalized_weights
WHERE user_id = 'VOTRE_USER_ID'
  AND is_active = TRUE;
```

**Résultat attendu :**
```
factor_name      | weight_multiplier | feedback_count | confidence_score
-----------------|-------------------|----------------|------------------
Mirtazapine      | 0.985             | 3              | 0.30
Dépression       | 0.990             | 3              | 0.30
```

2. **Rafraîchir l'app** (tirer vers le bas sur l'onglet Énergie)

3. **Observer la nouvelle prédiction** :
   - Avant : 29% (avec poids = 1.0)
   - Après : ~32% (avec poids = 0.985)
   - ➡️ **Le système apprend !** 🎯

---

## 🎯 Stratégies d'affichage du Slider

### Option 1 : Trigger automatique (recommandé)

Afficher le slider si l'écart est > 15% :

```tsx
useEffect(() => {
  const error = Math.abs(systemScore - estimatedUserScore);
  if (error > 15 && !showFeedback) {
    setShowFeedback(true);
  }
}, [systemScore]);
```

### Option 2 : Bouton manuel

Ajouter un bouton "Donner mon ressenti" :

```tsx
<TouchableOpacity onPress={() => setShowFeedback(true)}>
  <Text>💬 Donner mon ressenti</Text>
</TouchableOpacity>
```

### Option 3 : Notification programmée

Demander un feedback à des moments clés :
- Après le réveil (10h-11h)
- Après le déjeuner (14h-15h)
- En fin de journée (19h-20h)

```tsx
useEffect(() => {
  const now = new Date().getHours();
  if ([10, 14, 19].includes(now) && !hasGivenFeedbackToday) {
    setShowFeedback(true);
  }
}, []);
```

---

## 📊 Dashboard ML (optionnel)

Pour visualiser les ajustements, créer une page dédiée :

```tsx
// mobile/app/(tabs)/ml-stats.tsx
const MLStatsScreen = () => {
  const [stats, setStats] = useState(null);
  
  useEffect(() => {
    fetch(`${API_URL}/api/v1/users/${user.id}/ml-stats`)
      .then(res => res.json())
      .then(setStats);
  }, []);
  
  return (
    <ScrollView>
      <Text>Facteurs personnalisés : {stats?.total_factors}</Text>
      {stats?.factors.map(f => (
        <View key={f.factor_code}>
          <Text>{f.factor_name}</Text>
          <Text>Poids: {f.weight_multiplier.toFixed(2)}</Text>
          <Text>Confiance: {(f.confidence_score * 100).toFixed(0)}%</Text>
        </View>
      ))}
    </ScrollView>
  );
};
```

---

## 🔧 Troubleshooting

### Problème : Le slider n'apparaît pas

**Solution :**
1. Vérifier que `showFeedback` est bien à `true`
2. Vérifier que `user` est défini
3. Vérifier les logs : `console.log('[EnergyAnalysis] showFeedback:', showFeedback)`

### Problème : Erreur 500 lors de l'envoi

**Solution :**
1. Vérifier que le backend est démarré
2. Vérifier l'URL dans `mobile/src/config/api.ts`
3. Regarder les logs backend : `tail -f backend.log`

### Problème : Les ajustements ne sont pas appliqués

**Solution :**
1. Vérifier que `feedback_count >= 3` dans Supabase
2. Vérifier que le backend a été redémarré après mise à jour
3. Vérifier les logs : `[PulseEnergyDecay] ⚖️ X poids personnalisés chargés`

---

## 🎓 Ressources

- 📖 [ML_SYSTEM_README.md](backend/ML_SYSTEM_README.md) - Documentation technique complète
- 🧪 [Exemple de payload](backend/ML_SYSTEM_README.md#-api-endpoint)
- 📊 [Formule SGD](backend/ML_SYSTEM_README.md#-fonctionnement-mathématique)

---

**Le système est prêt ! Maintenant, il ne reste plus qu'à le déployer et à commencer à l'entraîner. 🚀🧠**
