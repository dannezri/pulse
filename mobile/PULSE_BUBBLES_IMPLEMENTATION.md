# 🎨 Pulse Bubbles - Interface Haute Définition

## 📋 Vue d'ensemble

Ce document décrit l'implémentation des **"Pulse Bubbles"** - un système de bulles d'alerte visuelles pour l'analyse IA des événements du calendrier.

## ✨ Fonctionnalités

### 1. Bulles d'Alerte Visuelles

Les **blockquotes Markdown** (`>`) sont maintenant transformées en **bulles d'alerte** visuelles avec :
- Fond sombre (`#1C1C1E`)
- Bordure gauche rouge alerte (`#FF3B30`, 4px)
- Coins arrondis (12px)
- Ombre portée pour créer de la profondeur
- Padding généreux pour la lisibilité

### 2. Hiérarchie Visuelle Renforcée

#### Titres
- **H1** : Vert Pulse (`#34C759`) - Pour le "Diagnostic Flash"
- **H2** : Orange Attention (`#FF9500`) - Pour les sections importantes
- **H3** : Blanc - Pour les sous-sections

#### Emphases
- **Gras** (`**texte**`) : Vert Pulse pour les métriques clés (HRV, Sommeil, etc.)
- *Italique* (`*texte*`) : Gris discret pour les notes secondaires

### 3. Smart Cache Intégré

Le système de cache intelligent est déjà implémenté :
- ✅ **Cache actif** : Affiche "💾 Analysé il y a X min (Cache)"
- ⚡ **Nouvelle analyse** : Affiche "Analysé il y a X min"
- 🔄 **Bouton Recalculer** : Force une nouvelle analyse si nécessaire

## 📱 Exemple d'Utilisation

### Prompt LLM (Backend)

Le prompt demande maintenant explicitement d'utiliser des blockquotes pour les actions :

```markdown
## ⚡ Actions Immédiates

> **Avant l'événement (30 min)**
> - Prendre 20g de glucides rapides (banane, miel)
> - Hydratation : 500ml d'eau
> - 5 minutes de respiration pour activer le parasympathique

> **Pendant l'événement**
> - Fractionnez l'effort : 20 min d'activité, 5 min de repos
> - Surveillez votre fréquence cardiaque (ne pas dépasser 140 bpm)

> **Après l'événement**
> - Repas riche en protéines dans les 30 minutes
> - Sieste de 20 minutes si possible
```

### Rendu Mobile

Les blockquotes s'affichent comme des **bulles d'alerte** :
- Fond noir profond
- Bordure rouge vif à gauche
- Texte blanc avec emojis
- Effet d'ombre pour la profondeur

## 🎯 Architecture

### Frontend (Mobile)

**Fichier** : `/mobile/app/event-detail.tsx`

**Styles Markdown Clés** :
```typescript
blockquote: {
  backgroundColor: '#1C1C1E',
  borderLeftWidth: 4,
  borderLeftColor: '#FF3B30',
  borderRadius: 12,
  paddingHorizontal: 16,
  paddingVertical: 12,
  marginVertical: 15,
  shadowColor: '#FF3B30',
  shadowOffset: { width: 0, height: 2 },
  shadowOpacity: 0.3,
  shadowRadius: 8,
}
```

### Backend (API)

**Fichiers** :
- `/backend/services/ai_service.py` : Smart Cache + Prompt construction
- `/backend/llm_client.py` : Appel OpenAI avec format JSON

**Flow du Smart Cache** :
1. Génère un ID stable pour l'événement (hash de user_id + title + start + end)
2. Récupère le dernier insight en cache
3. Compare `insight.created_at` avec `biometrics.recorded_at`
4. Si nouvelles données → Rappel OpenAI
5. Sinon → Retourne le cache (0€, instantané)

## 🚀 Utilisation

### Côté Mobile

```typescript
import { useEventAnalysis } from '../src/hooks/useEventAnalysis';

// Lancer l'analyse avec cache
const { mutate, data, isLoading } = useEventAnalysis(userId, event);
mutate({ forceRefresh: false }); // Utilise le cache si disponible

// Forcer une nouvelle analyse
mutate({ forceRefresh: true }); // Bypass le cache
```

### Côté Backend

```bash
# Démarrer le serveur avec le endpoint /api/v1/analyze-event
cd backend
python api_server.py
```

**Endpoint** : `POST /api/v1/analyze-event`

**Body** :
```json
{
  "user_id": "uuid",
  "event": {
    "title": "Séance de Padel",
    "start": "2024-01-15T10:00:00Z",
    "end": "2024-01-15T11:00:00Z",
    "location": "Club de sport",
    "notes": ""
  },
  "force_refresh": false
}
```

