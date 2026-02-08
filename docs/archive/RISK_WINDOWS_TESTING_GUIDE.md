# Risk Windows + Agenda : Guide de Test Complet

**Date:** 2026-01-30  
**Status:** ✅ Tests créés, prêts à exécuter  

---

## 🎯 Objectif

Valider l'implémentation complète **backend + mobile** des risk windows enrichis avec agenda.

---

## 📁 Fichiers de Test Créés

| Fichier | Type | Description |
|---------|------|-------------|
| `backend/tests/test_risk_windows_agenda.py` | Backend | Tests Python pour enrichissement agenda |
| `mobile/src/components/__tests__/RiskWindowWithRecommendation.test.tsx` | Mobile | Tests React Native pour composant UI |
| `RISK_WINDOWS_TESTING_GUIDE.md` | Doc | Ce guide |

---

## 🧪 Tests Backend

### Fichier: `backend/tests/test_risk_windows_agenda.py`

**Contient 5 tests :**

1. **Classification Événements** : Valide que les événements sont bien classifiés par importance (0-3)
2. **Génération Recommandations** : Vérifie que le bon type de recommandation est généré
3. **Enrichissement Risk Window** : Teste l'ajout des événements dans le risk window
4. **Risk Windows Complet** : Teste la génération complète avec différents niveaux d'énergie
5. **Fail-Safe Erreur DB** : Vérifie que les erreurs DB ne cassent pas l'app

### Prérequis

```bash
# Définir un user_id de test avec des événements calendrier
export TEST_USER_ID="<uuid-user-avec-events>"
```

**Note :** Les tests 1, 2 et 5 fonctionnent **sans** TEST_USER_ID. Les tests 3 et 4 seront skipped si TEST_USER_ID n'est pas défini.

### Exécution

```bash
cd /Users/dannezri/Desktop/Pulse/backend/tests
python test_risk_windows_agenda.py
```

### Résultats Attendus

```
🧪 RISK WINDOWS + AGENDA TEST SUITE
====================================

=== TEST: Classification Événements ===
   ✅ 'Réunion client important' → critique (3)
   ✅ 'Call équipe' → important (2)
   ✅ 'Gym' → normal (1)
   ✅ 'Déjeuner' → personnel (0)
✅ PASS: Tous les événements correctement classifiés

=== TEST: Génération Recommandations ===
   ✅ Événement critique → prepare
   ✅ Événement important → reschedule
   ✅ Plusieurs événements (3) → accept
✅ PASS: Toutes les recommandations correctes

=== TEST: Enrichissement Risk Window ===
   ✅ Pas de conflit détecté (comme attendu)
   ✅ Conflit détecté dans créneau 16h-18h
      Événements: 1
      Type: prepare
✅ PASS: Enrichissement fonctionne

=== TEST: Risk Windows Complet ===
   ✅ Énergie haute:
      Créneau: 17:00 - 19:00
      ⚠️ Conflit détecté!
      Recommandation: prepare
✅ PASS: Risk windows générés avec enrichissement

=== TEST: Fail-Safe Erreur DB ===
   ✅ Fail-safe activé: risk_window classique retourné
✅ PASS

📊 TEST RESULTS SUMMARY
====================================
✅ PASS | Classification Événements
✅ PASS | Génération Recommandations
✅ PASS | Enrichissement Risk Window
✅ PASS | Risk Windows Complet
✅ PASS | Fail-Safe Erreur DB
------------------------------------
Total: 5/5 passed
🎉 ALL TESTS PASSED
```

---

## 🧪 Tests Mobile

### Fichier: `mobile/src/components/__tests__/RiskWindowWithRecommendation.test.tsx`

**Contient 6 suites de tests :**

1. **Affichage Classique** : Risk window sans conflit
2. **Affichage Enrichi - Prepare** : Recommandation type "prepare"
3. **Affichage Enrichi - Reschedule** : Recommandation type "reschedule"
4. **Affichage Enrichi - Accept** : Recommandation type "accept"
5. **Edge Cases** : Cas limites (pas de recommendation, events vides, etc.)
6. **Snapshots** : Snapshots pour regression testing

### Prérequis

```bash
cd /Users/dannezri/Desktop/Pulse/mobile

# Installer dependencies si nécessaire
npm install

# Installer @testing-library/react-native si pas déjà fait
npm install --save-dev @testing-library/react-native @testing-library/jest-native
```

### Configuration Jest

Vérifier que `package.json` contient :

```json
{
  "jest": {
    "preset": "react-native",
    "setupFilesAfterEnv": ["@testing-library/jest-native/extend-expect"],
    "transformIgnorePatterns": [
      "node_modules/(?!(react-native|@react-native|lucide-react-native)/)"
    ]
  }
}
```

