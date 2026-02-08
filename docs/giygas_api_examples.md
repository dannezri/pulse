# Exemples Réponses API Giygas

Documentation des réponses de l'API `medicaments-api.giygas.dev`

---

## Endpoint : `GET /medicament/{query}`

### Exemple 1 : Recherche "doliprane"

**Requête :**
```bash
curl https://medicaments-api.giygas.dev/medicament/doliprane
```

**Réponse (simplifié) :**
```json
[
  {
    "cis": "60001551",
    "elementPharmaceutique": "DOLIPRANE 500 mg, comprimé",
    "formePharmaceutique": "comprimé",
    "voiesAdministration": ["orale"],
    "statutAmm": "Autorisation active",
    "typeAmm": "Autorisation de mise sur le marché",
    "commercialisation": "Commercialisée",
    "dateAmm": "1988-07-01",
    "composition": [
      {
        "substanceActive": "PARACETAMOL",
        "dosage": "500",
        "unite": "mg",
        "reference": "PARACÉTAMOL"
      }
    ],
    "generiques": [
      {
        "cis": "61234567",
        "elementPharmaceutique": "PARACETAMOL BIOGARAN 500 mg, comprimé",
        "titulaire": "BIOGARAN",
        "typeGenerique": "générique"
      },
      {
        "cis": "61234568",
        "elementPharmaceutique": "PARACETAMOL TEVA 500 mg, comprimé",
        "titulaire": "TEVA SANTE",
        "typeGenerique": "générique"
      }
    ],
    "presentation": [
      {
        "cip13": "3400930001551",
        "cip7": "3000155",
        "libelle": "plaquette(s) thermoformée(s) PVC aluminium de 16 comprimé(s)",
        "statutAdministratif": "Déclaration de commercialisation",
        "etatCommercialisation": "Commercialisée",
        "dateDeclaration": "1988-07-01",
        "prix": 2.50,
        "tauxRemboursement": 65,
        "titulaire": "OPELLA HEALTHCARE FRANCE SAS",
        "agrementCollectivites": true
      }
    ],
    "conditions": {
      "prescription": "Liste I",
      "delivrance": "Prescription médicale facultative",
      "smr": "Important",
      "asmr": "Absence d'amélioration"
    }
  }
]
```

---

## Endpoint : `GET /medicament/id/{cis}`

### Exemple 2 : Détails par CIS (Doliprane 500mg)

**Requête :**
```bash
curl https://medicaments-api.giygas.dev/medicament/id/60001551
```

**Réponse (complète) :**
```json
{
  "cis": "60001551",
  "elementPharmaceutique": "DOLIPRANE 500 mg, comprimé",
  "formePharmaceutique": "comprimé",
  "voiesAdministration": ["orale"],
  "statutAmm": "Autorisation active",
  "typeAmm": "Autorisation de mise sur le marché",
  "commercialisation": "Commercialisée",
  "dateAmm": "1988-07-01",
  "titulaire": "OPELLA HEALTHCARE FRANCE SAS",
  "surveillance": false,
  "composition": [
    {
      "substanceActive": "PARACETAMOL",
      "dosage": "500",
      "unite": "mg",
      "reference": "PARACÉTAMOL",
      "nature": "SA"
    }
  ],
  "generiques": [
    {
      "cis": "61234567",
      "elementPharmaceutique": "PARACETAMOL BIOGARAN 500 mg, comprimé",
      "titulaire": "BIOGARAN",
      "typeGenerique": "générique",
      "groupeGenerique": "DOLIPRANE 500 mg, comprimé"
    },
    {
      "cis": "61234568",
      "elementPharmaceutique": "PARACETAMOL TEVA 500 mg, comprimé",
      "titulaire": "TEVA SANTE",
      "typeGenerique": "générique",
      "groupeGenerique": "DOLIPRANE 500 mg, comprimé"
    }
  ],
  "presentation": [
    {
      "cip13": "3400930001551",
      "cip7": "3000155",
      "libelle": "plaquette(s) thermoformée(s) PVC aluminium de 16 comprimé(s)",
      "statutAdministratif": "Déclaration de commercialisation",
      "etatCommercialisation": "Commercialisée",
      "dateDeclaration": "1988-07-01",
      "prix": 2.50,
      "tauxRemboursement": 65,
      "honoraires": 0.53,
      "titulaire": "OPELLA HEALTHCARE FRANCE SAS",
      "agrementCollectivites": true,
      "txRemboursement": "65%"
    },
    {
      "cip13": "3400930001568",
      "cip7": "3000156",
      "libelle": "plaquette(s) thermoformée(s) PVC aluminium de 8 comprimé(s)",
      "statutAdministratif": "Déclaration de commercialisation",
      "etatCommercialisation": "Commercialisée",
      "dateDeclaration": "1988-07-01",
      "prix": 1.50,
      "tauxRemboursement": 65,
      "honoraires": 0.53,
      "titulaire": "OPELLA HEALTHCARE FRANCE SAS",
      "agrementCollectivites": true,
      "txRemboursement": "65%"
    }
  ],
  "conditions": {
    "prescription": "Liste I",
    "delivrance": "Prescription médicale facultative",
    "smr": "Important",
    "asmr": "Absence d'amélioration",
    "conditionsPrescription": [
      "Prescription initiale hospitalière",
      "Renouvellement non restreint"
    ],
    "surveillance": []
  },
  "informationsImportantes": {
    "surveillance": false,
    "stupefiant": false,
    "psychotrope": false,
    "exceptionnelleImportation": false
  }
}
```

