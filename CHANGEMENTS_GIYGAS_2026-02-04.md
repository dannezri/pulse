# Changements API Giygas - 4 Février 2026

## 📦 Résumé Exécutif

**Objectif :** Remplacer l'API BDPM/open-medicaments.fr par l'API Giygas comme source unique pour les médicaments.

**Impact :** Majeur (système médicaments complet)

**Durée déploiement :** 15 minutes

**Status ICD-11 :** ✅ Inchangée (utilisée uniquement pour conditions de santé)

---

## 📂 Fichiers Créés (8)

### Backend (3)

1. **`backend/giygas_medication_service.py`** (495 lignes)
   - Service complet API Giygas
   - Méthodes : `search_medications()`, `get_by_cis()`, `get_by_cip13()`, `parse_gtin_to_cip13()`
   - Cache local intelligent (Supabase)
   - Support scan GS1 DataMatrix

2. **`backend/migrate_bdpm_to_giygas.py`** (script migration optionnel)
   - Migre données BDPM → Giygas
   - Usage : `python migrate_bdpm_to_giygas.py --dry-run`

3. **`backend/tests/test_giygas_medication_service.py`** (tests unitaires)
   - 15+ tests unitaires
   - Tests d'intégration avec API réelle
   - Usage : `pytest backend/tests/test_giygas_medication_service.py -v`

### Base de Données (1)

4. **`database/migrations/034_giygas_medications_refactor.sql`**
   - Nouvelle table `drug_presentations` (CIP13/CIP7, prix, remboursement)
   - Extension `medication_details` (composition, conditions)
   - Fonction `gtin_to_cip13()` pour conversion GTIN → CIP13
   - Vue `medications_full` pour requêtes simplifiées
   - RLS policies

### Documentation (3)

5. **`GIYGAS_MIGRATION_GUIDE.md`** (guide complet, 600+ lignes)
   - Architecture détaillée
   - Mapping API → DB
   - Flow scan boîtes (GTIN → CIP13 → Médicament)
   - Tests complets
   - Troubleshooting

6. **`REFACTORING_SUMMARY.md`** (résumé exécutif)
   - Vue d'ensemble rapide
   - Checklist de déploiement
   - TODO future

7. **`docs/giygas_api_examples.md`** (exemples API)
   - Exemples réponses Giygas
   - Mapping vers DB Pulse
   - Cas particuliers
   - Limites connues

### Scripts (1)

8. **`DEPLOY_GIYGAS.sh`** (script déploiement automatisé)
   - Vérifications préalables
   - Application migration DB
   - Redémarrage backend
   - Tests de validation
   - Usage : `./DEPLOY_GIYGAS.sh`

9. **`test-giygas-api.sh`** (script tests)
   - 5 tests automatisés
   - Vérification endpoints
   - Vérification DB
   - Usage : `./test-giygas-api.sh`

---

## 📝 Fichiers Modifiés (2)

### Backend (2)

1. **`backend/api_server.py`**
   - **Ligne 38 :** `from giygas_medication_service import GiygasMedicationService`
   - **Ligne 60 :** `medication_service = GiygasMedicationService(...)`
   - **Endpoints adaptés :**
     - `GET /api/medications/search` (adapté Giygas)
     - `GET /api/medications/{id}` (adapté Giygas)
   - **Nouvel endpoint :**
     - `POST /api/medications/scan` (GS1 DataMatrix)

2. **`backend/medication_service.py`**
   - **Header ajouté :** Marqué comme OBSOLÈTE/LEGACY
   - **Warning log :** Indique utiliser `giygas_medication_service.py`
   - **Action future :** Peut être supprimé après validation complète

---

## 🗂️ Schéma DB - Changements

### Nouvelle Table : `drug_presentations`

```sql
CREATE TABLE drug_presentations (
    id UUID PRIMARY KEY,
    item_id UUID REFERENCES medications_catalog(id),
    cip13 TEXT NOT NULL UNIQUE,        -- Identifiant unique présentation
    cip7 TEXT,                          -- Ancien format
    label TEXT,                         -- Libellé présentation
    price NUMERIC(10, 2),               -- Prix public TTC (€)
    reimbursement_rate INTEGER,        -- Taux remboursement (0-100%)
    status TEXT,                        -- Statut AMM
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Index :** `cip13` (unique), `cip7`, `item_id`

**Utilité :**
- Permet recherche par CIP13 (scan de boîtes)
- Stocke prix et taux de remboursement
- Support multi-présentations par médicament

### Extension : `medication_details`

**Nouvelles colonnes :**
```sql
ALTER TABLE medication_details 
ADD COLUMN composition JSONB DEFAULT '[]'::jsonb,
ADD COLUMN conditions JSONB DEFAULT '{}'::jsonb;
```

**Contenu :**
- `composition` : `[{"substance": "PARACETAMOL", "dosage": "500", "unite": "mg"}]`
- `conditions` : `{"prescription": "Liste I", "delivrance": "..."}`

### Nouvelle Vue : `medications_full`

```sql
CREATE VIEW medications_full AS
SELECT 
    mc.*,
    md.composition,
    md.generics,
    md.conditions,
    md.notice_url
