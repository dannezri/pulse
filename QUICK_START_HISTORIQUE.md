# Guide de Démarrage Rapide - Historique des Médicaments 🚀

## ✅ Ce qui a été fait

### 1. Base de données
- ✅ Table `medication_intake_history` créée et migrée
- ✅ Vue `medication_intake_daily_summary` pour statistiques
- ✅ RLS (Row Level Security) configurée
- ✅ Index pour performance optimale

### 2. Hooks React Query
- ✅ `useMedicationHistory()` - Récupère l'historique complet
- ✅ `useMedicationHistoryByDay()` - Historique groupé par jour
- ✅ `useRecordMedicationIntake()` - Enregistre une prise
- ✅ `useMarkAsTaken()` - Raccourci pour marquer comme pris

### 3. Composants UI
- ✅ `MedicationHistoryTab` - Onglet historique avec liste par jour
- ✅ `MedicationCard` - Bouton "Marquer comme pris" intégré
- ✅ `QuickMarkAllButton` - Marquer tous les médicaments du jour
- ✅ Système d'onglets dans `medications.tsx`

## 📱 Comment l'utiliser

### Pour l'utilisateur final

#### 1. Marquer un médicament comme pris
```
1. Ouvrir l'app Pulse
2. Aller dans "Médicaments"
3. Cliquer sur "Marquer comme pris" sur une carte
4. ✅ Confirmation visuelle (bouton devient vert)
```

#### 2. Marquer tous les médicaments du jour
```
1. Dans l'onglet "Mes Médicaments"
2. Section "Aujourd'hui"
3. Cliquer sur "Marquer tout (X)"
4. Confirmer dans la popup
5. ✅ Tous les médicaments sont enregistrés
```

#### 3. Consulter l'historique
```
1. Dans "Médicaments"
2. Cliquer sur l'onglet "Historique"
3. Voir la liste des jours avec:
   - Nombre de prises par jour
   - Statut de chaque médicament
   - Heure de prise vs heure prévue
```

## 🧪 Tests à effectuer

### Test 1: Marquer un médicament
```bash
# Dans l'app mobile:
1. Ouvrir un médicament (ex: Venlafaxine)
2. Cliquer "Marquer comme pris"
3. Vérifier que le bouton devient vert
4. Aller dans l'onglet "Historique"
5. Vérifier que la prise apparaît dans "Aujourd'hui"
```

**Résultat attendu:**
- ✅ Bouton change de couleur
- ✅ Prise visible dans l'historique
- ✅ Heure de prise enregistrée
- ✅ Statut "Pris" avec checkmark vert

### Test 2: Marquer tous les médicaments
```bash
# Dans l'app mobile:
1. Avoir plusieurs médicaments pour aujourd'hui
2. Cliquer "Marquer tout (X)"
3. Confirmer dans la popup
4. Vérifier dans l'historique
```

**Résultat attendu:**
- ✅ Popup de confirmation
- ✅ Tous les médicaments enregistrés
- ✅ Historique montre "X/X pris"
- ✅ Chaque médicament a son heure de prise

### Test 3: Historique multi-jours
```bash
# Dans l'app mobile:
1. Marquer des médicaments aujourd'hui
2. (Attendre demain OU modifier la date dans Supabase)
3. Marquer des médicaments le lendemain
4. Consulter l'historique
```

**Résultat attendu:**
- ✅ Deux cartes de jour distinctes
- ✅ Tri par date décroissante (plus récent en haut)
- ✅ Compteurs corrects pour chaque jour

### Test 4: Vérification base de données
```sql
-- Dans Supabase SQL Editor:
SELECT 
  intake_date,
  intake_time,
  scheduled_time,
  was_on_time,
  status,
  um.name as medication_name
FROM medication_intake_history mih
JOIN user_medications um ON mih.medication_id = um.id
WHERE mih.user_id = 'YOUR_USER_ID'
ORDER BY intake_date DESC, intake_time DESC;
```

**Résultat attendu:**
- ✅ Lignes insérées avec les bonnes dates
- ✅ `was_on_time` calculé correctement (±1h)
- ✅ Jointure avec `user_medications` fonctionne

## 🐛 Troubleshooting

### Problème: "Aucun historique" alors que j'ai marqué des médicaments

**Solution:**
```bash
# 1. Vérifier les logs React Query
console.log('[useMedicationHistory] Fetching...');

# 2. Vérifier dans Supabase
SELECT * FROM medication_intake_history WHERE user_id = 'YOUR_ID';

# 3. Vérifier les RLS policies
# Aller dans Supabase > Authentication > Policies
# S'assurer que les policies sont actives
```

### Problème: Bouton "Marquer comme pris" ne répond pas

