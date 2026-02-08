# 🚀 Quick Start - Tests de Validation

**5 minutes pour valider l'intégration complète**

---

## ✅ Test 1 : Sync Oura (2 min)

```bash
cd /Users/dannezri/Desktop/Pulse/backend
python3 test_oura_sync.py
```

**Vérifier** :
- ✅ Token Oura trouvé
- ✅ Readiness Score récupéré
- ✅ health_profiles mis à jour
- ✅ Modèle Pulse Energy Decay généré
- ✅ Influencers affichés

**Si erreur "No Oura token found"** :
```python
# Le token est déjà dans le script test_oura_sync.py
OURA_TOKEN = "IX6RMKRCMIJOVZMIB2IKVL2PWUQOCNNI"
```

---

## ✅ Test 2 : API Endpoint (1 min)

**Backend en cours d'exécution ?**
```bash
# Dans un terminal séparé
cd /Users/dannezri/Desktop/Pulse/backend
python3 api_server.py
```

**Tester l'endpoint** :
```bash
# Nouveau terminal
curl "http://localhost:9000/api/energy/intraday?model=pulse_energy_decay&force_refresh=true" \
  -H "Authorization: Bearer c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd" \
  | jq .
```

**Vérifier** :
- ✅ `"type": "pulse_energy_decay"`
- ✅ `"current_energy"` présent
- ✅ `"influencers"` avec 4 éléments
- ✅ `"forecast_curve"` avec 32 points

---

## ✅ Test 3 : Mobile App (1 min)

**Sur votre iPhone** :
1. Ouvrir l'app Pulse
2. Secouer l'iPhone
3. Appuyer sur "Reload"
4. Naviguer vers "Énergie – reste de la journée"

**Vérifier** :
- ✅ Section "FACTEURS CLÉS" visible
- ✅ 4 influencers affichés :
  - 🟢 Sommeil (Readiness)
  - 🔴 HRV Anomaly
  - 🟢 Médicament (Caféine)
  - 🔴 Condition (Fatigue)
- ✅ Markers colorés sur la courbe

---

## ✅ Test 4 : Cron Job (30 sec)

```bash
cd /Users/dannezri/Desktop/Pulse/backend
python3 cron_oura_daily_sync.py
```

**Vérifier** :
- ✅ `Success: 1`
- ✅ `Errors: 0`
- ✅ Durée < 3s

---

## ✅ Test 5 : Vérification DB (30 sec)

**Via MCP Supabase** (ou pgAdmin) :
```sql
SELECT 
  date,
  current_metrics->>'readiness_score' as readiness,
  current_metrics->>'hrv_ms' as hrv,
  jsonb_array_length(anomalies) as nb_anomalies
FROM health_profiles
WHERE user_id = 'c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd'
  AND date = CURRENT_DATE;
```

**Résultat attendu** :
```
date       | readiness | hrv | nb_anomalies
-----------|-----------|-----|-------------
2026-01-31 | 87        | 65  | 1
```

---

## 🐛 Dépannage Rapide

### Erreur: "No Oura token found"
**Solution** : Vérifier `external_identities.metadata.access_token`
```sql
UPDATE external_identities
SET metadata = jsonb_set(metadata, '{access_token}', '"IX6RMKRCMIJOVZMIB2IKVL2PWUQOCNNI"')
WHERE supabase_user_id = 'c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd'
  AND provider_system = 'oura';
```

### Erreur: "Could not generate intraday forecast"
**Solution** : Vérifier que `daily_energy` existe
```sql
SELECT * FROM daily_energy 
WHERE user_id = 'c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd' 
AND energy_date = CURRENT_DATE;
```

### Mobile: Carte ne s'affiche pas
**Solution** :
1. Vérifier backend logs : `[PulseEnergyDecay] E0 calculated`
2. Vérifier React Query cache : Reload app
3. Vérifier console Metro : Chercher `[EnergyOverviewCard]`

---

## 📊 Statut Final

Si les 5 tests passent :
- ✅ **Sync Oura** opérationnel
- ✅ **Modèle V2** fonctionnel
- ✅ **API** responsive
- ✅ **Mobile** intégré
- ✅ **Cron** prêt

**🎉 L'intégration est COMPLÈTE !**

---

## 🚀 Prochaine Étape

**Configurer le cron en production** :
```bash
crontab -e

# Ajouter (08:00 UTC = 09:00 Paris)
0 8 * * * cd /Users/dannezri/Desktop/Pulse/backend && /usr/local/bin/python3 cron_oura_daily_sync.py >> /var/log/oura_sync.log 2>&1
```

**Créer le log** :
```bash
sudo touch /var/log/oura_sync.log
sudo chown $USER /var/log/oura_sync.log
```

**Tester demain matin à 09:00** :
```bash
tail -f /var/log/oura_sync.log
```

---

**Temps total de validation : ~5 minutes** ⏱️
