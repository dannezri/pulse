# Guide de Test - Page Tendances Améliorée

## 🎯 Objectif
Tester les nouvelles fonctionnalités de la page Tendances avec sélection de période ou jour spécifique.

## 📋 Pré-requis
- Application mobile Pulse lancée
- Utilisateur connecté avec des données de santé synchronisées
- Données disponibles sur plusieurs jours

## 🧪 Scénarios de test

### Test 1 : Mode Période (par défaut)

**Étapes :**
1. Ouvrir l'onglet "Tendances"
2. Vérifier que le mode "Période" est actif (bouton vert)
3. Par défaut, "30J" devrait être sélectionné

**Résultats attendus :**
- ✅ Toutes les métriques disponibles sont affichées
- ✅ Chaque carte montre : Moyenne, Min/Max, Graphique avec baseline, Tendance (↑↓→)
- ✅ Le texte en bas affiche : "X points • 30 derniers jours"

### Test 2 : Changement de période

**Étapes :**
1. Appuyer sur "7J"
2. Observer les changements
3. Appuyer sur "90J"
4. Observer les changements

**Résultats attendus :**
- ✅ Les graphiques se mettent à jour instantanément
- ✅ Les statistiques (moyenne, min, max) changent
- ✅ Le nombre de points affichés correspond à la période
- ✅ Les tendances peuvent changer selon la période

### Test 3 : Basculer en Mode Jour

**Étapes :**
1. Appuyer sur le bouton "Jour"
2. Observer l'interface

**Résultats attendus :**
- ✅ Le bouton "Jour" devient vert (actif)
- ✅ Les boutons de période (7J, 30J, 90J) disparaissent
- ✅ Un sélecteur de date apparaît avec la date du jour
- ✅ La date est affichée en français : "mercredi 29 janvier 2026"

### Test 4 : Sélection d'une date

**iOS :**
1. Appuyer sur le sélecteur de date
2. Un spinner apparaît avec les roues de sélection
3. Faire défiler pour choisir une date passée
4. Valider

**Android :**
1. Appuyer sur le sélecteur de date
2. Un dialog système s'ouvre avec un calendrier
3. Sélectionner une date passée
4. Valider avec "OK"

**Résultats attendus :**
- ✅ Le date picker s'ouvre correctement
- ✅ Impossible de sélectionner une date future
- ✅ Les données se chargent pour le jour sélectionné
- ✅ Les cartes affichent maintenant :
  - "X enregistrements" au lieu de "Moyenne"
  - "Plage : min - max" au lieu de "Min / Max"
  - Pas d'indicateur de tendance (ou neutre)
  - Texte : "X mesures • [date sélectionnée]"

### Test 5 : Comparaison Jour vs Période

**Étapes :**
1. En mode "Jour", sélectionner une date avec beaucoup de données
2. Noter le nombre de mesures pour une métrique (ex: HRV)
3. Basculer en mode "Période" (30J)
4. Observer la même métrique

**Résultats attendus :**
- ✅ En mode "Jour" : toutes les mesures de la journée sont visibles (peut être > 1)
- ✅ En mode "Période" : une seule mesure par jour (agrégation)
- ✅ Le graphique en mode "Jour" peut montrer plus de variation intra-journalière

### Test 6 : Pull to Refresh

**Étapes :**
1. En mode "Période" ou "Jour"
2. Faire un geste de pull-to-refresh
3. Observer le comportement

**Résultats attendus :**
- ✅ Indicateur de chargement s'affiche
- ✅ Les données se rechargent
- ✅ Les graphiques se mettent à jour

### Test 7 : Métriques sans données

**Étapes :**
1. Sélectionner une date très ancienne (avant la synchronisation des données)
2. Observer les cartes de métriques

**Résultats attendus :**
- ✅ Les métriques sans données ne sont pas affichées
- ✅ Si aucune donnée : message "Aucune donnée disponible"

## 🎨 Vérifications visuelles

### Design cohérent
- [ ] Style "Dark Zen" respecté (fond noir #000000)
- [ ] Couleurs des métriques distinctives et lisibles
- [ ] Icônes appropriées pour chaque métrique
- [ ] Espacement cohérent entre les cartes
- [ ] Animations fluides lors du changement de mode

### Typographie
- [ ] Dates en français avec accents et capitalisation correcte
- [ ] Nombres formatés selon la locale française (espaces pour milliers)
- [ ] Unités clairement affichées

### Interactions
- [ ] Feedback visuel sur les boutons (changement de couleur)
- [ ] Date picker natif respecte le design de la plateforme
- [ ] Scrolling fluide même avec beaucoup de métriques

## 🐛 Cas limites à tester

### Jour sans données
- Sélectionner un jour où aucune donnée n'existe
- Vérifier l'affichage du message approprié

### Jour avec une seule mesure
- Sélectionner un jour avec peu de données
- Vérifier que le graphique s'affiche correctement même avec 1 point

### Période avec données incomplètes
- Sélectionner 90J alors qu'on n'a que 30J de données
- Vérifier que seules les données disponibles sont affichées

### Changement rapide de mode/date
- Basculer rapidement entre modes
- Changer rapidement de dates
- Vérifier qu'il n'y a pas de conflit ou d'erreur

## ✅ Checklist finale

- [ ] Mode Période fonctionne comme avant (non-régression)
- [ ] Mode Jour affiche correctement toutes les mesures d'une journée
- [ ] Date picker s'ouvre et se ferme correctement
- [ ] Pas d'erreur dans les logs
- [ ] Performance satisfaisante (pas de lag)
- [ ] Toutes les métriques listées sont affichées quand disponibles
- [ ] Le texte explicatif change selon le mode
- [ ] Les statistiques affichées sont pertinentes au mode

## 📱 Commandes de test

### Lancer l'app
```bash
cd /Users/dannezri/Desktop/Pulse/mobile
npx expo start
```

### Vérifier les logs
- Observer la console pour les messages `[useMetricsHistory]`
- Vérifier que les requêtes sont correctes :
  - Mode période : `Fetching metrics from [date] to [date]`
  - Mode jour : `Fetching metrics for specific day: [date]`

### En cas de problème
```bash
# Nettoyer le cache
npx expo start -c

# Vérifier les dépendances
npx expo-doctor
```

## 🎉 Résultat attendu

Un utilisateur peut maintenant :
1. **Explorer les tendances** sur 7, 30 ou 90 jours
2. **Analyser en détail** un jour spécifique
3. **Comparer** différentes périodes facilement
4. **Comprendre** l'évolution de toutes ses métriques de santé

Cette fonctionnalité rend Pulse plus puissant pour l'analyse des données de santé ! 🚀
