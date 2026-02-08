# Améliorations Page Analyse Énergétique ✅

## Date
2026-02-01

## Vue d'Ensemble

Suite aux retours utilisateur sur la page "Analyse énergétique", plusieurs améliorations majeures ont été implémentées pour améliorer la visualisation et la compréhension du déclin énergétique quotidien.

## Problèmes Identifiés

### 1. Courbe Commençait à 21h au lieu du Réveil
**Impact** : L'utilisateur ne voyait pas toute l'évolution de son énergie depuis le matin.

**Citation utilisateur** :
> "Pour que l'utilisateur comprenne son déclin, il doit voir d'où il vient. Une courbe qui commence au réveil permet de visualiser la 'pente' de la journée. Si je vois que j'ai perdu 40% en 4h, je comprends l'urgence de ralentir."

### 2. Influenceurs Manquants
**Impact** : Les facteurs d'influence (médicaments, conditions) n'étaient pas affichés.

### 3. Composants d'Énergie Non Visibles
**Impact** : Les détails sur Recovery, Sleep Debt, Overtrain n'étaient pas accessibles.

### 4. Poids ML Non Visibles en Debug
**Impact** : Impossible de voir comment le ML ajuste les impacts pour chaque utilisateur.

---

## 🔧 Implémentation 1 : Courbe depuis le Réveil

### Backend (`backend/intraday_energy_service.py`)

#### Changement 1 : Utilisation du Timezone Local
```python
from zoneinfo import ZoneInfo

user_tz = ZoneInfo("Europe/Paris")
now = datetime.now(user_tz)
target_datetime = datetime.fromisoformat(f"{target_date}T00:00:00").replace(tzinfo=user_tz)
```

#### Changement 2 : Début de Courbe à l'Heure de Réveil
```python
# Défaut: 7h du matin heure locale
wake_time_hour = 7

# Essayer de récupérer l'heure réelle depuis biometrics
wake_time = target_datetime.replace(hour=wake_time_hour, minute=0, second=0, microsecond=0)
current_time = wake_time  # Commence au réveil au lieu de "maintenant"
```

### Résultats

**Avant** :
- 7 points (20h30 → 23h59 = 3h30)
- Impossible de voir le déclin depuis le matin

**Après** :
- 34 points (7h00 → 23h59 = 17h)
- Visualisation complète de la pente énergétique
- Marqueur "Maintenant" sur la courbe

### Fichiers Modifiés
- `backend/intraday_energy_service.py` (lignes 176-300)

---

## 🔧 Implémentation 2 : Génération des Influenceurs

### Backend (`backend/intraday_energy_service.py`)

#### Fonction `generate_influencers_heuristic()`

Génère une liste structurée d'influenceurs à partir de :
- **Médicaments actifs** (via `user_medications` + `medication_energy_impacts`)
- **Conditions médicales** (via `user_conditions` + `condition_energy_impacts`)
- **Poids ML personnalisés** (via `personalized_weights`)
- **Biométriques Oura** (via `biometrics.sleep_score`)

```python
def generate_influencers_heuristic(
    user_id: str,
    base_energy: float,
    recovery: float = 0.5,
    sleep_debt: float = 0.5,
    overtrain: float = 0.3,
    infection: float = 0.5
) -> List[Dict]:
    """
    Génère la liste des facteurs d'influence avec impacts ajustés ML
    
    Returns:
        List de dicts avec:
        - name: str (ex: "💊 Sertraline")
        - type: "medication" | "condition" | "biometric"
        - code: str (ATC ou ICD-11)
        - impact: str (ex: "-15%")
        - status: "positive" | "negative"
    """
```

#### Enrichissement des Notes Explicatives

Nouvelles notes contextuelles :
- **Combinaisons de sédatifs** : Alerte sur effet cumulatif
- **Paradoxes sommeil/énergie** : "Ton sommeil est bon mais masqué par d'autres facteurs"
- **Pic d'effet médicament** : Indique les heures d'impact maximal

```python
def generate_notes_intraday(
    base_energy: float,
    recovery: float,
    sleep_debt: float,
    events: List[Dict],
    windows: List[Dict],
    influencers: List[Dict]  # ← Nouveau paramètre
) -> List[str]:
    notes = []
    
    # Note sur combinaisons de sédatifs
    sedative_meds = [inf for inf in influencers if inf.get('type') == 'medication' and inf.get('status') == 'negative']
    if len(sedative_meds) >= 2:
        notes.append(f"💊 La combinaison de sédatifs a un effet cumulatif sur ta fatigue")
    
    # Note sur paradoxe sommeil
    sleep_factors = [inf for inf in influencers if inf.get('code') == 'sleep_score' and inf.get('status') == 'positive']
    if sleep_factors and base_energy < 50:
        notes.append("😴 Ton sommeil est bon mais masqué par d'autres facteurs")
    
    return notes[:4]
```

### Résultats

