# Configuration OpenAI API pour Enrichissement des Médicaments

## 🎯 Objectif

Configurer l'API OpenAI (GPT-4o) pour l'enrichissement automatique des médicaments avec le code ATC.

**Note** : Cette configuration est **optionnelle**. Sans elle :
- ✅ L'app fonctionne normalement
- ✅ BDPM API (gratuite) est utilisée
- ❌ Pas de code ATC automatique pour les médicaments hors base locale

---

## 📋 Prérequis

1. **Compte OpenAI** : https://platform.openai.com
2. **Crédits** : ~$5 minimum recommandé
3. **API Key** : Créer une clé API

---

## 🔑 Obtenir une API Key

### Étape 1 : Créer un compte OpenAI

1. Aller sur https://platform.openai.com/signup
2. S'inscrire avec email ou Google
3. Vérifier l'email

### Étape 2 : Ajouter des crédits

1. Aller sur https://platform.openai.com/account/billing
2. Cliquer "Add payment details"
3. Ajouter une carte de crédit
4. Ajouter au minimum **$5** de crédits

**Coûts estimés** :
- 1 enrichissement : ~$0.005 (0.5 centime)
- 100 enrichissements : ~$0.50
- 1000 enrichissements : ~$5

### Étape 3 : Créer une API Key

1. Aller sur https://platform.openai.com/api-keys
2. Cliquer "Create new secret key"
3. Nommer la clé : "Pulse Mobile - Medication Enrichment"
4. **Copier la clé** (format : `sk-proj-...`)
5. ⚠️ **Important** : La clé ne sera affichée qu'une seule fois !

---

## ⚙️ Configuration dans l'App

### Méthode 1 : Fichier .env (Recommandé)

1. **Créer le fichier** `.env` dans `mobile/` :

```bash
cd /Users/dannezri/Desktop/Pulse/mobile
touch .env
```

2. **Éditer le fichier** `.env` :

```bash
# OpenAI API Key
EXPO_PUBLIC_OPENAI_API_KEY=sk-proj-votre-cle-ici
```

3. **Redémarrer Metro** :

```bash
# Arrêter Metro (Ctrl+C)
# Relancer
npm start
```

### Méthode 2 : Variable système (macOS)

```bash
# Ajouter à ~/.zshrc ou ~/.bash_profile
export EXPO_PUBLIC_OPENAI_API_KEY="sk-proj-votre-cle-ici"

# Recharger le shell
source ~/.zshrc
```

### Méthode 3 : EAS Secrets (Production)

```bash
# Pour la production via EAS
eas secret:create --scope project --name EXPO_PUBLIC_OPENAI_API_KEY --value sk-proj-votre-cle-ici
```

---

## 🧪 Vérification

### Test 1 : Vérifier la configuration

Ajouter ce code temporairement dans `App.tsx` :

```typescript
import Constants from 'expo-constants';

console.log('OpenAI API Key configurée:', 
  Constants.expoConfig?.extra?.EXPO_PUBLIC_OPENAI_API_KEY ? 'OUI ✅' : 'NON ❌'
);
```

**Résultat attendu** :
```
OpenAI API Key configurée: OUI ✅
```

### Test 2 : Tester l'enrichissement

1. Ouvrir l'app
2. Aller dans Profil → "Ajouter un médicament"
3. Entrer : "Mirtazapine 15mg"
4. Sauvegarder

**Logs attendus** :
```
[MedicationEnrichment] 🔍 Enrichissement pour: Mirtazapine
[MedicationEnrichment] Recherche BDPM pour: mirtazapine
[MedicationEnrichment] Aucun résultat BDPM
[MedicationEnrichment] Appel GPT-4o pour: Mirtazapine 15mg
[MedicationEnrichment] ✅ GPT-4o résultat: { atc_code: "N06AX11", ... }
[useMedications] ✅ Enrichissement réussi
```

---

## 🔒 Sécurité

### ⚠️ Règles importantes

1. **Ne JAMAIS commiter le fichier `.env`**
   ```bash
   # Vérifier que .env est dans .gitignore
   cat .gitignore | grep .env
   ```

2. **Ne JAMAIS partager la clé API**
   - Pas dans Slack, Discord, email, etc.
   - Pas dans les screenshots de logs

3. **Rotation de la clé**
   - Changer la clé tous les 3 mois
   - Changer immédiatement si fuite suspectée

4. **Limiter les permissions**
   - Dans OpenAI Dashboard → API Keys
   - Limiter aux modèles nécessaires (gpt-4o uniquement)
   - Définir un budget mensuel

### 🚨 En cas de fuite

