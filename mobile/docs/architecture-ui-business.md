# Architecture : Séparation UI vs Métier

## Vue d'ensemble

Ce document définit les règles de séparation entre l'interface utilisateur (UI) et la logique métier (business logic) dans l'application Pulse.

## Structure des dossiers

```
mobile/
├── app/                    # Routes Expo Router (file-based routing)
│   ├── _layout.tsx         # Layouts
│   ├── (tabs)/             # Routes avec navigation par onglets
│   │   ├── index.tsx        # Dashboard (orchestration minimale)
│   │   ├── profil.tsx       # Profil (orchestration minimale)
│   │   └── tendances.tsx    # Tendances (orchestration minimale)
│   └── login.tsx           # Login (orchestration minimale)
│
└── src/
    ├── components/         # Composants UI réutilisables (présentation pure)
    │   ├── InsightCard.tsx
    │   ├── MetricCard.tsx
    │   └── ...
    │
    ├── hooks/              # Logique métier (business logic)
    │   ├── useHealthData.ts      # Gestion des données de santé
    │   ├── useProfile.ts         # Gestion du profil utilisateur
    │   ├── useAuth.ts            # Authentification
    │   └── ...
    │
    ├── lib/                # Utilitaires et clients
    │   ├── supabase.ts     # Client Supabase
    │   └── storage.ts      # Stockage local
    │
    └── screens/            # ⚠️ OPTIONNEL - Voir section dédiée
```

## Principes

### 1. Logique métier dans les hooks (`src/hooks/`)

**Responsabilités :**
- Appels API (Supabase, services externes)
- Gestion d'état métier
- Calculs et transformations de données
- Validation métier
- Gestion des erreurs métier
- Cache et synchronisation

**Exemple :**
```typescript
// src/hooks/useHealthData.ts
export function useHealthData(userId: string) {
  return useQuery({
    queryKey: ['healthData', userId],
    queryFn: async () => {
      const { data, error } = await supabase
        .rpc('get_latest_health_profile', { user_uuid: userId });
      
      if (error) throw error;
      return transformHealthData(data); // Transformation métier
    },
  });
}
```

### 2. Composants UI dans `src/components/`

**Responsabilités :**
- Affichage uniquement (présentation)
- Reçoivent des props
- Peuvent utiliser des hooks pour la logique
- Pas de logique métier directe

**Exemple :**
```typescript
// src/components/MetricCard.tsx
interface MetricCardProps {
  title: string;
  value: string | number | null;
  icon: React.ReactNode;
  color: string;
}

export function MetricCard({ title, value, icon, color }: MetricCardProps) {
  // UI pure : affichage uniquement
  return (
    <View style={styles.card}>
      <Text>{title}</Text>
      <Text>{value ?? '--'}</Text>
      {icon}
    </View>
  );
}
```

### 3. Routes dans `app/` = Orchestration minimale

**Responsabilités :**
- Point d'entrée minimal
- Utilisent les hooks pour la logique métier
- Composent les composants UI
- Gèrent la navigation
- Gèrent les états de chargement/erreur au niveau route

**Exemple :**
```typescript
// app/(tabs)/index.tsx
export default function HomeScreen() {
  const { userId } = useAuth();
  const { data: healthData, isLoading, error } = useHealthData(userId);
  
  if (isLoading) return <LoadingSkeleton />;
  if (error) return <ErrorView error={error} />;
  
  return (
    <View>
      <MetricCard 
        title="HRV" 
        value={healthData?.hrv} 
        icon={<Activity />}
      />
    </View>
  );
}
```

## Règle pour `src/screens/`

### Option 1 : Tout dans `app/` (RECOMMANDÉ pour ce projet)

**Approche :**
- Les routes dans `app/` contiennent directement le code des écrans
- Pas de dossier `src/screens/`
- Plus simple, aligné avec Expo Router

**Avantages :**
- Moins de confusion
- Aligné avec les conventions Expo Router
- Moins de fichiers à gérer

### Option 2 : `src/screens/` comme composants réutilisables

**Approche :**
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

// ❌ INCORRECT : Duplication
// Ne pas avoir du code d'écran à la fois dans app/ ET src/screens/
```

**Quand utiliser cette option :**
- Un écran est réutilisé dans plusieurs routes
- Un écran est complexe et mérite d'être extrait
- Vous voulez tester un écran isolément

## Recommandation pour ce projet

**Supprimer `src/screens/` et tout mettre dans `app/`**

Raisons :
1. Les écrans actuels dans `src/screens/` ne sont pas utilisés
2. Expo Router gère déjà le routing
3. Plus simple et moins de confusion
4. Aligné avec les conventions Expo Router

## Checklist avant d'ajouter du code

- [ ] **Logique métier** (API, calculs, validation) → `src/hooks/`
- [ ] **Composants UI réutilisables** → `src/components/`
- [ ] **Routes/Écrans** → `app/` (ou `src/screens/` si réutilisables)
- [ ] **Utilitaires et clients** → `src/lib/`

## Exemples

### ❌ MAUVAIS : Logique métier dans un composant

```typescript
// app/(tabs)/index.tsx
export default function HomeScreen() {
  // ❌ Logique métier directement dans le composant
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    supabase
      .from('health_data')
      .select()
      .then(({ data, error }) => {
        if (error) console.error(error);
        else setData(data);
        setLoading(false);
      });
  }, []);
  
  if (loading) return <Text>Chargement...</Text>;
  
  return <View>{data && <Text>{data.value}</Text>}</View>;
}
```

### ✅ BON : Séparation claire

```typescript
// src/hooks/useHealthData.ts
export function useHealthData(userId: string) {
  return useQuery({
    queryKey: ['healthData', userId],
    queryFn: async () => {
      const { data, error } = await supabase
        .rpc('get_latest_health_profile', { user_uuid: userId });
      
      if (error) throw error;
      return transformHealthData(data);
    },
  });
}

// app/(tabs)/index.tsx
export default function HomeScreen() {
  const { userId } = useAuth();
  const { data, isLoading, error } = useHealthData(userId);
  
  // ✅ Utiliser les composants UI
  if (isLoading) return <LoadingSkeleton />;
  if (error) return <ErrorView error={error} />;
  
  return (
    <View>
      <MetricCard 
        title="HRV" 
        value={data?.hrv} 
        icon={<Activity />}
      />
    </View>
  );
}
```

## Migration recommandée

1. **Supprimer `src/screens/`** (non utilisé actuellement)
2. **S'assurer que toute la logique métier est dans `src/hooks/`**
3. **Garder les routes dans `app/` simples** (orchestration uniquement)