FROM medications_catalog mc
LEFT JOIN medication_details md ON mc.id = md.medication_id;
```

**Utilité :** Requête simplifiée pour récupérer médicament complet.

### Nouvelle Fonction : `gtin_to_cip13()`

```sql
SELECT gtin_to_cip13('34009300015517');
-- Retourne: 3400930001551
```

**Utilité :** Convertit GTIN (GS1 DataMatrix) en CIP13.

---

## 🔌 Nouveaux Endpoints

### 1. Recherche (adapté)

**`GET /api/medications/search?q=doliprane`**

**Avant (BDPM) :**
```json
{
  "results": [{
    "id": "CIS-60001551",
    "name": "Doliprane 500mg",
    "source": "bdpm"
  }]
}
```

**Après (Giygas) :**
```json
{
  "results": [{
    "cis": "60001551",
    "name": "DOLIPRANE 500 mg, comprimé",
    "form": "comprimé",
    "laboratory": "OPELLA HEALTHCARE FRANCE SAS",
    "active_substance": "PARACETAMOL",
    "source": "giygas"
  }]
}
```

### 2. Détails (adapté)

**`GET /api/medications/60001551`**

**Après (Giygas) :**
```json
{
  "cis": "60001551",
  "name": "DOLIPRANE 500 mg, comprimé",
  "composition": [
    {"substance": "PARACETAMOL", "dosage": "500", "unite": "mg"}
  ],
  "generics": [...],
  "presentations": [
    {"cip13": "3400930001551", "price": 2.50, "reimbursement_rate": 65}
  ],
  "conditions": {...}
}
```

### 3. Scan Boîte (nouveau) ✨

**`POST /api/medications/scan`**

**Body :**
```json
{
  "gtin": "34009300015517"
}
```

**Réponse :**
```json
{
  "gtin": "34009300015517",
  "cip13": "3400930001551",
  "medication": {
    "cis": "60001551",
    "name": "DOLIPRANE 500 mg, comprimé",
    ...
  }
}
```

**Flow :**
1. Scanner lit GS1 DataMatrix → GTIN
2. Backend convertit GTIN → CIP13 (`parse_gtin_to_cip13()`)
3. Recherche présentation par CIP13 (`drug_presentations`)
4. Récupère médicament complet par CIS

---

## ⚠️ Points de Vigilance

### 1. ICD-11 Inchangée ✅

**ICD-11 n'a JAMAIS été utilisée pour les médicaments.**

- ✅ ICD-11 reste pour diagnostics/conditions de santé
- ✅ Endpoint `/api/terminology/icd11/search` inchangé
- ✅ Table `user_conditions` inchangée
- ✅ Table `condition_energy_impacts` inchangée

**Aucune action requise sur ICD-11.**

### 2. GTIN → CIP13 : Limitations

- ⚠️ GTIN-14 → CIP13 : Enlève 1er chiffre (packaging indicator)
- ⚠️ GTIN-13 = CIP13 directement
- ⚠️ Formats invalides : Retour `null` + log

**Solution :** Fonction `parse_gtin_to_cip13()` gère automatiquement.

### 3. Migration Progressive

**Stratégie :**
- Nouvelles données → `source='giygas'`
- Anciennes données → `source='bdpm'` (conservées)
- Coexistence temporaire

**Pas de perte de données.**

### 4. Code ATC Non Fourni

L'API Giygas ne fournit **pas** le code ATC.

**Solution :**
- Récupérer depuis autre source (WHO ATC/DDD Index)
- Ou laisser `NULL` dans `medications_catalog.atc_code`

### 5. Notice Médicament

L'API Giygas ne fournit **pas** le texte de la notice.

**Solution :**
- Récupérer depuis ANSM
- URL : `https://base-donnees-publique.medicaments.gouv.fr/affichageDoc.php?specid={cis}&typedoc=N`

---

## 🚀 Déploiement

### Option 1 : Script Automatisé (recommandé)

```bash
./DEPLOY_GIYGAS.sh
```

Le script effectue :
1. Vérifications préalables
2. Application migration DB
3. Redémarrage backend
4. Tests de validation

### Option 2 : Manuel

**Étape 1 : Migration DB**

```bash
# Via Supabase Dashboard
1. Ouvrir https://app.supabase.com
2. SQL Editor → New Query
3. Copier-coller database/migrations/034_giygas_medications_refactor.sql
4. Run
```

