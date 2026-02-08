# 🚀 Why Energy Stack - Quick Start Guide

## ✅ Ce qui a été implémenté

Le **Why-Stack** piloté par GPT-4o est maintenant **complètement opérationnel** ! 🎉

```
┌──────────────────────────────────────────────────────────┐
│  Avant                           Après                   │
│  ─────                           ─────                   │
│  Score: 38% ❓                  Score: 38% 💡           │
│  Utilisateur confus              Explication claire       │
│  Données brutes                  Analogies simples       │
│  Pas de contexte                 Validation empathique   │
└──────────────────────────────────────────────────────────┘
```

---

## 📁 Structure des Fichiers

```
Pulse/
│
├── backend/
│   ├── explain_service.py                    ✅ NEW - Service d'explication
│   ├── api_server.py                         ✏️  MODIFIED - Endpoint ajouté
│   ├── test_explain_service.py               ✅ NEW - Tests unitaires
│   └── example_explain_response.json         ✅ NEW - Exemple de réponse
│
├── mobile/
│   ├── src/
│   │   ├── hooks/
│   │   │   └── useEnergyExplanation.ts       ✅ NEW - Hook React Query
│   │   └── components/
│   │       └── WhyEnergyStack.tsx            ✅ NEW - Composant UI
│   ├── app/
│   │   └── (tabs)/
│   │       └── energie.tsx                   ✏️  MODIFIED - Intégration
│   └── WHY_ENERGY_STACK_MVP.md              ✅ NEW - Documentation technique
│
├── WHY_ENERGY_STACK_IMPLEMENTATION.md        ✅ NEW - Guide complet
├── WHY_STACK_QUICK_START.md                  ✅ NEW - Ce fichier
└── test-why-stack.sh                         ✅ NEW - Script de test
```

---

## 🎯 Test en 3 Étapes

### 1️⃣ Vérifier l'Implémentation

```bash
cd /Users/dannezri/Desktop/Pulse
./test-why-stack.sh
```

Ce script vérifie :
- ✅ Tous les fichiers sont créés
- ✅ Backend est accessible
- ✅ Dépendances frontend sont installées

### 2️⃣ Tester le Backend

```bash
cd backend
python test_explain_service.py
```

**Résultat attendu** :
```
🚀 WHY ENERGY STACK - TEST SUITE
============================================================
📊 Test pour user_id: c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd
🤖 Génération de l'explication via GPT-4o...

✅ RÉSULTATS:
🔋 Score d'énergie: 38%
📊 Confiance: 62%
📇 Cartes générées: 3

✅ TOUS LES TESTS SONT PASSÉS!
```

### 3️⃣ Tester le Frontend

```bash
cd mobile
npx expo start --clear
```

**Navigation dans l'app** :
1. Se connecter
2. Aller sur l'onglet **"Énergie"** (⚡️ icône)
3. Scroll vers le bas après le score actuel
4. ➡️ Le **WhyEnergyStack** apparaît avec les cartes

**Test d'interaction** :
- Swipe horizontalement pour voir les 3 cartes
- Press sur une carte pour feedback tactile
- Observer les animations fluides

---

## 🎨 Aperçu Visuel

### Carte Exemple (Type: Nervous ⚡️)

```
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
```

---

## 🔑 Endpoints API

### GET /api/energy/explain/{user_id}

**Request** :
```http
GET /api/energy/explain/c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd?date=2026-02-01
Authorization: Bearer <jwt_token>
```

**Response** :
```json
{
  "energyScore": 38,
  "confidence": 62,
  "label": "Journée fragile",
  "cards": [
    {
      "type": "nervous",
      "title": "Le câblage est saturé",
      "text": "...",
      "analogy": "...",
      "metrics": {...}
    }
  ]
}
```

**Format complet** : Voir `backend/example_explain_response.json`

---

## 🧩 Types de Cartes

| Type | Icône | Couleur | Quand ? |
|------|-------|---------|---------|
| **nervous** | ⚡️ | Rouge | Recovery < 50%, HRV bas, RHR élevé |
| **chemistry** | 💊 | Orange | Impact médicaments > 50%, sommeil bon mais score bas |
| **load** | 🎒 | Jaune | Overtrain < 50%, conditions chroniques |

---

## 🛠️ Configuration

### Backend (`.env`)

```bash
OPENAI_API_KEY=sk-...           # REQUIS
OPENAI_MODEL=gpt-4o             # Optionnel (défaut: gpt-4o)
SUPABASE_URL=https://...        # REQUIS
SUPABASE_SERVICE_KEY=...        # REQUIS
```

### Frontend

