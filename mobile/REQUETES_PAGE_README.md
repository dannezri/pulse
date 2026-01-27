# 📊 Page Requêtes API - Guide Rapide

## ✅ Implémentation Complète

Une page stylisée a été créée pour afficher toutes les requêtes API avec des icônes spécifiques selon le type.

## 🚀 Accès rapide

### Dans l'application
1. Lancez l'app : `npm start` (depuis `/mobile`)
2. Allez dans l'onglet **"Requêtes"** (icône 📊 Activity)
3. Les requêtes apparaîtront automatiquement

### Navigation
```
┌─────┬─────────┬────────────┬─────────┬───────────┬────────┐
│Pulse│ Sources │Médicaments │Requêtes │Historique │ Profil │
│ 🏠  │   🔗    │     💊     │   📊    │    📜     │   👤   │
└─────┴─────────┴────────────┴─────────┴───────────┴────────┘
                               ↑ Nouvel onglet
```

## 🎨 Fonctionnalités

### 1. Visualisation des requêtes
- ✅ Toutes les requêtes API affichées en temps réel
- ✅ Icônes selon la méthode HTTP (GET, POST, PUT, DELETE)
- ✅ Couleurs selon le statut (succès, erreur, en cours)
- ✅ Détails expandables (request/response body)

### 2. Stats en temps réel
- ✅ Nombre de succès (vert)
- ✅ Nombre d'erreurs (rouge)
- ✅ Requêtes en cours (jaune)
- ✅ Temps moyen de réponse (bleu)

### 3. Filtres
- ✅ Filtrer par méthode HTTP (ALL, GET, POST, PUT, DELETE)
- ✅ Pull-to-refresh
- ✅ Bouton pour effacer tous les logs

## 💻 Utilisation dans le code

### Méthode 1 : Client API (Recommandé)

```typescript
import { api } from '@/src/lib/api-client';

// Toutes ces requêtes seront automatiquement loggées
const users = await api.get('https://api.example.com/users');
const newUser = await api.post('https://api.example.com/users', { name: 'John' });
const updated = await api.put(`https://api.example.com/users/${id}`, { name: 'Jane' });
await api.delete(`https://api.example.com/users/${id}`);
```

### Méthode 2 : Logger manuellement

```typescript
import { useApiLogger } from '@/src/hooks/useApiLogger';

const { addRequest, updateRequest } = useApiLogger.getState();

const requestId = addRequest({
  method: 'GET',
  url: 'https://api.example.com/data',
  status: 'pending',
});

// ... faire la requête ...

updateRequest(requestId, {
  status: 'success',
  statusCode: 200,
  duration: 123,
  responseBody: data,
});
```

## 🧪 Tester

### Panel de test intégré

Ajoutez ce composant à une page pour générer des requêtes de test :

```typescript
import { ApiLoggerTestPanel } from '@/src/hooks/useApiLogger.test.example';

export default function TestScreen() {
  return (
    <ScrollView style={{ flex: 1, backgroundColor: '#000' }}>
      <SafeAreaView>
        <View style={{ padding: 20 }}>
          <ApiLoggerTestPanel />
        </View>
      </SafeAreaView>
    </ScrollView>
  );
}
```

Cliquez sur "Générer des requêtes de test" puis allez dans l'onglet "Requêtes".

## 📁 Fichiers créés

```
mobile/
├── src/
│   ├── hooks/
│   │   ├── useApiLogger.ts                    # Hook principal (Zustand)
│   │   ├── useApiLogger.example.ts            # Exemples d'utilisation
│   │   └── useApiLogger.test.example.tsx      # Panel de test
│   ├── lib/
│   │   └── api-client.ts                      # Client API avec logging
│   └── components/
│       └── RequestCard.tsx                    # Composant UI pour une requête
├── app/(tabs)/
│   ├── requests.tsx                           # Page principale
│   └── _layout.tsx                            # (modifié) Ajout de l'onglet
├── docs/
│   ├── api-logger.md                          # Documentation complète
│   ├── api-logger-visual-guide.md             # Guide visuel
│   └── api-logger-integration.md              # Guide d'intégration
├── API_LOGGER_IMPLEMENTATION.md               # Résumé de l'implémentation
└── REQUETES_PAGE_README.md                    # Ce fichier
```

## 🎨 Design

### Couleurs par méthode
- **GET** : 🔵 Bleu ciel (`#00BFFF`) - Lecture
- **POST** : 🟢 Vert néon (`#00FF41`) - Création
- **PUT** : 🟡 Or (`#FFD700`) - Mise à jour
- **DELETE** : 🔴 Rouge (`#FF4444`) - Suppression