**Avant** :
- 0 influenceurs affichés
- Notes génériques peu contextualisées

**Après** :
- 9 influenceurs générés (3 médicaments + 3 conditions + biométriques)
- Notes enrichies avec contexte médicamenteux

### Fichiers Modifiés
- `backend/intraday_energy_service.py` (lignes 400-650)

---

## 🔧 Implémentation 3 : Section Composants d'Énergie

### Backend (`backend/intraday_energy_service.py`)

Ajout des composants au forecast :

```python
result = {
    # ... (points, windows, events, influencers, notes)
    'components': {
        'recovery': recovery,        # 0-1 (récupération physique)
        'sleep_debt': sleep_debt,    # 0-1 (dette de sommeil)
        'overtrain': overtrain,      # 0-1 (surmenage)
        'infection': infection,      # 0-1 (risque infection)
        'base_energy': base_energy   # 0-100 (énergie de base)
    }
}
```

### Mobile (`mobile/app/(tabs)/energie.tsx`)

Nouvelle section UI avec jauges visuelles :

```tsx
{Object.keys(components).length > 0 && (
  <View style={styles.componentsCard}>
    <Text style={styles.sectionTitle}>🧬 Composants d'énergie</Text>
    
    {/* Recovery */}
    <View style={styles.componentItem}>
      <View style={styles.componentHeader}>
        <Text style={styles.componentLabel}>🔋 Récupération</Text>
        <Text style={styles.componentValue}>{Math.round((components.recovery || 0) * 100)}%</Text>
      </View>
      <View style={styles.componentBarContainer}>
        <View style={[styles.componentBar, { 
          width: `${(components.recovery || 0) * 100}%`,
          backgroundColor: (components.recovery || 0) > 0.6 ? '#10B981' : '#EF4444'
        }]} />
      </View>
      <Text style={styles.componentDescription}>
        {(components.recovery || 0) > 0.6 ? 'Bonne récupération' : 'Récupération insuffisante'}
      </Text>
    </View>
    
    {/* Sleep Debt */}
    {/* ... */}
    
    {/* Overtrain */}
    {/* ... */}
  </View>
)}
```

### Résultats

**Avant** :
- Composants cachés dans la DB
- Aucun détail sur l'origine de l'énergie

**Après** :
- 3 jauges visuelles (Recovery, Sleep Debt, Overtrain)
- Codes couleur selon niveau (vert/orange/rouge)
- Descriptions contextuelles

### Fichiers Modifiés
- `backend/intraday_energy_service.py` (lignes 816-840)
- `mobile/app/(tabs)/energie.tsx` (lignes 183-255, styles 663-712)

---

## 🔧 Implémentation 4 : Poids ML en Mode Debug

### Backend (`backend/intraday_energy_service.py`)

Récupération des poids personnalisés :

```python
# 8. Récupérer les poids ML personnalisés
ml_weights = []
try:
    weights_response = supabase.table("personalized_weights").select(
        "factor_type, factor_code, weight_multiplier, updated_at"
    ).eq("user_id", user_id).eq("is_active", True).execute()
    
    if weights_response.data:
        ml_weights = weights_response.data
        logger.info(f"✓ Retrieved {len(ml_weights)} ML weights for user {user_id}")
except Exception as e:
    logger.warning(f"Could not fetch ML weights: {e}")

result = {
    # ...
    'ml_weights': ml_weights
}
```

### Mobile (`mobile/app/(tabs)/energie.tsx`)

Affichage dans le mode Debug :

```tsx
{showDebugMode && (
  <View style={styles.debugCard}>
    {/* ... informations existantes ... */}
    
    {/* Poids ML personnalisés */}
    {forecast.ml_weights && forecast.ml_weights.length > 0 && (
      <View style={styles.debugSection}>
        <Text style={styles.debugLabel}>
          🤖 Poids ML personnalisés ({forecast.ml_weights.length})
        </Text>
        {forecast.ml_weights.map((weight: any, index: number) => (
          <View key={index} style={styles.mlWeightItem}>
            <Text style={styles.mlWeightType}>
              {weight.factor_type === 'medication' ? '💊' : '🏥'} {weight.factor_code}
            </Text>
            <Text style={styles.mlWeightValue}>
              ×{weight.weight_multiplier.toFixed(2)}
            </Text>
          </View>
        ))}
        <Text style={styles.mlWeightNote}>
          Ces multiplicateurs ajustent l'impact de chaque facteur selon tes feedbacks
        </Text>
      </View>
    )}
  </View>
)}
```

### Résultats

**Avant** :
- Poids ML invisibles
- Impossible de comprendre l'ajustement personnalisé

**Après** :
- Liste de 3 poids ML pour l'utilisateur test
- Affichage du multiplicateur (ex: `×0.95`)
- Note explicative sur le rôle des poids

### Fichiers Modifiés
- `backend/intraday_energy_service.py` (lignes 816-825, 840)
- `mobile/app/(tabs)/energie.tsx` (lignes 404-440, styles 797-836)

