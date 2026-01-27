# Guide de Test : Dark Zen UI

Ce document décrit comment tester la nouvelle interface "Dark Zen" sur un iPhone réel.

## Prérequis

- **iPhone physique** (iOS 15+) - Le simulateur ne permet pas de tester :
  - Les animations Skia à 60fps
  - Le geste shake
  - Les performances réelles du glassmorphism
  - L'affichage OLED avec noir absolu (#000000)
  
- **Expo Dev Client** installé sur l'iPhone
- **Node.js >= 20.19.4** (actuellement 20.16.0, mais fonctionne)

## Installation

### 1. Construire le Dev Client (première fois uniquement)

```bash
cd mobile
npx expo prebuild
npx expo run:ios --device
```

### 2. Démarrer le serveur de développement

```bash
cd mobile
npm start
```

### 3. Scanner le QR code avec l'iPhone

Ouvrir l'app Expo Go ou Expo Dev Client et scanner le QR code affiché dans le terminal.

## Checklist de Test

### ✅ Phase 1 : Orb Organique

- [ ] **L'Orb respire de manière organique**
  - État `calm` : pulsation lente et fluide (3s), forme arrondie
  - État `warning` : vibrations rapides (1s), forme anguleuse
  - État `alert` : contraction, forme plus petite et statique (4s)

- [ ] **Les couleurs sont correctes**
  - Optimal : Vert Électrique (#00FF41)
  - Attention : Orange Ambre (#FF9500)
  - Urgence : Rouge Système (#FF3B30)

- [ ] **Les animations sont fluides**
  - 60fps constant (vérifier avec Xcode Instruments si nécessaire)
  - Pas de saccades lors des déformations morphologiques

### ✅ Phase 2 : Gestes Tactiles

- [ ] **Tap sur l'Orb**
  - Feedback visuel : scale down à 0.95
  - Ouvre le drawer glassmorphique du bas

- [ ] **Pinch sur l'Orb**
  - Détection du pinch (zoom > 1.3x)
  - Navigation vers `/details` (page complète des métriques)

- [ ] **Shake du téléphone**
  - Détection du geste shake
  - Feedback haptique (vibration moyenne)
  - Rafraîchissement des données (invalidation des queries)

### ✅ Phase 3 : Bottom Drawer

- [ ] **Ouverture du drawer**
  - Animation slide up fluide avec spring
  - Effet glassmorphism visible (flou + transparence)
  - Backdrop noir semi-transparent (50%)

- [ ] **Contenu du drawer**
  - One-Line Insight affiché en grande typo (26px, bold)
  - WhyPills : 3 pilules horizontales avec les anomalies
  - Bouton Vision en bas à droite (vert électrique #00FF41)

- [ ] **Swipe down pour fermer**
  - Détection du swipe down (> 100px ou vélocité > 500)
  - Animation de fermeture fluide
  - Retour au dashboard

### ✅ Phase 4 : Lignes de Vie (Tendances)

- [ ] **Graphiques avec baseline**
  - Ligne de baseline pointillée grise (#8E8E93)
  - Ligne fluide des données avec courbes de Bézier
  - Zone au-dessus : dégradé vert (#00FF41)
  - Zone en dessous : dégradé orange (#FF9500)

- [ ] **Sélecteur de période**
  - Boutons 7J / 30J / 90J fonctionnels
  - Changement de graphique instantané

- [ ] **Stats affichées**
  - Moyenne, Min/Max correctement calculés
  - Nombre de points de données affiché

### ✅ Phase 5 : Animations et Transitions

- [ ] **Stagger delays**
  - Header : 0ms
  - Orb : 150ms
  - Message d'état : 300ms
  - Carte Insight : 450ms
  - Timeline : 600ms

- [ ] **Effet spring**
  - Animations avec spring naturel (tension: 50, friction: 8)
  - Pas d'effet de rebond excessif
  - Transitions fluides entre les écrans

### ✅ Phase 6 : Esthétique Globale

- [ ] **Dark Zen**
  - Fond noir absolu (#000000) - fusion avec l'OLED
  - Pas de traits de séparation nets
  - Tout suggéré par l'ombre et la lumière

- [ ] **Typographie**
  - San Francisco native (pas de police custom)
  - Textes importants : bold, 28-34px
  - Informations secondaires : #8E8E93, 14-16px

- [ ] **Glassmorphism**
  - Effets de verre dépoli visibles
  - Flous subtils (blur intensity: 80)
  - Bordures subtiles rgba(255, 255, 255, 0.1)

## Tests de Performance

### Mesurer les FPS

1. Ouvrir Xcode
2. Window > Devices and Simulators
3. Sélectionner l'iPhone connecté
4. Ouvrir "Instruments" > "Core Animation"
5. Vérifier que les FPS restent à 60 pendant les animations

### Mesurer la mémoire

1. Dans Xcode Instruments, sélectionner "Allocations"
2. Vérifier que la mémoire ne dépasse pas 150MB
3. Vérifier qu'il n'y a pas de fuites mémoire (leaks)

### Tester sur Android (optionnel)

⚠️ **Note :** Skia Canvas peut être plus lourd sur Android low-end.

Si les performances sont dégradées (< 30fps) :
- Prévoir un fallback vers l'ancien `PulseOrb.tsx`
- Désactiver les animations complexes
- Réduire le nombre de points de contrôle de l'Orb (8 → 6)

## Problèmes Connus

### Node.js version warning

```
npm warn EBADENGINE Unsupported engine {
  required: { node: '>=20.19.4' },
  current: { node: 'v20.16.0' }
}
```

**Solution :** Mettre à jour Node.js vers 20.19.4+ ou ignorer (fonctionne quand même).

### Expo Doctor warnings

Si `npx expo-doctor` retourne des warnings, exécuter :

```bash
cd mobile
npx expo install --fix
```

## Validation Finale

Une fois tous les tests passés, valider que :

- ✅ L'Orb respire de manière organique selon l'état de santé
- ✅ Tap sur l'Orb ouvre le drawer glassmorphique
- ✅ Pinch sur l'Orb ouvre la page de détails complète
- ✅ Shake rafraîchit les données avec feedback haptique
- ✅ Swipe down ferme le drawer
- ✅ Les tendances affichent des Lignes de Vie avec baseline
- ✅ `npx expo-doctor` ne retourne aucun warning
- ✅ Animations fluides 60fps sur iPhone réel

## Captures d'écran recommandées

Pour documenter l'implémentation, prendre des captures d'écran de :

1. Dashboard avec Orb en état `calm`
2. Dashboard avec Orb en état `warning`
3. Dashboard avec Orb en état `alert`
4. Drawer ouvert avec WhyPills
5. Page Tendances avec Lignes de Vie
6. Détails complets (après pinch)

## Prochaines Étapes

Si tous les tests sont validés, les prochaines améliorations possibles :

1. **Optimisation Android** : Fallback pour devices low-end
2. **Bouton Vision** : Implémenter le scanner de repas avec caméra
3. **Animations avancées** : Ajouter des micro-interactions supplémentaires
4. **Accessibilité** : Tester avec VoiceOver et ajuster les labels
5. **Dark Mode adaptatif** : Ajuster selon l'heure de la journée

---

**Date de création :** 2026-01-27  
**Version :** 1.0.0  
**Auteur :** Pulse Team
