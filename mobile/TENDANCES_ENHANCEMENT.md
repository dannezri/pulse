# Amélioration de la Page Tendances

## Résumé des changements

La page Tendances a été améliorée pour offrir deux modes de visualisation des métriques de santé :

### 1. Mode Période (existant, amélioré)
- Affiche les tendances sur 7, 30 ou 90 jours
- Une mesure par jour (la plus récente)
- Calcul de la tendance (hausse/baisse/stable)
- Statistiques : moyenne, min, max

### 2. Mode Jour (nouveau)
- Sélection d'un jour spécifique via un date picker natif
- Affiche **toutes** les mesures de la journée sélectionnée
- Permet de voir les variations intra-journalières
- Utile pour analyser l'évolution d'une métrique au cours d'une journée

## Métriques disponibles

Toutes les métriques utilisées pour les calculs sont affichées :

### Activité
- Pas
- Distance (km)
- Calories totales
- Calories actives
- Étages montés
- VO2 Max

### Signes vitaux
- HRV (variabilité du rythme cardiaque)
- Rythme cardiaque
- Saturation O2 (SpO2)
- Pression artérielle
- Glycémie
- Fréquence respiratoire

### Corps
- Poids
- Masse grasse
- IMC
- Température corporelle

### Sommeil
- Durée du sommeil

### Bien-être
- Niveau de stress
- Méditation

### Nutrition
- Hydratation
- Caféine
- Glucides

## Modifications techniques

### Fichiers modifiés

1. **`mobile/app/(tabs)/tendances.tsx`**
   - Ajout du sélecteur de mode (Période/Jour)
   - Intégration du DateTimePicker de `@react-native-community/datetimepicker`
   - Adaptation de l'affichage selon le mode
   - Gestion de l'état pour la date sélectionnée

2. **`mobile/src/hooks/useMetricsHistory.ts`**
   - Modification pour accepter soit une période (`days`) soit une date spécifique (`specificDate`)
   - En mode période : une mesure par jour (agrégation)
   - En mode jour : toutes les mesures de la journée (pour voir les variations horaires)

### Dépendance ajoutée

```bash
npx expo install @react-native-community/datetimepicker
```

Package compatible avec Expo SDK 54, installé via `expo install` comme requis.

## Utilisation

1. **Sélectionner le mode** :
   - Appuyer sur "Période" pour voir l'évolution sur plusieurs jours
   - Appuyer sur "Jour" pour analyser une journée spécifique

2. **Mode Période** :
   - Choisir entre 7J, 30J ou 90J
   - Voir les tendances et statistiques

3. **Mode Jour** :
   - Appuyer sur le sélecteur de date
   - Choisir un jour dans le calendrier
   - Voir toutes les mesures du jour avec leurs variations

## Compatibilité

✅ **Expo SDK 54** : Vérifié avec `npx expo-doctor`
✅ **React Native 0.81.5** : Compatible
✅ **iOS & Android** : DateTimePicker natif pour chaque plateforme
✅ **Pas d'erreur de linting** : Code propre et validé

## Interface utilisateur

- **Design cohérent** : Suit le style dark/zen de l'application
- **Animations fluides** : Transitions naturelles entre les modes
- **Date picker natif** : 
  - iOS : Spinner élégant
  - Android : Dialog système
- **Accessibilité** : Dates formatées en français avec localisation complète

## Exemple de flux utilisateur

1. L'utilisateur ouvre la page Tendances
2. Par défaut, le mode "Période" (30 jours) est actif
3. Pour analyser un jour précis où il s'est senti différent :
   - Il bascule en mode "Jour"
   - Il sélectionne la date concernée
   - Il voit toutes ses métriques de cette journée avec leurs variations
4. Il peut comparer avec d'autres jours en changeant la date
5. Il peut revenir au mode "Période" pour voir les tendances générales

## Prochaines améliorations possibles

- [ ] Comparaison de deux jours côte à côte
- [ ] Export des données en CSV/PDF
- [ ] Annotations personnalisées sur les graphiques
- [ ] Zoom et pan sur les graphiques pour exploration détaillée
- [ ] Filtrage par catégorie de métrique (Activité, Vitaux, etc.)
- [ ] Affichage des heures exactes pour chaque mesure en mode Jour
