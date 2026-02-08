# 🎯 Guide d'intégration du système de Feedback ML

## ✅ Intégration terminée dans `app/(tabs)/index.tsx`

Le système de feedback ML est maintenant actif sur l'écran d'accueil !

---

## 🔄 Triggers automatiques

Le feedback s'affiche automatiquement dans ces cas :

### 1️⃣ **Low Energy Trigger** (Énergie < 15%)
Quand ton énergie tombe sous 15%, le BottomSheet s'affiche automatiquement pour demander comment tu te sens vraiment.

### 2️⃣ **Energy Spike** (Changement > 30 points)
Si ton énergie change brusquement de plus de 30 points, le système demande confirmation.

### 3️⃣ **Throttling intelligent**
- ✅ Minimum 2h entre deux demandes de feedback
- ✅ Sauvegardé dans AsyncStorage pour persistance

---

## 🎨 Ajouter un bouton manuel (optionnel)

Si tu veux permettre à l'utilisateur de donner un feedback manuellement, voici comment faire :

### Option 1 : Dans le profil

Modifie `app/(tabs)/profile.tsx` :

```tsx
import { useFeedback } from '../../src/hooks/useFeedback';
import { Pressable, Text, StyleSheet } from 'react-native';

export default function ProfileScreen() {
  const { openFeedbackManually } = useFeedback({
    userId,
    currentEnergy,
    systemScore,
    hoursSinceWake: calculateHoursSinceWake(),
    activeFactors: extractActiveFactors(),
  });

  return (
    <View>
      {/* ... votre UI ... */}
      
      <Pressable style={styles.feedbackButton} onPress={openFeedbackManually}>
        <Text style={styles.feedbackButtonText}>💡 Donner mon feedback</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  feedbackButton: {
    backgroundColor: '#8B5CF6',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 20,
  },
  feedbackButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});
```

### Option 2 : Dans le header

Ajoute un bouton dans le header de navigation :

```tsx
// app/_layout.tsx ou dans votre Stack.Screen
<Stack.Screen
  name="index"
  options={{
    headerRight: () => (
      <Pressable onPress={openFeedbackManually}>
        <Text style={{ fontSize: 24 }}>💡</Text>
      </Pressable>
    ),
  }}
/>
```

---

## 📊 Visualiser les poids personnalisés (optionnel)

Crée un écran pour afficher les ajustements ML :

```tsx
// screens/PersonalizedWeightsScreen.tsx
import { useEffect, useState } from 'react';
import { View, Text, FlatList } from 'react-native';
import { supabase } from '../config/supabase';

export function PersonalizedWeightsScreen({ userId }) {
  const [weights, setWeights] = useState([]);

  useEffect(() => {
    async function fetchWeights() {
      const { data } = await supabase
        .from('personalized_weights')
        .select('*')
        .eq('user_id', userId)
        .eq('is_active', true);
      
      setWeights(data || []);
    }

    fetchWeights();
  }, [userId]);

  return (
    <FlatList
      data={weights}
      keyExtractor={(item) => item.id}
      renderItem={({ item }) => (
        <View style={styles.weightCard}>
          <Text style={styles.factorName}>{item.factor_name}</Text>
          <Text style={styles.weight}>
            Poids: {(item.weight_multiplier * 100).toFixed(0)}%
          </Text>
          <Text style={styles.confidence}>
            Confiance: {(item.confidence_score * 100).toFixed(0)}%
          </Text>
          <Text style={styles.feedbackCount}>
            {item.feedback_count} feedbacks
          </Text>
        </View>
      )}
    />
  );
}
```

---

## 🧪 Tester le système

### 1. Forcer l'affichage du feedback (dev)

Dans `useFeedback.ts`, ajoute temporairement :

```tsx
// Pour tester en dev
useEffect(() => {
  if (__DEV__) {
    setShowFeedbackSheet(true); // Force l'affichage
  }
}, []);
```

### 2. Simuler une énergie basse

Dans `index.tsx`, force une énergie basse :

```tsx
const currentEnergy = 10; // Force 10% pour tester le trigger
```

### 3. Vérifier les logs

Ouvre la console React Native :

```bash
npx react-native log-android  # Android
npx react-native log-ios      # iOS
```

