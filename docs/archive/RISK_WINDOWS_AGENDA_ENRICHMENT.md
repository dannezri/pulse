# Risk Windows + Agenda : Enrichissement Intelligent

**Date:** 2026-01-30  
**Status:** ✅ Implémenté  
**Priorité:** HAUTE (UX proactif)  

---

## 🎯 Objectif

Transformer les **risk windows** (créneaux à risque d'énergie faible) d'une **info passive** en **assistant proactif** en les croisant avec les événements du calendrier.

### Avant (V1)

```
📉 Creux prévu : 16h-18h
```

**Limite :** Info utile mais passive. L'utilisateur doit lui-même croiser avec son agenda.

### Après (V2)

```
⚠️ Creux prévu : 16h-18h
   Réunion client durant ce creux

💡 Recommandation Pulse
👉 Prends une pause 30 min avant
   15 min de marche + snack protéiné
```

**Avantage :** Assistant proactif qui analyse l'agenda et propose des actions concrètes.

---

## 🔧 Architecture

```
compute_daily_energy(states, user_id, target_date)
  ↓
  generate_risk_windows(energy, debt, recovery, user_id, target_date)
    ↓
    1. Calcule créneau à risque (selon énergie/dette/chronotype)
    2. enrich_risk_window_with_calendar(risk_window, user_id, date)
       ↓
       a. Récupère événements du jour (calendar_events)
       b. Identifie conflits (événement dans risk window)
       c. Classifie importance (critique/important/normal/personnel)
       d. Génère recommandation (prepare/reschedule/accept)
    3. Return risk_window enrichi
  ↓
  return energy_data avec risk_windows enrichis
```

---

## 📊 Classification des Événements

### Keywords par Importance

| Importance | Score | Keywords | Recommandation |
|------------|-------|----------|----------------|
| **Critique** | 3 | réunion, meeting, client, présentation, entretien, interview, board | **Prepare** (pause/boost avant) |
| **Important** | 2 | call, appel, rendez-vous, démo, review, sync, 1:1 | **Reschedule** (déplacer) |
| **Normal** | 1 | sport, gym, workout, training, course | **Reschedule** ou **Accept** |
| **Personnel** | 0 | lunch, déjeuner, dîner, café, pause, break | **Reschedule** (flexible) |

### Logic de Recommandation

**1. Événement Critique (importance = 3)**

→ **Type : `prepare`**

Ne PAS déplacer (trop important), mais **préparer** l'utilisateur :

```json
{
  "type": "prepare",
  "action": "Prends une pause 30 min avant 'Réunion client'",
  "details": "15 min de marche + snack protéiné + hydratation. Ton énergie sera à 16h-18h, donc prépare-toi.",
  "reason": "Événement critique durant un creux d'énergie prévu"
}
```

**Rationale :** Une réunion client ne peut souvent pas être déplacée. Mieux vaut préparer l'utilisateur.

---

**2. Événement Important (importance = 2)**

→ **Type : `reschedule`**

Proposer de **déplacer** hors du creux :

```json
{
  "type": "reschedule",
  "action": "Déplace 'Call équipe' hors du creux d'énergie",
  "details": "Suggère 10h-12h ou 14h-16h pour maximiser ta performance.",
  "reason": "Timing sous-optimal pour un événement important"
}
```

**Rationale :** Un call interne peut souvent être déplacé. L'utilisateur sera plus performant hors du creux.

---

**3. Événement Normal/Personnel (importance = 0-1)**

→ **Type : `reschedule`** (si 1 événement) ou **`accept`** (si plusieurs)

Si 1 seul événement :

```json
{
  "type": "reschedule",
  "action": "Déplace 'Gym' en matinée si possible",
  "details": "Tu auras plus d'énergie avant 14h.",
  "reason": "Optimisation simple possible"
}
```

Si plusieurs événements :

```json
{
  "type": "accept",
  "action": "3 événements durant le creux : Accepte la baisse de rythme",
  "details": "Priorise l'essentiel, reporte ce qui peut l'être.",
  "reason": "Trop d'événements à déplacer"
}
```

**Rationale :** Éviter de submerger l'utilisateur de recommandations. Si trop d'événements, suggérer l'acceptation.

---

## 📁 Fichiers Modifiés

| Fichier | Changement | Description |
|---------|-----------|-------------|
| `backend/daily_energy_engine.py` | ✅ Ajout `enrich_risk_window_with_calendar()` | Fonction d'enrichissement |
| `backend/daily_energy_engine.py` | ✅ Ajout `classify_event_importance()` | Classification par keywords |
| `backend/daily_energy_engine.py` | ✅ Ajout `generate_calendar_recommendation()` | Génération recommandations |
| `backend/daily_energy_engine.py` | ✅ Modification `generate_risk_windows()` | Accepte user_id + target_date |
| `backend/daily_energy_engine.py` | ✅ Modification `compute_daily_energy()` | Accepte user_id + target_date |
| `backend/services/latent_state_service.py` | ✅ Mise à jour appel | Passe user_id + target_date |
| `MOBILE_SCREENS_GUIDE.md` | ✅ Documentation V2 | Section enrichissement agenda |
| `RISK_WINDOWS_AGENDA_ENRICHMENT.md` | ✅ Doc technique | Ce fichier |

---

## 📝 Format API

### Sans Conflit (V1 - compatible)

```json
{
  "energy_score": 78,
  "label": "Bonne journée",
  "risk_windows": [
    {
      "from": "16:00",
      "to": "18:00",
      "risk": "dip",
      "text": "Baisse d'énergie attendue en milieu d'après-midi"
    }
  ]
}
```

### Avec Conflit (V2 - enrichi)

```json
{
  "energy_score": 65,
  "label": "Journée moyenne",
  "risk_windows": [
    {
      "from": "16:00",
      "to": "18:00",
      "risk": "dip",
      "text": "⚠️ Réunion client prévu durant ce creux d'énergie",
      "has_conflict": true,
      "conflicting_events": [
        {
          "title": "Réunion client important",
          "start": "2026-01-30T16:30:00Z",
          "importance": 3
        }
      ],
      "recommendation": {
        "type": "prepare",
        "action": "Prends une pause 30 min avant 'Réunion client'",
        "details": "15 min de marche + snack protéiné + hydratation.",
        "reason": "Événement critique durant un creux d'énergie prévu"
      }
    }
  ]
}
```

---

## 📱 Impact Mobile

### Affichage Recommandé

**Si `has_conflict === true` :**

1. **Afficher l'alerte** : `⚠️ {risk_window.text}`
2. **Afficher la recommandation** :
   ```
   💡 Recommandation Pulse
   👉 {recommendation.action}
   ```
3. **Détails (optionnel, expandable)** :
   ```
   {recommendation.details}
   
   Raison: {recommendation.reason}
   ```
4. **CTA selon type** :
   - `prepare` → [Configurer rappel] (notification 30 min avant)
   - `reschedule` → [Déplacer dans calendrier] (deep link future)
   - `accept` → [Voir alternatives] (suggestions d'optimisation)

**Si `has_conflict === false` :**

Afficher le risk window classique :
```
📉 Creux prévu : {from}-{to}
```

---

## 🧪 Exemples de Test

### Test 1 : Événement Critique

**Setup :**
- User avec energy = 0.65 (moyenne)
- Risk window : 16h-18h
- Événement : "Réunion client" à 16h30

**Résultat attendu :**
```json
{
  "recommendation": {
    "type": "prepare",
    "action": "Prends une pause 30 min avant 'Réunion client'",
    ...
  }
}
```

---

### Test 2 : Événement Important

**Setup :**
- User avec energy = 0.75 (haute)
- Risk window : 17h-19h
- Événement : "Call équipe" à 17h30

**Résultat attendu :**
```json
{
  "recommendation": {
    "type": "reschedule",
    "action": "Déplace 'Call équipe' hors du creux d'énergie",
    ...
  }
}
```

---

### Test 3 : Pas de Conflit

**Setup :**
- User avec energy = 0.80
- Risk window : 17h-19h
- Événement : "Déjeuner" à 12h30 (hors risk window)

**Résultat attendu :**
```json
{
  "from": "17:00",
  "to": "19:00",
  "text": "Baisse d'énergie probable en fin d'après-midi",
  "has_conflict": undefined  // Pas de champ
}
```

---

## ✅ Avantages

1. ✅ **Proactif** : Pulse anticipe et prévient les conflits
2. ✅ **Actionnable** : Recommandations concrètes (pas juste une alerte)
3. ✅ **Intelligent** : Classifie l'importance (ne suggère pas de déplacer une réunion CEO)
4. ✅ **Fail-Safe** : Si erreur récupération agenda → retourne risk window classique
5. ✅ **Rétrocompatible** : Mobile peut ignorer les nouveaux champs (dégradation gracieuse)

---

## 🚀 Évolutions Futures (V3+)

### Deep Links Calendar

```json
{
  "recommendation": {
    "type": "reschedule",
    "action": "Déplace 'Call équipe'",
    "calendar_action": {
      "type": "reschedule",
      "event_id": "cal_event_123",
      "suggested_slots": [
        {"from": "10:00", "to": "11:00"},
        {"from": "14:00", "to": "15:00"}
      ]
    }
  }
}
```

**Implémentation :** Deep link vers l'app calendrier avec suggestions pré-remplies.

---

### ML Importance Prediction

Actuellement, l'importance est basée sur **keywords**. V3 pourrait utiliser :

- Historique de l'utilisateur (événements qu'il déplace vs ceux qu'il garde)
- Participants (CEO/team lead = critique)
- Durée (1h+ = plus important)
- Localisation (in-person = moins flexible)

---

### Recommendations Historiques

Tracker les recommandations :
- Acceptées → reinforcer le modèle
- Ignorées → ajuster les seuils
- Déplacées → apprendre les préférences timing

---

## 📊 Métriques à Monitorer

### Adoption

- % users avec au moins 1 conflit détecté / jour
- % users qui voient la recommandation
- % users qui cliquent sur [Voir détails]

### Efficacité

- % recommandations suivies (si tracking implémenté)
- Feedback explicite (👍/👎 sur recommendation)
- Churn rate des users avec vs sans conflicts

### Performance

- Latency de `enrich_risk_window_with_calendar()` (doit être < 200ms)
- Error rate (doit être < 0.1%)
- Cache hit rate des événements calendrier

---

## 🔐 Sécurité & Privacy

### Données Utilisées

- ✅ `calendar_events` table (user_id, title, start_time, end_time, notes)
- ✅ Aucune donnée externe (Google Calendar API, etc.)

### Fail-Safe

Si erreur lors de la récupération des événements :
- ✅ Retourne risk_window classique (sans enrichissement)
- ✅ Log l'erreur (monitoring)
- ✅ Ne bloque PAS le calcul de daily_energy

### Privacy

- ✅ Les événements calendrier restent dans Supabase (pas de partage externe)
- ✅ Les titres d'événements apparaissent dans les recommandations (OK car données user propres)
- ✅ Classification par keywords (pas d'envoi à un LLM)

---

## ✅ Checklist Déploiement

### Phase 1 : Implémentation (DONE ✅)

- [x] Fonction `enrich_risk_window_with_calendar()`
- [x] Fonction `classify_event_importance()`
- [x] Fonction `generate_calendar_recommendation()`
- [x] Modification `generate_risk_windows()` (params)
- [x] Modification `compute_daily_energy()` (params)
- [x] Update appel dans `latent_state_service.py`
- [x] Documentation `MOBILE_SCREENS_GUIDE.md`
- [x] Documentation `RISK_WINDOWS_AGENDA_ENRICHMENT.md`

### Phase 2 : Testing (TODO)

- [ ] Test unitaire : `test_enrich_risk_window_with_calendar()`
- [ ] Test intégration : Event critique → prepare
- [ ] Test intégration : Event important → reschedule
- [ ] Test intégration : Pas d'événement → pas d'enrichissement
- [ ] Test fail-safe : Erreur DB → retour classique
- [ ] Test mobile : Affichage avec/sans conflit

### Phase 3 : Mobile UI (TODO)

- [ ] Composant `<RiskWindowWithRecommendation />`
- [ ] Affichage conditionnel si `has_conflict`
- [ ] Styling recommandation (💡 icône, couleur distinctive)
- [ ] CTA selon type (prepare/reschedule/accept)
- [ ] Expandable details (optionnel)

### Phase 4 : Déploiement Prod (TODO)

- [ ] Merge PR
- [ ] Deploy backend
- [ ] Monitor latency `enrich_risk_window_with_calendar()`
- [ ] Monitor error rate
- [ ] A/B test : avec vs sans enrichissement (impact engagement)

---

## 📚 Références

- `backend/daily_energy_engine.py` : Implémentation
- `MOBILE_SCREENS_GUIDE.md` : Specs UI
- `DAILY_ENERGY_BACKEND_MIGRATION.md` : Context migration backend

---

**Implémentation backend complète ! Prêt pour tests et UI mobile.** 🚀
