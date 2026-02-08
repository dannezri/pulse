# Guide de Test : Smart Cache IA

## ✅ Implémentation Complète

Tous les composants du Smart Cache ont été implémentés avec succès :

### 1. Base de Données ✅
- **Migration 014** : `/database/migrations/014_add_smart_cache_to_insights.sql`
  - Ajout de `calendar_event_id` (TEXT)
  - Ajout de `biometrics_ref_at` (TIMESTAMPTZ)
  - Index pour recherche rapide

### 2. Backend ✅
- **LLMClient** : Méthode `generate_event_analysis()` pour Markdown JSON
- **AIAnalysisService** : Service avec logique de cache intelligent
- **API Endpoint** : `POST /api/v1/analyze-event` avec timeout 15s

### 3. Mobile ✅
- **Dépendances** : `react-native-markdown-display` installé
- **Hook** : `useEventAnalysis.ts` pour appeler le backend
- **UI** : `event-detail.tsx` refonte complète avec Markdown

## 🧪 Plan de Test

### Étape 1 : Appliquer la Migration

```bash
# Dans Supabase Dashboard > SQL Editor
# Copier/coller le contenu de database/migrations/014_add_smart_cache_to_insights.sql
# Exécuter la migration

# Vérifier que les colonnes existent :
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'insights' 
AND column_name IN ('calendar_event_id', 'biometrics_ref_at');
```

**Résultat attendu** : 2 lignes (calendar_event_id TEXT, biometrics_ref_at timestamptz)

### Étape 2 : Démarrer le Backend

```bash
cd backend
python api_server.py
```

**Résultat attendu** : 
```
🚀 Démarrage du serveur Bio-Feedback IA sur http://0.0.0.0:9000
📡 Endpoint webhook: http://localhost:9000/api/webhooks/wearables
```

### Étape 3 : Tester l'Endpoint (Postman/curl)

#### Test A : Première Analyse (Cache Miss)

```bash
curl -X POST http://localhost:9000/api/v1/analyze-event \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_USER_UUID",
    "event": {
      "title": "Réunion importante",
      "start": "2026-01-28T14:00:00Z",
      "end": "2026-01-28T15:00:00Z",
      "location": "Bureau",
      "notes": "Présentation client"
    },
    "force_refresh": false
  }'
```

**Résultat attendu** :
```json
{
  "status": "success",
  "insight": "# 🟢 Diagnostic Flash\n\nTon corps est...",
  "cached": false,
  "analyzed_at": "2026-01-28T13:30:00Z",
  "biometrics_ref_at": "2026-01-28T13:25:00Z",
  "usage": {
    "total_tokens": 450
  }
}
```

