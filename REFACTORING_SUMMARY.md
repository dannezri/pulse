# Refactoring API Giygas - Résumé Exécutif

**Date:** 4 Février 2026  
**Durée estimée déploiement:** 15 minutes  
**Impact:** Majeur (système médicaments)

---

## ✅ Ce qui a été modifié

### 📦 Fichiers Créés (3)

1. **`backend/giygas_medication_service.py`** (495 lignes)
   - Service complet API Giygas
   - Remplace `medication_service.py` (ancien BDPM)
   - Méthodes : search, get_by_cis, get_by_cip13, parse_gtin

2. **`database/migrations/034_giygas_medications_refactor.sql`**
   - Nouvelle table `drug_presentations` (CIP13/CIP7, prix)
   - Extension `medication_details` (composition, conditions)
   - Fonction `gtin_to_cip13()` pour scan boîtes
   - Vue `medications_full`

3. **`GIYGAS_MIGRATION_GUIDE.md`** (documentation complète)
   - Architecture, mapping, tests, troubleshooting

### 📝 Fichiers Modifiés (1)

1. **`backend/api_server.py`**
   - Ligne 38 : `from giygas_medication_service import GiygasMedicationService`
   - Ligne 60 : `medication_service = GiygasMedicationService(...)`
   - Endpoints adaptés : `/api/medications/search`, `/api/medications/{id}`
   - Nouvel endpoint : `POST /api/medications/scan` (GS1 DataMatrix)

### 🗑️ Fichiers Obsolètes (À conserver temporairement)

1. **`backend/medication_service.py`**
   - Ancienne version BDPM/open-medicaments
   - ⚠️ Ne pas supprimer immédiatement
   - Pourra être retiré après validation complète

---

## 🎯 Résultat

### Avant (BDPM/open-medicaments.fr)

```python
# Recherche limitée
{
  "cis": "60001551",
  "name": "Doliprane 500mg",
  "form": "Comprimé",
  "laboratory": "Sanofi"
}

# Pas de :
# - Composition détaillée
# - Prix/remboursement
# - Scan boîtes
```

### Après (API Giygas)

```python
# Recherche enrichie
{
  "cis": "60001551",
  "name": "DOLIPRANE 500 mg, comprimé",
  "form": "comprimé",
  "laboratory": "OPELLA HEALTHCARE FRANCE SAS",
  "active_substance": "PARACETAMOL",
  "composition": [
    {"substance": "PARACETAMOL", "dosage": "500", "unite": "mg"}
  ],
  "generics": [...],
  "presentations": [
    {"cip13": "3400930001551", "price": 2.50, "reimbursement_rate": 65}
  ],
  "conditions": {...}
}

# Nouveau : Scan boîtes (GTIN → CIP13 → Médicament)
```

---

## ⚠️ Points de Vigilance

### 1. ICD-11 Inchangée ✅

**ICD-11 n'a JAMAIS été utilisée pour les médicaments.**

- ✅ ICD-11 reste pour diagnostics/conditions de santé
- ✅ Endpoint `/api/terminology/icd11/search` inchangé
- ✅ Table `user_conditions` inchangée

**Aucune action requise sur ICD-11.**

### 2. GTIN → CIP13 : Limitations

- ⚠️ GTIN-14 → CIP13 : Enlève 1er chiffre (packaging indicator)
- ⚠️ GTIN-13 = CIP13 directement
- ⚠️ Formats invalides : Retour null + log

**Solution :** Fonction `parse_gtin_to_cip13()` gère automatiquement.

### 3. Migration Progressive

**Stratégie :**
- Nouvelles données → `source='giygas'`
- Anciennes données → `source='bdpm'` (conservées)
- Coexistence temporaire

**Pas de perte de données.**

---

## 🚀 Déploiement

### Étape 1 : Migration DB

```bash
# Via Supabase Dashboard (recommandé)
1. Ouvrir https://app.supabase.com
2. SQL Editor → New Query
3. Copier-coller database/migrations/034_giygas_medications_refactor.sql
4. Run
```

### Étape 2 : Redémarrer Backend

```bash
cd backend
./restart_backend.sh
# ou
pkill -f "python.*api_server"
python api_server.py
```

### Étape 3 : Vérifier

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

### Étape 4 : Vérifier DB

```sql
-- Vérifier table drug_presentations
SELECT * FROM drug_presentations LIMIT 1;

-- Vérifier fonction GTIN
SELECT gtin_to_cip13('34009300015517');
-- Expected: 3400930001551

-- Vérifier vue medications_full
SELECT * FROM medications_full LIMIT 5;
```

---

## 📊 Nouveaux Endpoints

### 1. Recherche (adapté)

**`GET /api/medications/search?q=doliprane`**

Retourne médicaments avec composition, substance active, laboratoire.

### 2. Détails (adapté)

**`GET /api/medications/60001551`**

Retourne médicament complet : composition, génériques, présentations (CIP13, prix), conditions.

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

---

## 🗂️ Schéma DB - Changements

### Nouvelle Table : `drug_presentations`

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID | Clé primaire |
| `item_id` | UUID | FK vers medications_catalog |
| `cip13` | TEXT | **Code CIP 13 chiffres (unique)** |
| `cip7` | TEXT | Code CIP 7 chiffres (ancien) |
| `label` | TEXT | Libellé présentation |
| `price` | NUMERIC | Prix public TTC (€) |
| `reimbursement_rate` | INTEGER | Taux remboursement (0-100%) |
| `status` | TEXT | Statut AMM |

**Index :** `cip13` (unique), `cip7`, `item_id`

### Extension : `medication_details`

**Nouvelles colonnes :**
- `composition` JSONB : Composition détaillée
- `conditions` JSONB : Conditions de prescription

---

## 📋 Checklist de Validation

### Backend

- [ ] Migration 034 appliquée sans erreurs
- [ ] Fichier `giygas_medication_service.py` présent
- [ ] `api_server.py` modifié (import GiygasMedicationService)
- [ ] Backend redémarré : `python api_server.py` → 0 erreur

### Base de Données

- [ ] Table `drug_presentations` existe
- [ ] Fonction `gtin_to_cip13('34009300015517')` → `3400930001551`
- [ ] Vue `medications_full` accessible
- [ ] RLS activé sur `drug_presentations`

### Endpoints

- [ ] `GET /api/medications/search?q=test` → 200 OK
- [ ] `GET /api/medications/60001551` → Détails complets
- [ ] `POST /api/medications/scan` → Conversion GTIN OK

### Mobile (à adapter)

- [ ] Page recherche : Adapter pour champs Giygas
- [ ] Fiche médicament : Afficher composition, présentations
- [ ] (Optionnel) Ajouter scanner code-barres

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

- [ ] Adapter composants affichage composition
- [ ] Ajouter onglet "Présentations" (prix, remboursement)
- [ ] Intégrer scanner caméra (GS1 DataMatrix)
- [ ] Flow scan → fiche → ajout traitement

---

## 📚 Documentation

**Guide complet :** `GIYGAS_MIGRATION_GUIDE.md`

Contient :
- Architecture détaillée
- Mapping API Giygas → DB
- Flow scan boîtes (GTIN → CIP13)
- Tests complets
- Troubleshooting

---

## ✨ Résumé 1 Ligne

**API BDPM/open-medicaments → API Giygas + scan boîtes (GTIN→CIP13) + composition/prix/remboursement**

---

**Fin du résumé - Version 2.0.0 - 4 Février 2026**
