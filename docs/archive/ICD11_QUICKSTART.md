# 🚀 Guide de démarrage rapide - Conditions de Santé (ICD-11)

## ⚡ Démarrage en 5 minutes

### 1️⃣ Base de données (1 min)

```bash
cd /Users/dannezri/Desktop/Pulse
```

**Option A: Via Supabase CLI** (recommandé)
```bash
# Si supabase CLI est installé
supabase db push
```

**Option B: Via Dashboard Supabase**
1. Ouvrir https://supabase.com/dashboard
2. Sélectionner votre projet
3. Aller dans **SQL Editor**
4. Copier le contenu de `database/migrations/017_user_conditions.sql`
5. Exécuter

### 2️⃣ Credentials ICD-11 (2 min)

1. Aller sur: https://icd.who.int/icdapi
2. Cliquer sur **"Request API Access"**
3. Remplir le formulaire (gratuit pour usage non-commercial)
4. Recevoir `CLIENT_ID` et `CLIENT_SECRET` par email

5. Ajouter dans `backend/.env`:
```env
ICD11_CLIENT_ID=votre_client_id_ici
ICD11_CLIENT_SECRET=votre_client_secret_ici
```

### 3️⃣ Redémarrer le backend (30 sec)

```bash
cd backend

# Arrêter le serveur actuel (Ctrl+C si en cours)
# Puis redémarrer
python api_server.py
```

Vous devriez voir:
```
🚀 Démarrage du serveur Bio-Feedback IA sur http://0.0.0.0:9000
```

### 4️⃣ Tester (1 min 30)

#### Test backend

```bash
# Dans un nouveau terminal
curl "http://localhost:9000/api/terminology/icd11/search?q=TDAH&lang=fr"
```

Réponse attendue:
```json
{
  "system": "icd11",
  "query": "TDAH",
  "count": 3,
  "results": [
    {
      "code": "6A05",
      "display": "Trouble déficitaire de l'attention avec hyperactivité",
      "category": "Troubles mentaux"
    }
  ]
}
```

#### Test mobile

1. Ouvrir l'app Pulse
2. Aller dans **Profil**
3. Descendre jusqu'à **"Conditions de santé"**
4. Cliquer sur **"Renseigner mes conditions"**
5. Rechercher "TDAH"
6. Sélectionner un résultat
7. Vérifier que le chip apparaît

## ✅ Checklist de vérification

- [ ] Migration DB exécutée sans erreur
- [ ] Variables `ICD11_CLIENT_ID` et `ICD11_CLIENT_SECRET` dans `.env`
- [ ] Backend redémarré et accessible sur port 9000
- [ ] Endpoint `/api/terminology/icd11/search` répond correctement
- [ ] Section "Conditions de santé" visible dans le Profil mobile
- [ ] Recherche fonctionne dans l'app
- [ ] Les chips s'affichent après ajout
- [ ] La suppression fonctionne

## 🧪 Tests automatisés (optionnel)

```bash
cd backend

# Définir un user_id de test dans .env
echo "TEST_USER_ID=votre-uuid-utilisateur-test" >> .env

# Lancer les tests
python tests/test_icd11_conditions.py
```

Résultats attendus:
```
✅ Tests de recherche ICD-11 terminés
✅ Tests CRUD terminés
✅ Tests RLS terminés
✅ Test de nettoyage terminé
✅ TOUS LES TESTS TERMINÉS AVEC SUCCÈS
```

## 🎯 Exemples de recherche

Testez ces termes pour vérifier que tout fonctionne:

| Terme | Code attendu | Catégorie |
|-------|--------------|-----------|
| TDAH | 6A05 | Troubles mentaux |
| Dépression | 6A70.Z | Troubles mentaux |
| Diabète | 5A11 | Endocrinologie |
| SOP (Syndrome ovaires polykystiques) | GA34.3 | Endocrinologie |
| Anxiété | 6B00 | Troubles mentaux |

## 🐛 Problèmes fréquents

### "401 Unauthorized" lors de la recherche

**Cause**: Credentials ICD-11 invalides ou manquants

**Solution**:
```bash
# Vérifier les variables d'env
cd backend
grep ICD11 .env

# Devraient afficher:
# ICD11_CLIENT_ID=...
# ICD11_CLIENT_SECRET=...
```

### "No results found"

**Cause**: Terme de recherche trop court ou incorrect

**Solution**: Essayez avec au moins 3 caractères et des termes courants (TDAH, diabète, dépression)

### "Table user_conditions does not exist"

**Cause**: Migration non appliquée

**Solution**:
```bash
# Vérifier les migrations dans Supabase Dashboard
# SQL Editor > Exécuter: SELECT * FROM user_conditions LIMIT 1;
```

### Mobile ne trouve pas l'API

**Cause**: URL API incorrecte

**Solution**:
```bash
# Vérifier l'IP dans mobile/src/config/api.ts
# Sur Mac, trouver votre IP:
ipconfig getifaddr en0  # WiFi
```

## 📱 Utilisation quotidienne

### Ajouter une condition

1. **Profil** → **Conditions de santé**
2. **Renseigner mes conditions**
3. Taper 2-3 lettres (ex: "dia" pour diabète)
4. Sélectionner dans les résultats
5. ✅ Confirmation

### Retirer une condition

1. **Profil** → **Conditions de santé**
2. Cliquer sur ✕ du chip
3. Confirmer la suppression
4. ✅ Disparaît immédiatement

### "Je préfère ne pas répondre"

C'est parfaitement OK! Cette section est **facultative**. L'app fonctionne sans conditions renseignées.

## 🎉 Félicitations!

Vous avez maintenant une fonctionnalité de conditions de santé complète basée sur la classification médicale internationale ICD-11 de l'OMS.

## 📚 Pour aller plus loin

- Lire la doc complète: `ICD11_CONDITIONS_IMPLEMENTATION.md`
- Consulter l'API ICD-11: https://icd.who.int/icdapi
- Voir le code source:
  - Backend: `backend/icd11_client.py`
  - Mobile: `mobile/src/components/ConditionPicker.tsx`

## 💡 Conseils

1. **Ajoutez uniquement les conditions diagnostiquées**: Les utilisateurs devraient ajouter des conditions connues, pas des auto-diagnostics
2. **Limitez à 5-10 conditions**: Plus de clarté pour l'IA
3. **Mettez à jour régulièrement**: Si une condition change (guérison, nouveau diagnostic)

## 🆘 Besoin d'aide?

- Consultez les logs backend: `backend/api_server.py` (dans le terminal)
- Consultez les logs mobile: Metro bundler (dans le terminal Expo)
- Lisez le troubleshooting: `ICD11_CONDITIONS_IMPLEMENTATION.md#troubleshooting`
