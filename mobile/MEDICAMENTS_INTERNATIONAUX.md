# 🌍 Gestion des Médicaments Internationaux

**Date**: 2026-02-05  
**Statut**: Guide pour implémentation future

---

## 📊 Situation Actuelle

### ✅ Supporté
- **Médicaments français** : 20 919 présentations ANSM
- **Codes commençant par** : `3400` (CIP13) ou `0340` (GTIN14)
- **Couverture** : 95-100% des médicaments français

### ⚠️ Non Supporté
- Médicaments d'autres pays européens
- Compléments alimentaires internationaux
- Produits de parapharmacie étrangers

---

## 🔍 Identification des Codes par Pays

### Préfixes GS1 par Pays

| Pays | Préfixe | Exemple |
|------|---------|---------|
| 🇫🇷 **France** | 30-37 | **3400**930091357 ✅ |
| 🇮🇹 Italie | 80-83 | **8000**500166758 |
| 🇧🇪 Belgique | 54 | **5400**... |
| 🇩🇪 Allemagne | 40-44 | **4000**... |
| 🇪🇸 Espagne | 84 | **8400**... |
| 🇬🇧 Royaume-Uni | 50 | **5000**... |
| 🇨🇭 Suisse | 76 | **7600**... |

**Code scanné** : `8000500166758` → **🇮🇹 Produit italien**

---

## 💡 Solutions Implémentées

### 1. Message Informatif ✅

Quand un code non-français est scanné :

```
⚠️ Médicament non-français

Le code scanné (8000500166758) semble être un médicament 
étranger ou un produit de parapharmacie.

💡 Astuce : Recherchez le nom du médicament manuellement 
dans la barre de recherche ci-dessus.

[Rechercher par nom]  [Réessayer le scan]
```

### 2. Redirection vers Recherche Manuelle

L'utilisateur est guidé vers la **barre de recherche** pour saisir le nom.

---

## 🚀 Solutions Futures

### Option A : Base de Données Multi-Pays

#### Sources Possibles

1. **EMA (European Medicines Agency)**
   - URL : https://www.ema.europa.eu/en/medicines
   - API : Disponible
   - Couverture : UE complète

2. **WHO (World Health Organization)**
   - Base : Global pharmacovigilance database
   - Couverture : Internationale

3. **OpenFDA (USA)**
   - URL : https://open.fda.gov/apis/drug/
   - API : Gratuite et complète
   - Couverture : Médicaments américains

#### Implémentation

```python
# backend/international_medication_service.py

def resolve_international_barcode(ean13: str) -> Optional[Dict]:
    """Résout un code-barres international"""
    
    # Identifier le pays
    country = identify_country_by_prefix(ean13)
    
    if country == "IT":  # Italie
        return query_italian_db(ean13)
    elif country == "BE":  # Belgique
        return query_belgian_db(ean13)
    # etc...
```

### Option B : API Commerciale

#### Exemples

1. **Vidal API** (payant)
   - Couverture : France + International
   - Prix : ~€500/mois

2. **DrugBank** (payant)
   - Couverture : Mondiale
   - Prix : Variable

3. **RxNorm (NIH)** (gratuit)
   - Couverture : USA principalement
   - API : Gratuite

### Option C : Saisie Manuelle Améliorée

#### Workflow Optimisé

```
1. Scan code non-français
   ↓
2. Détection du pays (préfixe)
   ↓
3. Message : "Produit italien détecté"
   ↓
4. Pré-remplissage partiel du formulaire :
   - Nom : [À saisir]
   - Pays d'origine : 🇮🇹 Italie
   - Code EAN : 8000500166758
   ↓
5. Recherche dans Giygas par nom
   ↓
6. Si trouvé : Ajout
   Si non : Création médicament personnalisé
```

---

## 📝 Exemple d'Implémentation Minimale

### Ajout Détection de Pays

```typescript
// mobile/src/utils/barcodeCountry.ts

export function detectCountryByEAN(ean13: string): string {
  const prefix = ean13.substring(0, 3);
  
  if (prefix >= '300' && prefix <= '379') return '🇫🇷 France';
  if (prefix >= '800' && prefix <= '839') return '🇮🇹 Italie';
  if (prefix === '540') return '🇧🇪 Belgique';
  if (prefix >= '400' && prefix <= '440') return '🇩🇪 Allemagne';
  if (prefix === '840') return '🇪🇸 Espagne';
  if (prefix === '500') return '🇬🇧 Royaume-Uni';
  if (prefix === '760') return '🇨🇭 Suisse';
  
  return '🌍 International';
}
```

### Message Personnalisé

```typescript
const country = detectCountryByEAN(cip13);
Alert.alert(
  `Médicament ${country}`,
  `Le produit scanné semble provenir de ${country}.\n\nRecherchez-le par son nom dans la barre de recherche.`,
  [{ text: 'Rechercher', onPress: onClose }]
);
```

---

## 📊 Statistiques d'Usage

Pour prioriser l'implémentation, il faudrait mesurer :

```sql
-- Combien de scans échouent par pays ?
SELECT 
  SUBSTRING(cip13, 1, 3) as prefix,
  COUNT(*) as scan_count,
  COUNT(DISTINCT user_id) as unique_users
FROM scan_logs
WHERE success = false
GROUP BY prefix
ORDER BY scan_count DESC;
```

---

## 💰 Coût/Bénéfice

| Solution | Coût | Couverture | Effort |
|----------|------|------------|--------|
| **A. Base multi-pays** | Gratuit | 80-90% UE | 3-5 jours |
| **B. API commerciale** | €500/mois | 95-100% | 1-2 jours |
| **C. Saisie améliorée** | Gratuit | 100%* | 1 jour |

*Avec recherche manuelle

---

## 🎯 Recommandation

### Immédiat ✅ (Déjà fait)
- Message informatif clair
- Redirection vers recherche manuelle

### Court Terme (1-2 semaines)
- Ajout détection de pays par préfixe
- Message personnalisé par pays
- Pré-remplissage formulaire avec pays d'origine

### Moyen Terme (1-3 mois)
- Intégration base EMA (Union Européenne)
- Couverture : France + Italie + Belgique + Allemagne

### Long Terme (3-6 mois)
- API commerciale complète (si volume justifie)
- Couverture mondiale

---

## 🧪 Pour Tester

### Codes de Test

- 🇫🇷 France : `3400930091357` ✅ Fonctionne
- 🇮🇹 Italie : `8000500166758` ⚠️ Message informatif
- 🇧🇪 Belgique : `5400...` ⚠️ À tester
- 🇩🇪 Allemagne : `4000...` ⚠️ À tester

---

## 📚 Ressources

- **GS1 Prefixes** : https://www.gs1.org/standards/id-keys/company-prefix
- **EMA Database** : https://www.ema.europa.eu/en/medicines
- **OpenFDA** : https://open.fda.gov/apis/drug/
- **WHO Database** : https://www.who.int/medicines/

---

**Conclusion** : Le système actuel gère élégamment les médicaments non-français en guidant l'utilisateur vers la recherche manuelle. Pour une couverture complète, l'intégration EMA serait la prochaine étape logique. 🌍
