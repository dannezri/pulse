# 🎯 Décision : Tests Mobile MVP

**Date:** 2026-01-30  
**Décision:** Tests Manuels Documentés pour MVP  
**Rationale:** Blocages techniques Jest + ROI temps vs. qualité  

---

## 📊 Contexte

### Feature Implémentée
**Risk Windows avec Agenda Enrichment**
- Backend : Classification + Recommandations + Enrichissement
- Mobile : Composant RiskWindowWithRecommendation + UI dynamique
- Status : ✅ Implémentation complète

### Tests Backend
- ✅ 3/3 tests unitaires passent
- ✅ Couverture : classification, recommandations, fail-safe
- ✅ Qualité : Robuste et documenté

### Tests Mobile : Blocages Techniques

**Problèmes Rencontrés :**

1. **jest-expo preset** → `TypeError: Object.defineProperty called on non-object`
2. **Cache + watchman** → Nettoyage sans effet
3. **Config externalisée** → Erreur persiste
4. **Preset désactivé** → `Cannot find module NativeAnimatedHelper`
5. **Mocks simplifiés** → Toujours des erreurs de modules

**Temps Investi :** 2-3h de debugging, 6 tentatives différentes

---

## 🎯 Décision : Tests Manuels pour MVP

### Rationale

**Arguments POUR Tests Manuels :**
1. ✅ **ROI Temps** : 2-3h déjà investies sans succès, 1-2h de tests manuels = pragmatique
2. ✅ **Qualité Backend** : Tests backend solides (3/3) couvrent la logique métier
3. ✅ **Documentation** : Guide tests manuels complet (7 scénarios)
4. ✅ **User Acceptance** : Tests manuels = validation UX réelle
5. ✅ **Time-to-Market** : MVP déployable rapidement

**Arguments CONTRE Tests Jest (actuellement) :**
1. ❌ **Blocages Techniques** : Problèmes upstream (jest-expo)
2. ❌ **ROI Négatif** : Temps de debug >> Valeur ajoutée MVP
3. ❌ **Flaky Tests** : Mocks incomplets = tests non fiables
4. ❌ **Maintenance** : Config fragile, risque de régression

---

## ✅ Solution Adoptée

### 1. Tests Backend Unitaires (FAIT)

```bash
cd backend/tests
python3 test_risk_windows_agenda.py
# ✅ 3/3 tests passent
```

**Couverture :**
- Classification événements (critique/important/normal/personnel)
- Génération recommandations (prepare/reschedule/accept)
- Fail-safe en cas d'erreur DB

---

### 2. Tests Manuels Mobile Documentés (À FAIRE)

**Fichier :** `MANUAL_TESTING_GUIDE.md`

**7 Scénarios :**
1. Risk window classique (sans conflit)
2. Événement critique → recommandation "prepare"
3. Événement important → recommandation "reschedule"
4. Événement normal → reschedule léger
5. Événement personnel → reschedule léger
6. Multiples conflits → priorité sur critique
7. Pas de risk window (énergie élevée)

**Checklist :**
- [ ] 7 scénarios exécutés (1-2h)
- [ ] 8 screenshots capturés
- [ ] Rapport de test rempli
- [ ] 0 crash identifié
- [ ] UX fluide et compréhensible

**Validation MVP :** 6/7 scénarios minimum passent

---

### 3. Post-MVP : Tests E2E avec Detox

**Timeline :** Prochaine sprint (après deploy MVP)

**Setup :**
```bash
cd mobile
npm install detox --save-dev
npx detox init
```

**Avantages Detox :**
- ✅ Tests E2E robustes (pas de mocks fragiles)
- ✅ Tests sur device réel ou simulateur
- ✅ Plus proche du comportement utilisateur
- ✅ Maintenance plus simple

**Exemple Test :**
```javascript
describe('Risk Windows', () => {
  it('affiche la recommandation prepare', async () => {
    await device.launchApp();
    await element(by.id('energy-card')).scroll(200, 'down');
    await expect(element(by.text('Prends une pause 30 min avant'))).toBeVisible();
    await element(by.text('Voir détails')).tap();
    await expect(element(by.text('15 min de marche rapide'))).toBeVisible();
  });
});
```

---

