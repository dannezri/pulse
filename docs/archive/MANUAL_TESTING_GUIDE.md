# 📱 Guide de Test Manuel - Risk Windows avec Agenda

**Date:** 2026-01-30  
**Feature:** Enrichissement Risk Windows avec recommandations agenda  
**Status:** Alternative aux tests Jest (problème jest-expo)  

---

## 🎯 Objectif

Valider manuellement que les risk windows enrichis avec les recommandations agenda fonctionnent correctement sur l'app mobile.

---

## ✅ Prérequis

1. **Backend déployé** avec les modifications `daily_energy_engine.py`
2. **Mobile app buildée** avec `RiskWindowWithRecommendation.tsx`
3. **Compte test** avec accès au calendrier
4. **Device** ou simulateur iOS/Android

---

## 🧪 Scénarios de Test

### Scénario 1 : Risk Window Classique (Sans Conflit)

**Setup :**
- Aucun événement dans le calendrier aujourd'hui
- Ou événements en dehors des heures 14h-20h

**Actions :**
1. Ouvrir l'app Pulse
2. Naviguer vers l'écran Home
3. Scroller jusqu'à la carte "Énergie du jour"
4. Observer la section "Prévision creux d'énergie"

**Résultat Attendu :**
```
📉 Prévision creux d'énergie
🕐 16:00 - 18:00 Baisse d'énergie probable
```

**Validation :**
- [ ] Le risk window s'affiche avec l'icône horloge
- [ ] Le texte "Baisse d'énergie probable" est visible
- [ ] Pas de recommandation affichée
- [ ] Design classique (pas de pill coloré)

**Screenshot :** 📸 `test_1_classic_risk_window.png`

---

### Scénario 2 : Événement Critique (Prepare)

**Setup :**
1. Créer un événement dans le calendrier :
   - Titre : "Réunion client stratégique"
   - Date : Aujourd'hui
   - Heure : 16h30 - 17h30

**Actions :**
1. Rafraîchir l'app (pull to refresh sur Home)
2. Observer la carte "Énergie du jour"
3. Observer la section "Prévision creux d'énergie"

**Résultat Attendu :**
```
📉 Prévision creux d'énergie
🔻 16:00 - 18:00 ⚠️ Baisse d'énergie probable (conflit agenda)

[Pill Orange/Ambre]
⚠️ 💡 Recommandation Pulse
   👉 Prends une pause 30 min avant 'Réunion client stratégique'
   [▼ Voir détails]
```

**Validation :**
- [ ] Le risk window affiche "⚠️" et "(conflit agenda)"
- [ ] La recommandation s'affiche dans un pill orange/ambre
- [ ] L'icône AlertTriangle est visible
- [ ] Le texte "Prends une pause 30 min avant" est visible
- [ ] Le bouton "Voir détails" est présent

**Actions Supplémentaires :**
4. Taper sur "Voir détails"

**Résultat Attendu (Expanded) :**
```
[Pill Orange/Ambre - Expanded]
⚠️ 💡 Recommandation Pulse
   👉 Prends une pause 30 min avant 'Réunion client stratégique'
   
   15 min de marche rapide, hydratation et un snack protéiné léger.
   
   Événements en conflit :
   • Réunion client stratégique (16:30)
   
   [▲ Masquer détails]
```

**Validation (Expanded) :**
- [ ] Les détails s'affichent avec animation
- [ ] Le texte de préparation est visible
- [ ] L'événement en conflit est listé avec l'heure
- [ ] Le bouton devient "Masquer détails"

**Actions Supplémentaires :**
5. Re-taper sur "Masquer détails"

**Validation (Collapse) :**
- [ ] Les détails se cachent avec animation
- [ ] Retour à l'état initial (recommandation courte)

**Screenshot :** 📸 `test_2_critical_event_prepare.png`, `test_2_critical_event_expanded.png`

---

### Scénario 3 : Événement Important (Reschedule)

**Setup :**
1. Supprimer l'événement du Scénario 2
2. Créer un nouvel événement :
   - Titre : "Call équipe produit"
   - Date : Aujourd'hui
   - Heure : 17h00 - 17h30

**Actions :**
1. Rafraîchir l'app
2. Observer la section "Prévision creux d'énergie"

**Résultat Attendu :**
```
📉 Prévision creux d'énergie
🔻 16:00 - 18:00 ⚠️ Baisse d'énergie probable (conflit agenda)

[Pill Bleu]
📅 💡 Recommandation Pulse
   👉 Déplace 'Call équipe produit' hors du creux d'énergie
   [▼ Voir détails]
```

