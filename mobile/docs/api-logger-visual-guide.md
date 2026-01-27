# Guide Visuel - API Logger

## 🎨 Aperçu de l'interface

### 1. Page Requêtes (`app/(tabs)/requests.tsx`)

```
┌─────────────────────────────────────────┐
│  [Activity Icon] Requêtes API    [🗑️]   │
│  6 requêtes                             │
├─────────────────────────────────────────┤
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐│
│  │  4   │  │  2   │  │  0   │  │ 123ms││
│  │ ✅   │  │ ❌   │  │ ⏳   │  │ ⚡   ││
│  │Succès│  │Erreur│  │EnCour│  │Temps ││
│  └──────┘  └──────┘  └──────┘  └──────┘│
├─────────────────────────────────────────┤
│  [ALL] [GET] [POST] [PUT] [DELETE]      │
├─────────────────────────────────────────┤
│  ┌───────────────────────────────────┐  │
│  │ [👁️] GET     [✅] 200             │  │
│  │ /api/users                        │  │
│  │ 🕐 Il y a 2min  ⬇️ 123ms          │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ [⬆️] POST    [✅] 201             │  │
│  │ /api/users                        │  │
│  │ 🕐 Il y a 5min  ⬇️ 234ms          │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ [✏️] PUT     [✅] 200             │  │
│  │ /api/users/123                    │  │
│  │ 🕐 Il y a 10min ⬇️ 156ms          │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ [🗑️] DELETE  [✅] 204             │  │
│  │ /api/users/123                    │  │
│  │ 🕐 Il y a 15min ⬇️ 89ms           │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ [👁️] GET     [❌] 404             │  │
│  │ /api/users/999999                 │  │
│  │ 🕐 Il y a 20min ⬇️ 67ms           │  │
│  │ ⚠️ HTTP 404 Not Found              │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ [⬆️] POST    [❌] -                │  │
│  │ /api/invalid                      │  │
│  │ 🕐 Il y a 25min ⬇️ 5000ms         │  │
│  │ ⚠️ Network error                   │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### 2. RequestCard Expandée

```
┌───────────────────────────────────────┐
│ [⬆️] POST    [✅] 201               ▼ │
│ /api/users                            │
│ 🕐 Il y a 5min  ⬇️ 234ms              │
├───────────────────────────────────────┤
│ URL COMPLÈTE                          │
│ https://api.example.com/api/users     │
│                                       │
│ REQUEST BODY                          │
│ ┌─────────────────────────────────┐   │
│ │ {                               │   │
│ │   "name": "John Doe",           │   │
│ │   "email": "john@example.com"   │   │
│ │ }                               │   │
│ └─────────────────────────────────┘   │
│                                       │
│ RESPONSE BODY                         │
│ ┌─────────────────────────────────┐   │
│ │ {                               │   │
│ │   "id": 123,                    │   │
│ │   "name": "John Doe",           │   │
│ │   "email": "john@example.com",  │   │
│ │   "created_at": "2026-01-27"    │   │
│ │ }                               │   │
│ └─────────────────────────────────┘   │
└───────────────────────────────────────┘
```

## 🎨 Palette de couleurs

### Méthodes HTTP

| Méthode | Couleur | Hex | Usage |
|---------|---------|-----|-------|
| GET | 🔵 Bleu ciel | `#00BFFF` | Lecture de données |
| POST | 🟢 Vert néon | `#00FF41` | Création de ressources |
| PUT | 🟡 Or | `#FFD700` | Mise à jour complète |
| PATCH | 🟠 Orange | `#FFA500` | Mise à jour partielle |
| DELETE | 🔴 Rouge | `#FF4444` | Suppression |

### Statuts

| Statut | Couleur | Hex | Usage |
|--------|---------|-----|-------|
| Success | 🟢 Vert néon | `#00FF41` | Requête réussie (2xx) |
| Error | 🔴 Rouge | `#FF4444` | Requête échouée (4xx, 5xx, network) |
| Pending | 🟡 Or | `#FFD700` | Requête en cours |

### Fond et bordures

| Élément | Couleur | Hex |
|---------|---------|-----|
| Fond principal | Noir | `#000000` |
| Fond carte | Noir foncé | `#0a0a0a` |
| Bordure | Gris foncé | `#1a1a1a` |
| Texte principal | Blanc | `#FFFFFF` |
| Texte secondaire | Gris | `#888888` |
| Texte désactivé | Gris foncé | `#666666` |

## 🎯 Icônes

### Par méthode HTTP

| Méthode | Icône | Nom Lucide | Signification |
|---------|-------|------------|---------------|
| GET | 👁️ | `Eye` | Voir/Lire des données |
| POST | ⬆️ | `Upload` | Envoyer/Créer des données |
| PUT | ✏️ | `Edit` | Modifier des données |
| PATCH | ✏️ | `Edit` | Modifier partiellement |
| DELETE | 🗑️ | `Trash2` | Supprimer des données |

