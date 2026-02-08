# 📊 Page d'Analyse Énergétique Détaillée

## 🎯 Objectif

Créer une page dédiée qui isole et explique en détail le calcul d'énergie intrajournalière avec toutes les précisions nécessaires.

---

## ✅ Ce qui a été créé

### 1️⃣ **Nouvelle page : `energy-analysis.tsx`**

Chemin : `/Users/dannezri/Desktop/Pulse/mobile/app/energy-analysis.tsx`

**Contenu** :
- 📈 **Courbe prédictive** : Graphique LineChart avec tous les points
- 💯 **Score actuel** : Énergie courante en grand avec statut
- ⚖️ **Balance énergétique** : Barre visuelle positive/négative
- 🎯 **Facteurs d'influence** : Liste détaillée de tous les influencers
- 📝 **Notes explicatives** : Toutes les notes du système
- 🔬 **Mode Debug** : JSON complet, métadonnées, timestamps
- 🧠 **Explication** : Comment fonctionne le modèle

### 2️⃣ **Bouton dans IntradayEnergyCurveCard**

Modification : `/Users/dannezri/Desktop/Pulse/mobile/src/components/IntradayEnergyCurveCard.tsx`

**Ajouté** :
- Bouton "🔬 Analyse détaillée" avec gradient violet
- Navigation vers `/energy-analysis`
- Feedback haptique au clic

---

## 🎨 Design de la page

### Header
```
← Analyse Énergétique 🔬
```
- Bouton retour à gauche
- Bouton debug à droite (toggle)

### Section 1 : Score actuel
```
┌─────────────────────┐
│  Énergie actuelle   │
│      45%            │ ← Grande taille
│  Énergie modérée    │ ← Statut
└─────────────────────┘
```

### Section 2 : Graphique
```
┌─────────────────────────┐
│ 📈 Courbe prédictive    │
│                         │
│  [Graphique LineChart]  │
│                         │
│ Prédiction basée sur... │
└─────────────────────────┘
```

### Section 3 : Balance
```
┌──────────────────────────┐
│ ⚖️ Balance énergétique   │
│                          │
│ [█████████▓▓▓▓▓▓▓▓]      │
│  +85      -32            │
│                          │
│ Facteurs positifs: 1     │
│ Facteurs négatifs: 1     │
└──────────────────────────┘
```

### Section 4 : Influencers détaillés
```
┌──────────────────────────┐
│ 🎯 Facteurs d'influence  │
│                          │
│ Facteurs positifs        │
│ ├─ Sommeil (Readiness)   │
│ │  +85                   │
│                          │
│ Facteurs négatifs        │
│ ├─ 😔 Dépression          │
│ │  -32                   │
│ └─ 💊 Mirtazapine         │
│    -25                   │
└──────────────────────────┘
```

### Section 5 : Notes
```
┌──────────────────────────┐
│ 📝 Notes explicatives    │
│                          │
│ • Dépression : décr...   │
│ • Mirtazapine : effet... │
│ • ...                    │
└──────────────────────────┘
```

### Section 6 : Mode Debug (optionnel)
```
┌──────────────────────────┐
│ 🔬 Mode Debug            │
│                          │
│ Type de modèle:          │
│ pulse_energy_decay       │
│                          │
│ Version:                 │
│ pulse_energy_decay_v1    │
│                          │
│ Date de génération:      │
│ 31/01/2026 15:30:00      │
│                          │
│ Points de données: 48    │
│                          │
│ [📋 Log JSON complet]    │
└──────────────────────────┘
```

### Footer : Explication
```
┌──────────────────────────┐
│ 🧠 Comment ça marche ?   │
│                          │
│ Le modèle Pulse Energy   │
│ Decay V2 combine vos...  │
│                          │
│ Chaque facteur a un...   │
└──────────────────────────┘
```

---

## 🔄 Flux d'utilisation

```
1. Utilisateur voit la card IntradayEnergyCurveCard
   ↓
2. Clique sur "🔬 Analyse détaillée"
   ↓
3. Feedback haptique (vibration)
   ↓
4. Navigation vers /energy-analysis
   ↓
5. Page s'affiche avec toutes les sections
   ↓
6. (Optionnel) Active le mode debug
   ↓
7. Voit les métadonnées complètes
   ↓
8. Clique sur "Log JSON complet"
   ↓
9. JSON affiché dans la console
   ↓
10. Retour via bouton ←
```

---

## 📱 Composants utilisés

### UI
- ✅ `SafeAreaView` : Zones sûres iOS
- ✅ `ScrollView` : Défilement vertical
- ✅ `LineChart` (react-native-chart-kit) : Graphique
- ✅ `LinearGradient` : Dégradés
- ✅ `Pressable` : Boutons tactiles
- ✅ `ActivityIndicator` : Loading

### Hooks
- ✅ `useAuth()` : Récupère userId
- ✅ `useBriefData()` : Récupère forecast
- ✅ `useRouter()` : Navigation
- ✅ `useLocalSearchParams()` : Paramètres URL (si besoin)
- ✅ `useState()` : Mode debug

### Animations
- ✅ `Haptics.impactAsync()` : Feedback haptique

---

## 🎨 Palette de couleurs

| Élément | Couleur | Code |
|---------|---------|------|
| Background | Noir | `#000000` |
| Cards | Gris foncé | `#1F1F1F` |
| Texte principal | Blanc | `#FFFFFF` |
| Texte secondaire | Gris | `#9CA3AF` |
| Accent principal | Violet | `#8B5CF6` |
| Positif | Vert | `#10B981` |
| Négatif | Rouge | `#EF4444` |
| Border | Gris très foncé | `#1F1F1F` |

