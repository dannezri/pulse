# Infection-Like Disclaimer Enforcement

**Date:** 2026-01-30
**Status:** ✅ Implémenté
**Priorité:** CRITIQUE (médico-légal)

---

## 🎯 Objectif

**ENFORCER** le disclaimer médical pour toute carte Brief mentionnant une signature infection-like avec `score > 0.3`.

Le disclaimer **NE DOIT PAS** être optionnel ou laissé à la discrétion du LLM/mobile.

---

## ⚠️ Risques Sans Enforcement

1. **Médico-légal** : Utilisateur confond "signature physiologique" avec "diagnostic médical"
2. **Réglementaire** : Non-conformité CE Medical Device / FDA
3. **Santé publique** : Retard de consultation médicale pour symptômes graves
4. **Réputation** : Procès / bad press si utilisateur retarde consultation

---

## ✅ Solution Implémentée

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Request                             │
│                GET /api/insights/brief                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              AIAnalysisService.generate_brief()             │
│                                                             │
│  1. Build prompt avec latent states                        │
│  2. LLM génère cartes Brief                                │
│  3. ✅ _enforce_infection_disclaimer() <── NEW             │
│     │                                                       │
│     ├─► Récupère infection_like.smoothed_score            │
│     ├─► Si score > 0.3, cherche cartes avec keywords      │
│     ├─► Injecte disclaimer automatiquement                │
│     └─► Log enforcement                                    │
│                                                             │
│  4. Save en DB                                             │
│  5. Return à mobile                                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Mobile Display                           │
│                (affiche disclaimer enforcé)                 │
└─────────────────────────────────────────────────────────────┘
```

### Implémentation

**Fichier :** `backend/services/ai_service.py`

**Fonction :** `_enforce_infection_disclaimer(user_id, brief_data)`

**Logic :**

```python
1. Récupérer infection_like.smoothed_score depuis daily_state
2. Si score < 0.3 → return brief_data (pas de disclaimer)
3. Si score >= 0.3 :
   a. Chercher toute carte avec keywords:
      ['infection', 'vigilance', 'santé', 'signature', 
       'inhabituel', 'maladie', 'symptômes', 'physiologique', 
       'pattern', 'immune']
   
   b. Pour chaque carte trouvée:
      - Vérifier si disclaimer déjà présent
      - Si non, injecter disclaimer dans content
   
   c. Disclaimer varie selon sévérité:
      - score 0.3-0.6 : moderate (surveillance)
      - score > 0.6 : high (consultation urgente)
```

---

## 📝 Disclaimers Standards

### Moderate (0.3 - 0.6)

```markdown
---

⚠️ **Important**

• **Ceci n'est PAS un diagnostic médical**, mais une observation de patterns physiologiques.

• Si vous ressentez des symptômes importants ou persistants, **consultez un professionnel de santé**.
```

### High (> 0.6)

```markdown
---

⚠️ **Important**

• **Ceci n'est PAS un diagnostic médical**, mais une observation de patterns physiologiques.

• Si vous ressentez des symptômes importants ou persistants (fièvre, douleurs, fatigue intense), **consultez immédiatement un professionnel de santé**.
```

---

## 🔍 Keywords Détectés

Les cartes suivantes déclenchent l'enforcement :

| Keyword | Contexte |
|---------|----------|
| infection | Mention directe |
| vigilance | "Vigilance santé" |
| santé | Carte santé générale |
| signature | "Signature physiologique inhabituelle" |
| inhabituel | Pattern inhabituel |
| maladie | Mention maladie |
| symptômes | Mention symptômes |
| physiologique | Pattern physiologique |
| pattern | Pattern inhabituel |
| immune | Système immunitaire |

---

## 🧪 Testing

### Test Manuel

1. **Setup :**
   - User avec `infection_like.smoothed_score = 0.45`
   - Biométries : RHR élevé, HRV bas, fragmentation haute

2. **Action :**
   - `GET /api/insights/brief`

3. **Vérification :**
   ```bash
   # Logs backend
   [DISCLAIMER ENFORCEMENT] Infection score: 0.450
   [DISCLAIMER ENFORCEMENT] Injected disclaimer in card 'Vigilance santé' (severity: moderate)
   [DISCLAIMER ENFORCEMENT] ✅ Enforced disclaimer on 1 card(s)
   ```

4. **Résultat attendu :**
   - Carte contient disclaimer complet
   - Disclaimer pas dupliqué si LLM l'avait déjà ajouté

### Test Automatisé

**Fichier :** `backend/tests/test_disclaimer_enforcement.py`

```python
def test_disclaimer_enforcement():
    # Setup user avec infection score 0.45
    # Generate brief
    # Assert: disclaimer présent dans carte infection
    # Assert: disclaimer NOT présent si score < 0.3
