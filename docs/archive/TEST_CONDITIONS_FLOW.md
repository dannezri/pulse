# 🧪 Test du flow complet - Conditions de santé

## Objectif

Vérifier que l'ajout et la suppression de conditions fonctionnent correctement avec Supabase.

---

## ✅ Test 1: Ajout d'une condition

### Étapes

1. **Ouvrir l'app mobile**
   - Aller dans **Profil**
   - Descendre jusqu'à "Conditions de santé"

2. **Ajouter une condition**
   - Cliquer sur "Renseigner mes conditions"
   - Rechercher "TDAH"
   - Sélectionner le résultat
   - ✅ Confirmation "Ajouté"

3. **Vérifier l'affichage**
   - Le chip "TDAH" apparaît dans le profil
   - Avec un X pour le supprimer

4. **Vérifier dans Supabase**
   ```sql
   -- Dans Supabase SQL Editor
   SELECT * FROM user_conditions 
   WHERE user_id = 'votre-user-id'
   ORDER BY noted_at DESC;
   ```
   
   **Résultat attendu:**
   ```
   id: uuid
   user_id: votre-uuid
   system: "icd11"
   code: "6A05"
   display: "Trouble déficitaire de l'attention avec hyperactivité"
   category: "Troubles mentaux..."
   noted_at: timestamp
   ```

### Logs à surveiller

**Backend (terminal serveur):**
```
INFO:jwt_auth:Using simple UUID auth (temporary): c559fcd7...
INFO:httpx:HTTP Request: POST .../user_conditions "HTTP/2 201 Created"
INFO:     - "POST /api/profile/conditions HTTP/1.1" 200 OK
```

**Mobile (Metro bundler):**
```
[useConditions] Error adding condition: (si erreur)
```

---

## ✅ Test 2: Suppression d'une condition

### Étapes

1. **Dans le profil**
   - Trouver le chip "TDAH" ajouté précédemment
   - Cliquer sur le **X**

2. **Confirmation**
   - Popup: "Voulez-vous retirer 'TDAH' de votre profil ?"
   - Cliquer sur "Supprimer"

3. **Vérifier l'affichage**
   - Le chip disparaît immédiatement
   - Message "Aucune condition renseignée" si c'était la dernière

4. **Vérifier dans Supabase**
   ```sql
   -- Dans Supabase SQL Editor
   SELECT * FROM user_conditions 
   WHERE user_id = 'votre-user-id';
   ```
   
   **Résultat attendu:**
   ```
   (aucune ligne / ligne supprimée)
   ```

### Logs à surveiller

**Backend (terminal serveur):**
```
INFO:jwt_auth:Using simple UUID auth (temporary): c559fcd7...
INFO:httpx:HTTP Request: DELETE .../user_conditions?id=eq.uuid "HTTP/2 204 No Content"
INFO:     - "DELETE /api/profile/conditions/uuid HTTP/1.1" 200 OK
```

---

## ✅ Test 3: Multi-conditions

### Étapes

1. **Ajouter plusieurs conditions**
   - TDAH
   - Dépression
   - Diabète

2. **Vérifier l'affichage**
   - 3 chips visibles
   - Chacun avec son X

3. **Supprimer une condition au milieu**
   - Supprimer "Dépression"
   - Vérifier que TDAH et Diabète restent

4. **Vérifier dans Supabase**
   ```sql
   SELECT code, display FROM user_conditions 
   WHERE user_id = 'votre-user-id'
   ORDER BY noted_at;
   ```
   
   **Résultat attendu:**
   ```
   6A05 | Trouble déficitaire...
   5A11 | Diabète...
   (pas de dépression)
   ```

---

## ✅ Test 4: RLS (Row Level Security)

### Objectif
Vérifier que les utilisateurs ne voient que leurs propres conditions.

### Étapes

1. **Avec User A**
   - Ajouter "TDAH"
   - Vérifier qu'il apparaît

