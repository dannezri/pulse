# 🔄 Redémarrage Backend pour Effets Horaires

## 📋 Checklist

### ✅ 1. Cache Invalidé
```sql
DELETE FROM medication_analysis_cache
WHERE user_id = 'c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd';
```
**Statut** : ✅ FAIT

### ⏳ 2. Redémarrer le Backend

**Terminal 2** est déjà en train d'exécuter `./restart_api_server.sh`

Pour forcer un redémarrage :
```bash
# Dans le terminal 2 (backend)
Ctrl+C  # Arrêter le serveur actuel
./restart_api_server.sh  # Redémarrer
```

Ou dans un nouveau terminal :
```bash
cd /Users/dannezri/Desktop/Pulse/backend
./restart_api_server.sh
```

### ⏳ 3. Tester l'API

Une fois le backend redémarré, testez manuellement :

```bash
curl -X GET \
  "http://192.168.0.23:9000/api/medications/analyze/c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd" \
  -H "Authorization: Bearer c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd" \
  -H "Content-Type: application/json" \
  | python3 -m json.tool
```

**Attendu** :
```json
{
  "analyse_traitements": [
    {
      "nom": "VENLAFAXINE ARROW GENERIQUES LP 37,5 mg",
      "intro_explicative": "...",
      "impact_corps": "...",
      "impact_journee": "...",
      "observation": "...",
      "effets_horaires": [
        {
          "heure": "00:00",
          "concentration": 85,
          "efficacite": 90,
          "effets_secondaires": 10,
          "description": "Effet stable pendant la nuit"
        },
        // ... 23 autres heures
      ]
    }
  ],
  "_cost": 0.015,
  "_generated_at": "2026-02-06T...",
  "_medications_count": 2
}
```

### ⏳ 4. Recharger l'App Mobile

Dans Metro (terminal 33) :
- Appuyez sur `r` pour reload
- Ou secouez l'appareil → Reload

### ⏳ 5. Vérifier dans l'App

1. Ouvrir l'écran **Médicaments**
2. Appuyer sur un médicament pour déplier
3. Scroller jusqu'à **"Profil d'efficacité sur 24h"**
4. Vérifier que le graphique s'affiche avec :
   - 3 barres par heure (bleu, vert, orange)
   - Indicateur 💊 à l'heure de prise
   - Légende en haut
   - Scrollable horizontalement

## 🔍 Logs à Surveiller

### Backend (terminal 2)
```
INFO: Calling Gemini 3 Pro...
INFO: ✅ Generated analysis for 2 medications
INFO: 💰 Cost: $0.01XX USD
INFO: 💾 Stored analysis in cache
```

### Mobile (terminal 33)
```
LOG  [useMedicationAnalysis] 📡 Fetching analysis from: http://192.168.0.23:9000/api/medications/analyze/...
LOG  [useMedicationAnalysis] ✅ Analysis received: {...}
LOG  [Medications] 🔎 Recherche analyse pour "VENLAFAXINE...": ✅ Trouvée
LOG  [Medications]    ↳ Matché avec: "VENLAFAXINE ARROW GENERIQUES LP 37,5 mg"
```

## 🐛 Si ça ne marche pas

### Problème 1 : Backend ne redémarre pas
```bash
# Tuer tous les processus Python
pkill -f "python.*api_server.py"
sleep 2
cd /Users/dannezri/Desktop/Pulse/backend
python3 api_server.py
```

### Problème 2 : Gemini ne génère pas les effets horaires
- Vérifier que `GOOGLE_API_KEY` est défini :
  ```bash
  echo $GOOGLE_API_KEY
  ```
- Vérifier les logs backend pour les erreurs Gemini

### Problème 3 : Le graphique ne s'affiche pas
- Ouvrir les DevTools React Native
- Vérifier que `analysis.effets_horaires` existe et contient 24 éléments
- Vérifier les logs : `[Medications] 🔍 Debug Analyses Gemini`

### Problème 4 : Erreur de parsing JSON
- Gemini peut parfois retourner du texte avant/après le JSON
- Vérifier `gemini_client.py` ligne ~80 pour le parsing

## 📝 Commandes Rapides

```bash
# Redémarrer backend
cd /Users/dannezri/Desktop/Pulse/backend && ./restart_api_server.sh

# Tester API
curl -H "Authorization: Bearer c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd" \
  http://192.168.0.23:9000/api/medications/analyze/c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd

# Invalider cache
psql $DATABASE_URL -c "DELETE FROM medication_analysis_cache WHERE user_id = 'c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd';"

# Recharger app
# Dans Metro : appuyez sur 'r'
```

## ✅ Succès !

Si tout fonctionne, vous verrez :
1. ✅ Backend génère les analyses avec `effets_horaires`
2. ✅ Mobile reçoit les données
3. ✅ Graphique s'affiche dans la section dépliée
4. ✅ Les 3 barres (concentration, efficacité, effets 2nd) sont visibles
5. ✅ L'indicateur 💊 marque l'heure de prise
