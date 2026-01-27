# Séparation UI vs Métier

## Principe fondamental

**Séparation claire entre la logique métier (business logic) et l'interface utilisateur (UI).**

## Structure

```
mobile/
├── app/                    # Routes Expo Router (file-based routing)
│   └── (tabs)/
│       └── index.tsx       # Route = Point d'entrée minimal
│
└── src/
    ├── components/         # Composants UI réutilisables (présentation pure)
    ├── hooks/              # Logique métier (business logic)
    │   ├── useHealthData.ts
    │   ├── useProfile.ts
    │   └── ...
    ├── lib/                # Utilitaires et clients (Supabase, storage)
    └── screens/            # ⚠️ OPTIONNEL - Voir règle ci-dessous
```

## Règles de séparation

### 1. Hooks (`src/hooks/`) = Logique métier

Les hooks contiennent TOUTE la logique métier :
- Appels API (Supabase, etc.)
- Gestion d'état métier
- Calculs et transformations de données
- Validation métier
- Gestion des erreurs métier

**Exemple :**
```typescript
// src/hooks/useHealthData.ts
export function useHealthData(userId: string) {
  // Logique métier : fetch, transform, validate
  const { data, error, isLoading } = useQuery(...);
  return { healthData: transform(data), error, isLoading };
}
```

### 2. Composants (`src/components/`) = UI pure

Les composants sont des composants de présentation :
- Affichage uniquement
- Reçoivent des props
- Pas de logique métier directe
- Peuvent utiliser des hooks pour la logique

**Exemple :**
```typescript
// src/components/MetricCard.tsx
export function MetricCard({ value, title, icon }) {
  // UI pure : affichage uniquement
  return <View>...</View>;
}
```

### 3. Routes (`app/`) = Orchestration minimale

Les routes Expo Router :
- Point d'entrée minimal
- Utilisent les hooks pour la logique métier
- Composent les composants UI
- Gèrent la navigation

**Exemple :**
```typescript
// app/(tabs)/index.tsx
export default function HomeScreen() {
  // Utiliser les hooks métier
  const { data, isLoading } = useHealthData(userId);
  
  // Composer les composants UI
  return (
    <View>
      {isLoading ? <LoadingSkeleton /> : <MetricCard data={data} />}
    </View>
  );
}
```

## Règle pour `src/screens/`

### Option 1 : Tout dans `app/` (RECOMMANDÉ)

**Si vous gardez tout dans `app/` :**
- Les routes dans `app/` contiennent directement le code des écrans
- Pas de dossier `src/screens/`
- Plus simple, aligné avec Expo Router

### Option 2 : `src/screens/` comme composants réutilisables

**Si vous gardez `src/screens/` :**
- `src/screens/` contient des **composants screen** réutilisables
- Les routes dans `app/` **importent** ces composants
- Utile si un écran est utilisé dans plusieurs routes

**Règle stricte :**
```typescript
// ✅ CORRECT : app/ importe src/screens/
// app/(tabs)/index.tsx
import HomeScreen from '@/src/screens/HomeScreen';

export default function HomeTab() {
  return <HomeScreen />;
}

// ❌ INCORRECT : Mélange app/ et src/screens/
// Ne pas avoir du code d'écran à la fois dans app/ ET src/screens/
```

## Recommandation actuelle

**Pour ce projet : Supprimer `src/screens/` et tout mettre dans `app/`**

Raisons :
1. Expo Router gère déjà le routing
2. Plus simple et moins de confusion
3. Aligné avec les conventions Expo Router
4. Les écrans actuels dans `src/screens/` ne sont pas utilisés

## Checklist

Avant d'ajouter du code :

- [ ] **Logique métier** → `src/hooks/`
- [ ] **Composants UI** → `src/components/`
- [ ] **Routes/Écrans** → `app/` (ou `src/screens/` si réutilisables)
- [ ] **Utilitaires** → `src/lib/`

## Exemples

### ❌ MAUVAIS : Logique métier dans un composant

```typescript
// app/(tabs)/index.tsx
export default function HomeScreen() {
  // ❌ Logique métier directement dans le composant
  const [data, setData] = useState(null);
  useEffect(() => {
    supabase.from('health_data').select().then(setData);
  }, []);
  
  return <View>{data && <Text>{data.value}</Text>}</View>;
}
```

### ✅ BON : Séparation claire

```typescript
// src/hooks/useHealthData.ts
export function useHealthData() {
  return useQuery({
    queryKey: ['healthData'],
    queryFn: () => supabase.from('health_data').select(),
  });
}

// app/(tabs)/index.tsx
export default function HomeScreen() {
  // ✅ Utiliser le hook métier
  const { data, isLoading } = useHealthData();
  
  // ✅ Composer les composants UI
  return (
    <View>
      {isLoading ? <LoadingSkeleton /> : <MetricCard data={data} />}
    </View>
  );
}
```
