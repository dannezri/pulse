# Checklist de Test - Historique des Médicaments ✅

**Date:** 2026-02-06  
**Testeur:** _________________  
**Version:** 1.0.0

---

## 🎯 Tests Fonctionnels

### Test 1: Marquer un médicament individuel
**Objectif:** Vérifier que le bouton "Marquer comme pris" fonctionne

**Étapes:**
1. [ ] Ouvrir l'app Pulse
2. [ ] Naviguer vers "Médicaments"
3. [ ] Trouver une carte de médicament (ex: Venlafaxine)
4. [ ] Cliquer sur "Marquer comme pris"
5. [ ] Observer le changement visuel du bouton

**Résultat attendu:**
- [ ] Le bouton devient vert
- [ ] Le texte change en "Pris aujourd'hui ✓"
- [ ] Le checkmark se remplit
- [ ] Après 2 secondes, le bouton revient à l'état normal

**Résultat réel:**
```
_________________________________________________________________
_________________________________________________________________
```

---

### Test 2: Marquer tous les médicaments
**Objectif:** Vérifier le bouton "Marquer tout"

**Étapes:**
1. [ ] Dans l'onglet "Mes Médicaments"
2. [ ] Section "Aujourd'hui" (doit avoir 2+ médicaments)
3. [ ] Cliquer sur "Marquer tout (X)"
4. [ ] Confirmer dans la popup

**Résultat attendu:**
- [ ] Popup de confirmation apparaît
- [ ] Texte: "Marquer les X médicaments comme pris aujourd'hui ?"
- [ ] Après confirmation, bouton devient vert
- [ ] Texte change en "Tous pris ✓"

**Résultat réel:**
```
_________________________________________________________________
_________________________________________________________________
```

---

### Test 3: Consulter l'historique
**Objectif:** Vérifier que l'onglet "Historique" affiche les prises

**Étapes:**
1. [ ] Marquer au moins 1 médicament (Test 1)
2. [ ] Cliquer sur l'onglet "Historique"
3. [ ] Observer la liste des jours

**Résultat attendu:**
- [ ] Carte "Aujourd'hui" visible
- [ ] Compteur "X/Y pris" correct
- [ ] Médicament marqué apparaît avec ✅
- [ ] Heure de prise affichée (ex: "12:05")
- [ ] Heure prévue affichée (ex: "prévu à 12:00")

**Résultat réel:**
```
_________________________________________________________________
_________________________________________________________________
```

---

### Test 4: Historique multi-jours
**Objectif:** Vérifier le groupement par jour

**Prérequis:** Avoir des prises sur plusieurs jours (ou utiliser SQL pour insérer)

**Étapes:**
1. [ ] Aller dans l'onglet "Historique"
2. [ ] Scroller pour voir plusieurs jours

**Résultat attendu:**
- [ ] Jours triés du plus récent au plus ancien
- [ ] Chaque jour a sa propre carte
- [ ] Compteurs corrects pour chaque jour
- [ ] Dates formatées (ex: "Aujourd'hui", "Hier", "lundi 5 février")

**Résultat réel:**
```
_________________________________________________________________
_________________________________________________________________
```

---

### Test 5: Empty state
**Objectif:** Vérifier l'affichage quand aucun historique

**Prérequis:** Nouveau compte ou historique vide

**Étapes:**
1. [ ] Aller dans l'onglet "Historique"
2. [ ] Observer l'affichage

**Résultat attendu:**
- [ ] Icône calendrier grise
- [ ] Texte "Aucun historique"
- [ ] Sous-texte explicatif

**Résultat réel:**
```
_________________________________________________________________
_________________________________________________________________
```

---

## 🔍 Tests d'Intégration

### Test 6: Persistance des données
**Objectif:** Vérifier que les données sont bien enregistrées en DB

**Étapes:**
1. [ ] Marquer un médicament
2. [ ] Fermer complètement l'app
3. [ ] Rouvrir l'app
4. [ ] Aller dans "Historique"

**Résultat attendu:**
- [ ] La prise est toujours visible
- [ ] Les données sont identiques

**Résultat réel:**
```
_________________________________________________________________
_________________________________________________________________
```

---

### Test 7: Vérification Supabase
**Objectif:** Confirmer que les données sont en DB

**Étapes:**
1. [ ] Marquer un médicament
2. [ ] Ouvrir Supabase Dashboard
3. [ ] Aller dans Table Editor > medication_intake_history
4. [ ] Chercher la ligne correspondante

**Résultat attendu:**
- [ ] Ligne insérée avec bon `user_id`
- [ ] `medication_id` correct
- [ ] `intake_date` = aujourd'hui
- [ ] `intake_time` proche de l'heure actuelle
- [ ] `status` = 'taken'
- [ ] `was_on_time` calculé correctement

**Résultat réel:**
```
_________________________________________________________________
_________________________________________________________________
```

---

### Test 8: Calcul de `was_on_time`
**Objectif:** Vérifier le calcul de ponctualité

**Étapes:**
1. [ ] Médicament prévu à 12:00
2. [ ] Marquer à 12:30 (dans la marge de 1h)
3. [ ] Vérifier dans Supabase

**Résultat attendu:**
- [ ] `was_on_time` = true

**Étapes (hors marge):**
1. [ ] Médicament prévu à 12:00
2. [ ] Marquer à 14:00 (hors marge)
3. [ ] Vérifier dans Supabase

**Résultat attendu:**
- [ ] `was_on_time` = false