**Réponse** :
```json
{
  "status": "success",
  "insight": "# 🔴 Diagnostic Flash\n\nÉvénement à risque...",
  "cached": false,
  "analyzed_at": "2024-01-15T09:30:00Z",
  "biometrics_ref_at": "2024-01-15T09:25:00Z"
}
```

## 💰 Économies Réalisées

### Sans Smart Cache
- Chaque analyse : ~$0.01
- 100 analyses/jour : $1.00/jour = $30/mois

### Avec Smart Cache
- Cache hit : $0.00
- Cache miss : ~$0.01
- Taux de cache estimé : 80%
- 100 analyses/jour : $0.20/jour = $6/mois

**Économies : ~80% ($24/mois pour 100 analyses/jour)**

## 📊 Métriques de Performance

### Temps de Réponse
- **Cache hit** : ~50ms (lecture Supabase)
- **Cache miss** : ~2-5s (appel OpenAI + sauvegarde)

### Taille des Réponses
- Prompt : ~500-800 tokens
- Réponse : ~400-800 tokens
- Coût par analyse : ~$0.008-0.012 (gpt-4o)

## 🎨 Palette de Couleurs

### Couleurs Principales
- **Vert Pulse** : `#34C759` - Diagnostic positif, métriques saines
- **Orange Attention** : `#FF9500` - Vigilance, alertes modérées
- **Rouge Alerte** : `#FF3B30` - Danger, actions immédiates requises
- **Bleu iOS** : `#0A84FF` - Liens, informations

### Couleurs de Fond
- **Noir profond** : `#000000` - Background principal
- **Gris foncé** : `#1C1C1E` - Cards, bulles
- **Gris moyen** : `#2C2C2E` - Code inline, fences
- **Gris clair** : `#8E8E93` - Texte secondaire

## 🔧 Configuration

### Dépendances Requises

**Mobile** :
```json
{
  "react-native-markdown-display": "^7.0.2"
}
```

**Backend** :
```txt
openai>=1.0.0
python-dotenv
```

### Variables d'Environnement

```bash
# Backend
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
SUPABASE_URL=https://...
SUPABASE_SERVICE_KEY=...
```

## 📝 Checklist de Validation

- [x] Styles Markdown avec bulles d'alerte (blockquotes)
- [x] Smart Cache implémenté (compare biometrics.recorded_at)
- [x] Footer de cache avec timestamp et indicateur
- [x] Bouton "Recalculer" pour forcer refresh
- [x] Prompt LLM optimisé avec structure obligatoire
- [x] Format JSON structuré `{"insight": "MARKDOWN"}`
- [x] Hiérarchie visuelle avec couleurs Apple Health
- [x] Emojis pour la clarté (🟢🟡🔴💡⚡)

## 🎓 Conseils d'Utilisation

### Pour l'IA (Prompt Engineering)

1. **Utilisez des emojis de couleur** au début du Diagnostic Flash :
   - 🟢 pour "GO"
   - 🟡 pour "VIGILANCE"
   - 🔴 pour "PIVOT/DANGER"

2. **Encadrez les actions dans des blockquotes** :
   ```markdown
   > **Avant l'événement**
   > - Action 1
   > - Action 2
   ```

3. **Utilisez le gras pour les métriques** :
   ```markdown
   **HRV bas** (45ms vs moyenne 60ms)
   ```

### Pour l'Utilisateur

1. **Lisibilité en 3 secondes** :
   - Emoji de couleur → Verdict immédiat
   - Bulles rouges → Actions urgentes
   - Gras vert → Métriques clés

2. **Badge de Cache** :
   - 💾 = Données déjà analysées (réponse instantanée)
   - Sans 💾 = Nouvelle analyse (quelques secondes)

3. **Bouton Recalculer** :
   - Utilisez-le après avoir ajouté de nouvelles données biométriques
   - Ou si vous voulez une analyse plus fraîche

## 🚨 Troubleshooting

### "L'analyse prend trop de temps"
→ Timeout de 15s activé. Si dépassé, l'API retourne une erreur 504.

### "Le cache n'est jamais utilisé"
→ Vérifiez que `force_refresh: false` dans la requête.

### "Les blockquotes ne s'affichent pas correctement"
→ Vérifiez que `react-native-markdown-display` est en version 7.0.2+.

## 📚 Ressources

- [Documentation Expo SDK 54](https://docs.expo.dev/)
- [OpenAI API Reference](https://platform.openai.com/docs)
- [react-native-markdown-display](https://github.com/iamacup/react-native-markdown-display)

---

**Version** : 1.0.0  
**Date** : 28 janvier 2026  
**Auteur** : Pulse Team
