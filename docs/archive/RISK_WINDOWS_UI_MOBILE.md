# Risk Windows UI Mobile : Implémentation Complète

**Date:** 2026-01-30  
**Status:** ✅ Implémenté  
**Priorité:** HAUTE (UX proactif)  

---

## 🎯 Objectif

Afficher les **risk windows enrichis** (créneaux à risque + recommandations agenda) dans l'application mobile avec un design moderne et une UX intuitive.

---

## 📁 Fichiers Créés/Modifiés

| Fichier | Action | Description |
|---------|--------|-------------|
| `mobile/src/hooks/useDailyEnergy.ts` | ✅ Modifié | Ajout interfaces `ConflictingEvent`, `CalendarRecommendation`, update `RiskWindow` |
| `mobile/src/components/RiskWindowWithRecommendation.tsx` | ✅ Créé | Nouveau composant pour affichage enrichi |
| `mobile/src/components/DailyEnergyCard.tsx` | ✅ Modifié | Utilise nouveau composant au lieu de l'affichage classique |
| `RISK_WINDOWS_UI_MOBILE.md` | ✅ Créé | Ce fichier (documentation) |

---

## 📝 Nouvelles Interfaces TypeScript

### `ConflictingEvent`

```typescript
export interface ConflictingEvent {
  title: string;      // "Réunion client"
  start: string;      // ISO timestamp
  importance: number; // 0-3 (0=personnel, 1=normal, 2=important, 3=critique)
}
```

### `CalendarRecommendation`

```typescript
export interface CalendarRecommendation {
  type: 'prepare' | 'reschedule' | 'accept';
  action: string;     // "Prends une pause 30 min avant 'Réunion client'"
  details: string;    // "15 min de marche + snack protéiné"
  reason: string;     // "Événement critique durant un creux d'énergie"
}
```

### `RiskWindow` (mis à jour)

```typescript
export interface RiskWindow {
  from: string;       // "16:00"
  to: string;         // "18:00"
  risk: string;       // "dip"
  text: string;       // "Baisse d'énergie probable"
  
  // 🆕 Enrichissement Agenda (V2)
  has_conflict?: boolean;                   // true si événement(s) dans le creux
  conflicting_events?: ConflictingEvent[];  // Liste des événements en conflit
  recommendation?: CalendarRecommendation;  // Recommandation intelligente
}
```

---

## 🎨 Composant `RiskWindowWithRecommendation`

### Logic

Le composant gère **2 modes d'affichage** :

#### Mode 1 : Classique (sans conflit)

Si `has_conflict === undefined` ou `false` :

```
┌────────────────────────────────────┐
│ 📉 Prévision creux d'énergie       │
│                                    │
│ 🕐 16:00 - 18:00                   │
│    Baisse d'énergie attendue       │
└────────────────────────────────────┘
```

**Style :** Gris, discret, informe sans alarmer.

---

#### Mode 2 : Enrichi (avec conflit + recommandation)

Si `has_conflict === true` :

```
┌────────────────────────────────────┐
│ ⚠️ Creux prévu : 16:00 - 18:00     │
│    Réunion client durant ce creux  │
│                                    │
│ ┌────────────────────────────────┐ │
│ │ 💡 Recommandation Pulse        │ │
│ │                                │ │
│ │ 👉 Prends une pause 30 min     │ │
│ │    avant 'Réunion client'      │ │
│ │                                │ │
│ │ ▶ Voir détails                 │ │ ← Expandable
│ └────────────────────────────────┘ │
└────────────────────────────────────┘
```

**Expandable :**

```
┌────────────────────────────────────┐
│ │ ▼ Masquer détails              │ │
│ │                                │ │
│ │ 15 min de marche + snack       │ │
│ │ protéiné                       │ │
│ │                                │ │
│ │ Raison: Événement critique     │ │
│ │ durant un creux d'énergie      │ │
│ └────────────────────────────────┘ │
│                                    │
│ Événements concernés:              │
│  • Réunion client (16:30)          │
└────────────────────────────────────┘
```

**Style :** 
- Alerte rouge (`#ef4444`) pour le creux
- Couleur dynamique selon type de recommandation :
  - **Prepare** (critique) : Amber `#f59e0b`
  - **Reschedule** (optimisation) : Blue `#3b82f6`
  - **Accept** (accepter) : Gray `#6b7280`

---

### Icônes selon Type

| Type | Icône | Couleur | Signification |
|------|-------|---------|---------------|
| `prepare` | ⚠️ AlertTriangle | Amber `#f59e0b` | Événement critique, prépare-toi |
| `reschedule` | 📅 Calendar | Blue `#3b82f6` | Suggère de déplacer |
| `accept` | ✅ CheckCircle | Gray `#6b7280` | Accepte la situation |

---

### Props