**Étape 2 : Redémarrer Backend**

```bash
cd backend
pkill -f "python.*api_server"
python api_server.py
```

**Étape 3 : Vérifier**

```bash
./test-giygas-api.sh
```

---

## 🧪 Tests

### Tests Automatisés

```bash
# Tests API
./test-giygas-api.sh

# Tests unitaires
pytest backend/tests/test_giygas_medication_service.py -v
```

### Tests Manuels

```bash
# Test recherche
curl "http://localhost:9000/api/medications/search?q=doliprane"

# Test détails
curl "http://localhost:9000/api/medications/60001551"

# Test scan
curl -X POST "http://localhost:9000/api/medications/scan" \
  -H "Content-Type: application/json" \
  -d '{"gtin": "34009300015517"}'
```

---

## 📋 Checklist de Validation

### Backend

- [ ] Migration 034 appliquée sans erreurs
- [ ] Fichier `giygas_medication_service.py` présent
- [ ] `api_server.py` modifié (import GiygasMedicationService)
- [ ] Backend redémarré : `python api_server.py` → 0 erreur
- [ ] Logs backend propres (pas d'erreurs Giygas)

### Base de Données

- [ ] Table `drug_presentations` existe
- [ ] Fonction `gtin_to_cip13('34009300015517')` → `3400930001551`
- [ ] Vue `medications_full` accessible
- [ ] RLS activé sur `drug_presentations`

### Endpoints

- [ ] `GET /api/medications/search?q=test` → 200 OK
- [ ] `GET /api/medications/60001551` → Détails complets
- [ ] `POST /api/medications/scan` → Conversion GTIN OK

### Tests

- [ ] `./test-giygas-api.sh` → Tous tests passent
- [ ] `pytest backend/tests/test_giygas_medication_service.py` → OK

---

## 🎯 TODO Future

### Phase 1 : Validation (cette semaine)

- [ ] Tester 20+ médicaments courants
- [ ] Vérifier cache fonctionne (2ème recherche rapide)
- [ ] Vérifier génériques retournés correctement
- [ ] Tester scan avec GTIN réels

### Phase 2 : Enrichissement (semaine prochaine)

- [ ] Ajouter code ATC (via source complémentaire)
- [ ] Ajouter URL notice ANSM
- [ ] Lier conditions ICD-11 ↔ indications médicaments
- [ ] Photos boîtes médicaments

### Phase 3 : Mobile (2 semaines)

- [ ] Adapter page recherche (champs Giygas)
- [ ] Adapter fiche médicament (composition, présentations)
- [ ] Ajouter scanner caméra (GS1 DataMatrix)
- [ ] Flow scan → fiche → ajout traitement

### Phase 4 : Migration Données (optionnel)

- [ ] Exécuter `python backend/migrate_bdpm_to_giygas.py --dry-run`
- [ ] Valider résultats
- [ ] Exécuter migration complète
- [ ] Supprimer `backend/medication_service.py` (LEGACY)

---

## 📚 Documentation

### Guides Complets

1. **`GIYGAS_MIGRATION_GUIDE.md`** (600+ lignes)
   - Architecture détaillée
   - Mapping API → DB
   - Flow scan boîtes
   - Tests complets
   - Troubleshooting

2. **`REFACTORING_SUMMARY.md`**
   - Vue d'ensemble rapide
   - Checklist de déploiement
   - TODO future

3. **`docs/giygas_api_examples.md`**
   - Exemples réponses Giygas
   - Mapping vers DB Pulse
   - Cas particuliers
   - Limites connues

### Scripts

1. **`DEPLOY_GIYGAS.sh`** - Déploiement automatisé
2. **`test-giygas-api.sh`** - Tests automatisés
3. **`backend/migrate_bdpm_to_giygas.py`** - Migration données (optionnel)

---

## 🎯 Résumé 1 Ligne

**API BDPM/open-medicaments → API Giygas + scan boîtes (GTIN→CIP13) + composition/prix/remboursement**

---

## 📊 Statistiques

- **Fichiers créés :** 9
- **Fichiers modifiés :** 2
- **Lignes de code :** ~1500
- **Tables DB créées :** 1 (`drug_presentations`)
- **Colonnes ajoutées :** 2 (`composition`, `conditions`)
- **Fonctions SQL créées :** 1 (`gtin_to_cip13`)
- **Vues créées :** 1 (`medications_full`)
- **Endpoints créés :** 1 (`POST /api/medications/scan`)
- **Endpoints adaptés :** 2 (`GET /search`, `GET /{id}`)
- **Tests unitaires :** 15+
- **Durée déploiement :** 15 minutes
- **Impact utilisateur :** Majeur (données enrichies)

---

**Fin du document - Version 1.0 - 4 Février 2026**
