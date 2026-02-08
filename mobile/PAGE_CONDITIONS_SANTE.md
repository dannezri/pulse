# Page Conditions de Santé

## 📋 Résumé

Une page complète dédiée à la gestion des conditions de santé de l'utilisateur, permettant d'ajouter, visualiser et supprimer des conditions pour des recommandations personnalisées.

## ✅ Ce qui a été créé

### Fichier Principal
**`app/health-conditions.tsx`** - Page de gestion des conditions de santé

## 🎨 Design et Structure

### Header
- **Bouton retour** (←) à gauche
- **Titre** "Conditions de Santé" centré
- **Bouton ajout** (+) à droite pour ajouter rapidement

### Card Info Rose
- Icône Heart en rose
- Titre "Personnalisez vos conseils"
- Description explicative
- Badge jaune "Facultatif"

### Stats Overview (si conditions présentes)
Trois cards affichant :
1. **Nombre** de conditions
2. **Statut** Actives
3. **Info** Suivies

### Section "Mes Conditions"
- **Header** avec titre et compteur
- **Grille de cards** colorées pour chaque condition
  - Point de couleur
  - Nom de la condition
  - Code (si disponible)
  - Bouton de suppression (×)
- **État vide** élégant si aucune condition
- **Bouton d'ajout** en bas (si conditions présentes)

### Section "Pourquoi c'est important ?"
Trois raisons avec emojis :
1. 🎯 **Conseils personnalisés**
2. 📊 **Analyses précises**
3. 🔒 **Confidentialité**

### Note de Confidentialité
- Message rassurant sur la sécurité des données
- Fond vert avec icône cadenas

## 🎨 Palette de Couleurs

### Couleurs Principales
- **Accent rose**: `#FF2D55` (Heart icon, buttons)
- **Conditions** : 6 couleurs différentes en rotation
  - Orange: `#FF9500`
  - Violet: `#5E5CE6`
  - Vert: `#34C759`
  - Rose: `#FF6B9D`
  - Turquoise: `#4ECDC4`
  - Jaune: `#FFB800`

### Backgrounds
- Container: `#0D0D1F`
- Cards: `#1A1A2E`
- Info card: `#FF2D5520` (rose transparent)

## 🔧 Fonctionnalités

### 1. Affichage des Conditions
```typescript
- Chargement via useConditions()
- Affichage en grille colorée
- Compteur en temps réel
- État de chargement élégant
```

### 2. Ajout de Conditions
```typescript
- Bouton + dans le header
- Bouton dans l'état vide
- Bouton en bas si conditions présentes
- Modal ConditionPicker réutilisé
- Rafraîchissement automatique après ajout
```

### 3. Suppression de Conditions
```typescript
handleDeleteCondition = (id, display) => {
  Alert.alert avec confirmation
  → deleteCondition(id)
  → Mise à jour automatique de la liste
}
```

### 4. Gestion des États
- **Loading**: ActivityIndicator + message
- **Vide**: État vide avec CTA
- **Avec données**: Grille de cards
- **Erreur**: Alert avec message

## 🎯 Intégration

### Hooks Utilisés
```typescript
const { 
  conditions,              // Array de conditions
  loading,                 // État de chargement
  deleteCondition,         // Supprimer une condition
  fetchConditions         // Recharger les conditions
} = useConditions();
```

### Composants Réutilisés
- `ConditionPicker` - Modal de sélection/recherche
- `ActivityIndicator` - Loading states
- `Alert` - Confirmations
- Icônes Lucide React Native

### Navigation
```
Profil → Clic sur "Conditions de santé" → /health-conditions
Header + → Ouvre ConditionPicker
Bouton retour ← → Retour au profil
```

## 📊 Structure de la Page

```
Header (avec retour + ajout)
  └── "Conditions de Santé"

Info Card Rose
  ├── Icône Heart
  ├── Titre + Description
  └── Badge "Facultatif"

Stats Overview (si conditions)
  ├── Nombre
  ├── Actives
  └── Suivies

Section "Mes Conditions"
  ├── Header avec compteur
  ├── Grille de conditions
  │   └── [Card condition] × N
  │       ├── Point coloré
  │       ├── Nom
  │       ├── Code
  │       └── Bouton supprimer
  └── Bouton "Ajouter"

Section "Pourquoi c'est important ?"
  ├── Conseils personnalisés 🎯
  ├── Analyses précises 📊
  └── Confidentialité 🔒

Note de Confidentialité 🔒
```

## 🎨 Coloration des Conditions

Les conditions sont colorées automatiquement :

```typescript
const getConditionColor = (index: number) => {
  const colors = [
    { bg: '#FF950020', border: '#FF9500', dot: '#FF9500' },  // Orange
    { bg: '#5E5CE620', border: '#5E5CE6', dot: '#5E5CE6' },  // Violet
    { bg: '#34C75920', border: '#34C759', dot: '#34C759' },  // Vert
    { bg: '#FF6B9D20', border: '#FF6B9D', dot: '#FF6B9D' },  // Rose
    { bg: '#4ECDC420', border: '#4ECDC4', dot: '#4ECDC4' },  // Turquoise
    { bg: '#FFB80020', border: '#FFB800', dot: '#FFB800' },  // Jaune
  ];
  return colors[index % colors.length];
};
```

Chaque condition reçoit une couleur différente en rotation.

## 💡 UX et Détails

### États de Chargement
1. **Initial** : Skeleton loader avec message
2. **Rechargement** : Mise à jour discrète
3. **Après ajout** : Transition fluide

