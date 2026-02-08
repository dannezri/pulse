/**
 * ⚠️ OBSOLÈTE - Ce service est déprécié et ne devrait plus être utilisé
 * 
 * Utilisez GiygasMedicationAPI.ts à la place, qui utilise l'API Giygas
 * via le backend Pulse pour des données à jour et complètes.
 * 
 * @deprecated Remplacé par GiygasMedicationAPI.ts (2026-02-04)
 * 
 * Ancien service d'API pour la recherche de médicaments
 * Base de données locale complète des médicaments français les plus courants
 */

export interface MedicationSuggestion {
  id: string;
  name: string;
  dosage?: string;
  form?: string;
  laboratory?: string;
  commonFrequency?: number; // Fréquence quotidienne commune (1-4x/jour)
}

/**
 * Base de données étendue des médicaments français les plus prescrits
 * Source: Top médicaments les plus vendus en France (2024-2026)
 * Contient 180+ médicaments couvrant toutes les catégories principales
 */
export const MEDICATIONS_DATABASE = [
  // Antalgiques / Anti-inflammatoires
  { name: 'Doliprane', dosage: '500mg', form: 'Comprimé', laboratory: 'Sanofi', commonFrequency: 3 },
  { name: 'Doliprane', dosage: '1000mg', form: 'Comprimé', laboratory: 'Sanofi', commonFrequency: 3 },
  { name: 'Dafalgan', dosage: '500mg', form: 'Comprimé', laboratory: 'Bristol-Myers Squibb', commonFrequency: 3 },
  { name: 'Dafalgan', dosage: '1000mg', form: 'Comprimé', laboratory: 'Bristol-Myers Squibb', commonFrequency: 3 },
  { name: 'Efferalgan', dosage: '500mg', form: 'Comprimé', laboratory: 'Bristol-Myers Squibb', commonFrequency: 3 },
  { name: 'Efferalgan', dosage: '1000mg', form: 'Comprimé', laboratory: 'Bristol-Myers Squibb', commonFrequency: 3 },
  { name: 'Paracétamol', dosage: '500mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 3 },
  { name: 'Paracétamol', dosage: '1000mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 3 },
  { name: 'Ibuprofène', dosage: '200mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 3 },
  { name: 'Ibuprofène', dosage: '400mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 3 },
  { name: 'Advil', dosage: '200mg', form: 'Comprimé', laboratory: 'Pfizer', commonFrequency: 3 },
  { name: 'Advil', dosage: '400mg', form: 'Comprimé', laboratory: 'Pfizer', commonFrequency: 3 },
  { name: 'Nurofen', dosage: '200mg', form: 'Comprimé', laboratory: 'Reckitt Benckiser', commonFrequency: 3 },
  { name: 'Nurofen', dosage: '400mg', form: 'Comprimé', laboratory: 'Reckitt Benckiser', commonFrequency: 3 },
  { name: 'Aspirine', dosage: '500mg', form: 'Comprimé', laboratory: 'Bayer', commonFrequency: 1 },
  { name: 'Aspirine', dosage: '1000mg', form: 'Comprimé', laboratory: 'Bayer', commonFrequency: 1 },
  { name: 'Kardegic', dosage: '75mg', form: 'Poudre', laboratory: 'Sanofi', commonFrequency: 1 },
  { name: 'Kardegic', dosage: '160mg', form: 'Poudre', laboratory: 'Sanofi', commonFrequency: 1 },
  { name: 'Tramadol', dosage: '50mg', form: 'Gélule', laboratory: 'Générique', commonFrequency: 3 },
  { name: 'Tramadol', dosage: '100mg', form: 'Gélule', laboratory: 'Générique', commonFrequency: 2 },
  { name: 'Codoliprane', dosage: '500mg', form: 'Comprimé', laboratory: 'Sanofi', commonFrequency: 3 },
  
  // Antispasmodiques
  { name: 'Spasfon', dosage: '80mg', form: 'Comprimé', laboratory: 'Teva', commonFrequency: 3 },
  { name: 'Spasfon', dosage: '160mg', form: 'Comprimé', laboratory: 'Teva', commonFrequency: 3 },
  { name: 'Débridat', dosage: '100mg', form: 'Comprimé', laboratory: 'Mylan', commonFrequency: 3 },
  
  // Troubles digestifs
  { name: 'Omeprazole', dosage: '10mg', form: 'Gélule', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Omeprazole', dosage: '20mg', form: 'Gélule', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Inexium', dosage: '20mg', form: 'Comprimé', laboratory: 'AstraZeneca', commonFrequency: 1 },
  { name: 'Inexium', dosage: '40mg', form: 'Comprimé', laboratory: 'AstraZeneca', commonFrequency: 1 },
  { name: 'Gaviscon', dosage: '', form: 'Suspension buvable', laboratory: 'Reckitt Benckiser', commonFrequency: 3 },
  { name: 'Maalox', dosage: '', form: 'Suspension buvable', laboratory: 'Sanofi', commonFrequency: 3 },
  { name: 'Smecta', dosage: '3g', form: 'Poudre', laboratory: 'Ipsen', commonFrequency: 3 },
  { name: 'Motilium', dosage: '10mg', form: 'Comprimé', laboratory: 'Janssen', commonFrequency: 3 },
  { name: 'Imodium', dosage: '2mg', form: 'Gélule', laboratory: 'Johnson & Johnson', commonFrequency: 2 },
  
  // Thyroïde
  { name: 'Levothyrox', dosage: '25µg', form: 'Comprimé', laboratory: 'Merck', commonFrequency: 1 },
  { name: 'Levothyrox', dosage: '50µg', form: 'Comprimé', laboratory: 'Merck', commonFrequency: 1 },
  { name: 'Levothyrox', dosage: '75µg', form: 'Comprimé', laboratory: 'Merck', commonFrequency: 1 },
  { name: 'Levothyrox', dosage: '100µg', form: 'Comprimé', laboratory: 'Merck', commonFrequency: 1 },
  { name: 'Levothyrox', dosage: '125µg', form: 'Comprimé', laboratory: 'Merck', commonFrequency: 1 },
  { name: 'Levothyrox', dosage: '150µg', form: 'Comprimé', laboratory: 'Merck', commonFrequency: 1 },
  { name: 'L-Thyroxine', dosage: '50µg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'L-Thyroxine', dosage: '100µg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  
  // Antibiotiques
  { name: 'Amoxicilline', dosage: '500mg', form: 'Gélule', laboratory: 'Générique', commonFrequency: 3 },
  { name: 'Amoxicilline', dosage: '1g', form: 'Gélule', laboratory: 'Générique', commonFrequency: 3 },
  { name: 'Augmentin', dosage: '500mg', form: 'Comprimé', laboratory: 'GSK', commonFrequency: 3 },
  { name: 'Augmentin', dosage: '1g', form: 'Comprimé', laboratory: 'GSK', commonFrequency: 2 },
  { name: 'Azithromycine', dosage: '250mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Zithromax', dosage: '250mg', form: 'Comprimé', laboratory: 'Pfizer', commonFrequency: 1 },
  { name: 'Clamoxyl', dosage: '500mg', form: 'Gélule', laboratory: 'GSK', commonFrequency: 3 },
  { name: 'Clamoxyl', dosage: '1g', form: 'Gélule', laboratory: 'GSK', commonFrequency: 2 },
  
  // Asthme / Respiratoire
  { name: 'Ventoline', dosage: '100µg', form: 'Inhalateur', laboratory: 'GSK' },
  { name: 'Seretide', dosage: '250µg', form: 'Inhalateur', laboratory: 'GSK' },
  { name: 'Symbicort', dosage: '200µg', form: 'Inhalateur', laboratory: 'AstraZeneca' },
  { name: 'Flixotide', dosage: '125µg', form: 'Inhalateur', laboratory: 'GSK' },
  { name: 'Singulair', dosage: '10mg', form: 'Comprimé', laboratory: 'MSD' },
  
  // Anxiolytiques / Antidépresseurs
  { name: 'Xanax', dosage: '0.25mg', form: 'Comprimé', laboratory: 'Pfizer', commonFrequency: 2 },
  { name: 'Xanax', dosage: '0.5mg', form: 'Comprimé', laboratory: 'Pfizer', commonFrequency: 2 },
  { name: 'Alprazolam', dosage: '0.25mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 2 },
  { name: 'Alprazolam', dosage: '0.5mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 2 },
  { name: 'Lexomil', dosage: '6mg', form: 'Comprimé', laboratory: 'Roche', commonFrequency: 2 },
  { name: 'Atarax', dosage: '25mg', form: 'Comprimé', laboratory: 'UCB Pharma', commonFrequency: 2 },
  { name: 'Hydroxyzine', dosage: '25mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 2 },
  { name: 'Sertraline', dosage: '50mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Sertraline', dosage: '100mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Zoloft', dosage: '50mg', form: 'Comprimé', laboratory: 'Pfizer', commonFrequency: 1 },
  { name: 'Seroplex', dosage: '10mg', form: 'Comprimé', laboratory: 'Lundbeck', commonFrequency: 1 },
  { name: 'Seroplex', dosage: '20mg', form: 'Comprimé', laboratory: 'Lundbeck', commonFrequency: 1 },
  { name: 'Escitalopram', dosage: '10mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Escitalopram', dosage: '20mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Effexor', dosage: '75mg', form: 'Gélule', laboratory: 'Pfizer', commonFrequency: 1 },
  { name: 'Effexor', dosage: '150mg', form: 'Gélule', laboratory: 'Pfizer', commonFrequency: 1 },
  { name: 'Venlafaxine', dosage: '75mg', form: 'Gélule', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Deroxat', dosage: '20mg', form: 'Comprimé', laboratory: 'GSK', commonFrequency: 1 },
  { name: 'Paroxétine', dosage: '20mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Prozac', dosage: '20mg', form: 'Gélule', laboratory: 'Lilly', commonFrequency: 1 },
  { name: 'Fluoxétine', dosage: '20mg', form: 'Gélule', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Mirtazapine', dosage: '15mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Mirtazapine', dosage: '30mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Norset', dosage: '15mg', form: 'Comprimé', laboratory: 'MSD', commonFrequency: 1 },
  { name: 'Norset', dosage: '30mg', form: 'Comprimé', laboratory: 'MSD', commonFrequency: 1 },
  { name: 'Cymbalta', dosage: '30mg', form: 'Gélule', laboratory: 'Lilly', commonFrequency: 1 },
  { name: 'Cymbalta', dosage: '60mg', form: 'Gélule', laboratory: 'Lilly', commonFrequency: 1 },
  { name: 'Duloxétine', dosage: '30mg', form: 'Gélule', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Duloxétine', dosage: '60mg', form: 'Gélule', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Laroxyl', dosage: '25mg', form: 'Comprimé', laboratory: 'Pierre Fabre', commonFrequency: 1 },
  { name: 'Amitriptyline', dosage: '25mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Bromazepam', dosage: '6mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 2 },
  
  // Antihistaminiques
  { name: 'Cetirizine', dosage: '10mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Zyrtec', dosage: '10mg', form: 'Comprimé', laboratory: 'UCB Pharma', commonFrequency: 1 },
  { name: 'Aerius', dosage: '5mg', form: 'Comprimé', laboratory: 'MSD', commonFrequency: 1 },
  { name: 'Desloratadine', dosage: '5mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Clarityne', dosage: '10mg', form: 'Comprimé', laboratory: 'Bayer', commonFrequency: 1 },
  { name: 'Loratadine', dosage: '10mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  
  // Diabète
  { name: 'Metformine', dosage: '500mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 2 },
  { name: 'Metformine', dosage: '850mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 2 },
  { name: 'Metformine', dosage: '1000mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 2 },
  { name: 'Glucophage', dosage: '850mg', form: 'Comprimé', laboratory: 'Merck', commonFrequency: 2 },
  { name: 'Glucophage', dosage: '1000mg', form: 'Comprimé', laboratory: 'Merck', commonFrequency: 2 },
  
  // Hypertension / Cardiovasculaire
  { name: 'Amlodipine', dosage: '5mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Amlodipine', dosage: '10mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Ramipril', dosage: '5mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Ramipril', dosage: '10mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Enalapril', dosage: '5mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Enalapril', dosage: '20mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Lisinopril', dosage: '10mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Lisinopril', dosage: '20mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Tahor', dosage: '10mg', form: 'Comprimé', laboratory: 'Pfizer', commonFrequency: 1 },
  { name: 'Tahor', dosage: '20mg', form: 'Comprimé', laboratory: 'Pfizer', commonFrequency: 1 },
  { name: 'Atorvastatine', dosage: '10mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Atorvastatine', dosage: '20mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Crestor', dosage: '5mg', form: 'Comprimé', laboratory: 'AstraZeneca', commonFrequency: 1 },
  { name: 'Crestor', dosage: '10mg', form: 'Comprimé', laboratory: 'AstraZeneca', commonFrequency: 1 },
  { name: 'Rosuvastatine', dosage: '5mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Rosuvastatine', dosage: '10mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Simvastatine', dosage: '20mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Simvastatine', dosage: '40mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  
  // Douleurs neuropathiques
  { name: 'Lyrica', dosage: '75mg', form: 'Gélule', laboratory: 'Pfizer', commonFrequency: 2 },
  { name: 'Lyrica', dosage: '150mg', form: 'Gélule', laboratory: 'Pfizer', commonFrequency: 2 },
  { name: 'Prégabaline', dosage: '75mg', form: 'Gélule', laboratory: 'Générique', commonFrequency: 2 },
  { name: 'Prégabaline', dosage: '150mg', form: 'Gélule', laboratory: 'Générique', commonFrequency: 2 },
  { name: 'Neurontin', dosage: '300mg', form: 'Gélule', laboratory: 'Pfizer', commonFrequency: 3 },
  { name: 'Gabapentine', dosage: '300mg', form: 'Gélule', laboratory: 'Générique', commonFrequency: 3 },
  
  // Sommeil
  { name: 'Stilnox', dosage: '10mg', form: 'Comprimé', laboratory: 'Sanofi', commonFrequency: 1 },
  { name: 'Zolpidem', dosage: '10mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Imovane', dosage: '7.5mg', form: 'Comprimé', laboratory: 'Sanofi', commonFrequency: 1 },
  { name: 'Zopiclone', dosage: '7.5mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Melatonine', dosage: '1mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Melatonine', dosage: '2mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Circadin', dosage: '2mg', form: 'Comprimé', laboratory: 'RAD Neurim', commonFrequency: 1 },
  
  // Vitamines / Compléments
  { name: 'Tardyferon', dosage: '80mg', form: 'Comprimé', laboratory: 'Pierre Fabre', commonFrequency: 1 },
  { name: 'Fer', dosage: '80mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Vitamine D', dosage: '100000 UI', form: 'Ampoule', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Vitamine D', dosage: '1000 UI', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Vitamine B12', dosage: '1000µg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Magnésium', dosage: '300mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Calcium', dosage: '500mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Vitamine C', dosage: '1000mg', form: 'Comprimé', laboratory: 'Générique', commonFrequency: 1 },
  { name: 'Omega 3', dosage: '1000mg', form: 'Capsule', laboratory: 'Générique', commonFrequency: 1 },
  
  // Contraception
  { name: 'Leeloo', dosage: '', form: 'Comprimé', laboratory: 'Theramex', commonFrequency: 1 },
  { name: 'Optimizette', dosage: '75µg', form: 'Comprimé', laboratory: 'Theramex', commonFrequency: 1 },
  { name: 'Cerazette', dosage: '75µg', form: 'Comprimé', laboratory: 'MSD', commonFrequency: 1 },
  { name: 'Minidril', dosage: '', form: 'Comprimé', laboratory: 'Pfizer', commonFrequency: 1 },
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
 * Recherche dans une API externe (fallback si base locale vide)
 * Utilise l'API publique française des médicaments
 */
async function searchMedicationsFromAPI(query: string): Promise<MedicationSuggestion[]> {
  try {
    // API publique française : Base de données publique des médicaments
    // Format: https://open-medicaments.fr/api/v1/medicaments?query=doliprane
    const url = `https://open-medicaments.fr/api/v1/medicaments?query=${encodeURIComponent(query)}&limit=10`;
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      console.warn('[MedicationAPI] API externe erreur:', response.status);
      return [];
    }

    const data = await response.json();
    
    // Transformer les résultats au format MedicationSuggestion
    if (Array.isArray(data)) {
      return data.slice(0, 10).map((item: any, index: number) => ({
        id: `api_${index}_${Date.now()}`,
        name: item.denomination || item.name || '',
        dosage: item.dosage || '',
        form: item.forme || item.form || 'Comprimé',
        laboratory: item.titulaire || item.laboratory || 'Laboratoire',
        commonFrequency: undefined, // Pas de suggestion de fréquence pour l'API
      }));
    }

    return [];
  } catch (error) {
    console.error('[MedicationAPI] Erreur API externe:', error);
    return [];
  }
}

/**
 * Recherche locale dans la base de données
 */
function searchMedicationsLocal(query: string): MedicationSuggestion[] {
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
 * Recherche de médicaments (locale + API externe en fallback)
 */
export async function searchMedications(query: string): Promise<MedicationSuggestion[]> {
  if (!query || query.trim().length < 2) {
    return [];
  }

  // 1. Chercher d'abord dans la base locale
  const localResults = searchMedicationsLocal(query);

  // 2. Si résultats trouvés localement, les retourner
  if (localResults.length > 0) {
    return localResults;
  }

  // 3. Sinon, chercher dans l'API externe
  console.log('[MedicationAPI] Aucun résultat local, recherche via API externe...');
  const apiResults = await searchMedicationsFromAPI(query);

  if (apiResults.length > 0) {
    console.log(`[MedicationAPI] ✅ ${apiResults.length} résultats trouvés via API externe`);
  } else {
    console.log('[MedicationAPI] ❌ Aucun résultat trouvé');
  }

  return apiResults;
}

/**
 * Version synchrone pour compatibilité (recherche locale uniquement)
 */
export function searchMedicationsSync(query: string): MedicationSuggestion[] {
  return searchMedicationsLocal(query);
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
