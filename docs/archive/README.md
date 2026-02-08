# Archive de Documentation

Ce dossier contient la documentation historique et les notes d'implémentation complétées.

## 📂 Organisation

Les fichiers ici sont organisés par catégorie :

### Implémentations Complétées
- Fichiers `*_IMPLEMENTATION.md` : Notes détaillées d'implémentation de features
- Fichiers `*_COMPLETE*.md` / `*_DONE.md` : Résumés de features terminées
- Fichiers `*_SUMMARY.md` : Synthèses de projets achevés

### Tests et Validation
- Fichiers `*_TESTING.md` / `*_TESTS*.md` : Guides de tests spécifiques
- Fichiers `TEST_*.md` : Procédures de validation
- `*_CHECKLIST.md` : Checklists de validation

### Features Spécifiques
- `FATSECRET_*.md` : Intégration FatSecret API
- `ICD11_*.md` : Système de conditions de santé ICD-11
- `OURA_*.md` : Intégration Oura Ring
- `FOOD_DIARY_*.md` : Journal alimentaire
- `RISK_WINDOWS_*.md` : Fenêtres de risque santé
- `ENERGY_*.md` : Systèmes de score d'énergie
- `PULSE_ENERGY_DECAY_*.md` : Modèle de décroissance énergétique

### Architecture et Corrections
- `*_ARCHITECTURE.md` : Anciennes versions d'architecture
- `*_GUIDE*.md` : Guides spécifiques
- `*_FIX*.md` : Corrections et patches

### Références Rapides
- `*_QUICKSTART.md` / `*_QUICK_REF.md` : Guides de démarrage rapide
- `*_AGENDA*.md` : Plans d'action spécifiques

## 🔍 Recherche

Pour retrouver une information archivée :

```bash
# Rechercher un terme
grep -r "terme" docs/archive/

# Lister par date de modification
ls -lt docs/archive/*.md | head -20
```

## 📋 Notes

- Ces fichiers sont conservés pour référence historique
- La documentation active se trouve dans `/docs/` (racine)
- Pour toute nouvelle documentation, créer dans `/docs/` ou `/mobile/docs/`
- Ne pas éditer les fichiers archivés (sauf pour corrections critiques)

---

**Date d'archivage** : 2026-01-31  
**Raison** : Nettoyage et centralisation du workspace Pulse