### Exécution

```bash
cd /Users/dannezri/Desktop/Pulse/mobile

# Tous les tests
npm test

# Seulement RiskWindowWithRecommendation
npm test RiskWindowWithRecommendation

# Avec coverage
npm test -- --coverage

# Watch mode
npm test -- --watch
```

### Résultats Attendus

```
PASS  src/components/__tests__/RiskWindowWithRecommendation.test.tsx
  RiskWindowWithRecommendation
    Affichage Classique
      ✓ affiche le risk window classique quand has_conflict est absent (45ms)
      ✓ affiche le risk window classique quand has_conflict est false (23ms)
    Affichage Enrichi - Type Prepare
      ✓ affiche l'alerte creux d'énergie (31ms)
      ✓ affiche la recommandation Pulse (28ms)
      ✓ affiche le bouton expand détails (22ms)
      ✓ expand/collapse les détails au tap (89ms)
      ✓ affiche les événements en conflit quand expanded (67ms)
    Affichage Enrichi - Type Reschedule
      ✓ affiche la recommandation reschedule (29ms)
    Affichage Enrichi - Type Accept
      ✓ affiche la recommandation accept (26ms)
      ✓ affiche tous les événements en conflit quand expanded (71ms)
    Edge Cases
      ✓ gère has_conflict=true mais pas de recommendation (fallback) (24ms)
      ✓ gère conflicting_events vide (32ms)
    Snapshots
      ✓ snapshot classique (18ms)
      ✓ snapshot enrichi prepare (21ms)

Test Suites: 1 passed, 1 total
Tests:       14 passed, 14 total
Snapshots:   2 passed, 2 total
Time:        2.456s
```

---

## 📱 Tests Manuels Mobile

### Setup Test

1. **Créer événement de test :**
   - Aller dans l'app calendrier mobile
   - Créer "Réunion client important" à 16h30 aujourd'hui
   - Sync avec Supabase (attendre quelques secondes)

2. **Forcer calcul daily_energy :**
   ```bash
   # Backend
   cd /Users/dannezri/Desktop/Pulse/backend
   python
   
   >>> from services.latent_state_service import LatentStateService
   >>> from supabase_client import get_supabase_client
   >>> 
   >>> service = LatentStateService(get_supabase_client())
   >>> service.calculate_all_states(
   ...     user_id="<your-user-id>",
   ...     force_refresh=True
   ... )
   ```

3. **Ouvrir app mobile :**
   - Aller sur l'écran Brief (accueil)
   - Scroll jusqu'à la carte "Ton énergie aujourd'hui"

### Cas de Test

#### Test 1 : Risk Window Classique (sans événement)

**Setup :** Pas d'événement entre 16h-18h

**Résultat attendu :**
```
┌────────────────────────────────────┐
│ 📉 Prévision creux d'énergie       │
│ 🕐 16:00 - 18:00                   │
│    Baisse d'énergie attendue       │
└────────────────────────────────────┘
```