### Couleurs par statut
- **Success** : 🟢 Vert néon (`#00FF41`)
- **Error** : 🔴 Rouge (`#FF4444`)
- **Pending** : 🟡 Or (`#FFD700`)

### Icônes
- **GET** : 👁️ Eye
- **POST** : ⬆️ Upload
- **PUT/PATCH** : ✏️ Edit
- **DELETE** : 🗑️ Trash2
- **Success** : ✅ CheckCircle
- **Error** : ❌ XCircle
- **Pending** : ⏳ Loader

## 📦 Dépendances

### Installées
- ✅ **zustand** : State management (via `npx expo install zustand`)

### Existantes
- ✅ **lucide-react-native** : Icônes
- ✅ **react-native-safe-area-context** : SafeAreaView
- ✅ **expo-router** : Navigation

## ✅ Validation

### Expo Doctor
```bash
cd mobile && npx expo-doctor
# ✅ 17/17 checks passed. No issues detected!
```

### Compatibilité
- ✅ Expo SDK 54
- ✅ React Native 0.81.5
- ✅ React 19.1.0
- ✅ iOS
- ✅ Android

## 📚 Documentation

### Guides complets
- **[docs/api-logger.md](docs/api-logger.md)** : Documentation complète du système
- **[docs/api-logger-visual-guide.md](docs/api-logger-visual-guide.md)** : Guide visuel avec maquettes
- **[docs/api-logger-integration.md](docs/api-logger-integration.md)** : Intégration avec Supabase

### Exemples de code
- **[src/hooks/useApiLogger.example.ts](src/hooks/useApiLogger.example.ts)** : Exemples d'utilisation
- **[src/hooks/useApiLogger.test.example.tsx](src/hooks/useApiLogger.test.example.tsx)** : Panel de test

### Résumé technique
- **[API_LOGGER_IMPLEMENTATION.md](API_LOGGER_IMPLEMENTATION.md)** : Résumé de l'implémentation

## 🎯 Prochaines étapes

### Pour tester immédiatement
1. Lancez l'app : `npm start`
2. Allez dans l'onglet "Requêtes"
3. Utilisez l'app normalement (les requêtes apparaîtront automatiquement)

### Pour intégrer avec vos requêtes
1. Remplacez `fetch` par `api.get/post/put/delete` (voir exemples)
2. Ou utilisez le wrapper Supabase (voir `docs/api-logger-integration.md`)

### Pour tester avec des données fictives
1. Ajoutez le `ApiLoggerTestPanel` à une page
2. Cliquez sur "Générer des requêtes de test"
3. Allez dans l'onglet "Requêtes"

## 💡 Conseils

### Développement
- ✅ Utilisez le logger pour débugger les problèmes d'API
- ✅ Vérifiez les temps de réponse pour optimiser les performances
- ✅ Filtrez par méthode pour trouver rapidement une requête

### Production
- ⚠️ Désactivez le logging en production (ou loggez uniquement les erreurs)
- ⚠️ Les logs ne sont pas persistés (perdus au redémarrage)
- ⚠️ Limite de 100 requêtes pour éviter les fuites mémoire

## 🔗 Liens utiles

- [Architecture mobile](ARCHITECTURE.md)
- [Séparation UI vs Métier](docs/architecture-ui-business.md)
- [Politique des dépendances](docs/deps-policy.md)

## ❓ Questions fréquentes

### Comment logger les requêtes Supabase ?
Voir le guide d'intégration : [docs/api-logger-integration.md](docs/api-logger-integration.md)

### Comment désactiver le logging en production ?
Ajoutez une condition `if (__DEV__)` dans le client API (voir exemples)

### Les logs sont-ils persistés ?
Non, les logs sont perdus au redémarrage de l'app (feature future)

### Combien de requêtes sont stockées ?
Maximum 100 requêtes (les plus anciennes sont supprimées automatiquement)

## 🎉 Résultat

Une page professionnelle et stylisée qui permet de :
- 📊 Monitorer toutes les requêtes API en temps réel
- 🔍 Débugger les problèmes facilement
- ⚡ Analyser les performances
- 🎨 Interface cohérente avec le thème Dark Zen de l'app
- 🚀 Prêt à l'emploi, aucune configuration nécessaire

---

**Bon développement ! 🚀**
