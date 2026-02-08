# Fonctionnalité Historique des Médicaments 📅

## Vue d'ensemble

Cette fonctionnalité permet de tracker et visualiser l'historique des prises de médicaments jour par jour. Les utilisateurs peuvent marquer leurs médicaments comme "pris" et consulter un historique détaillé avec statistiques.

## Architecture

### 1. Base de données (Supabase)

**Table `medication_intake_history`**
```sql
- id: UUID (primary key)
- user_id: UUID (référence auth.users)
- medication_id: UUID (référence user_medications)
- taken_at: TIMESTAMPTZ (date/heure de la prise)
- intake_date: DATE (date pour regroupement)
- intake_time: TIME (heure de prise)
- scheduled_time: TIME (heure prévue)
- was_on_time: BOOLEAN (pris à l'heure)
- pills_taken: INTEGER (nombre de comprimés)
- status: VARCHAR (taken/skipped/late/early)
- notes: TEXT (notes optionnelles)
```

**Vue `medication_intake_daily_summary`**
- Agrégation par jour et utilisateur
- Compteurs: total, pris, oubliés, à l'heure
- Liste des medication_ids

**RLS (Row Level Security)**
- Policies pour SELECT, INSERT, UPDATE, DELETE
- Isolation par user_id
- Service role bypass

### 2. Backend (React Query Hooks)

**`useMedicationHistory.ts`**
- `useMedicationHistory()`: Récupère l'historique complet
- `useMedicationHistoryByDay()`: Historique groupé par jour
- `useRecordMedicationIntake()`: Enregistre une prise
- `useMarkAsTaken()`: Raccourci pour marquer comme pris

**Fonctionnalités clés:**
- Jointure automatique avec `user_medications` pour récupérer le nom
- Calcul automatique de `was_on_time` (marge de 1h)
- Invalidation du cache après enregistrement
- Tri par date décroissante

### 3. Frontend (React Native Components)

**`MedicationHistoryTab.tsx`**
- Onglet dédié dans la page médicaments
- Liste des jours avec cartes expandables
- Affichage des prises par jour
- États: pris ✅, oublié ❌, en retard 🕐
- Empty state élégant

**`MedicationCard.tsx` (modifié)**
- Bouton "Marquer comme pris"
- Feedback visuel (couleur verte + checkmark)
- Animation de confirmation (2 secondes)
- Désactivation pendant le chargement

**`medications.tsx` (modifié)**
- Système d'onglets: "Mes Médicaments" / "Historique"
- Navigation fluide entre les vues
- Design cohérent avec le reste de l'app

## UI/UX

### Onglets
```
┌────────────────────────────────────┐
│  [💊 Mes Médicaments] [📅 Historique] │
└────────────────────────────────────┘
```

### Bouton "Marquer comme pris"
```
┌─────────────────────────────┐
│  ✓  Marquer comme pris      │  ← État normal (bleu)
└─────────────────────────────┘

┌─────────────────────────────┐
│  ✓  Pris aujourd'hui ✓      │  ← État actif (vert)
└─────────────────────────────┘
```

### Carte d'historique quotidien
```
┌─────────────────────────────────────┐
│ 📅 Aujourd'hui           2/3 pris   │
├─────────────────────────────────────┤
│ ✅ Venlafaxine                 Pris │
│    12:00 (prévu à 12:00)            │
│                                     │
│ ✅ Sertraline                  Pris │
│    23:05 (prévu à 23:00)            │
│                                     │
│ ❌ Vitamine D                Oublié │
│    — (prévu à 08:00)                │
└─────────────────────────────────────┘
```

## Workflow utilisateur

### 1. Marquer un médicament comme pris
```
User clique sur "Marquer comme pris"
    ↓
useMarkAsTaken() appelle l'API
    ↓
Insertion dans medication_intake_history
    ↓
Cache invalidé (React Query)
    ↓
Feedback visuel (bouton devient vert)
    ↓
Réinitialisation après 2s
```

### 2. Consultation de l'historique
```
User navigue vers l'onglet "Historique"
    ↓
useMedicationHistoryByDay() charge les données
    ↓
Affichage groupé par jour (plus récent en premier)
    ↓
User peut voir:
  - Combien de prises par jour
  - Quels médicaments pris/oubliés
  - Heure de prise vs heure prévue
  - Notes optionnelles
```

## Cas d'usage

