# Règle pour `src/screens/` avec Expo Router

## Principe

Avec Expo Router, `src/screens/` est **optionnel**. Il faut choisir une approche claire.

## Deux options possibles

### Option 1 : Tout dans `app/` (RECOMMANDÉ)

**Approche :**
- Les routes dans `app/` contiennent directement le code des écrans
- Pas de dossier `src/screens/`
- Plus simple, aligné avec Expo Router

**Exemple :**
```typescript
// app/(tabs)/index.tsx
export default function HomeScreen() {
  const { data, isLoading } = useHealthData();
  return <View>...</View>;
}
```

**Avantages :**
- Moins de confusion
- Aligné avec les conventions Expo Router
- Moins de fichiers à gérer
- Routing et écran au même endroit

### Option 2 : `src/screens/` comme composants réutilisables

**Approche :**
- `src/screens/` contient des **composants screen** réutilisables
- Les routes dans `app/` **importent** ces composants
- Utile si un écran est utilisé dans plusieurs routes

**Exemple :**
```typescript
// src/screens/HomeScreen.tsx
export default function HomeScreen() {
  const { data, isLoading } = useHealthData();
  return <View>...</View>;
}

// app/(tabs)/index.tsx
import HomeScreen from '@/src/screens/HomeScreen';

export default function HomeTab() {
  return <HomeScreen />;
}
```

**Quand utiliser cette option :**
- Un écran est réutilisé dans plusieurs routes
- Un écran est complexe et mérite d'être extrait
- Vous voulez tester un écran isolément

## Règle stricte

**JAMAIS de mélange :**
- ❌ Ne pas avoir du code d'écran à la fois dans `app/` ET `src/screens/`
- ❌ Ne pas avoir des routes dans `app/` qui font à la fois du routing ET du rendu d'écran complexe

**Choisir une approche et s'y tenir.**

## Recommandation pour ce projet

**Supprimer `src/screens/` et tout mettre dans `app/`**

Raisons :
1. Les écrans actuels dans `src/screens/` ne sont pas utilisés
2. Expo Router gère déjà le routing
3. Plus simple et moins de confusion
4. Aligné avec les conventions Expo Router

## Migration

Si vous voulez supprimer `src/screens/` :

1. Vérifier qu'aucun fichier n'importe depuis `src/screens/`
2. Supprimer le dossier `src/screens/`
3. S'assurer que toutes les routes dans `app/` contiennent le code nécessaire
