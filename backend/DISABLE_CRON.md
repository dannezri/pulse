# ⚠️ Désactiver l'Ancien Cron

## 🔄 Transition : Cron → launchd

Vous utilisez maintenant **launchd** au lieu de cron pour la synchronisation automatique Oura.

### Pourquoi ?

- ✅ Meilleure intégration macOS
- ✅ Pas de problèmes de permissions
- ✅ Logs séparés et plus clairs
- ✅ Rattrapage automatique si manqué
- ✅ Plus fiable et stable

---

## 🛑 Désactiver le Cron Précédent

Si vous aviez configuré un cron job pour Oura, il faut le désactiver pour éviter les doublons.

### Étape 1 : Vérifier si un Cron Existe

```bash
crontab -l
```

Si vous voyez une ligne comme :
```
0 * * * * cd /Users/dannezri/Desktop/Pulse/backend && ./run_oura_import_full.sh >> /tmp/oura_import.log 2>&1
```

→ Vous devez la désactiver.

### Étape 2 : Éditer le Crontab

```bash
crontab -e
```

**Dans l'éditeur :**

1. Appuyez sur `i` pour passer en mode insertion (si vi/vim)
2. Ajoutez un `#` au début de la ligne Oura pour la commenter :
   ```
   # 0 * * * * cd /Users/dannezri/Desktop/Pulse/backend && ./run_oura_import_full.sh >> /tmp/oura_import.log 2>&1
   ```
3. Appuyez sur `ESC` puis tapez `:wq` et `ENTRÉE` pour sauvegarder

**Ou supprimez complètement la ligne** (avec `dd` en mode normal dans vi).

### Étape 3 : Vérifier

```bash
crontab -l
```

La ligne Oura devrait être commentée (avec #) ou absente.

---

## ✅ Confirmer que launchd est Actif

```bash
# Vérifier le service
launchctl list com.pulse.oura-sync

# Ou utiliser le script de monitoring
cd /Users/dannezri/Desktop/Pulse/backend
./monitor_oura_sync.sh
```

---

## 📝 Ancien vs Nouveau

| Aspect | Cron (ancien) | launchd (nouveau) |
|--------|---------------|-------------------|
| **Fichier config** | `crontab -e` | `~/Library/LaunchAgents/com.pulse.oura-sync.plist` |
| **Script** | `run_oura_import_full.sh` | `run_oura_sync.py` |
| **Logs** | `/tmp/oura_import.log` | `/tmp/oura_sync.error.log` et `/tmp/oura_sync.log` |
| **Statut** | Difficile à vérifier | `launchctl list com.pulse.oura-sync` |
| **Permissions** | ❌ Problématique | ✅ Fonctionne |

---

## 🔧 Nettoyer les Anciens Logs

Si vous n'avez plus besoin des anciens logs cron :

```bash
# Voir la taille
ls -lh /tmp/oura_import.log

# Supprimer (optionnel)
rm /tmp/oura_import.log
```

---

## 🆘 Problème ?

Si vous avez désactivé le cron mais que les synchronisations ne fonctionnent plus :

```bash
# 1. Vérifier que launchd est actif
launchctl list com.pulse.oura-sync

# 2. Si absent, charger le service
launchctl load ~/Library/LaunchAgents/com.pulse.oura-sync.plist

# 3. Tester manuellement
launchctl start com.pulse.oura-sync

# 4. Vérifier les logs
tail -20 /tmp/oura_sync.error.log
```

---

**Note :** Vous pouvez garder les deux systèmes en parallèle si vous le souhaitez, mais ce n'est pas recommandé (risque de doublons et de conflits).
