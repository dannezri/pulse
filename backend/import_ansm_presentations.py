#!/usr/bin/env python3
"""
Script d'import des présentations ANSM (CIS_CIP_bdpm.txt) vers Supabase
Permet la recherche de médicaments par code-barres (CIP13)
"""

import sys
import os
from datetime import datetime
from supabase_client import SupabaseClient
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_ansm_presentations(file_path: str):
    """Parse le fichier CIS_CIP_bdpm.txt"""
    presentations = []
    errors = 0
    
    logger.info(f"📖 Lecture du fichier: {file_path}")
    
    with open(file_path, 'r', encoding='latin-1') as f:
        for line_num, line in enumerate(f, 1):
            try:
                # Format TSV (Tab Separated Values)
                parts = line.strip().split('\t')
                
                # Vérifier qu'on a au minimum les colonnes essentielles (CIS, CIP7, CIP13)
                if len(parts) < 7:
                    logger.warning(f"Ligne {line_num}: format invalide (colonnes insuffisantes: {len(parts)})")
                    errors += 1
                    continue
                
                cis = parts[0].strip() if len(parts) > 0 else ""
                cip7 = parts[1].strip() if len(parts) > 1 else ""
                libelle = parts[2].strip() if len(parts) > 2 else ""
                statut = parts[3].strip() if len(parts) > 3 else ""
                type_commercialisation = parts[4].strip() if len(parts) > 4 else ""
                date_commercialisation = parts[5].strip() if len(parts) > 5 else ""
                cip13 = parts[6].strip() if len(parts) > 6 else ""
                remboursable = parts[7].strip().lower() == 'oui' if len(parts) > 7 else False
                taux_remboursement = parts[8].strip() if len(parts) > 8 else ""
                prix_str = parts[9].strip() if len(parts) > 9 else ""
                
                # Valider le CIP13
                if not cip13 or len(cip13) != 13 or not cip13.isdigit():
                    logger.warning(f"Ligne {line_num}: CIP13 invalide: {cip13}")
                    errors += 1
                    continue
                
                # Parser le prix
                prix = None
                try:
                    if prix_str:
                        prix = float(prix_str.replace(',', '.'))
                except:
                    pass
                
                # Extraire le taux de remboursement numérique
                taux = None
                if taux_remboursement and '%' in taux_remboursement:
                    try:
                        taux = int(taux_remboursement.replace('%', '').strip())
                    except:
                        pass
                
                presentation = {
                    'cis': cis,
                    'cip7': cip7,
                    'cip13': cip13,
                    'libelle': libelle,
                    'statut': statut,
                    'type_commercialisation': type_commercialisation,
                    'date_commercialisation': date_commercialisation,
                    'remboursable': remboursable,
                    'taux_remboursement': taux,
                    'prix': prix,
                }
                
                presentations.append(presentation)
                
            except Exception as e:
                logger.error(f"Erreur ligne {line_num}: {e}")
                errors += 1
                continue
    
    logger.info(f"✅ {len(presentations)} présentations parsées")
    logger.info(f"⚠️  {errors} erreurs")
    
    return presentations


def import_to_supabase(presentations: list):
    """Importe les présentations dans Supabase par lots"""
    supabase = SupabaseClient(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    # Taille des lots
    BATCH_SIZE = 500
    total = len(presentations)
    success_count = 0
    error_count = 0
    
    logger.info(f"📤 Import de {total} présentations dans Supabase...")
    logger.info(f"📦 Taille des lots: {BATCH_SIZE}")
    
    for i in range(0, total, BATCH_SIZE):
        batch = presentations[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        
        try:
            # Upsert (insert ou update si existe déjà)
            result = supabase.client.table("ansm_presentations") \
                .upsert(batch, on_conflict='cip13') \
                .execute()
            
            success_count += len(batch)
            logger.info(f"✅ Lot {batch_num}/{total_batches}: {len(batch)} présentations importées ({success_count}/{total})")
            
        except Exception as e:
            error_count += len(batch)
            logger.error(f"❌ Erreur lot {batch_num}/{total_batches}: {e}")
            
            # En cas d'erreur, essayer une par une
            for pres in batch:
                try:
                    supabase.client.table("ansm_presentations") \
                        .upsert([pres], on_conflict='cip13') \
                        .execute()
                    success_count += 1
                except Exception as e2:
                    error_count += 1
                    logger.error(f"❌ CIP13 {pres.get('cip13')}: {e2}")
    
    logger.info(f"\n📊 Résumé de l'import:")
    logger.info(f"  ✅ Succès: {success_count}/{total}")
    logger.info(f"  ❌ Erreurs: {error_count}/{total}")
    
    return success_count, error_count


def main():
    """Point d'entrée principal"""
    file_path = "/Users/dannezri/Downloads/CIS_CIP_bdpm.txt"
    
    if not os.path.exists(file_path):
        logger.error(f"❌ Fichier introuvable: {file_path}")
        sys.exit(1)
    
    logger.info("🚀 Démarrage de l'import ANSM")
    logger.info(f"📁 Fichier: {file_path}")
    
    # Parser le fichier
    presentations = parse_ansm_presentations(file_path)
    
    if not presentations:
        logger.error("❌ Aucune présentation parsée")
        sys.exit(1)
    
    # Importer dans Supabase
    success, errors = import_to_supabase(presentations)
    
    if errors == 0:
        logger.info("\n🎉 Import terminé avec succès !")
    else:
        logger.warning(f"\n⚠️  Import terminé avec {errors} erreurs")
    
    logger.info(f"\n💡 Pour tester le scanner, rescannez un code-barres !")


if __name__ == "__main__":
    main()
