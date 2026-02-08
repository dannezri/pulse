# Fix : Composants et Influencers Manquants dans le Rapport Partagé

## Date
2026-02-01 22:20

## Problème Identifié

Le rapport partagé **manquait 2 sections critiques** :

1. ❌ **Composants d'énergie** (Recovery, Sleep Debt, Overtrain)
2. ❌ **Facteurs d'influence** (Liste des influencers positifs/négatifs)

### Rapport Reçu (Incomplet)

```
⚡ RAPPORT ANALYSE ÉNERGÉTIQUE - PULSE
==================================================

📅 dimanche 1 février 2026

🔋 ÉNERGIE ACTUELLE: 38%
État: Énergie basse

==================================================
📝 NOTES EXPLICATIVES
==================================================

• Ton énergie de base est faible aujourd'hui (38%)
• 💊 La combinaison Mirtazapine + Melatonine a un effet cumulatif sur ta fatigue
• 😴 Ton sommeil est bon mais masqué par d'autres facteurs
• Ta récupération est incomplète (32%)

==================================================
⚡ Pulse - Coach énergétique personnalisé
```

**Sections manquantes** :
- Pas de détail sur Recovery (32%)
- Pas de détail sur Sleep Debt
- Pas de détail sur Overtrain
- Pas de liste d'influencers (Mirtazapine, Melatonine, etc.)

---

## Cause Racine

### 1. ❌ Colonne `components` Manquante en DB

La table `intraday_energy_forecast` ne contenait **pas la colonne `components`**.

```sql
-- ❌ AVANT
CREATE TABLE intraday_energy_forecast (
  id UUID,
  user_id UUID,
  points JSONB,
  influencers JSONB,
  notes JSONB,
  -- components MANQUANT !
);
```

### 2. ❌ Backend Ne Sauvegardait Pas `components`

La fonction `save_intraday_forecast()` générait bien les components mais **ne les persistait pas** :

```python
# ❌ AVANT (intraday_energy_service.py ligne 878-891)
record = {
    'user_id': user_id,
    'forecast_date': forecast['date'],
    'timezone': forecast['timezone'],
    'points': forecast['points'],
    'influencers': forecast.get('influencers', []),
    'notes': forecast['notes'],
    # 'components' MANQUANT !
}
```

---

## Corrections Apportées

### 1. ✅ Migration DB : Ajout Colonne `components`

**Migration** : `add_components_to_intraday_forecast`

```sql
ALTER TABLE intraday_energy_forecast
ADD COLUMN IF NOT EXISTS components jsonb DEFAULT '{}'::jsonb;

COMMENT ON COLUMN intraday_energy_forecast.components IS 
  'Composants d''énergie détaillés: {recovery, sleep_debt, overtrain, infection, base_energy}';
```

**Structure des Components** :

```json
{
  "recovery": 0.32,        // 0.0-1.0 (score de récupération)
  "sleep_debt": 0.0,       // 0.0-1.0 (dette de sommeil)
  "overtrain": 0.67,       // 0.0-1.0 (surcharge d'entraînement)
  "infection": 0.5,        // 0.0-1.0 (état inflammatoire)
  "base_energy": 38        // 0-100 (score d'énergie de base)
}
```

### 2. ✅ Backend : Sauvegarde des `components`

**Fichier** : `backend/intraday_energy_service.py` (ligne 887)

```python
# ✅ APRÈS
record = {
    'user_id': user_id,
    'forecast_date': forecast['date'],
    'timezone': forecast['timezone'],
    'points': forecast['points'],
    'influencers': forecast.get('influencers', []),
    'components': forecast.get('components', {}),  # ✅ AJOUTÉ
    'notes': forecast['notes'],
    'model_version': forecast['model_version'],
    'confidence': forecast['confidence'],
}
```

### 3. ✅ Cache Invalidation

```sql
DELETE FROM intraday_energy_forecast 
WHERE user_id = 'c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd' 
  AND forecast_date = '2026-02-01';
```

---

## Rapport Attendu (Complet)

Après le fix, le rapport devrait contenir :

