# 📔 Food Diary MVP - Documentation Complète

**Version**: 1.0  
**Date**: 29 janvier 2026  
**Status**: ✅ Production Ready

---

## 📋 Vue d'Ensemble

Le **Food Diary MVP** permet aux utilisateurs Pulse de :
- 🔍 **Rechercher** des aliments (base FatSecret)
- ✏️ **Ajouter** des repas (petit-déj, déjeuner, dîner, snack)
- 👀 **Consulter** leur journal alimentaire (par jour, par repas)
- 📷 **Prendre des photos** de repas (avec suggestions IA optionnelles)
- 🔄 **Synchroniser** automatiquement avec FatSecret

**Architecture** : Supabase (source de vérité) ↔️ FatSecret (source nutritionnelle + backup diary)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    APP MOBILE PULSE                          │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Recherche│  │  Ajouter │  │ Consulter│  │  Photo   │   │
│  │ aliments │  │  repas   │  │  journal │  │  repas   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼──────────────┼─────────────┼─────────┘
        │             │              │             │
        └─────────────┴──────────────┴─────────────┘
                      │
        ┌─────────────▼─────────────┐
        │   API SERVER (FastAPI)     │
        │                            │
        │  FoodLogService            │
        │  PhotoService              │
        └────────┬──────────┬────────┘
                 │          │
        ┌────────▼──────┐   │
        │   FatSecret   │   │
        │ (nutrition DB)│   │
        └────────┬──────┘   │
                 │          │
        ┌────────▼──────────▼────────┐
        │      SUPABASE              │
        │  - fatsecret_profiles      │
        │  - food_logs               │
        │  - food_log_items          │
        │  - food_photos             │
        │  - food_entries_raw        │
        └────────────────────────────┘
```

---

## 🗄️ Schéma Base de Données

### **`fatsecret_profiles`**
Profils FatSecret API-only (anciennement `fatsecret_connections`)

```sql
CREATE TABLE fatsecret_profiles (
  user_id UUID PRIMARY KEY,
  oauth_token TEXT NOT NULL,
  oauth_token_secret TEXT NOT NULL,
  connected_at TIMESTAMPTZ DEFAULT NOW(),
  last_synced_date DATE,
  last_sync_at TIMESTAMPTZ,
  is_active BOOLEAN DEFAULT TRUE,
  metadata JSONB DEFAULT '{}'
);
```

### **`food_logs`**
Journal alimentaire principal (un log = un repas/événement)

```sql
CREATE TABLE food_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id),
  
  logged_at TIMESTAMPTZ NOT NULL,  -- Heure réelle du repas
  meal_type TEXT NOT NULL CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')),
  source TEXT NOT NULL DEFAULT 'manual' CHECK (source IN ('manual', 'search', 'photo', 'import')),
  
  note TEXT,
  context JSONB DEFAULT '{}',  -- {hunger: 7, mood: "ok", location: "home"}
  
  -- Sync FatSecret
  fs_sync_status TEXT DEFAULT 'pending',
  fs_food_entry_ids JSONB DEFAULT '[]',
  fs_synced_at TIMESTAMPTZ,
  fs_error TEXT,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### **`food_log_items`**
Items alimentaires dans un repas

