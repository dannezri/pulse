# 🔄 Redémarrage du Backend pour Activer les Bulles d'Alerte

## 📋 Diagnostic

✅ **Frontend** : Les styles Markdown sont configurés correctement  
❌ **Backend** : Les nouveaux prompts ne sont pas chargés (serveur démarré avant les modifications)

**Solution** : Redémarrer le serveur backend

## 🚀 Instructions de Redémarrage

### Option 1 : Via le Terminal Existant (95.txt)

1. **Allez dans le terminal 95** (celui qui affiche les logs du serveur)
2. **Stoppez le serveur** : `Ctrl+C`
3. **Redémarrez le serveur** :

```bash
python3 api_server_ambient.py
```

### Option 2 : Kill et Redémarrer

Dans n'importe quel terminal :

```bash
# Tuer le processus sur le port 9000
lsof -ti:9000 | xargs kill -9

# Attendre 1 seconde
sleep 1

# Redémarrer le serveur
cd /Users/dannezri/Desktop/Pulse/backend
python3 api_server_ambient.py
```

### Option 3 : Script de Redémarrage Rapide

```bash
cd /Users/dannezri/Desktop/Pulse/backend
./restart_server.sh
```

## ✅ Vérification Post-Redémarrage

Après le redémarrage, vous devriez voir dans les logs :

```
🚀 Démarrage de Pulse - Ambient Concierge API sur http://0.0.0.0:9000
📊 Endpoints disponibles:
   - GET  /api/baselines/{user_id}
   - POST /api/insights/prioritized
   - GET  /api/insights/latest
   - POST /api/v1/analyze-event  🆕 Smart Cache
```

## 🧪 Test des Blockquotes

### 1. Dans l'App Mobile

1. **Ouvrez l'événement "Séance de Padle"**
2. **Tapez sur le bouton refresh vert** (en haut à droite)
3. **Attendez 2-5 secondes** (nouvelle analyse OpenAI)
4. **Les bulles d'alerte doivent apparaître** 🎨

### 2. Vérification Backend

Exécutez le script de vérification :

```bash
cd /Users/dannezri/Desktop/Pulse/backend
python3 check_blockquotes.py
```

Vous devriez voir :

```
✅ BLOCKQUOTES TROUVÉES !
📊 Statistiques:
   - Lignes totales: XX
   - Lignes avec blockquote (>): XX

📝 Exemples de blockquotes:
   1. > **Avant l'événement (30 min)**
   2. > - Prendre 20g de glucides rapides
   ...
```

## 🎨 Exemple Visuel Attendu

Après le redémarrage et le refresh, l'analyse devrait ressembler à :

```markdown
# 🔴 Diagnostic Flash

Ton corps n'est pas prêt pour une séance de padel.

## 💡 Le "Pourquoi"

Le manque de sommeil est critique. Avec **0h00 de sommeil**...

## ⚡ Actions Immédiates

> **Avant l'événement (30 min)**
> - Repos immédiat : Priorité sommeil de qualité
> - Nourriture adéquate : Repas riche en glucides

> **Pendant l'événement**
> - Hydratation constante : 200ml/15min
> - Surveillance fréquence cardiaque

> **Après l'événement**
> - Récupération active : Étirements doux
> - Nutrition réparatrice : Repas équilibré
```

Les sections avec `>` s'afficheront comme des **bulles avec bordure rouge** !

## 🐛 Troubleshooting

### Le serveur ne redémarre pas

**Erreur** : `Address already in use`

**Solution** :
```bash
lsof -ti:9000 | xargs kill -9
sleep 1
python3 api_server_ambient.py
```

### Les blockquotes n'apparaissent toujours pas

**Vérifiez** :

1. ✅ Le serveur a bien été redémarré APRÈS les modifications
2. ✅ Vous avez forcé un refresh dans l'app (bouton vert)
3. ✅ Le script `check_blockquotes.py` confirme la présence de `>`

**Commande de debug** :
```bash
cd /Users/dannezri/Desktop/Pulse/backend
python3 check_blockquotes.py | grep "BLOCKQUOTES"
```

### L'IA ne génère toujours pas de blockquotes

**Vérifiez que les fichiers modifiés sont bien chargés** :

```bash
cd /Users/dannezri/Desktop/Pulse/backend

# Vérifier que le prompt contient bien "blockquote"
grep -n "blockquote" llm_client.py
grep -n "blockquote" services/ai_service.py
```

Devrait afficher :
```
llm_client.py:143:- > blockquote pour les ALERTES et ACTIONS IMMÉDIATES
services/ai_service.py:226:IMPORTANT : Pour les actions concrètes, utilise des blockquotes (>)
```

## 📊 Checklist Finale

- [ ] Serveur backend redémarré
- [ ] Logs confirment le démarrage réussi
- [ ] App mobile ouverte sur l'événement
- [ ] Bouton refresh tapé
- [ ] Nouvelle analyse générée (2-5 sec)
- [ ] Script check_blockquotes.py confirme les `>`
- [ ] Bulles d'alerte visibles dans l'app 🎨

## 🎯 Résultat Attendu

**Avant** (analyse du cache) :
- Texte plat avec des listes à puces simples
- Pas de bulles visuelles

**Après** (nouvelle analyse) :
- 🟢/🟡/🔴 Emoji de couleur dans le titre
- **Métriques en gras vert** (HRV, Sommeil, etc.)
- 🎨 **Bulles d'alerte rouges** pour les actions
- Ombre portée sur les blockquotes
- Coins arrondis

---

**Note** : Le premier appel après le redémarrage prendra 2-5 secondes (OpenAI), puis les suivants seront instantanés grâce au Smart Cache.