### 1. Suivi de l'observance
- L'utilisateur peut voir s'il oublie souvent ses médicaments
- Identification des jours problématiques
- Statistiques de régularité

### 2. Dialogue médecin/patient
- Export potentiel de l'historique
- Preuve de prise régulière
- Identification des effets secondaires liés aux oublis

### 3. Rappels et notifications (futur)
- Notification si oubli à l'heure prévue
- Rappel basé sur l'historique (ex: "Vous avez oublié hier")

## Données enregistrées

### Automatiquement
- `user_id` (depuis le contexte auth)
- `medication_id` (depuis le médicament)
- `taken_at` (timestamp actuel)
- `intake_date` (date extraite de taken_at)
- `intake_time` (heure extraite de taken_at)
- `was_on_time` (calculé: ±1h de l'heure prévue)
- `pills_taken` (par défaut: 1, ou depuis medication)
- `status` (par défaut: 'taken')

### Optionnellement
- `scheduled_time` (depuis medication.intakeTimes[0])
- `notes` (ajouté manuellement par l'utilisateur)

## Performance

### Optimisations
1. **Index DB:**
   - `idx_medication_intake_history_user_date` pour les requêtes fréquentes
   - `idx_medication_intake_history_medication_id` pour les jointures

2. **React Query:**
   - `staleTime: 1 minute` pour l'historique
   - Invalidation ciblée après mutation
   - Cache local (SecureStore) en backup

3. **Pagination (future):**
   - Charger seulement les 30 derniers jours par défaut
   - "Load more" pour l'historique ancien

## Extensions futures

### 1. Statistiques avancées
- Taux d'observance mensuel/hebdomadaire
- Graphiques de tendance
- Comparaison par médicament

### 2. Rappels intelligents
- Notification à l'heure prévue
- Rappel si oubli détecté
- Ajustement basé sur les habitudes

### 3. Export de données
- PDF pour le médecin
- CSV pour analyse personnelle
- Partage sécurisé avec professionnels de santé

### 4. Gestion des oublis
- Bouton "Marquer comme oublié"
- Raison de l'oubli (optionnel)
- Conseils pour améliorer l'observance

### 5. Validation par photo
- Preuve de prise (photo du médicament)
- OCR pour vérifier la boîte
- Compliance pour essais cliniques

## Tests à effectuer

### Fonctionnels
- [ ] Marquer un médicament comme pris
- [ ] Voir l'historique groupé par jour
- [ ] Vérifier le calcul de `was_on_time`
- [ ] Tester avec plusieurs prises le même jour
- [ ] Vérifier l'affichage des notes
- [ ] Tester avec différents statuts (skipped, late, early)

### Edge cases
- [ ] Marquer plusieurs fois le même jour
- [ ] Prises à minuit (changement de jour)
- [ ] Médicament sans heure prévue
- [ ] Suppression d'un médicament avec historique
- [ ] Utilisateur avec 0 prise (empty state)

### Performance
- [ ] Historique avec 100+ entrées
- [ ] Chargement initial rapide
- [ ] Invalidation de cache
- [ ] Scroll fluide dans l'historique

## Migration

La migration `031_medication_intake_history.sql` a été appliquée avec succès le 2026-02-06.

**Rollback (si nécessaire):**
```sql
DROP VIEW IF EXISTS medication_intake_daily_summary;
DROP TABLE IF EXISTS medication_intake_history;
DROP FUNCTION IF EXISTS update_medication_intake_history_updated_at();
```

## Notes techniques

### Timezone
- Tous les timestamps sont en UTC (TIMESTAMPTZ)
- Conversion en local timezone dans l'UI (React Native)
- `intake_date` et `intake_time` pour faciliter les requêtes

### Unicité
- Constraint `unique_intake_per_medication_time` évite les doublons exacts
- Permet plusieurs prises du même médicament dans la journée (heures différentes)

### RLS
- Les policies sont strictes: utilisateur = propriétaire uniquement
- Service role peut bypasser pour scripts admin/analytics

## Conformité RGPD

- ✅ Données de santé protégées (RLS + encryption at rest)
- ✅ Suppression en cascade si user supprimé
- ✅ Export de données possible (droit d'accès)
- ✅ Pas de partage avec tiers sans consentement

---

**Auteur:** Assistant AI  
**Date:** 2026-02-06  
**Version:** 1.0.0
