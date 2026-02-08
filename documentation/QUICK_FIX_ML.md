# 🔥 Fix Rapide : Erreur `onSubmit is not a function`

## ✅ Problème résolu

L'erreur venait d'un conflit entre deux versions du hook `useFeedback` :
- Ancienne version : gère le FeedbackBottomSheet (Dashboard)
- Nouvelle version : appel API simple (page Énergie)

**Solution** : Hook unifié compatible avec les deux usages.

---

## 🚀 Étapes de correction (2 minutes)

### 1️⃣ Nettoyer les caches

```bash
cd /Users/dannezri/Desktop/Pulse/mobile
chmod +x clear-all-caches.sh
./clear-all-caches.sh
```

### 2️⃣ Redémarrer Metro

```bash
npx expo start --clear
```

### 3️⃣ Relancer l'app

Appuyez sur **[i]** dans le terminal Metro.

---

## ✅ Test de validation

### Sur le Dashboard (index.tsx)

1. Ouvrir l'app → Dashboard
2. Le `FeedbackBottomSheet` devrait pouvoir s'ouvrir
3. Ajuster le slider et appuyer sur "Envoyer"

**Logs attendus :**
```
[useFeedback] 📝 handleSubmitFeedback appelé, userScore: 45
[useFeedback] 📤 Envoi feedback: {...}
[useFeedback] ✅ Feedback envoyé: error=16.0%, adjustments=2
```

### Sur la page Énergie (energie.tsx)

1. Onglet "Énergie" → Attendre 15 secondes
2. Le `FeedbackSlider` apparaît en bas
3. Ajuster et envoyer

**Logs attendus :**
```
[EnergyAnalysis] 📤 onSubmit appelé avec userScore: 45
[useFeedback] 📤 Envoi feedback
[EnergyAnalysis] ✅ Feedback result
```

---

## 📊 Modifications apportées

| Fichier | Changement |
|---------|------------|
| `mobile/src/hooks/useFeedback.ts` | Hook unifié compatible Dashboard + Énergie |

---

## 🔧 Si l'erreur persiste

### Option 1 : Forcer la reconstruction

```bash
cd /Users/dannezri/Desktop/Pulse/mobile
rm -rf node_modules
npm install
npx expo start --clear
```

### Option 2 : Vérifier les logs

Ouvrez Metro et cherchez :
```
[useFeedback] handleSubmitFeedback appelé
```

Si ce log n'apparaît pas, partagez les logs Metro complets.

---

**Le hook est maintenant compatible avec les deux composants de feedback ! 🎯**
