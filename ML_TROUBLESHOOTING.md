# 🔧 Troubleshooting ML Feedback System

## Problème : `onSubmit is not a function (it is undefined)`

### Diagnostic

L'erreur indique que la prop `onSubmit` n'est pas correctement passée au composant `FeedbackSlider`.

### Solutions

#### 1️⃣ Nettoyer tous les caches

```bash
cd /Users/dannezri/Desktop/Pulse/mobile
chmod +x clear-all-caches.sh
./clear-all-caches.sh
```

Puis redémarrer Metro :

```bash
npx expo start --clear
```

#### 2️⃣ Vérifier les logs

Ouvrez l'app et regardez les logs Metro. Vous devriez voir :

```
[FeedbackSlider] onSubmit type: function
[FeedbackSlider] onSubmit defined: true
```

Si vous voyez :

```
[FeedbackSlider] onSubmit type: undefined
[FeedbackSlider] onSubmit defined: false
```

Cela signifie que `submitFeedback` du hook `useFeedback` n'est pas défini.

#### 3️⃣ Vérifier que le hook retourne bien `submitFeedback`

Dans le terminal Metro, cherchez :

```
[useFeedback] 📤 Envoi feedback
```

Si ce log n'apparaît jamais, le hook n'est pas correctement chargé.

#### 4️⃣ Forcer la recompilation

Si les caches ne suffisent pas, réinstallez les dépendances :

```bash
cd /Users/dannezri/Desktop/Pulse/mobile
rm -rf node_modules
npm install
npx expo start --clear
```

#### 5️⃣ Vérifier l'import de `useFeedback`

Ouvrez `mobile/src/hooks/useFeedback.ts` et assurez-vous que :
- Le fichier existe
- Il exporte bien `useFeedback`
- Il n'y a pas d'erreur de syntaxe

#### 6️⃣ Vérifier l'import dans `energie.tsx`

```tsx
import { useFeedback } from '../../src/hooks/useFeedback'; // ✅ Chemin correct
```

Et dans le composant :

```tsx
const { submitFeedback } = useFeedback(); // ✅ Extraction correcte
```

#### 7️⃣ Ajouter un log de debug

Dans `energie.tsx`, juste après le `useFeedback()`, ajoutez :

```tsx
const { submitFeedback } = useFeedback();
console.log('[EnergyAnalysis] submitFeedback type:', typeof submitFeedback);
```

Vous devriez voir :

```
[EnergyAnalysis] submitFeedback type: function
```

#### 8️⃣ Vérifier que le backend est accessible

Le hook `useFeedback` appelle `${API_URL}/api/v1/feedback`. Vérifiez que :

1. Le backend est démarré :
```bash
ps aux | grep api_server.py
```

2. L'URL est correcte dans `mobile/src/config/api.ts` :
```tsx
export const API_URL = 'http://192.168.X.X:9000'; // ✅ IP de votre Mac
```

3. Le device mobile peut accéder au backend :
```bash
curl http://192.168.X.X:9000/health
```

---

## Problème : Le FeedbackSlider ne s'affiche pas

### Causes possibles

1. **Timer pas écoulé** : Le slider s'affiche après 15 secondes
2. **Conditions non remplies** : `showFeedback && userId && forecast && submitFeedback`
3. **forecast.influencers est vide** : Pas de médicaments ou conditions actifs

### Solutions

#### Afficher immédiatement (pour test)

Dans `energie.tsx`, remplacez :

```tsx
useEffect(() => {
  const timer = setTimeout(() => {
    if (forecast && !showFeedback) {
      setShowFeedback(true);
    }
  }, 15000); // 15 secondes
  
  return () => clearTimeout(timer);
}, [forecast, showFeedback]);
```

Par :

```tsx
useEffect(() => {
  if (forecast && !showFeedback) {
    console.log('[EnergyAnalysis] 💬 Affichage immédiat du FeedbackSlider');
    setShowFeedback(true);
  }
}, [forecast]);
```

#### Ajouter un bouton de test

Dans `energie.tsx`, ajoutez dans le header :

```tsx
<Pressable
  style={styles.testButton}
  onPress={() => {
    console.log('[EnergyAnalysis] 🧪 Affichage manuel du FeedbackSlider');
    setShowFeedback(true);
  }}
>
  <Text style={styles.testButtonText}>💬 Test Feedback</Text>
</Pressable>
```

---

## Problème : Erreur 500 lors de l'envoi du feedback

### Diagnostic

Le backend retourne une erreur 500. Vérifiez les logs backend :

```bash
tail -f /Users/dannezri/Desktop/Pulse/backend/backend_ml.log
```

### Causes courantes

1. **MLOptimizer non initialisé** : Redémarrez le backend
2. **Supabase inaccessible** : Vérifiez les variables d'environnement
3. **Format de payload incorrect** : Vérifiez les logs `[useFeedback] 📤 Envoi feedback`

---

## Problème : Les ajustements ML ne sont pas appliqués

### Vérifier dans Supabase

```sql
SELECT * FROM user_feedback 
WHERE user_id = 'VOTRE_USER_ID' 
ORDER BY created_at DESC 
LIMIT 5;
```

Vous devriez voir vos feedbacks.

```sql
SELECT * FROM personalized_weights 
WHERE user_id = 'VOTRE_USER_ID' 
  AND is_active = TRUE;
```

Les poids ne seront créés qu'après le 3ème feedback pour un facteur donné.

### Vérifier les logs backend

```
[MLOptimizer] 📝 Feedback reçu
[MLOptimizer] 🎯 medication:XXX weight: 1.000 → 0.992
```

Si vous voyez :

```
[MLOptimizer] ⏸️ Pas assez de feedbacks (2/3)
```

C'est normal ! Donnez 1-2 feedbacks de plus.

---

## Checklist complète

- [ ] Backend démarré (`ps aux | grep api_server.py`)
- [ ] Backend logs OK (`tail -f backend_ml.log`)
- [ ] Caches mobile nettoyés (`./clear-all-caches.sh`)
- [ ] Metro redémarré (`npx expo start --clear`)
- [ ] App relancée sur le device
- [ ] `submitFeedback` est défini (`console.log`)
- [ ] `onSubmit` est défini dans FeedbackSlider (`console.log`)
- [ ] Conditions de rendu remplies (`userId`, `forecast`, etc.)
- [ ] Timer écoulé (15 secondes) ou bouton test ajouté
- [ ] Pas d'erreur dans les logs Metro
- [ ] Pas d'erreur 500 dans les logs backend

---

**Si le problème persiste après toutes ces étapes, partagez les logs complets !** 🔍