**Résultat réel:**
```
_________________________________________________________________
_________________________________________________________________
```

---

## 🎨 Tests UI/UX

### Test 9: Animations et transitions
**Objectif:** Vérifier la fluidité de l'UI

**Étapes:**
1. [ ] Cliquer sur "Marquer comme pris"
2. [ ] Observer l'animation du bouton
3. [ ] Switcher entre onglets "Mes Médicaments" / "Historique"
4. [ ] Scroller dans l'historique

**Résultat attendu:**
- [ ] Animations fluides (60 FPS)
- [ ] Pas de lag lors du switch d'onglet
- [ ] Scroll smooth dans l'historique
- [ ] Feedback visuel immédiat

**Résultat réel:**
```
_________________________________________________________________
_________________________________________________________________
```

---

### Test 10: Responsive design
**Objectif:** Vérifier l'affichage sur différents écrans

**Étapes:**
1. [ ] Tester sur iPhone SE (petit écran)
2. [ ] Tester sur iPhone 15 Pro Max (grand écran)
3. [ ] Vérifier les cartes, boutons, textes

**Résultat attendu:**
- [ ] Tout est lisible sur petit écran
- [ ] Pas de débordement de texte
- [ ] Boutons accessibles
- [ ] Espacement cohérent

**Résultat réel:**
```
_________________________________________________________________
_________________________________________________________________
```

---

## ⚡ Tests de Performance

### Test 11: Chargement initial
**Objectif:** Mesurer le temps de chargement

**Étapes:**
1. [ ] Ouvrir l'app (cold start)
2. [ ] Chronométrer jusqu'à l'affichage des médicaments
3. [ ] Noter le temps

**Résultat attendu:**
- [ ] < 2 secondes pour afficher la liste

**Résultat réel:**
```
Temps mesuré: __________ secondes
```

---

### Test 12: Historique volumineux
**Objectif:** Tester avec beaucoup de données

**Prérequis:** Insérer 100+ entrées via SQL (voir QUICK_START_HISTORIQUE.md)

**Étapes:**
1. [ ] Aller dans "Historique"
2. [ ] Scroller rapidement
3. [ ] Observer la fluidité

**Résultat attendu:**
- [ ] Scroll fluide sans lag
- [ ] Pas de freeze
- [ ] Mémoire stable

**Résultat réel:**
```
_________________________________________________________________
_________________________________________________________________
```

---

## 🔒 Tests de Sécurité

### Test 13: Isolation des données utilisateur
**Objectif:** Vérifier que les RLS policies fonctionnent

**Prérequis:** Avoir 2 comptes utilisateur

**Étapes:**
1. [ ] User A marque un médicament
2. [ ] Se connecter avec User B
3. [ ] Aller dans "Historique" de User B

**Résultat attendu:**
- [ ] User B ne voit PAS les prises de User A
- [ ] Historique de User B est vide (ou contient seulement ses propres prises)

**Résultat réel:**
```
_________________________________________________________________
_________________________________________________________________
```

---

### Test 14: Tentative d'injection SQL
**Objectif:** Vérifier la protection contre les injections

**Étapes:**
1. [ ] Essayer de marquer un médicament avec `medication_id` = `''; DROP TABLE medication_intake_history; --`
2. [ ] Observer le comportement

**Résultat attendu:**
- [ ] Erreur de validation
- [ ] Table non supprimée
- [ ] Aucune donnée corrompue

**Résultat réel:**
```
_________________________________________________________________
_________________________________________________________________
```

---

## 🐛 Tests de Gestion d'Erreurs

### Test 15: Perte de connexion
**Objectif:** Vérifier le comportement hors ligne

**Étapes:**
1. [ ] Activer le mode avion
2. [ ] Essayer de marquer un médicament
3. [ ] Observer le message d'erreur

**Résultat attendu:**
- [ ] Message d'erreur clair
- [ ] Pas de crash
- [ ] Possibilité de réessayer après reconnexion

**Résultat réel:**
```
_________________________________________________________________
_________________________________________________________________
```

---

### Test 16: Médicament supprimé
**Objectif:** Vérifier le comportement si le médicament n'existe plus

**Étapes:**
1. [ ] Marquer un médicament
2. [ ] Supprimer ce médicament
3. [ ] Aller dans "Historique"

**Résultat attendu:**
- [ ] Historique affiche "Médicament inconnu" ou le nom est conservé
- [ ] Pas de crash
- [ ] Données historiques préservées

**Résultat réel:**
```
_________________________________________________________________
_________________________________________________________________
```

---

## 📊 Résumé des Tests

### Statistiques
- **Total de tests:** 16
- **Tests réussis:** _____ / 16
- **Tests échoués:** _____ / 16
- **Tests bloqués:** _____ / 16

### Bugs identifiés
```
1. _________________________________________________________________
2. _________________________________________________________________
3. _________________________________________________________________
```

### Améliorations suggérées
```
1. _________________________________________________________________
2. _________________________________________________________________
3. _________________________________________________________________
```

---

## ✅ Validation Finale

### Checklist de déploiement
- [ ] Tous les tests fonctionnels passent
- [ ] Aucun bug bloquant
- [ ] Performance acceptable (< 2s chargement)
- [ ] UI/UX validée
- [ ] Sécurité vérifiée (RLS)
- [ ] Documentation à jour

### Signatures
**Développeur:** _________________  Date: __________  
**Testeur:** _________________  Date: __________  
**Product Owner:** _________________  Date: __________

---

**Prêt pour le déploiement en production ! 🚀**
