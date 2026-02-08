# 🚀 Service launchd Oura Sync

## ✅ Service Actif

Le service de synchronisation automatique Oura est maintenant actif via **launchd** (le système natif macOS).

### 📋 Configuration

| Paramètre | Valeur |
|-----------|--------|
| **Nom du service** | `com.pulse.oura-sync` |
| **Fichier plist** | `~/Library/LaunchAgents/com.pulse.oura-sync.plist` |
| **Script d'exécution** | `/Users/dannezri/Desktop/Pulse/backend/run_oura_sync.py` |
| **Fréquence** | Toutes les heures (3600 secondes) |
| **Logs sortie** | `/tmp/oura_sync.log` |
| **Logs erreur** | `/tmp/oura_sync.error.log` |
| **Démarrage auto** | ✅ Oui (au login) |

---

## 🔧 Commandes de Gestion

### Vérifier le Statut

```bash
# Voir si le service est chargé
launchctl list | grep pulse

# Voir les détails du service
launchctl list com.pulse.oura-sync
```

### Contrôler le Service

```bash
# Démarrer manuellement (sans attendre l'heure)
launchctl start com.pulse.oura-sync

# Arrêter le service
launchctl stop com.pulse.oura-sync

# Décharger le service (désactiver)
launchctl unload ~/Library/LaunchAgents/com.pulse.oura-sync.plist

# Recharger le service (activer)
launchctl load ~/Library/LaunchAgents/com.pulse.oura-sync.plist
```

### Redémarrer Après Modification

Si vous modifiez le fichier plist :

```bash
# Décharger, puis recharger
launchctl unload ~/Library/LaunchAgents/com.pulse.oura-sync.plist
launchctl load ~/Library/LaunchAgents/com.pulse.oura-sync.plist
```

---

## 📊 Surveiller les Logs

### Logs en Temps Réel

```bash
# Voir les nouvelles lignes au fur et à mesure
tail -f /tmp/oura_sync.error.log

# Ou voir les logs de sortie (stdout)
tail -f /tmp/oura_sync.log
```

### Analyser l'Historique

```bash
# Voir les 50 dernières lignes
tail -50 /tmp/oura_sync.error.log

# Compter les exécutions réussies
grep -c "HTTP/2 201 Created" /tmp/oura_sync.error.log

# Voir les erreurs uniquement
grep "ERROR" /tmp/oura_sync.error.log

# Voir quand le service s'est exécuté
grep "Starting FULL Oura" /tmp/oura_sync.error.log
```

### Nettoyer les Logs

```bash
# Vider les logs (ils peuvent devenir gros)
> /tmp/oura_sync.error.log
> /tmp/oura_sync.log
```

---

## 🔍 Diagnostic

### Le Service est-il Actif ?

```bash
launchctl list com.pulse.oura-sync
```

**Interprétation :**
- Si vous voyez des détails → ✅ Le service est chargé
- Si vous voyez "Could not find service" → ❌ Le service n'est pas chargé

### Le Service s'Exécute-t-il ?

```bash
# Vérifier la dernière exécution
tail -20 /tmp/oura_sync.error.log | grep "Starting"
```

### Tester Manuellement

```bash
# Lancer une synchronisation maintenant
launchctl start com.pulse.oura-sync

# Attendre 5 secondes et vérifier
sleep 5 && tail -30 /tmp/oura_sync.error.log
```

---

## 🛠️ Modifier la Fréquence

### Changer l'Intervalle de Synchronisation

Éditez le fichier plist :

```bash
nano ~/Library/LaunchAgents/com.pulse.oura-sync.plist
```

Modifiez la ligne `StartInterval` :

```xml
<key>StartInterval</key>
<integer>3600</integer>  <!-- En secondes -->
```

**Exemples :**
- Toutes les 30 minutes : `1800`
- Toutes les 2 heures : `7200`
- Toutes les 6 heures : `21600`
- Une fois par jour : `86400`

Puis rechargez le service :

```bash
launchctl unload ~/Library/LaunchAgents/com.pulse.oura-sync.plist
launchctl load ~/Library/LaunchAgents/com.pulse.oura-sync.plist
```

---

## 🚨 Désactiver Complètement

Si vous voulez arrêter la synchronisation automatique :

```bash
# Décharger le service
launchctl unload ~/Library/LaunchAgents/com.pulse.oura-sync.plist

# Optionnel : supprimer le fichier plist
rm ~/Library/LaunchAgents/com.pulse.oura-sync.plist
```

---

## ⚙️ Configuration Avancée

### Exécuter à des Heures Précises

Si vous préférez des heures fixes plutôt qu'un intervalle, modifiez le plist :

```xml
<!-- Remplacer StartInterval par StartCalendarInterval -->
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>8</integer>  <!-- 8h du matin -->
    <key>Minute</key>
    <integer>0</integer>
</dict>
```

Pour plusieurs horaires :

```xml
<key>StartCalendarInterval</key>
<array>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <dict>
        <key>Hour</key>
        <integer>20</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</array>
```

---

## 📝 Notes Importantes

### Différences avec Cron

| Cron | launchd |
|------|---------|
| Standard Unix | Natif macOS |
| Problèmes de permissions | Meilleure intégration |
| Pas de rattrapage | Rattrapage si manqué |
| Simple | Plus de fonctionnalités |

### Désactiver l'Ancien Cron

Si vous aviez configuré un cron auparavant, désactivez-le :

```bash
# Éditer le crontab
crontab -e

# Commenter ou supprimer la ligne Oura
# (ajouter # au début de la ligne)
```

---

## 🆘 Dépannage

### Erreur : "Operation not permitted"

Si vous voyez cette erreur, donnez l'accès complet au disque à Python :

1. **Préférences Système** → **Confidentialité et sécurité**
2. **Accès complet au disque**
3. Ajoutez `/Library/Frameworks/Python.framework/Versions/3.10/bin/python3`

### Le Service ne Démarre pas au Login

Vérifiez que `RunAtLoad` est à `true` dans le plist :

```xml
<key>RunAtLoad</key>
<true/>
```

### Les Logs ne se Créent pas

Vérifiez les permissions sur `/tmp/` :

```bash
ls -la /tmp/oura_sync*
```

---

## ✨ Avantages de launchd

✅ **Intégration macOS native**  
✅ **Meilleure gestion des permissions**  
✅ **Rattrapage automatique si l'exécution est manquée**  
✅ **Logs séparés (stdout et stderr)**  
✅ **Pas de problème avec les variables d'environnement**  
✅ **Démarre automatiquement au login**

---

**Mis en place le :** 28 janvier 2026  
**Version :** 1.0.0
