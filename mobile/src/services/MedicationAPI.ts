/**
 * Service d'API pour la recherche de médicaments
 * Base de données locale complète des médicaments français les plus courants
 */

export interface MedicationSuggestion {
  id: string;
  name: string;
  dosage?: string;
  form?: string;
  laboratory?: string;
}

/**
 * Base de données complète des médicaments français les plus prescrits
 * Source: Top 100 des médicaments les plus vendus en France (2024)
 */
export const MEDICATIONS_DATABASE = [
  // Antalgiques / Anti-inflammatoires
  { name: 'Doliprane', dosage: '500mg', form: 'Comprimé', laboratory: 'Sanofi' },
  { name: 'Doliprane', dosage: '1000mg', form: 'Comprimé', laboratory: 'Sanofi' },
  { name: 'Dafalgan', dosage: '500mg', form: 'Comprimé', laboratory: 'Bristol-Myers Squibb' },
  { name: 'Dafalgan', dosage: '1000mg', form: 'Comprimé', laboratory: 'Bristol-Myers Squibb' },
  { name: 'Efferalgan', dosage: '500mg', form: 'Comprimé', laboratory: 'Bristol-Myers Squibb' },
  { name: 'Efferalgan', dosage: '1000mg', form: 'Comprimé', laboratory: 'Bristol-Myers Squibb' },
  { name: 'Paracétamol', dosage: '500mg', form: 'Comprimé', laboratory: 'Générique' },
  { name: 'Paracétamol', dosage: '1000mg', form: 'Comprimé', laboratory: 'Générique' },
  { name: 'Ibuprofène', dosage: '200mg', form: 'Comprimé', laboratory: 'Générique' },
  { name: 'Ibuprofène', dosage: '400mg', form: 'Comprimé', laboratory: 'Générique' },
  { name: 'Advil', dosage: '200mg', form: 'Comprimé', laboratory: 'Pfizer' },
  { name: 'Advil', dosage: '400mg', form: 'Comprimé', laboratory: 'Pfizer' },
  { name: 'Nurofen', dosage: '200mg', form: 'Comprimé', laboratory: 'Reckitt Benckiser' },
  { name: 'Nurofen', dosage: '400mg', form: 'Comprimé', laboratory: 'Reckitt Benckiser' },
  { name: 'Aspirine', dosage: '500mg', form: 'Comprimé', laboratory: 'Bayer' },
  { name: 'Aspirine', dosage: '1000mg', form: 'Comprimé', laboratory: 'Bayer' },
  { name: 'Kardegic', dosage: '75mg', form: 'Poudre', laboratory: 'Sanofi' },
  { name: 'Kardegic', dosage: '160mg', form: 'Poudre', laboratory: 'Sanofi' },
  { name: 'Tramadol', dosage: '50mg', form: 'Gélule', laboratory: 'Générique' },
  { name: 'Tramadol', dosage: '100mg', form: 'Gélule', laboratory: 'Générique' },
  { name: 'Codoliprane', dosage: '500mg', form: 'Comprimé', laboratory: 'Sanofi' },
  
  // Antispasmodiques
  { name: 'Spasfon', dosage: '80mg', form: 'Comprimé', laboratory: 'Teva' },
  { name: 'Spasfon', dosage: '160mg', form: 'Comprimé', laboratory: 'Teva' },
  { name: 'Débridat', dosage: '100mg', form: 'Comprimé', laboratory: 'Mylan' },
  
  // Troubles digestifs
  { name: 'Omeprazole', dosage: '10mg', form: 'Gélule', laboratory: 'Générique' },
  { name: 'Omeprazole', dosage: '20mg', form: 'Gélule', laboratory: 'Générique' },
  { name: 'Inexium', dosage: '20mg', form: 'Comprimé', laboratory: 'AstraZeneca' },
  { name: 'Inexium', dosage: '40mg', form: 'Comprimé', laboratory: 'AstraZeneca' },
  { name: 'Gaviscon', dosage: '', form: 'Suspension buvable', laboratory: 'Reckitt Benckiser' },
  { name: 'Maalox', dosage: '', form: 'Suspension buvable', laboratory: 'Sanofi' },
  { name: 'Smecta', dosage: '3g', form: 'Poudre', laboratory: 'Ipsen' },
  { name: 'Motilium', dosage: '10mg', form: 'Comprimé', laboratory: 'Janssen' },
  { name: 'Imodium', dosage: '2mg', form: 'Gélule', laboratory: 'Johnson & Johnson' },
  
  // Thyroïde
  { name: 'Levothyrox', dosage: '25µg', form: 'Comprimé', laboratory: 'Merck' },
  { name: 'Levothyrox', dosage: '50µg', form: 'Comprimé', laboratory: 'Merck' },
  { name: 'Levothyrox', dosage: '75µg', form: 'Comprimé', laboratory: 'Merck' },
  { name: 'Levothyrox', dosage: '100µg', form: 'Comprimé', laboratory: 'Merck' },
  { name: 'Levothyrox', dosage: '125µg', form: 'Comprimé', laboratory: 'Merck' },
  { name: 'Levothyrox', dosage: '150µg', form: 'Comprimé', laboratory: 'Merck' },
  { name: 'L-Thyroxine', dosage: '50µg', form: 'Comprimé', laboratory: 'Générique' },
  { name: 'L-Thyroxine', dosage: '100µg', form: 'Comprimé', laboratory: 'Générique' },
  
  // Antibiotiques
  { name: 'Amoxicilline', dosage: '500mg', form: 'Gélule', laboratory: 'Générique' },
  { name: 'Amoxicilline', dosage: '1g', form: 'Gélule', laboratory: 'Générique' },
  { name: 'Augmentin', dosage: '500mg', form: 'Comprimé', laboratory: 'GSK' },
  { name: 'Augmentin', dosage: '1g', form: 'Comprimé', laboratory: 'GSK' },
  { name: 'Azithromycine', dosage: '250mg', form: 'Comprimé', laboratory: 'Générique' },
  { name: 'Zithromax', dosage: '250mg', form: 'Comprimé', laboratory: 'Pfizer' },
  { name: 'Clamoxyl', dosage: '500mg', form: 'Gélule', laboratory: 'GSK' },
  { name: 'Clamoxyl', dosage: '1g', form: 'Gélule', laboratory: 'GSK' },
  
  // Asthme / Respiratoire
  { name: 'Ventoline', dosage: '100µg', form: 'Inhalateur', laboratory: 'GSK' },
  { name: 'Seretide', dosage: '250µg', form: 'Inhalateur', laboratory: 'GSK' },
  { name: 'Symbicort', dosage: '200µg', form: 'Inhalateur', laboratory: 'AstraZeneca' },
  { name: 'Flixotide', dosage: '125µg', form: 'Inhalateur', laboratory: 'GSK' },
  { name: 'Singulair', dosage: '10mg', form: 'Comprimé', laboratory: 'MSD' },
  
  // Anxiolytiques / Antidépresseurs
  { name: 'Xanax', dosage: '0.25mg', form: 'Comprimé', laboratory: 'Pfizer' },
  { name: 'Xanax', dosage: '0.5mg', form: 'Comprimé', laboratory: 'Pfizer' },
  { name: 'Lexomil', dosage: '6mg', form: 'Comprimé', laboratory: 'Roche' },
  { name: 'Atarax', dosage: '25mg', form: 'Comprimé', laboratory: 'UCB Pharma' },
  { name: 'Sertraline', dosage: '50mg', form: 'Comprimé', laboratory: 'Générique' },
  { name: 'Seroplex', dosage: '10mg', form: 'Comprimé', laboratory: 'Lundbeck' },
  { name: 'Seroplex', dosage: '20mg', form: 'Comprimé', laboratory: 'Lundbeck' },
  { name: 'Effexor', dosage: '75mg', form: 'Gélule', laboratory: 'Pfizer' },
  { name: 'Deroxat', dosage: '20mg', form: 'Comprimé', laboratory: 'GSK' },
  
  // Antihistaminiques
  { name: 'Cetirizine', dosage: '10mg', form: 'Comprimé', laboratory: 'Générique' },
  { name: 'Zyrtec', dosage: '10mg', form: 'Comprimé', laboratory: 'UCB Pharma' },
  { name: 'Aerius', dosage: '5mg', form: 'Comprimé', laboratory: 'MSD' },
  { name: 'Clarityne', dosage: '10mg', form: 'Comprimé', laboratory: 'Bayer' },
  
  // Diabète
  { name: 'Metformine', dosage: '500mg', form: 'Comprimé', laboratory: 'Générique' },
  { name: 'Metformine', dosage: '850mg', form: 'Comprimé', laboratory: 'Générique' },
  { name: 'Metformine', dosage: '1000mg', form: 'Comprimé', laboratory: 'Générique' },
  { name: 'Glucophage', dosage: '850mg', form: 'Comprimé', laboratory: 'Merck' },
  { name: 'Glucophage', dosage: '1000mg', form: 'Comprimé', laboratory: 'Merck' },
  
  // Hypertension / Cardiovasculaire
  { name: 'Amlodipine', dosage: '5mg', form: 'Comprimé', laboratory: 'Générique' },
  { name: 'Amlodipine', dosage: '10mg', form: 'Comprimé', laboratory: 'Générique' },
  { name: 'Ramipril', dosage: '5mg', form: 'Comprimé', laboratory: 'Générique' },
  { name: 'Ramipril', dosage: '10mg', form: 'Comprimé', laboratory: 'Générique' },
  { name: 'Tahor', dosage: '10mg', form: 'Comprimé', laboratory: 'Pfizer' },
  { name: 'Tahor', dosage: '20mg', form: 'Comprimé', laboratory: 'Pfizer' },
  { name: 'Crestor', dosage: '5mg', form: 'Comprimé', laboratory: 'AstraZeneca' },
  { name: 'Crestor', dosage: '10mg', form: 'Comprimé', laboratory: 'AstraZeneca' },
  
  // Douleurs neuropathiques
  { name: 'Lyrica', dosage: '75mg', form: 'Gélule', laboratory: 'Pfizer' },
  { name: 'Lyrica', dosage: '150mg', form: 'Gélule', laboratory: 'Pfizer' },
  { name: 'Neurontin', dosage: '300mg', form: 'Gélule', laboratory: 'Pfizer' },
  
  // Sommeil
  { name: 'Stilnox', dosage: '10mg', form: 'Comprimé', laboratory: 'Sanofi' },
  { name: 'Imovane', dosage: '7.5mg', form: 'Comprimé', laboratory: 'Sanofi' },
  { name: 'Melatonine', dosage: '1mg', form: 'Comprimé', laboratory: 'Générique' },
  
  // Vitamines / Compléments
  { name: 'Tardyferon', dosage: '80mg', form: 'Comprimé', laboratory: 'Pierre Fabre' },
  { name: 'Vitamine D', dosage: '100000 UI', form: 'Ampoule', laboratory: 'Générique' },
  { name: 'Magnésium', dosage: '300mg', form: 'Comprimé', laboratory: 'Générique' },
  { name: 'Calcium', dosage: '500mg', form: 'Comprimé', laboratory: 'Générique' },
  
  // Contraception
  { name: 'Leeloo', dosage: '', form: 'Comprimé', laboratory: 'Theramex' },
  { name: 'Optimizette', dosage: '75µg', form: 'Comprimé', laboratory: 'Theramex' },
  { name: 'Cerazette', dosage: '75µg', form: 'Comprimé', laboratory: 'MSD' },
];