```sql
CREATE TABLE food_log_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  food_log_id UUID NOT NULL REFERENCES food_logs(id) ON DELETE CASCADE,
  
  name TEXT NOT NULL,
  quantity NUMERIC NOT NULL DEFAULT 1.0,
  unit TEXT NOT NULL DEFAULT 'serving',
  
  -- Références FatSecret
  fs_food_id BIGINT,
  fs_serving_id BIGINT,
  
  nutrition JSONB DEFAULT '{}',  -- {calories: 200, protein: 10, ...}
  raw JSONB DEFAULT '{}',
  
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### **`food_photos`**
Photos de repas avec analyse IA optionnelle

```sql
CREATE TABLE food_photos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  food_log_id UUID NOT NULL REFERENCES food_logs(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES profiles(id),
  
  storage_path TEXT NOT NULL,
  storage_bucket TEXT DEFAULT 'food-photos',
  taken_at TIMESTAMPTZ DEFAULT NOW(),
  file_size_bytes BIGINT,
  mime_type TEXT,
  
  -- Analyse IA
  analysis JSONB DEFAULT '{}',
  analysis_status TEXT DEFAULT 'pending',
  confidence NUMERIC CHECK (confidence >= 0 AND confidence <= 1),
  
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 🔌 API Endpoints

### **1. Provisioning Profil FatSecret**

```http
POST /api/food-diary/provision
Authorization: Bearer <jwt_token>
```

**Response**:
```json
{
  "status": "ok|exists",
  "fatsecret_profile": "active|created"
}
```

---

### **2. Recherche d'Aliments**

```http
GET /api/foods/search?q=pomme&page=0
Authorization: Bearer <jwt_token>
```

**Response**:
```json
{
  "foods": [
    {
      "fs_food_id": 35718,
      "name": "Pommes",
      "brand": null,
      "description": "Par 100g - Calories: 52kcal | Fat: 0.17g | Carbs: 13.81g | Protein: 0.26g",
      "type": "generic"
    }
  ]
}
```

---

### **3. Détails d'un Aliment**

```http
GET /api/foods/35718
Authorization: Bearer <jwt_token>
```

**Response**:
```json
{
  "food_id": 35718,
  "name": "Pommes",
  "brand": null,
  "servings": [
    {
      "serving_id": 0,
      "serving_description": "100g",
      "metric_serving_amount": "100",
      "metric_serving_unit": "g",
      "calories": "52",
      "protein": "0.26",
      "carbohydrate": "13.81",
      "fat": "0.17",
      "fiber": "2.4"
    }
  ]
}
```

---

### **4. Ajouter un Repas**

```http
POST /api/food-logs
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "logged_at": "2026-01-29T12:30:00Z",
  "meal_type": "lunch",
  "items": [
    {
      "name": "Pommes",
      "fs_food_id": 35718,
      "fs_serving_id": 0,
      "quantity": 1.5,
      "unit": "serving",
      "nutrition": {
        "calories": 78,
        "protein": 0.4,
        "carbohydrate": 20.7,
        "fat": 0.3
      }
    }
  ],
  "note": "Déjeuner rapide",
  "context": {
    "hunger": 7,
    "mood": "ok",
    "location": "home"
  },
  "source": "search"
}
```

**Response**:
```json
{
  "food_log_id": "550e8400-e29b-41d4-a716-446655440000",
  "items_count": 1,
  "fs_sync_status": "synced",
  "fs_entry_ids": [123456]
}
```

---

### **5. Consulter le Journal**

```http
GET /api/food-diary?date_str=2026-01-29&force_sync=false
Authorization: Bearer <jwt_token>
```

**Response**:
```json
{
  "date": "2026-01-29",
  "meals": {
    "breakfast": [
      {
        "id": "...",
        "logged_at": "2026-01-29T08:00:00Z",
        "note": "Petit-déj",
        "context": {},
        "items": [...],
        "photos": [],
        "nutrition": {
          "calories": 350,
          "protein": 15,
          "carbohydrate": 45,
          "fat": 12
        },
        "fs_sync_status": "synced"
      }
    ],
    "lunch": [],
    "dinner": [],
    "snack": []
  },
  "total_nutrition": {
    "calories": 350,
    "protein": 15,
    "carbohydrate": 45,
    "fat": 12
  },
  "source": "cache"
}
```

---

### **6. Upload Photo**

```http
POST /api/food-logs/{food_log_id}/photo
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data

file: <image_file>
analyze: false
```

**Response**:
```json
{
  "photo_id": "...",
  "storage_path": "user-id/food-log-id/photo-id.jpg",
  "public_url": "https://...",
  "file_size_bytes": 245678,
  "analysis_status": "skipped"
}
```

---

### **7. Obtenir URL Photo**

```http
GET /api/food-photos/{photo_id}/url?expires_in=3600
Authorization: Bearer <jwt_token>
```

**Response**:
```json
{
  "url": "https://khhcywhnhncwcevleclh.supabase.co/storage/v1/object/sign/food-photos/..."
}
```

---

### **8. Réconciliation (Admin)**

```http
POST /api/admin/reconcile-food-logs?days_back=7
Authorization: Bearer <jwt_token>
```

**Response**:
```json
{
  "reconciled": 5,
  "failed": 1,
  "users": ["user-id-1", "user-id-2"]
}
```

---

## 🔄 Stratégie de Synchronisation

### **À chaque ajout de repas** :
1. ✅ Insertion dans Supabase (`food_logs` + `food_log_items`)
2. ✅ Sync vers FatSecret (`food_entry.create`) - **best effort**
3. ✅ Mise à jour `fs_sync_status` : `synced` | `error` | `pending`

### **En cas d'échec** :
- Status = `error`
- Message d'erreur stocké dans `fs_error`
- Réessai via script de réconciliation

### **Cron quotidien** (3h du matin) :
```bash
0 3 * * * cd /path/to/backend && python3 reconcile_food_logs.py
```

Script : `/backend/reconcile_food_logs.py`

---

## 📱 UX Mobile (Flux Utilisateur)

### **1. Onglet "Journal"**
```
┌────────────────────────────┐
│  Journal - 29 Jan 2026     │
│                            │
│  🌅 Petit-déjeuner         │
│    Pommes (100g)    52kcal │
│    + Ajouter               │
│                            │
│  🌞 Déjeuner               │
│    + Ajouter               │
│                            │
│  🌙 Dîner                  │
│    + Ajouter               │
│                            │
│  🍪 Snack                  │
│    + Ajouter               │
│                            │
│  Total: 52kcal             │
└────────────────────────────┘
```

### **2. Ajouter un Repas**
```
Choix :
┌────────────────────────────┐
│  🔎 Rechercher aliment     │
│  📷 Photo d'un plat        │
│  🧾 Scanner code-barres    │
└────────────────────────────┘
```

### **3. Flow Recherche**
```
1. Search "pomme"
   → Résultats
2. Pick "Pommes"
   → Servings disponibles
3. Choisir portion "100g"
   → Quantité
4. Confirm
   → Ajouté au journal
```

### **4. Flow Photo**
```
1. Prendre photo
   → Upload
2. (Optionnel) IA propose items
   → User confirme
   OU
   Search manuelle
3. Confirm
   → Ajouté au journal
```

---

## 🛠️ Configuration & Déploiement

### **Variables d'environnement**

```bash
# FatSecret
FATSECRET_CONSUMER_KEY=your_consumer_key
FATSECRET_CONSUMER_SECRET=your_consumer_secret

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key

# Optional : Réconciliation
RECONCILE_DAYS_BACK=7
```

### **Migration Supabase**

```bash
# Appliquer migration
python3 backend/apply_fatsecret_migration.py

# Ou via MCP
# (déjà fait via migration 019_food_diary_mvp.sql)
```

### **Créer bucket Supabase Storage**

```sql
-- Via Supabase Dashboard:
-- Storage → New Bucket → "food-photos"
-- Policies: RLS activées (déjà configuré via migration)
```

### **Lancer le serveur**

```bash
cd backend
python3 api_server.py

# Ou avec uvicorn
uvicorn api_server:app --host 0.0.0.0 --port 9000 --reload
```

### **Tester**

```bash
# Provisioning
curl -X POST http://localhost:9000/api/food-diary/provision \
  -H "Authorization: Bearer YOUR_JWT"

# Recherche
curl "http://localhost:9000/api/foods/search?q=pomme" \
  -H "Authorization: Bearer YOUR_JWT"

# Ajouter repas
curl -X POST http://localhost:9000/api/food-logs \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{"logged_at":"2026-01-29T12:00:00Z","meal_type":"lunch","items":[{"name":"Pommes","fs_food_id":35718,"fs_serving_id":0,"quantity":1}]}'
```

---

## 🎯 Ultra Personnalisable

### **Contexte JSONB**

Stockez n'importe quelle donnée dans `food_logs.context` :

```json
{
  "hunger": 7,
  "mood": "happy",
  "location": "home",
  "social": "alone",
  "activity_before": "workout",
  "digestive_symptoms": ["bloating"],
  "energy_after": 8,
  "custom_tags": ["cheat_meal", "celebration"]
}
```

### **Préférences Utilisateur**

Dans `profiles.settings` (à créer) :

```json
{
  "food_diary": {
    "default_meal_times": {
      "breakfast": "08:00",
      "lunch": "12:30",
      "dinner": "19:00"
    },
    "meal_labels": {
      "snack": "Collation"
    },
    "goals": {
      "calories": 2000,
      "protein": 150,
      "carbs": 200,
      "fat": 65
    },
    "diet_preferences": ["vegetarian"],
    "allergens": ["gluten", "lactose"],
    "macro_focus": "protein",
    "ui_mode": "simple"
  }
}
```

---

## 🚀 Prochaines Étapes

### **MVP Complet** ✅
- [x] Schéma Supabase
- [x] Services backend
- [x] API endpoints
- [x] Upload photo
- [x] Script réconciliation
- [x] Documentation

### **Intégration Mobile** 🔄
- [ ] Screens React Native/Expo
- [ ] Hooks pour API calls
- [ ] Composants UI (SearchBar, FoodItem, MealCard, PhotoPicker)
- [ ] État local (Context/Zustand)

### **Améliorations Futures** 💡
- [ ] Analyse IA photo (FatSecret Image Recognition ou Passio)
- [ ] Scanner code-barres
- [ ] Suggestions basées sur historique
- [ ] Macros tracking avancé (fibres, sodium, vitamines)
- [ ] Exportation données (CSV, PDF)
- [ ] Intégration calendrier (repas planifiés)
- [ ] Partage social
- [ ] Coaching nutritionnel (LLM)

---

## 📞 Support

**Questions ?** Consultez :
- `backend/services/food_log_service.py` (logique métier)
- `backend/services/photo_service.py` (photos)
- `backend/fatsecret_client_v2.py` (API FatSecret)

**Logs** : `backend/logs/` (si configuré)

**Issues** : Voir `fs_error` dans `food_logs` pour diagnostiquer les échecs de sync.

---

**🎉 Food Diary MVP Ready for Production!**