Tu verras :
```
[Feedback] 🔴 Low energy trigger: 10
[Feedback] ✅ Submitted: {...}
[Feedback] 🎯 ML optimized: [...]
```

---

## 📦 Dépendances requises

Assure-toi que ces packages sont installés :

```bash
npm install @react-native-community/slider
npm install @react-native-async-storage/async-storage
npm install expo-haptics
npm install expo-linear-gradient
```

---

## 🔄 Cycle de vie du feedback

```
┌─────────────────────────────┐
│  Utilisateur utilise l'app  │
└──────────────┬──────────────┘
               │
               ▼
     ┌─────────────────────┐
     │  Trigger détecté ?  │
     │  (énergie < 15%)    │
     └─────────┬───────────┘
               │ OUI
               ▼
     ┌─────────────────────┐
     │ BottomSheet s'affiche│
     │ avec slider 0-100    │
     └─────────┬───────────┘
               │
               ▼
     ┌─────────────────────┐
     │ Utilisateur répond   │
     │ (ex: 65%)            │
     └─────────┬───────────┘
               │
               ▼
     ┌─────────────────────┐
     │ POST /api/v1/feedback│
     └─────────┬───────────┘
               │
               ▼
     ┌─────────────────────┐
     │ Si 5 feedbacks atteints│
     │ → ML Optimizer      │
     └─────────┬───────────┘
               │
               ▼
     ┌─────────────────────┐
     │ Poids ajustés        │
     │ (ex: 1.0 → 0.95)    │
     └─────────┬───────────┘
               │
               ▼
     ┌─────────────────────┐
     │ Prochains calculs    │
     │ utilisent les nouveaux│
     │ poids personnalisés  │
     └─────────────────────┘
```

---

## 🎯 Métriques à surveiller

Dans la console Supabase, lance ces requêtes :

```sql
-- Nombre de feedbacks par utilisateur
SELECT 
    user_id,
    COUNT(*) as feedback_count,
    AVG(ABS(error)) as avg_error
FROM user_feedback
GROUP BY user_id
ORDER BY feedback_count DESC;

-- Poids les plus ajustés
SELECT 
    factor_name,
    weight_multiplier,
    feedback_count,
    confidence_score
FROM personalized_weights
WHERE feedback_count > 5
ORDER BY ABS(weight_multiplier - 1.0) DESC;

-- Distribution des contextes
SELECT 
    feedback_context,
    COUNT(*) as count
FROM user_feedback
GROUP BY feedback_context;
```

---

## ⚡ Performance

Le système est optimisé pour :
- ✅ Pas d'impact sur la performance de l'app (requêtes async)
- ✅ Cache des poids personnalisés au démarrage
- ✅ Throttling intelligent (max 1 feedback toutes les 2h)
- ✅ Batch processing des ajustements ML

---

## 🐛 Debugging

### Le feedback ne s'affiche pas ?

1. Vérifie que `userId` n'est pas null
2. Vérifie que `currentEnergy` est bien un nombre
3. Regarde les logs console :
```tsx
console.log('[Feedback] userId:', userId);
console.log('[Feedback] currentEnergy:', currentEnergy);
```

### L'API retourne une erreur ?

1. Vérifie que le backend tourne : `http://localhost:9000/docs`
2. Vérifie les logs backend :
```bash
tail -f /Users/dannezri/Desktop/Pulse/backend/nohup.out
```

### Les poids ne s'appliquent pas ?

1. Vérifie que les poids sont bien en DB :
```sql
SELECT * FROM personalized_weights WHERE user_id = 'your-uuid';
```

2. Vérifie que le cache est rechargé :
```
[PulseEnergyDecay] ⚖️ 3 poids personnalisés chargés
```

---

## 🚀 Prêt à lancer !

Le système est maintenant intégré et fonctionnel. Les triggers automatiques sont actifs et le ML s'adaptera progressivement à chaque utilisateur.

**Pour aller plus loin** :
- Ajouter des animations au BottomSheet
- Créer un écran de visualisation des poids
- Implémenter des notifications push pour les feedbacks importants
- A/B tester le learning rate (0.05 vs 0.03 vs 0.07)

---

**Documentation complète** : `MACHINE_LEARNING_FEEDBACK_SYSTEM.md`
