# Risk Windows + Agenda : Référence Rapide

**Status:** ✅ Implémenté (backend)  
**Date:** 2026-01-30  

---

## 🎯 En Bref

**Quoi :** Risk windows enrichis avec événements du calendrier

**Pourquoi :** Transformer info passive → assistant proactif

**Comment :** Backend croise créneaux à risque avec événements et génère recommandations intelligentes

---

## 🔄 Flow

```
User avec event "Réunion client" à 16h30
  ↓
compute_daily_energy(states, user_id, date)
  ↓
generate_risk_windows(...) 
  → Détecte creux 16h-18h
  → Récupère events du jour
  → Trouve conflit avec "Réunion client"
  → Classifie: importance = 3 (critique)
  → Génère: recommendation type "prepare"
  ↓
API return risk_windows enrichis
  ↓
Mobile affiche:
  ⚠️ Creux prévu : 16h-18h
     Réunion client durant ce creux
  
  💡 Recommandation Pulse
  👉 Prends une pause 30 min avant
```

---

## 📊 Classification

| Importance | Keywords | Action |
|------------|----------|--------|
| Critique (3) | réunion, meeting, client | **Prepare** (ne pas déplacer) |
| Important (2) | call, appel, rendez-vous | **Reschedule** (déplacer) |
| Normal (1) | sport, gym | **Reschedule** ou **Accept** |
| Personnel (0) | lunch, café | **Reschedule** (flexible) |

---

## 📝 Format API

```json
{
  "risk_windows": [
    {
      "from": "16:00",
      "to": "18:00",
      "text": "⚠️ Réunion client prévu durant ce creux",
      "has_conflict": true,
      "recommendation": {
        "type": "prepare",
        "action": "Prends une pause 30 min avant",
        "details": "15 min de marche + snack protéiné"
      }
    }
  ]
}
```

---

## 📁 Fichiers

- `backend/daily_energy_engine.py` (ligne 367-560) → Implémentation
- `RISK_WINDOWS_AGENDA_ENRICHMENT.md` → Doc complète
- `MOBILE_SCREENS_GUIDE.md` (ligne 145-285) → Specs UI

---

## 🧪 Test Rapide

```bash
cd backend
python daily_energy_engine.py
# Vérifier risk_windows avec recommendation si events présents
```

---

## ✅ Avantages

- ✅ Proactif (anticipe conflits)
- ✅ Intelligent (classifie importance)
- ✅ Fail-safe (erreur → classique)
- ✅ Rétrocompatible (mobile peut ignorer)