### Confirmations
- **Suppression** : Alert avec nom de la condition
- **Ajout** : Fermeture automatique du modal
- **Erreur** : Message explicite

### Accessibilité
- Zones tactiles généreuses (hitSlop)
- Contrastes de couleurs respectés
- Textes lisibles et hiérarchisés
- Feedback visuel sur les actions

### Performance
- Chargement optimisé
- Mise à jour locale après suppression
- Pas de re-render inutile
- ScrollView performant

## 🔗 Ajout au Menu Profil

Dans `app/(tabs)/profil.tsx` :

```typescript
{/* Conditions de santé */}
<TouchableOpacity 
  style={styles.menuItem}
  onPress={() => router.push('/health-conditions')}
>
  <View style={[styles.menuIcon, { backgroundColor: '#FF2D55' }]}>
    <Heart size={24} color="#FFFFFF" />
  </View>
  <Text style={styles.menuText}>Conditions de santé</Text>
  <View style={styles.menuArrow} />
</TouchableOpacity>
```

## 📱 Navigation Complète

```
Profil (Account)
├── Goals → /goals
├── My Body → /my-body
├── Settings → /settings
├── Normalisation → /baselines
└── Conditions de santé → /health-conditions ✨ NOUVEAU
```

## ✨ Points Forts

1. **Design élégant** - Interface moderne et colorée
2. **UX soignée** - États vides, loading, erreurs gérés
3. **Réutilisation** - ConditionPicker déjà existant
4. **Pédagogique** - Section "Pourquoi c'est important"
5. **Sécurisant** - Note sur la confidentialité
6. **Flexible** - Système de couleurs automatique
7. **Accessible** - Grandes zones tactiles et contrastes

## 🚀 Améliorations Futures

### Phase 1 : Fonctionnalités
- [ ] Édition de conditions
- [ ] Catégories de conditions
- [ ] Dates de diagnostic
- [ ] Notes personnelles
- [ ] Export des conditions

### Phase 2 : UX
- [ ] Animation d'ajout/suppression
- [ ] Pull-to-refresh
- [ ] Recherche locale
- [ ] Filtres par catégorie
- [ ] Tri personnalisé

### Phase 3 : Analytics
- [ ] Impact sur les recommandations
- [ ] Historique des modifications
- [ ] Statistiques d'utilisation
- [ ] Suggestions de conditions

### Phase 4 : Intégration
- [ ] Lien avec les médicaments
- [ ] Alertes personnalisées
- [ ] Partage avec professionnels
- [ ] Import depuis dossier médical

## 🎨 Exemples Visuels

### État Vide
```
┌──────────────────────────┐
│    [ Heart Icon 64px ]   │
│                          │
│  Aucune condition        │
│  renseignée              │
│                          │
│  Commencez par ajouter...│
│                          │
│  [+ Ajouter condition]   │
└──────────────────────────┘
```

### Avec Conditions
```
┌──────────────────────────┐
│ 🔴 Hypertension          │
│ Code: I10            [×] │
└──────────────────────────┘

┌──────────────────────────┐
│ 🟣 Diabète Type 2        │
│ Code: E11            [×] │
└──────────────────────────┘

┌──────────────────────────┐
│ 🟢 Asthme                │
│ Code: J45            [×] │
└──────────────────────────┘
```

## 📝 Code Key Features

### Gestion Couleurs Automatique
```typescript
{conditions.map((condition, index) => {
  const colors = getConditionColor(index);
  return (
    <View style={{
      backgroundColor: colors.bg,
      borderColor: colors.border
    }}>
      <View style={{ backgroundColor: colors.dot }} />
      <Text>{condition.display}</Text>
    </View>
  );
})}
```

### Modal Integration
```typescript
<Modal visible={conditionPickerVisible}>
  <ConditionPicker
    onClose={() => setConditionPickerVisible(false)}
    onSuccess={() => {
      fetchConditions(); // Refresh list
    }}
  />
</Modal>
```

### Delete with Confirmation
```typescript
const handleDeleteCondition = async (id, display) => {
  Alert.alert(
    'Supprimer la condition',
    `Voulez-vous retirer "${display}" ?`,
    [
      { text: 'Annuler', style: 'cancel' },
      {
        text: 'Supprimer',
        style: 'destructive',
        onPress: async () => {
          await deleteCondition(id);
        }
      }
    ]
  );
};
```

## ✅ Checklist de Validation

- [x] Page créée et fonctionnelle
- [x] Ajoutée au menu profil
- [x] Design cohérent avec les autres pages
- [x] Tous les états gérés (loading, empty, error)
- [x] Ajout de conditions fonctionnel
- [x] Suppression avec confirmation
- [x] Compteurs et stats corrects
- [x] Navigation fluide
- [x] Composants réutilisés (ConditionPicker)
- [x] Documentation complète
- [x] Pas d'erreurs de linter
- [x] UX soignée et accessible

## 🔒 Sécurité et Confidentialité

### Données Sensibles
- Conditions de santé = données médicales sensibles
- Stockage sécurisé dans la base de données
- Accès restreint à l'utilisateur
- Pas de partage sans consentement

### Messages
- Note de confidentialité visible
- Badge "Facultatif" pour rassurer
- Explications claires sur l'usage

---

**Date de création**: 4 Février 2026  
**Status**: ✅ Terminé et fonctionnel  
**Fichier**: `app/health-conditions.tsx`  
**Route**: `/health-conditions`  
**Icône**: Heart (❤️)  
**Couleur**: Rose `#FF2D55`
