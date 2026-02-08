"""
Script de migration BDPM → Giygas (optionnel)

Ce script migre les données existantes de l'ancienne source BDPM
vers la nouvelle API Giygas, en enrichissant les données.

Usage:
    python migrate_bdpm_to_giygas.py [--dry-run] [--limit N]

Options:
    --dry-run    : Affiche les changements sans les appliquer
    --limit N    : Limite à N médicaments (pour test)
"""

import os
import sys
import logging
import argparse
from typing import List, Dict
from datetime import datetime

# Import des services
from supabase_client import SupabaseClient
from giygas_medication_service import GiygasMedicationService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BDPMToGiygasMigrator:
    """Migrateur BDPM → Giygas"""
    
    def __init__(self, supabase_client: SupabaseClient, dry_run: bool = False):
        self.supabase = supabase_client
        self.giygas_service = GiygasMedicationService(supabase_client=supabase_client)
        self.dry_run = dry_run
        
        self.stats = {
            "total": 0,
            "migrated": 0,
            "enriched": 0,
            "failed": 0,
            "skipped": 0
        }
    
    def get_bdpm_medications(self, limit: int = None) -> List[Dict]:
        """
        Récupère les médicaments avec source='bdpm'
        
        Args:
            limit: Nombre max de médicaments (None = tous)
        
        Returns:
            Liste de médicaments BDPM
        """
        logger.info("Récupération des médicaments BDPM...")
        
        query = self.supabase.client.table("medications_catalog")\
            .select("*")\
            .eq("source", "bdpm")
        
        if limit:
            query = query.limit(limit)
        
        result = query.execute()
        
        medications = result.data or []
        logger.info(f"Trouvé {len(medications)} médicaments BDPM")
        
        return medications
    
    def migrate_medication(self, med: Dict) -> bool:
        """
        Migre un médicament BDPM → Giygas
        
        Args:
            med: Médicament depuis medications_catalog
        
        Returns:
            True si migration réussie, False sinon
        """
        cis = med.get("external_id")
        name = med.get("name")
        
        logger.info(f"Migration: {name} (CIS: {cis})")
        
        if not cis:
            logger.warning(f"  ⚠️ Pas de CIS pour {name}, skip")
            self.stats["skipped"] += 1
            return False
        
        # Récupérer données complètes depuis Giygas
        try:
            giygas_data = self.giygas_service.get_by_cis(cis)
            
            if not giygas_data:
                logger.warning(f"  ⚠️ CIS {cis} non trouvé dans Giygas")
                self.stats["failed"] += 1
                return False
            
            # Comparer les données
            has_changes = False
            
            # Vérifier si enrichissement nécessaire
            if giygas_data.get("composition") or giygas_data.get("presentations"):
                has_changes = True
                logger.info(f"  ✅ Données enrichies disponibles (composition, présentations)")
            
            if self.dry_run:
                logger.info(f"  [DRY-RUN] Mise à jour source → giygas")
                if has_changes:
                    self.stats["enriched"] += 1
                self.stats["migrated"] += 1
                return True
            
            # Mettre à jour la source
            self.supabase.client.table("medications_catalog")\
                .update({
                    "source": "giygas",
                    "updated_at": datetime.now().isoformat()
                })\
                .eq("id", med["id"])\
                .execute()
            
            logger.info(f"  ✅ Migré vers Giygas")
            
            if has_changes:
                self.stats["enriched"] += 1
            
            self.stats["migrated"] += 1
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Erreur migration {cis}: {e}")
            self.stats["failed"] += 1
            return False
    
    def run(self, limit: int = None):
        """
        Exécute la migration complète
        
        Args:
            limit: Nombre max de médicaments à migrer
        """
        logger.info("=" * 60)
        logger.info("🔄 Début migration BDPM → Giygas")
        logger.info("=" * 60)
        
        if self.dry_run:
            logger.info("⚠️ MODE DRY-RUN : Aucune modification ne sera appliquée")
        
        # Récupérer médicaments BDPM
        medications = self.get_bdpm_medications(limit=limit)
        self.stats["total"] = len(medications)
        
        if not medications:
            logger.info("Aucun médicament BDPM à migrer")
            return
        
        # Migrer chaque médicament
        for i, med in enumerate(medications, 1):
            logger.info(f"\n[{i}/{len(medications)}] ----------------------------------------")
            self.migrate_medication(med)
        
        # Afficher statistiques
        logger.info("\n" + "=" * 60)
        logger.info("📊 Statistiques de migration")
        logger.info("=" * 60)
        logger.info(f"Total médicaments       : {self.stats['total']}")
        logger.info(f"Migrés avec succès      : {self.stats['migrated']}")
        logger.info(f"Enrichis (composition)  : {self.stats['enriched']}")
        logger.info(f"Échecs                  : {self.stats['failed']}")
        logger.info(f"Ignorés (pas de CIS)    : {self.stats['skipped']}")
        logger.info("=" * 60)
        
        if self.dry_run:
            logger.info("\n⚠️ MODE DRY-RUN : Aucune modification appliquée")
            logger.info("Relancez sans --dry-run pour appliquer les changements")


def main():
    """Point d'entrée du script"""
    parser = argparse.ArgumentParser(
        description="Migration BDPM → Giygas"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche les changements sans les appliquer"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limite à N médicaments (pour test)"
    )
    
    args = parser.parse_args()
    
    # Vérifier variables d'environnement
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_KEY"):
        logger.error("❌ Variables d'environnement manquantes:")
        logger.error("   SUPABASE_URL et SUPABASE_SERVICE_KEY requis")
        sys.exit(1)
    
    # Créer client Supabase
    supabase_client = SupabaseClient()
    
    # Créer migrateur
    migrator = BDPMToGiygasMigrator(
        supabase_client=supabase_client,
        dry_run=args.dry_run
    )
    
    # Exécuter migration
    try:
        migrator.run(limit=args.limit)
        logger.info("\n✅ Migration terminée avec succès")
    except KeyboardInterrupt:
        logger.info("\n⚠️ Migration interrompue par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Erreur fatale: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
