# 📊 Extraction des Données de la Page Énergie

## Vue d'ensemble

Ce script permet d'extraire **toutes les données** affichées dans la page **Analyse Énergétique** de l'application Pulse Mobile pour un utilisateur donné.

## Prérequis

- Node.js >= 20.19.4
- Backend Pulse en cours d'exécution (`http://localhost:9000`)
- Package `node-fetch` installé

## Installation

```bash
cd /Users/dannezri/Desktop/Pulse/mobile
npm install node-fetch
```

## Usage

### 1. Extraction pour l'utilisateur par défaut

```bash
node extract-energy-data.js
```

Par défaut, utilise l'utilisateur ID: `c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd`

### 2. Extraction pour un utilisateur spécifique

```bash
node extract-energy-data.js <USER_ID>
```

Exemple:
```bash
node extract-energy-data.js 12345678-1234-1234-1234-123456789abc
```

### 3. Forcer un recalcul (ignorer le cache)

```bash
node extract-energy-data.js --force
```

Ou avec un userId spécifique:
```bash
node extract-energy-data.js <USER_ID> --force
```

### 4. Utiliser une URL d'API différente

```bash
API_URL=http://192.168.0.23:9000 node extract-energy-data.js
```

## Données Extraites

Le script extrait et affiche les données suivantes :

### 📋 Métadonnées
- User ID
- Date d'analyse
- Statut du cache
- Pulse Score global

### ⚡ Forecast d'Énergie
- Type de modèle (ex: `forecast_v2`)
- Version du modèle (ex: `2.0`)
- Date de génération
- Timezone
- Confiance du modèle

### 🎯 Énergie Actuelle
- Score d'énergie (0-100%)
- État visuel (🔴/🟠/🟡/🟢)
- Label descriptif ("Énergie basse", "Bonne énergie", etc.)

### 📈 Courbe Prédictive
- Tous les points de prédiction (timestamp + valeur)
- Plage horaire couverte
- Nombre total de points

### 📊 Statistiques
- Énergie minimale
- Énergie maximale
- Énergie moyenne
- Plage horaire (début → fin)

### ⚖️ Balance Énergétique
- Nombre de facteurs positifs
- Nombre de facteurs négatifs
- Impact total positif (%)
- Impact total négatif (%)
- Balance nette (%)

### ✅ Facteurs Positifs (Influencers)
Pour chaque facteur positif :
- Nom (ex: "Sommeil de qualité")
- Type (`oura`, `medication`, `condition`)
- Code (ATC pour médicaments, ICD-11 pour conditions)
- Impact (ex: "+15%")

### ❌ Facteurs Négatifs (Influencers)
Pour chaque facteur négatif :
- Nom (ex: "Mirtazapine 15mg")
- Type (`medication`, `condition`, etc.)
- Code (ATC ou ICD-11)
- Impact (ex: "-23.75%")

### 📝 Notes Explicatives
- Liste des explications textuelles générées par le système
- Contexte sur les facteurs dominants
- Recommandations

### 🕐 Fenêtres Temporelles
- Périodes définies (ex: "Matin", "Après-midi", "Soirée")
- Heures de début et fin pour chaque fenêtre

### 📅 Événements Prédits
Pour chaque événement :
- Titre
- Heure de début
- Heure de fin
- Impact sur l'énergie (%)
- Confiance de la prédiction (%)
- Tags associés

### 🔍 Diagnostic
- Détection automatique des problèmes :
  - Influencers manquants (CRITIQUE)
  - Courbe prédictive vide
  - Notes manquantes
  - Confiance faible
  - Plage horaire non définie

## Sortie

### 1. Affichage Console

Le script affiche un rapport détaillé formaté dans la console :

