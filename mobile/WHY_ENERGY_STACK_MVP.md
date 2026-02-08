# Why Energy Stack - MVP Documentation

## 🎯 Objectif

Transformer Pulse d'un simple tracker en un **Coach Partenaire** empathique qui explique le score d'énergie via des **analogies simples et percutantes** générées par GPT-4o.

## 🏗️ Architecture

### Backend (`backend/explain_service.py`)

**Service d'explication énergétique** qui :
1. Récupère les données du calcul d'énergie (daily_energy, daily_state)
2. Récupère les médicaments, conditions et biométriques
3. Construit un prompt structuré pour GPT-4o
4. Génère 3 cartes narratives maximum (nervous, chemistry, load)
5. Retourne un JSON structuré pour l'application mobile

**Endpoint** : `GET /api/energy/explain/{user_id}?date=YYYY-MM-DD`

**Réponse** :
```json
{
  "energyScore": 38,
  "confidence": 62,
  "label": "Journée fragile",
  "date": "2026-02-01",
  "cards": [
    {
      "type": "nervous",
      "title": "Le câblage est saturé",
      "text": "Ton HRV est tombé à 20ms (baseline: 30ms). Ton système nerveux parasympathique ne récupère plus efficacement.",
      "analogy": "C'est comme charger ton téléphone avec un câble sectionné : l'énergie ne passe plus correctement.",
      "metrics": {
        "primary": {"label": "HRV actuel", "value": 20, "unit": "ms"},
        "secondary": {"label": "HRV baseline", "value": 30, "unit": "ms"}
      }
    }
  ]
}
```

### Frontend Hook (`src/hooks/useEnergyExplanation.ts`)

**Hook React Query** pour :
- Gérer le cache (30 min stale time)
- États de chargement/erreur
- Retry automatique
- Type-safety TypeScript

**Usage** :
```tsx
const { data, isLoading, error, refetch } = useEnergyExplanation({
  userId: 'user-123',
  date: '2026-02-01'
});
```

### Frontend Component (`src/components/WhyEnergyStack.tsx`)

**Composant UI pur** avec :
- 3 types de cartes (nervous ⚡️, chemistry 💊, load 🎒)
- Scroll horizontal paginé
- Effet glassmorphism (expo-blur)
- Animations fluides (react-native-reanimated)
- Indicateurs de pagination (dots)

**Props** :
```tsx
interface WhyEnergyStackProps {
  cards: EnergyCard[];
  energyScore?: number;
  label?: string;
  onCardPress?: (card: EnergyCard, index: number) => void;
}
```

## 📋 Types de Cartes

### 1. Nervous (Système Nerveux) ⚡️
**Quand ?** Recovery < 50%, HRV bas, RHR élevé, Infection > 80%

**Exemples d'analogies** :
- "Câble sectionné"
- "Circuit saturé"
- "Disjoncteur sauté"

