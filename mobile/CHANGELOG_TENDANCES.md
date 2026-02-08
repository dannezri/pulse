# Changelog - Page Tendances

## [1.1.0] - 2026-01-29

### ✨ Ajouts

#### Mode Jour Spécifique
- Nouveau sélecteur de mode : Période / Jour
- DateTimePicker natif pour sélectionner un jour précis
- Affichage de toutes les mesures d'une journée (vs agrégation par jour)
- Statistiques adaptées au mode jour : "X enregistrements" + "Plage min-max"

#### Métriques Complètes
Affichage de toutes les métriques disponibles pour les calculs :
- Activité : steps, distance, calories, active_calories, floors_climbed, vo2_max
- Vitaux : hrv, heart_rate, spo2, blood_pressure, glucose, respiratory_rate
- Corps : weight, body_fat, bmi, body_temperature
- Sommeil : sleep_duration
- Bien-être : stress, mindfulness
- Nutrition : water, caffeine, carbs

### 🔧 Modifications

#### `app/(tabs)/tendances.tsx`
- Ajout du state `viewMode` (period/day)
- Ajout du state `selectedDate` avec DateTimePicker
- Condition d'affichage selon le mode (période vs jour)
- Adaptation des statistiques selon le mode
- Import de `@react-native-community/datetimepicker`
- Styles pour `modeSelector`, `datePickerContainer`, etc.

#### `src/hooks/useMetricsHistory.ts`
- Nouvelle signature : `useMetricsHistory(userId, days?, specificDate?)`
- Support de deux modes :
  - **Période** : agrégation par jour (une mesure/jour)
  - **Jour spécifique** : toutes les mesures de la journée
- QueryKey mise à jour pour inclure `specificDate`

### 📦 Dépendances

#### Ajoutée
```json
"@react-native-community/datetimepicker": "8.4.4"
```

Installation :
```bash
npx expo install @react-native-community/datetimepicker
```

### ✅ Tests

- `npx expo-doctor` : ✅ 17/17 checks passed
- Linting : ✅ No errors
- Compatibilité : ✅ Expo SDK 54, RN 0.81.5, React 19.1.0

### 📚 Documentation

- `TENDANCES_ENHANCEMENT.md` - Documentation technique
- `TENDANCES_TEST_GUIDE.md` - Guide de test
- `TENDANCES_FEATURE_SUMMARY.md` - Résumé exécutif
- `CHANGELOG_TENDANCES.md` - Ce fichier

### 🎯 Impact

- **UX** : Meilleure exploration des données de santé
- **Analyse** : Possibilité de zoom sur une journée spécifique
- **Performance** : Aucun impact négatif (React Query cache)
- **Maintenance** : Code propre, typé, documenté

---

## Comment tester

```bash
cd /Users/dannezri/Desktop/Pulse/mobile
npx expo start
```

Naviguer vers l'onglet **Tendances** et tester :
1. Mode Période : 7J, 30J, 90J
2. Mode Jour : sélectionner une date, observer les mesures
3. Pull-to-refresh dans les deux modes

---

**Fait avec ❤️ pour Pulse**