1. **Révoquer immédiatement** sur https://platform.openai.com/api-keys
2. **Créer une nouvelle clé**
3. **Mettre à jour** dans `.env`
4. **Vérifier les logs** OpenAI pour détecter des usages suspects

---

## 💰 Gestion des Coûts

### Monitoring

1. **Dashboard OpenAI** : https://platform.openai.com/usage
2. Vérifier :
   - Nombre de requêtes / jour
   - Coût par requête
   - Coût total mensuel

### Optimisations

**1. Cache local** (déjà implémenté ✅)
```typescript
// Le cache évite les appels répétés pour le même médicament
enrichmentCache.set(cacheKey, result);
```

**2. Base locale en priorité** (déjà implémenté ✅)
```typescript
// BDPM gratuit essayé avant GPT-4o
const localResult = await searchLocalDatabase(medicationName);
if (localResult.success) return localResult;
```

**3. Limiter les appels**
```typescript
// Dans MedicationEnrichment.ts, modifier :
const MAX_GPT4O_CALLS_PER_DAY = 100;
let gpt4oCallsToday = 0;

// Vérifier avant l'appel
if (gpt4oCallsToday >= MAX_GPT4O_CALLS_PER_DAY) {
  return { success: false, error: 'Limite quotidienne atteinte' };
}
```

### Budget Alert

Configurer une alerte dans OpenAI Dashboard :
- Settings → Billing → Usage limits
- Hard limit : $10/mois
- Email alert : $5/mois

---

## 🐛 Dépannage

### Erreur : "API key non configurée"

**Solution** :
1. Vérifier que `.env` existe dans `mobile/`
2. Vérifier que la clé commence par `sk-proj-`
3. Redémarrer Metro complètement
4. Clear cache : `npm start --reset-cache`

### Erreur : "Insufficient credits"

**Solution** :
1. Aller sur https://platform.openai.com/account/billing
2. Ajouter des crédits ($5 minimum)
3. Attendre 1-2 minutes (propagation)

### Erreur : "Rate limit exceeded"

**Solution** :
- Attendre 1 minute (limite : 60 requêtes/minute)
- Ou upgrader vers un tier supérieur

### Erreur : "Invalid API key"

**Solution** :
1. Vérifier que la clé n'a pas expiré
2. Révoquer et recréer une nouvelle clé
3. Mettre à jour `.env`

---

## 🔄 Mode Développement vs Production

### Développement (sans coût)

```bash
# .env.development
EXPO_PUBLIC_OPENAI_API_KEY=placeholder-key
```

Résultat :
- ✅ Base locale fonctionne
- ✅ BDPM API fonctionne
- ❌ GPT-4o désactivé (pas de coût)

### Production (avec enrichissement complet)

```bash
# .env.production
EXPO_PUBLIC_OPENAI_API_KEY=sk-proj-vraie-cle
```

Résultat :
- ✅ Base locale fonctionne
- ✅ BDPM API fonctionne
- ✅ GPT-4o actif

---

## 📊 Dashboard

### Métriques à surveiller

1. **Requêtes GPT-4o** :
   ```
   [MedicationEnrichment] Appel GPT-4o pour: ...
   ```
   Compter combien par jour

2. **Taux de succès** :
   ```typescript
   successRate = (enrichissements réussis) / (total enrichissements) * 100
   ```

3. **Sources utilisées** :
   ```
   local_cache: 40%
   bdpm_api: 35%
   gpt4o: 25%
   ```

### Alertes recommandées

- ⚠️ > 50 appels GPT-4o/jour
- 🚨 > 100 appels GPT-4o/jour
- ⚠️ Coût mensuel > $5
- 🚨 Coût mensuel > $10

---

## ✅ Checklist

- [ ] Compte OpenAI créé
- [ ] Crédits ajoutés ($5 minimum)
- [ ] API Key générée
- [ ] Fichier `.env` créé
- [ ] Variable `EXPO_PUBLIC_OPENAI_API_KEY` définie
- [ ] `.env` dans `.gitignore`
- [ ] Metro redémarré
- [ ] Test d'enrichissement réussi
- [ ] Logs GPT-4o visibles
- [ ] Budget alert configuré
- [ ] Monitoring en place

---

## 🎉 Résultat

Avec OpenAI configuré :
- ✅ **100% des médicaments** peuvent être enrichis
- ✅ **Code ATC automatique** même pour les médicaments rares
- ✅ **Intelligence contextuelle** pour les variantes

Sans OpenAI :
- ✅ **Base locale** : ~30 médicaments communs
- ✅ **BDPM** : Tous les médicaments français (substance, labo)
- ⚠️ **Pas d'ATC** pour les médicaments non répertoriés

**Configuration recommandée : Activer OpenAI pour une expérience optimale ! 🚀**
