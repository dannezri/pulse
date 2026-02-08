# Documentation API Giygas - Pulse

Documentation complète de l'intégration API Giygas pour le système médicaments.

---

## 📚 Documents Disponibles

### 1. Guide de Migration Complet

**Fichier :** `../GIYGAS_MIGRATION_GUIDE.md` (600+ lignes)

**Contenu :**
- Architecture détaillée (DB, Backend, Mobile)
- Mapping API Giygas → DB Pulse
- Flow scan boîtes (GTIN → CIP13 → Médicament)
- Nouveaux endpoints
- Tests complets
- Troubleshooting
- TODO restant

**Public :** Développeurs backend/fullstack

---

### 2. Résumé Exécutif

**Fichier :** `../REFACTORING_SUMMARY.md`

**Contenu :**
- Vue d'ensemble rapide (5 minutes de lecture)
- Fichiers créés/modifiés
- Schéma DB - Changements
- Checklist de déploiement
- TODO future

**Public :** Chefs de projet, développeurs

---

### 3. Exemples API Giygas

**Fichier :** `giygas_api_examples.md`

**Contenu :**
- Exemples réponses API Giygas (JSON)
- Mapping vers DB Pulse
- Cas particuliers (génériques, non commercialisés)
- Limites connues (ATC, notice, photos)
- Exemples d'utilisation (frontend)

**Public :** Développeurs frontend/mobile

---

### 4. Changements Détaillés

**Fichier :** `../CHANGEMENTS_GIYGAS_2026-02-04.md`

**Contenu :**
- Liste exhaustive des fichiers créés/modifiés
- Schéma DB complet
- Nouveaux endpoints
- Points de vigilance
- Checklist de validation
- Statistiques

**Public :** Tous (référence complète)

---

## 🚀 Déploiement

### Script Automatisé

```bash
cd /Users/dannezri/Desktop/Pulse
./DEPLOY_GIYGAS.sh
```

Le script effectue :
1. Vérifications préalables
2. Application migration DB
3. Redémarrage backend
4. Tests de validation

**Durée :** 15 minutes

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

## 📊 Architecture

### Backend

```
backend/
├── giygas_medication_service.py    # Service principal (495 lignes)
├── api_server.py                   # Endpoints (modifié)
├── medication_service.py           # OBSOLÈTE (LEGACY)
├── migrate_bdpm_to_giygas.py       # Script migration (optionnel)
└── tests/
    └── test_giygas_medication_service.py  # Tests unitaires
```

### Base de Données

```sql
-- Nouvelle table
drug_presentations (cip13, cip7, prix, remboursement)

-- Extension
medication_details (composition, conditions)

-- Nouvelle fonction
gtin_to_cip13(gtin TEXT) → cip13 TEXT

-- Nouvelle vue
medications_full (médicament complet)
```

### API

```
GET  /api/medications/search?q=...    # Recherche (adapté Giygas)
GET  /api/medications/{id}            # Détails (adapté Giygas)
POST /api/medications/scan            # Scan boîte (nouveau)
```

---

## 🔑 Concepts Clés

### CIS (Code Identifiant de Spécialité)

Identifiant unique d'un médicament en France (ex: `60001551`).

**Utilisation :**
- Clé primaire dans `medications_catalog.external_id`
- Endpoint : `GET /api/medications/{cis}`

### CIP13 (Code Identifiant de Présentation)

Identifiant unique d'une présentation commerciale (ex: `3400930001551`).

**Utilisation :**
- Clé primaire dans `drug_presentations.cip13`
- Scan de boîtes (GS1 DataMatrix)

### GTIN (Global Trade Item Number)

Code-barres international (13 ou 14 chiffres).

**Conversion :**
- GTIN-14 → CIP13 : Enlève 1er chiffre
- GTIN-13 → CIP13 : Déjà au bon format

**Fonction :** `gtin_to_cip13(gtin)`

### GS1 DataMatrix

Format de code-barres 2D utilisé sur les boîtes de médicaments.

**Flow :**
1. Scanner lit DataMatrix → GTIN
2. Convertit GTIN → CIP13
3. Recherche présentation par CIP13
4. Récupère médicament complet par CIS

---

## 📖 Exemples

### Recherche Médicament

```bash
curl "http://localhost:9000/api/medications/search?q=doliprane"
```