```

---

## 📊 Métriques

### Logs à Monitorer

```
[DISCLAIMER ENFORCEMENT] Infection score: {score}
[DISCLAIMER ENFORCEMENT] Score < 0.3, no disclaimer needed
[DISCLAIMER ENFORCEMENT] Injected disclaimer in card '{title}' (severity: {severity})
[DISCLAIMER ENFORCEMENT] ✅ Enforced disclaimer on {count} card(s)
[DISCLAIMER ENFORCEMENT] No relevant card found for disclaimer injection
[DISCLAIMER ENFORCEMENT] Error: {error}
```

### Alertes Critiques

- ⚠️ Si `Error:` apparaît → fail-safe activé (retourne cartes sans modification)
- ⚠️ Si score > 0.6 et 0 cartes modifiées → LLM n'a pas généré carte infection (normal si pénalités)

---

## 🔐 Sécurité Produit

### Fail-Safe

Si erreur dans `_enforce_infection_disclaimer()` :
- ✅ Retourne `brief_data` non modifié
- ✅ Log l'erreur
- ✅ Ne bloque PAS la génération du Brief

**Justification :** Mieux vaut un Brief sans disclaimer qu'aucun Brief.

### Double Protection

1. **LLM Prompt** : Consigne au LLM d'ajouter le disclaimer
2. **Backend Enforcement** : Garantit présence même si LLM oublie

---

## 📱 Impact Mobile

### Aucune Modification Nécessaire

Le mobile reçoit déjà le `content` avec le disclaimer injecté.

**Fichier :** `mobile/src/components/BriefCard.tsx`

```tsx
// Aucun changement requis
<Text>{card.content}</Text>  {/* Disclaimer déjà présent */}
```

### Affichage

Le disclaimer apparaît **en bas du content** de la carte concernée :

```
┌─────────────────────────────────────────┐
│  🦠 Vigilance santé                     │
│                                         │
│  Votre **signature physiologique**      │
│  montre des marqueurs inhabituels...    │
│                                         │
│  ---                                    │
│                                         │
│  ⚠️ Important                           │
│  • Ceci n'est PAS un diagnostic médical│
│  • Consultez un professionnel de santé │
└─────────────────────────────────────────┘
```

---

## ✅ Checklist Déploiement

- [x] Implémenter `_enforce_infection_disclaimer()`
- [x] Intégrer dans `generate_brief()`
- [x] Logger enforcement
- [x] Fail-safe si erreur
- [x] Documenter dans MOBILE_SCREENS_GUIDE
- [ ] Test d'intégration
- [ ] Review légal/médical du texte disclaimer
- [ ] Test sur device réel
- [ ] Monitor logs en prod (J+7)

---

## 🚀 Prochaines Étapes

1. **Validation juridique** : Faire valider le texte du disclaimer par juriste santé
2. **Traduction** : Préparer disclaimers EN/ES si internationalisation
3. **Analytics** : Tracker combien de fois disclaimer est affiché (via logs)
4. **A/B Test** : Mesurer impact sur consultations médicales (si possible)

---

## 📚 Références

- `MOBILE_SCREENS_GUIDE.md` : Specs originales disclaimer
- `backend/services/ai_service.py` : Implémentation
- `backend/latent_states.py` : Calcul infection_like
- CE Medical Device Regulations
- FDA Digital Health Guidelines