```
┌─────────────────────────────────────────────────┐
│  📊 EXTRACTION DONNÉES PAGE ÉNERGIE - PULSE    │
└─────────────────────────────────────────────────┘

🆔 User ID: c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd
🌐 API URL: http://localhost:9000
🔄 Force Refresh: NON

📡 Appel de l'API /api/v1/generate-brief...
✅ Données reçues avec succès!

═══════════════════════════════════════════════════
  📊 DONNÉES COMPLÈTES PAGE ÉNERGIE
═══════════════════════════════════════════════════

📋 MÉTADONNÉES
──────────────────────────────────────────────────
User ID         : c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd
Analysé le      : 2026-02-01T20:25:42.123Z
Depuis cache    : OUI
Pulse Score     : 38%

⚡ FORECAST D'ÉNERGIE
──────────────────────────────────────────────────
Type            : forecast_v2
Version modèle  : 2.0
Généré le       : 2026-02-01T20:25:40.000Z
Date forecast   : 2026-02-01
Timezone        : Europe/Paris
Confiance       : 50.4%

🎯 ÉNERGIE ACTUELLE
──────────────────────────────────────────────────
Score           : 27%
État            : 🟠
Label           : Énergie basse

📈 COURBE PRÉDICTIVE
──────────────────────────────────────────────────
Points totaux   : 8
Plage horaire   : 20:00 → 23:30

Premiers points:
  20:00 : 27%
  20:30 : 27%
  21:00 : 24%
  21:30 : 24%
  22:00 : 24%

⚖️  BALANCE ÉNERGÉTIQUE
──────────────────────────────────────────────────
Facteurs +      : 2 (total: +25.0%)
Facteurs -      : 6 (total: -77.5%)
Balance nette   : -52.5%

✅ FACTEURS POSITIFS
──────────────────────────────────────────────────
  Sommeil de qualité
    Type   : oura
    Code   : sleep_score
    Impact : +15%

  Aucune dette de sommeil
    Type   : oura
    Code   : sleep_debt
    Impact : +10%

❌ FACTEURS NÉGATIFS
──────────────────────────────────────────────────
  Mirtazapine 15mg
    Type   : medication
    Code   : N06AX11
    Impact : -23.75%

  Sertraline 50mg
    Type   : medication
    Code   : N06AB06
    Impact : -14.25%

  ... (autres facteurs)

📝 NOTES EXPLICATIVES
──────────────────────────────────────────────────
  1. Ton énergie de base est faible aujourd'hui
  2. Ta récupération est faible, ménage-toi

🔍 DIAGNOSTIC
──────────────────────────────────────────────────
Problèmes détectés:
  ❌ CRITIQUE: Aucun influenceur détecté (tableau vide)
  ⚠️  Confiance faible (50.4%)

═══════════════════════════════════════════════════

💾 Données sauvegardées dans: energy-data-c559fcd7-...-2026-02-01.json
✅ Extraction terminée avec succès
```

### 2. Fichier JSON

Le script génère automatiquement un fichier JSON avec toutes les données :

**Nom du fichier:** `energy-data-<USER_ID>-<DATE>.json`

**Exemple:** `energy-data-c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd-2026-02-01.json`

**Structure:**

```json
{
  "metadata": {
    "user_id": "c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd",
    "analyzed_at": "2026-02-01T20:25:42.123Z",
    "cached": true,
    "pulse_score": 38
  },
  "energy_forecast": {
    "type": "forecast_v2",
    "model_version": "2.0",
    "generated_at": "2026-02-01T20:25:40.000Z",
    "forecast_date": "2026-02-01",
    "timezone": "Europe/Paris",
    "confidence": 0.504,
    "current_energy": 27,
    "forecast_curve": [
      { "t": "2026-02-01T20:00:00Z", "energy": 27 },
      { "t": "2026-02-01T20:30:00Z", "energy": 27 },
      { "t": "2026-02-01T21:00:00Z", "energy": 24 }
    ],
    "total_points": 8,
    "windows": [],
    "events": [],
    "influencers": [],
    "positive_influencers": [],
    "negative_influencers": [],
    "notes": [
      "Ton énergie de base est faible aujourd'hui",
      "Ta récupération est faible, ménage-toi"
    ]
  },
  "statistics": {
    "total_positive_impact": 25.0,
    "total_negative_impact": 77.5,
    "net_balance": -52.5,
    "positive_factors_count": 2,
    "negative_factors_count": 6,
    "min_energy": 24,
    "max_energy": 27,
    "avg_energy": 25.125,
    "time_range": {
      "start": "2026-02-01T20:00:00Z",
      "end": "2026-02-01T23:30:00Z"
    }
  },
  "brief_cards": [...]
}
```