/**
 * Normalise une chaîne pour la recherche (enlève accents, met en minuscules)
 */
function normalizeString(str: string): string {
  return str
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');
}

/**
 * Calcule le score de similarité entre deux chaînes (algorithme simple)
 */
function similarityScore(query: string, target: string): number {
  const normalizedQuery = normalizeString(query);
  const normalizedTarget = normalizeString(target);
  
  // Correspondance exacte
  if (normalizedTarget === normalizedQuery) return 100;
  
  // Commence par la requête
  if (normalizedTarget.startsWith(normalizedQuery)) return 90;
  
  // Contient la requête
  if (normalizedTarget.includes(normalizedQuery)) return 70;
  
  // Calcul de similarité plus avancé (caractères en commun)
  let matches = 0;
  for (let i = 0; i < normalizedQuery.length; i++) {
    if (normalizedTarget.includes(normalizedQuery[i])) {
      matches++;
    }
  }
  
  return (matches / normalizedQuery.length) * 50;
}

/**
 * Recherche locale dans la base de données
 */
export function searchMedications(query: string): MedicationSuggestion[] {
  if (!query || query.trim().length < 2) {
    return [];
  }

  const normalizedQuery = normalizeString(query.trim());
  
  // Chercher et scorer tous les médicaments
  const results = MEDICATIONS_DATABASE
    .map((med, index) => ({
      ...med,
      id: `med_${index}`,
      score: similarityScore(normalizedQuery, med.name)
    }))
    .filter(med => med.score > 30) // Seuil de pertinence
    .sort((a, b) => b.score - a.score) // Trier par score décroissant
    .slice(0, 15) // Limiter à 15 résultats
    .map(({ score, ...med }) => med); // Enlever le score

  return results;
}

/**
 * Obtenir les médicaments les plus populaires pour affichage initial
 */
export function getPopularMedications(): MedicationSuggestion[] {
  return MEDICATIONS_DATABASE
    .slice(0, 10)
    .map((med, index) => ({
      ...med,
      id: `popular_${index}`
    }));
}