```typescript
interface RiskWindowWithRecommendationProps {
  window: RiskWindow;  // Risk window avec enrichissement éventuel
  index: number;       // Index pour key React
}
```

---

## 🔧 Intégration dans `DailyEnergyCard`

### Avant

```tsx
{/* Risk window */}
{energy.risk_windows.length > 0 && (
  <View style={styles.riskSection}>
    <View style={styles.riskHeader}>
      <TrendingDown size={14} color="#9ca3af" strokeWidth={2} />
      <Text style={styles.riskTitle}>Prévision creux d'énergie</Text>
    </View>
    {energy.risk_windows.map((window, index) => (
      <View key={index} style={styles.riskItem}>
        <Clock size={12} color="#9ca3af" strokeWidth={2} />
        <Text style={styles.riskTime}>{window.from} - {window.to}</Text>
        <Text style={styles.riskText}>{window.text}</Text>
      </View>
    ))}
  </View>
)}
```

### Après

```tsx
{/* Risk window avec enrichissement agenda */}
{energy.risk_windows.length > 0 && energy.risk_windows.map((window, index) => (
  <RiskWindowWithRecommendation 
    key={index}
    window={window}
    index={index}
  />
))}
```

**Avantages :**
- ✅ Plus simple (délégaté au composant)
- ✅ Gère automatiquement classique vs enrichi
- ✅ Expandable intégré
- ✅ Rétrocompatible (si API ne retourne pas has_conflict, affichage classique)

---

## 🎨 Design System

### Couleurs

| Élément | Couleur | Usage |
|---------|---------|-------|
| Alerte creux | `#ef4444` (red) | Signale le conflit |
| Prepare | `#f59e0b` (amber) | Événement critique |
| Reschedule | `#3b82f6` (blue) | Optimisation suggérée |
| Accept | `#6b7280` (gray) | Accepter situation |
| Background recommendation | `#1f293715` (dark transparent) | Fond pill |
| Border recommendation | Couleur type + `40` opacity | Border pill |

### Typographie

| Élément | Font Size | Weight | Color |
|---------|-----------|--------|-------|
| Alert title | 13px | 700 | `#ef4444` |
| Alert text | 13px | 500 | `#fca5a5` (lighter red) |
| Recommendation label | 12px | 700 | `#9ca3af` |
| Recommendation action | 14px | 700 | Couleur type |
| Details text | 13px | 500 | `#d1d5db` |
| Details reason | 12px | 500 | `#9ca3af` (italic) |

### Spacing

- Gap entre sections : `12px`
- Padding recommendation pill : `12px`
- Gap entre header et action : `8px`
- Border radius recommendation : `12px`

---

## 📱 Comportement UX

### États

1. **Chargement** : Affiche ActivityIndicator (géré par `DailyEnergyCard`)
2. **Pas de risk window** : Composant non affiché
3. **Risk window classique** : Affichage minimaliste gris
4. **Risk window enrichi (collapsed)** : Alerte + recommandation compacte
5. **Risk window enrichi (expanded)** : + détails + événements

### Interactions

- **Tap "▶ Voir détails"** → Expand détails
- **Tap "▼ Masquer détails"** → Collapse détails
- Pas d'action CTA pour le moment (future: deep link calendrier)

### Animations

- Pas d'animation pour V1 (keep it simple)
- Future: FadeIn pour l'expansion des détails

---

## 🧪 Test Cases

### Test 1 : Pas de risk window

**Données :**
```json
{
  "risk_windows": []
}
```

**Résultat attendu :** Composant non affiché

---

### Test 2 : Risk window classique (sans conflit)

**Données :**
```json
{
  "risk_windows": [
    {
      "from": "16:00",
      "to": "18:00",
      "text": "Baisse d'énergie attendue"
    }
  ]
}
```

**Résultat attendu :** 
- Affichage gris minimaliste
- Pas de recommandation
- Texte : "📉 Prévision creux d'énergie"

---

### Test 3 : Risk window enrichi (prepare)

**Données :**
```json
{
  "risk_windows": [
    {
      "from": "16:00",
      "to": "18:00",
      "text": "⚠️ Réunion client prévu durant ce creux",
      "has_conflict": true,
      "recommendation": {
        "type": "prepare",
        "action": "Prends une pause 30 min avant 'Réunion client'",
        "details": "15 min de marche + snack protéiné",
        "reason": "Événement critique durant un creux d'énergie"
      },
      "conflicting_events": [
        {
          "title": "Réunion client",
          "start": "2026-01-30T16:30:00Z",
          "importance": 3
        }
      ]
    }
  ]
}
```

**Résultat attendu :**
- Alerte rouge ⚠️ avec créneau
- Recommandation amber (prepare) avec icône AlertTriangle
- Action visible
- "▶ Voir détails" expandable
- Si expanded : détails + événement "Réunion client (16:30)"

