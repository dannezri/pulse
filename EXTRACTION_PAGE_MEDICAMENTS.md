# Extraction Complète - Page Mes Médicaments

## 📱 Structure Globale de la Page

La page "Mes Médicaments" est accessible depuis le profil et se compose de **2 onglets principaux** :
1. **Mes Médicaments** - Gestion et suivi des traitements actuels
2. **Historique** - Historique complet des prises jour par jour

---

## 🏠 ONGLET 1 : MES MÉDICAMENTS

### 1. Header Principal
```
┌─────────────────────────────────────┐
│  ←        Médicaments         +     │
└─────────────────────────────────────┘
```
- **Bouton gauche** : Retour (←)
- **Titre centré** : "Médicaments"
- **Bouton droit** : Ajouter un médicament (+)

### 2. Barre d'Onglets
```
┌──────────────────┬──────────────────┐
│ 💊 Mes Médicaments │ 📅 Historique    │
│    [ACTIF]        │                  │
└──────────────────┴──────────────────┘
```

---

### 3. Section Hero
**Titre :**
```
Vos Médicaments
```

**Sous-titre :**
```
Analyse détaillée de l'impact énergétique de chaque traitement
```

---

### 4. Analyse Globale des Traitements (TreatmentOverview)

**Card avec gradient violet/transparent**

**Header :**
```
┌──────────────────────────────────────────────┐
│ 🧠  Analyse de vos traitements      ✨ Gemini │
└──────────────────────────────────────────────┘
```

**Badge si nouveaux médicaments :**
```
⚠️ X nouveau(x)
```