```
⚡ RAPPORT ANALYSE ÉNERGÉTIQUE - PULSE
==================================================

📅 dimanche 1 février 2026

🔋 ÉNERGIE ACTUELLE: 38%
État: Énergie basse

==================================================
🧬 COMPOSANTS D'ÉNERGIE
==================================================

🔋 Récupération: 32% (Insuffisante)
😴 Dette de sommeil: 100% (Aucune)
💪 Charge d'entraînement: 33% (Élevée)

==================================================
🎯 FACTEURS D'INFLUENCE
==================================================

✅ Facteurs positifs:
  • ✨ Sommeil de qualité: +8%

⚠️ Facteurs négatifs:
  • 💊 Mirtazapine: -15%
  • 💊 Melatonine: -5%
  • 🏥 Dépression: -10%
  • 🏥 Insomnie: -5%

==================================================
📝 NOTES EXPLICATIVES
==================================================

• ⚠️ Ton énergie de base est faible aujourd'hui (38%)
• 💊 La combinaison Mirtazapine + Melatonine a un effet cumulatif sur ta fatigue
• 😴 Ton sommeil est bon mais masqué par d'autres facteurs
• Ta récupération est incomplète (32%)

==================================================
⚡ Pulse - Coach énergétique personnalisé
Modèle: intraday_v1

Ce rapport est basé sur tes données Oura,
médicaments et conditions de santé.
Les prédictions sont personnalisées via ML.
```

---

## Actions Requises

### 1. ⚠️ Redémarrer le Backend

Le backend doit être redémarré pour charger la nouvelle version du code :

**Terminal 235** :

```bash
# 1. Arrêter le backend (Ctrl+C dans le terminal)

# 2. Redémarrer
cd /Users/dannezri/Desktop/Pulse/backend
./restart_api_server.sh
```

### 2. ⚠️ Recharger l'App Mobile

Une fois le backend redémarré :

1. **Ouvrir l'app Pulse**
2. **Aller sur la page "Analyse Énergétique"**
3. **Cliquer sur 🔄** (force refresh)
4. **Attendre 2-3 secondes** (régénération du forecast)
5. **Cliquer sur 📤** pour tester le nouveau rapport

---

## Validation

### Checklist Backend

```bash
# Vérifier que les components sont en DB
supabase db query --db-url <your-url> \
  "SELECT components FROM intraday_energy_forecast 
   WHERE user_id = 'c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd' 
   AND forecast_date = '2026-02-01'"

# Résultat attendu:
# { "recovery": 0.32, "sleep_debt": 0.0, "overtrain": 0.67, ... }
```

### Checklist Mobile

1. ✅ Les **components** s'affichent dans la card "🧬 Composants d'énergie"
2. ✅ Les **influencers** s'affichent dans la card "🎯 Facteurs d'influence"
3. ✅ Le **rapport partagé** contient les 2 sections manquantes

---

## Logs de Debug

### Backend

Après redémarrage, vérifier dans les logs :

```
INFO:intraday_energy_service:✓ Generated intraday forecast with X points, Y events
INFO:intraday_energy_service:✓ Saved intraday forecast for user ..., date 2026-02-01
```

### Mobile

Console Expo :

```javascript
[EnergyAnalysis] Has components: 5  // ✅ 5 clés (recovery, sleep_debt, overtrain, infection, base_energy)
[EnergyAnalysis] Has influencers: 7  // ✅ Nombre d'influencers > 0
```

---

## Résumé des Modifications

| Fichier | Ligne | Changement |
|---------|-------|------------|
| **Database** | Migration | Ajout colonne `components JSONB` |
| **backend/intraday_energy_service.py** | 887 | Ajout `'components': forecast.get('components', {})` |
| **Cache** | Supabase | Suppression forecast 2026-02-01 |

---

## Impact Utilisateur

### Avant le Fix ❌

- Rapport texte incomplet
- Pas de détail sur les composants d'énergie
- Pas de liste d'influencers
- Moins informatif

### Après le Fix ✅

- Rapport texte complet
- Détail des 3 composants avec statuts
- Liste complète des influencers positifs/négatifs
- Maximum de contexte pour l'utilisateur

---

## Prochaines Améliorations (Optionnel)

### 1. PDF Professionnel (Backend)

Si tu veux un PDF visuel au lieu de texte :

```python
# backend/api_server.py
@app.get("/api/v1/energy-report/pdf")
async def generate_pdf_report(user_id: str):
    forecast = generate_intraday_forecast(user_id)
    pdf_path = generate_pdf_from_html(forecast)  # weasyprint
    return FileResponse(pdf_path, media_type='application/pdf')
```

Puis côté mobile :

```typescript
// Ouvrir le PDF généré par le backend
const pdfUrl = `${API_URL}/api/v1/energy-report/pdf?user_id=${userId}`;
await Linking.openURL(pdfUrl);
```

### 2. Graphique dans le Rapport

Pour inclure le graphique de la courbe énergétique :

- **Option A** : Screenshot via `react-native-view-shot` (nécessite module natif)
- **Option B** : Générer SVG côté backend et l'inclure dans le PDF

---

**Auteur** : Assistant AI  
**Date** : 2026-02-01 22:20  
**Status** : ⚠️ EN ATTENTE REDÉMARRAGE BACKEND  
**Tags** : #fix #components #influencers #share #report
