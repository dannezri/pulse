# API Endpoints Oura

Documentation des endpoints API pour gérer les connexions Oura depuis l'application mobile.

## 📋 Endpoints disponibles

### 1. GET `/api/oura/status`

Vérifie le statut de la connexion Oura de l'utilisateur.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "connected": true,
  "last_sync": "2026-02-04T08:00:00Z",
  "has_readiness_data": true,
  "connected_at": "2026-01-15T10:30:00Z"
}
```

**Codes de statut:**
- `200` - Succès
- `401` - Non authentifié
- `500` - Erreur serveur

---

### 2. POST `/api/oura/connect`

Connecte un compte Oura à l'utilisateur.

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Body:**
```json
{
  "access_token": "IX6RMKRCMIJOVZMIB2IKVL2PWUQOCNNI"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Oura account connected successfully",
  "external_user_id": "user@example.com"
}
```

**Codes de statut:**
- `200` - Succès
- `400` - Token invalide ou manquant
- `401` - Non authentifié
- `500` - Erreur serveur

**Processus:**
1. Valide le token Oura en appelant l'API Oura
2. Récupère les informations personnelles de l'utilisateur
3. Crée ou met à jour l'entrée dans `external_identities`
4. Stocke le token dans `metadata.access_token`

---

### 3. POST `/api/oura/disconnect`

Déconnecte le compte Oura de l'utilisateur.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "status": "success",
  "message": "Oura account disconnected"
}
```

**Codes de statut:**
- `200` - Succès
- `404` - Aucun compte Oura trouvé
- `401` - Non authentifié
- `500` - Erreur serveur

**Note:** La déconnexion met `is_active` à `false` mais ne supprime pas les données.

---

### 4. POST `/api/oura/sync`

Synchronise les données Oura pour l'utilisateur connecté.

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Query params:**
- `date` (optionnel): Date à synchroniser au format `YYYY-MM-DD` (défaut: aujourd'hui)

**Response:**
```json
{
  "status": "success",
  "message": "Oura data synced successfully for 2026-02-04",
  "data": {
    "current_metrics": {
      "readiness_score": 85,
      "sleep_score": 78,
      "activity_score": 82,
      "hrv_ms": 45,
      "resting_hr": 58,
      "total_sleep_duration": 420,
      "deep_sleep_duration": 90,
      "rem_sleep_duration": 120,
      "steps": 8500,
      "temperature_deviation": 0.2
    },
    "anomalies": [],
    "synced_at": "2026-02-04T12:00:00Z"
  }
}
```

**Codes de statut:**
- `200` - Succès
- `400` - Erreur (ex: aucun token Oura trouvé)
- `401` - Non authentifié
- `500` - Erreur serveur

---

## 🔐 Obtenir un token Oura

### Méthode 1: Personal Access Token (actuelle)

1. Se connecter à [Oura Cloud](https://cloud.ouraring.com/)
2. Aller dans **Personal Access Tokens**
3. Créer un nouveau token avec les scopes nécessaires
4. Copier le token (format: `IX6RMKRCMIJOVZMIB2IKVL2PWUQOCNNI`)

### Méthode 2: OAuth2 (future)

À implémenter pour une meilleure expérience utilisateur:
- Redirection vers Oura pour autorisation
- Callback avec code d'autorisation
- Échange du code contre un access_token et refresh_token

---

## 📱 Intégration dans l'app mobile

### Exemple React Native / Expo

```typescript
import { useAuth } from '@/hooks/useAuth';

// Vérifier le statut
const checkOuraStatus = async () => {
  const { token } = useAuth();
  
  const response = await fetch('https://api.pulse.com/api/oura/status', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  return data.connected;
};

// Connecter un compte Oura
const connectOura = async (ouraToken: string) => {
  const { token } = useAuth();
  
  const response = await fetch('https://api.pulse.com/api/oura/connect', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      access_token: ouraToken
    })
  });
  
  if (!response.ok) {
    throw new Error('Failed to connect Oura account');
  }
  
  return await response.json();
};

// Synchroniser les données
const syncOura = async () => {
  const { token } = useAuth();
  
  const response = await fetch('https://api.pulse.com/api/oura/sync', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
};

// Déconnecter
const disconnectOura = async () => {
  const { token } = useAuth();
  
  const response = await fetch('https://api.pulse.com/api/oura/disconnect', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
};
```

---

## 🧪 Tests

### Test avec curl

```bash
# 1. Obtenir un JWT token
JWT_TOKEN="votre-jwt-token"

# 2. Vérifier le statut
curl -X GET "http://localhost:8000/api/oura/status" \
  -H "Authorization: Bearer $JWT_TOKEN"

# 3. Connecter un compte Oura
curl -X POST "http://localhost:8000/api/oura/connect" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"access_token": "IX6RMKRCMIJOVZMIB2IKVL2PWUQOCNNI"}'

# 4. Synchroniser les données
curl -X POST "http://localhost:8000/api/oura/sync" \
  -H "Authorization: Bearer $JWT_TOKEN"

# 5. Déconnecter
curl -X POST "http://localhost:8000/api/oura/disconnect" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

## 🔒 Sécurité

- Tous les endpoints nécessitent un JWT valide
- Les tokens Oura sont stockés de manière sécurisée dans Supabase
- Les tokens ne sont jamais exposés dans les réponses API
- RLS (Row Level Security) activé sur `external_identities`
- Les logs ne doivent pas afficher les tokens en clair

---

## 📊 Données synchronisées

Lors de la synchronisation, les données suivantes sont récupérées:

### Readiness (Préparation)
- Score de préparation (0-100)
- Température corporelle (déviation)
- Balance d'activité
- Index de récupération

### Sleep (Sommeil)
- Score de sommeil (0-100)
- Durée totale de sommeil
- Efficacité du sommeil
- Sommeil profond
- Sommeil paradoxal (REM)
- Périodes agitées
- Fréquence cardiaque au repos

### Activity (Activité)
- Score d'activité (0-100)
- Nombre de pas
- Calories actives
- Calories totales

### HRV (Variabilité cardiaque)
- HRV moyen (ms)
- Métadonnées de session

---

## 🐛 Dépannage

### Erreur: "No Oura token found for user"
- Vérifier que l'utilisateur a bien connecté son compte Oura
- Appeler `/api/oura/status` pour vérifier

### Erreur: "Failed to connect Oura account"
- Vérifier que le token Oura est valide
- Tester le token sur [Oura API Docs](https://cloud.ouraring.com/v2/docs)

### Erreur: "No Oura account connected"
- L'utilisateur n'a pas encore connecté son compte
- Rediriger vers l'écran de connexion Oura

---

**Date de création**: 4 février 2026  
**Version**: 1.0
