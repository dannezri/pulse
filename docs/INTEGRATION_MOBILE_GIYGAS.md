# Intégration Mobile - API Giygas (2026-02-04)

## Vue d'ensemble

Le frontend mobile Pulse a été mis à jour pour utiliser la nouvelle API Giygas pour toutes les recherches et informations de médicaments. Cette migration abandonne la base de données locale statique au profit d'une API complète et à jour.

---

## Changements Principaux

### 1. Nouveau Service API

**Fichier créé :** `mobile/src/services/GiygasMedicationAPI.ts`

Ce service remplace l'ancien `MedicationAPI.ts` et fournit :

- ✅ **Recherche de médicaments** via `/api/medications/search?q=...`
- ✅ **Détails d'un médicament** via `/api/medications/{cis}`
- ✅ **Scan de code-barres** via `/api/medications/scan` (GS1 DataMatrix → CIP13 → CIS)
- ✅ **Gestion des timeouts** (10s pour recherche/détails, 15s pour scan)
- ✅ **Gestion des erreurs** avec logging détaillé

**Interface principale :**

```typescript
export interface MedicationSuggestion {
  id: string; // CIS (Code Identifiant de Spécialité)
  name: string;
  form?: string; // Forme pharmaceutique (Comprimé, Gélule, etc.)
  laboratory?: string;
  activeSubstance?: string; // Substance active (DCI)
  status?: string; // Statut administratif
  cis?: string; // CIS explicite
  presentations?: {
    cip13: string;
    cip7?: string;
    label?: string;
    price?: number;
    reimbursement_rate?: number;
  }[];
}
```

**Fonctions exportées :**

```typescript
// Recherche asynchrone (principale)
async function searchMedications(query: string): Promise<MedicationSuggestion[]>

// Détails d'un médicament par CIS
async function getMedicationDetails(cis: string): Promise<MedicationSuggestion | null>

// Scan de code-barres (GTIN ou CIP13)
async function scanMedicationBarcode(barcode: string): Promise<MedicationSuggestion | null>

// ⚠️ Obsolètes (pour compatibilité)
function searchMedicationsSync(query: string): MedicationSuggestion[] // Retourne []
function getPopularMedications(): MedicationSuggestion[] // Retourne []
```

---

### 2. Composants Mis à Jour

#### `MedicationAutocomplete.tsx`

**Changements :**
- Import depuis `GiygasMedicationAPI` au lieu de `MedicationAPI`
- Suppression de la logique "médicaments populaires" (non applicable avec API backend)
- Simplification du footer (badge "Giygas API")
- Affichage de la substance active (`activeSubstance`) au lieu de `commonFrequency`

**Avant :**
```typescript
import { searchMedications, getPopularMedications } from '../services/MedicationAPI';
```

**Après :**
```typescript
import { searchMedications, getMedicationDetails } from '../services/GiygasMedicationAPI';
```

#### `MedicationForm.tsx`

**Changements :**
- Import du type `MedicationSuggestion` depuis `GiygasMedicationAPI`
- Suppression de la suggestion automatique de fréquence (`commonFrequency` non disponible)

---

### 3. Hook `useMedications.ts`

**Aucun changement nécessaire.** Ce hook gère uniquement le stockage local et la synchronisation avec Supabase. Il ne dépend pas de l'API de recherche.

---

## Migration pour les Développeurs

### Recherche de médicaments

**Avant (local) :**
```typescript
import { searchMedications } from '../services/MedicationAPI';

const results = await searchMedications('doliprane');
// Base locale + fallback open-medicaments.fr
```

**Après (Giygas) :**
```typescript
import { searchMedications } from '../services/GiygasMedicationAPI';

const results = await searchMedications('doliprane');
// API backend → Giygas → 100% à jour
```

### Obtenir les détails d'un médicament

**Nouveau :**
```typescript
import { getMedicationDetails } from '../services/GiygasMedicationAPI';

const details = await getMedicationDetails('61766304'); // CIS du Doliprane 500mg
if (details) {
  console.log(details.name); // "DOLIPRANE 500 mg, comprimé"
  console.log(details.laboratory); // "SANOFI AVENTIS FRANCE"
  console.log(details.presentations); // Liste des CIP13/CIP7, prix, taux de remboursement
}
```

### Scanner un code-barres (nouveau)

**Workflow complet :**

1. Utilisateur scanne un code-barres (GS1 DataMatrix)
2. Extraction du GTIN (ex : `03400927562396`)
3. Appel à `scanMedicationBarcode(barcode)`
4. Backend convertit GTIN → CIP13 → appelle Giygas par CIS
5. Retourne les détails complets du médicament

**Exemple d'intégration :**
```typescript
import { scanMedicationBarcode } from '../services/GiygasMedicationAPI';

// Après scan d'un code-barres
const scannedCode = '03400927562396'; // GTIN du Doliprane 500mg
const medication = await scanMedicationBarcode(scannedCode);

if (medication) {
  // Pré-remplir le formulaire
  setName(medication.name);
  setForm(medication.form);
  setLaboratory(medication.laboratory);
} else {
  Alert.alert('Erreur', 'Médicament non trouvé pour ce code-barres');
}
```

