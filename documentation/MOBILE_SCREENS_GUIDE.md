# 📱 Guide Complet des Écrans Mobiles Pulse

> **Guide visuel et détaillé de chaque écran de l'application mobile**  
> **Date:** 30 Janvier 2026  
> **Version:** 3.0.0

---

## 📋 Table des Matières

1. [Brief Quotidien (Accueil)](#brief-quotidien-accueil)
2. [Tendances](#tendances)
3. [Journal Alimentaire](#journal-alimentaire)
4. [Profil](#profil)
5. [Écrans Secondaires](#écrans-secondaires)

---

## Brief Quotidien (Accueil)

**Route:** `app/(tabs)/index.tsx`  
**Rôle:** Page d'accueil principale - Briefing quotidien avec cartes empilées swipeable

> 🆕 **Note v3.0:** Le Brief est maintenant la seule page d'accueil de l'application. L'ancienne page Dashboard (avec Orb organique) a été supprimée pour simplifier la navigation et offrir une expérience plus directe.

### Mockup Visuel

```
╔══════════════════════════════════════════╗
║                                          ║
║  ┌────────────────────────────────────┐  ║
║  │ ⚡ TON ÉNERGIE AUJOURD'HUI         │  ║ Carte 1 (Energy Overview)
║  │ ─────────────────────────────────  │  ║ Plein écran
║  │                                    │  ║
║  │  🟢 78%                            │  ║
║  │  Bonne journée                     │  ║
║  │                                    │  ║
║  │ Pourquoi ?                         │  ║
║  │  • Récupération correcte           │  ║
║  │  • Dette de sommeil faible         │  ║
║  │  • Charge physique maîtrisée       │  ║
║  │                                    │  ║
║  │ ⚡ Action clé                      │  ║
║  │ 👉 Planifie tes tâches importantes │  ║
║  │    ce matin                        │  ║
║  │                                    │  ║
║  │ 📉 Creux prévu : 16h-18h           │  ║
║  │                                    │  ║
║  │         [Swipe pour suivante ↓]    │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  ┌──────────────────────────┐ ← Carte 2 ║
║  │ 📈 DEMAIN               │   (partielle)
║  │ ───────────────────────  │            ║
║  └──────────────────────────┘            ║
║                                          ║
║  ┌──────────────────┐ ← Carte 3         ║
║  │ 🌟 RECOVERY     │   (mini preview)   ║
║  └──────────────────┘                    ║
║                                          ║
║        ● ○ ○ ○ ○  (5 cartes)            ║
║                                          ║
╚══════════════════════════════════════════╝
```

### Données Affichées

#### 1. Stack de Cartes Brief (BriefStack)

**Structure :**
- Cartes plein écran empilées (stack vertical)
- Navigation par swipe vertical (haut/bas)
- Dots de navigation sur le côté
- Animations FadeInDown + haptic feedback
- Preview des cartes suivantes en arrière-plan

**Types de cartes (dans l'ordre) :**

##### Carte 1 : Energy Overview (Ton énergie aujourd'hui)

**Source :** ✅ API Backend `GET /api/energy/daily` (calcul serveur)

**Données affichées :**
```javascript
{
  energy_score: 78,               // ✅ 0-100 (cohérent avec forecast)
  label: "Bonne journée",         // Label lifestyle
  confidence: 82,                 // ✅ 0-100
  reasons: [
    {key: "recovery_good", text: "Récupération correcte"},
    {key: "sleep_debt_low", text: "Dette de sommeil faible"},
    {key: "overtrain_low", text: "Charge physique maîtrisée"}
  ],
  primary_action: {
    key: "deep_work_morning",
    title: "Planifie tes tâches importantes ce matin",
    why: "Ton énergie est meilleure en début de journée"
  },
  risk_windows: [
    {from: "16:00", to: "18:00", risk: "dip", text: "Creux d'énergie prévu"}
  ]
}
```

**Calcul du score :**

✅ **Calcul Backend** : Voir `backend/daily_energy_engine.py`

⚠️ **Convention des scores `daily_state` :**
- **Recovery** : `score` élevé (1) = **BON** (bien récupéré)
- **Sleep Debt** : `score` élevé (1) = **MAUVAIS** (dette élevée) → **INVERSER**
- **Overtrain** : `score` élevé (1) = **MAUVAIS** (risque élevé) → **INVERSER**
- **Infection** : `score` élevé (1) = **MAUVAIS** (signes forts) → **INVERSER**

```javascript
// Normaliser les états en "bons" (uniformisation)
recovery_good = recovery.score           // Déjà bon
sleep_debt_good = 1 - sleep_debt.score   // Inverser : 0 dette = 1 bon
overtrain_good = 1 - overtrain.score     // Inverser : 0 risque = 1 bon
infection_good = 1 - infection.score     // Inverser : 0 signe = 1 bon

// Pondérations
energy = (
  0.45 * recovery_good +
  0.25 * sleep_debt_good +
  0.20 * overtrain_good +
  0.10 * infection_good
)

// Label (en DB: 0-1, en API: 0-100)
if (energy >= 0.80) label = "Excellente journée"
elif (energy >= 0.65) label = "Bonne journée"
elif (energy >= 0.50) label = "Journée moyenne"
else label = "Journée fragile"
```

✅ **Convention API** : Le score est converti en **0-100** dans l'endpoint `GET /api/energy/daily` pour cohérence avec forecast.

**Contexte temporel :**
- Matin (6h-12h) : Focus planification, sport, réunions
- Après-midi (12h-18h) : Gestion énergie
- Soir (18h-22h) : Préparation sommeil
- Nuit (22h-6h) : Urgence repos

**🆕 Risk Window Personnalisé (Creux d'Énergie) :**

Le creux d'énergie prévu est **adapté personnellement** selon 3 facteurs :

1. **Chronotype** (via `mid_sleep` des baselines) :
   - Morning person (mid_sleep < 3h) → Creux plus tôt (-1h)
   - Evening person (mid_sleep > 4h) → Creux plus tard (+1h)
   - Normal (3-4h) → Baseline standard (16h-18h)

2. **Dette de Sommeil** :
   - Dette élevée (>4h) → Creux beaucoup plus tôt (-1.5h)
   - Dette modérée (2-4h) → Creux légèrement plus tôt (-0.5h)
   - Peu/pas de dette (<2h) → Pas d'ajustement

3. **Énergie Globale** :
   - Énergie basse (<50%) → Creux plus tôt (-1h)
   - Énergie haute (≥75%) → Creux plus tard (+0.5h)
   - Énergie moyenne → Pas d'ajustement

**Exemples Concrets :**

| Profil | Chronotype | Dette | Énergie | Creux Prévu |
|--------|------------|-------|---------|-------------|
| 🌅 Lève-tôt, reposé | Morning (2.5h) | 1h | 80% | 16h30-18h30 |
| 🌃 Couche-tard, reposé | Evening (4.5h) | 1.5h | 75% | 17h00-19h00 |
| 😴 Normal, épuisé | Normal (3.5h) | 5h | 45% | **13h00-15h00** |
| 🌅 Lève-tôt, épuisé | Morning (2.5h) | 6h | 40% | **12h30-14h30** |

**Avantages UX :**
- ✅ Pertinence biologique (chronotype réel)
- ✅ Personnalisation sans ML (utilise baselines existantes)
- ✅ Actionnable : Planifier réunions/sport en dehors du creux
- ✅ Évolue avec les données utilisateur

**🆕 Enrichissement Agenda (V2) :**

Le risk window est désormais **croisé avec les événements du calendrier** pour transformer une info passive en **assistant proactif**.

**Logic :**
1. Récupère les événements du jour
2. Identifie ceux qui tombent dans le creux d'énergie
3. Classe par importance :
   - **Critique (3)** : réunion, meeting, client, présentation, entretien
   - **Important (2)** : call, appel, rendez-vous, démo, review
   - **Normal (1)** : sport, gym, workout
   - **Personnel (0)** : lunch, déjeuner, café
4. Génère recommandation intelligente :
   - Événement **critique** → Proposer pause/boost avant (ne pas déplacer)
   - Événement **important** → Suggérer de déplacer hors du creux
   - Événement **normal** → Suggérer déplacer ou accepter baisse de rythme

**Format Enrichi :**
```typescript
risk_windows: [
  {
    from: "16:00",
    to: "18:00",
    risk: "dip",
    text: "⚠️ Réunion client prévu durant ce creux d'énergie",  // Enrichi si conflit
    has_conflict: true,
    conflicting_events: [
      {
        title: "Réunion client important",
        start: "2026-01-30T16:30:00Z",
        importance: 3
      }
    ],
    recommendation: {
      type: "prepare",  // ou "reschedule", "accept"
      action: "Prends une pause 30 min avant 'Réunion client'",
      details: "15 min de marche + snack protéiné + hydratation.",
      reason: "Événement critique durant un creux d'énergie prévu"
    }
  }
]
```

**Types de Recommandations :**
- **`prepare`** : Événement critique → Ne pas déplacer, mais préparer (pause, boost)
- **`reschedule`** : Événement important/normal → Proposer de déplacer
- **`accept`** : Trop d'événements ou contraintes → Accepter baisse de rythme

**Affichage dans la Carte (sans conflit agenda) :**

```
┌────────────────────────────────────┐
│ ⚡ TON ÉNERGIE AUJOURD'HUI         │
│                                    │
│  🟢 78%                            │
│  Bonne journée                     │
│                                    │
│ Pourquoi ?                         │
│  • Récupération correcte           │
│  • Dette de sommeil faible         │
│                                    │
│ ⚡ Action clé                      │
│ 👉 Planifie tes tâches importantes │
│    ce matin                        │
│                                    │
│ 📉 Creux prévu : 16h30-18h30       │ ← Personnalisé !
│    (selon ton chronotype)          │
└────────────────────────────────────┘
```

**Affichage avec Conflit Agenda (V2) :**

```
┌────────────────────────────────────┐
│ ⚡ TON ÉNERGIE AUJOURD'HUI         │
│                                    │
│  🟡 65%                            │
│  Journée moyenne                   │
│                                    │
│ Pourquoi ?                         │
│  • Récupération correcte           │
│  • Dette de sommeil modérée        │
│                                    │
│ ⚡ Action clé                      │
│ 👉 Planifie tes tâches importantes │
│    ce matin                        │
│                                    │
│ ⚠️ Creux prévu : 16h-18h           │
│    Réunion client durant ce creux  │ ← Alerte conflit !
│                                    │
│ 💡 Recommandation Pulse            │ ← NEW
│ 👉 Prends une pause 30 min avant   │
│    15 min de marche + snack        │
│    protéiné pour compenser         │
│                                    │
│    [Voir détails]                  │ ← Optionnel: expand
└────────────────────────────────────┘
```

**Autre Exemple (Reschedule) :**

```
┌────────────────────────────────────┐
│ ⚠️ Creux prévu : 14h-16h           │
│    2 événements durant ce creux    │
│                                    │
│ 💡 Recommandation Pulse            │
│ 👉 Déplace "Call équipe" hors du   │
│    creux d'énergie                 │
│                                    │
│    Suggère 10h-12h ou après 16h30  │
│    pour maximiser ta performance   │
│                                    │
│    [Déplacer dans calendrier] 📅   │ ← Deep link (future)
└────────────────────────────────────┘
```

**Cas Extrême (Dette Élevée + Morning Person) :**

```
┌────────────────────────────────────┐
│ ⚡ TON ÉNERGIE AUJOURD'HUI         │
│                                    │
│  🟡 45%                            │
│  Journée fragile                   │
│                                    │
│ Pourquoi ?                         │
│  • Dette de sommeil élevée (5.5h)  │
│  • Récupération incomplète         │
│                                    │
│ ⚡ Action clé                      │
│ 👉 Couche-toi 2h plus tôt ce soir  │
│                                    │
│ 📉 Creux prévu : 12h30-14h30       │ ← Très tôt !
│    ⚠️ Prévois une pause déjeuner   │
│       prolongée                    │
└────────────────────────────────────┘
```

---

**🔒 Convention Globale des Scores `daily_state` :**

Pour maintenir la cohérence dans tout le système :

| État | Convention Score | Interprétation |
|------|------------------|----------------|
| **Recovery** | `1 = BON` | Score élevé = Bien récupéré |
| **Sleep Debt** | `1 = MAUVAIS` | Score élevé = Dette élevée |
| **Overtrain** | `1 = MAUVAIS` | Score élevé = Risque élevé |
| **Infection** | `1 = MAUVAIS` | Score élevé = Signes forts |

⚠️ **Important** : Dans les agrégateurs (Energy Overview, prédictions), les scores "mauvais" sont systématiquement **inversés** en `_good` :
```javascript
recovery_good = recovery.score           // Déjà bon
sleep_debt_good = 1 - sleep_debt.score   // Inverser
overtrain_good = 1 - overtrain.score     // Inverser
infection_good = 1 - infection.score     // Inverser
```

Cette conversion garantit que dans **tous les calculs d'agrégation**, un score élevé signifie toujours "bon état".

---

##### Carte 2 : Energy Forecast (Prédiction Demain)

**Source :** `energy_forecast` table (généré par cron 21h)

**Données affichées :**
```javascript
{
  forecast_date: "2026-01-31",
  predicted_energy_score: 52,     // ✅ 0-100 (cohérent avec energy overview)
  predicted_state: "moderate",    // excellent/good/moderate/low
  primary_cause: "sleep_debt",    // Facteur limitant
  suggestion: "Couche-toi 1h plus tôt ce soir",
  confidence: 80                  // ✅ 0-100 (harmonisé)
}
```

**Affichage uniquement si `confidence >= 50`** (✅ 0-100)

#### 2. Cartes Brief Détaillées (Suite du Stack)

##### Carte 3+ : Recovery State (État de Récupération)

**Source :** `daily_state` table, `state_type = 'recovery'`

**Convention :** `score` élevé (proche de 1) = **BON** (bien récupéré)

**Données affichées :**
```javascript
{
  title: "Recovery State",
  score: 0.92,                    // 0-1 (1 = BON) converti en /100
  smoothed_score: 0.89,           // EMA lissé
  confidence: 0.95,               // Confiance du calcul
  model_version: "latent_v1",     // Version algorithme pour tracking
  top_factors: [
    {
      factor: "hrv_above_baseline",
      weight: 0.40,
      direction: "up",
      evidence: {
        current: 68.5,
        baseline: 59.6,
        delta_percent: 15
      }
    },
    {
      factor: "rhr_low",
      weight: 0.30,
      direction: "down",
      evidence: {
        current: 58,
        baseline: 62,
        delta: -4
      }
    }
  ],
  recommendation: "Profitez de cet état pour un entraînement intense"
}
```

**Interprétation visuelle :**
- **Score > 0.80** (80/100) : ✅ Badge vert "EXCELLENT" (bien récupéré)
- **Score 0.60-0.80** (60-80/100) : ⚠️ Badge orange "MOYEN"
- **Score < 0.60** (<60/100) : 🚨 Badge rouge "FAIBLE" (mal récupéré)

**Exemples :**
- `score = 0.92` → "92% • Excellente récupération"
- `score = 0.68` → "68% • Récupération moyenne"
- `score = 0.45` → "45% • Récupération faible"

##### Carte 4 : Sleep Debt (Dette de Sommeil)

**Source :** `daily_state` table, `state_type = 'sleep_debt'`

**Convention :** `score` élevé (proche de 1) = **MAUVAIS** (dette élevée)

**Données affichées :**
```javascript
{
  title: "Sleep Debt",
  score: 0.35,                    // 0-1 (1 = MAUVAIS, dette max)
  hours_accumulated: 4.5,         // Heures de dette accumulées (7 jours)
  top_factors: [
    {
      factor: "short_sleep_yesterday",
      evidence: {
        sleep_duration: 5.5,
        target: 8.0,
        deficit: 2.5
      }
    }
  ],
  trend: "improving",             // improving | worsening | stable
  recommendation: "Couchez-vous 1h plus tôt pendant 3 jours"
}
```

**Visualisation :**
- Graphique barres : Dette par jour (7 derniers jours)
- Couleur selon niveau de dette accumulée :
  - < 2h : Vert (score < 0.14)
  - 2-5h : Jaune (score 0.14-0.36)
  - 5-10h : Orange (score 0.36-0.71)
  - > 10h : Rouge (score > 0.71)

**Exemples d'interprétation :**
- `score = 0.05, hours = 0.7h` → "✅ Aucune dette"
- `score = 0.35, hours = 4.9h` → "⚠️ Dette modérée (5h)"
- `score = 0.75, hours = 10.5h` → "🚨 Dette importante (11h)"

**Note :** Plus le score est **élevé**, plus la situation est **mauvaise** (dette accumulée).

##### Carte 5 : Overtrain Risk (Risque Surcharge)

**Source :** `daily_state` table, `state_type = 'overtrain'`

**Convention :** `score` élevé (proche de 1) = **MAUVAIS** (risque élevé)

**Données affichées :**
```javascript
{
  title: "Overtrain Risk",
  score: 0.25,                    // 0-1 (1 = MAUVAIS, risque max)
  acwr: 1.35,                     // Acute:Chronic Workload Ratio
  acwr_zone: "optimal",           // low | optimal | elevated | high
  top_factors: [
    {
      factor: "acwr_elevated",
      evidence: {
        load_7d: 2700,
        load_28d: 2000,
        ratio: 1.35
      }
    },
    {
      factor: "hrv_declining",
      evidence: {
        hrv_3d_avg: 52.3,
        baseline: 59.6,
        delta_percent: -12
      }
    }
  ],
  recommendation: "Journée de récupération active recommandée"
}
```

**Zones ACWR :**
- **< 0.8** : Sous-charge (bleu)
- **0.8-1.3** : Optimal (vert)
- **1.3-1.5** : Élevé (orange)
- **> 1.5** : Très élevé (rouge)

**Exemples d'interprétation :**
- `score = 0.10, acwr = 1.05` → "✅ Risque faible (zone optimale)"
- `score = 0.45, acwr = 1.35` → "⚠️ Risque modéré (ACWR élevé)"
- `score = 0.75, acwr = 1.65` → "🚨 Risque critique (surcharge détectée)"

**Note :** Plus le score est **élevé**, plus le risque de surentraînement est **élevé**.

##### Carte 6 : Infection-Like Signature

**Source :** `daily_state` table, `state_type = 'infection_like'`

**Convention :** `score` élevé (proche de 1) = **MAUVAIS** (signes forts)

**Données affichées :**
```javascript
{
  title: "Infection-Like Signature",
  score: 0.15,                    // 0-1 (1 = MAUVAIS, signes forts)
  persistent_days: 0,             // Nombre de jours consécutifs
  signals_triggered: 1,           // Nombre de signaux actifs (sur 3)
  top_factors: [
    {
      factor: "rhr_elevated",
      evidence: {
        rhr_night: 65,
        baseline: 60,
        z_score: 1.2
      }
    }
  ],
  confidence: "low",              // low | medium | high
  recommendation: "Surveiller l'évolution. Si persistant 2+ jours, consulter médecin."
}
```

**Signaux surveillés :**
1. **RHR↑** : Rythme cardiaque repos élevé
2. **HRV↓** : Variabilité cardiaque basse
3. **Fragmentation↑** : Sommeil fragmenté

**Garde-fous anti-faux-positifs :**
- Nécessite ≥2 signaux activés
- Nécessite persistance ≥2 jours
- Pénalité si dette de sommeil >3h
- Pénalité si surcharge >0.7

**Exemples d'interprétation :**
- `score = 0.10, signals = 1, persistent = false` → "✅ Aucun signe (confiance faible)"
- `score = 0.45, signals = 2, persistent = false` → "⚠️ Signes modérés (surveillance)"
- `score = 0.75, signals = 3, persistent = true` → "🚨 Signes forts (consulter médecin)"

**Note :** Plus le score est **élevé**, plus les signes d'infection/fatigue immunitaire sont **forts**.

---

**⚠️ Mode Prudence (Disclaimer Médical Obligatoire) :**

Pour tout score `infection_like > 0.3`, la carte **DOIT** afficher un disclaimer en bas :

```
╔══════════════════════════════════════════╗
║  🦠 Infection-Like Signature             ║
║                                          ║
║  Score: 45% (modéré)                     ║
║  Persistance: Non                        ║
║  Signaux: 2/3 actifs                     ║
║                                          ║
║  • RHR élevé (+5 bpm)                    ║
║  • Sommeil fragmenté                     ║
║                                          ║
║  ┌────────────────────────────────────┐  ║
║  │ ⚠️ Important                       │  ║
║  │                                    │  ║
║  │ • Ceci n'est PAS un diagnostic     │  ║
║  │   médical                          │  ║
║  │                                    │  ║
║  │ • Pulse surveille des marqueurs    │  ║
║  │   physiologiques                   │  ║
║  │                                    │  ║
║  │ • Si symptômes importants          │  ║
║  │   (fièvre, douleurs, fatigue       │  ║
║  │   intense) → Consultez un          │  ║
║  │   professionnel de santé           │  ║
║  └────────────────────────────────────┘  ║
╚══════════════════════════════════════════╝
```

**Règles d'affichage :**
- **Score < 0.3** : Pas de disclaimer (aucun signe)
- **Score 0.3-0.6** : Disclaimer "surveillance recommandée"
- **Score > 0.6** : Disclaimer renforcé "consultation recommandée"

**Justification produit :**
- Réduit le risque médico-légal
- Évite la confusion "détection = diagnostic"
- Incite à la consultation médicale appropriée
- Conforme aux réglementations santé (CE Medical Device, FDA)

##### Carte 7+ : Insight IA Personnalisé

**Généré par :** GPT-4o avec contexte complet

**Données affichées :**
- Texte insight (200-300 chars)
- Anomalies référencées
- Recommandation actionnable
- Lien vers métriques concernées

---

**🔒 Sécurité Produit : Disclaimer Infection-Like**

⚠️ **Obligation légale** : Toute carte affichant `infection_like.score > 0.3` **DOIT** inclure le disclaimer médical.

✅ **ENFORCED CÔTÉ BACKEND** (depuis 2026-01-30)

Le disclaimer est **automatiquement injecté** dans le `content` de toute carte Brief mentionnant une signature infection-like si le score > 0.3.

**Le mobile n'a RIEN à faire**, il affiche simplement le `content` tel quel.

**Architecture :**
```
Backend (AIAnalysisService.generate_brief)
  ↓
  1. LLM génère cartes Brief
  2. _enforce_infection_disclaimer()  <-- Injection auto
     ├─ Récupère infection_like.score
     ├─ Si score > 0.3, cherche cartes keywords
     └─ Injecte disclaimer dans content
  3. Return cartes avec disclaimer
  ↓
Mobile (BriefCard.tsx)
  ↓
  Affiche content (disclaimer déjà présent)
```

**Texte standard injecté (non modifiable) :**

**Moderate (0.3-0.6) :**
```
---

⚠️ Important

• Ceci n'est PAS un diagnostic médical, mais une observation de patterns physiologiques.

• Si vous ressentez des symptômes importants ou persistants, consultez un professionnel de santé.
```

**High (>0.6) :**
```
---

⚠️ Important

• Ceci n'est PAS un diagnostic médical, mais une observation de patterns physiologiques.

• Si vous ressentez des symptômes importants ou persistants (fièvre, douleurs, fatigue intense), consultez IMMÉDIATEMENT un professionnel de santé.
```

**Voir :** `INFECTION_DISCLAIMER_ENFORCEMENT.md` pour détails implémentation.

Ce disclaimer est **non-négociable** pour des raisons médico-légales et réglementaires.

#### 2. Navigation BriefStack

**Composant :** `BriefNavigator` (dots sur le côté)

**Indicateurs :**
- Dots verticaux sur le côté droit (●○○○○)
- Icône spécifique par carte (Zap, TrendingUp, Activity, etc.)
- Position courante mise en évidence
- Transform dynamique pour centrage

**Gestures :**
- **Swipe down** : Carte suivante
- **Swipe up** : Carte précédente
- **Tap dot** : Navigation directe vers une carte
- **Haptic feedback** : Sur chaque changement de carte

**Animations :**
- FadeInDown pour apparition de cartes
- Perspective 3D + parallax pour l'effet de profondeur
- Spring animation fluide (react-native-reanimated)

---

## Tendances

**Route:** `app/(tabs)/tendances.tsx`  
**Rôle:** Visualisation historique des métriques avec graphiques

### Mockup Visuel

```
╔══════════════════════════════════════════╗
║  Tendances                               ║
║  Historique de vos métriques             ║
║                                          ║
║  ┌─────────┬─────────┐                   ║
║  │ Période │  Jour   │  ← Toggle        ║
║  └─────────┴─────────┘                   ║
║                                          ║
║  ┌────┬────┬────┐                        ║
║  │ 7J │ 30J│ 90J│  ← Sélecteur période  ║
║  └────┴────┴────┘                        ║
║                                          ║
║  ┌────────────────────────────────────┐  ║
║  │ 💚 HRV                        ↑    │  ║
║  │ ────────────────────────────────   │  ║
║  │                                    │  ║
║  │ Moyenne: 65 ms    Min/Max: 45/82  │  ║
║  │                                    │  ║
║  │     ╱╲    ╱╲                       │  ║
║  │    ╱  ╲  ╱  ╲    ╱╲                │  ║
║  │ ──╱────╲╱────╲──╱──╲────          │  ║
║  │                     ╲╱              │  ║
║  │                                    │  ║
║  │ 30 points • 30 derniers jours      │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  ┌────────────────────────────────────┐  ║
║  │ ❤️  Rythme Cardiaque          ─    │  ║
║  │ ────────────────────────────────   │  ║
║  │                                    │  ║
║  │ Moyenne: 68 bpm   Min/Max: 59/102 │  ║
║  │                                    │  ║
║  │ ─────────────────────────────────  │  ║
║  │                                    │  ║
║  │ 120 points • 30 derniers jours     │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  ┌────────────────────────────────────┐  ║
║  │ 😴 Sommeil                     ↓    │  ║
║  │ ────────────────────────────────   │  ║
║  │                                    │  ║
║  │ Moyenne: 7.2 h    Min/Max: 5.5/9.0│  ║
║  │                                    │  ║
║  │     ╱╲╲    ╱╲                      │  ║
║  │    ╱  ╲  ╱  ╲                      │  ║
║  │ ──╱────╲╱────╲──╱──╲────          │  ║
║  │                     ╲╱              │  ║
║  │                                    │  ║
║  │ 28 points • 30 derniers jours      │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
╚══════════════════════════════════════════╝
```

### Modes de Vue

#### Mode Période (Par défaut)

**Options :**
- **7 derniers jours** : Vue hebdomadaire
- **30 derniers jours** : Vue mensuelle
- **90 derniers jours** : Vue trimestrielle

**Statistiques affichées :**
- **Moyenne** : Moyenne arithmétique sur la période
- **Min / Max** : Valeurs minimale et maximale
- **Tendance** : ↑ Hausse / ↓ Baisse / ─ Stable
- **Nombre de points** : Total de mesures

**Calcul de tendance :**
```javascript
// Compare première moitié vs deuxième moitié
const midPoint = Math.floor(values.length / 2)
const firstHalf = values.slice(0, midPoint)
const secondHalf = values.slice(midPoint)

const firstAvg = mean(firstHalf)
const secondAvg = mean(secondHalf)

const diff = secondAvg - firstAvg
const threshold = firstAvg * 0.05  // 5%

if (diff > threshold) return 'up'
if (diff < -threshold) return 'down'
return 'stable'
```

#### Mode Jour

**Sélection :**
- DatePicker iOS natif
- Plage : Du premier enregistrement à aujourd'hui
- Format : "lundi 30 janvier 2026"

**Statistiques affichées :**
- **Mesures** : Nombre d'enregistrements dans la journée
- **Plage** : Min - Max du jour
- **Heures** : Timeline horaire si >10 mesures

### Métriques Disponibles (23 total)

#### 1. Activité (6 métriques)

| Métrique | Icône | Couleur | Unité | Formatter |
|----------|-------|---------|-------|-----------|
| Pas | 👣 | #00FF41 | pas | `toLocaleString()` |
| Distance | 🛣️ | #5856D6 | km | `.toFixed(1)` |
| Calories Totales | 🔥 | #FF3B30 | kcal | `Math.round()` |
| Calories Actives | 🔥 | #FF6B35 | kcal | `Math.round()` |
| Étages Montés | 📈 | #AF52DE | étages | `Math.round()` |
| VO2 Max | 💨 | #32ADE6 | mL/kg/min | `.toFixed(1)` |

#### 2. Vitals (6 métriques)

| Métrique | Icône | Couleur | Unité | Formatter |
|----------|-------|---------|-------|-----------|
| HRV | 💚 | #00FF41 | ms | `Math.round()` |
| Rythme Cardiaque | ❤️ | #FF9500 | bpm | `Math.round()` |
| Saturation O2 | 🫁 | #00C7BE | % | `Math.round()` |
| Pression Artérielle | ❤️ | #FF375F | mmHg | `Math.round()` |
| Glycémie | 💧 | #BF5AF2 | mg/dL | `Math.round()` |
| Fréquence Respiratoire | 🌬️ | #64D2FF | bpm | `Math.round()` |

#### 3. Body (4 métriques)

| Métrique | Icône | Couleur | Unité | Formatter |
|----------|-------|---------|-------|-----------|
| Poids | ⚖️ | #FF9F0A | kg | `.toFixed(1)` |
| Masse Grasse | ⚖️ | #FFD60A | % | `.toFixed(1)` |
| IMC | ⚖️ | #FFCC00 | kg/m² | `.toFixed(1)` |
| Température Corporelle | 🌡️ | #FF453A | °C | `.toFixed(1)` |

#### 4. Sleep (1 métrique)

| Métrique | Icône | Couleur | Unité | Formatter |
|----------|-------|---------|-------|-----------|
| Sommeil | 😴 | #0066FF | h | `(v / 3600).toFixed(1)` |

#### 5. Wellness (2 métriques)

| Métrique | Icône | Couleur | Unité | Formatter |
|----------|-------|---------|-------|-----------|
| Niveau de Stress | 🧠 | #FF2D55 | score | `Math.round()` |
| Méditation | 🧘 | #30D158 | min | `Math.round()` |

#### 6. Nutrition (3 métriques)

| Métrique | Icône | Couleur | Unité | Formatter |
|----------|-------|---------|-------|-----------|
| Hydratation | 💧 | #00C7BE | mL | `Math.round()` |
| Caféine | ☕ | #8B4513 | mg | `Math.round()` |
| Glucides | 🍞 | #FFD60A | g | `Math.round()` |

### Graphique (LifeLineChart)

**Fonctionnalités :**
- Ligne continue avec baseline (pointillés)
- Zone colorée (fill) sous la courbe
- Points de données interactifs
- Tooltip au tap (valeur + timestamp)
- Axe X : Temps (dates)
- Axe Y : Valeur (auto-scale)

**Baseline :**
- Ligne horizontale en pointillés
- Couleur gris clair (#8E8E93)
- Valeur = moyenne de la période

**Interactions :**
- **Tap point** : Affiche tooltip avec détails
- **Pinch zoom** : Zoom in/out (désactivé pour simplicité)
- **Scroll horizontal** : Navigation dans le temps (si >30 points)

---

## Journal Alimentaire

**Route:** `app/(tabs)/journal.tsx`  
**Rôle:** Suivi quotidien de l'alimentation avec recherche FatSecret

### Mockup Visuel

```
╔══════════════════════════════════════════╗
║  Journal                                 ║
║  lundi 30 janvier                        ║
║                                          ║
║  ┌────────────────────────────────────┐  ║
║  │ 📊 Résumé Nutrition                │  ║
║  │                                    │  ║
║  │  Calories: 1,850 / 2,200 kcal     │  ║
║  │  ━━━━━━━━━━━━━━━━━━━━━━━ 84%     │  ║
║  │                                    │  ║
║  │  🥩 Protéines: 95g   💪 43%        │  ║
║  │  🍞 Glucides:  185g  🏃 42%        │  ║
║  │  🥑 Lipides:   52g   🧈 25%        │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  🌅 Petit-déjeuner                       ║
║  ┌────────────────────────────────────┐  ║
║  │ 🥐 Croissant au beurre             │  ║
║  │    1 pièce • 240 kcal              │  ║
║  │    P: 5g  C: 26g  L: 12g           │  ║
║  │                                    │  ║
║  │ ☕ Café au lait                     │  ║
║  │    250ml • 85 kcal                 │  ║
║  │    P: 4g  C: 8g  L: 3g             │  ║
║  │ ───────────────────────────────    │  ║
║  │ [+] Ajouter un aliment             │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  🌞 Déjeuner                             ║
║  ┌────────────────────────────────────┐  ║
║  │ 🍗 Poulet grillé                   │  ║
║  │    150g • 248 kcal                 │  ║
║  │    P: 37g  C: 0g  L: 10g           │  ║
║  │                                    │  ║
║  │ 🥗 Salade verte                    │  ║
║  │    1 bol • 65 kcal                 │  ║
║  │    P: 3g  C: 10g  L: 2g            │  ║
║  │                                    │  ║
║  │ 🍚 Riz basmati                     │  ║
║  │    200g • 260 kcal                 │  ║
║  │    P: 5g  C: 56g  L: 1g            │  ║
║  │ ───────────────────────────────    │  ║
║  │ [+] Ajouter un aliment             │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  🌙 Dîner                                ║
║  ┌────────────────────────────────────┐  ║
║  │ [+] Ajouter un aliment             │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  🍿 Collations                           ║
║  ┌────────────────────────────────────┐  ║
║  │ [+] Ajouter un aliment             │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
╚══════════════════════════════════════════╝
```

### Données Affichées

#### 1. Résumé Nutrition (NutritionSummary)

**Calcul :**
```javascript
// Agrégation de tous les food_logs du jour
// Les totaux sont calculés automatiquement via trigger SQL
const foodLogs = await supabase
  .from('food_logs')
  .select('*')
  .eq('user_id', userId)
  .gte('logged_at', startOfDay)
  .lte('logged_at', endOfDay)

total_nutrition = {
  calories: sum(foodLogs.map(log => log.total_calories)),
  protein: sum(foodLogs.map(log => log.total_protein)),
  carbs: sum(foodLogs.map(log => log.total_carbs)),
  fat: sum(foodLogs.map(log => log.total_fat))
}

// Pourcentages macros (calculés depuis calories)
protein_percent = (protein_g * 4) / total_calories * 100
carbs_percent = (carbs_g * 4) / total_calories * 100
fat_percent = (fat_g * 9) / total_calories * 100
```

**Affichage :**
- **Calories** : Valeur / Objectif avec barre de progression
- **Macros** : Protéines, Glucides, Lipides en grammes + %
- **Couleur barre** :
  - < 80% objectif : Rouge
  - 80-110% : Vert
  - > 110% : Orange

#### 2. Sections Repas (MealCard)

**Types de repas :**
1. **🌅 Petit-déjeuner** (`breakfast`)
2. **🌞 Déjeuner** (`lunch`)
3. **🌙 Dîner** (`dinner`)
4. **🍿 Collations** (`snack`)

**Architecture Extensible (Nouveau modèle) :**
```typescript
// Un repas (food_log) peut contenir plusieurs items + photos
interface FoodLog {
  id: string
  user_id: string
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  logged_at: Date
  total_calories: number      // Calculé automatiquement via trigger
  total_protein: number       // Calculé automatiquement via trigger
  total_carbs: number         // Calculé automatiquement via trigger
  total_fat: number           // Calculé automatiquement via trigger
  notes?: string
  items: FoodLogItem[]        // Relation 1-N
  photos: FoodPhoto[]         // Relation 1-N (support futur)
}

// Items individuels d'un repas
interface FoodLogItem {
  id: string
  food_log_id: string
  food_name: string           // "Croissant au beurre"
  serving_size: number        // 1
  serving_unit: string        // "pièce"
  calories: number            // 240
  protein: number             // 5
  carbs: number               // 26
  fat: number                 // 12
  fiber?: number              // 2 (optionnel)
  sugar?: number              // 8 (optionnel)
  sodium?: number             // 180 (optionnel)
  fatsecret_id?: string
  created_at: Date
}

// Photos de repas (support futur pour OCR/Vision)
interface FoodPhoto {
  id: string
  food_log_id: string
  photo_url: string
  analysis_result?: any       // OCR/Vision futur
  uploaded_at: Date
}
```

**Avantages de cette architecture :**
- Support des repas multi-items (ex: "Déjeuner complet" avec entrée+plat+dessert)
- Support des photos de repas
- Modification/suppression par repas entier ou item individuel
- Calcul automatique des totaux via triggers SQL

**Affichage par aliment :**
```
🥐 Croissant au beurre
   1 pièce • 240 kcal
   P: 5g  C: 26g  L: 12g
```

#### 3. Bouton Ajouter

**Interaction :**
```javascript
// Navigation vers search-food avec param
router.push({
  pathname: '/(tabs)/search-food',
  params: { mealType: 'breakfast' }
})
```

### Écran Recherche (search-food.tsx)

**Mockup :**
```
╔══════════════════════════════════════════╗
║  ← Ajouter • Petit-déjeuner              ║
║                                          ║
║  ┌────────────────────────────────────┐  ║
║  │ 🔍 Rechercher un aliment...        │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  Résultats (FatSecret API)               ║
║  ┌────────────────────────────────────┐  ║
║  │ Croissant au beurre                │  ║
║  │ 240 kcal • P: 5g C: 26g L: 12g     │  ║
║  │                            [+]      │  ║
║  └────────────────────────────────────┘  ║
║  ┌────────────────────────────────────┐  ║
║  │ Croissant aux amandes              │  ║
║  │ 280 kcal • P: 6g C: 28g L: 15g     │  ║
║  │                            [+]      │  ║
║  └────────────────────────────────────┘  ║
║  ┌────────────────────────────────────┐  ║
║  │ Croissant complet                  │  ║
║  │ 220 kcal • P: 6g C: 24g L: 10g     │  ║
║  │                            [+]      │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
╚══════════════════════════════════════════╝
```

**Flow :**
1. User tape recherche (ex: "croissant")
2. Debounce 500ms
3. `GET` FatSecret API `/foods/search.v2`
4. Affichage résultats
5. User tap [+] → Navigation vers `food-details`

### Écran Détails (food-details.tsx)

**Mockup :**
```
╔══════════════════════════════════════════╗
║  ← Croissant au beurre                   ║
║                                          ║
║  📊 Informations nutritionnelles         ║
║  ┌────────────────────────────────────┐  ║
║  │ Pour 100g:                         │  ║
║  │                                    │  ║
║  │ Calories:     406 kcal             │  ║
║  │ Protéines:    8.2g                 │  ║
║  │ Glucides:     45.8g                │  ║
║  │  - Sucres:    8.0g                 │  ║
║  │  - Fibres:    2.6g                 │  ║
║  │ Lipides:      21.0g                │  ║
║  │ Sodium:       470mg                │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  🥐 Portion                              ║
║  ┌────────────────────────────────────┐  ║
║  │ Taille:   [  1  ]                  │  ║
║  │ Unité:    [ pièce ▼ ]              │  ║
║  │                                    │  ║
║  │ Options: 1 pièce (60g)             │  ║
║  │          100g                      │  ║
║  │          1 croissant moyen (70g)   │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  🕒 Heure                                ║
║  ┌────────────────────────────────────┐  ║
║  │ [ 08:30 ]                          │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  [ Annuler ]    [ Ajouter au journal ] ║
║                                          ║
╚══════════════════════════════════════════╝
```

**Validation :**
```javascript
// Calcul nutrition finale
const finalNutrition = {
  calories: base_per_100g.calories * (portion_g / 100),
  protein: base_per_100g.protein * (portion_g / 100),
  carbs: base_per_100g.carbs * (portion_g / 100),
  fat: base_per_100g.fat * (portion_g / 100),
  fiber: base_per_100g.fiber * (portion_g / 100),
  sugar: base_per_100g.sugar * (portion_g / 100),
  sodium: base_per_100g.sodium * (portion_g / 100)
}

// 1. Créer ou récupérer le food_log pour ce repas
const { data: foodLog, error: logError } = await supabase
  .from('food_logs')
  .insert({
    user_id: userId,
    meal_type: mealType,
    logged_at: selectedTime,
    notes: null
  })
  .select()
  .single()

// 2. Insérer l'item (le trigger mettra à jour automatiquement les totaux)
const { data: item, error: itemError } = await supabase
  .from('food_log_items')
  .insert({
    food_log_id: foodLog.id,
    food_name: foodName,
    serving_size: servingSize,
    serving_unit: servingUnit,
    calories: finalNutrition.calories,
    protein: finalNutrition.protein,
    carbs: finalNutrition.carbs,
    fat: finalNutrition.fat,
    fiber: finalNutrition.fiber,
    sugar: finalNutrition.sugar,
    sodium: finalNutrition.sodium,
    fatsecret_id: fatsecretId
  })

// Les totaux du food_log sont calculés automatiquement via trigger SQL
```

**Avantages :**
- Groupement automatique des items par repas
- Support ajout multiple d'items au même repas
- Calcul automatique des totaux (pas d'erreur de somme)
- Suppression en cascade si le repas est supprimé

---

## Profil

**Route:** `app/(tabs)/profil.tsx`  
**Rôle:** Paramètres utilisateur et gestion santé

### Mockup Visuel

> 🆕 **Note v3.0:** Le design de la page Profil a été modernisé avec une hiérarchie visuelle améliorée, des espacements optimisés, et une cohérence des styles. L'objectif santé a été supprimé pour simplifier l'interface.

```
╔══════════════════════════════════════════╗
║  Profil                                  ║
║                                          ║
║  👤 Informations                         ║
║  ┌────────────────────────────────────┐  ║
║  │ Nom:    Dan Nezri                  │  ║
║  │ 📧 Email: Utilisateur connecté      │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  ⌚ Wearable                              ║
║  ┌────────────────────────────────────┐  ║
║  │ ✅ Connecté                         │  ║
║  │    Vos données sont synchronisées  │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  ❤️  Conditions de santé (Facultatif)   ║
║  💡 Renseignez vos conditions pour des  ║
║     conseils personnalisés et précis.   ║
║                                          ║
║  2 conditions renseignées                ║
║  ┌──────────────┐ ┌──────────────┐      ║
║  │ • Diabète    │ │ • Hypertension│     ║
║  │   Type 1  [×]│ │   artérielle[×]│    ║
║  └──────────────┘ └──────────────┘      ║
║                                          ║
║  [+] Renseigner mes conditions           ║
║                                          ║
║  📊 Journal d'Activités                  ║
║  Suivez votre consommation de caféine,  ║
║  d'alcool, vos repas et séances sport.  ║
║  [ Enregistrer un événement ]            ║
║                                          ║
║  💊 Médicaments                          ║
║  ┌──────────┬──────────┐                 ║
║  │    2     │     5    │                 ║
║  │Aujourd'hui│  Total   │                 ║
║  └──────────┴──────────┘                 ║
║  [+] Ajouter un médicament               ║
║                                          ║
║  ┌────────────────────────────────────┐  ║
║  │ 💊 Metformine 500mg                │  ║
║  │    2x/jour                         │  ║
║  │    Pris il y a 3h                  │  ║
║  │                            [Swipe]│  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  📈 Normalisation Personnelle            ║
║  Vos métriques de référence calculées   ║
║  automatiquement à partir de vos données║
║                                          ║
║  ┌────────────────────────────────────┐  ║
║  │ HRV                                │  ║
║  │ 65.2 ms ± 8.5                      │  ║
║  │ 📊 60 points • HIGH                │  ║
║  └────────────────────────────────────┘  ║
║  ┌────────────────────────────────────┐  ║
║  │ Rythme Cardiaque Repos             │  ║
║  │ 62 bpm ± 5                         │  ║
║  │ 📊 58 points • HIGH                │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  [ 🔄 Recalculer manuellement ]          ║
║  Note: Recalcul automatique chaque nuit  ║
║                                          ║
║  [ 🚪 Déconnexion ]                      ║
║                                          ║
╚══════════════════════════════════════════╝
```

### Sections Détaillées

#### 1. Informations Utilisateur

**Source :** `profiles` + `auth.users`

```typescript
interface UserProfile {
  id: string                    // UUID
  full_name: string             // "Dan Nezri"
  email: string                 // De auth.users
  created_at: Date
}
```

**Affichage :**
- Nom complet
- Email (masqué ou "Utilisateur connecté")
- Icônes : 👤 User, 📧 Mail

#### 2. Statut Wearable

**Détection :**
```javascript
const isConnected = !!profile.open_wearables_user_id

if (isConnected) {
  status = {
    icon: '✅',
    color: '#34C759',
    text: 'Connecté',
    subtext: 'Vos données sont synchronisées'
  }
} else {
  status = {
    icon: '⚪',
    color: '#8E8E93',
    text: 'Non connecté',
    subtext: 'Connectez un wearable pour commencer'
  }
}
```

#### 3. Conditions de Santé (ICD-11)

**Structure :**
```typescript
interface UserCondition {
  id: string
  user_id: string
  icd_code: string              // "5A10" (Diabète Type 1)
  display: string               // "Diabète sucré de type 1"
  category: string              // "Endocrine diseases"
  added_at: Date
}
```

**Affichage chips :**
- Couleurs alternées (orange, violet, vert)
- Dot coloré devant
- Bouton [×] pour supprimer
- Max 2 lignes de texte avec ellipsis

**Interaction :**
- Tap [+] → Modal `ConditionPicker`
- Tap [×] → Confirmation puis suppression

#### 4. Journal d'Activités

**Types trackables :**

```typescript
type EventType = 'caffeine' | 'alcohol' | 'sport' | 'meal'

interface UserEvent {
  id: string
  user_id: string
  event_type: EventType
  event_data: {
    // Pour caffeine
    amount_mg?: number
    source?: string
    
    // Pour alcohol
    units?: number
    type?: string
    
    // Pour sport
    activity_type?: string
    duration_minutes?: number
    intensity?: 'low' | 'medium' | 'high'
    
    // Pour meal
    description?: string
    photo_url?: string
  }
  logged_at: Date
}
```

**Modal EventTracker :**
```
╔══════════════════════════════════════════╗
║  Enregistrer un événement                ║
║                                          ║
║  ┌──────┬──────┬──────┬──────┐           ║
║  │  ☕  │  🍷  │  🏃  │  🍽️  │           ║
║  │Caféine│Alcool│Sport │Repas│           ║
║  └──────┴──────┴──────┴──────┘           ║
║                                          ║
║  [Formulaire selon type sélectionné]     ║
║                                          ║
║  [ Annuler ]          [ Enregistrer ]    ║
╚══════════════════════════════════════════╝
```

#### 5. Médicaments

**Stats :**
```javascript
function getTodayMedications(medications) {
  const today = startOfDay(new Date())
  return medications.filter(med => 
    med.taken_at >= today && med.taken_at < endOfDay(today)
  )
}

const todayCount = getTodayMedications(medications).length
const totalCount = medications.length
```

**Liste :**
- Affichage des 5 derniers
- Swipe left pour supprimer
- Format :
  ```
  💊 Metformine 500mg
     2x/jour
     Pris il y a 3h
  ```

**Modal MedicationForm :**
```
╔══════════════════════════════════════════╗
║  Ajouter un médicament                   ║
║                                          ║
║  Nom du médicament *                     ║
║  ┌────────────────────────────────────┐  ║
║  │ Metformine                         │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  Dosage *                                ║
║  ┌────────────────────────────────────┐  ║
║  │ 500mg                              │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  Fréquence *                             ║
║  ┌────────────────────────────────────┐  ║
║  │ 2x/jour                            │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  Heure de prise                          ║
║  ┌────────────────────────────────────┐  ║
║  │ [ 08:00 ]                          │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  Notes (optionnel)                       ║
║  ┌────────────────────────────────────┐  ║
║  │ Avec repas                         │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  [ Annuler ]             [ Ajouter ]     ║
╚══════════════════════════════════════════╝
```

#### 6. Normalisation Personnelle (Baselines Robustes)

**Baselines calculées (Statistiques Robustes) :**

```typescript
interface RobustBaseline {
  id: string
  user_id: string
  baseline_type: string         // 'hrv', 'heart_rate', etc.
  median: number                // Médiane (robuste)
  iqr: number                   // Interquartile Range (Q3 - Q1)
  p25: number                   // 25e percentile
  p75: number                   // 75e percentile
  sample_count: number          // Nombre de points
  confidence: 'low' | 'medium' | 'high'
  model_version: string         // 'baseline_v2_robust' ou 'baseline_v2_robust_migrated'
  calculated_at: Date
  last_updated: Date
}
```

**Affichage carte :**
```
┌────────────────────────────────────┐
│ HRV                                │
│ Médiane: 65.2 ms (IQR: 8.5)       │
│ Plage: 56.7 - 73.7 ms             │
│ 📊 60 points • HIGH • v2_robust   │
└────────────────────────────────────┘
```

**Pourquoi des statistiques robustes ?**
- Plus résistantes aux valeurs extrêmes et outliers
- Représentation plus fidèle des valeurs "typiques"
- Cohérence avec les calculs d'anomalies et états latents

**Badge confiance :**
- **HIGH** : ≥60 points (vert)
- **MEDIUM** : 30-59 points (orange)
- **LOW** : 10-29 points (gris)

**Recalcul manuel :**
```javascript
async function triggerRecalculation() {
  const response = await fetch('/api/baselines/calculate', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ user_id: userId })
  })
  
  if (response.ok) {
    // Invalider cache baselines
    queryClient.invalidateQueries(['baselines', userId])
    Alert.alert('Succès', 'Les baselines ont été recalculées.')
  }
}
```

**Note :**
- Recalcul automatique chaque nuit à 3h UTC via cron
- Le recalcul manuel est disponible pour les utilisateurs impatients

---

## Écrans Secondaires

### 1. Login (login.tsx)

**Mockup :**
```
╔══════════════════════════════════════════╗
║                                          ║
║            ⚫️  Pulse                     ║
║                                          ║
║     Bio-Feedback IA en Temps Réel        ║
║                                          ║
║                                          ║
║  Email                                   ║
║  ┌────────────────────────────────────┐  ║
║  │ dan@example.com                    │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  Mot de passe                            ║
║  ┌────────────────────────────────────┐  ║
║  │ ••••••••••                         │  ║
║  └────────────────────────────────────┘  ║
║                                          ║
║  [ Se connecter ]                        ║
║                                          ║
║  Pas encore de compte ? S'inscrire       ║
║                                          ║
╚══════════════════════════════════════════╝
```

### 2. Details (details.tsx)

**Rôle :** Page détails des anomalies (accès via pinch sur Orb)

**Données :**
- Liste complète des anomalies (pas que top 3)
- Graphiques détaillés par métrique
- Historique des anomalies (7 derniers jours)
- Recommandations IA étendues

### 3. Event Detail (event-detail.tsx)

**Rôle :** Détails d'un événement d'agenda

**Données :**
- Titre complet
- Date/heure début et fin
- Lieu (avec lien Maps si dispo)
- Notes de l'événement
- Participants (si accessible)
- Biométrie prévue :
  - État recommandé (calm/warning/alert)
  - Readiness prévu
  - Conseils pré-événement

---

## Résumé des Données par Écran

| Écran | Route | Données Sources | Fréquence Mise à Jour |
|-------|-------|-----------------|----------------------|
| **Brief (Accueil)** | `index.tsx` | `daily_state` (avec `model_version`), `biometrics`, `user_baselines` (robustes), Cache 1h | Pull-to-refresh |
| **Tendances** | `tendances.tsx` | `biometrics` | Pull-to-refresh |
| **Journal** | `journal.tsx` | `food_logs` + `food_log_items` + `food_photos`, FatSecret API (provider) | Pull-to-refresh + sync API |
| **Profil** | `profil.tsx` | `profiles`, `user_baselines` (robustes avec `model_version`), `user_conditions`, `medications`, `user_events` | Au chargement + actions |

**Notes Importantes :**

**Convention des Scores `daily_state` :**
- **Recovery** : `score = 1` = BON (bien récupéré)
- **Sleep Debt, Overtrain, Infection** : `score = 1` = MAUVAIS (dette/risque/signes élevés)
- Dans les agrégateurs (Energy Overview), les scores "mauvais" sont inversés en `_good`

**Baselines Robustes :**
- Toutes les baselines utilisent des **statistiques robustes** (median/IQR/p25/p75)
- Le champ `model_version` permet de tracker les versions d'algorithmes
- Migration progressive depuis anciennes baselines (mean/std) vers robustes

---

## Animations et Transitions

### Animations Principales

1. **Orb Organique**
   - Bibliothèque : `react-native-reanimated`
   - Type : Spring animation avec pulsation
   - Timing : 0.8s à 2s selon état

2. **BriefStack**
   - Bibliothèque : `react-native-gesture-handler` + `reanimated`
   - Type : Stack avec swipe gestures
   - Effet : Perspective 3D + parallax

3. **FadeInView**
   - Type : Fade + spring
   - Séquentiel : Delay entre éléments (0ms, 150ms, 300ms, 450ms)
   - Usage : Toutes les cartes du Dashboard

4. **BottomDrawer**
   - Type : Slide from bottom + glassmorphism
   - Bibliothèque : `@gorhom/bottom-sheet`
   - Backdrop blur : iOS native

### Micro-interactions

- **Haptic Feedback** : `expo-haptics`
  - Tap bouton : Light impact
  - Refresh : Medium impact
  - Erreur : Notification error
  - Succès : Notification success

- **Loading States** : Skeleton screens
- **Empty States** : Illustrations + messages contextuels
- **Error States** : Messages + bouton retry

---

## Notes de Version 3.0.0

### 🆕 Nouveautés Architecture

**Baselines Robustes :**
- Les baselines affichées dans le Profil utilisent désormais median/IQR/p25/p75
- Affichage de la plage (p25-p75) au lieu de mean±std
- Badge `model_version` pour tracking des algorithmes

**Journal Alimentaire Extensible :**
- Support des repas multi-items (plusieurs aliments par repas)
- Architecture préparée pour photos de repas (futur OCR/Vision)
- Calcul automatique des totaux via triggers SQL

**Détection Anomalies Robuste :**
- Z-score robuste (IQR) au lieu de classique (std)
- Plus résistant aux outliers et valeurs extrêmes
- Cohérence avec les calculs d'états latents

**Validation des Données :**
- Nouveaux helpers `hasValidBaselines()`, `hasValidData()`
- Dégradation gracieuse si données insuffisantes
- Messages d'erreur contextuels pour l'utilisateur

**Navigation Simplifiée :**
- Suppression de l'ancienne page Dashboard (avec Orb organique)
- Brief quotidien devient la seule page d'accueil (`index.tsx`)
- Navigation directe : Brief → Tendances → Journal → Profil
- Moins de friction, expérience plus fluide

### 📱 Impact UX

**Brief (Nouvelle Page d'Accueil) :**
- Expérience d'ouverture d'app plus directe et immédiate
- Cartes d'état avec `model_version` visible
- Baselines affichées en mode robuste
- Confiance calculée avec statistiques robustes
- Plus de focus sur les insights quotidiens

**Tendances :**
- Détection d'anomalies plus stable avec Z-score robuste
- Moins de faux positifs dans les graphiques
- Visualisation cohérente avec les autres écrans

**Journal :**
- Possibilité d'ajouter plusieurs items au même repas
- Suppression plus intuitive (par repas ou par item)
- Préparation pour scan photo de repas

**Profil (Design Modernisé) :**
- Baselines affichent plage (p25-p75) au lieu de ±std
- Version d'algorithme visible (`baseline_v2_robust`)
- Badge de confiance plus précis
- Suppression de l'objectif santé pour simplifier l'interface
- Hiérarchie visuelle améliorée avec espacements optimisés
- Typographie plus claire et cohérente
- Boutons et cartes avec styles uniformisés
- Shadows subtiles pour ajouter de la profondeur
- États vides plus engageants avec bordures en pointillés

**Sécurité Produit (Mode Prudence Infection-Like) :**
- Disclaimer médical obligatoire pour `infection_like > 0.3`
- Texte standard non-modifiable affiché dans la carte
- "Ceci n'est PAS un diagnostic médical"
- "Si symptômes importants → consulter médecin"
- Conformité réglementaire (CE Medical Device, FDA)
- Réduction du risque médico-légal

**Risk Windows Personnalisés (Creux d'Énergie) :**
- Prédiction adaptée au chronotype utilisateur (morning/evening)
- Ajustement selon dette de sommeil (élevée → creux plus tôt)
- Ajustement selon énergie globale (basse → creux plus tôt)
- Calcul sans ML : utilise baselines existantes (mid_sleep)
- Pertinence biologique pour planification quotidienne
- Exemples concrets affichés dans la carte Energy Overview

---

*Document mis à jour le 30 janvier 2026*  
*Guide complet des écrans mobiles Pulse*  
*Version 3.0.0 (Architecture Robuste)*
