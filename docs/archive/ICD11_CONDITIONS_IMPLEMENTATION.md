# Implémentation: Conditions de Santé (ICD-11)

## 📋 Vue d'ensemble

Cette fonctionnalité permet aux utilisateurs de renseigner leurs conditions de santé (pathologies) basées sur la classification ICD-11 de l'OMS (Organisation Mondiale de la Santé). Les données sont utilisées pour personnaliser les conseils de l'IA.

## 🎯 Objectifs

1. **UX novice-friendly**: Recherche simple par mot-clé, multi-sélection avec chips
2. **Source de vérité**: API officielle ICD-11 (WHO)
3. **Cache intelligent**: Réduire les appels API et améliorer les performances
4. **Sécurité**: RLS Supabase + OAuth2 pour l'API ICD-11

## 🏗️ Architecture

### Base de données (Supabase)

**Migration**: `database/migrations/017_user_conditions.sql`

#### Table `user_conditions`
Stocke les conditions de santé des utilisateurs.

```sql
CREATE TABLE user_conditions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES profiles(id),
    system TEXT NOT NULL,           -- 'icd11'
    code TEXT NOT NULL,            -- Code ICD-11
    display TEXT NOT NULL,         -- Libellé
    category TEXT,                 -- Catégorie
    severity TEXT,                 -- 'mild', 'moderate', 'severe'
    diagnosed BOOLEAN,             -- Diagnostiqué officiellement
    noted_at TIMESTAMP,
    UNIQUE(user_id, system, code)
);
```

#### Table `terminology_cache`
Cache pour les recherches ICD-11 (TTL: 7 jours).

```sql
CREATE TABLE terminology_cache (
    id UUID PRIMARY KEY,
    cache_key TEXT UNIQUE,         -- 'icd11:search:fr:depression'
    cache_data JSONB,              -- Résultats de recherche
    created_at TIMESTAMP,
    expires_at TIMESTAMP
);
```

### Backend (Python / FastAPI)

#### Fichiers créés/modifiés

1. **`backend/icd11_client.py`**
   - Client OAuth2 pour l'API ICD-11
   - Recherche par mot-clé
   - Cache intégré avec Supabase

2. **`backend/api_server.py`**
   - `GET /api/terminology/icd11/search?q=...&lang=fr`
   - `GET /api/profile/conditions`
   - `POST /api/profile/conditions`
   - `DELETE /api/profile/conditions/:id`

3. **`backend/config.example.env`**
   ```env
   ICD11_CLIENT_ID=your_icd11_client_id
   ICD11_CLIENT_SECRET=your_icd11_client_secret
   ```

### Mobile (React Native / Expo)

#### Fichiers créés/modifiés

1. **`mobile/src/hooks/useConditions.ts`**
   - Hook pour gérer les conditions
   - `fetchConditions()`, `searchConditions()`, `addCondition()`, `deleteCondition()`

2. **`mobile/src/components/ConditionPicker.tsx`**
   - Modal de recherche ICD-11
   - Affichage des résultats
   - Gestion de l'ajout
   - Disclaimer "Ceci n'est pas un diagnostic"

3. **`mobile/app/(tabs)/profil.tsx`**
   - Section "Conditions de santé (facultatif)"
   - Chips pour afficher les conditions
   - Bouton d'ajout

## 🚀 Installation

### 1. Base de données

Exécutez la migration Supabase:

```bash
# Via Supabase CLI
supabase migration up

# Ou via le dashboard Supabase
# Copiez le contenu de database/migrations/017_user_conditions.sql
```

### 2. Backend

#### Configuration ICD-11

1. Obtenez des credentials OAuth2 sur: https://icd.who.int/icdapi
2. Ajoutez-les dans `backend/.env`:

```env
ICD11_CLIENT_ID=your_client_id_here
ICD11_CLIENT_SECRET=your_client_secret_here
```

#### Installation des dépendances

Aucune nouvelle dépendance requise (utilise `requests` déjà présent).

#### Redémarrage du serveur

```bash
cd backend
python api_server.py
```

### 3. Mobile

Aucune dépendance supplémentaire. Les fichiers sont prêts à l'emploi.

```bash
cd mobile
npx expo start
```

## 📖 Utilisation

### Côté utilisateur (Mobile)

1. Ouvrir l'app → **Profil**
2. Section **"Conditions de santé (facultatif)"**
3. Cliquer sur **"Renseigner mes conditions"**
4. Rechercher une condition (ex: "TDAH", "dépression", "SOP")
5. Sélectionner dans les résultats
6. Les chips s'affichent dans le profil
7. Cliquer sur ✕ pour retirer une condition

### Côté backend (API)

#### Recherche ICD-11

```bash
GET /api/terminology/icd11/search?q=depression&lang=fr

# Réponse
{
  "system": "icd11",
  "query": "depression",
  "count": 5,
  "results": [
    {
      "code": "6A70",
      "display": "Trouble dépressif",
      "category": "Troubles mentaux"
    }
  ]
}
```

#### Récupérer les conditions d'un utilisateur

```bash
GET /api/profile/conditions
Authorization: Bearer <user_token>

# Réponse
{
  "status": "success",
  "count": 2,
  "conditions": [
    {
      "id": "uuid",
      "system": "icd11",
      "code": "6A70",
      "display": "TDAH",
      "category": "Troubles mentaux",
      "noted_at": "2026-01-29T12:00:00Z"
    }
  ]
}
```

