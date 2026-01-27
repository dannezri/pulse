# Interface "Ambient Concierge" - Documentation

## Vue d'ensemble

L'interface "Ambient Concierge" transforme Pulse d'un tableau de bord classique vers une expérience minimaliste qui ne communique que l'essentiel. L'utilisateur comprend son état en moins de 2 secondes.

## Philosophie

> "Un concierge discret qui ne parle que quand c'est nécessaire"

Au lieu d'afficher 52 métriques en permanence, l'interface :
- Calcule les Z-Scores pour détecter les anomalies (écart > 2σ)
- Priorise selon l'importance clinique (poids 1-3)
- N'affiche que les top 3 anomalies
- Génère un insight actionnable via LLM

## Architecture

```
Mobile ←→ Backend
  ↓         ↓
Baselines  Priority Engine
  ↓         (μ, σ, poids)
Z-Score      ↓
Calculator  LLM
  ↓         ↓
Anomalies → Insight
  ↓
PulseOrb + Card
```

## Composants Principaux

### 1. PulseOrb (`src/components/PulseOrb.tsx`)

Sphère animée qui représente l'état global :
- **Calm** (Vert) : Pulse lent et fluide, tout va bien
- **Warning** (Orange) : Pulse erratique, attention requise
- **Alert** (Rouge) : Pulse lent, repos nécessaire

Utilise `react-native-reanimated` pour des animations 60fps sur le thread UI.

### 2. AmbientInsightCard (`src/components/AmbientInsightCard.tsx`)

Carte unique qui affiche :
- L'insight principal (grande typographie 22px)
- Bordure colorée selon l'urgence
- Nombre d'anomalies détectées
- Tap gesture pour drill-down

### 3. ZScoreCalculator (`src/services/ZScoreCalculator.ts`)

Moteur de détection d'anomalies :
```typescript
Z = (valeur - μ) / σ
Priority = |Z| × poids
```

Filtre : garde uniquement |Z| > 2

### 4. useAnomalyDetection (`src/hooks/useAnomalyDetection.ts`)

Hook qui combine :
- Métriques actuelles (via `useCurrentMetrics`)
- Baselines (via `useBaselines`)
- Calcul des anomalies (via `ZScoreCalculator`)

### 5. useMainInsight (`src/hooks/useMainInsight.ts`)

Hook qui :
- Prend les top 3 anomalies
- Appelle le backend `/api/insights/prioritized`
- Retourne un insight "Concierge" ultra-court (≤150 chars)

## Backend

### PriorityEngine (`backend/priority_engine.py`)

Calcule les baselines :
- μ (moyenne) sur 14 derniers jours
- σ (écart-type) sur 14 derniers jours
- Poids par métrique (1-3)

### Endpoints

#### GET `/api/baselines/{user_id}`
Retourne les baselines pour le calcul mobile des Z-Scores.

#### POST `/api/insights/prioritized`
Génère un insight basé sur les top 3 anomalies.

Body :
```json
{
  "user_id": "uuid",
  "anomalies": [
    {
      "metric": "hrv",
      "value": 45.2,
      "z_score": -2.35,
      "weight": 3,
      "direction": "below"
    }
  ]
}
```

Response :
```json
{
  "status": "success",
  "insight": {
    "content": "HRV bas détectée. Priorisez le repos et évitez le stress.",
    "state": "warning",
    "priority": 1
  }
}
```

## Écrans

### 1. Home (`app/(tabs)/index.tsx`)

Interface minimaliste :
- Header avec date et prénom
- PulseOrb centré
- Message d'état
- Carte insight unique
- Timeline des anomalies (optionnel)

### 2. Details (`app/details.tsx`)

Drill-down en 3 niveaux :
- **Niveau 1** : État global (calm/warning/alert)
- **Niveau 2** : Détails des anomalies (Z-Score, baseline, priorité)
- **Niveau 3** : Toutes les métriques (52 critères)

## Poids des Métriques

### Poids 3 (Critique)
- HRV (variabilité cardiaque)
- Fréquence cardiaque au repos
- Température corporelle
- Durée de sommeil

### Poids 2 (Important)
- Calories actives
- Stress
- Glycémie
- SpO2

### Poids 1 (Info)
- Pas
- Calories totales
- Hydratation
- Distance
- Étages montés
- Poids
- Fréquence respiratoire
- Caféine

## Accessibilité

Toutes les interfaces respectent les standards WCAG 2.1 :
- Labels VoiceOver descriptifs
- Rôles sémantiques (`button`, `text`, `image`)
- Hints pour les interactions
- Contraste élevé (WCAG AAA)

## Performance

- Z-Score calculations : < 10ms (JavaScript pur)
- Baselines cachées : 24h (peu d'appels backend)
- Animation Orb : 60fps (UI thread via reanimated)
- Insight API : ~1-2s (LLM génération)

## Configuration

### Variables d'environnement (mobile)

```bash
EXPO_PUBLIC_API_URL=http://localhost:9000
```

### Variables d'environnement (backend)

```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=xxx
OPENAI_API_KEY=xxx
```

## Tests

### Tests unitaires

```bash
cd mobile
npm test
```

Tests couverts :
- Calcul Z-Score
- Détection d'anomalies
- Tri par priorité
- États globaux (calm/warning/alert)

## Migration depuis l'ancienne interface

L'ancienne interface (Dashboard) est toujours accessible via les onglets "Historique" et "Profil". La transition est progressive :
- Écran principal : Ambient Concierge (nouveau)
- Historique : Graphiques classiques (ancien)
- Profil : Paramètres (ancien)

## Roadmap

### Phase 1 (Actuelle) ✅
- Backend baselines + Z-Score Engine
- PulseOrb + AmbientHomeScreen
- Endpoint insights prioritized
- Écran détails

### Phase 2 (À venir)
- Notifications push pour alertes
- Widget iOS/Android
- Mode offline avec cache local
- Tendances prédictives (ML)

### Phase 3 (Future)
- Voice interface (Siri/Google Assistant)
- Apple Watch app minimaliste
- Partage avec médecin
- Rapport hebdomadaire automatique

## Support

Pour toute question ou bug, ouvrir une issue sur GitHub ou contacter l'équipe Pulse.

---

**Version** : 1.0.0  
**Date** : Janvier 2026  
**Compatibilité** : Expo SDK 54, React Native 0.81.5, iOS 13+, Android 8+
