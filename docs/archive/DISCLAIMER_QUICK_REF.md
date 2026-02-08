# Disclaimer Médical : Référence Rapide

**Status:** ✅ ENFORCED côté backend  
**Fichier:** `backend/services/ai_service.py` → `_enforce_infection_disclaimer()`  
**Date:** 2026-01-30  

---

## 🎯 En Bref

**Quoi :** Disclaimer médical automatiquement injecté dans toute carte Brief mentionnant infection-like si `score > 0.3`.

**Où :** Backend (`generate_brief()`) → pas besoin de modification mobile.

**Pourquoi :** Conformité médico-légale (CE / FDA) + éviter confusion "signature = diagnostic".

---

## 🔄 Flow

```
LLM génère cartes 
  → _enforce_infection_disclaimer()
    → Si infection score > 0.3
      → Cherche cartes avec keywords (infection, vigilance, santé...)
      → Injecte disclaimer dans content
  → Return cartes (disclaimer présent)
  → Mobile affiche content tel quel
```

---

## 📝 Disclaimers

### Moderate (0.3-0.6)

```
⚠️ Important
• Ceci n'est PAS un diagnostic médical
• Consultez un professionnel si symptômes
```

### High (>0.6)

```
⚠️ Important
• Ceci n'est PAS un diagnostic médical
• Consultez IMMÉDIATEMENT un professionnel si symptômes graves
```

---

## 🧪 Test Rapide

```bash
cd backend/tests
python test_disclaimer_enforcement.py
# Expect: 5/5 tests passed
```

---

## 📊 Monitoring

```bash
grep "DISCLAIMER ENFORCEMENT" backend_logs.log
```

**Alertes si :**
- Error rate > 1%
- Enforcement rate < 95%

---

## 📚 Docs Complètes

- `DISCLAIMER_ENFORCEMENT_SUMMARY.md` → Résumé complet
- `INFECTION_DISCLAIMER_ENFORCEMENT.md` → Doc technique détaillée
- `MOBILE_SCREENS_GUIDE.md` (ligne 511-555) → Specs originales