**Vérifier :**
- ✅ Texte gris (#9ca3af)
- ✅ Pas de recommandation visible
- ✅ Style minimaliste

---

#### Test 2 : Risk Window Enrichi (événement critique)

**Setup :** Événement "Réunion client" à 16h30

**Résultat attendu :**
```
┌────────────────────────────────────┐
│ ⚠️ Creux prévu : 16:00 - 18:00     │
│    Réunion client durant ce creux  │
│                                    │
│ ┌────────────────────────────────┐ │
│ │ 💡 Recommandation Pulse        │ │
│ │ ⚠️ [AlertTriangle icon amber]  │ │
│ │                                │ │
│ │ 👉 Prends une pause 30 min     │ │
│ │    avant 'Réunion client'      │ │
│ │                                │ │
│ │ ▶ Voir détails                 │ │
│ └────────────────────────────────┘ │
└────────────────────────────────────┘
```

**Vérifier :**
- ✅ Alerte rouge (#ef4444)
- ✅ Recommandation amber (#f59e0b)
- ✅ Icône AlertTriangle
- ✅ Texte "Prends une pause 30 min avant"
- ✅ Bouton "▶ Voir détails" présent

---

#### Test 3 : Expand Détails

**Action :** Tap sur "▶ Voir détails"

**Résultat attendu :**
```
┌────────────────────────────────────┐
│ │ ▼ Masquer détails              │ │
│ │                                │ │
│ │ 15 min de marche + snack       │ │
│ │ protéiné + hydratation         │ │
│ │                                │ │
│ │ Raison: Événement critique     │ │
│ │ durant un creux d'énergie      │ │
│ └────────────────────────────────┘ │
│                                    │
│ Événements concernés:              │
│  • Réunion client (16:30)          │
└────────────────────────────────────┘
```

**Vérifier :**
- ✅ Détails visibles
- ✅ Raison affichée (italic)
- ✅ Événements listés avec heure
- ✅ Bouton changé en "▼ Masquer détails"

---

#### Test 4 : Collapse Détails

**Action :** Tap sur "▼ Masquer détails"

**Résultat attendu :**
- ✅ Détails cachés
- ✅ Retour à l'état initial compact
- ✅ Bouton redevient "▶ Voir détails"

---

#### Test 5 : Type Reschedule (événement important)

**Setup :** Événement "Call équipe" à 17h

**Résultat attendu :**
- ✅ Recommandation blue (#3b82f6)
- ✅ Icône Calendar
- ✅ Texte "Déplace 'Call équipe' hors du creux"

---

#### Test 6 : Type Accept (plusieurs événements)

**Setup :** 3 événements entre 16h-18h

**Résultat attendu :**
- ✅ Recommandation gray (#6b7280)
- ✅ Icône CheckCircle
- ✅ Texte "3 événements durant le creux : Accepte la baisse"

---

### Checklist Visuelle

- [ ] **Spacing** : Paddings et gaps corrects (12px, 16px)
- [ ] **Typography** : Font sizes (12-14px), weights (500-700)
- [ ] **Colors** : Couleurs dynamiques selon type
- [ ] **Icons** : Icônes correctes (AlertTriangle/Calendar/CheckCircle)
- [ ] **Animations** : Pas de lag sur expand/collapse
- [ ] **Responsive** : Fonctionne sur différentes tailles écran
- [ ] **Dark mode** : Contraste suffisant

---

## 📊 Tests de Performance

### Backend

```bash
cd /Users/dannezri/Desktop/Pulse/backend

# Test latency enrichissement
python
>>> import time
>>> from daily_energy_engine import enrich_risk_window_with_calendar
>>> 
>>> risk_window = {'from': '16:00', 'to': '18:00', 'risk': 'dip', 'text': 'Test'}
>>> 
>>> start = time.time()
>>> result = enrich_risk_window_with_calendar(risk_window, '<user-id>', '2026-01-30')
>>> latency = (time.time() - start) * 1000
>>> print(f"Latency: {latency:.2f}ms")
```

**Seuil acceptable :** < 200ms

---

### Mobile

```bash
cd /Users/dannezri/Desktop/Pulse/mobile

# Profiling React Native
npm install --save-dev @welldone-software/why-did-you-render

# Measure render time
npm test -- --coverage
```

**Seuil acceptable :** 
- First render : < 100ms
- Re-render (expand) : < 50ms

---

## 🐛 Debugging

### Backend

```python
# Activer logs détaillés
import logging
logging.basicConfig(level=logging.DEBUG)

from daily_energy_engine import generate_risk_windows

result = generate_risk_windows(
    energy=0.65,
    debt_hours=2,
    recovery=0.60,
    user_id="<user-id>",
    target_date="2026-01-30"
)

print(json.dumps(result, indent=2, ensure_ascii=False))
```

### Mobile

```tsx
// Ajouter logs dans le composant
console.log('[RiskWindow] window:', window);
console.log('[RiskWindow] has_conflict:', window.has_conflict);
console.log('[RiskWindow] recommendation:', window.recommendation);
```

---

## ✅ Checklist Complète

### Backend Tests

- [ ] Test classification événements (pass)
- [ ] Test génération recommandations (pass)
- [ ] Test enrichissement risk window (pass)
- [ ] Test risk windows complet (pass)
- [ ] Test fail-safe erreur DB (pass)
- [ ] Test performance enrichissement < 200ms

### Mobile Tests

- [ ] Tests unitaires (14/14 pass)
- [ ] Test affichage classique (manuel)
- [ ] Test affichage enrichi prepare (manuel)
- [ ] Test affichage enrichi reschedule (manuel)
- [ ] Test affichage enrichi accept (manuel)
- [ ] Test expand/collapse (manuel)
- [ ] Test performance render < 100ms
- [ ] Test iOS
- [ ] Test Android

### Tests Intégration

- [ ] Créer événement → Voir conflit mobile (E2E)
- [ ] Supprimer événement → Conflit disparaît (E2E)
- [ ] Modifier heure événement → Conflit mis à jour (E2E)

---

## 🚀 Prochaines Étapes

1. **Exécuter tous les tests** ✅
2. **Corriger les tests qui échouent** (si nécessaire)
3. **Screenshots tests manuels** (pour doc/PR)
4. **Merge PR** avec tests passés
5. **Deploy** + monitor

---

**Tests créés et prêts ! Exécutez-les pour valider l'implémentation.** 🧪