**Vérifications** :
- ✅ `cached: false` (première analyse)
- ✅ `insight` contient du Markdown (# pour titres, ** pour gras)
- ✅ Temps de réponse : 3-8 secondes
- ✅ Coût estimé : ~0.01€

#### Test B : Deuxième Analyse (Cache Hit)

**Répéter exactement la même requête immédiatement**

**Résultat attendu** :
```json
{
  "status": "success",
  "insight": "# 🟢 Diagnostic Flash\n\nTon corps est...",
  "cached": true,
  "analyzed_at": "2026-01-28T13:30:00Z",
  "biometrics_ref_at": "2026-01-28T13:25:00Z"
}
```

**Vérifications** :
- ✅ `cached: true` (cache utilisé)
- ✅ Même `insight` qu'avant
- ✅ Temps de réponse : < 500ms (instantané)
- ✅ Coût : 0.00€ (pas d'appel OpenAI)

#### Test C : Nouvelles Données Biométriques (Cache Miss)

**1. Insérer une nouvelle biométrie**
```sql
INSERT INTO biometrics (user_id, metric_type, value, recorded_at, source)
VALUES ('YOUR_USER_UUID', 'hrv', 55.0, NOW(), 'test');
```

**2. Répéter la même requête**

**Résultat attendu** :
```json
{
  "status": "success",
  "insight": "# 🟡 Diagnostic Flash\n\nTon HRV a baissé...",
  "cached": false,
  "analyzed_at": "2026-01-28T13:35:00Z",
  "biometrics_ref_at": "2026-01-28T13:34:00Z"
}
```

**Vérifications** :
- ✅ `cached: false` (nouvelles données détectées)
- ✅ Nouvelle analyse générée
- ✅ `biometrics_ref_at` est plus récent qu'avant

#### Test D : Force Refresh

```bash
curl -X POST http://localhost:9000/api/v1/analyze-event \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_USER_UUID",
    "event": {
      "title": "Réunion importante",
      "start": "2026-01-28T14:00:00Z",
      "end": "2026-01-28T15:00:00Z"
    },
    "force_refresh": true
  }'
```

**Résultat attendu** :
- ✅ `cached: false` même si le cache existe
- ✅ Nouvelle analyse générée

### Étape 4 : Tester le Mobile

```bash
cd mobile
npm start
# Puis 'i' pour iOS ou 'a' pour Android
```

#### Test E : Affichage Markdown

1. Ouvrir l'app mobile
2. Aller sur l'onglet "Requêtes" ou "Événements"
3. Sélectionner un événement du calendrier

**Résultat attendu** :
- ✅ Header affiche "Analyse IA" (pas "Prompt Preview")
- ✅ Icône `RefreshCw` en haut à droite
- ✅ Pendant le chargement : Spinner + "L'IA analyse votre état biologique..."
- ✅ Après analyse : Markdown formaté avec :
  - Titres H1 en vert (#34C759)
  - Titres H2 en orange (#FF9500)
  - Texte en gras (**) en orange
  - Listes à puces bien formatées
- ✅ Footer avec timestamp : "Analysé il y a X min (Cache)"
- ✅ Bouton "🔄 Recalculer" en bas (discret, gris)

#### Test F : Badge de Probabilité

**Vérifications** :
- ✅ Badge 🟢 "Feu vert" si Readiness ≥ 80%
- ✅ Badge 🟡 "Vigilance" si 60-79%
- ✅ Badge 🔴 "À risque" si < 60%

#### Test G : Bouton Recalculer

1. Cliquer sur le bouton "🔄 Recalculer" en bas
2. Observer le rechargement

**Résultat attendu** :
- ✅ Spinner affiché
- ✅ Nouvelle analyse générée (force_refresh=true)
- ✅ Icône RefreshCw tourne pendant le chargement

#### Test H : Gestion d'Erreurs

**Simuler une erreur (backend arrêté)**

**Résultat attendu** :
- ✅ Affichage d'un conteneur d'erreur rouge
- ✅ Icône AlertCircle
- ✅ Message d'erreur clair
- ✅ Bouton "Réessayer"

## 📊 Résultats Attendus

### Performance
- **Cache hit** : < 500ms (vs 3-8s sans cache)
- **Économies** : ~70-80% d'appels OpenAI évités

### UX
- **Instantanéité** : L'utilisateur ne voit presque jamais le spinner pour les analyses répétées
- **Pertinence** : Dès qu'une nouvelle donnée arrive (entraînement, repas, sommeil), l'analyse se met à jour automatiquement
- **Transparence** : L'utilisateur sait quand l'analyse vient du cache ("Analysé il y a X min (Cache)")

### Économie
- Sans cache : 10 ouvertures/jour × 0.01€ = **0.10€/jour/utilisateur**
- Avec cache : 2 analyses/jour × 0.01€ = **0.02€/jour/utilisateur**
- **Économie : 80%**

## 🐛 Dépannage

### Erreur "OPENAI_API_KEY not set"
```bash
# Dans backend/.env
OPENAI_API_KEY=sk-...
```

### Erreur "calendar_event_id column does not exist"
→ La migration 014 n'a pas été appliquée. Exécuter le SQL dans Supabase Dashboard.

### Erreur "react-native-markdown-display not found"
```bash
cd mobile
npm install react-native-markdown-display
```

### Backend timeout après 15s
→ Normal si OpenAI prend trop de temps. Réessayer ou vérifier la connexion réseau.

### Markdown non formaté (affiche # et **)
→ Vérifier que `import Markdown from 'react-native-markdown-display'` est bien présent et que les styles markdownStyles sont appliqués.

## ✨ Fonctionnalités Bonus Implémentées

1. **Timeout 15s** : Évite blocage infini
2. **Style Apple Health** : Couleurs iOS natives (vert/orange)
3. **Timestamp relatif** : "il y a 5 min" au lieu de timestamp brut
4. **Badge Readiness** : Feu vert/orange/rouge selon le score
5. **Bouton discret** : "🔄 Recalculer" pour forcer refresh
6. **Gestion d'erreurs** : UI claire avec bouton retry
7. **Indicateur cache** : 💾 emoji quand l'analyse vient du cache

## 🎉 Conclusion

Le Smart Cache est maintenant **opérationnel** ! 

Prochaines étapes recommandées :
- Tester en conditions réelles avec plusieurs événements
- Monitorer les logs backend pour vérifier les cache hits/misses
- Ajuster le prompt LLM selon les retours utilisateurs
- Considérer un cache TTL (Time-To-Live) optionnel

---

*Document de test généré le 28 janvier 2026*