2. **Avec User B** (autre compte)
   - Ouvrir le profil
   - Vérifier que User B ne voit PAS le TDAH de User A
   - Vérifier "Aucune condition renseignée"

3. **Vérifier dans Supabase** (avec service key)
   ```sql
   -- Voir toutes les conditions
   SELECT user_id, display FROM user_conditions;
   ```
   
   **Résultat attendu:**
   ```
   user-a-id | TDAH
   (pas visible pour user B via l'app)
   ```

---

## ✅ Test 5: Limite de 20 conditions

### Étapes

1. **Ajouter 20 conditions**
   - Via l'app ou via SQL:
   ```sql
   INSERT INTO user_conditions (user_id, system, code, display)
   VALUES 
     ('votre-user-id', 'icd11', 'TEST1', 'Condition Test 1'),
     ('votre-user-id', 'icd11', 'TEST2', 'Condition Test 2'),
     -- ... jusqu'à 20
   ;
   ```

2. **Essayer d'ajouter une 21e condition**
   - Via l'app, rechercher et ajouter une nouvelle condition
   
   **Résultat attendu:**
   ```
   Erreur: "Maximum 20 conditions per user"
   ```

3. **Vérifier dans les logs backend**
   ```
   INFO:     - "POST /api/profile/conditions HTTP/1.1" 400 Bad Request
   ```

---

## ✅ Test 6: Conditions en double

### Étapes

1. **Ajouter "TDAH"**
   - Via l'app
   - ✅ Succès

2. **Essayer d'ajouter "TDAH" à nouveau**
   - Rechercher "TDAH"
   - Sélectionner le même résultat
   
   **Résultat attendu:**
   ```
   Erreur: "Impossible d'ajouter cette condition. Elle existe peut-être déjà."
   ```

3. **Vérifier dans Supabase**
   ```sql
   SELECT COUNT(*) FROM user_conditions 
   WHERE user_id = 'votre-user-id' AND code = '6A05';
   ```
   
   **Résultat attendu:**
   ```
   count: 1 (pas de doublon)
   ```

---

## 🐛 Problèmes possibles

### "500 Internal Server Error" lors de l'ajout

**Cause**: Fonction `get_user_conditions` ou table manquante
**Solution**: 
```bash
# Vérifier que la migration est appliquée
supabase db push
# ou via SQL Editor: appliquer 017_user_conditions.sql
```

### "401 Unauthorized"

**Cause**: Token JWT invalide
**Solution**: Vérifier que `storage.getUserId()` retourne bien un UUID valide

### Le chip n'apparaît pas après ajout

**Cause**: `fetchConditions()` n'est pas appelé
**Solution**: Vérifier que `onSuccess()` est bien câblé (ligne 529 profil.tsx)

### Le chip ne disparaît pas après suppression

**Cause**: État local non mis à jour
**Solution**: Vérifier que `setConditions` retire bien l'élément (ligne 161 useConditions.ts)

---

## 📊 Checklist de validation

- [ ] Ajout d'une condition → visible dans Supabase
- [ ] Chip s'affiche dans le profil
- [ ] Clic sur X → popup de confirmation
- [ ] Suppression → disparaît du profil
- [ ] Suppression → supprimée de Supabase
- [ ] Multi-conditions fonctionnent
- [ ] RLS isole les données par utilisateur
- [ ] Limite 20 conditions respectée
- [ ] Pas de doublons possibles
- [ ] Logs backend cohérents

---

## 🎉 Résultat attendu

✅ **Flow complet fonctionnel:**

```
Recherche → Ajout → Supabase → Affichage
                       ↓
Suppression ← Confirmation ← Clic X
    ↓
Supabase (DELETE)
    ↓
Disparition du chip
```

**Si tous les tests passent, la fonctionnalité est 100% opérationnelle !** 🚀

---

**Date**: 29 janvier 2026  
**Testé par**: [À compléter]  
**Status**: [À compléter après tests]
