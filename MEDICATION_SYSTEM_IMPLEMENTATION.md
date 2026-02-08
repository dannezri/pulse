# Système de Gestion des Médicaments et Traitements

**Date de création:** 4 Février 2026  
**Version:** 1.0.0  
**Auteur:** Développement Pulse

---

## 📋 Vue d'ensemble

Le système de gestion des médicaments permet aux utilisateurs de :

1. **Rechercher** des médicaments dans un catalogue (BDPM/ANSM)
2. **Consulter** une fiche détaillée (notice, génériques, alternatives)
3. **Ajouter** un traitement avec posologie complète, récurrence et durée

### Fonctionnalités principales

- ✅ Recherche intelligente avec autocomplete
- ✅ Base locale de 180+ médicaments français (fallback)
- ✅ Intégration API BDPM (Base de données publique des médicaments)
- ✅ Fiches détaillées avec notice/génériques/alternatives
- ✅ Formulaire complet de traitement :
  - Posologie (dosage, unité, quantité)
  - Prise unique ou récurrente
  - Jours de semaine + heures multiples
  - Durée (indéfinie, jusqu'à date, nombre de jours)
- ✅ Synchronisation offline-first (mobile)

---

## 🏗️ Architecture

### Base de Données (PostgreSQL/Supabase)

**3 tables principales créées par la migration `033_fix_medications_schema.sql` :**

#### 1. `medications_catalog` - Catalogue de référence

Stocke les médicaments du référentiel BDPM/ANSM.

```sql
CREATE TABLE medications_catalog (
    id UUID PRIMARY KEY,
    external_id TEXT NOT NULL,        -- Code CIS BDPM
    source TEXT NOT NULL,             -- 'bdpm', 'ansm', 'manual'
    name TEXT NOT NULL,
    active_substance TEXT,            -- DCI (substance active)
    atc_code TEXT,                    -- Code ATC WHO
    laboratory TEXT,
    form TEXT,                        -- Forme pharmaceutique
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(source, external_id)
);
```

**Politique RLS:** Lecture publique (données de référence)

#### 2. `medication_details` - Détails enrichis

Cache des détails récupérés depuis l'API (notice, génériques, alternatives).

```sql
CREATE TABLE medication_details (
    medication_id UUID PRIMARY KEY REFERENCES medications_catalog(id),
    notice_url TEXT,
    notice_text TEXT,
    generics JSONB DEFAULT '[]'::jsonb,
    alternatives JSONB DEFAULT '[]'::jsonb,
    last_refreshed_at TIMESTAMP WITH TIME ZONE
);
```

**Politique RLS:** Lecture publique

#### 3. `user_treatments` - Traitements utilisateur

Stocke les traitements médicamenteux des utilisateurs (anciennement `medications`).

```sql
CREATE TABLE user_treatments (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES profiles(id),
    medication_catalog_id UUID REFERENCES medications_catalog(id), -- Optionnel
    name TEXT NOT NULL,
    dosage TEXT,
    unit TEXT,
    pills_per_intake FLOAT,
    schedule_type TEXT DEFAULT 'recurring',  -- 'once' ou 'recurring'
    weekdays INTEGER[],                       -- [1,2,3,4,5] = Lun-Ven
    intake_times TEXT[],                      -- ['08:00', '20:00']
    daily_frequency INTEGER,
    start_date DATE NOT NULL,
    end_mode TEXT DEFAULT 'indefinite',      -- 'indefinite', 'until_date', 'duration_days'
    end_date DATE,
    duration_days INTEGER,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

**Politique RLS:** Utilisateur voit uniquement ses propres traitements

---

### Backend API (FastAPI - Python)

**Fichier principal:** `backend/medication_service.py`

#### Service `MedicationService`

Gère la recherche et l'enrichissement des médicaments.

**Méthodes principales:**
- `search_medications(query, limit)` : Recherche médicaments (cache local + API BDPM)
- `get_medication_details(external_id, source)` : Récupère notice/génériques/alternatives
- `cache_medication(medication_data)` : Enregistre dans le catalogue local
- `cache_medication_details(medication_id, details)` : Enregistre les détails

**Stratégie de cache:**
1. Recherche d'abord dans `medications_catalog` (rapide)
2. Si non trouvé, interroge API BDPM
3. Enregistre automatiquement le résultat dans le cache
4. TTL du cache : 7 jours

#### Endpoints API (`backend/api_server.py`)

##### 1. `GET /api/medications/search`

Recherche de médicaments par nom.

**Query params:**
- `q` (string, requis) : Terme de recherche (min 2 caractères)
- `limit` (integer, optionnel) : Nombre max de résultats (défaut: 10, max: 20)

**Réponse:**
```json
{
  "query": "doliprane",
  "results": [
    {
      "id": "CIS-60001551",
      "name": "DOLIPRANE 500 mg, comprimé",
      "form": "Comprimé",
      "laboratory": "OPELLA HEALTHCARE FRANCE SAS",
      "active_substance": "Paracétamol",
      "atc_code": "N02BE01",
      "source": "bdpm"
    }
  ],
  "count": 1
}
```

##### 2. `GET /api/medications/{medication_id}`

Récupère les détails complets d'un médicament.

**Path params:**
- `medication_id` : UUID dans medications_catalog OU external_id (CIS)

**Réponse:**
```json
{
  "id": "uuid...",
  "external_id": "CIS-60001551",
  "name": "DOLIPRANE 500 mg, comprimé",
  "form": "Comprimé",
  "laboratory": "OPELLA HEALTHCARE FRANCE SAS",
  "active_substance": "Paracétamol",
  "atc_code": "N02BE01",
  "notice_url": "https://...",
  "generics": [
    {
      "id": "CIS-...",
      "name": "Paracétamol 500mg",
      "laboratory": "Générique"
    }
  ],
  "alternatives": [
    {
      "id": "uuid...",
      "name": "Dafalgan 500mg",
      "laboratory": "Bristol-Myers Squibb",
      "reason": "Même substance active"
    }
  ]
}
```

##### 3. `POST /api/treatments`

Créer un nouveau traitement médicamenteux.

**Headers:**
- `Authorization: Bearer {jwt_token}` (requis)

**Body:**
```json
{
  "medication_id": "uuid",          // Optionnel
  "medication_name": "Doliprane 500mg",
  "dosage": "500",
  "unit": "mg",
  "pills_per_intake": 1,
  "schedule_type": "recurring",     // 'once' ou 'recurring'
  "weekdays": [1, 2, 3, 4, 5],      // 1=lun, 7=dim
  "intake_times": ["08:00", "20:00"],
  "start_date": "2026-02-04",
  "end_mode": "until_date",         // 'indefinite', 'until_date', 'duration_days'
  "end_date": "2026-03-04",
  "duration_days": null,
  "notes": "Avec repas"
}
```

**Réponse:**
```json
{
  "id": "uuid...",
  "message": "Traitement créé avec succès"
}
```

##### 4. `GET /api/treatments`

Liste des traitements de l'utilisateur connecté.

**Headers:**
- `Authorization: Bearer {jwt_token}` (requis)

**Query params:**
- `active_only` (boolean, optionnel) : Filtrer uniquement les actifs (défaut: true)

**Réponse:**
```json
{
  "treatments": [
    {
      "id": "uuid...",
      "name": "Doliprane 500mg",
      "dosage": "500",
      "unit": "mg",
      "schedule_type": "recurring",
      "intake_times": ["08:00", "20:00"],
      "weekdays": [1, 2, 3, 4, 5],
      "start_date": "2026-02-04",
      "end_mode": "indefinite",
      "is_active": true,
      ...
    }
  ],
  "count": 5
}
```

##### 5. `DELETE /api/treatments/{treatment_id}`

Supprime (soft delete) un traitement.

**Headers:**
- `Authorization: Bearer {jwt_token}` (requis)

**Path params:**
- `treatment_id` : UUID du traitement

**Réponse:**
```json
{
  "message": "Traitement supprimé avec succès"
}
```

---

### Mobile (React Native + Expo SDK 54)

#### Pages créées

##### 1. `/medication-detail` - Fiche détaillée

**Fichier:** `mobile/app/medication-detail.tsx`

**Fonctionnalités:**
- Affichage des informations du médicament
- 3 onglets : Notice / Génériques / Alternatives
- Bouton "Ajouter à mes prises" (navigation vers `/add-treatment`)
- Ouverture de la notice dans le navigateur

**Route:**
```
/medication-detail?id={medicationId}&name={medicationName}
```

##### 2. `/add-treatment` - Formulaire complet

**Fichier:** `mobile/app/add-treatment.tsx`

**Fonctionnalités:**
- Posologie (dosage, unité, quantité par prise)
- Type de prise : unique ou récurrent
- Jours de semaine (checkboxes L-D)
- Heures multiples (ajout/suppression)
- Date de début (DatePicker)
- Durée traitement :
  - Indéfiniment
  - Jusqu'au (date de fin)
  - Pendant X jours
- Notes optionnelles
- Validation complète côté client
- Envoi vers API backend

**Route:**
```
/add-treatment?medicationId={id}&medicationName={name}
```

#### Composants réutilisés

**Existants:**
- `MedicationAutocomplete` : Recherche avec autocomplete
- `MedicationForm` : Formulaire basique (conservé pour compatibilité)
- `MedicationList` : Affichage liste de médicaments

**Hook principal:**
- `useMedications()` : Hook existant pour la gestion locale (à migrer vers `user_treatments`)

#### Dépendances

```json
{
  "@react-native-community/datetimepicker": "^8.2.0"
}
```

**Installation:**
```bash
cd mobile
npx expo install @react-native-community/datetimepicker
```

---

## ⚠️ Limitations et Points d'Attention

### 1. ICD-11 ≠ Médicaments

**Confusion à éviter :**
- **ICD-11** (WHO) = Classification des **maladies/diagnostics** (ex: "6A70" = Épisode dépressif)
- **BDPM** (ANSM) = Base de données des **médicaments** français

❌ ICD-11 ne contient **PAS** de médicaments, notice, génériques.

**Ce qui existe déjà dans Pulse :**
- ✅ Intégration ICD-11 pour les conditions de santé (`icd11_client.py`)
- ✅ Table `user_conditions` avec codes ICD-11

**Nouveau :**
- ✅ Intégration BDPM pour les médicaments (`medication_service.py`)
- ✅ Tables `medications_catalog`, `medication_details`, `user_treatments`

### 2. API BDPM : Couverture partielle

**API utilisée :** `https://open-medicaments.fr/api/v1`

**Ce qui fonctionne :**
- ✅ Recherche par nom de médicament
- ✅ Informations de base (nom, laboratoire, forme, substance active)

**Limitations connues :**
- ⚠️ **Notice :** URL disponible pour ~60% des médicaments
- ⚠️ **Génériques :** Données pas toujours complètes
- ⚠️ **Alternatives :** Calculées localement (même substance active)

**Solutions de secours :**
1. Base locale de 180+ médicaments français (`mobile/src/services/MedicationAPI.ts`)
2. Affichage "données indisponibles" si API échoue
3. Cache local pour réduire les appels API

### 3. Timezone et Dates

**Configuration actuelle :** UTC par défaut dans Supabase

**Recommandations :**
- Configurer timezone `Europe/Paris` dans Supabase :
  ```sql
  ALTER DATABASE postgres SET timezone TO 'Europe/Paris';
  ```
- Utiliser `TIMESTAMP WITH TIME ZONE` (déjà fait)
- Conversion côté mobile en ISO 8601 (déjà implémenté)

### 4. Migration de l'Existant

**Problème résolu :**
- ❌ Hook mobile utilisait `user_medications` (table inexistante)
- ✅ Migration 033 renomme `medications` → `user_treatments`
- ✅ Ajout des colonnes manquantes

**Actions nécessaires :**
1. Appliquer la migration `033_fix_medications_schema.sql`
2. Mettre à jour le hook `useMedications()` pour utiliser `user_treatments`
3. Tester la synchronisation mobile ↔ backend

---

## 🚀 Guide de Déploiement

### Étape 1 : Appliquer la migration DB

**Via Supabase Dashboard (recommandé) :**
1. Ouvrir [Supabase Dashboard](https://app.supabase.com)
2. Sélectionner le projet Pulse
3. Aller dans **SQL Editor** (icône </> dans la barre latérale)
4. Cliquer sur **New Query**
5. Copier-coller le contenu de `database/migrations/033_fix_medications_schema.sql`
6. Cliquer sur **Run** (ou `Cmd+Enter`)
7. Vérifier que "Success. No rows returned" s'affiche

**Via CLI :**
```bash
cd /Users/dannezri/Desktop/Pulse
supabase db push
```

**Vérification :**
```sql
-- Vérifier que les 3 tables existent
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('medications_catalog', 'medication_details', 'user_treatments');
```

### Étape 2 : Déployer le backend

```bash
cd backend

# Le nouveau service medication_service.py est automatiquement importé dans api_server.py

# Redémarrer le backend
./restart_backend.sh

# Ou manuellement
pkill -f "python.*api_server"
python api_server.py
```

**Vérifier que le serveur démarre :**
```
🚀 Démarrage du serveur Bio-Feedback IA sur http://0.0.0.0:9000
```

**Tester les endpoints :**
```bash
# Test recherche
curl "http://localhost:9000/api/medications/search?q=doliprane"

# Test détails (remplacer {id} par un ID réel)
curl "http://localhost:9000/api/medications/{id}"
```

### Étape 3 : Déployer le mobile

```bash
cd mobile

# La dépendance @react-native-community/datetimepicker est déjà installée
# Si besoin :
# npx expo install @react-native-community/datetimepicker

# Relancer l'app
npm run ios      # iOS
# ou
npm run android  # Android
```

**Vérifier :**
1. Aller dans l'app
2. Rechercher un médicament
3. Cliquer sur un résultat → Fiche détaillée
4. Cliquer sur "Ajouter à mes prises" → Formulaire complet
5. Remplir et valider

### Étape 4 : Tests

#### Backend

```bash
cd backend

# Test manuel des endpoints
./test-medications-api.sh

# Tests unitaires (à créer)
pytest tests/test_medication_service.py
```

#### Mobile

```bash
cd mobile

# Tests unitaires
npm test

# Test spécifique
npm test -- src/hooks/useMedications.test.ts
```

---

## 📊 Données de Test

**Insérer des médicaments de test :**

```sql
-- Médicaments courants
INSERT INTO medications_catalog (external_id, source, name, active_substance, atc_code, laboratory, form)
VALUES 
  ('CIS-60001551', 'bdpm', 'DOLIPRANE 500 mg, comprimé', 'Paracétamol', 'N02BE01', 'OPELLA HEALTHCARE FRANCE SAS', 'Comprimé'),
  ('CIS-61133534', 'bdpm', 'DOLIPRANE 1000 mg, comprimé', 'Paracétamol', 'N02BE01', 'OPELLA HEALTHCARE FRANCE SAS', 'Comprimé'),
  ('CIS-67132169', 'bdpm', 'LEVOTHYROX 50 microgrammes, comprimé sécable', 'Lévothyroxine sodique', 'H03AA01', 'MERCK SANTE', 'Comprimé')
ON CONFLICT (source, external_id) DO NOTHING;

-- Détails pour Doliprane 500mg
INSERT INTO medication_details (medication_id, notice_url, generics)
SELECT 
  id,
  'https://www.has-sante.fr/upload/docs/application/pdf/doliprane_notice.pdf',
  '[
    {"id": "CIS-generic1", "name": "Paracétamol 500mg", "laboratory": "Biogaran"},
    {"id": "CIS-generic2", "name": "Paracétamol 500mg", "laboratory": "Mylan"}
  ]'::jsonb
FROM medications_catalog
WHERE external_id = 'CIS-60001551'
ON CONFLICT (medication_id) DO NOTHING;

-- Traitement de test (remplacer {user_id} par votre UUID)
INSERT INTO user_treatments (user_id, name, dosage, unit, pills_per_intake, schedule_type, weekdays, intake_times, daily_frequency, start_date, end_mode, is_active)
VALUES 
  ('{user_id}', 'Doliprane 500mg', '500', 'mg', 1, 'recurring', ARRAY[1,2,3,4,5], ARRAY['08:00', '20:00'], 2, CURRENT_DATE, 'indefinite', true);
```

---

## 🔄 Scénarios d'utilisation

### Scénario 1 : Ajout simple d'un traitement

1. User ouvre l'app mobile
2. Recherche "doliprane" dans la barre de recherche
3. Sélectionne "Doliprane 500mg"
4. Voit la fiche détaillée avec notice/génériques
5. Clique "Ajouter à mes prises"
6. Remplit :
   - Dosage : 500mg
   - Quantité : 1 comprimé
   - Récurrence : Lun-Ven
   - Heures : 08:00, 20:00
   - Date début : Aujourd'hui
   - Durée : Indéfiniment
7. Valide → Traitement enregistré

### Scénario 2 : Traitement temporaire

1. Recherche "Amoxicilline"
2. Ajoute avec :
   - Dosage : 1g
   - Récurrence : Tous les jours
   - Heures : 08:00, 14:00, 20:00
   - Date début : Aujourd'hui
   - **Durée : 7 jours**
3. Après 7 jours → Traitement automatiquement inactif

### Scénario 3 : Prise unique

1. Recherche "Vitamine D"
2. Ajoute avec :
   - Type : **Prise unique**
   - Date : Dimanche prochain
   - Dosage : 100000 UI

---

## 🧪 Cas de test

### Test 1 : Recherche médicament

```bash
# Input
curl "http://localhost:9000/api/medications/search?q=doli"

# Expected
{
  "query": "doli",
  "results": [
    {"name": "DOLIPRANE 500 mg, comprimé", ...},
    {"name": "DOLIPRANE 1000 mg, comprimé", ...}
  ],
  "count": 2
}
```

### Test 2 : Création traitement récurrent

```bash
# Input
curl -X POST "http://localhost:9000/api/treatments" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "medication_name": "Doliprane 500mg",
    "dosage": "500",
    "unit": "mg",
    "pills_per_intake": 1,
    "schedule_type": "recurring",
    "weekdays": [1,2,3,4,5],
    "intake_times": ["08:00", "20:00"],
    "start_date": "2026-02-04",
    "end_mode": "duration_days",
    "duration_days": 7
  }'

# Expected
{
  "id": "uuid...",
  "message": "Traitement créé avec succès"
}
```

---

## 📝 TODO Future

### Phase 1 : Fonctionnalités MVP+

- [ ] Édition de traitements existants
- [ ] Historique des prises effectuées
- [ ] Notifications locales (push) pour rappels
- [ ] Export PDF pour médecin
- [ ] Marquer une prise comme "prise" ou "oubliée"

### Phase 2 : Enrichissement

- [ ] Intégration API ANSM officielle (si clé API disponible)
- [ ] Photos de boîtes de médicaments (OCR)
- [ ] Alertes interactions médicamenteuses
- [ ] Lien automatique avec conditions ICD-11
- [ ] Effets secondaires courants

### Phase 3 : Analytics

- [ ] Observance (% de prises respectées)
- [ ] Impact sur biométriques (HRV, énergie, sommeil)
- [ ] Corrélations médicament ↔ symptômes
- [ ] Graphiques de suivi temporel
- [ ] Suggestions d'optimisation des horaires

### Phase 4 : Intégration avancée

- [ ] Synchronisation avec pharmacies
- [ ] Scan d'ordonnances
- [ ] Rappels automatiques de renouvellement
- [ ] Partage sécurisé avec professionnels de santé
- [ ] Intégration HealthKit (iOS) / Health Connect (Android)

---

## 📚 Ressources et Liens

### API & Documentation

- **API BDPM Open :** https://open-medicaments.fr
- **Base de données publique des médicaments :** https://base-donnees-publique.medicaments.gouv.fr
- **ICD-11 WHO (conditions, pas médicaments) :** https://icd.who.int/en
- **Code ATC WHO :** https://www.whocc.no/atc_ddd_index/

### Réglementation

- **ANSM (Agence nationale de sécurité du médicament) :** https://ansm.sante.fr
- **HAS (Haute Autorité de Santé) :** https://www.has-sante.fr

### Supabase

- **Documentation Supabase :** https://supabase.com/docs
- **RLS (Row Level Security) :** https://supabase.com/docs/guides/auth/row-level-security

### React Native

- **Expo DateTimePicker :** https://docs.expo.dev/versions/latest/sdk/date-time-picker/
- **Expo Router :** https://docs.expo.dev/router/introduction/

---

## 🆘 Troubleshooting

### Erreur : "Médicament non trouvé"

**Cause :** Le médicament n'est pas dans le catalogue local et l'API BDPM ne le trouve pas.

**Solution :**
1. Vérifier l'orthographe
2. Essayer avec moins de caractères (ex: "doli" au lieu de "doliprane")
3. Vérifier que l'API BDPM est accessible :
   ```bash
   curl "https://open-medicaments.fr/api/v1/medicaments?query=doliprane"
   ```

### Erreur : "Notice indisponible"

**Cause :** La notice n'est pas fournie par l'API BDPM pour ce médicament.

**Solution :** Normal, afficher le message "Notice non disponible" dans l'UI.

### Erreur : "Traitement non créé"

**Causes possibles :**
1. Token JWT expiré → Reconnexion nécessaire
2. Validation échouée → Vérifier les champs requis
3. Problème RLS Supabase → Vérifier les policies

**Debug :**
```bash
# Logs backend
tail -f backend/backend.log

# Vérifier token
curl -X POST "http://localhost:9000/api/treatments" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"medication_name":"Test",...}'
```

### Erreur : "Table user_treatments does not exist"

**Cause :** Migration 033 pas appliquée.

**Solution :** Appliquer la migration (voir section Déploiement)

---

## ✅ Checklist de validation

### Backend

- [ ] Migration 033 appliquée avec succès
- [ ] Tables créées : `medications_catalog`, `medication_details`, `user_treatments`
- [ ] Service `medication_service.py` fonctionnel
- [ ] Endpoints API testés :
  - [ ] `GET /api/medications/search`
  - [ ] `GET /api/medications/{id}`
  - [ ] `POST /api/treatments`
  - [ ] `GET /api/treatments`
  - [ ] `DELETE /api/treatments/{id}`
- [ ] Logs backend sans erreurs
- [ ] Cache local fonctionnel

### Mobile

- [ ] Pages créées : `/medication-detail`, `/add-treatment`
- [ ] Dépendance `@react-native-community/datetimepicker` installée
- [ ] Navigation fonctionnelle
- [ ] Formulaire complet validé
- [ ] Synchronisation avec backend testée
- [ ] États vides/loading/erreurs gérés
- [ ] Pas d'erreurs TypeScript/ESLint

### Integration

- [ ] Recherche → Fiche → Ajout fonctionnel end-to-end
- [ ] Données persistantes après redémarrage app
- [ ] Timezone correcte (Europe/Paris)
- [ ] Soft delete fonctionnel
- [ ] RLS testé (user A ne voit pas traitements user B)

---

## 📄 License et Responsabilité

**⚠️ Avertissement Médical**

Ce système est un outil d'aide à la gestion personnelle et ne remplace **PAS** :
- Une consultation médicale
- L'avis d'un pharmacien
- Les instructions de votre médecin

En cas de doute sur un médicament ou un traitement, **consultez un professionnel de santé**.

**Limitation de responsabilité**

Les données fournies par l'API BDPM sont indicatives. Pulse ne garantit pas l'exhaustivité ou l'exactitude des informations médicamenteuses.

---

**Fin du document - Version 1.0.0 - 4 Février 2026**