**Solution:**
```bash
# 1. Vérifier les logs
console.log('[useMarkAsTaken] Mutation...');

# 2. Vérifier le userId
console.log('userId:', storage.userId);

# 3. Redémarrer l'app mobile
# Fermer complètement l'app et la rouvrir
```

### Problème: Erreur "Not authenticated" ou 401

**Solution:**
```bash
# 1. Vérifier l'authentification
# Dans mobile/src/lib/storage.ts
console.log('Access token:', storage.getAccessToken());

# 2. Vérifier les headers Supabase
# Dans mobile/src/lib/supabase.ts
# S'assurer que le token est bien passé

# 3. Vérifier les RLS policies
# Elles doivent utiliser auth.uid() = user_id
```

## 📊 Données de test

### Insérer des données de test manuellement

```sql
-- Dans Supabase SQL Editor:
INSERT INTO medication_intake_history (
  user_id,
  medication_id,
  taken_at,
  intake_date,
  intake_time,
  scheduled_time,
  pills_taken,
  status,
  was_on_time
)
VALUES (
  'YOUR_USER_ID',
  'YOUR_MEDICATION_ID',
  NOW(),
  CURRENT_DATE,
  CURRENT_TIME,
  '12:00:00',
  1,
  'taken',
  true
);
```

### Générer un historique de 7 jours

```sql
-- Dans Supabase SQL Editor:
DO $$
DECLARE
  med_id UUID;
  day_offset INT;
BEGIN
  -- Récupérer un medication_id
  SELECT id INTO med_id FROM user_medications WHERE user_id = 'YOUR_USER_ID' LIMIT 1;
  
  -- Créer des prises pour les 7 derniers jours
  FOR day_offset IN 0..6 LOOP
    INSERT INTO medication_intake_history (
      user_id,
      medication_id,
      taken_at,
      intake_date,
      intake_time,
      scheduled_time,
      pills_taken,
      status,
      was_on_time
    )
    VALUES (
      'YOUR_USER_ID',
      med_id,
      NOW() - (day_offset || ' days')::INTERVAL,
      CURRENT_DATE - day_offset,
      '12:00:00',
      '12:00:00',
      1,
      'taken',
      true
    );
  END LOOP;
END $$;
```

## 🎨 Personnalisation

### Modifier les couleurs du bouton "Marquer comme pris"

```typescript
// Dans mobile/src/components/MedicationCard.tsx
markAsTakenButton: {
  backgroundColor: 'rgba(94, 92, 230, 0.15)', // ← Couleur normale
  borderColor: 'rgba(94, 92, 230, 0.3)',
},
markAsTakenButtonActive: {
  backgroundColor: 'rgba(52, 199, 89, 0.15)', // ← Couleur active (vert)
  borderColor: 'rgba(52, 199, 89, 0.4)',
},
```

### Modifier le délai de confirmation

```typescript
// Dans mobile/src/components/MedicationCard.tsx
setTimeout(() => setMarkedToday(false), 2000); // ← 2 secondes
// Changer en 5000 pour 5 secondes, etc.
```

### Ajouter des notes à une prise

```typescript
// Dans mobile/src/hooks/useMedicationHistory.ts
const handleMarkAsTaken = async () => {
  await markAsTaken(medication.id, scheduledTime);
  
  // Ajouter une note
  await recordIntake.mutateAsync({
    medicationId: medication.id,
    scheduledTime,
    status: 'taken',
    notes: 'Pris avec le repas', // ← Note personnalisée
  });
};
```

## 🚀 Prochaines étapes

### Court terme (1-2 semaines)
- [ ] Ajouter des statistiques d'observance (%)
- [ ] Graphique de tendance (prises par semaine)
- [ ] Export PDF de l'historique

### Moyen terme (1 mois)
- [ ] Notifications de rappel
- [ ] Détection automatique des oublis
- [ ] Conseils personnalisés

### Long terme (3+ mois)
- [ ] Intégration avec Apple Health / Google Fit
- [ ] Partage sécurisé avec médecin
- [ ] Analyse prédictive des oublis

## 📚 Documentation complète

Pour plus de détails techniques, voir:
- `MEDICATION_HISTORY_FEATURE.md` - Architecture complète
- `database/migrations/031_medication_intake_history.sql` - Schéma DB
- `mobile/src/hooks/useMedicationHistory.ts` - API React Query
- `mobile/src/components/MedicationHistoryTab.tsx` - UI principale

---

**Besoin d'aide ?**
- 📧 Ouvrir une issue sur GitHub
- 💬 Contacter le support
- 📖 Consulter la documentation technique

**Bon suivi de vos médicaments ! 💊✨**