**Réponse :**
```json
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

### Détails Médicament

```bash
curl "http://localhost:9000/api/medications/60001551"
```

**Réponse :**
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

### Scan Boîte

```bash
curl -X POST "http://localhost:9000/api/medications/scan" \
  -H "Content-Type: application/json" \
  -d '{"gtin": "34009300015517"}'
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

## ⚠️ Limites Connues

### 1. Code ATC Non Fourni

L'API Giygas ne fournit **pas** le code ATC.

**Solution :**
- Récupérer depuis WHO ATC/DDD Index
- Ou laisser `NULL`

### 2. Notice Médicament

L'API Giygas ne fournit **pas** le texte de la notice.

**Solution :**
- Récupérer depuis ANSM
- URL : `https://base-donnees-publique.medicaments.gouv.fr/affichageDoc.php?specid={cis}&typedoc=N`

### 3. Photos Boîtes

L'API Giygas ne fournit **pas** de photos.

**Solution :**
- Scraper depuis sites pharmaceutiques (légalité à vérifier)
- Ou laisser vide

### 4. Interactions Médicamenteuses

L'API Giygas ne fournit **pas** les interactions.

**Solution :**
- Utiliser base Thériaque ou Vidal
- Ou implémenter logique métier

---

## 🔗 Ressources Externes

### API Giygas

- **Base URL :** `https://medicaments-api.giygas.dev`
- **Endpoints :**
  - `GET /medicament/{query}` - Recherche par nom
  - `GET /medicament/id/{cis}` - Détails par CIS

### Standards

- **GS1 DataMatrix :** https://www.gs1.org/standards/barcodes/datamatrix
- **GTIN :** https://www.gs1.org/standards/id-keys/gtin
- **CIP13 :** https://www.vidal.fr/medicaments/glossaire/cip.html

### Réglementation France

- **ANSM :** https://ansm.sante.fr
- **BDPM :** https://base-donnees-publique.medicaments.gouv.fr
- **AMM :** https://ansm.sante.fr/page/autorisations-de-mise-sur-le-marche

---

## 🎯 TODO Future

### Phase 1 : Validation (cette semaine)

- [ ] Tester 20+ médicaments courants
- [ ] Vérifier cache fonctionne
- [ ] Vérifier génériques retournés
- [ ] Tester scan avec GTIN réels

### Phase 2 : Enrichissement (semaine prochaine)

- [ ] Ajouter code ATC
- [ ] Ajouter URL notice ANSM
- [ ] Lier conditions ICD-11 ↔ indications
- [ ] Photos boîtes

### Phase 3 : Mobile (2 semaines)

- [ ] Adapter page recherche
- [ ] Adapter fiche médicament
- [ ] Ajouter scanner caméra
- [ ] Flow scan → fiche → ajout

### Phase 4 : Migration Données (optionnel)

- [ ] Exécuter migration BDPM → Giygas
- [ ] Valider résultats
- [ ] Supprimer `medication_service.py` (LEGACY)

---

## 📞 Support

### Questions Fréquentes

**Q : ICD-11 a-t-elle été modifiée ?**
R : Non, ICD-11 reste inchangée. Elle est utilisée uniquement pour les conditions de santé, pas pour les médicaments.

**Q : Les anciennes données BDPM sont-elles perdues ?**
R : Non, elles sont conservées avec `source='bdpm'`. Migration progressive.

**Q : Le scan de boîtes fonctionne-t-il avec tous les médicaments ?**
R : Oui, si le médicament a une présentation avec CIP13. Sinon, retour 404.

**Q : Pourquoi le code ATC n'est-il pas fourni ?**
R : L'API Giygas ne l'expose pas. À récupérer depuis autre source (WHO ATC/DDD Index).

---

## 📊 Statistiques

- **Fichiers créés :** 9
- **Fichiers modifiés :** 2
- **Lignes de code :** ~1500
- **Tables DB créées :** 1
- **Colonnes ajoutées :** 2
- **Fonctions SQL créées :** 1
- **Vues créées :** 1
- **Endpoints créés :** 1
- **Endpoints adaptés :** 2
- **Tests unitaires :** 15+
- **Durée déploiement :** 15 minutes

---

**Fin du README - Version 1.0 - 4 Février 2026**
