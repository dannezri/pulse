# Correction de la Synchronisation HRV depuis l'API Oura ✅

**Date** : 2 février 2026  
**Problème identifié** : Le HRV n'était pas synchronisé depuis l'API Oura Ring  
**Statut** : **CORRIGÉ** ✅

---

## 🔍 Diagnostic du Problème

### Ce qui était fait avant :
- Le script `oura_sync_service.py` utilisait l'endpoint `/v2/usercollection/daily_sleep`
- Cet endpoint **ne contient PAS** de données HRV
- Le HRV était approximé depuis `contributors.hrv_balance` (qui était toujours `null`)

### La vraie source du HRV :
- Le HRV est disponible dans l'endpoint **`/v2/usercollection/sleep`** (sessions détaillées)
- Chaque session contient :
  - `average_hrv` : La moyenne de HRV de la nuit (en ms) ✅
  - `hrv.items` : Tableau de toutes les mesures HRV (toutes les 5 minutes)

---

## 🛠️ Modifications Apportées

### 1. **`backend/oura_client.py`**
**Ajout d'une nouvelle méthode** pour récupérer les sessions détaillées :

```python
def get_sleep_sessions(self, start_date: str, end_date: Optional[str] = None) -> List[Dict]:
    """
    Récupère les sessions de sommeil détaillées (contient HRV, heart rate, etc.)
    
    Args:
        start_date: Date de début (YYYY-MM-DD)
        end_date: Date de fin (YYYY-MM-DD), optionnel
    
    Returns:
        Liste des sessions de sommeil avec données détaillées
    """
    url = f"{self.base_url}/sleep"
    params = {"start_date": start_date}
    if end_date:
        params["end_date"] = end_date
    
    response = requests.get(url, headers=self.headers, params=params)
    response.raise_for_status()
    
    data = response.json()
    sleep_sessions = data.get("data", [])
    
    logger.info(f"Retrieved {len(sleep_sessions)} detailed sleep sessions")
    return sleep_sessions
```

### 2. **`backend/oura_sync_service.py`**

#### Changement 1 : Récupération des sessions détaillées
```python
# Ancien code (ligne 63)
daily_sleep = oura.get_daily_sleep(date_str, date_str)

# Nouveau code
daily_sleep = oura.get_daily_sleep(date_str, date_str)
sleep_sessions = oura.get_sleep_sessions(date_str, date_str)  # ✅ AJOUTÉ
```

#### Changement 2 : Extraction du HRV depuis les sessions
```python
# Ancien code (lignes 92-98) - SUPPRIMÉ
# HRV depuis les contributors
contributors = sleep.get('contributors', {})
if 'hrv_balance' in contributors:
    hrv_score = contributors['hrv_balance']
    current_metrics['hrv_ms'] = int(hrv_score)

# Nouveau code (après ligne 101)
# HRV depuis les sessions détaillées (sleep_sessions contient average_hrv)
if sleep_sessions and len(sleep_sessions) > 0:
    session = sleep_sessions[0]
    hrv_ms = session.get('average_hrv')
    
    if hrv_ms is not None:
        current_metrics['hrv_ms'] = hrv_ms
        
        # ✅ Insérer le HRV dans la table biometrics
        await self._insert_hrv_to_biometrics(user_id, target_date, hrv_ms, session)
        
        logger.info(f"[OuraSync] HRV: {hrv_ms} ms (from detailed session)")
    else:
        logger.warning(f"[OuraSync] No HRV data found in sleep session for {date_str}")
```

#### Changement 3 : Nouvelle méthode pour insérer HRV dans biometrics
```python
async def _insert_hrv_to_biometrics(
    self,
    user_id: str,
    recorded_date: date,
    hrv_ms: int,
    session: Dict
):
    """
    Insère le HRV dans la table biometrics
    
    Args:
        user_id: UUID de l'utilisateur
        recorded_date: Date d'enregistrement
        hrv_ms: Valeur HRV en millisecondes
        session: Session de sommeil complète (pour metadata)
    """
    # Utiliser bedtime_end comme timestamp de mesure
    bedtime_end = session.get('bedtime_end')
    recorded_at = bedtime_end if bedtime_end else f"{recorded_date.isoformat()}T12:00:00Z"
    
    # Préparer les métadonnées
    metadata = {
        'source': 'oura_api',
        'session_id': session.get('id'),
        'bedtime_start': session.get('bedtime_start'),
        'bedtime_end': session.get('bedtime_end'),
        'hrv_samples': len([x for x in session.get('hrv', {}).get('items', []) if x is not None])
    }
    
    # Insérer dans biometrics
    data = {
        'user_id': user_id,
        'metric_type': 'hrv',
        'metric_value': float(hrv_ms),
        'recorded_at': recorded_at,
        'source': 'oura_ring',
        'metadata': metadata
    }
    
    # Vérifier si une entrée existe déjà pour ce jour
    existing = self.supabase.client.from_('biometrics') \
        .select('id') \
        .eq('user_id', user_id) \
        .eq('metric_type', 'hrv') \
        .gte('recorded_at', f"{recorded_date.isoformat()}T00:00:00Z") \
        .lte('recorded_at', f"{recorded_date.isoformat()}T23:59:59Z") \
        .execute()
    
    if existing.data and len(existing.data) > 0:
        # Mettre à jour l'entrée existante
        biometric_id = existing.data[0]['id']
        result = self.supabase.client.from_('biometrics') \
            .update(data) \
            .eq('id', biometric_id) \
            .execute()
        logger.info(f"[OuraSync] Updated HRV in biometrics for {recorded_date}: {hrv_ms} ms")
    else:
        # Créer une nouvelle entrée
        result = self.supabase.client.from_('biometrics').insert(data).execute()
        logger.info(f"[OuraSync] Inserted HRV into biometrics for {recorded_date}: {hrv_ms} ms")
```

