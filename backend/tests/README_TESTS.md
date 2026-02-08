# Guide des Tests - Latent States System

## Configuration des Variables d'Environnement

Les tests d'intégration nécessitent un accès à Supabase. Vous devez créer un fichier `.env` dans le dossier `backend/`.

### Étape 1 : Créer le fichier .env

```bash
cd /Users/dannezri/Desktop/Pulse/backend
cp config.example.env .env
```

### Étape 2 : Remplir les variables

Éditez le fichier `.env` avec vos vraies valeurs :

```bash
# Supabase Configuration
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_SERVICE_KEY=votre-service-role-key
SUPABASE_ANON_KEY=votre-anon-key

# OpenAI Configuration (nécessaire pour les tests de génération de brief)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# Autres variables (optionnelles pour les tests)
CRON_SECRET=your-secret-here
PORT=9000
```

**Important** : 
- Utilisez `SUPABASE_SERVICE_KEY` (pas `SUPABASE_KEY`)
- Le service key a les permissions complètes (nécessaire pour les tests)

### Étape 3 : Trouver vos clés Supabase

1. Allez sur [supabase.com](https://supabase.com)
2. Sélectionnez votre projet
3. Allez dans **Settings** → **API**
4. Copiez :
   - **Project URL** → `SUPABASE_URL`
   - **service_role** key (sous "Project API keys") → `SUPABASE_SERVICE_KEY`

## Lancer les Tests

### Tests Unitaires (sans Supabase)

```bash
cd backend
python3 -m pytest tests/test_latent_states.py -v
```

**Attendu** : 29/29 tests passent ✅

### Tests d'Intégration (avec Supabase)

```bash
cd backend
python3 tests/test_integration_latent_states.py
```

**Ou avec un user_id spécifique** :

```bash
python3 tests/test_integration_latent_states.py --user-id c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd
```

**Attendu** : 5/5 tests passent ✅

### Structure des Tests d'Intégration

1. **Database Migration** - Vérifie que la table `daily_state` existe
2. **Latent State Calculation** - Calcule les 4 états latents pour un utilisateur
3. **AI Prompt Integration** - Vérifie que les états sont dans le prompt LLM
4. **Brief Generation** - Génère un brief complet avec l'IA
5. **Medical Disclaimers (CRITICAL)** - Vérifie les disclaimers dans les cartes alert

## Résolution des Problèmes

### Erreur : "SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables must be set"

**Solution** : Créez le fichier `.env` comme indiqué ci-dessus.

### Erreur : "daily_state table not found"

**Solution** : La migration n'a pas été appliquée. Elle a normalement été appliquée via MCP, mais si besoin :

```bash
psql -U your_user -d your_db -f database/migrations/016_daily_state.sql
```

### Erreur : "No users found in database"

**Solution** : Votre base de données Supabase est vide. Créez un utilisateur test ou utilisez `--user-id` avec un UUID existant.

### Tests d'intégration très lents

**Normal** : Les tests appellent l'API OpenAI GPT-4o, ce qui peut prendre 10-30 secondes par génération.

### Erreur OpenAI API

Si vous n'avez pas de clé OpenAI valide, les tests 4 et 5 échoueront. Les tests 1-3 passeront quand même.

## Structure des Fichiers de Test

```
backend/tests/
├── test_latent_states.py              # Tests unitaires (29 tests)
├── test_integration_latent_states.py  # Tests d'intégration (5 tests)
└── README_TESTS.md                    # Ce fichier
```

## CI/CD

Pour intégrer ces tests dans votre CI/CD :

```yaml
# .github/workflows/test.yml
env:
  SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
  SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

steps:
  - name: Run Unit Tests
    run: python3 -m pytest backend/tests/test_latent_states.py -v
  
  - name: Run Integration Tests
    run: python3 backend/tests/test_integration_latent_states.py
```

---

**Questions ?** Consultez `LATENT_STATES_IMPLEMENTATION_SUMMARY.md` pour plus de détails.