#### Ajouter une condition

```bash
POST /api/profile/conditions
Authorization: Bearer <user_token>
Content-Type: application/json

{
  "system": "icd11",
  "code": "6A70",
  "display": "Trouble déficitaire de l'attention avec hyperactivité",
  "category": "Troubles mentaux",
  "severity": "moderate",
  "diagnosed": true
}
```

#### Supprimer une condition

```bash
DELETE /api/profile/conditions/:condition_id
Authorization: Bearer <user_token>
```

## 🧪 Tests

### Backend

```bash
cd backend

# Tests complets
python tests/test_icd11_conditions.py

# Prérequis:
# - Définir TEST_USER_ID dans .env (UUID d'un utilisateur de test)
# - Avoir des credentials ICD-11 valides
```

Les tests couvrent:
- ✅ Recherche ICD-11 (TDAH, SOP, dépression)
- ✅ CRUD des conditions utilisateur
- ✅ RLS policies (limité, tests manuels requis)
- ✅ Nettoyage du cache

### Mobile

Tests manuels recommandés:
1. Rechercher "TDAH" → vérifier les résultats
2. Ajouter une condition → vérifier le chip
3. Supprimer une condition → vérifier la disparition
4. Tester avec un autre utilisateur → vérifier l'isolation RLS

## 📊 Performance & Cache

### Stratégie de cache

- **Clé**: `icd11:search:{lang}:{query}`
- **TTL**: 7 jours
- **Stockage**: Table `terminology_cache` (Supabase)

### Nettoyage automatique

La fonction `clean_expired_terminology_cache()` peut être appelée via cron:

```sql
SELECT clean_expired_terminology_cache();
```

## 🔒 Sécurité

### RLS Policies

Toutes les opérations sur `user_conditions` sont protégées par RLS:

- **SELECT**: `auth.uid() = user_id`
- **INSERT**: `auth.uid() = user_id`
- **UPDATE**: `auth.uid() = user_id`
- **DELETE**: `auth.uid() = user_id`

### OAuth2 ICD-11

- Le `client_secret` est stocké côté backend uniquement
- Les tokens OAuth2 sont cachés en mémoire (1h)
- Aucune exposition du secret au mobile

## 🎨 UX & Design

### Principes

1. **Transparence**: Disclaimer "Ceci n'est pas un diagnostic"
2. **Simplicité**: Recherche par mot-clé (pas de hiérarchie complexe)
3. **Flexibilité**: Option "Je préfère ne pas répondre"
4. **Feedback**: Confirmations claires à chaque action

### Limites

- Maximum 20 conditions par utilisateur (soft limit)
- Recherche minimum 2 caractères
- Résultats limités à 20 pour la performance

## 🌍 Internationalisation

Actuellement supporté:
- **Français** (fr) - par défaut
- **Anglais** (en) - disponible

Pour ajouter d'autres langues:
```typescript
searchConditions(query, 'en') // English
```

## 📝 Checklist de déploiement

- [x] Migration DB appliquée
- [x] Credentials ICD-11 configurés
- [x] Backend redémarré
- [x] Tests backend passés
- [x] Tests mobile manuels
- [ ] Documentation utilisateur créée
- [ ] Monitoring des appels API ICD-11 configuré

## 🔮 Évolutions futures

### MVP+

- [ ] Sévérité des conditions (mild/moderate/severe)
- [ ] Statut diagnostiqué (true/false)
- [ ] Date de diagnostic
- [ ] Historique des conditions

### Pro

- [ ] Intégration SNOMED CT (plus détaillé)
- [ ] Suggestions basées sur les symptômes
- [ ] Import depuis dossiers médicaux
- [ ] Export pour médecins

## 📚 Ressources

- **API ICD-11**: https://icd.who.int/icdapi
- **Documentation WHO**: https://icd.who.int/docs/icdapi/
- **License**: CC BY-ND 3.0 IGO (attribution requise, pas de modification des codes)

## 🐛 Troubleshooting

### Erreur: "Invalid token format"

- Vérifiez que `ICD11_CLIENT_ID` et `ICD11_CLIENT_SECRET` sont corrects
- Testez manuellement l'OAuth2: https://id.who.int/connect/token

### Erreur: "Condition not found"

- Vérifiez que la condition appartient à l'utilisateur
- Vérifiez les RLS policies dans Supabase

### Recherche lente

- Vérifiez le cache: `SELECT * FROM terminology_cache;`
- Nettoyez le cache expiré: `SELECT clean_expired_terminology_cache();`

### Aucun résultat de recherche

- Vérifiez la connexion à l'API ICD-11
- Testez avec des termes en anglais si le français ne fonctionne pas
- Vérifiez les logs backend pour les erreurs API

## ✅ Résumé

Cette implémentation fournit une solution complète et production-ready pour gérer les conditions de santé des utilisateurs avec:

- ✅ Base de données normalisée (ICD-11)
- ✅ API backend sécurisée
- ✅ UX mobile intuitive
- ✅ Cache performant
- ✅ Tests automatisés
- ✅ Documentation complète

**Statut**: ✅ MVP Complet - Prêt pour la production