---

## 📊 Données affichées

### Depuis `forecast`

```typescript
interface IntradayForecast {
  type: string;                    // "pulse_energy_decay"
  date: string;                    // "2026-01-31"
  generated_at: string;            // ISO8601
  model_version: string;           // "pulse_energy_decay_v1"
  current_energy: number;          // 0-100
  forecast_curve: Array<{
    time: string;                  // ISO8601
    value: number;                 // 0-100
    event?: string;                // Événement marquant
  }>;
  influencers: Array<{
    name: string;                  // "Sommeil (Readiness)"
    impact: string;                // "+85"
    status: 'positive' | 'negative';
  }>;
  notes: string[];                 // Notes explicatives
}
```

### Calculs dérivés

```typescript
// Total des impacts positifs
const totalPositive = positiveInfluencers.reduce((sum, inf) => 
  sum + Math.abs(parseInt(inf.impact) || 0), 0
);

// Total des impacts négatifs
const totalNegative = negativeInfluencers.reduce((sum, inf) => 
  sum + Math.abs(parseInt(inf.impact) || 0), 0
);

// Statut de l'énergie
const getEnergyStatus = (energy: number) => {
  if (energy < 20) return 'Repos nécessaire';
  if (energy < 40) return 'Énergie basse';
  if (energy < 60) return 'Énergie modérée';
  if (energy < 80) return 'Bonne énergie';
  return 'Énergie excellente';
};
```

---

## 🔬 Mode Debug

### Activé via bouton
Le mode debug affiche :
- Type de modèle utilisé
- Version du modèle
- Date/heure de génération
- Nombre de points de données
- Bouton "Log JSON complet"

### Console logs
```javascript
console.log('[Energy Analysis] Full forecast data:', JSON.stringify(forecast, null, 2));
```

Affiche dans la console React Native :
```json
{
  "type": "pulse_energy_decay",
  "date": "2026-01-31",
  "current_energy": 45.2,
  "forecast_curve": [...],
  "influencers": [...],
  "notes": [...]
}
```

---

## 🧪 Comment tester

### 1. Démarrer l'app
```bash
cd mobile
npx expo start
```

### 2. Naviguer vers la home
L'écran principal affiche les cards

### 3. Voir la card IntradayEnergyCurveCard
Défiler jusqu'à la card avec la courbe d'énergie

### 4. Cliquer sur "🔬 Analyse détaillée"
Le bouton violet en bas de la card

### 5. Explorer la page
- Défiler pour voir toutes les sections
- Activer le mode debug (bouton 🔬)
- Cliquer sur "Log JSON complet"

### 6. Vérifier la console
```bash
npx react-native log-ios   # iOS
npx react-native log-android  # Android
```

---

## 📚 Exemples d'affichage

### Énergie haute (85%)
```
Énergie actuelle
      85%
Énergie excellente
```

### Énergie basse (12%)
```
Énergie actuelle
      12%
Repos nécessaire
```

### Balance (85 positif, 57 négatif)
```
[████████████▓▓▓▓▓▓▓▓]
 +85          -57
```

### Influencer positif
```
┌─────────────────────────┐
│ ● Sommeil (Readiness)   │
│                    +85  │
└─────────────────────────┘
Vert avec border gauche
```

### Influencer négatif
```
┌─────────────────────────┐
│ ● 😔 Dépression          │
│                    -32  │
└─────────────────────────┘
Rouge avec border gauche
```

---

## 🚀 Améliorations futures

### Phase 1 (Actuel) ✅
- Page de base avec graphique
- Influencers détaillés
- Mode debug
- Navigation depuis la card

### Phase 2 (Suggéré)
- [ ] Graphique interactif (clic sur un point)
- [ ] Comparaison avec les jours précédents
- [ ] Export PDF du rapport
- [ ] Partage vers médecin

### Phase 3 (Avancé)
- [ ] Prédiction à 7 jours
- [ ] Recommandations personnalisées
- [ ] Alertes intelligentes
- [ ] Timeline des événements

---

## 📖 Documentation

### Fichiers modifiés
1. ✅ `mobile/app/energy-analysis.tsx` - Nouvelle page (594 lignes)
2. ✅ `mobile/src/components/IntradayEnergyCurveCard.tsx` - Ajout bouton

### Fichiers créés
1. ✅ `ENERGY_ANALYSIS_PAGE.md` - Documentation (ce fichier)

### Dépendances
- ✅ `react-native-chart-kit` (déjà installé)
- ✅ `expo-linear-gradient` (déjà installé)
- ✅ `expo-haptics` (déjà installé)
- ✅ `react-native-svg` (déjà installé)

---

## ✨ Conclusion

La page d'**Analyse Énergétique Détaillée** est maintenant **100% fonctionnelle** et accessible depuis la card IntradayEnergyCurveCard.

**Avantages** :
- ✅ Isolée : Page dédiée, pas de distraction
- ✅ Complète : Toutes les données affichées
- ✅ Pédagogique : Explications claires
- ✅ Debug : Mode développeur intégré
- ✅ UX premium : Animations, haptics, gradients
- ✅ Responsive : S'adapte à tous les écrans

**L'utilisateur peut maintenant comprendre en détail comment son énergie est calculée !** 🚀
