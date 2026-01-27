# Idempotence & Dédoublonnage des Webhooks

## 📋 Vue d'Ensemble

Le système d'idempotence garantit que les webhooks peuvent être rejoués sans créer de doublons, même en cas de :
- **Webhooks doublés** : Le même événement est envoyé plusieurs fois
- **Retards** : Les événements arrivent en retard
- **Événements hors-ordre** : Les événements arrivent dans un ordre différent de leur création

## 🔧 Implémentation

### Schéma de Base de Données

La table `biometrics` inclut maintenant :
- **`source_event_id`** : ID unique de l'événement depuis la source (webhook/provider)
- **Contrainte unique** : `(user_id, source, source_event_id)` pour empêcher les doublons

```sql
-- Migration 003 : Ajout de l'idempotence
ALTER TABLE biometrics ADD COLUMN source_event_id TEXT;
CREATE UNIQUE INDEX biometrics_user_source_event_unique 
    ON biometrics(user_id, source, source_event_id) 
    WHERE source_event_id IS NOT NULL;
```

### Génération de `source_event_id`

Le système utilise trois stratégies (par ordre de priorité) :

1. **ID fourni par le provider** : Si Open Wearables fournit un `event_id` dans le webhook
2. **ID de l'entrée** : Si chaque point de données a son propre `event_id`
3. **Hash du payload** : Fallback - génère un hash MD5 du payload JSON

### Code d'Exemple

#### Webhook Handler

```python
# Le webhook peut inclure un event_id global
payload = {
    "user_id": "uuid",
    "event_id": "webhook-uuid-123",  # Optionnel
    "data": {
        "hr": [
            {"value": 72, "timestamp": "...", "event_id": "hr-event-1"},  # Optionnel
            {"value": 73, "timestamp": "..."}
        ]
    }
}

# Le handler génère un source_event_id unique pour chaque point
source_event_id = f"{webhook_event_id}_hr_{hash(payload)}"
```

#### Client Supabase

```python
# insert_biometric vérifie automatiquement les doublons
result = supabase_client.insert_biometric(
    user_id=user_id,
    metric_type="hr",
    value=72.0,
    recorded_at=datetime.now(),
    raw_data=entry,
    source="open_wearables",
    source_event_id="webhook-uuid-123_hr_abc123"  # Unique par point
)

# Retourne {"status": "duplicate"} si l'événement existe déjà
```

## 🔄 Flux de Traitement

```
1. Webhook reçu
   └─> Extraire event_id (si disponible)
   
2. Pour chaque point de données :
   ├─> Générer source_event_id unique
   ├─> Vérifier si existe déjà (SELECT)
   └─> Si nouveau : INSERT
      └─> Si doublon : Contrainte unique bloque → Ignorer silencieusement
   
3. Résultat : Aucun doublon, même si webhook rejoué
```

## ✅ Avantages

1. **Idempotence garantie** : Rejouer un webhook ne crée pas de doublons
2. **Performance** : Index unique pour vérification rapide
3. **Flexibilité** : Supporte les providers avec/sans event_id
4. **Rétrocompatibilité** : Les anciennes données (sans source_event_id) continuent de fonctionner

## 📝 Format des Webhooks

### Format Recommandé (avec event_id)

```json
{
  "user_id": "open-wearables-uuid",
  "event_id": "webhook-event-uuid-123",
  "timestamp": "2024-01-15T10:00:00Z",
  "data": {
    "hr": [
      {
        "value": 72,
        "timestamp": "2024-01-15T10:00:00Z",
        "event_id": "hr-point-uuid-456"
      }
    ],
    "sleep": {
      "duration_seconds": 28800,
      "start_time": "2024-01-15T22:00:00Z"
    }
  }
}
```

### Format Minimal (sans event_id)

```json
{
  "user_id": "open-wearables-uuid",
  "data": {
    "hr": [{"value": 72, "timestamp": "2024-01-15T10:00:00Z"}]
  }
}
```

Dans ce cas, le système génère automatiquement un hash du payload comme `source_event_id`.

## 🧪 Tests

### Test de Doublon

```python
# Premier appel
result1 = supabase_client.insert_biometric(
    user_id="user-123",
    metric_type="hr",
    value=72.0,
    recorded_at=datetime.now(),
    raw_data={"value": 72},
    source="open_wearables",
    source_event_id="event-123"
)
# Résultat: {"status": "inserted"}

# Deuxième appel (même source_event_id)
result2 = supabase_client.insert_biometric(
    user_id="user-123",
    metric_type="hr",
    value=72.0,
    recorded_at=datetime.now(),
    raw_data={"value": 72},
    source="open_wearables",
    source_event_id="event-123"  # Même ID
)
# Résultat: {"status": "duplicate"} - Pas d'erreur, juste ignoré
```

## 🔍 Vérification

Pour vérifier que l'idempotence fonctionne :

```sql
-- Vérifier les doublons potentiels
SELECT user_id, source, source_event_id, COUNT(*) 
FROM biometrics 
WHERE source_event_id IS NOT NULL
GROUP BY user_id, source, source_event_id
HAVING COUNT(*) > 1;
-- Devrait retourner 0 lignes (grâce à la contrainte unique)
```

## 📚 Migration

Pour appliquer l'idempotence à une base existante :

1. Exécuter la migration `003_add_idempotence.sql`
2. Les anciennes données auront `source_event_id = NULL` (normal)
3. Les nouvelles insertions incluront automatiquement `source_event_id`

## ⚠️ Notes Importantes

- **NULL est autorisé** : Les anciennes données sans `source_event_id` continuent de fonctionner
- **Contrainte partielle** : La contrainte unique ne s'applique que si `source_event_id IS NOT NULL`
- **Hash comme fallback** : Si aucun `event_id` n'est fourni, un hash MD5 est généré
- **Unicité par point** : Chaque point de données dans un webhook a son propre `source_event_id`

---

*Document créé le : 2024*
*Migration : 003_add_idempotence.sql*