---

## Mapping vers DB Pulse

### Table `medications_catalog`

| Champ Giygas | Colonne DB | Type | Notes |
|---|---|---|---|
| `cis` | `external_id` | TEXT | Identifiant unique |
| `elementPharmaceutique` | `name` | TEXT | Nom complet |
| `formePharmaceutique` | `form` | TEXT | Forme pharma |
| `titulaire` | `laboratory` | TEXT | Laboratoire |
| `composition[0].substanceActive` | `active_substance` | TEXT | Substance principale |
| (non fourni) | `atc_code` | TEXT | À récupérer ailleurs |
| (réponse complète) | `raw_data` | JSONB | Backup complet |

### Table `medication_details`

| Champ Giygas | Colonne DB | Type | Notes |
|---|---|---|---|
| `composition` | `composition` | JSONB | Liste substances + dosages |
| `generiques` | `generics` | JSONB | Liste génériques |
| `conditions` | `conditions` | JSONB | Conditions prescription |
| (non fourni) | `notice_url` | TEXT | À récupérer ANSM |
| (non fourni) | `notice_text` | TEXT | À récupérer ANSM |

### Table `drug_presentations`

| Champ Giygas | Colonne DB | Type | Notes |
|---|---|---|---|
| `presentation[].cip13` | `cip13` | TEXT | Identifiant unique |
| `presentation[].cip7` | `cip7` | TEXT | Ancien format |
| `presentation[].libelle` | `label` | TEXT | Description |
| `presentation[].prix` | `price` | NUMERIC | Prix TTC (€) |
| `presentation[].tauxRemboursement` | `reimbursement_rate` | INTEGER | Taux (0-100%) |
| `presentation[].statutAdministratif` | `status` | TEXT | Statut AMM |

---

## Cas Particuliers

### Médicament sans génériques

```json
{
  "cis": "12345678",
  "elementPharmaceutique": "MEDICAMENT PRINCEPS",
  "generiques": []
}
```

→ `medication_details.generics` = `[]`

### Médicament non commercialisé

```json
{
  "cis": "12345678",
  "commercialisation": "Arrêt de commercialisation",
  "presentation": [
    {
      "etatCommercialisation": "Arrêt de commercialisation",
      "prix": null,
      "tauxRemboursement": null
    }
  ]
}
```

→ `drug_presentations.price` = `NULL`

### Médicament sans conditions spéciales

```json
{
  "conditions": {
    "prescription": "Aucune",
    "delivrance": "Médicament non soumis à prescription médicale"
  }
}
```

