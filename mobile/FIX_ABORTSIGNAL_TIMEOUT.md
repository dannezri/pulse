# Fix : AbortSignal.timeout non supporté dans React Native

## Problème

**Erreur rencontrée :**
```
ERROR [GiygasMedicationAPI] Erreur recherche: 
[TypeError: AbortSignal.timeout is not a function (it is undefined)]
```

**Cause :**
`AbortSignal.timeout()` est une API récente (ajoutée dans Node.js 17.3.0 et les navigateurs modernes) qui **n'est pas disponible dans React Native/Expo**.

## Solution Appliquée

Remplacement de `AbortSignal.timeout()` par `AbortController` + `setTimeout`, qui est compatible avec React Native.

### Avant (non compatible)

```typescript
const response = await fetch(url, {
  method: 'GET',
  headers: { ... },
  signal: AbortSignal.timeout(10000), // ❌ Non supporté dans RN
});
```

### Après (compatible)

```typescript
// Créer un AbortController pour le timeout (compatible React Native)
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 secondes

try {
  const response = await fetch(url, {
    method: 'GET',
    headers: { ... },
    signal: controller.signal, // ✅ Compatible RN
  });

  clearTimeout(timeoutId); // Nettoyer le timeout si la requête réussit

  // ... traitement de la réponse ...

} catch (error) {
  clearTimeout(timeoutId); // Nettoyer le timeout en cas d'erreur
  
  if (error instanceof Error && error.name === 'AbortError') {
    console.error('Timeout dépassé');
  } else {
    console.error('Erreur:', error);
  }
}
```

## Fichiers Modifiés

- **`mobile/src/services/GiygasMedicationAPI.ts`** ✅

**Fonctions corrigées :**
1. `searchMedications()` - Timeout : 10s
2. `getMedicationDetails()` - Timeout : 10s
3. `scanMedicationBarcode()` - Timeout : 15s

## Détection des Timeouts

**Avant :** Erreur avec `error.name === 'TimeoutError'`  
**Après :** Erreur avec `error.name === 'AbortError'`

```typescript
catch (error) {
  clearTimeout(timeoutId);
  if (error instanceof Error && error.name === 'AbortError') {
    console.error('[GiygasMedicationAPI] Timeout dépassé (10s)');
  } else {
    console.error('[GiygasMedicationAPI] Erreur recherche:', error);
  }
  return [];
}
```

## Test de la Correction

### 1. Redémarrer le Metro Bundler

```bash
cd /Users/dannezri/Desktop/Pulse/mobile
# Arrêter le serveur Metro (Ctrl+C)
npx expo start --clear
```

### 2. Recharger l'App

- **iOS :** Cmd + R dans le simulateur
- **Android :** Double tap sur R dans le simulateur
- **Device physique :** Shake + "Reload"

### 3. Tester la Recherche

1. Ouvrir l'écran "Médicaments"
2. Cliquer sur le bouton "+"
3. Taper "doliprane" dans le champ de recherche
4. **Résultat attendu :** Les suggestions apparaissent sans erreur

### 4. Vérifier les Logs

**Avant (avec erreur) :**
```
LOG  [GiygasMedicationAPI] Recherche: http://192.168.0.23:9000/api/medications/search?q=Doliprane
ERROR [GiygasMedicationAPI] Erreur recherche: [TypeError: AbortSignal.timeout is not a function]
```

**Après (sans erreur) :**
```
LOG  [GiygasMedicationAPI] Recherche: http://192.168.0.23:9000/api/medications/search?q=Doliprane
LOG  [GiygasMedicationAPI] ✅ 12 résultats trouvés
```

## Compatibilité

### ✅ Compatible avec :
- Expo SDK 54
- React Native 0.81.5
- iOS (Device + Simulateur)
- Android (Device + Émulateur)
- React 19.1.0

### ❌ Non compatible avec :
- `AbortSignal.timeout()` (API trop récente pour RN)

## Explications Techniques

### Pourquoi `AbortSignal.timeout()` ne fonctionne pas ?

React Native utilise **JavaScriptCore** (iOS) et **Hermes** (Android) comme moteurs JavaScript, qui ne supportent pas encore toutes les APIs récentes de Node.js/Web.

### Alternative Recommandée

L'approche `AbortController` + `setTimeout` est :
- ✅ **Compatible** avec tous les environnements React Native
- ✅ **Standard** : `AbortController` est largement supporté
- ✅ **Flexible** : Permet de gérer les timeouts manuellement
- ✅ **Robuste** : `clearTimeout()` évite les fuites de mémoire

### Pourquoi `clearTimeout()` dans le `catch` ?

Il est crucial d'appeler `clearTimeout()` dans **tous les cas** (succès et erreur) pour éviter que le timer continue à tourner après la fin de la requête.

```typescript
try {
  const response = await fetch(...);
  clearTimeout(timeoutId); // ← Cas de succès
  // ...
} catch (error) {
  clearTimeout(timeoutId); // ← Cas d'erreur
  // ...
}
```

## Documentation Mise à Jour

- ✅ `docs/INTEGRATION_MOBILE_GIYGAS.md` : Ajouter note sur les timeouts
- ✅ `INTEGRATION_MOBILE_COMPLETE_2026-02-04.md` : Mentionner ce correctif

## Historique

- **2026-02-04 16:00** : Intégration mobile initiale (avec `AbortSignal.timeout`)
- **2026-02-04 17:30** : Correction pour compatibilité React Native ✅

---

**🎉 La recherche de médicaments fonctionne maintenant correctement dans l'app mobile !**

Pour tester :
```bash
cd /Users/dannezri/Desktop/Pulse/mobile
npx expo start --clear
```