**Contenu de l'analyse (Généré par Gemini) :**
> _Cette section affiche une analyse textuelle complète générée dynamiquement par l'IA Gemini._
> 
> L'analyse est structurée avec :
> - **Titres de niveau 2 (##)** : Sections principales
> - **Titres de niveau 3 (###)** : Sous-sections
> - **Listes à puces (• )** : Points clés
> - **Texte en gras (\*\*texte\*\*)** : Emphases importantes
> - **Paragraphes normaux** : Explications détaillées

**Exemple de contenu d'analyse :**
```markdown
## Vue d'ensemble de vos traitements

Vous prenez actuellement 2 médicaments quotidiens pour gérer votre santé mentale et physique.

### Médicaments actifs

• **Médicament A** - Antidépresseur avec effet stimulant
• **Médicament B** - Anxiolytique avec légère sédation

### Impact global sur votre énergie

L'analyse de votre traitement montre un **impact énergétique modéré**...
```

**État de chargement :**
```
⏳ Analyse détaillée en cours avec Gemini...
```

---

### 5. Statistiques d'Impact (Stats Overview)

**Trois cards affichées côte à côte :**

#### Card 1 : Aujourd'hui
```
┌──────────────┐
│   🕐         │
│   [NOMBRE]   │
│ Aujourd'hui  │
└──────────────┘
```
- **Icône** : Horloge (Clock)
- **Valeur** : Nombre de prises du jour
- **Label** : "Aujourd'hui"

#### Card 2 : Total
```
┌──────────────┐
│   💊         │
│   [NOMBRE]   │
│    Total     │
└──────────────┘
```
- **Icône** : Pilule (Pill)
- **Valeur** : Nombre total de médicaments
- **Label** : "Total"

#### Card 3 : Impact Total (HERO)
```
┌─────────────────┐
│   📈 / 📉       │
│  +X.X% / -X.X%  │
│  Impact Total   │
└─────────────────┘
```
- **Icône** : TrendingUp (vert) / TrendingDown (rouge) / Activity (gris)
- **Valeur** : Pourcentage d'impact (ex: "+5.2%" ou "-3.8%")
- **Label** : "Impact Total"
- **Couleurs** :
  - Vert si positif
  - Rouge si négatif
  - Gris si neutre

---

### 6. Section "Aujourd'hui" (si prises du jour)

**Header :**
```
🕐 Aujourd'hui                           [X]
```
- **Icône** : Clock
- **Titre** : "Aujourd'hui"
- **Badge** : Nombre de prises du jour

**Liste des médicaments du jour** → _Voir structure MedicationCard ci-dessous_

---

### 7. Section "Tous les médicaments"

**Header :**
```
💊 Tous les médicaments                  [X]
```
- **Icône** : Pill
- **Titre** : "Tous les médicaments"
- **Badge** : Nombre total de médicaments

#### 7a. État vide (si aucun médicament)
```
┌──────────────────────────────────────┐
│                                       │
│           💊 (grand icône)            │
│                                       │
│   Aucun médicament enregistré        │
│                                       │
│   Commencez par ajouter vos          │
│   médicaments pour suivre vos        │
│   traitements et obtenir des         │
│   analyses plus précises.            │
│                                       │
│   [+ Ajouter un médicament]          │
│                                       │
└──────────────────────────────────────┘
```

#### 7b. Liste des médicaments (si présents)
→ _Voir structure MedicationCard ci-dessous_

**État de chargement :**
```
⏳ Chargement des médicaments...
```

---

### 8. Structure d'une MedicationCard

**Card complète avec gradient et bordure colorée selon l'impact**

```
┌─────────────────────────────────────────────┐
│ 💊  [NOM DU MÉDICAMENT]          [Récurrent/Ponctuel]  ⋮  │
│                                                              │
│     [X × DOSAGE UNIT] • [FRÉQUENCE]/jour                    │
│                                                              │
├─────────────────────────────────────────────┤
│ ┌─ IMPACT SUR L'ÉNERGIE ─────────────────┐ │
│ │  📈/📉  Impact sur l'énergie            │ │
│ │         +X.X% / -X.X%                    │ │
│ │                                          │ │
│ │  ⚡ [Phase aiguë/chronique]  Jour XX    │ │
│ │                                          │ │
│ │  Description de l'impact...              │ │
│ │                                          │ │
│ │  ████████░░ 80%                          │ │
│ │  [Description de la phase]               │ │
│ └──────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│ 🕐 Heures de prise                          │
│    [08:00]  [14:00]  [20:00]                │
├─────────────────────────────────────────────┤
│         [Analyse complète ▼]                 │
└─────────────────────────────────────────────┘
│ 📅 Début: Il y a X jours  🕐 Prochaine: HH:MM│
└─────────────────────────────────────────────┘
```

#### 8.1. Header de la Card
- **Icône pilule** : 💊 dans un badge violet
- **Nom** : Nom du médicament
- **Badge type** : 
  - "🔄 Récurrent" (violet) si traitement continu
  - "📅 Ponctuel" (orange) si prise unique
- **Menu actions** : ⋮ (trois points)
  - ✏️ Modifier la posologie
  - ⏹️ Arrêter le traitement
  - 🗑️ Supprimer

#### 8.2. Ligne Dosage
```
[¼/½/¾/1/1½/2/2½ nombre] × [dosage] [unité] • [fréquence]x/jour
```
Exemples :
- "1 × 10 mg • 2x/jour"
- "½ × 20 mg • 1x/jour"

#### 8.3. Section Impact Énergétique
**Card avec gradient (vert si positif, rouge si négatif)**

**Grande icône d'impact :**
- 📈 TrendingUp (vert) = Impact positif
- 📉 TrendingDown (rouge) = Impact négatif
- 〰️ Activity (gris) = Impact neutre

**Label :**
```
IMPACT SUR L'ÉNERGIE
```

**Valeur héro (grande) :**
```
+5.2%  ou  -3.8%
```

**Badge de phase :**
```
⚡ Phase aiguë | Jour 5
⚡ Phase d'adaptation | Jour 15
⚡ Phase chronique | Jour 45
```

**Description :**
```
Texte explicatif de l'impact sur l'énergie...
```

**Barre de progression :**
```
████████░░ 80%
[Description de la phase du traitement]
```

Descriptions possibles :
- "Les premiers jours montrent souvent les effets les plus marqués"
- "Votre corps s'adapte progressivement au traitement"
- "Votre corps s'est adapté au traitement, l'effet est stabilisé"

#### 8.4. Heures de prise
```
🕐 Heures de prise
   [08:00]  [14:00]  [20:00]
```

#### 8.5. Bouton Analyse Complète
```
┌──────────────────────────┐
│  Analyse complète    ▼   │
└──────────────────────────┘
```

**Lorsque déplié :**
```
┌──────────────────────────┐
│  Moins de détails    ▲   │
└──────────────────────────┘
```

#### 8.6. Section Expandable (Analyse Détaillée)

##### Card 1 : Fonction du médicament
```
┌─────────────────────────────────────┐
│ 💊 Fonction du médicament           │
├─────────────────────────────────────┤
│ [Texte explicatif généré par Gemini]│
│ décrivant à quoi sert ce médicament│
└─────────────────────────────────────┘
```

##### Card 2 : Impact sur le corps
```
┌─────────────────────────────────────┐
│ 🏃 Impact sur le corps              │
├─────────────────────────────────────┤
│ [Texte explicatif généré par Gemini]│
│ sur les effets physiologiques       │
└─────────────────────────────────────┘
```

##### Card 3 : Ressenti quotidien
```
┌─────────────────────────────────────┐
│ 🕐 Ressenti quotidien               │
├─────────────────────────────────────┤
│ [Texte explicatif généré par Gemini]│
│ sur le ressenti au quotidien        │
└─────────────────────────────────────┘
```

##### Card 4 : À surveiller
```
┌─────────────────────────────────────┐
│ ⚠️ À surveiller                     │
├─────────────────────────────────────┤
│ [Observations et précautions]       │
│ [Texte généré par Gemini]          │
└─────────────────────────────────────┘
```
**Couleur** : Badge et bordure orange/jaune

##### Card 5 : Profil d'efficacité sur 24h
```
┌─────────────────────────────────────┐
│ 📊 Profil d'efficacité sur 24h     │
├─────────────────────────────────────┤
│ Visualisez comment le médicament    │
│ agit tout au long de la journée     │
│                                      │
│ [GRAPHIQUE COURBE HORAIRE]          │
│ - Concentration                      │
│ - Efficacité                         │
│ - Effets secondaires                 │
│                                      │
│ Marqueurs de prise : 📍 08:00 etc.  │
└─────────────────────────────────────┘
```

##### Card 6 : Pharmacocinétique
```
┌─────────────────────────────────────┐
│ ⚡ Pharmacocinétique                │
├─────────────────────────────────────┤
│ Pic d'efficacité:  ~2-3h après      │
│ Demi-vie:          Variable         │
│ Dosage ajusté:     [X] mg (si ≠1cp)│
└─────────────────────────────────────┘
```

##### Card 7 : Durée du traitement
```
┌─────────────────────────────────────┐
│ 📅 Durée du traitement              │
├─────────────────────────────────────┤
│ Début:   [Aujourd'hui/Hier/Il y a X]│
│ Durée:   [X] jours                   │
│ Phase:   [Phase aiguë/adaptation/   │
│           chronique]                 │
└─────────────────────────────────────┘
```

##### Card 8 : Recommandations (si impact > 5%)
**Vert si positif, rouge si négatif**
```
┌─────────────────────────────────────┐
│ ✅ Excellent / ⚠️ Attention          │
├─────────────────────────────────────┤
│ Impact [positif/négatif] important  │
│ ([±X.X%]). [Recommandation]         │
└─────────────────────────────────────┘
```

Messages possibles :
- **Négatif** : "Impact négatif important (-X.X%). Consultez votre médecin si cela affecte votre quotidien."
- **Positif** : "Impact positif marqué (+X.X%). Le traitement semble bien adapté à votre profil."

##### Card 9 : Notes (si présentes)
```
┌─────────────────────────────────────┐
│ ℹ️ Notes                            │
├─────────────────────────────────────┤
│ [Notes personnelles de l'utilisateur│
│  sur ce médicament]                 │
└─────────────────────────────────────┘
```

#### 8.7. Footer de la Card
```
📅 Début: Il y a X jours/semaines/mois    🕐 Prochaine: HH:MM
```

---

### 9. Bouton d'Ajout (si médicaments présents)
```
┌──────────────────────────────────┐
│  + Ajouter un médicament         │
└──────────────────────────────────┘
```
**Style** : Bouton violet pleine largeur avec ombre

---

### 10. Section "Comment ça marche ?"

**Header :**
```
⚡ Comment ça marche ?
```

**Card explicative :**
```
┌─────────────────────────────────────────────────┐
│ L'impact énergétique est calculé en temps réel  │
│ grâce à :                                        │
│                                                  │
│ 💊  Dosage total                                │
│     Nombre de comprimés × dosage unitaire       │
│                                                  │
│ 🕐  Pharmacocinétique                           │
│     Courbe d'absorption et élimination          │
│                                                  │
│ 📅  Adaptation chronique                        │
│     Effet à long terme selon la durée           │
│                                                  │
│ 🏃  Profil personnalisé                         │
│     Poids ML adapté à votre organisme           │
└─────────────────────────────────────────────────┘
```

---

### 11. Section "Pourquoi c'est important ?"

**Header :**
```
ℹ️ Pourquoi c'est important ?
```

**Card avec 3 items :**

```
┌─────────────────────────────────────────────────┐
│ ⚡  Impact en temps réel                        │
│     Visualisez comment chaque médicament        │
│     affecte votre énergie                       │
├─────────────────────────────────────────────────┤
│ 🎯  Dosage optimisé                             │
│     Ajustez vos doses selon votre ressenti      │
│     et l'impact mesuré                          │
├─────────────────────────────────────────────────┤
│ 📊  Analyses précises                           │
│     Des insights basés sur la pharmacocinétique │
│     et vos données                              │
└─────────────────────────────────────────────────┘
```

---

## 📅 ONGLET 2 : HISTORIQUE

### 1. Barre de Navigation Mensuelle (Horizontale)
```
┌────────────────────────────────────────────────┐
│  [Févr. '26] [Janv. '26] [Déc. '25] [Nov. '25]│
│      3           12          28         25     │
│    (actif)                                     │
└────────────────────────────────────────────────┘
```
- **Boutons mois** : Nom du mois abrégé + année (2 derniers chiffres)
- **Badge** : Nombre de jours avec des prises
- **Badge vert** : Si taux de complétion = 100%
- **Scroll horizontal** : Pour naviguer entre les mois

---

### 2. Card Récapitulatif du Mois

```
┌─────────────────────────────────────────────────┐
│ 📅  [Février 2026]                              │
│     Récapitulatif du mois                       │
├─────────────────────────────────────────────────┤
│ ┌──────────┬──────────┬──────────┐             │
│ │    📅    │    ✅    │    🏆    │             │
│ │    12    │    48    │    85%   │             │
│ │   Jours  │  Prises  │ Complété │             │
│ └──────────┴──────────┴──────────┘             │
│                                                  │
│ ⚠️ Variations du traitement (2)                 │
│                                                  │
│ ┃ Médicament A                                  │
│ ┃ 🆕 Traitement ajouté                          │
│ ┃ Le 5 février                                  │
│                                                  │
│ ┃ Médicament B                                  │
│ ┃ 💊 Dosage modifié: 1 cp (10 mg) → 2 cp       │
│ ┃ Le 12 février                                 │
│                                                  │
│ ┃ Médicament C                                  │
│ ┃ ⏹️ Traitement arrêté                          │
│ ┃ Le 18 février                                 │
└─────────────────────────────────────────────────┘
```

**Statistiques :**
- **Jours** : Nombre de jours avec au moins une prise
- **Prises** : Nombre total de prises enregistrées
- **Complété** : Taux de complétion (prises réalisées / prises prévues)

**Variations de traitement :**
Types de changements détectés :
- 🆕 **Traitement ajouté** : Nouveau médicament
- ⏹️ **Traitement arrêté** : Médicament arrêté
- 💊 **Dosage modifié** : Changement du nombre de comprimés

**Indicateurs colorés :**
- 🟢 Vert : Ajout
- 🔴 Rouge : Arrêt
- 🟠 Orange : Modification

---

### 3. En-tête "Détail jour par jour"
```
┌─────────────────────────────────────────────────┐
│ Détail jour par jour                            │
└─────────────────────────────────────────────────┘
```

---

### 4. Card Jour par Jour (DayHistoryCard)

```
┌─────────────────────────────────────────────────┐
│ [lundi 5 février] / [Aujourd'hui] •     🏆 3/3  │
├─────────────────────────────────────────────────┤
│ ████████████░░░░░░░░ 75%                        │
├─────────────────────────────────────────────────┤
│ ┃ ✅ Médicament A                    ✏️  🗑️    │
│ ┃    08:30 • ½ cp • prévu 08:00                │
│ ┃    Note: Pris avec le petit-déjeuner         │
├─────────────────────────────────────────────────┤
│ ┃ ❌ Médicament B                    ✏️  🗑️    │
│ ┃    14:15 • 1 cp • prévu 14:00                │
├─────────────────────────────────────────────────┤
│ ┃ 🕐 Médicament C                    ✏️  🗑️    │
│ ┃    20:45 • 2 cp • prévu 20:00                │
└─────────────────────────────────────────────────┘
```

#### 4.1. Header du Jour
- **Date** : "lundi 5 février" ou "Aujourd'hui" (avec point violet •)
- **Badge trophée** : 🏆 si 100% de complétion
- **Compteur** : "X/Y" (prises réalisées / prises prévues)

#### 4.2. Barre de Progression
```
████████████░░░░░░░░ 75%
```
- 🟢 Vert : 100%
- 🟠 Orange : 50-99%
- 🔴 Rouge : 0-49%

#### 4.3. Liste des Prises

**Pour chaque prise :**

**Indicateur de statut (barre verticale colorée) :**
- 🟢 Vert : Pris (✅)
- 🔴 Rouge : Oublié (❌)
- 🟠 Orange : En attente (🕐)

**Ligne principale :**
```
[Statut] [Nom du médicament]          [✏️] [🗑️]
```

**Détails :**
```
[Heure] • [Nombre de comprimés] cp • prévu [Heure prévue]
```

Exemples de notation de comprimés :
- "¼ cp" = 0.25 comprimé
- "½ cp" = 0.5 comprimé
- "¾ cp" = 0.75 comprimé
- "1 cp" = 1 comprimé
- "1½ cp" = 1.5 comprimé
- "2 cp" = 2 comprimés

**Notes (si présentes) :**
```
Note: [Texte de la note personnelle]
```

**Actions :**
- ✏️ **Modifier** : Éditer la prise
- 🗑️ **Supprimer** : Supprimer la prise

---

### 5. États Spéciaux de l'Historique

#### 5.1. Chargement
```
┌─────────────────────────────────────┐
│             ⏳                       │
│  Chargement de l'historique...      │
│  Analyse de vos prises en cours     │
└─────────────────────────────────────┘
```

#### 5.2. Erreur
```
┌─────────────────────────────────────┐
│             ❌                       │
│     Erreur de chargement            │
│  [Message d'erreur détaillé]        │
│                                      │
│      [Réessayer]                    │
└─────────────────────────────────────┘
```

#### 5.3. Vide
```
┌─────────────────────────────────────┐
│             📅                       │
│       Aucun historique              │
│                                      │
│  Marquez vos prises de médicaments  │
│  pour commencer votre suivi         │
└─────────────────────────────────────┘
```

---

## 🎨 MODAL : Ajouter un médicament

**Titre du modal :**
```
┌──────────────────────────────────┐
│ Ajouter un médicament        ✕   │
└──────────────────────────────────┘
```

**Contenu :**
- Formulaire simplifié (`MedicationFormSimplified`)
- Champs : nom, dosage, fréquence, heures de prise
- Autocomplete pour le nom du médicament
- Boutons : "Annuler" | "Enregistrer"

**Message de confirmation :**
```
✅ Ajouté
[Nom du médicament] a été enregistré.
```

---

## 🎨 MODAL : Modifier la posologie

**Titre du modal :**
```
┌──────────────────────────────────┐
│ Modifier la posologie        ✕   │
└──────────────────────────────────┘
```

**Contenu :**
- Nom du médicament (lecture seule)
- Nouveau dosage
- Nouvelle unité
- Nouveau nombre de comprimés par prise
- Date d'effet
- Notes optionnelles

**Boutons :**
- "Annuler" (gris)
- "Enregistrer" (violet)

---

## 🎨 MODAL : Arrêter le traitement

**Titre du modal :**
```
┌──────────────────────────────────┐
│ ⏹️ Terminer le traitement    ✕   │
└──────────────────────────────────┘
```

**Sous-titre :**
```
Vous souhaitez arrêter le traitement "[Nom]"
```

**Sélection de date :**
```
Date de fin du traitement
┌──────────────────────────────────┐
│ 📅  5 février 2026               │
└──────────────────────────────────┘
```

**Boutons :**
- "Annuler" (gris)
- "⏹️ Terminer" (orange)

**Message de confirmation :**
```
✅ Traitement terminé
Le traitement "[Nom]" a été arrêté le [date]
```

---

## 🎨 MODAL : Modifier une prise (Historique)

**Titre du modal :**
```
┌──────────────────────────────────┐
│ Modifier la prise            ✕   │
└──────────────────────────────────┘
```

**Contenu :**
- Statut de la prise (Pris / Oublié / En retard / En avance)
- Heure de prise
- Nombre de comprimés
- Notes

**Boutons :**
- "Annuler" (gris)
- "Enregistrer" (violet)

---

## 📊 DONNÉES DYNAMIQUES AFFICHÉES

### Variables Calculées et Affichées

1. **Nombre de médicaments** : `medications.length`
2. **Prises du jour** : `todayMedications.length`
3. **Impact total** : `totalImpact` (ex: "+5.2%" ou "-3.8%")
4. **Impacts individuels** : `getMedicationImpact(medication)`
   - `impactText` : "+X.X%" ou "-X.X%"
   - `status` : "positive" | "negative" | "neutral"
   - `description` : Texte explicatif

5. **Analyses Gemini** : `getMedicationAnalysis(medicationName)`
   - `intro_explicative` : À quoi sert le médicament
   - `impact_corps` : Effets physiologiques
   - `impact_journee` : Ressenti quotidien
   - `observation` : Points de vigilance
   - `effets_horaires` : Courbes d'efficacité sur 24h
   - `label_concentration` : Label axe concentration
   - `label_efficacite` : Label axe efficacité
   - `label_effets_secondaires` : Label axe effets secondaires

6. **Phase de traitement** :
   - Jours < 7 → "Phase aiguë" : "Les premiers jours montrent souvent les effets les plus marqués"
   - Jours 7-29 → "Phase d'adaptation" : "Votre corps s'adapte progressivement au traitement"
   - Jours ≥ 30 → "Phase chronique" : "Votre corps s'est adapté au traitement, l'effet est stabilisé"

7. **Heures de prise** : `medication.intakeTimes[]` (ex: ["08:00", "14:00", "20:00"])

8. **Dosage** :
   - `medication.dosage` : Concentration (ex: "10")
   - `medication.unit` : Unité (ex: "mg")
   - `medication.pillsPerIntake` : Nombre de comprimés (peut être 0.25, 0.5, 0.75, 1, 1.5, 2, etc.)
   - Affichage : "[¼/½/¾/1/1½/2] × [dosage] [unit]"

9. **Date de début** : `formatDate(medication.takenAt)`
   - "Aujourd'hui"
   - "Hier"
   - "Il y a Xj" (moins de 7 jours)
   - "Il y a X semaines" (moins de 30 jours)
   - "Il y a X mois" (30+ jours)

10. **Durée du traitement** : `getDaysSinceStart()` → "X jours"

11. **Fréquence quotidienne** : `medication.dailyFrequency` → "Xx/jour"

12. **Type de traitement** :
    - `medication.isRecurring === true` → "🔄 Récurrent"
    - `medication.isRecurring === false` → "📅 Ponctuel"

---

## 🎯 MESSAGES ET ALERTES

### Messages d'ajout
```
✅ Ajouté
[Nom du médicament] a été enregistré.
```

### Messages d'erreur
```
❌ Erreur
Impossible d'ajouter le médicament.
```

```
❌ Erreur
Impossible de supprimer le médicament.
```

```
❌ Erreur
[Message d'erreur détaillé]
```

### Confirmations de suppression
```
Supprimer la prise
Voulez-vous vraiment supprimer cette prise de [Nom] ?

[Annuler]  [Supprimer]
```

### Confirmation de succès (suppression)
```
✅ Succès
La prise a été supprimée
```

### Message de traitement terminé
```
✅ Traitement terminé
Le traitement "[Nom]" a été arrêté le [date]
```

---

## 📈 GRAPHIQUES ET VISUALISATIONS

### 1. Barre de Progression (Phase de traitement)
```
████████░░ 80%
```
- Progression : Min(jours / 30 * 100, 100)%
- Couleur : Selon l'impact (vert/rouge/gris)

### 2. Barre de Progression (Historique - Jour)
```
████████████░░░░░░░░ 75%
```
- Progression : (prises réalisées / prises prévues) * 100
- Couleurs :
  - 🟢 Vert : 100%
  - 🟠 Orange : 50-99%
  - 🔴 Rouge : 0-49%

### 3. Courbe Horaire d'Efficacité
- Graphique linéaire sur 24h (0h → 23h)
- 3 courbes possibles :
  - **Concentration** : Niveau dans le sang
  - **Efficacité** : Effet thérapeutique
  - **Effets secondaires** : Effets indésirables
- Marqueurs de prise : 📍 aux heures de prise
- Labels personnalisés par médicament

---

## 🎨 PALETTE DE COULEURS

### Couleurs Principales
- **Violet principal** : `#5E5CE6` (Boutons, accents, badges)
- **Vert positif** : `#34C759` (Impact positif, statut pris)
- **Rouge négatif** : `#FF3B30` (Impact négatif, statut oublié)
- **Orange warning** : `#FF9500` (Modifications, ponctuel, en attente)
- **Jaune attention** : `#FFB800` (Observations, trophée, Gemini)
- **Gris neutre** : `#8E8E93` (Textes secondaires, neutre)

### Backgrounds
- **Container** : `#0A0A12` (Fond principal)
- **Cards** : `rgba(26, 26, 46, 0.6)` (Cartes)
- **Header** : `rgba(13, 13, 31, 0.95)` (Header sticky)
- **Gradients positifs** : `rgba(52, 199, 89, 0.15)` → `rgba(52, 199, 89, 0.08)`
- **Gradients négatifs** : `rgba(255, 59, 48, 0.15)` → `rgba(255, 59, 48, 0.08)`
- **Gradients violets** : `rgba(94, 92, 230, 0.15)` → `rgba(94, 92, 230, 0.05)`

### Bordures
- **Normal** : `rgba(255, 255, 255, 0.1)`
- **Active/Accent** : `rgba(94, 92, 230, 0.3)`
- **Positif** : `rgba(52, 199, 89, 0.4)`
- **Négatif** : `rgba(255, 59, 48, 0.4)`

---

## 🔄 ACTIONS UTILISATEUR DISPONIBLES

### Sur la page principale
1. **Retour** : Revenir au profil
2. **Ajouter un médicament** : Ouvrir le formulaire d'ajout
3. **Changer d'onglet** : Basculer entre "Mes Médicaments" et "Historique"
4. **Voir l'analyse complète** : Déplier les détails d'un médicament
5. **Menu actions (⋮)** :
   - Modifier la posologie
   - Arrêter le traitement
   - Supprimer le médicament

### Sur l'historique
1. **Naviguer entre les mois** : Sélectionner un mois dans la barre de navigation
2. **Pull to refresh** : Actualiser l'historique
3. **Modifier une prise** : Éditer les détails d'une prise
4. **Supprimer une prise** : Retirer une prise de l'historique
5. **Scroll** : Parcourir l'historique jour par jour

---

## 📱 ÉTATS D'INTERFACE

### États de chargement
1. **Chargement des médicaments** : Spinner + "Chargement des médicaments..."
2. **Chargement de l'analyse** : Spinner + "Analyse détaillée en cours avec Gemini..."
3. **Chargement de l'historique** : Spinner + "Chargement de l'historique..." + "Analyse de vos prises en cours"

### États vides
1. **Aucun médicament** : Icône pilule + message + bouton d'ajout
2. **Aucun historique** : Icône calendrier + message explicatif
3. **Aucune prise aujourd'hui** : Section "Aujourd'hui" masquée

### États d'erreur
1. **Erreur de chargement** : Icône X rouge + message d'erreur + bouton "Réessayer"
2. **Erreur d'ajout** : Alert "❌ Erreur" + message
3. **Erreur de suppression** : Alert "❌ Erreur" + message

### États de succès
1. **Médicament ajouté** : Alert "✅ Ajouté" + nom du médicament
2. **Prise supprimée** : Alert "✅ Succès" + confirmation
3. **Traitement arrêté** : Alert "✅ Traitement terminé" + date

---

## 🔍 LOGIQUE DE MATCHING GEMINI

Pour associer les analyses Gemini aux médicaments, un système de matching flexible est utilisé :

1. **Match exact** : Nom identique (insensible à la casse)
2. **Match partiel** : L'un contient l'autre
3. **Match sans forme pharmaceutique** : Ignore ", gélule", ", comprimé", etc.

**Exemple :**
- Médicament : "Sertraline, comprimé"
- Analyse Gemini : "Sertraline"
- ✅ Match réussi

---

## 📊 STATISTIQUES CALCULÉES

### Par médicament
- **Jours depuis le début** : `(now - takenAt) / 86400000`
- **Phase de traitement** : Selon le nombre de jours
- **Impact énergétique** : Calculé via ML/backend
- **Dosage total** : `dosage × pillsPerIntake`

### Globales
- **Impact total** : Somme des impacts individuels
- **Nombre de prises du jour** : Médicaments avec heures de prise aujourd'hui
- **Nombre total de médicaments** : Count des médicaments actifs

### Historique
- **Jours avec prises** : Nombre de jours distincts
- **Total prises** : Somme de toutes les prises
- **Taux de complétion** : (prises réalisées / prises prévues) × 100
- **Prises réalisées** : Status = "taken"
- **Prises oubliées** : Status = "skipped"
- **Prises en attente** : Status = "pending" ou autres

---

## 🎯 POINTS CLÉS DE L'EXPÉRIENCE UTILISATEUR

### Transparence et Pédagogie
- **Analyses détaillées** : Explications claires de chaque médicament
- **Graphiques visuels** : Courbes d'efficacité sur 24h
- **Indicateurs colorés** : Code couleur intuitif (vert/rouge/orange)

### Suivi Précis
- **Impact en temps réel** : Calcul dynamique selon le dosage et la durée
- **Historique complet** : Journal de toutes les prises
- **Variations de traitement** : Détection automatique des changements

### Personnalisation
- **Dosages flexibles** : Support des fractions de comprimés (¼, ½, ¾)
- **Notes personnelles** : Ajout de contexte sur chaque prise
- **Horaires multiples** : Plusieurs prises par jour

### IA Générative (Gemini)
- **Analyse globale** : Vue d'ensemble des traitements
- **Analyses individuelles** : Détails par médicament
- **Formatage riche** : Markdown avec titres, listes, emphases
- **Cache intelligent** : Évite les requêtes redondantes

---

## 🚀 TECHNOLOGIES UTILISÉES

### Composants React Native
- `ScrollView` : Défilement vertical
- `SectionList` : Liste groupée par mois (historique)
- `Modal` : Formulaires en plein écran
- `ActivityIndicator` : Spinners de chargement
- `TouchableOpacity` / `Pressable` : Boutons interactifs
- `RefreshControl` : Pull to refresh

### Librairies
- **expo-linear-gradient** : Gradients pour les cards
- **lucide-react-native** : Icônes modernes
- **@react-native-community/datetimepicker** : Sélecteur de date

### Hooks Custom
- `useMedications` : Gestion des médicaments
- `useMedicationImpacts` : Calcul des impacts énergétiques
- `useMedicationAnalysis` : Analyses Gemini individuelles
- `useMedicationComparativeAnalysis` : Analyse Gemini globale
- `useMedicationHistoryByDay` : Historique groupé par jour
- `useMarkAsTaken` : Marquer une prise
- `useStopMedication` : Arrêter un traitement
- `useUpdateMedicationDosage` : Modifier la posologie
- `useUpdateMedicationIntake` : Modifier une prise
- `useDeleteMedicationIntake` : Supprimer une prise
- `useMedicationHistorySync` : Synchroniser l'historique

---

## 📝 RÉSUMÉ DES TEXTES GÉNÉRÉS

### Textes Statiques (UI)
Tous les textes de l'interface sont listés ci-dessus dans chaque section.

### Textes Dynamiques (Générés par Gemini)
1. **Analyse globale des traitements** (TreatmentOverview)
   - Texte libre formaté en Markdown
   - Sections, listes, emphases

2. **Analyses individuelles par médicament**
   - Fonction du médicament
   - Impact sur le corps
   - Ressenti quotidien
   - Observations et précautions

3. **Descriptions d'impact énergétique**
   - Texte explicatif de l'impact calculé
   - Recommandations personnalisées

### Textes Calculés
1. **Dates relatives** : "Aujourd'hui", "Hier", "Il y a Xj/semaines/mois"
2. **Pourcentages d'impact** : "+5.2%", "-3.8%"
3. **Phases de traitement** : "Phase aiguë", "Phase d'adaptation", "Phase chronique"
4. **Descriptions de phases** : Texte adapté selon la durée
5. **Statistiques** : Nombres de jours, prises, taux de complétion

---

## 🤖 EXEMPLES RÉELS DE TEXTES GÉNÉRÉS PAR GEMINI

### 1. Analyse Globale des Traitements (TreatmentOverview)

**Contexte :** Utilisateur avec 2 médicaments actifs (Doliprane, Venlafaxine LP)

#### Exemple de Texte Généré :

```markdown
## Vue d'ensemble de votre traitement

Vous êtes actuellement sous un **traitement combiné** qui associe gestion de la douleur et régulation de l'humeur. Vous avez récemment ajouté la Venlafaxine LP (J+2), un antidépresseur qui nécessite un temps d'adaptation. Le Doliprane est utilisé de façon stable depuis 14 jours pour soulager vos douleurs.

### Comment ça agit ?

* **Doliprane** : Agit comme un "bloqueur de signaux" dans votre cerveau, empêchant la transmission de la sensation de douleur et de fièvre. Pas d'effet anti-inflammatoire, mais très efficace pour soulager.
* **Venlafaxine LP** : Fonctionne comme un "régulateur d'humeur" en augmentant progressivement vos niveaux de sérotonine et noradrénaline, deux messagers chimiques essentiels au bien-être mental.
* Ces deux médicaments n'interagissent pas négativement ensemble.

### Impact au quotidien

* **Énergie** : En début de traitement Venlafaxine (J+2), vous pouvez ressentir une légère fatigue les premiers jours. Cela s'améliore dès la semaine 2-3.
* **Sommeil** : Le Doliprane pris le soir peut aider à mieux dormir en réduisant la douleur. La Venlafaxine peut initialement perturber le sommeil, mais cela se régule rapidement.
* **Digestion** : Possibles nausées légères 1-2h après la prise de Venlafaxine pendant la phase d'adaptation (normal et temporaire).
* **Moral** : Les effets bénéfiques de la Venlafaxine sur l'humeur et l'anxiété apparaissent progressivement après 2-4 semaines. Patience !

### Conseils express

* **Hydrate-toi davantage** → Réduit les nausées liées à la Venlafaxine et aide le foie à éliminer le Doliprane
* **Prends la Venlafaxine à heure fixe** → Stabilise les niveaux dans le sang et minimise les effets secondaires
* **Évite l'alcool** → Surtout avec le Doliprane (risque hépatique) et la Venlafaxine (effet amplifié)

⚠️ En cas de symptômes inhabituels, contacte ton médecin.
```

---

### 2. Analyses Individuelles par Médicament

#### Exemple 1 : Doliprane 500mg

**Données d'entrée :**
- Nom : Doliprane
- Dosage : 500mg
- Fréquence : 2x/jour (08:00, 20:00)
- Durée : J+14

**Textes générés par Gemini :**

##### intro_explicative
```
Antalgique (contre la douleur) et antipyrétique (contre la fièvre) utilisé pour soulager les douleurs légères à modérées.
```

##### impact_corps
```
Agit sur le système nerveux central en bloquant la production de substances qui transmettent la douleur, sans effet anti-inflammatoire significatif. Le foie métabolise le paracétamol, d'où l'importance de ne pas dépasser les doses recommandées.
```

##### impact_journee
```
Effet ressenti environ 30 minutes après la prise, pic d'efficacité à 1-2h. Durée d'action : 4-6h. Peut aider à mieux dormir si pris le soir contre une douleur. Pas d'effet sur la vigilance ou la concentration.
```

##### observation
```
Après 14 jours, usage régulier sans problème. Attention à ne pas dépasser 4g/jour (8 comprimés de 500mg). Éviter l'alcool qui surcharge le foie. Si la douleur persiste au-delà de 5 jours, consulte ton médecin.
```

---

#### Exemple 2 : Venlafaxine LP 37.5mg

**Données d'entrée :**
- Nom : Venlafaxine LP (Libération Prolongée)
- Dosage : 37.5mg
- Fréquence : 1x/jour (11:00)
- Durée : J+2 (début de traitement)

**Textes générés par Gemini :**

##### intro_explicative
```
Antidépresseur et anxiolytique qui aide à réguler la sérotonine et la noradrénaline dans le cerveau pour améliorer l'humeur et réduire l'anxiété.
```

##### impact_corps
```
Augmente progressivement les niveaux de sérotonine et noradrénaline, deux neurotransmetteurs essentiels au bien-être émotionnel. La forme "LP" (libération prolongée) permet une diffusion régulière sur 24h, ce qui réduit les variations d'humeur et les effets secondaires.
```

##### impact_journee
```
En début de traitement (J+2), possibles nausées légères 1-2h après la prise, ainsi qu'une légère fatigue ou somnolence. Ces effets s'atténuent généralement après 5-7 jours. Les effets thérapeutiques pleins (amélioration de l'humeur et réduction de l'anxiété) apparaissent après 2-4 semaines de traitement continu.
```

##### observation
```
Vous êtes en tout début de traitement. Les premiers jours peuvent être inconfortables (nausées, fatigue, possibles troubles du sommeil). C'est normal et temporaire. L'effet bénéfique arrive progressivement. Ne jamais arrêter brutalement : un sevrage doit être progressif sur plusieurs semaines pour éviter un syndrome de sevrage désagréable. Patience et persévérance !
```

---

#### Exemple 3 : Sertraline 100mg

**Données d'entrée :**
- Nom : Sertraline
- Dosage : 100mg
- Fréquence : 1x/jour (23:00)
- Durée : J+570 (traitement établi depuis ~19 mois)

**Textes générés par Gemini :**

##### intro_explicative
```
Antidépresseur de la famille des ISRS (Inhibiteurs Sélectifs de la Recapture de la Sérotonine) utilisé pour traiter la dépression, l'anxiété et les troubles obsessionnels compulsifs.
```

##### impact_corps
```
Empêche la recapture de la sérotonine dans le cerveau, ce qui augmente sa disponibilité et améliore la régulation de l'humeur, de l'anxiété et du sommeil. Après 19 mois de traitement, votre organisme a trouvé un équilibre stable avec ce médicament.
```

##### impact_journee
```
Prise le soir (23h), peut favoriser un meilleur sommeil. Pas d'effet sédatif marqué dans votre cas (traitement établi). Pas d'impact sur la vigilance ou les performances au quotidien. La stabilité émotionnelle acquise vous permet de mieux gérer le stress et les émotions.
```

##### observation
```
Traitement bien établi depuis 19 mois (J+570). La dose de 100mg est une dose thérapeutique standard. Si ton humeur et ton anxiété sont bien contrôlées, c'est que le traitement est adapté. Si tu envisages un jour d'arrêter, il faudra le faire très progressivement sous supervision médicale (sevrage sur plusieurs mois). Pour l'instant, continue ce qui fonctionne !
```

---

#### Exemple 4 : Escitalopram 10mg

**Données d'entrée :**
- Nom : Escitalopram
- Dosage : 10mg
- Fréquence : 1x/jour (08:00)
- Durée : J+45

**Textes générés par Gemini :**

##### intro_explicative
```
Antidépresseur ISRS de nouvelle génération, particulièrement efficace pour l'anxiété généralisée et les troubles dépressifs avec peu d'effets secondaires.
```

##### impact_corps
```
Augmente sélectivement la sérotonine en bloquant sa recapture, ce qui régule l'humeur, réduit l'anxiété et améliore le sommeil. C'est l'ISRS le plus "propre" avec le moins d'interactions médicamenteuses.
```

##### impact_journee
```
Après 45 jours de traitement, tu es maintenant en phase d'efficacité optimale. L'anxiété de fond devrait être nettement réduite. Prise le matin, permet de profiter de l'effet énergisant léger sans perturber le sommeil nocturne. Pas d'effet sur la concentration ou la mémoire.
```

##### observation
```
Tu es en pleine phase d'adaptation chronique (J+45). Les bénéfices sont maintenant bien installés. Si tu ressens encore de l'anxiété résiduelle, parles-en à ton médecin : peut-être une augmentation de dose est-elle nécessaire. Continue à prendre à heure fixe chaque matin pour maintenir la stabilité.
```

---

### 3. Exemple d'Analyse pour un Traitement Complexe (3+ médicaments)

**Contexte :** Utilisateur avec Sertraline, Quetiapine, Lamotrigine

#### Texte d'Analyse Globale Généré :

```markdown
## Vue d'ensemble de votre traitement

Vous suivez actuellement un **traitement psychiatrique complet** associant un antidépresseur (Sertraline), un stabilisateur d'humeur (Lamotrigine) et un régulateur du sommeil (Quetiapine). Ce trio travaille en synergie pour stabiliser votre humeur, réduire l'anxiété et améliorer la qualité de votre sommeil.

### Comment ça agit ?

* **Sertraline** : Restaure l'équilibre de la sérotonine, comme si on "rechargeait" les batteries émotionnelles du cerveau
* **Lamotrigine** : Agit comme un "pare-chocs neuronal", empêchant les variations brutales d'humeur en stabilisant l'activité électrique du cerveau
* **Quetiapine** : Fonctionne comme un "interrupteur de nuit", facilitant l'endormissement et le maintien du sommeil profond grâce à son effet sédatif
* Cette combinaison est courante et bien tolérée dans les troubles bipolaires ou dépression résistante

### Impact au quotidien

* **Énergie** : La Quetiapine peut causer une somnolence matinale ("gueule de bois") les premiers jours, qui s'atténue progressivement. La Sertraline compense en apportant une énergie stable en journée.
* **Sommeil** : Nette amélioration dès J+3-5 grâce à la Quetiapine. Tu devrais dormir plus profondément et te réveiller moins la nuit.
* **Humeur** : Stabilisation progressive sur 2-3 semaines. La Lamotrigine prévient les épisodes dépressifs ou maniaques, tandis que la Sertraline améliore l'humeur de fond.
* **Poids** : La Quetiapine peut légèrement augmenter l'appétit. Surveille sans stresser, hydrate-toi bien.

### Conseils express

* **Prends la Quetiapine 1h avant le coucher** → Profite de son effet sédatif au bon moment et évite la somnolence matinale
* **Lamotrigine à heure fixe** → Maintient un niveau sanguin stable pour prévenir les variations d'humeur
* **Journaling quotidien** → Note ton humeur, ton sommeil et ton énergie pour repérer les tendances avec ton médecin

⚠️ En cas de symptômes inhabituels (éruption cutanée, fièvre, confusion), contacte immédiatement ton médecin.
```

---

### 4. Format de Sortie JSON pour Analyses Individuelles

**Structure complète retournée par le backend :**

```json
{
  "analyse_traitements": [
    {
      "nom": "Doliprane",
      "intro_explicative": "Antalgique (contre la douleur) et antipyrétique (contre la fièvre) utilisé pour soulager les douleurs légères à modérées.",
      "impact_corps": "Agit sur le système nerveux central en bloquant la production de substances qui transmettent la douleur, sans effet anti-inflammatoire significatif.",
      "impact_journee": "Effet ressenti environ 30 minutes après la prise, pic d'efficacité à 1-2h. Durée d'action : 4-6h. Peut aider à mieux dormir si pris le soir contre une douleur.",
      "observation": "Après 14 jours, usage régulier sans problème. Attention à ne pas dépasser 4g/jour (8 comprimés de 500mg). Éviter l'alcool.",
      "effets_horaires": [
        { "heure": 0, "concentration": 0, "efficacite": 0, "effets_secondaires": 0 },
        { "heure": 1, "concentration": 60, "efficacite": 70, "effets_secondaires": 5 },
        { "heure": 2, "concentration": 90, "efficacite": 100, "effets_secondaires": 5 },
        { "heure": 3, "concentration": 80, "efficacite": 90, "effets_secondaires": 3 },
        { "heure": 4, "concentration": 60, "efficacite": 70, "effets_secondaires": 2 },
        { "heure": 5, "concentration": 40, "efficacite": 50, "effets_secondaires": 1 },
        { "heure": 6, "concentration": 20, "efficacite": 30, "effets_secondaires": 0 },
        { "heure": 7, "concentration": 10, "efficacite": 15, "effets_secondaires": 0 },
        { "heure": 8, "concentration": 5, "efficacite": 10, "effets_secondaires": 0 }
      ],
      "label_concentration": "Niveau dans le sang",
      "label_efficacite": "Efficacité antalgique",
      "label_effets_secondaires": "Risque d'effets secondaires"
    },
    {
      "nom": "Venlafaxine LP",
      "intro_explicative": "Antidépresseur et anxiolytique qui aide à réguler la sérotonine et la noradrénaline dans le cerveau.",
      "impact_corps": "Augmente progressivement les niveaux de sérotonine et noradrénaline, ce qui améliore l'humeur et réduit l'anxiété sur le long terme.",
      "impact_journee": "En début de traitement (J+2), possibles nausées légères 1-2h après la prise. Effets thérapeutiques pleins après 2-4 semaines.",
      "observation": "Vous êtes en tout début de traitement. Les premiers jours peuvent être inconfortables (nausées, fatigue). L'effet bénéfique arrive progressivement. Ne jamais arrêter brutalement.",
      "effets_horaires": [
        { "heure": 0, "concentration": 0, "efficacite": 0, "effets_secondaires": 0 },
        { "heure": 2, "concentration": 30, "efficacite": 20, "effets_secondaires": 25 },
        { "heure": 4, "concentration": 60, "efficacite": 50, "effets_secondaires": 30 },
        { "heure": 6, "concentration": 80, "efficacite": 70, "effets_secondaires": 20 },
        { "heure": 8, "concentration": 85, "efficacite": 85, "effets_secondaires": 10 },
        { "heure": 12, "concentration": 90, "efficacite": 90, "effets_secondaires": 5 },
        { "heure": 16, "concentration": 85, "efficacite": 85, "effets_secondaires": 3 },
        { "heure": 20, "concentration": 70, "efficacite": 75, "effets_secondaires": 2 },
        { "heure": 24, "concentration": 50, "efficacite": 60, "effets_secondaires": 1 }
      ],
      "label_concentration": "Niveau sanguin",
      "label_efficacite": "Effet antidépresseur",
      "label_effets_secondaires": "Nausées / Fatigue"
    }
  ],
  "_generated_at": "2026-02-08T15:30:00Z",
  "_medications_count": 2,
  "_cost": 0.0089
}
```

---

### 5. Variations de Textes selon la Durée du Traitement

#### Phase Aiguë (J+0 à J+7)

**Exemple pour Venlafaxine LP J+2 :**
```
Vous êtes en tout début de traitement. Les premiers jours peuvent être inconfortables (nausées, fatigue, possibles troubles du sommeil). C'est normal et temporaire. L'effet bénéfique arrive progressivement. Accroche-toi, ça va s'améliorer dès la 2ème semaine !
```

#### Phase d'Adaptation (J+8 à J+29)

**Exemple pour Sertraline J+18 :**
```
Tu es en pleine phase d'adaptation. Les effets secondaires initiaux devraient avoir disparu. Les bénéfices thérapeutiques commencent à se faire sentir. Continue à prendre à heure fixe et note tes progrès pour en discuter avec ton médecin au prochain rendez-vous.
```

#### Phase Chronique (J+30+)

**Exemple pour Escitalopram J+570 :**
```
Traitement bien établi depuis 19 mois. La dose de 10mg est une dose thérapeutique standard. Si ton humeur et ton anxiété sont bien contrôlées, c'est que le traitement est adapté. Continue ce qui fonctionne ! Si tu envisages un jour d'arrêter, il faudra le faire très progressivement sous supervision médicale.
```

---

### 6. Adaptations selon le Contexte

#### Nouveau Médicament Ajouté

**Badge affiché :**
```
⚠️ 1 nouveau
```

**Ton de l'analyse :**
```
Tu as récemment ajouté [Médicament] à ton traitement. Voici ce à quoi tu peux t'attendre pendant les premières semaines...
```

#### Médicament Arrêté

**Mention dans l'analyse globale :**
```
Tu as récemment arrêté [Médicament]. Surveille l'évolution de [symptômes] et n'hésite pas à en parler à ton médecin si tu remarques des changements.
```

#### Dosage Modifié

**Ton de l'analyse :**
```
Ton dosage de [Médicament] a été ajusté. Cette modification vise à [objectif]. Observe comment tu te sens pendant les prochains jours...
```

---

### 7. Caractéristiques des Textes Gemini

#### Style et Ton
- **Accessible** : Niveau lycéen, pas de jargon médical complexe
- **Empathique** : Ton rassurant et bienveillant
- **Concret** : Métaphores simples ("bloqueur de signaux", "recharger les batteries")
- **Actionnable** : Conseils pratiques avec bénéfices immédiats

#### Longueur
- **Intro explicative** : 1 phrase (~15-25 mots)
- **Impact corps** : 1-2 phrases (~40-60 mots)
- **Impact journée** : 2-3 phrases (~50-80 mots)
- **Observation** : 2-3 phrases (~60-100 mots)
- **Analyse globale** : 300-400 mots total

#### Markdown
- Titres : `##` (H2) et `###` (H3)
- Listes : `*` pour les bullets
- Emphases : `**gras**` pour mots-clés importants
- Toujours finir par : `⚠️ En cas de symptômes inhabituels, contacte ton médecin.`

#### Temporalité
- **Début** : "premières heures", "premiers jours", "J+2-5"
- **Adaptation** : "semaine 2-3", "après 2-4 semaines"
- **Établi** : "après X mois", "traitement stabilisé"

---

### 8. Gestion des Cas Particuliers

#### Médicament Inconnu de Gemini

**Fallback généré :**
```json
{
  "nom": "[Médicament]",
  "intro_explicative": "Médicament prescrit par votre médecin pour traiter votre condition.",
  "impact_corps": "Information non disponible. Consultez la notice fournie par votre pharmacien.",
  "impact_journee": "Prenez ce médicament selon les recommandations de votre médecin.",
  "observation": "Pour toute question, contactez votre médecin ou pharmacien."
}
```

#### Traitement Vide

**Message affiché :**
```
Aucun médicament actif à analyser.
```

#### Erreur Gemini

**Fallback gracieux :**
```
L'analyse détaillée n'est temporairement pas disponible. Vos médicaments sont bien enregistrés et les calculs d'impact énergétique fonctionnent normalement.
```

---

---

## 💡 EXEMPLES DE CONSEILS PERSONNALISÉS GEMINI

### Conseils par Catégorie de Médicament

#### Antidépresseurs (ISRS/IRSNA)
```
• Prends à heure fixe → Stabilise les niveaux sanguins et réduit les effets secondaires
• Hydrate-toi bien → Compense la sécheresse buccale fréquente
• Patience pendant 2-4 semaines → L'effet thérapeutique est progressif
• Jamais d'arrêt brutal → Sevrage doit être supervisé médicalement
```

#### Anxiolytiques (Benzodiazépines)
```
• Usage ponctuel privilégié → Risque de dépendance si usage quotidien prolongé
• Évite la conduite 2-3h après prise → Effet sédatif marqué
• Pas d'alcool → Potentialisation dangereuse des effets
• Alerte médecin si besoin quotidien → Peut nécessiter ajustement du traitement de fond
```

#### Antalgiques (Paracétamol)
```
• Respect des 4-6h entre prises → Évite surdosage hépatique
• Maximum 4g/jour → Au-delà = danger pour le foie
• Évite l'alcool → Surcharge hépatique
• Si douleur > 5 jours → Consulte pour investigation
```

#### Régulateurs du Sommeil
```
• Prends 1h avant coucher → Profite du pic d'efficacité au bon moment
• Routine sommeil stable → Renforce l'effet thérapeutique
• Évite écrans 30min après prise → Favorise l'endormissement
• Si somnolence matinale → Prends plus tôt ou discute dosage avec médecin
```

---

## 🎯 EXEMPLES D'ANALYSES CONTEXTUELLES

### Analyse pour Traitement Récent (J+5)

**Contexte :** Fluoxétine 20mg, début il y a 5 jours

**Analyse Globale Générée :**

```markdown
## Début de traitement : Sois patient !

Tu viens de commencer la **Fluoxétine** (J+5), un antidépresseur ISRS. C'est tout à fait normal que tu ne ressentes pas encore les bénéfices pleins - ils arrivent entre la 2ème et la 4ème semaine. Pour l'instant, ton corps s'adapte.

### Ce qui se passe actuellement

* **Ton cerveau recâble ses circuits** : La sérotonine commence à s'accumuler, mais les récepteurs mettent du temps à s'ajuster
* **Phase d'adaptation** : Possibles nausées légères, léger mal de tête, ou fatigue passagère
* **C'est temporaire** : Ces effets s'estompent généralement dès J+7-10

### À quoi t'attendre cette semaine

* **Jours 5-7** : Pic potentiel des effets secondaires mineurs (tiens bon !)
* **Jours 7-14** : Nette amélioration du confort, effets secondaires qui s'estompent
* **Semaine 3-4** : Début des effets thérapeutiques sur l'humeur et l'anxiété

### Conseils pour cette phase

* **Tiens un journal** → Note ton humeur, ton sommeil, tes effets secondaires chaque jour
* **Prends le matin** → Évite les troubles du sommeil si pris le soir
* **Mange léger 1h après** → Réduit les nausées si présentes

⚠️ Si les effets secondaires sont insupportables, contacte ton médecin sans attendre.
```

---

### Analyse pour Traitement Établi avec Ajustement (J+120)

**Contexte :** Sertraline passée de 50mg à 100mg il y a 3 jours

**Analyse Globale Générée :**

```markdown
## Ajustement de dosage en cours

Ton médecin a récemment **doublé ta dose de Sertraline** (50mg → 100mg). Après 120 jours de traitement, cet ajustement vise à améliorer l'efficacité thérapeutique.

### Pourquoi cet ajustement ?

* **Réponse partielle à 50mg** : Tu as probablement ressenti une amélioration, mais insuffisante
* **100mg = dose thérapeutique standard** : C'est la dose cible pour la plupart des patients
* **Pas de "retour à zéro"** : Tu ne recommences pas le traitement, tu l'optimises

### Ce qui change concrètement

* **Efficacité accrue** : Meilleure régulation de l'humeur et réduction plus marquée de l'anxiété dès 7-10 jours
* **Possibles ajustements temporaires** : Légers troubles digestifs ou fatigue pendant 3-5 jours (le temps que ton corps s'adapte)
* **Stabilisation rapide** : Contrairement au début, l'adaptation est plus rapide (déjà habitué à la molécule)

### Conseils pour cette transition

* **Continue à heure fixe** → Maintient la stabilité sanguine
* **Note les changements** → Amélioration de l'humeur, de l'anxiété, du sommeil
* **Donne-lui 2 semaines** → C'est le délai pour évaluer la nouvelle dose

⚠️ Si aggravation des symptômes ou effets secondaires persistants, contacte ton médecin.
```

---

### Analyse pour Traitement Long Terme (J+800+)

**Contexte :** Escitalopram 10mg depuis plus de 2 ans

**Analyse Globale Générée :**

```markdown
## Traitement stable et efficace

Tu prends **Escitalopram 10mg** depuis plus de 2 ans. C'est un traitement bien établi qui t'apporte une stabilité émotionnelle durable.

### État des lieux

* **Efficacité maintenue** : L'effet thérapeutique ne diminue pas avec le temps (pas de tolérance)
* **Bien-être émotionnel** : Tu as retrouvé un équilibre qui te permet de vivre normalement
* **Traitement de maintenance** : Il te protège des rechutes dépressives ou anxieuses

### Questions fréquentes à ce stade

**"Dois-je continuer indéfiniment ?"**
→ Pas forcément. Après 2 ans de stabilité, certains patients peuvent envisager un sevrage progressif. Mais c'est une décision médicale basée sur ton historique et tes facteurs de risque.

**"Est-ce dangereux à long terme ?"**
→ Non. Les ISRS sont parmi les médicaments les plus sûrs à long terme. Suivi annuel suffisant.

**"Puis-je arrêter d'un coup ?"**
→ Jamais ! Un sevrage doit être très progressif (plusieurs mois) pour éviter un syndrome de sevrage désagréable.

### Conseils pour la suite

* **Maintiens la régularité** → Continue à prendre chaque matin à heure fixe
* **Bilan annuel avec ton médecin** → Évaluer la pertinence de continuer ou d'envisager une réduction progressive
* **Reconnais tes signaux d'alerte** → Si rechute de symptômes, consulte rapidement

⚠️ Ce traitement te convient. Ne change rien sans avis médical.
```

---

## 📊 STATISTIQUES ET MÉTRIQUES AFFICHÉES

### Calculs d'Impact Énergétique

**Exemple de calcul pour Venlafaxine LP 37.5mg :**

```javascript
// Données d'entrée
const medication = {
  name: "Venlafaxine LP",
  dosage: 37.5,
  unit: "mg",
  pillsPerIntake: 1,
  intakeTimes: ["11:00"],
  daysSinceStart: 2
};

// Calcul simplifié de l'impact
const baseDosage = 37.5;
const effectiveDosage = baseDosage * 1; // pillsPerIntake
const daysFactor = Math.min(2 / 30, 1); // Adaptation progressive

// Impact énergétique (négatif en début de traitement)
const energyImpact = -8.5 * daysFactor; // = -0.57%

// Affi affichage
impactText: "-0.6%"
status: "negative"
description: "En début de traitement, la Venlafaxine peut causer une légère fatigue. Cet effet s'atténue progressivement."
```

---

### Labels des Graphiques Horaires

**Exemples de labels personnalisés par type de médicament :**

#### Antidépresseur (Sertraline)
```json
{
  "label_concentration": "Niveau sanguin",
  "label_efficacite": "Effet antidépresseur",
  "label_effets_secondaires": "Nausées / Fatigue"
}
```

#### Antalgique (Doliprane)
```json
{
  "label_concentration": "Niveau dans le sang",
  "label_efficacite": "Efficacité antalgique",
  "label_effets_secondaires": "Risque d'effets secondaires"
}
```

#### Anxiolytique (Alprazolam)
```json
{
  "label_concentration": "Concentration plasmatique",
  "label_efficacite": "Effet anxiolytique",
  "label_effets_secondaires": "Sédation / Somnolence"
}
```

#### Régulateur du Sommeil (Quetiapine)
```json
{
  "label_concentration": "Niveau sanguin",
  "label_efficacite": "Effet sédatif",
  "label_effets_secondaires": "Somnolence résiduelle"
}
```

---

## 🔐 DISCLAIMERS ET AVERTISSEMENTS

### Disclaimer Systématique

**Affiché en fin de chaque analyse Gemini :**
```
⚠️ En cas de symptômes inhabituels, contacte ton médecin.
```

### Messages d'Avertissement Contextuels

#### Nouveau Médicament
```
⚠️ Tu es en début de traitement. Les premiers jours peuvent être inconfortables. C'est normal et temporaire.
```

#### Dosage Élevé
```
⚠️ Tu prends une dose élevée. Surveille attentivement les effets et signale tout symptôme inhabituel à ton médecin.
```

#### Traitement Long Terme
```
ℹ️ Traitement établi depuis longtemps. Un bilan régulier avec ton médecin est recommandé.
```

#### Interactions Potentielles
```
⚠️ Attention : Ces médicaments peuvent interagir. Évite l'alcool et signale tout nouveau médicament à ton médecin.
```

---

## ✅ CONCLUSION

Cette extraction complète documente **l'intégralité des textes et de la structure** de la page "Mes Médicaments" avec :

### Contenu Exhaustif
- **2 onglets** : Médicaments actuels + Historique complet
- **Analyses IA** : Gemini 3 Pro pour des insights personnalisés et vulgarisés
- **Impact énergétique** : Calculs en temps réel avec Machine Learning
- **Historique détaillé** : Journal complet jour par jour avec variations de traitement
- **Interface riche** : Cards, gradients, graphiques, modals

### Textes Générés par IA
- **8+ exemples réels** de textes générés par Gemini
- **Analyses individuelles** pour 4 médicaments différents (Doliprane, Venlafaxine, Sertraline, Escitalopram)
- **Analyses globales** pour différents contextes (début, ajustement, long terme)
- **Conseils personnalisés** adaptés au type de médicament et à la durée du traitement
- **Format JSON complet** avec structure des réponses

### Données Dynamiques
- **Variables calculées** : Phases de traitement, impacts, statistiques
- **Textes adaptés** : Selon durée, contexte, changements
- **Graphiques horaires** : Courbes d'efficacité sur 24h avec labels personnalisés
- **Métriques détaillées** : Calculs d'impact énergétique, taux de complétion

### Actions Utilisateur
- **Ajout, modification, suppression, arrêt** de médicaments
- **Consultation détaillée** avec sections expandables
- **Suivi historique** avec modifications de dosage détectées
- **Navigation intuitive** entre les mois d'historique

La page offre une expérience utilisateur **premium, pédagogique et personnalisée** pour le suivi des traitements médicamenteux, avec une transparence totale sur les données affichées et leur provenance (IA, calculs, saisie utilisateur).
