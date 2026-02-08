# Why Energy Stack - Implémentation Complète

## 🎉 Résumé

Le **Why Energy Stack** transforme Pulse d'un simple tracker en un **Coach Partenaire** qui explique le score d'énergie via des **analogies simples et percutantes** générées par GPT-4o.

**Status** : ✅ MVP Implémenté (Backend + Frontend)  
**Date** : 2026-02-02  
**Technologies** : Python FastAPI, React Native (Expo SDK 54), GPT-4o  

---

## 📁 Fichiers Créés

### Backend (Python)

```
backend/
├── explain_service.py              # Service d'explication énergétique (NEW)
├── api_server.py                   # Endpoint /api/energy/explain/{user_id} ajouté (MODIFIED)
└── test_explain_service.py         # Tests unitaires (NEW)
```

### Frontend (React Native / TypeScript)

```
mobile/
├── src/
│   ├── hooks/
│   │   └── useEnergyExplanation.ts       # Hook React Query (NEW)
│   └── components/
│       └── WhyEnergyStack.tsx            # Composant UI des cartes (NEW)
└── app/
    └── (tabs)/
        └── energie.tsx                   # Intégration WhyEnergyStack (MODIFIED)
```

### Documentation

```
mobile/
└── WHY_ENERGY_STACK_MVP.md               # Documentation technique complète (NEW)

/
└── WHY_ENERGY_STACK_IMPLEMENTATION.md    # Ce fichier (NEW)
```

---

## 🔄 Flow Complet

```
┌─────────────────────────────────────────────────────────────┐
│                    UTILISATEUR                               │
│                 Ouvre l'écran Énergie                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               FRONTEND (React Native)                        │
│                                                              │
│  1. energie.tsx                                              │
│     └─> useEnergyExplanation() hook                         │
│         └─> GET /api/energy/explain/{user_id}               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               BACKEND (FastAPI)                              │
│                                                              │
│  2. api_server.py                                            │
│     └─> explain_energy() endpoint                           │
│         └─> EnergyExplainService.generate_explanation()     │
│             │                                                │
│             ├─> Récupère daily_energy (score 38%)           │
│             ├─> Récupère daily_state (recovery, sleep, etc) │
│             ├─> Récupère médicaments actifs                 │
│             ├─> Récupère conditions de santé                │
│             ├─> Récupère biométriques (HRV, RHR, etc)       │
│             │                                                │
│             └─> Construit prompt pour GPT-4o                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  GPT-4o (OpenAI)                             │
│                                                              │
│  3. Génère 3 cartes narratives                              │
│     ├─> Type: nervous (Système nerveux) ⚡️                  │
│     │   Analogie: "Câble sectionné"                         │
│     │                                                        │
│     ├─> Type: chemistry (Chimie corporelle) 💊              │
│     │   Analogie: "Moteur bridé"                            │
│     │                                                        │
│     └─> Type: load (Charge & Effort) 🎒                     │
│         Analogie: "Sac à dos invisible"                     │
│                                                              │
│  Retourne JSON structuré                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               FRONTEND (React Native)                        │
│                                                              │
│  4. WhyEnergyStack component                                │
│     ├─> Affiche les cartes en scroll horizontal             │
│     ├─> Effet glassmorphism (expo-blur)                     │
│     ├─> Animations fluides (reanimated)                     │
│     └─> Press feedback & pagination dots                    │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    UTILISATEUR                               │
│      Comprend POURQUOI son énergie est à 38%                │
│      Validation empathique + Autorité technique              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 Exemple de Sortie

### Requête

```http
GET /api/energy/explain/c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd?date=2026-02-01
Authorization: Bearer eyJhbGc...
```

### Réponse (JSON)

```json
{
  "energyScore": 38,
  "confidence": 62,
  "label": "Journée fragile",
  "date": "2026-02-01",
  "cards": [
    {
      "type": "nervous",
      "title": "Le câblage est saturé",
      "text": "Ton HRV est tombé à 20ms (baseline: 30ms). Ton système nerveux parasympathique ne récupère plus efficacement. C'est lui qui gère la régénération nocturne.",
      "analogy": "C'est comme charger ton téléphone avec un câble sectionné : l'énergie ne passe plus correctement.",
      "metrics": {
        "primary": {"label": "HRV actuel", "value": 20, "unit": "ms"},
        "secondary": {"label": "HRV baseline", "value": 30, "unit": "ms"}
      }
    },
    {
      "type": "chemistry",
      "title": "Réservoir plein, moteur bridé",
      "text": "Ton sommeil est correct (81/100), mais tes médicaments (68% d'impact) empêchent ton corps d'utiliser cette récupération pleinement.",
      "analogy": "Tu as fait le plein d'essence, mais ton moteur a un limiteur de vitesse actif.",
      "metrics": {
        "primary": {"label": "Impact total", "value": 68, "unit": "%"},
        "secondary": {"label": "Score sommeil", "value": 81, "unit": "/100"}
      }
    },
    {
      "type": "load",
      "title": "Le coût de l'oxygène",
      "text": "Tes sinus obstrués forcent ton corps à dépenser de l'énergie supplémentaire juste pour maintenir une oxygénation correcte, augmentant ton RHR de repos.",
      "analogy": "C'est comme courir avec un sac à dos invisible toute la journée.",
      "metrics": {
        "primary": {"label": "RHR actuel", "value": 65, "unit": "bpm"},
        "secondary": {"label": "RHR baseline", "value": 63, "unit": "bpm"}
      }
    }
  ]
}
```

### Affichage Mobile

```
┌─────────────────────────────────────────────┐
│  Pourquoi ce score ?              38%       │
│                            Journée fragile  │
└─────────────────────────────────────────────┘

