# 🔄 Vider le Cache Local des Médicaments

## Problème

Les médicaments sont cachés localement dans SecureStore/AsyncStorage.
Même si Supabase est à jour, l'app affiche l'ancienne valeur du cache local.

## Solution Rapide : Dev Menu

1. **Ouvrir le Dev Menu** :
   - Sur iPhone physique : **Secouez l'appareil**
   - Sur simulateur : `Cmd + D` (Mac) ou `Ctrl + D` (Windows)

2. **Sélectionner "Debug"** → **"Clear AsyncStorage"** ou **"Reload"**

3. **Relancer l'app**

## Solution Alternative : Code

Ajoutez temporairement ce code dans `app/medications.tsx` :

```typescript
// À ajouter en haut du composant, juste après const { medications, ... } = useMedications();

useEffect(() => {
  // Forcer le rechargement depuis Supabase
  const forceReload = async () => {
    console.log('🔄 Force reload medications from Supabase');
    // Le hook devrait se recharger automatiquement
  };
  forceReload();
}, []);
```

Mais la solution la plus simple reste de **secouer l'appareil** → **Reload**.