→ `medication_details.conditions` = `{"prescription": "Aucune", ...}`

---

## Erreurs API

### 404 - Médicament non trouvé

```bash
curl https://medicaments-api.giygas.dev/medicament/id/99999999
```

**Réponse :**
```json
{
  "error": "Medication not found",
  "cis": "99999999"
}
```

### 400 - Requête invalide

```bash
curl https://medicaments-api.giygas.dev/medicament/
```

**Réponse :**
```json
{
  "error": "Query parameter required"
}
```

---

## Limites Connues

### 1. Code ATC non fourni

L'API Giygas ne fournit **pas** le code ATC (Anatomical Therapeutic Chemical).

**Solution :**
- Récupérer depuis autre source (ex: WHO ATC/DDD Index)
- Ou laisser `NULL` dans `medications_catalog.atc_code`

### 2. Notice médicament

L'API Giygas ne fournit **pas** le texte de la notice.

**Solution :**
- Récupérer depuis ANSM (Agence Nationale de Sécurité du Médicament)
- URL notice : `https://base-donnees-publique.medicaments.gouv.fr/affichageDoc.php?specid={cis}&typedoc=N`

### 3. Photos boîtes

L'API Giygas ne fournit **pas** de photos des boîtes.

**Solution :**
- Scraper depuis sites pharmaceutiques (légalité à vérifier)
- Ou laisser vide

### 4. Interactions médicamenteuses

L'API Giygas ne fournit **pas** les interactions.

**Solution :**
- Utiliser base Thériaque ou Vidal
- Ou implémenter logique métier côté backend

---

## Exemples d'Utilisation

### Recherche Autocomplete

```javascript
// Frontend : Autocomplete médicaments
const searchMedications = async (query) => {
  const response = await fetch(
    `${API_URL}/api/medications/search?q=${query}&limit=5`
  );
  const data = await response.json();
  
  return data.results.map(med => ({
    label: med.name,
    value: med.cis,
    subtitle: `${med.form} - ${med.laboratory}`
  }));
};
```

### Scan Code-Barres

```javascript
// Frontend : Scanner code-barres GS1 DataMatrix
const scanBarcode = async (gtin) => {
  const response = await fetch(`${API_URL}/api/medications/scan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ gtin })
  });
  
  const data = await response.json();
  
  // Rediriger vers fiche médicament
  navigation.navigate('MedicationDetail', { cis: data.medication.cis });
};
```

### Affichage Fiche Complète

```javascript
// Frontend : Afficher fiche médicament
const MedicationDetail = ({ cis }) => {
  const [medication, setMedication] = useState(null);
  
  useEffect(() => {
    fetch(`${API_URL}/api/medications/${cis}`)
      .then(res => res.json())
      .then(data => setMedication(data));
  }, [cis]);
  
  return (
    <View>
      <Text>{medication.name}</Text>
      
      {/* Composition */}
      <Section title="Composition">
        {medication.composition.map(comp => (
          <Text key={comp.substance}>
            {comp.substance} {comp.dosage} {comp.unite}
          </Text>
        ))}
      </Section>
      
      {/* Génériques */}
      <Section title="Génériques">
        {medication.generics.map(gen => (
          <Text key={gen.cis}>{gen.name} - {gen.laboratory}</Text>
        ))}
      </Section>
      
      {/* Présentations */}
      <Section title="Présentations">
        {medication.presentations.map(pres => (
          <View key={pres.cip13}>
            <Text>{pres.label}</Text>
            <Text>Prix: {pres.price}€ - Remboursement: {pres.reimbursement_rate}%</Text>
          </View>
        ))}
      </Section>
    </View>
  );
};
```

---

## Références

- **API Giygas :** `https://medicaments-api.giygas.dev`
- **BDPM (source) :** `https://base-donnees-publique.medicaments.gouv.fr`
- **ANSM :** `https://ansm.sante.fr`
- **Code GS1 :** `https://www.gs1.org/standards/barcodes/datamatrix`

---

**Fin des exemples - Version 1.0 - 4 Février 2026**
