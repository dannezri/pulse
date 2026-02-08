# Migration API Giygas - Guide Complet

**Date:** 4 Février 2026  
**Version:** 2.0.0  
**Type:** Refactoring majeur - Source médicaments

---

## 📋 Résumé des Changements

### ✅ Ce qui a été fait

**Refactoring complet du système médicaments :**
1. ❌ **Supprimé** : Dépendance à `open-medicaments.fr` (BDPM indirect)
2. ✅ **Ajouté** : API Giygas comme source unique (`https://medicaments-api.giygas.dev`)
3. ✅ **Ajouté** : Support présentations (CIP13/CIP7, prix, remboursement)
4. ✅ **Ajouté** : Scan de boîtes GS1 DataMatrix (GTIN → CIP13)
5. ✅ **Ajouté** : Composition détaillée + conditions de prescription

### ⚠️ Important : ICD-11 Inchangée

**ICD-11 n'a JAMAIS été utilisée pour les médicaments !**

- ✅ ICD-11 reste pour **conditions de santé / diagnostics** (inchangé)
- ✅ Table `user_conditions` utilise codes ICD-11 (inchangé)
- ✅ Endpoint `/api/terminology/icd11/search` toujours actif (conditions uniquement)

**Aucune modification d'ICD-11 nécessaire** ✨

---

## 🏗️ Fichiers Créés/Modifiés

### Nouveaux Fichiers (2)

1. **`backend/giygas_medication_service.py`** (495 lignes)
   - Service complet pour API Giygas
   - Méthodes : `search_medications()`, `get_by_cis()`, `get_by_cip13()`, `parse_gtin_to_cip13()`
   - Cache local intelligent
   - Support scan GS1 DataMatrix

2. **`database/migrations/034_giygas_medications_refactor.sql`**
   - Nouvelle table `drug_presentations` (CIP13/CIP7, prix, remboursement)
   - Extension `medication_details` (composition, conditions)
   - Fonction utilitaire `gtin_to_cip13()`
   - Vue `medications_full`

### Fichiers Modifiés (1)

1. **`backend/api_server.py`**
   - Import `GiygasMedicationService` (remplace `MedicationService`)
   - Endpoints mis à jour :
     - `GET /api/medications/search` (adapté Giygas)
     - `GET /api/medications/{id}` (adapté Giygas)
   - Nouvel endpoint : `POST /api/medications/scan` (GS1 DataMatrix)

### Fichiers Obsolètes (À conserver pour référence)

- ⚠️ `backend/medication_service.py` (ancienne version BDPM)
  - Ne pas supprimer immédiatement
  - Garder pour migration progressive des données
  - Pourra être supprimé après validation complète

---

## 🗂️ Architecture DB - Changements

### Nouvelle Table : `drug_presentations`