---

## Gestion des Erreurs

### Timeouts

- **Recherche/détails :** 10 secondes
- **Scan barcode :** 15 secondes (peut nécessiter plusieurs requêtes)

Si un timeout se produit, la fonction retourne `[]` (recherche) ou `null` (détails/scan).

### Erreurs Réseau

Toutes les erreurs sont loggées dans la console avec le préfixe `[GiygasMedicationAPI]` :

```typescript
console.log('[GiygasMedicationAPI] Recherche:', url);
console.log('[GiygasMedicationAPI] ✅ 12 résultats trouvés');
console.error('[GiygasMedicationAPI] Timeout dépassé (10s)');
```

### Erreurs Backend

Si le backend retourne une erreur HTTP (404, 500, etc.), l'erreur est loggée et la fonction retourne un résultat vide.

---

## Tests

### Test Manuel (Expo Go)

1. Démarrer le backend :
   ```bash
   cd /Users/dannezri/Desktop/Pulse
   python3 backend/api_server.py
   ```

2. Démarrer l'app mobile :
   ```bash
   cd mobile
   npx expo start
   ```

3. Tester la recherche :
   - Ouvrir l'écran d'ajout de médicament
   - Taper "doliprane" dans le champ de recherche
   - Vérifier que les suggestions apparaissent
   - Sélectionner un médicament
   - Vérifier que les champs sont pré-remplis

### Test du Scan (Device Réel Uniquement)

⚠️ **Important :** Le scan de code-barres nécessite un device physique (iOS/Android). Expo Go sur simulateur ne supporte pas la caméra.

1. Installer une bibliothèque de scan (exemple : `expo-barcode-scanner`)
2. Implémenter le composant de scan
3. Passer le code scanné à `scanMedicationBarcode()`
4. Vérifier que les détails du médicament sont récupérés

**Exemple de code-barres à tester :**
- GTIN : `03400927562396` (Doliprane 500mg)
- CIP13 : `3400927562396`

---

## Configuration API

Le fichier `mobile/src/config/api.ts` détecte automatiquement l'URL du backend :

- **Simulateur iOS :** `http://localhost:9000`
- **Simulateur Android :** `http://10.0.2.2:9000`
- **Device physique (iOS/Android) :** `http://192.168.0.23:9000`

Si l'IP du Mac change, mettre à jour cette ligne dans `api.ts` :

```typescript
return 'http://192.168.0.23:9000'; // ← Changer si nécessaire
```

Ou définir `EXPO_PUBLIC_API_URL` dans `.env`.

---

## Compatibilité

### Expo SDK
- ✅ Compatible Expo SDK 54
- ✅ Compatible React Native 0.81.5
- ✅ Compatible React 19.1.0
- ✅ Aucune dépendance native ajoutée

### Anciens Composants
- ❌ `MedicationAPI.ts` est marqué comme **@deprecated**
- ✅ Tous les composants ont été migrés vers `GiygasMedicationAPI.ts`
- ⚠️ Si d'autres composants utilisent encore `MedicationAPI.ts`, ils doivent être mis à jour

---

## Points d'Attention

### 1. Données Offline

⚠️ **Limitation :** L'API Giygas nécessite une connexion réseau. Contrairement à l'ancienne base locale, aucune suggestion n'apparaît en mode hors ligne.

**Solution future :** Implémenter un cache local des dernières recherches (AsyncStorage ou SQLite).

### 2. Fréquence Commune (`commonFrequency`)

L'API Giygas ne fournit pas de suggestion de fréquence (ex : "3x/jour"). L'utilisateur doit saisir manuellement.

**Valeur par défaut :** 1x/jour à 08:00

### 3. Dosage

Le dosage est extrait de la composition si disponible, mais le format peut varier (ex : "500 mg", "500mg", "0.5 g").

---

## TODO / Améliorations Futures

- [ ] **Cache local** : Sauvegarder les dernières recherches pour usage hors ligne
- [ ] **Scan de boîte** : Intégrer `expo-barcode-scanner` pour scanner les codes-barres GS1 DataMatrix
- [ ] **Fiche médicament détaillée** : Écran dédié avec onglets (Composition, Génériques, Présentations, Conditions)
- [ ] **Historique de recherche** : Afficher les médicaments récemment recherchés
- [ ] **Favoris** : Permettre de marquer des médicaments comme favoris
- [ ] **Notifications de rappel** : Notifications push pour les heures de prise

---

## Support

En cas de problème :
1. Vérifier que le backend est démarré (`http://localhost:9000/health`)
2. Vérifier l'URL API dans les logs console : `[API Config] Using API URL: ...`
3. Vérifier les logs `[GiygasMedicationAPI]` dans la console mobile
4. Consulter la documentation backend : `docs/README_GIYGAS.md`

---

## Historique

- **2026-02-04** : Migration complète de `MedicationAPI.ts` vers `GiygasMedicationAPI.ts`
- **2026-02-04** : Intégration de l'API Giygas dans le backend Pulse
- **2026-02-04** : Dépréciation de `MedicationAPI.ts` et de la base locale statique

---

**✅ L'intégration mobile est complète et fonctionnelle.**