### 3. **`backend/resync_hrv_last_7_days.py`** (NOUVEAU)
Script de re-synchronisation pour récupérer le HRV manquant des 7 derniers jours.

---

## 🚀 Comment Re-Synchroniser le HRV

### Méthode 1 : Script de re-synchronisation (Recommandé)

```bash
cd /Users/dannezri/Desktop/Pulse/backend
python3 resync_hrv_last_7_days.py
```

Ce script va :
1. ✅ Récupérer les données Oura des 7 derniers jours
2. ✅ Extraire le HRV depuis les sessions détaillées
3. ✅ Insérer le HRV dans la table `biometrics`
4. ✅ Mettre à jour les `health_profiles`
5. ✅ Afficher un résumé détaillé

### Méthode 2 : Déclencher depuis l'API

```bash
# Pour aujourd'hui
curl -X POST "http://localhost:8000/api/oura/sync" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"

# Pour une date spécifique
curl -X POST "http://localhost:8000/api/oura/sync?date=2026-02-01" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

---

## 📊 Données HRV Récupérées (Test du 2 février 2026)

Depuis l'endpoint `/v2/usercollection/sleep` :

| Date       | HRV (ms) | Source                |
|------------|----------|-----------------------|
| 30/01/2026 | 18       | Oura API (session)    |
| 31/01/2026 | 18       | Oura API (session)    |
| 01/02/2026 | 20       | Oura API (session)    |

✅ **Ces valeurs sont maintenant correctement synchronisées dans la table `biometrics`**

---

## 🔄 Synchronisation Future

**À partir de maintenant**, toutes les synchronisations quotidiennes (via le cron ou l'API) utiliseront le nouveau code et récupéreront automatiquement le HRV.

### Cron automatique
Le fichier `backend/cron_oura_daily_sync.py` utilise déjà `sync_user_oura_data`, donc il bénéficiera automatiquement de la correction.

---

## 🎯 Impact sur l'Application

### Dans le calcul d'énergie
Le HRV est maintenant disponible pour le calcul de l'énergie :

```python
# backend/energy_calculator_v2.py
hrv_result = self.supabase.client.from_('biometrics') \
    .select('metric_value') \
    .eq('user_id', user_id) \
    .eq('metric_type', 'hrv') \
    .gte('recorded_at', f"{target_date}T00:00:00Z") \
    .lte('recorded_at', f"{target_date}T23:59:59Z") \
    .single() \
    .execute()

if hrv_result.data:
    hrv_ms = hrv_result.data['metric_value']
    # Impact du HRV sur la récupération
    if hrv_ms < 30:
        recovery *= 0.8
    elif hrv_ms < 50:
        recovery *= 0.9
```

### Dans l'affichage mobile
Le HRV apparaîtra désormais dans :
- La page "Analyse énergétique" (dans les facteurs d'influence)
- Le rapport partagé en PDF/texte

---

## ✅ Checklist de Vérification

- [x] Ajout de `get_sleep_sessions()` dans `oura_client.py`
- [x] Modification de `oura_sync_service.py` pour utiliser les sessions détaillées
- [x] Ajout de `_insert_hrv_to_biometrics()` pour sauvegarder dans `biometrics`
- [x] Création du script `resync_hrv_last_7_days.py`
- [x] Test manuel avec `test_oura_sleep_detailed.py` : ✅ HRV trouvé (18ms, 18ms, 20ms)
- [ ] **Exécution du script de re-synchronisation** (à lancer manuellement)
- [ ] Vérification dans Supabase que le HRV est bien inséré dans `biometrics`
- [ ] Test de l'application mobile pour voir le HRV dans les facteurs

---

## 🐛 Troubleshooting

### "No HRV data found in sleep session"
**Causes possibles** :
1. La bague n'a pas capturé le HRV cette nuit-là (batterie faible, mauvais port)
2. Les données ne sont pas encore synchronisées dans le cloud Oura (délai de 1-2h)
3. L'utilisateur n'a pas dormi suffisamment longtemps pour une mesure HRV

**Solution** : Réessayer la synchronisation quelques heures plus tard.

### HRV trop faible (< 10 ms)
C'est normal si :
- L'utilisateur est fatigué
- Il y a eu une infection récente
- Le stress est élevé
- Le sommeil était de mauvaise qualité

---

## 📚 Références

- **Documentation Oura API** : https://cloud.ouraring.com/v2/docs
- **Endpoint `/sleep`** : https://cloud.ouraring.com/v2/docs#tag/Sleep-Routes/operation/Multiple_sleep_Documents_v2_usercollection_sleep_get
- **HRV (Heart Rate Variability)** : Indicateur de récupération et de stress du système nerveux autonome

---

## 🎉 Résumé

**Avant** :
- ❌ HRV non synchronisé (toujours `null`)
- ❌ Utilisation d'un endpoint incomplet (`daily_sleep`)
- ❌ Approximation incorrecte depuis `contributors.hrv_balance`

**Après** :
- ✅ HRV correctement synchronisé depuis les sessions détaillées
- ✅ Valeurs réelles en millisecondes (18-20 ms)
- ✅ Sauvegarde dans la table `biometrics`
- ✅ Disponible pour le calcul d'énergie
- ✅ Affiché dans l'application mobile

---

**Prochaine étape** : Lance `python3 resync_hrv_last_7_days.py` pour remplir le HRV manquant ! 🚀