```sql
CREATE TABLE drug_presentations (
    id UUID PRIMARY KEY,
    item_id UUID REFERENCES medications_catalog(id),
    cip13 TEXT NOT NULL UNIQUE,        -- Identifiant unique présentation
    cip7 TEXT,                          -- Ancien format
    label TEXT,                         -- Libellé présentation
    price NUMERIC(10, 2),               -- Prix public TTC
    reimbursement_rate INTEGER,        -- Taux remboursement (0-100%)
    status TEXT,                        -- Statut AMM
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Utilité :**
- Permet recherche par CIP13 (scan de boîtes)
- Stocke prix et taux de remboursement
- Indexé pour recherche rapide

### Extension Table : `medication_details`

**Nouvelles colonnes :**
```sql
ALTER TABLE medication_details 
ADD COLUMN composition JSONB DEFAULT '[]'::jsonb,
ADD COLUMN conditions JSONB DEFAULT '{}'::jsonb;
```

**Contenu :**
- `composition` : `[{"substance": "PARACETAMOL", "dosage": "500", "unite": "mg"}]`
- `conditions` : Conditions de prescription/délivrance depuis Giygas

### Vue Utilitaire : `medications_full`

```sql
SELECT * FROM medications_full WHERE cis = '60001551';
```

Retourne médicament avec toutes ses données (composition, génériques, présentations).

---

## 🔌 API Giygas - Mapping

### Endpoint : `GET /medicament/{query}`

**Réponse Giygas :**
```json
{
  "cis": "60001551",
  "elementPharmaceutique": "DOLIPRANE 500 mg, comprimé",
  "formePharmaceutique": "comprimé",
  "composition": [
    {
      "substanceActive": "PARACETAMOL",
      "dosage": "500",
      "unite": "mg"
    }
  ],
  "generiques": [
    {
      "cis": "61234567",
      "elementPharmaceutique": "PARACETAMOL 500mg générique",
      "titulaire": "BIOGARAN"
    }
  ],
  "presentation": [
    {
      "cip13": "3400930001551",
      "cip7": "3000155",
      "libelle": "plaquette(s) de 16 comprimé(s)",
      "prix": 2.50,
      "tauxRemboursement": 65,
      "statut": "Commercialisée",
      "titulaire": "OPELLA HEALTHCARE FRANCE SAS"
    }
  ],
  "conditions": {
    "prescription": "Liste I",
    "delivrance": "Prescription médicale facultative"
  }
}
```

### Mapping vers DB

| Champ Giygas | Table Pulse | Colonne |
|---|---|---|
| `cis` | `medications_catalog` | `external_id` |
| `elementPharmaceutique` | `medications_catalog` | `name` |
| `formePharmaceutique` | `medications_catalog` | `form` |
| `composition` | `medication_details` | `composition` |
| `generiques` | `medication_details` | `generics` |
| `presentation` | `drug_presentations` | (table séparée) |
| `conditions` | `medication_details` | `conditions` |

---

## 🚀 Nouveaux Endpoints

### 1. Recherche (modifié)

**`GET /api/medications/search?q=doliprane`**

**Avant (BDPM) :**
```json
{
  "query": "doliprane",
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
  "query": "doliprane",
  "results": [{
    "cis": "60001551",
    "name": "DOLIPRANE 500 mg, comprimé",
    "form": "comprimé",
    "laboratory": "OPELLA HEALTHCARE FRANCE SAS",
    "active_substance": "PARACETAMOL",
    "source": "giygas"
  }],
  "count": 2
}
```

### 2. Détails (modifié)

**`GET /api/medications/60001551`**

**Après (Giygas) :**
```json
{
  "cis": "60001551",
  "name": "DOLIPRANE 500 mg, comprimé",
  "form": "comprimé",
  "laboratory": "OPELLA HEALTHCARE FRANCE SAS",
  "active_substance": "PARACETAMOL",
  "composition": [
    {"substance": "PARACETAMOL", "dosage": "500", "unite": "mg"}
  ],
  "generics": [
    {"cis": "...", "name": "...", "laboratory": "..."}
  ],
  "presentations": [
    {
      "cip13": "3400930001551",
      "cip7": "3000155",
      "label": "plaquette(s) de 16 comprimé(s)",
      "price": 2.50,
      "reimbursement_rate": 65
    }
  ],
  "conditions": {
    "prescription": "Liste I",
    "delivrance": "Prescription médicale facultative"
  }
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
2. Convertit GTIN → CIP13
3. Recherche présentation par CIP13
4. Récupère médicament complet par CIS

---

## 📊 Schéma de Flow

### Ancien Flow (BDPM)

```
User → Recherche "doliprane"
     → Backend → open-medicaments.fr API
                 → Cache medications_catalog
                 → Retour résultats
```

### Nouveau Flow (Giygas)

```
User → Recherche "doliprane"
     → Backend → API Giygas /medicament/doliprane
                 → Cache medications_catalog
                 → Cache medication_details (composition, génériques)
                 → Cache drug_presentations (CIP13, prix)
                 → Retour résultats enrichis
```

### Flow Scan Boîte (nouveau)

```
User → Scan code-barres → GTIN: "34009300015517"
     → Backend → parse_gtin_to_cip13() → CIP13: "3400930001551"
                 → Recherche drug_presentations
                 → Trouve CIS: "60001551"
                 → API Giygas /medicament/id/60001551
                 → Fiche médicament complète
```

---

## 🔄 Migration des Données

### Stratégie de Migration

**Option 1 : Migration progressive (recommandé)**
1. Nouvelles données → source='giygas'
2. Anciennes données → source='bdpm' (conservées)
3. Coexistence temporaire
4. Migration batch ultérieure si besoin

**Option 2 : Migration immédiate**
```sql
-- Mettre à jour toutes les sources BDPM → Giygas
UPDATE medications_catalog 
SET source = 'giygas' 
WHERE source = 'bdpm';
```

⚠️ **Recommandation :** Option 1 (progressive) pour éviter les régressions.

### Vérification Post-Migration

```sql
-- 1. Vérifier table drug_presentations créée
SELECT * FROM information_schema.tables 
WHERE table_name = 'drug_presentations';

-- 2. Vérifier fonction gtin_to_cip13
SELECT gtin_to_cip13('34009300015517'); -- Doit retourner: 3400930001551

-- 3. Vérifier vue medications_full
SELECT * FROM medications_full LIMIT 5;

-- 4. Compter médicaments par source
SELECT source, COUNT(*) 
FROM medications_catalog 
GROUP BY source;
```

---

## 🧪 Tests

### Test 1 : Recherche Médicament

```bash
# Test recherche
curl "http://localhost:9000/api/medications/search?q=doliprane"

# Expected
{
  "query": "doliprane",
  "results": [
    {
      "cis": "60001551",
      "name": "DOLIPRANE 500 mg, comprimé",
      "form": "comprimé",
      "laboratory": "OPELLA HEALTHCARE FRANCE SAS",
      "active_substance": "PARACETAMOL",
      "source": "giygas"
    }
  ],
  "count": 1
}
```

### Test 2 : Détails Médicament

```bash
# Test détails par CIS
curl "http://localhost:9000/api/medications/60001551"

# Expected
{
  "cis": "60001551",
  "composition": [...],
  "generics": [...],
  "presentations": [...]
}
```

### Test 3 : Scan Boîte

```bash
# Test scan GS1 DataMatrix
curl -X POST "http://localhost:9000/api/medications/scan" \
  -H "Content-Type: application/json" \
  -d '{"gtin": "34009300015517"}'

# Expected
{
  "gtin": "34009300015517",
  "cip13": "3400930001551",
  "medication": {
    "cis": "60001551",
    ...
  }
}
```

### Test 4 : Conversion GTIN

```sql
-- Test fonction SQL
SELECT gtin_to_cip13('34009300015517'); -- GTIN-14
SELECT gtin_to_cip13('3400930001551');  -- GTIN-13
```

---

## ⚠️ Points de Vigilance

### 1. GTIN ≠ Toujours CIP13

**Problèmes possibles :**
- GTIN peut avoir plusieurs formats (8, 12, 13, 14 chiffres)
- Conversion GTIN-14 → CIP13 : enlève 1er chiffre (packaging indicator)
- GTIN-13 = CIP13 directement

**Solution :**
- Fonction `parse_gtin_to_cip13()` gère les cas
- Log si format invalide
- Retour null si non convertible

### 2. CIP13 non trouvé dans DB

**Causes :**
- Médicament jamais recherché auparavant
- Présentation non commercialisée
- Erreur de scan

**Solution :**
- Cache au fur et à mesure des recherches
- Message explicite à l'utilisateur
- Proposer recherche manuelle

### 3. API Giygas Indisponible

**Solution :**
- Cache local toujours interrogé d'abord
- Fallback sur cache si API timeout
- Logs d'erreurs explicites

### 4. Composition vs Substance Active

**Différence :**
- Composition = liste complète (ex: `[{"substance": "PARACETAMOL", "dosage": "500", "unite": "mg"}]`)
- Substance active = première substance (ex: `"PARACETAMOL"`)

**Stockage :**
- `medication_details.composition` : JSONB complet
- `medications_catalog.active_substance` : TEXT principal (pour recherche rapide)

---

## 📝 TODO Restant

### Phase 1 : Validation

- [ ] Tester recherche sur 10+ médicaments courants
- [ ] Tester scan boîte avec GTIN réels
- [ ] Vérifier cache fonctionne (2ème recherche plus rapide)
- [ ] Vérifier génériques retournés correctement

### Phase 2 : Enrichissement

- [ ] Ajouter code ATC (si disponible via autre source)
- [ ] Ajouter URL notice officielle (ANSM)
- [ ] Lier conditions ICD-11 ↔ médicaments (indications)
- [ ] Améliorer présentations (photos boîtes)

### Phase 3 : Mobile

- [ ] Adapter composants pour afficher composition
- [ ] Ajouter onglet "Présentations" avec prix/remboursement
- [ ] Intégrer scanner code-barres (caméra)
- [ ] Flow scan → fiche → ajout traitement

### Phase 4 : Optimisations

- [ ] Batch import médicaments courants (cache pré-rempli)
- [ ] Compression cache (raw_data peut être gros)
- [ ] TTL cache configurable
- [ ] Logs détaillés performances API Giygas

---

## 🔗 Ressources

### API Giygas

- **Base URL:** `https://medicaments-api.giygas.dev`
- **Endpoints :**
  - `GET /medicament/{query}` - Recherche par nom
  - `GET /medicament/id/{cis}` - Détails par CIS
- **Format :** JSON
- **Rate limit :** À déterminer
- **Documentation :** Fournie par utilisateur

### Standards

- **GS1 DataMatrix :** Standard international code-barres pharmaceutique
- **GTIN :** Global Trade Item Number (13 ou 14 chiffres)
- **CIP13 :** Code Identifiant de Présentation (13 chiffres, France)
- **CIS :** Code Identifiant de Spécialité (ANSM)

### Réglementation France

- **ANSM :** Agence nationale de sécurité du médicament
- **BDPM :** Base de Données Publique des Médicaments
- **AMM :** Autorisation de Mise sur le Marché

---

## ✅ Checklist Déploiement

### Backend

- [ ] Migration 034 appliquée (Supabase SQL Editor)
- [ ] Fichier `giygas_medication_service.py` présent
- [ ] `api_server.py` modifié (import + endpoints)
- [ ] Backend redémarré sans erreurs
- [ ] Logs backend propres (pas d'erreurs Giygas)

### Base de Données

- [ ] Table `drug_presentations` existe
- [ ] Colonnes `composition` et `conditions` dans `medication_details`
- [ ] Fonction `gtin_to_cip13()` créée
- [ ] Vue `medications_full` accessible
- [ ] RLS activé sur `drug_presentations`

### Tests

- [ ] `curl /api/medications/search?q=test` → 200 OK
- [ ] `curl /api/medications/{cis}` → Détails complets
- [ ] `curl -X POST /api/medications/scan` → Conversion GTIN OK
- [ ] Vérifier cache (2ème recherche identique plus rapide)

### Mobile (à venir)

- [ ] Adapter page recherche (champs Giygas)
- [ ] Adapter fiche médicament (composition, présentations)
- [ ] Ajouter scanner code-barres
- [ ] Tester flow scan → fiche → ajout

---

## 🎯 Résumé Exécutif

### Ce qui change

1. **Source médicaments :** BDPM/open-medicaments → API Giygas
2. **Données enrichies :** Composition, présentations (CIP13/CIP7, prix), conditions
3. **Nouveau flow :** Scan GS1 DataMatrix (GTIN → CIP13 → Médicament)

### Ce qui ne change PAS

1. **ICD-11 :** Toujours utilisée pour conditions de santé (inchangé)
2. **Tables traitements :** `user_treatments` inchangée
3. **Endpoints traitements :** `/api/treatments` inchangés
4. **Mobile :** Formulaire ajout traitement inchangé (hors fiche)

### Impact utilisateur

- ✅ Recherche plus riche (composition, génériques, prix)
- ✅ Scan de boîtes (QR code médicaments)
- ✅ Prix et remboursement visibles
- ⚠️ Migration progressive (anciennes données conservées)

---

**Fin du guide - Version 2.0.0 - 4 Février 2026**