### Par statut

| Statut | Icône | Nom Lucide | Signification |
|--------|-------|------------|---------------|
| Success | ✅ | `CheckCircle` | Requête réussie |
| Error | ❌ | `XCircle` | Requête échouée |
| Pending | ⏳ | `Loader` | Requête en cours |

### Autres icônes

| Usage | Icône | Nom Lucide |
|-------|-------|------------|
| Temps | 🕐 | `Clock` |
| Durée | ⬇️ | `Download` |
| Expand | ▶️ | `ChevronRight` |
| Collapse | ▼ | `ChevronRight` (rotation 90°) |
| Effacer | 🗑️ | `Trash2` |
| Activité | 📊 | `Activity` |

## 📊 Stats Cards

Les stats cards affichent des métriques en temps réel :

### 1. Succès (Vert)
```
┌──────────┐
│    4     │  ← Nombre de requêtes réussies
│  Succès  │
└──────────┘
```

### 2. Erreurs (Rouge)
```
┌──────────┐
│    2     │  ← Nombre de requêtes échouées
│  Erreurs │
└──────────┘
```

### 3. En cours (Jaune)
```
┌──────────┐
│    0     │  ← Nombre de requêtes en cours
│ En cours │
└──────────┘
```

### 4. Temps moyen (Bleu)
```
┌──────────┐
│  123 ms  │  ← Temps moyen de réponse
│   Temps  │
│   moyen  │
└──────────┘
```

## 🔍 Filtres

Les filtres permettent de filtrer les requêtes par méthode HTTP :

```
┌────┐ ┌─────┐ ┌──────┐ ┌─────┐ ┌────────┐
│ALL │ │ GET │ │ POST │ │ PUT │ │ DELETE │
└────┘ └─────┘ └──────┘ └─────┘ └────────┘
  ↑ Actif (vert néon)
```

- **Actif** : Fond vert néon transparent + bordure verte
- **Inactif** : Fond noir + bordure grise

## 📱 Navigation

L'onglet "Requêtes" est accessible depuis la barre de navigation :

```
┌─────┬─────────┬────────────┬─────────┬───────────┬────────┐
│Pulse│ Sources │Médicaments │Requêtes │Historique │ Profil │
│ 🏠  │   🔗    │     💊     │   📊    │    📜     │   👤   │
└─────┴─────────┴────────────┴─────────┴───────────┴────────┘
                               ↑ Nouvel onglet
```

## 🎬 Animations

### 1. Expand/Collapse
- Icône `ChevronRight` tourne de 0° à 90° lors de l'expansion
- Transition smooth

### 2. Pull-to-refresh
- Indicateur de chargement vert néon
- Animation standard iOS/Android

### 3. Loader (Pending)
- Icône `Loader` peut être animée en rotation (optionnel)

## 📐 Dimensions

### RequestCard
- **Padding** : 16px
- **Border radius** : 16px
- **Border width** : 1px
- **Margin bottom** : 12px
- **Icon size** : 20px (méthode/statut)
- **Icon container** : 40x40px, border-radius 12px

### Stats Cards
- **Padding** : 16px
- **Border radius** : 12px
- **Border width** : 1px
- **Min width** : 120px
- **Gap** : 12px

### Filtres
- **Padding** : 12px horizontal, 6px vertical
- **Border radius** : 8px
- **Border width** : 1px
- **Gap** : 8px

## 💡 États vides

Quand aucune requête n'est enregistrée :

```
┌─────────────────────────────────────────┐
│                                         │
│            ┌──────────┐                 │
│            │          │                 │
│            │    📊    │                 │
│            │          │                 │
│            └──────────┘                 │
│                                         │
│      Aucune requête enregistrée         │
│                                         │
│  Les requêtes API apparaîtront ici      │
│         automatiquement                 │
│                                         │
└─────────────────────────────────────────┘
```

## 🎯 Responsive

- **Scroll horizontal** : Stats cards
- **Scroll vertical** : Liste des requêtes
- **Wrap** : Filtres (si trop nombreux)
- **Truncate** : URL longues (avec `numberOfLines={1}`)

## 🔥 Points d'attention UX

1. **Feedback visuel** : Couleurs distinctes pour chaque type
2. **Hiérarchie visuelle** : Taille de police, poids, couleurs
3. **Lisibilité** : Contraste suffisant sur fond noir
4. **Affordance** : Icônes reconnaissables, labels clairs
5. **Performance** : Limite de 100 requêtes pour éviter les lags
6. **Accessibilité** : Tailles de police lisibles, contraste élevé

## 📱 Compatibilité

- ✅ iOS (iPhone, iPad)
- ✅ Android (tous formats)
- ✅ Mode sombre uniquement (cohérent avec l'app)
- ✅ SafeAreaView pour les encoches
- ✅ Responsive (toutes tailles d'écran)