**Validation :**
- [ ] Le pill est bleu (couleur différente du critique)
- [ ] L'icône Calendar est visible
- [ ] Le texte "Déplace ... hors du creux" est visible
- [ ] Le bouton "Voir détails" est présent

**Actions Supplémentaires :**
3. Taper sur "Voir détails"

**Résultat Attendu (Expanded) :**
```
[Pill Bleu - Expanded]
📅 💡 Recommandation Pulse
   👉 Déplace 'Call équipe produit' hors du creux d'énergie
   
   Essaie de le planifier en dehors de 16:00-18:00 pour optimiser ta performance.
   
   Événements en conflit :
   • Call équipe produit (17:00)
   
   [▲ Masquer détails]
```

**Validation (Expanded) :**
- [ ] Les détails suggèrent de replanifier
- [ ] L'événement en conflit est listé
- [ ] Le ton est suggéré, pas impératif

**Screenshot :** 📸 `test_3_important_event_reschedule.png`

---

### Scénario 4 : Événement Normal (Reschedule Léger)

**Setup :**
1. Supprimer l'événement du Scénario 3
2. Créer un nouvel événement :
   - Titre : "Gym"
   - Date : Aujourd'hui
   - Heure : 16h30 - 17h30

**Actions :**
1. Rafraîchir l'app
2. Observer la section "Prévision creux d'énergie"

**Résultat Attendu :**
```
📉 Prévision creux d'énergie
🔻 16:00 - 18:00 ⚠️ Baisse d'énergie probable (conflit agenda)

[Pill Bleu]
📅 💡 Recommandation Pulse
   👉 Déplace 'Gym' en dehors du creux si possible
   [▼ Voir détails]
```

**Validation :**
- [ ] Le pill est bleu (type reschedule)
- [ ] Le ton est plus léger ("si possible")
- [ ] Le bouton "Voir détails" est présent

**Actions Supplémentaires :**
3. Taper sur "Voir détails"

**Résultat Attendu (Expanded) :**
```
[Pill Bleu - Expanded]
📅 💡 Recommandation Pulse
   👉 Déplace 'Gym' en dehors du creux si possible
   
   Profite de ce moment pour une activité plus légère ou une vraie pause.
   
   Événements en conflit :
   • Gym (16:30)
   
   [▲ Masquer détails]
```

**Validation (Expanded) :**
- [ ] Le ton suggère une alternative ("activité plus légère")
- [ ] Pas de pression pour déplacer obligatoirement

**Screenshot :** 📸 `test_4_normal_event_gym.png`

---

### Scénario 5 : Événement Personnel (Reschedule Léger)

**Setup :**
1. Supprimer l'événement du Scénario 4
2. Créer un nouvel événement :
   - Titre : "Déjeuner avec ami"
   - Date : Aujourd'hui
   - Heure : 17h00 - 18h00

**Actions :**
1. Rafraîchir l'app
2. Observer la section "Prévision creux d'énergie"

**Résultat Attendu :**
```
📉 Prévision creux d'énergie
🔻 16:00 - 18:00 ⚠️ Baisse d'énergie probable (conflit agenda)

[Pill Bleu]
📅 💡 Recommandation Pulse
   👉 Déplace 'Déjeuner avec ami' en dehors du creux si possible
   [▼ Voir détails]
```

**Validation :**
- [ ] Le pill est bleu (type reschedule)
- [ ] Le ton respecte le contexte personnel

**Screenshot :** 📸 `test_5_personal_event.png`

---

### Scénario 6 : Multiples Événements en Conflit

**Setup :**
1. Créer plusieurs événements :
   - "Réunion board" à 16h00 - 16h30 (critique)
   - "Call équipe" à 17h00 - 17h30 (important)
   - "Gym" à 18h00 - 19h00 (normal, hors creux)

**Actions :**
1. Rafraîchir l'app
2. Observer la section "Prévision creux d'énergie"

**Résultat Attendu :**
```
📉 Prévision creux d'énergie
🔻 16:00 - 18:00 ⚠️ Baisse d'énergie probable (conflit agenda)

[Pill Orange - Critique car max_importance=3]
⚠️ 💡 Recommandation Pulse
   👉 Prends une pause 30 min avant 'Réunion board, Call équipe...'
   [▼ Voir détails]
```