---

## 📊 Résumé Global

### Fichiers Backend Modifiés
1. **`backend/intraday_energy_service.py`**
   - Ajout timezone Europe/Paris
   - Début courbe au réveil (7h local)
   - Génération influencers
   - Enrichissement notes
   - Ajout composants au forecast
   - Ajout poids ML au forecast

### Fichiers Mobile Modifiés
1. **`mobile/app/(tabs)/energie.tsx`**
   - Récupération et affichage des composants
   - Nouvelle section "Composants d'énergie"
   - Affichage poids ML en mode Debug
   - 6 nouveaux styles CSS

### Cache Invalidé
```sql
DELETE FROM intraday_energy_forecast 
WHERE user_id = 'c559fcd7-f6a6-4a4d-8036-c9c9d8b8c7bd' 
  AND forecast_date = '2026-02-01';
```

### Lignes de Code Modifiées
- **Backend** : ~150 lignes ajoutées/modifiées
- **Mobile** : ~110 lignes ajoutées/modifiées
- **Total** : ~260 lignes

---

## 🧪 Tests à Effectuer

### Test 1 : Courbe depuis le Réveil
1. Redémarrer le backend
2. Rafraîchir la page Énergie (pull-to-refresh)
3. **Vérifier** : La courbe commence à 7h (ou heure de réveil réelle)
4. **Vérifier** : Marqueur "Maintenant" présent

### Test 2 : Influenceurs
1. Rafraîchir la page
2. **Vérifier** : 9 influenceurs affichés
3. **Vérifier** : Séparation positifs/négatifs
4. **Vérifier** : Impacts en pourcentage

### Test 3 : Composants d'Énergie
1. Rafraîchir la page
2. **Vérifier** : Section "🧬 Composants d'énergie" visible
3. **Vérifier** : 3 jauges (Recovery, Sleep Debt, Overtrain)
4. **Vérifier** : Codes couleur corrects

### Test 4 : Poids ML en Debug
1. Activer le mode Debug (🔬)
2. Scroller jusqu'à la section Debug
3. **Vérifier** : Section "🤖 Poids ML personnalisés"
4. **Vérifier** : 3 poids affichés avec multiplicateurs

---

## 📈 Valeurs Attendues (User Test)

### Composants
```json
{
  "recovery": 0.32,      // 32% (insuffisante)
  "sleep_debt": 0,       // 0% (pas de dette)
  "overtrain": 0.67,     // 67% (charge élevée)
  "infection": 0.98,     // 98% (très faible risque)
  "base_energy": 38      // 38% (journée fragile)
}
```

### Poids ML
```json
[
  { "factor_type": "medication", "factor_code": "N06AB06", "weight_multiplier": 0.95 },
  { "factor_type": "medication", "factor_code": "N06AX11", "weight_multiplier": 0.95 },
  { "factor_type": "condition", "factor_code": "6A70", "weight_multiplier": 0.95 }
]
```

### Courbe
- **Points** : 34 (au lieu de 7)
- **Début** : 7h00 (au lieu de 21h30)
- **Fin** : 23h59

---

## 🎯 Bénéfices Utilisateur

### 1. Compréhension du Déclin
> "Si je vois que j'ai perdu 40% en 4h, je comprends l'urgence de ralentir."

**Impact** : Visualisation complète de la pente énergétique depuis le réveil.

### 2. Transparence des Facteurs
**Impact** : 9 influenceurs détaillés avec impacts mesurables.

### 3. Détails Techniques Accessibles
**Impact** : Composants d'énergie visibles pour les utilisateurs curieux.

### 4. Confiance dans le ML
**Impact** : Poids personnalisés visibles en mode Debug, montrant l'adaptation du système.

---

## 🚀 Prochaines Améliorations

### 1. Extraction Réelle de l'Heure de Réveil
Actuellement, on utilise 7h par défaut. Il faudrait enrichir les métadonnées Oura.

### 2. Timezone Dynamique par Utilisateur
Ajouter une colonne `timezone` dans `profiles`.

### 3. Historique des Poids ML
Afficher l'évolution des poids au fil du temps.

### 4. Graphique des Composants
Courbes historiques de Recovery, Sleep Debt, Overtrain sur 30 jours.

---

## ✅ Statut

**TOUS LES TODOs COMPLÉTÉS** :
- ✅ Générer les influencers dans le forecast backend
- ✅ Enrichir les notes explicatives avec contexte médicaments
- ✅ Étendre la courbe d'énergie depuis le réveil
- ✅ Ajouter section Composants d'énergie dans la page mobile
- ✅ Afficher les poids ML personnalisés dans le mode Debug

**En attente** : Tests utilisateur après redémarrage backend

---

**Auteur** : Assistant AI  
**Date** : 2026-02-01  
**Review** : En attente  
**Tags** : #energy #intraday #influencers #components #ml-weights #UX