**Dépendances déjà installées** :
- ✅ `expo-blur` ~15.0.8
- ✅ `react-native-reanimated` ~4.1.1
- ✅ `@tanstack/react-query` ^5.17.0

**Vérifier** :
```bash
cd mobile
npx expo-doctor
```

---

## 📊 Architecture Simplifiée

```
┌─────────────┐
│  User       │  Ouvre l'écran Énergie
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────┐
│  energie.tsx                         │
│  └─> useEnergyExplanation()         │
│      └─> GET /api/energy/explain/   │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  Backend API                         │
│  └─> EnergyExplainService            │
│      ├─> daily_energy (38%)          │
│      ├─> daily_state (recovery...)   │
│      ├─> medications                 │
│      ├─> conditions                  │
│      └─> biometrics (HRV, RHR...)    │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  GPT-4o                              │
│  Génère 3 cartes narratives          │
│  avec analogies                      │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  WhyEnergyStack                      │
│  Affiche les cartes                  │
│  Scroll horizontal + Animations      │
└──────────────────────────────────────┘
```

---

## 📖 Documentation Complète

| Document | Description |
|----------|-------------|
| `WHY_ENERGY_STACK_IMPLEMENTATION.md` | Guide complet d'implémentation |
| `mobile/WHY_ENERGY_STACK_MVP.md` | Documentation technique détaillée |
| `WHY_STACK_QUICK_START.md` | Ce fichier (Quick Start) |
| `backend/explain_service.py` | Code source avec docstrings |
| `mobile/src/components/WhyEnergyStack.tsx` | Code source avec JSDoc |

---

## 🎯 Checklist de Validation

### Backend
- [x] Service créé (`explain_service.py`)
- [x] Endpoint ajouté (`/api/energy/explain`)
- [x] Tests unitaires créés
- [x] Prompt GPT-4o optimisé
- [x] Gestion d'erreurs

### Frontend
- [x] Hook créé (`useEnergyExplanation`)
- [x] Composant créé (`WhyEnergyStack`)
- [x] Intégration dans `energie.tsx`
- [x] Glassmorphism design
- [x] Animations fluides

### Tests à Effectuer
- [ ] Backend: Tester avec plusieurs users
- [ ] Frontend: Tester scroll horizontal
- [ ] Frontend: Tester press feedback
- [ ] Integration: Tester latence end-to-end

---

## 🚀 Démarrage Rapide

### 1. Lancer le Backend

```bash
cd backend
python api_server.py
```

### 2. Lancer le Frontend

```bash
cd mobile
npx expo start --clear
```

### 3. Naviguer dans l'App

```
Login → Onglet "Énergie" → Scroll ↓ → Why-Stack apparaît
```

---

## 🤔 Troubleshooting

### Backend ne démarre pas

**Problème** : `ModuleNotFoundError: No module named 'openai'`

**Solution** :
```bash
cd backend
pip install -r requirements.txt
```

### Frontend ne compile pas

**Problème** : Erreur TypeScript sur `useEnergyExplanation`

**Solution** :
```bash
cd mobile
npx expo install --fix
npx expo start --clear
```

### Les cartes n'apparaissent pas

**Problème** : Hook ne récupère pas les données

**Vérifier** :
1. Backend est lancé : `curl http://localhost:8000/health`
2. JWT token est valide
3. User a des données : Vérifier dans Supabase `daily_energy` table

---

## 💡 Exemples d'Analogies Générées

### Type: Nervous ⚡️
- "Câble sectionné"
- "Circuit saturé"
- "Disjoncteur sauté"

### Type: Chemistry 💊
- "Moteur bridé"
- "Limiteur de vitesse"
- "Frein à main actif"

### Type: Load 🎒
- "Sac à dos invisible"
- "Courir dans le sable"
- "Escalier sans paliers"

---

## 🎉 Conclusion

Le **Why Energy Stack** est **prêt pour les tests** !

**Impact attendu** :
- ✅ Validation psychologique de l'utilisateur
- ✅ Autorité technique prouvée
- ✅ Scalabilité par l'IA (s'adapte à tous les profils)

**Coût par explication** : ~$0.01 (OpenAI GPT-4o)  
**Latence attendue** : < 3 secondes  
**Cache** : 30 minutes (React Query)

---

**Prêt pour production testing** ✅  
**Date** : 2026-02-02  
**Version** : MVP 1.0

---

## 📞 Besoin d'Aide ?

- 📖 Documentation technique : `mobile/WHY_ENERGY_STACK_MVP.md`
- 🏗️ Guide d'implémentation : `WHY_ENERGY_STACK_IMPLEMENTATION.md`
- 🧪 Tests : `./test-why-stack.sh`
- 🐛 Logs Backend : `backend/backend.log`