## Cas d'Usage

### 1. Debugging

Vérifier rapidement pourquoi la page énergie affiche certaines données :

```bash
node extract-energy-data.js
```

### 2. Analyse de Données

Extraire les données pour analyse externe (Excel, Python, etc.) :

```bash
node extract-energy-data.js > output.txt
```

### 3. Comparaison Avant/Après

Comparer les données avant et après un changement backend :

```bash
# Avant
node extract-energy-data.js > before.json

# Après modification backend
node extract-energy-data.js --force > after.json

# Comparer
diff before.json after.json
```

### 4. Vérification ML

Vérifier que les poids ML personnalisés sont bien appliqués :

```bash
node extract-energy-data.js | grep -A 10 "FACTEURS NÉGATIFS"
```

### 5. Export pour Support

Générer un rapport complet pour le support technique :

```bash
node extract-energy-data.js <USER_ID> > rapport-user-$(date +%Y%m%d).txt
```

## Problèmes Courants

### Erreur: `Cannot find module 'node-fetch'`

**Solution:**
```bash
npm install node-fetch
```

### Erreur: `API Error 500`

**Causes possibles:**
- Backend non démarré
- User ID invalide
- Données manquantes dans la base

**Solution:**
```bash
# Vérifier que le backend tourne
curl http://localhost:9000/health

# Vérifier l'utilisateur existe
psql -d pulse -c "SELECT id FROM users WHERE id = '<USER_ID>';"
```

### Erreur: `ECONNREFUSED`

**Cause:** Backend non accessible

**Solution:**
```bash
# Démarrer le backend
cd /Users/dannezri/Desktop/Pulse/backend
python api_server.py
```

### Données vides ou incomplètes

**Cause:** Cache périmé ou données non générées

**Solution:**
```bash
# Forcer un recalcul
node extract-energy-data.js --force
```

## Intégration avec le Backend

Le script appelle l'endpoint suivant :

```
POST http://localhost:9000/api/v1/generate-brief
Content-Type: application/json

{
  "user_id": "c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd",
  "force_refresh": false
}
```

Cet endpoint retourne toutes les données nécessaires à la page Énergie, incluant :
- Pulse Score global
- Cartes Brief (contexte)
- **Forecast d'énergie intrajournalier** (`intraday_energy_forecast`)

## Fichiers Liés

### Mobile
- `mobile/app/energy-analysis.tsx` - Page UI
- `mobile/src/hooks/useBriefData.ts` - Hook de récupération
- `mobile/src/services/briefApi.ts` - Appels API
- `mobile/src/types/brief.ts` - Types TypeScript

### Backend
- `backend/api_server.py` - Endpoint `/api/v1/generate-brief`
- `backend/services/ai_service.py` - Génération du forecast
- `backend/ml_optimizer.py` - Poids ML personnalisés

### Documentation
- `ANALYSE_PAGE_ENERGIE.md` - Architecture complète
- `ANALYSE_RESULTATS_ENERGIE_USER.md` - Analyse détaillée des données
- `CALCUL_ENERGIE_DETAILLE_USER.md` - Formules de calcul

## Améliorations Futures

- [ ] Support de l'export en CSV
- [ ] Comparaison multi-utilisateurs
- [ ] Génération de graphiques (PNG/SVG)
- [ ] Mode interactif (CLI avec prompts)
- [ ] Historique des extractions
- [ ] Alertes automatiques si données critiques manquantes

## Contribution

Pour améliorer ce script :

1. Modifier `extract-energy-data.js`
2. Tester avec plusieurs utilisateurs
3. Mettre à jour cette documentation
4. Commit avec message descriptif

## Support

En cas de problème :

1. Vérifier les logs backend : `tail -f backend/logs/api_server.log`
2. Vérifier les données utilisateur : `psql -d pulse`
3. Consulter `ANALYSE_RESULTATS_ENERGIE_USER.md` pour comprendre les données attendues

---

**Dernière mise à jour:** 2026-02-03  
**Version:** 1.0.0  
**Auteur:** Pulse Team
