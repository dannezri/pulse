# Wellness Coach AI Integration - Documentation

## Vue d'ensemble

Le système Wellness Coach utilise OpenAI GPT-4o pour générer des cartes Brief pédagogiques et empathiques basées sur les données biométriques de l'utilisateur. Un système de cache intelligent optimise les coûts et la performance.

## Architecture

```
Mobile App → API Backend → AIAnalysisService → Cache/OpenAI → BriefCards
```

### Flux de Données

1. **Mobile** : L'utilisateur ouvre l'onglet Brief
2. **useBriefData()** : Appelle `/api/v1/generate-brief`
3. **Backend** : Vérifie le cache dans `insights` table
   - **Cache HIT** : Retourne les cartes sauvegardées (< 500ms, 0€)
   - **Cache MISS** : Appelle GPT-4o avec le prompt Wellness Coach (~3s, ~$0.01)
4. **Mobile** : Affiche les cartes avec animations et couleurs

## Fichiers Modifiés

### Backend

- **`backend/services/ai_service.py`** : Nouvelle méthode `generate_brief()`
- **`backend/llm_client.py`** : Nouvelle méthode `generate_wellness_brief()`
- **`backend/api_server.py`** : Nouvel endpoint `POST /api/v1/generate-brief`

### Frontend

- **`mobile/src/services/briefApi.ts`** : Service API pour appeler le backend
- **`mobile/src/hooks/useBriefData.ts`** : Refactorisé pour utiliser l'API
- **`mobile/src/components/BriefCard.tsx`** : Déjà configuré pour les états alert/warning/optimal

### Test

- **`backend/test_wellness_coach.py`** : Script de validation

## Utilisation

### 1. Configuration Backend

Assurez-vous que les variables d'environnement sont configurées :

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
SUPABASE_URL=https://...
SUPABASE_SERVICE_KEY=...
```

### 2. Lancer le Backend

```bash
cd backend
python3 api_server.py
```

Le serveur démarre sur `http://localhost:8000`.

### 3. Tester l'API

```bash
# Test avec curl
curl -X POST http://localhost:8000/api/v1/generate-brief \
  -H "Content-Type: application/json" \
  -d '{"user_id": "votre-uuid", "force_refresh": false}'
```

### 4. Configurer le Mobile

Assurez-vous que `mobile/src/config/api.ts` pointe vers votre backend :

```typescript
export const API_URL = 'http://YOUR_IP:8000'; // ou ngrok URL
```

### 5. Lancer l'App Mobile

```bash
cd mobile
npx expo start
```

## Tests de Validation

### Test 1 : Système de Cache

```bash
cd backend
export TEST_USER_ID=<votre-uuid>
python3 test_wellness_coach.py
```

**Comportement attendu** :
- ✅ Premier appel : `cached: false`, durée ~3s
- ✅ Deuxième appel : `cached: true`, durée < 500ms
- ✅ Force refresh : `cached: false`, ignore le cache

### Test 2 : États et Couleurs

Le système utilise ces règles :

| Score Pulse | Timing | État Résultant | Couleur | Glow |
|-------------|--------|----------------|---------|------|
| < 60 | N/A | `alert` | Rouge | #FF3B30 |
| N/A | < 30 | `alert` | Rouge | #FF3B30 |
| 60-75 | ≥ 30 | `warning` | Orange | #FF9500 |
| > 75 | ≥ 30 | `optimal` | Vert | #34C759 |

**Vérification visuelle** :
1. Ouvrir l'app mobile
2. Aller dans l'onglet "Brief"
3. Observer les couleurs des cartes
4. Vérifier que les cartes "alert" ont un glow rouge intense

### Test 3 : Contenu Pédagogique

**Analogies attendues** :
- 🔋 "batterie" → Énergie globale
- 🚗 "moteur" → Système cardiovasculaire
- ⏰ "horloge" → Rythme circadien
- ⛽ "carburant" → Nutrition

**Vérifier manuellement** :
1. Lire le contenu des cartes
2. Chercher les analogies
3. Vérifier que le ton est empathique et direct
4. Confirmer que les actions sont concrètes ("Marchez 10 min", "Reposez-vous")

## Format de Réponse API

```json
{
  "status": "success",
  "pulseScore": 58,
  "cached": false,
  "analyzed_at": "2024-01-15T09:30:00Z",
  "biometrics_ref_at": "2024-01-15T09:25:00Z",
  "cards": [
    {
      "id": "verdict",
      "type": "verdict",
      "title": "Le bilan du coach",
      "content": "Dan, votre **batterie physique** est pleine, mais votre **moteur** est décalé...",
      "state": "warning",
      "iconName": "Activity",
      "badge": 58,
      "priority": 100,
      "actionButton": {
        "label": "Voir détails",
        "action": "view_details"
      }
    }
  ]
}
```

## Dépannage

### Problème : "Error calling LLM"

**Solution** :
- Vérifier `OPENAI_API_KEY` dans `.env`
- Vérifier les crédits OpenAI

### Problème : "Cache ne fonctionne pas"

**Solution** :
- Vérifier que la table `insights` existe
- Vérifier que `category="brief_daily"` est bien utilisé
- Vérifier les logs backend : `[generate-brief] Cache hit/miss`

### Problème : "Timeout 504"

**Solution** :
- Augmenter le timeout dans `api_server.py` (ligne `timeout=20.0`)
- Vérifier la connexion à OpenAI
- Réduire `max_tokens` dans le prompt

### Problème : "Cartes ne s'affichent pas"

**Solution** :
- Vérifier `API_URL` dans `mobile/src/config/api.ts`
- Vérifier que le backend est démarré
- Vérifier les logs console du mobile : `Error fetching Brief from API`
- Vérifier que l'utilisateur a des données biométriques

## Performance

### Coûts Estimés

- **Premier appel** (génération) : ~$0.01 (GPT-4o)
- **Appels cachés** : $0.00
- **Coût journalier par utilisateur** : ~$0.01-0.03 (selon fréquence de refresh)

### Temps de Réponse

- **Cache HIT** : < 500ms
- **Cache MISS** : 2-4 secondes
- **Avec connexion lente** : Jusqu'à 8 secondes (timeout à 20s)

### Optimisations

- **Cache intelligent** : Ne rappelle l'IA que si nouvelles biométriques
- **Stale time** : 5 minutes de cache React Query côté mobile
- **Compression JSON** : Markdown au lieu de HTML

## Prochaines Améliorations

- [ ] Ajouter des graphiques dans les cartes
- [ ] Intégrer les événements calendrier dans le prompt
- [ ] Personnaliser les analogies selon le profil utilisateur
- [ ] Ajouter un système de feedback ("Cette carte m'a été utile")
- [ ] Implémenter un système de suggestions d'actions interactives

## Support

Pour toute question ou problème :
1. Consulter les logs backend : `tail -f backend/logs/api_server.log`
2. Consulter les logs mobile : Console Expo
3. Exécuter le script de test : `python3 test_wellness_coach.py`