**Couleur** : Rouge (#FF453A)

### 2. Chemistry (Chimie Corporelle) 💊
**Quand ?** Impact médicaments > 50%, sommeil bon mais score bas

**Exemples d'analogies** :
- "Moteur bridé"
- "Limiteur de vitesse"
- "Frein à main actif"

**Couleur** : Orange (#FF9F0A)

### 3. Load (Charge & Effort) 🎒
**Quand ?** Overtrain < 50%, conditions respiratoires, fatigue chronique

**Exemples d'analogies** :
- "Sac à dos invisible"
- "Courir dans le sable"
- "Escalier sans paliers"

**Couleur** : Jaune (#FFD60A)

## 🎨 Design Principles

### Glassmorphism
```tsx
<BlurView intensity={80} tint="dark" style={styles.card}>
  {/* Content */}
</BlurView>
```

### Animations
```tsx
// Entrée échelonnée
entering={FadeInRight.delay(index * 100).springify()}

// Press feedback
const scale = useSharedValue(1);
scale.value = withSpring(0.98); // onPressIn
scale.value = withSpring(1);    // onPressOut
```

### Responsive
```tsx
const CARD_WIDTH = SCREEN_WIDTH - 64; // 32px padding
const CARD_SPACING = 16;
```

## 🧪 Test Manuel

### 1. Backend

```bash
# Depuis backend/
cd /Users/dannezri/Desktop/Pulse/backend

# Test avec curl
curl -X GET "http://localhost:8000/api/energy/explain/USER_ID?date=2026-02-01" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Réponse attendue** : JSON avec `energyScore`, `cards[]`, `confidence`

### 2. Frontend

```bash
# Depuis mobile/
cd /Users/dannezri/Desktop/Pulse/mobile

# Vérifier les dépendances
npx expo-doctor

# Lancer l'app
npx expo start --clear
```

**Navigation** :
1. Login
2. Aller sur l'onglet "Énergie" (energie.tsx)
3. Scroll vers le bas après le score
4. Le WhyEnergyStack devrait apparaître avec les cartes

## 🔧 Configuration Requise

### Backend
- Python 3.9+
- OpenAI API key (GPT-4o)
- Supabase configuré

**Env variables** :
```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o  # Optionnel, défaut = gpt-4o
```

### Frontend
- Node >= 20.19.4
- Expo SDK 54
- React Native 0.81.5
- React 19.1.0

**Dépendances (déjà installées)** :
- `expo-blur` ~15.0.8
- `react-native-reanimated` ~4.1.1
- `@tanstack/react-query` ^5.17.0

## 🎯 Validation du MVP

### ✅ Backend
- [x] Service `EnergyExplainService` créé
- [x] Endpoint `/api/energy/explain/{user_id}` ajouté
- [x] Intégration LLMClient pour GPT-4o
- [x] Prompt système optimisé (analogies, longueurs strictes)
- [x] Gestion des erreurs et fallback

### ✅ Frontend
- [x] Hook `useEnergyExplanation` créé
- [x] Composant `WhyEnergyStack` créé
- [x] Intégration dans `energie.tsx`
- [x] Design glassmorphism
- [x] Animations fluides
- [x] Type-safety TypeScript

### 🧪 Tests à Effectuer
- [ ] Backend : Tester l'endpoint avec différents user_ids
- [ ] Frontend : Tester le scroll horizontal
- [ ] Frontend : Tester le press feedback
- [ ] Frontend : Tester avec 0 cartes (empty state)
- [ ] Frontend : Tester avec 1, 2, 3 cartes
- [ ] Integration : Tester la latence (devrait être < 3s)

## 🚀 Prochaines Étapes (Post-MVP)

1. **Cache intelligent** : Invalider le cache si nouvelles données Oura
2. **Pull-to-refresh** : Recharger les explications
3. **Détails expandables** : Modal avec détails complets
4. **Feedback utilisateur** : "Cette explication est-elle utile ?"
5. **Partage** : Exporter les cartes en image
6. **Notifications** : "Ton énergie a baissé, voici pourquoi"

## 🎓 Pourquoi C'est un Game Changer

### Avant
❌ Score de 38% → Utilisateur frustré et confus  
❌ Données brutes (HRV, RHR) → Incompréhensibles  
❌ Aucun contexte émotionnel → Culpabilisation  

### Après
✅ "Le câblage est saturé" → Validation empathique  
✅ Analogie simple → Compréhension immédiate  
✅ Métriques contextualisées → Autorité technique  
✅ Scalabilité IA → S'adapte à tous les profils  

## 📊 Métriques de Succès

### Engagement
- **Time on screen** : Temps passé sur WhyEnergyStack
- **Scroll depth** : Nombre de cartes consultées
- **Card interactions** : Presses sur les cartes

### Satisfaction
- **Feedback positif** : "Cette explication est utile"
- **Retention** : Taux de retour sur l'écran Énergie
- **NPS** : Net Promoter Score lié au storytelling

### Technique
- **Latence** : < 3s de la requête à l'affichage
- **Cache hit rate** : > 70% (éviter appels OpenAI)
- **Coût OpenAI** : < $0.02 par explication

## 🔐 Sécurité & Privacy

### Backend
- JWT authentication obligatoire
- User peut accéder uniquement à SES données
- Rate limiting recommandé (max 10 req/min par user)

### Frontend
- Pas de stockage sensible en local
- Cache géré par React Query (in-memory)
- Invalidation automatique après 1h

## 📚 Références

- **Prompt Engineering** : Voir `backend/explain_service.py` ligne 210-350
- **Type Definitions** : Voir `mobile/src/hooks/useEnergyExplanation.ts`
- **UI Components** : Voir `mobile/src/components/WhyEnergyStack.tsx`
- **Integration** : Voir `mobile/app/(tabs)/energie.tsx` ligne 41-46

## 🤝 Contribuer

Pour améliorer le Why-Stack :

1. **Nouvelles analogies** : Modifier le prompt système
2. **Nouveaux types de cartes** : Ajouter dans le type union
3. **Animations** : Modifier `WhyEnergyStack.tsx`
4. **Logique de priorisation** : Modifier `explain_service.py`

---

**Auteur** : Assistant AI  
**Date** : 2026-02-02  
**Version** : MVP 1.0  
**Status** : ✅ Prêt pour test