[Scroll horizontal →]

╔═══════════════════════════════════════════╗
║  ⚡️  [SYSTÈME NERVEUX]                    ║
║                                           ║
║  Le câblage est saturé                    ║
║                                           ║
║  Ton HRV est tombé à 20ms (baseline:      ║
║  30ms). Ton système nerveux parasym-      ║
║  pathique ne récupère plus efficacement.  ║
║                                           ║
║  ┌──────────────────┬──────────────────┐  ║
║  │ HRV actuel: 20ms │ Baseline: 30ms   │  ║
║  └──────────────────┴──────────────────┘  ║
║                                           ║
║  ╭────────────────────────────────────╮   ║
║  │ 💡 C'est comme charger ton         │   ║
║  │    téléphone avec un câble         │   ║
║  │    sectionné : l'énergie ne passe  │   ║
║  │    plus correctement.              │   ║
║  ╰────────────────────────────────────╯   ║
╚═══════════════════════════════════════════╝

[●] [ ] [ ]  ← Pagination dots
```

---

## 🧪 Tests

### Backend Test

```bash
cd /Users/dannezri/Desktop/Pulse/backend

# Test du service
python test_explain_service.py
```

**Résultat attendu** :
```
🚀 WHY ENERGY STACK - TEST SUITE
============================================================
📊 Test pour user_id: c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd
📅 Date: 2026-02-01

🤖 Génération de l'explication via GPT-4o...

✅ RÉSULTATS:
============================================================
🔋 Score d'énergie: 38%
📊 Confiance: 62%
🏷️  Label: Journée fragile
📅 Date: 2026-02-01

📇 Cartes générées: 3
============================================================

📋 CARTE 1 - Type: nervous
...

✅ Toutes les validations sont passées!
✅ TOUS LES TESTS SONT PASSÉS!
```

### Frontend Test

```bash
cd /Users/dannezri/Desktop/Pulse/mobile

# Vérifier les dépendances
npx expo-doctor

# Lancer l'app
npx expo start --clear
```

**Navigation manuelle** :
1. Login avec credentials
2. Aller sur l'onglet "Énergie"
3. Scroll vers le bas après le score actuel
4. Le WhyEnergyStack devrait apparaître
5. Tester le scroll horizontal
6. Tester le press feedback

---

## ⚙️ Configuration

### Variables d'Environnement (Backend)

```bash
# backend/.env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o  # Optionnel, défaut = gpt-4o
SUPABASE_URL=https://...
SUPABASE_SERVICE_KEY=...
```

### Dépendances (Frontend)

Toutes les dépendances sont **déjà installées** :

```json
{
  "expo-blur": "~15.0.8",
  "react-native-reanimated": "~4.1.1",
  "@tanstack/react-query": "^5.17.0"
}
```

---

## 🚀 Déploiement

### Backend

```bash
cd /Users/dannezri/Desktop/Pulse/backend

