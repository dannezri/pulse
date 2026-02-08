# Test des Blockquotes (Bulles d'Alerte)

## 🧪 Test Rapide

Pour tester si les blockquotes s'affichent correctement, voici ce qu'il faut faire :

### 1. Forcer une Nouvelle Analyse

Dans l'app, **tapez sur le bouton vert de refresh** (en haut à droite) pour forcer une nouvelle analyse avec le nouveau prompt.

### 2. Exemple de Markdown avec Blockquotes

Voici ce que l'IA devrait générer maintenant :

```markdown
# 🔴 Diagnostic Flash

Ton corps n'est pas prêt pour une séance de padel.

## 💡 Le "Pourquoi"

Le manque de sommeil est critique. Avec **0h00 de sommeil** lors des dernières 24 heures, ton corps manque de temps de récupération essentiel.

## ⚡ Actions Immédiates

> **Avant l'événement (30 min)**
> - Repos immédiat : Priorite une période de sommeil de qualité
> - Nourriture adéquate : Consomme un repas riche en glucides complexes

> **Pendant l'événement**
> - Hydratation régulière : 200ml toutes les 15 minutes
> - Surveillance de la fréquence cardiaque

> **Après l'événement**
> - Repas de récupération dans les 30 minutes
> - Étirements légers pendant 10 minutes
```

### 3. Rendu Attendu

Les sections avec `>` (blockquotes) doivent s'afficher comme des **bulles avec** :
- ✅ Fond sombre (#1C1C1E)
- ✅ Bordure rouge à gauche (4px)
- ✅ Coins arrondis (12px)
- ✅ Ombre portée rouge

### 4. Vérifier dans les Logs Backend

Si vous avez accès aux logs backend, vérifiez que la réponse contient des `>` :

```bash
cd backend
tail -f logs/api.log | grep "insight"
```

## 🐛 Si les Bulles ne S'affichent Pas

### Problème 1 : react-native-markdown-display ne supporte pas les blockquotes

**Solution** : Vérifier la version

```bash
cd mobile
npm list react-native-markdown-display
```

Devrait afficher : `react-native-markdown-display@7.0.2`

### Problème 2 : L'IA ne génère pas de blockquotes

**Test manuel** : Créer un insight de test avec des blockquotes directement dans la BDD

```sql
-- Dans Supabase SQL Editor
UPDATE insights
SET instruction_text = '# 🔴 Test

## Actions

> **Test Blockquote**
> - Action 1
> - Action 2'
WHERE user_id = 'VOTRE_USER_ID'
AND calendar_event_id = 'VOTRE_EVENT_ID';
```

Puis rafraîchir l'app pour voir si la bulle s'affiche.

### Problème 3 : Les styles ne sont pas appliqués

**Solution** : Clear le cache Metro

```bash
cd mobile
npm run start:clear
```

## 📊 Exemple de Test Complet

### Markdown de Test

```markdown
# 🟢 Test des Bulles

Ceci est un paragraphe normal.

## Section avec Bulle

> **Ceci est une bulle d'alerte**
> - Point 1
> - Point 2
> - Point 3

Texte après la bulle.

> **Deuxième bulle**
> Avec du texte simple

Fin du test.
```

### Rendu Attendu

1. Titre vert "Test des Bulles"
2. Paragraphe blanc normal
3. Titre orange "Section avec Bulle"
4. **BULLE 1** (fond noir, bordure rouge, arrondie)
5. Texte blanc normal
6. **BULLE 2** (même style)
7. Texte blanc final

## 🔧 Debug Mode

Pour activer les logs de debug dans react-native-markdown-display, ajoutez ceci temporairement :

```typescript
<Markdown 
  style={markdownStyles}
  debugPrintTree={true}  // Active les logs de parsing
>
  {analysisData.insight}
</Markdown>
```

Regardez les logs dans la console pour voir si les blockquotes sont bien parsées.

## ✅ Checklist de Validation

- [ ] Version react-native-markdown-display@7.0.2+
- [ ] Styles blockquote présents dans markdownStyles
- [ ] Prompt backend demande des blockquotes
- [ ] Cache Metro cleared
- [ ] Nouvelle analyse forcée (bouton refresh)
- [ ] Blockquotes présentes dans analysisData.insight

## 🎯 Solution Rapide

**Le plus simple** : Tapez sur le bouton refresh vert en haut à droite de l'écran "Analyse IA". Si le backend est à jour avec le nouveau prompt, vous devriez voir les bulles apparaître immédiatement !

Si ça ne fonctionne toujours pas, c'est que l'IA ne génère pas encore de blockquotes. Dans ce cas, vérifiez que le backend a bien été redémarré avec les nouveaux prompts.