## 📊 Comparaison Approches

| Critère | Jest Unit | Tests Manuels | Detox E2E |
|---------|-----------|---------------|-----------|
| **Setup** | ❌ Bloqué | ✅ Immédiat | 🔄 1-2h |
| **Fiabilité** | ❌ Fragile | ✅ Réel | ✅ Robuste |
| **Maintenance** | ❌ Complexe | ✅ Simple | ✅ Modérée |
| **Couverture** | 🟡 Composant | ✅ UX complète | ✅ UX complète |
| **CI/CD** | ✅ Automatisé | ❌ Manuel | ✅ Automatisé |
| **Time-to-MVP** | ❌ Bloqué | ✅ Immédiat | 🔄 Post-MVP |

**Verdict MVP :** Tests Manuels + Backend ✅

---

## 🎯 Plan de Test MVP

### Phase 1 : Tests Manuels (1-2h)

```bash
# 1. Ouvrir le guide
open MANUAL_TESTING_GUIDE.md

# 2. Lancer l'app
cd mobile && npm start

# 3. Exécuter scénarios
# - Créer événements dans calendrier
# - Observer comportement app
# - Capturer screenshots
# - Noter bugs éventuels

# 4. Remplir rapport
# - 7 scénarios testés
# - 8 screenshots capturés
# - Bugs identifiés
# - Validation : 6/7 minimum
```

---

### Phase 2 : Deploy Staging

```bash
# Backend
cd backend && git push staging main

# Mobile
cd mobile && eas build --platform ios --profile staging
```

---

### Phase 3 : User Acceptance (2-3 jours)

**Testeurs :** 2-3 utilisateurs pilotes

**Feedback Collecté :**
- UX compréhensible ?
- Recommandations pertinentes ?
- Performance fluide ?
- Bugs identifiés ?

---

### Phase 4 : Production Deploy

**Critères de Validation :**
- ✅ 6/7 tests manuels passent
- ✅ 0 crash bloquant
- ✅ User acceptance positif
- ✅ Backend tests toujours verts (3/3)

**Si validé :** → Production 🚀

---

## 🔄 Post-MVP : Tests E2E Detox

**Timeline :** Sprint N+1 (après deploy production)

**Objectifs :**
1. Automatiser les 7 scénarios manuels
2. Intégrer dans CI/CD
3. Tests de régression automatisés
4. Couverture E2E complète

**Setup :**
```bash
npm install detox detox-cli --save-dev
npx detox init
npx detox build --configuration ios.sim.debug
npx detox test --configuration ios.sim.debug
```

---

## 📚 Documentation Créée

**Tests :**
- `MANUAL_TESTING_GUIDE.md` → 7 scénarios, checklist, rapport
- `backend/tests/test_risk_windows_agenda.py` → Tests backend (3/3 ✅)
- `DECISION_TESTS_MOBILE.md` → Ce document

**Debugging Jest :**
- `TESTS_JEST_FIXES.md` → Tentatives de fix
- `TESTS_JEST_EXPO_FIX.md` → Désactivation preset
- `TESTS_TROUBLESHOOTING.md` → Guide dépannage

**Résumés :**
- `START_HERE.md` → Point d'entrée
- `NEXT_STEPS.md` → Actions détaillées
- `TESTS_FINAL_STATUS.md` → Status complet

---

## ✅ Validation Décision

**Signé par :** [Équipe Dev]  
**Date :** 2026-01-30  
**Approuvé pour :** MVP  

**Conditions :**
- ✅ Tests backend robustes (3/3)
- ✅ Tests manuels documentés (7 scénarios)
- ✅ Plan post-MVP défini (Detox)
- ✅ Time-to-market optimisé

**Revue Post-MVP :**
- Sprint N+1 : Migration vers Detox
- Sprint N+2 : CI/CD intégration

---

## 🚀 Action Immédiate

```bash
open MANUAL_TESTING_GUIDE.md
cd mobile && npm start
```

**Exécuter les 7 scénarios, capturer screenshots, valider MVP.** ✅

---

**Décision actée : Tests manuels pour MVP, Tests E2E Detox pour post-MVP.** 🎯

**Qualité : Backend tests solides + Validation manuelle rigoureuse = MVP de qualité.** 🚀
