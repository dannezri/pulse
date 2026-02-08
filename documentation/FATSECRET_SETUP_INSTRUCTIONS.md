# FatSecret Setup - Instructions rapides ⚡

## 🎯 Architecture (Option 1 - Profile-based)

Au lieu du flow OAuth 3-legged complexe, on utilise `profile.create` :
- Créer un profil FatSecret vide pour chaque utilisateur Pulse
- L'utilisateur enregistre ses repas via l'app Pulse
- Les données sont stockées dans FatSecret et synchronisées

**Avantage :** Pas besoin que l'utilisateur ait déjà un compte FatSecret !

---

## 📋 Setup en 3 étapes

### Étape 1: Appliquer la migration SQL (1 min)

1. Ouvrir https://supabase.com/dashboard
2. Sélectionner votre projet Pulse  
3. Aller dans "SQL Editor"
4. Copier/coller le contenu de `database/migrations/018_fatsecret_integration.sql`
5. Cliquer sur "Run"

✅ **Vérification:** Les tables `fatsecret_connections` et `food_entries_raw` sont créées

---

### Étape 2: Créer un profil FatSecret pour un utilisateur (30 sec)

```bash
cd backend
python3 setup_fatsecret.py
```

Choisir option "1", entrer l'UUID de l'utilisateur.

Le script va :
- Créer un profil FatSecret vide
- Générer auth_token + auth_secret
- Stocker dans Supabase

✅ **Résultat:** Le profil est prêt !

---

### Étape 3: Tester la synchronisation

```bash
python3 sync_fatsecret_food_entries.py --user-id "UUID_USER" --days-back 7
```

(Le profil est vide pour l'instant, donc 0 entrées trouvées - c'est normal !)

---

## 🧪 Test complet

### Test 1: Rechercher un aliment

```bash
python3 -c "
from dotenv import load_dotenv
load_dotenv()

from fatsecret_client import get_fatsecret_client

client = get_fatsecret_client()
results = client.search_foods('banana')

foods = results.get('foods', {}).get('food', [])
print(f'Trouvé {len(foods)} aliments pour \"banana\"')
print(f'Premier résultat: {foods[0][\"food_name\"]}')
"
```

### Test 2: Créer une entrée alimentaire

```bash
python3 -c "
from dotenv import load_dotenv
load_dotenv()

from fatsecret_client import get_fatsecret_client
import datetime as dt

# Récupérer les credentials du profil depuis Supabase
# (Remplacer par les vraies valeurs)
client = get_fatsecret_client(
    oauth_token='votre_auth_token',
    oauth_secret='votre_auth_secret'
)

# Créer une entrée
result = client.create_food_entry(
    food_id=45,  # ID d'un aliment (ex: banana)
    serving_id=100,  # ID de la portion
    num_servings=1.0,
    meal='breakfast',
    date=dt.date.today()
)

print(f'Entrée créée: {result}')
"
```

### Test 3: Récupérer les entrées

```bash
python3 -c "
from dotenv import load_dotenv
load_dotenv()

from fatsecret_client import get_fatsecret_client
import datetime as dt

client = get_fatsecret_client(
    oauth_token='votre_auth_token',
    oauth_secret='votre_auth_secret'
)

entries = client.get_food_entries_for_date(dt.date.today())
print(f'Entrées du jour: {entries}')
"
```

---

## 🚀 Prochaines étapes

### Phase 1: Backend (✅ FAIT)
- [x] Migration SQL
- [x] Client FatSecret fonctionnel
- [x] Script de création de profil
- [x] Script de synchronisation

### Phase 2: API Endpoints (EN COURS)
- [ ] POST `/api/fatsecret/connect` - Créer profil
- [ ] GET `/api/fatsecret/status` - Vérifier profil
- [ ] GET `/api/fatsecret/search-foods` - Rechercher aliments
- [ ] POST `/api/fatsecret/add-food-entry` - Ajouter repas
- [ ] GET `/api/fatsecret/food-entries` - Lister repas
- [ ] DELETE `/api/fatsecret/food-entry/:id` - Supprimer repas

### Phase 3: Interface Mobile
- [ ] Écran "Alimentation"
- [ ] Recherche d'aliments
- [ ] Ajout de repas (formulaire)
- [ ] Liste des repas (par jour/semaine)
- [ ] Statistiques nutritionnelles

---

## 📝 Différences avec Oura

| Aspect | Oura | FatSecret |
|--------|------|-----------|
| Authentification | Personal Access Token | Profile (auth_token + auth_secret) |
| Données source | Oura Ring (capteur) | Saisie manuelle via app |
| Type de données | Biométriques (sommeil, HRV) | Alimentaires (repas, calories) |
| Synchronisation | Pull (API → Supabase) | Pull + Push (bi-directionnel) |
| Setup utilisateur | Token unique | Profil individuel |

---

## 🔧 Troubleshooting

### "Table fatsecret_connections not found"
→ Appliquer la migration SQL (Étape 1)

### "FATSECRET_CONSUMER_KEY manquante"
→ Ajouter les credentials dans `backend/.env`:
```bash
FATSECRET_CONSUMER_KEY=votre_key
FATSECRET_CONSUMER_SECRET=votre_secret
```

### "Invalid access token"
→ Le profil n'a pas encore de données. Ajoutez une entrée d'abord.

---

## 📚 Documentation complète

- **Guide complet:** `backend/FATSECRET_INTEGRATION.md`
- **Flow correct:** `backend/FATSECRET_CORRECT_FLOW.md`
- **API FatSecret:** https://platform.fatsecret.com/api/

---

**Statut:** ✅ Backend fonctionnel, prêt pour les endpoints API !
