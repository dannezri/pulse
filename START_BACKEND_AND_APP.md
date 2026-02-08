# 🚀 Démarrage Backend + App Mobile (Guide Complet)

## ❌ Problème actuel

Les logs montrent :
```
Socket SO_ERROR 61
TCP Conn Failed : error 61
Connection refused
```

**Erreur 61 = "Connection refused"** → Le backend n'est pas démarré ou pas accessible.

---

## ✅ Solution en 3 étapes

### 1️⃣ Démarrer le backend

```bash
cd /Users/dannezri/Desktop/Pulse/backend
chmod +x restart_backend_ml.sh
./restart_backend_ml.sh
```

**Vérification :**
```bash
# Le backend doit répondre
curl http://localhost:9000/health
# Attendu: {"status":"healthy"}
```

Si le script échoue, démarrez manuellement :
```bash
cd /Users/dannezri/Desktop/Pulse/backend
python api_server.py
```

---

### 2️⃣ Vérifier votre IP locale

Le backend écoute sur `localhost:9000`, mais votre iPhone doit utiliser l'**IP locale de votre Mac**.

**Trouver votre IP :**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

Vous verrez quelque chose comme :
```
inet 192.168.0.23 netmask 0xffffff00 broadcast 192.168.0.255
```

**Votre IP locale = `192.168.0.23`**

---

### 3️⃣ Mettre à jour la config mobile

Ouvrez `/Users/dannezri/Desktop/Pulse/mobile/src/config/api.ts` :

**Ligne 28, remplacez par VOTRE IP :**
```typescript
return 'http://192.168.0.23:9000';  // ← Votre IP locale
```

**Exemple :**
```typescript
if (Platform.OS === 'ios') {
  if (isSimulator) {
    return 'http://localhost:9000';
  }
  // ⚠️ REMPLACEZ PAR VOTRE IP
  return 'http://192.168.1.45:9000';  // ← Mettez VOTRE IP ici
}
```

---

### 4️⃣ Nettoyer les caches et relancer

```bash
cd /Users/dannezri/Desktop/Pulse/mobile
./clear-all-caches.sh
npx expo start --clear
```

Puis **[i]** pour lancer sur votre iPhone.

---

## 🧪 Tests de validation

### A. Backend accessible depuis le Mac

```bash
curl http://localhost:9000/health
# Attendu: {"status":"healthy"}
```

### B. Backend accessible depuis l'iPhone

Sur votre Mac :
```bash
curl http://VOTRE_IP:9000/health
# Ex: curl http://192.168.0.23:9000/health
```

Si cette commande échoue, **c'est un problème de firewall**.

**Solution Firewall Mac :**
1. Préférences Système → Sécurité et confidentialité → Coupe-feu
2. Options du coupe-feu
3. Autoriser `Python` (ou décocher "Bloquer toutes les connexions entrantes")

### C. App mobile affiche les données

Ouvrez l'app → Les logs Metro devraient montrer :
```
[API Config] Using API URL: http://192.168.0.23:9000
[useBriefData] 📡 Appel API generateBrief
[useBriefData] ✅ Réponse reçue
```

**Pas d'erreur 61 !** ✅

---

## 🔧 Diagnostic automatique

Lancez ce script pour tout vérifier :

```bash
cd /Users/dannezri/Desktop/Pulse
chmod +x check-backend.sh
./check-backend.sh
```

Il vous dira :
- ✅ Backend démarré ou ❌ Non démarré
- ✅ Port 9000 ouvert ou ❌ Fermé
- ✅ Votre IP locale

---

## 🆘 Troubleshooting

### Erreur : "Address already in use"

Le port 9000 est déjà pris. Trouvez le processus :
```bash
lsof -i :9000
kill -9 <PID>
```

### Erreur : "Module not found" au démarrage backend

Installez les dépendances :
```bash
cd /Users/dannezri/Desktop/Pulse/backend
pip install -r requirements.txt
```

### L'app dit toujours "Connection refused"

1. **Vérifiez l'IP dans `api.ts`** (ligne 28)
2. **Vérifiez le firewall Mac**
3. **Assurez-vous que Mac et iPhone sont sur le même WiFi**
4. **Redémarrez Metro** : `npx expo start --clear`

### Le port 8097 apparaît dans les logs

C'est probablement un ancien service. Ignorez-le si l'app fonctionne.

Si vous voulez le tuer :
```bash
lsof -i :8097
kill -9 <PID>
```

---

## 📋 Checklist complète

- [ ] Backend démarré (`ps aux | grep api_server`)
- [ ] Port 9000 ouvert (`lsof -i :9000`)
- [ ] Backend répond (`curl http://localhost:9000/health`)
- [ ] IP locale trouvée (`ifconfig`)
- [ ] IP mise à jour dans `mobile/src/config/api.ts`
- [ ] Firewall Mac autorise Python
- [ ] Mac et iPhone sur le même WiFi
- [ ] Caches mobile nettoyés (`./clear-all-caches.sh`)
- [ ] Metro redémarré (`npx expo start --clear`)
- [ ] App relancée sur iPhone
- [ ] Pas d'erreur 61 dans les logs

---

**Une fois le backend accessible, l'erreur `onSubmit is not a function` devrait aussi disparaître car le hook `useFeedback` pourra charger correctement ! 🎯**
