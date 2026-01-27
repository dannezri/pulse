# Test 3 : Qualité des Insights IA

Ce test vérifie la pertinence des conseils générés par l'IA pour différents scénarios de vie.

## 🎯 Objectif

Tester que l'IA génère des conseils **intelligents et pertinents** selon différents profils de santé (personas), et non pas juste des réponses génériques.

## 📋 Scénarios Testés

### 1. "Le Burnout imminent"
- **HRV très bas** : 42 ms (chute de 35% par rapport à baseline 65 ms)
- **Sommeil catastrophique** : 5h seulement (baseline 450 min = 7h30)
- **Rythme cardiaque au repos élevé** : 72 bpm (baseline 58 bpm)
- **Activité réduite** : 2000 pas

**Attendu** : L'IA devrait recommander de la récupération urgente (sommeil, réduction du stress, repos).

### 2. "L'Athlète en forme"
- **HRV haut** : 80 ms (au-dessus de baseline 75 ms)
- **Sommeil parfait** : 8h30 (510 min, baseline 480 min)
- **Rythme cardiaque au repos excellent** : 50 bpm (baseline 52 bpm)
- **Activité physique élevée** : 15000 pas

**Attendu** : L'IA devrait reconnaître l'excellent état de forme et peut-être suggérer de maintenir ou optimiser.

### 3. "Le sédentaire stressé"
- **HRV moyen** : 58 ms (légèrement en dessous de baseline 60 ms)
- **HR élevé pendant 2h** : 85-92 bpm (réunion stressante)
- **Pas de pas** : 500 pas seulement (sédentaire)
- **Sommeil moyen** : 6h40 (400 min)

**Attendu** : L'IA devrait recommander de l'activité physique et de la gestion du stress.

## 🚀 Utilisation

### Prérequis

1. **Configuration Supabase** :
   ```bash
   export SUPABASE_URL=https://your-project.supabase.co
   export SUPABASE_SERVICE_KEY=your_supabase_service_role_key
   ```

2. **Configuration OpenAI** :
   ```bash
   export OPENAI_API_KEY=your_openai_api_key
   ```

3. **Installation des dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

### Exécution

```bash
cd backend
python test_ai_insights_quality.py
```

### Résultat Attendu

Le script va :
1. ✅ Créer 3 profils utilisateurs (personas) dans Supabase
2. ✅ Injecter des données biométriques historiques et du jour
3. ✅ Calculer les baselines et créer les profils de santé
4. ✅ Générer un insight IA pour chaque persona
5. ✅ Afficher les résultats et sauvegarder les insights dans la base

**Exemple de sortie** :
```
🧪 TEST : Le Burnout imminent
📝 Création du profil...
✅ Profil créé
📊 Profil de santé : {...}
🤖 Génération de l'insight IA...
💡 INSIGHT GÉNÉRÉ :
   Catégorie : recovery
   Priorité : 🔴 URGENT
   Conseil : Ton HRV chute de 35% et ton sommeil est en déficit de 2h30. 
            Prends 20 min de méditation maintenant, puis couche-toi avant 22h. 
            Tu récupéreras mieux et éviteras le burnout.
```

## 🔍 Vérification de la Qualité

Pour chaque persona, vérifiez que :

1. **Le conseil est spécifique** (pas générique comme "Fais du sport")
2. **Le conseil est actionnable** (action concrète avec timing)
3. **Le conseil correspond au scénario** :
   - Burnout → Récupération urgente
   - Athlète → Optimisation/maintenance
   - Sédentaire stressé → Activité + gestion stress
4. **La catégorie est correcte** (recovery, movement, stress, nutrition)
5. **La priorité est adaptée** (urgent pour burnout, normal pour athlète)

## 📊 Analyse des Résultats

Les insights sont sauvegardés dans la table `insights` de Supabase. Vous pouvez :

1. **Vérifier dans Supabase** :
   ```sql
   SELECT i.*, p.full_name 
   FROM insights i
   JOIN profiles p ON i.user_id = p.id
   ORDER BY i.created_at DESC;
   ```

2. **Comparer les conseils** entre les 3 personas pour vérifier la différenciation

3. **Vérifier la cohérence** avec les anomalies détectées dans les profils de santé

## 🐛 Dépannage

### Erreur : "OpenAI API key required"
- Vérifiez que `OPENAI_API_KEY` est défini dans votre environnement

### Erreur : "User not found"
- Vérifiez que `SUPABASE_URL` et `SUPABASE_SERVICE_KEY` sont corrects

### Les insights sont génériques
- Vérifiez que le prompt système dans `prompt.md` est bien utilisé
- Vérifiez que les profils de santé contiennent bien les anomalies détectées

### Les baselines ne sont pas calculées
- Vérifiez que les données historiques sont bien créées (7 jours minimum)
- Vérifiez que les métriques sont dans le bon format (hrv, hr, sleep_duration)

## 📝 Notes

- Les personas créées sont des utilisateurs de test (UUID aléatoires)
- Les données sont injectées directement dans Supabase (pas via Open Wearables)
- Le test utilise `gpt-4o-mini` par défaut (plus économique), modifiable via `OPENAI_MODEL`