---

### Test 4 : Risk window enrichi (reschedule)

**Données :**
```json
{
  "recommendation": {
    "type": "reschedule",
    "action": "Déplace 'Call équipe' hors du creux",
    ...
  }
}
```

**Résultat attendu :**
- Recommandation blue (reschedule) avec icône Calendar

---

### Test 5 : Risk window enrichi (accept)

**Données :**
```json
{
  "recommendation": {
    "type": "accept",
    "action": "3 événements durant le creux : Accepte la baisse de rythme",
    ...
  }
}
```

**Résultat attendu :**
- Recommandation gray (accept) avec icône CheckCircle

---

## ✅ Checklist Déploiement

### Phase 1 : Implémentation (DONE ✅)

- [x] Update `RiskWindow` interface (nouveaux champs)
- [x] Créer `ConflictingEvent` interface
- [x] Créer `CalendarRecommendation` interface
- [x] Créer composant `RiskWindowWithRecommendation`
- [x] Update `DailyEnergyCard` (utilise nouveau composant)
- [x] Cleanup styles inutilisés
- [x] Documentation `RISK_WINDOWS_UI_MOBILE.md`

### Phase 2 : Testing (TODO)

- [ ] Test affichage sans risk window
- [ ] Test affichage risk window classique
- [ ] Test affichage risk window enrichi (prepare)
- [ ] Test affichage risk window enrichi (reschedule)
- [ ] Test affichage risk window enrichi (accept)
- [ ] Test expand/collapse détails
- [ ] Test affichage événements (si >1)
- [ ] Test sur iOS
- [ ] Test sur Android

### Phase 3 : Refinement (TODO)

- [ ] Animations expand/collapse (FadeIn)
- [ ] Haptic feedback sur tap expand
- [ ] CTA actionnable (deep link calendrier future)
- [ ] Accessibility (voiceover, labels)
- [ ] Dark mode verification
- [ ] Responsive (différentes tailles écran)

### Phase 4 : Déploiement (TODO)

- [ ] Merge PR
- [ ] Deploy avec backend sync
- [ ] Monitor erreurs Sentry
- [ ] A/B test : impact engagement
- [ ] Feedback users (in-app survey)

---

## 🚀 Évolutions Futures (V3+)

### Deep Links Calendar

Ajouter CTA actionnable selon type :

**Prepare :**
```tsx
<TouchableOpacity 
  onPress={() => scheduleReminder(window.from, 30)} // 30 min avant
  style={styles.ctaButton}
>
  <Text>⏰ Configurer rappel</Text>
</TouchableOpacity>
```

**Reschedule :**
```tsx
<TouchableOpacity 
  onPress={() => openCalendarWithSuggestions(event, suggestedSlots)}
  style={styles.ctaButton}
>
  <Text>📅 Déplacer dans calendrier</Text>
</TouchableOpacity>
```

---

### Animations

```tsx
import { FadeIn, SlideInDown } from 'react-native-reanimated';

// Expand avec animation
{expanded && (
  <Animated.View 
    entering={FadeIn.duration(200)}
    style={styles.detailsSection}
  >
    ...
  </Animated.View>
)}
```

---

### Analytics

Tracker interactions :

```typescript
// Event: risk_window_viewed
analytics.track('risk_window_viewed', {
  has_conflict: window.has_conflict,
  recommendation_type: window.recommendation?.type,
  conflicting_events_count: window.conflicting_events?.length,
});

// Event: risk_window_expanded
analytics.track('risk_window_expanded', {
  recommendation_type: window.recommendation?.type,
});

// Event: risk_window_cta_clicked (future)
analytics.track('risk_window_cta_clicked', {
  action: 'schedule_reminder' | 'open_calendar',
  recommendation_type: window.recommendation?.type,
});
```

---

## 📊 Métriques à Monitorer

### Engagement

- % users qui voient un risk window enrichi
- % users qui expand les détails
- Temps moyen passé sur la carte avec risk window enrichi
- Click rate sur CTA (future)

### Performance

- Render time `RiskWindowWithRecommendation` < 16ms
- Memory footprint acceptable (pas de leak)
- Pas de lag lors de l'expand

### Qualité

- Crash rate lié au composant (Sentry)
- Feedback négatif mentionnant risk windows
- A/B test : engagement global avec vs sans enrichissement

---

## ✨ Résultat Final

**Avant :** Info passive grise

**Après :** Assistant proactif coloré avec recommandations intelligentes

**L'utilisateur voit immédiatement :**
1. ⚠️ Alerte conflit
2. 💡 Recommandation actionnable
3. 📋 Détails expandables
4. 📅 Événements concernés

**UX Proactive → Engagement Maximum !** 🚀

---

**Implémentation UI mobile complète ! Prêt pour testing.** ✅