**Validation :**
- [ ] Le type est "prepare" (basé sur l'événement le plus critique)
- [ ] Le texte mentionne les 2 premiers événements + "..."
- [ ] Le pill est orange (critique)

**Actions Supplémentaires :**
3. Taper sur "Voir détails"

**Résultat Attendu (Expanded) :**
```
[Pill Orange - Expanded]
⚠️ 💡 Recommandation Pulse
   👉 Prends une pause 30 min avant 'Réunion board, Call équipe...'
   
   15 min de marche rapide, hydratation et un snack protéiné léger.
   
   Événements en conflit :
   • Réunion board (16:00)
   • Call équipe (17:00)
   
   [▲ Masquer détails]
```

**Validation (Expanded) :**
- [ ] Tous les événements en conflit sont listés
- [ ] L'heure de chaque événement est affichée
- [ ] L'ordre est correct (tri par importance)

**Screenshot :** 📸 `test_6_multiple_conflicts.png`

---

### Scénario 7 : Pas de Risk Window (Énergie Élevée)

**Setup :**
- Simuler un jour avec énergie élevée (score > 0.7)
- Ou attendre un jour où aucun creux n'est prévu

**Actions :**
1. Ouvrir l'app
2. Observer la carte "Énergie du jour"

**Résultat Attendu :**
```
⚡ Énergie du Jour
🔋 85/100 | Excellent
Confiance : 90%

[Pas de section "Prévision creux d'énergie"]
```

**Validation :**
- [ ] Aucune section risk window affichée
- [ ] L'app ne crash pas
- [ ] Le reste de la carte fonctionne normalement

**Screenshot :** 📸 `test_7_no_risk_window.png`

---

## 📊 Checklist Globale

### Affichage & Design
- [ ] Les pills ont les bonnes couleurs (orange/bleu/gris)
- [ ] Les icônes sont visibles (AlertTriangle/Calendar/CheckCircle)
- [ ] Le texte est lisible (contraste suffisant)
- [ ] Les animations expand/collapse sont fluides
- [ ] Les emojis s'affichent correctement (💡 👉 ⚠️)

### Logique
- [ ] Les événements critiques → recommandation "prepare"
- [ ] Les événements importants → recommandation "reschedule"
- [ ] Les événements normaux/personnels → reschedule léger
- [ ] Les multiples conflits affichent tous les événements
- [ ] L'importance maximale détermine le type de recommandation

### UX
- [ ] Le tap sur "Voir détails" expand immédiatement
- [ ] Le tap sur "Masquer détails" collapse immédiatement
- [ ] Le pull-to-refresh recharge les données
- [ ] Pas de freeze ou lag
- [ ] Les textes sont en français correct

### Edge Cases
- [ ] Pas de crash si aucun événement
- [ ] Pas de crash si risk_windows est vide
- [ ] Pas de crash si recommendation est undefined
- [ ] Pas de crash si conflicting_events est vide

---

## 📸 Screenshots à Capturer

1. `test_1_classic_risk_window.png` → Risk window sans conflit
2. `test_2_critical_event_prepare.png` → Événement critique collapsed
3. `test_2_critical_event_expanded.png` → Événement critique expanded
4. `test_3_important_event_reschedule.png` → Événement important
5. `test_4_normal_event_gym.png` → Événement normal (sport)
6. `test_5_personal_event.png` → Événement personnel
7. `test_6_multiple_conflicts.png` → Multiples conflits
8. `test_7_no_risk_window.png` → Pas de creux d'énergie

---

## 📝 Rapport de Test

**Date :** ___ / ___ / ___  
**Testeur :** _______________  
**Device :** iOS / Android (version : _____)  
**Build :** _________________  

### Résultats

| Scénario | Status | Notes |
|----------|--------|-------|
| 1. Risk Window Classique | ⬜ Pass ⬜ Fail | |
| 2. Événement Critique | ⬜ Pass ⬜ Fail | |
| 3. Événement Important | ⬜ Pass ⬜ Fail | |
| 4. Événement Normal | ⬜ Pass ⬜ Fail | |
| 5. Événement Personnel | ⬜ Pass ⬜ Fail | |
| 6. Multiples Conflits | ⬜ Pass ⬜ Fail | |
| 7. Pas de Risk Window | ⬜ Pass ⬜ Fail | |

### Bugs Identifiés

1. _______________________
2. _______________________
3. _______________________

### Suggestions d'Amélioration

1. _______________________
2. _______________________
3. _______________________

---

## ✅ Validation MVP

**Critères de validation :**
- [ ] 6/7 scénarios passent (minimum)
- [ ] Aucun crash identifié
- [ ] Les recommandations sont pertinentes
- [ ] L'UX est fluide et compréhensible

**Si validé :** ✅ Prêt pour deploy staging  
**Si non validé :** ❌ Corriger bugs + re-tester

---

**Guide complet pour valider manuellement la feature Risk Windows enrichis.** 📱✅
