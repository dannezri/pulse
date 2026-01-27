# 🌐 Trouver votre IP locale

## Méthode 1 : Terminal

```bash
ipconfig getifaddr en0
```

Si ça ne marche pas, essayez :
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

## Méthode 2 : Préférences Système

1. Ouvrir **Préférences Système**
2. **Réseau**
3. Sélectionner votre connexion WiFi (généralement en vert)
4. L'IP est affichée : "WiFi est connecté à XXX et a l'adresse IP **192.168.1.15**"

## Une fois que vous avez votre IP

Éditez le fichier :
```
mobile/src/config/api.ts
```

Ligne 28 et 37, remplacez `192.168.1.15` par VOTRE IP :

```typescript
// Ligne 28 (iOS device)
return 'http://192.168.1.15:9000';  // ← Remplacez par votre IP

// Ligne 37 (Android device)
return 'http://192.168.1.15:9000';  // ← Remplacez par votre IP
```

Sauvegardez et rebuild !