# Restart le serveur FastAPI
./restart_api_server.sh
```

Le nouvel endpoint sera disponible sur :
```
http://localhost:8000/api/energy/explain/{user_id}
```

### Frontend

```bash
cd /Users/dannezri/Desktop/Pulse/mobile

# Rebuild avec les nouveaux fichiers
npx expo start --clear
```

---

## 🎯 Validation du MVP

### ✅ Fonctionnalités Implémentées

| Feature | Backend | Frontend | Status |
|---------|---------|----------|--------|
| Service d'explication | ✅ | - | Done |
| Endpoint API | ✅ | - | Done |
| Prompt GPT-4o optimisé | ✅ | - | Done |
| Hook React Query | - | ✅ | Done |
| Composant WhyEnergyStack | - | ✅ | Done |
| Intégration écran Énergie | - | ✅ | Done |
| Glassmorphism design | - | ✅ | Done |
| Animations fluides | - | ✅ | Done |
| Tests unitaires | ✅ | ⏳ | Backend only |
| Documentation | ✅ | ✅ | Done |

### 🧪 Tests à Effectuer

- [ ] Backend : Tester avec plusieurs user_ids
- [ ] Backend : Tester les cas d'erreur (user inexistant, pas de données)
- [ ] Frontend : Tester scroll horizontal sur iOS
- [ ] Frontend : Tester scroll horizontal sur Android
- [ ] Frontend : Tester press feedback
- [ ] Frontend : Tester avec 0, 1, 2, 3 cartes
- [ ] Integration : Tester la latence end-to-end
- [ ] Integration : Tester le cache React Query

---

## 📊 Impact Attendu

### Validation Psychologique
**Avant** : "Pourquoi je suis à 38% ?! 😢"  
**Après** : "Ah, c'est mon HRV qui est bas. Ça a du sens." ✅

### Autorité Technique
En citant des métriques précises (HRV 20ms → 30ms baseline), l'app prouve sa précision médicale.

### Scalabilité par l'IA
Que l'utilisateur ait une grippe, un lendemain de fête ou une dépression, GPT-4o trouve toujours l'analogie juste.

---

## 🤝 Contribution

### Améliorer les Analogies

Modifier le prompt dans `backend/explain_service.py` ligne 210-350 :

```python
prompt = f"""
...
### Exemple 1 : Récupération faible (HRV bas)
{{
  "type": "nervous",
  "title": "Le câblage est saturé",
  "analogy": "C'est comme charger ton téléphone avec un câble sectionné."
}}
...
"""
```

### Ajouter un Nouveau Type de Carte

1. Ajouter le type dans le type union TypeScript :

```typescript
// mobile/src/hooks/useEnergyExplanation.ts
export interface EnergyCard {
  type: 'nervous' | 'chemistry' | 'load' | 'NEW_TYPE'; // Ajouter ici
  ...
}
```

2. Ajouter l'icône et la couleur :

```typescript
export function getCardIcon(type: EnergyCard['type']): string {
  switch (type) {
    case 'NEW_TYPE':
      return '🆕';
    ...
  }
}
```

3. Ajouter la logique de priorisation dans le backend :

```python
# backend/explain_service.py
if new_condition:
    # Carte "NEW_TYPE"
    ...
```

---

## 📚 Documentation Complète

Pour plus de détails techniques :
- **MVP Guide** : `mobile/WHY_ENERGY_STACK_MVP.md`
- **API Reference** : `backend/explain_service.py` (docstrings)
- **Component API** : `mobile/src/components/WhyEnergyStack.tsx` (JSDoc)
- **Hook API** : `mobile/src/hooks/useEnergyExplanation.ts` (JSDoc)

---

## 🎓 Conclusion

Le **Why Energy Stack** est maintenant **complètement implémenté** et prêt pour les tests.

### Prochaines Étapes Recommandées

1. **Test Manuel** : Lancer l'app et naviguer vers l'écran Énergie
2. **Validation Utilisateur** : Tester avec plusieurs profils utilisateurs
3. **Monitoring** : Ajouter des logs pour mesurer la latence et le cache hit rate
4. **Feedback Loop** : Ajouter un bouton "Cette explication est-elle utile ?"
5. **Optimisation** : Ajuster les prompts GPT-4o selon les retours utilisateurs

---

**Auteur** : Assistant AI  
**Date** : 2026-02-02  
**Version** : MVP 1.0  
**License** : Privé (Pulse)  
**Status** : ✅ Prêt pour Production Testing
