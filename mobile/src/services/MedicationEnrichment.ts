/**
 * Service d'enrichissement automatique des médicaments
 * - Code ATC (Anatomical Therapeutic Chemical)
 * - Substance active
 * - Laboratoire
 * - Forme pharmaceutique
 */

interface MedicationEnrichmentResult {
  success: boolean;
  atc_code?: string;
  active_substance?: string;
  laboratory?: string;
  form?: string;
  confidence: 'high' | 'medium' | 'low';
  source: 'bdpm_api' | 'gpt4o' | 'local_cache' | 'none';
  error?: string;
}

interface BDPMMedicament {
  codeCIS: string;
  denomination: string;
  formePharmaceutique: string;
  voiesAdministration: string[];
  statutAMM: string;
  titulaire: string;
  dateAMM?: string;
}

interface BDPMComposition {
  codeCIS: string;
  designationElementPharmaceutique: string;
  codeSubstance: string;
  denominationSubstance: string;
  dosageSubstance: string;
  referenceDosage: string;
  natureComposant: string;
}

interface BDPMPresentations {
  codeCIS: string;
  codeCIP7: string;
  codeCIP13: string;
  libellePresentation: string;
  statutAdministratif: string;
  etatCommercialisation: string;
  dateDeclarationCommercialisation?: string;
  codeCIP13?: string;
}

// Cache local des résultats (évite les appels répétés)
const enrichmentCache = new Map<string, MedicationEnrichmentResult>();

/**
 * Normalise le nom du médicament pour la recherche
 */
function normalizeMedicationName(name: string): string {
  return name
    .toLowerCase()
    .trim()
    .replace(/\s+/g, ' ')
    .replace(/[®™©]/g, '')
    .split(/\s+/)[0]; // Prendre le premier mot (généralement le nom DCI)
}

/**
 * Recherche le médicament dans la Base de Données Publique des Médicaments (France)
 * API officielle : https://base-donnees-publique.medicaments.gouv.fr
 */
async function searchBDPMAPI(medicationName: string): Promise<MedicationEnrichmentResult> {
  try {
    const normalizedName = normalizeMedicationName(medicationName);
    console.log(`[MedicationEnrichment] Recherche BDPM pour: ${normalizedName}`);

    // API BDPM : Recherche par dénomination
    const searchUrl = `https://base-donnees-publique.medicaments.gouv.fr/api/v1/medicaments.json?query=${encodeURIComponent(normalizedName)}&limit=5`;
    
    const response = await fetch(searchUrl, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`BDPM API error: ${response.status}`);
    }

    const data = await response.json();
    
    if (!data || !data.data || data.data.length === 0) {
      console.log('[MedicationEnrichment] Aucun résultat BDPM');
      return {
        success: false,
        confidence: 'low',
        source: 'bdpm_api',
        error: 'Aucun résultat trouvé dans BDPM',
      };
    }

    // Prendre le premier résultat (meilleure correspondance)
    const medication = data.data[0];
    
    // Récupérer la composition pour obtenir la substance active
    const compositionUrl = `https://base-donnees-publique.medicaments.gouv.fr/api/v1/compositions/${medication.cis}.json`;
    let activeSubstance = undefined;
    
    try {
      const compResponse = await fetch(compositionUrl);
      if (compResponse.ok) {
        const compData = await compResponse.json();
        if (compData && compData.data && compData.data.length > 0) {
          activeSubstance = compData.data[0].denomination_substance || compData.data[0].designation_element_pharmaceutique;
        }
      }
    } catch (compError) {
      console.warn('[MedicationEnrichment] Erreur récupération composition:', compError);
    }

    console.log(`[MedicationEnrichment] ✅ BDPM trouvé: ${medication.denomination}`);

    return {
      success: true,
      atc_code: undefined, // BDPM ne fournit pas directement le code ATC
      active_substance: activeSubstance,
      laboratory: medication.titulaire,
      form: medication.forme_pharmaceutique,
      confidence: 'high',
      source: 'bdpm_api',
    };
  } catch (error) {
    console.error('[MedicationEnrichment] Erreur BDPM API:', error);
    return {
      success: false,
      confidence: 'low',
      source: 'bdpm_api',
      error: error instanceof Error ? error.message : 'Erreur inconnue',
    };
  }
}

/**
 * Utilise GPT-4o pour enrichir les informations du médicament
 * Nécessite EXPO_PUBLIC_OPENAI_API_KEY dans .env
 */
async function enrichWithGPT4o(
  medicationName: string,
  dosage?: string,
  unit?: string
): Promise<MedicationEnrichmentResult> {
  try {
    const apiKey = process.env.EXPO_PUBLIC_OPENAI_API_KEY;
    
    if (!apiKey || apiKey === 'placeholder-key') {
      console.warn('[MedicationEnrichment] OpenAI API key non configurée');
      return {
        success: false,
        confidence: 'low',
        source: 'gpt4o',
        error: 'API key non configurée',
      };
    }

    const fullName = dosage && unit 
      ? `${medicationName} ${dosage}${unit}`
      : medicationName;

    console.log(`[MedicationEnrichment] Appel GPT-4o pour: ${fullName}`);

    const prompt = `Tu es un expert en pharmacologie. Pour le médicament "${fullName}", fournis les informations suivantes au format JSON strict :

{
  "atc_code": "Code ATC (ex: N06AB06)",
  "active_substance": "Substance active principale (DCI)",
  "form": "Forme pharmaceutique (comprimé, gélule, etc.)",
  "confidence": "high/medium/low selon ta certitude"
}

Important :
- Si tu ne connais pas une information, mets null
- Le code ATC doit être exact (7 caractères: 1 lettre, 2 chiffres, 1 lettre, 2 chiffres, 2 chiffres)
- Réponds UNIQUEMENT avec le JSON, aucun texte avant ou après
- Utilise les noms DCI (Dénomination Commune Internationale)`;

    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: 'gpt-4o',
        messages: [
          {
            role: 'system',
            content: 'Tu es un expert en pharmacologie spécialisé dans la classification ATC des médicaments. Tu réponds toujours en JSON strict.',
          },
          {
            role: 'user',
            content: prompt,
          },
        ],
        temperature: 0.1, // Bas pour plus de précision
        max_tokens: 200,
      }),
    });

    if (!response.ok) {
      throw new Error(`OpenAI API error: ${response.status}`);
    }

    const data = await response.json();
    const content = data.choices[0]?.message?.content;

    if (!content) {
      throw new Error('Pas de réponse GPT-4o');
    }

    // Parser le JSON
    const result = JSON.parse(content.trim());

    console.log('[MedicationEnrichment] ✅ GPT-4o résultat:', result);

    return {
      success: true,
      atc_code: result.atc_code || undefined,
      active_substance: result.active_substance || undefined,
      form: result.form || undefined,
      confidence: result.confidence || 'medium',
      source: 'gpt4o',
    };
  } catch (error) {
    console.error('[MedicationEnrichment] Erreur GPT-4o:', error);
    return {
      success: false,
      confidence: 'low',
      source: 'gpt4o',
      error: error instanceof Error ? error.message : 'Erreur inconnue',
    };
  }
}

/**
 * Recherche le code ATC dans la base locale Pulse
 * (depuis medication_energy_impacts)
 */
async function searchLocalDatabase(
  medicationName: string,
  activeSubstance?: string
): Promise<MedicationEnrichmentResult> {
  try {
    // Import dynamique pour éviter les cycles
    const { supabase } = await import('../lib/supabase');

    const normalizedName = normalizeMedicationName(medicationName);
    
    // Recherche par nom ou substance active
    const { data, error } = await supabase
      .from('medication_energy_impacts')
      .select('atc_code, medication_name, active_substance')
      .or(`medication_name.ilike.%${normalizedName}%,active_substance.ilike.%${normalizedName}%`)
      .limit(1)
      .single();

    if (error || !data) {
      return {
        success: false,
        confidence: 'low',
        source: 'local_cache',
        error: 'Non trouvé dans la base locale',
      };
    }

    console.log('[MedicationEnrichment] ✅ Trouvé dans base locale:', data);

    return {
      success: true,
      atc_code: data.atc_code,
      active_substance: data.active_substance,
      confidence: 'high',
      source: 'local_cache',
    };
  } catch (error) {
    console.error('[MedicationEnrichment] Erreur recherche locale:', error);
    return {
      success: false,
      confidence: 'low',
      source: 'local_cache',
      error: error instanceof Error ? error.message : 'Erreur inconnue',
    };
  }
}

/**
 * Enrichit automatiquement un médicament avec toutes les sources disponibles
 * Stratégie : Local → BDPM → GPT-4o
 */
export async function enrichMedication(
  medicationName: string,
  dosage?: string,
  unit?: string
): Promise<MedicationEnrichmentResult> {
  // Vérifier le cache
  const cacheKey = `${medicationName}_${dosage}_${unit}`.toLowerCase();
  if (enrichmentCache.has(cacheKey)) {
    console.log('[MedicationEnrichment] 💾 Résultat depuis cache');
    return enrichmentCache.get(cacheKey)!;
  }

  console.log('[MedicationEnrichment] 🔍 Enrichissement pour:', medicationName);

  // Étape 1 : Recherche locale (la plus rapide et fiable)
  const localResult = await searchLocalDatabase(medicationName);
  if (localResult.success && localResult.atc_code) {
    enrichmentCache.set(cacheKey, localResult);
    return localResult;
  }

  // Étape 2 : API BDPM (officielle française)
  const bdpmResult = await searchBDPMAPI(medicationName);
  
  // Étape 3 : GPT-4o pour obtenir le code ATC si BDPM n'a pas tout
  let gpt4oResult: MedicationEnrichmentResult | null = null;
  if (!bdpmResult.atc_code) {
    gpt4oResult = await enrichWithGPT4o(medicationName, dosage, unit);
  }

  // Merger les résultats (BDPM + GPT-4o)
  const finalResult: MedicationEnrichmentResult = {
    success: bdpmResult.success || (gpt4oResult?.success ?? false),
    atc_code: gpt4oResult?.atc_code || bdpmResult.atc_code,
    active_substance: bdpmResult.active_substance || gpt4oResult?.active_substance,
    laboratory: bdpmResult.laboratory,
    form: bdpmResult.form || gpt4oResult?.form,
    confidence: gpt4oResult?.atc_code ? (gpt4oResult.confidence || 'medium') : (bdpmResult.confidence || 'low'),
    source: gpt4oResult?.atc_code ? 'gpt4o' : bdpmResult.source,
  };

  // Mettre en cache
  if (finalResult.success) {
    enrichmentCache.set(cacheKey, finalResult);
  }

  console.log('[MedicationEnrichment] ✅ Enrichissement final:', finalResult);

  return finalResult;
}

/**
 * Vide le cache d'enrichissement (utile pour les tests)
 */
export function clearEnrichmentCache(): void {
  enrichmentCache.clear();
  console.log('[MedicationEnrichment] 🗑️ Cache vidé');
}

/**
 * Récupère la taille du cache
 */
export function getEnrichmentCacheSize(): number {
  return enrichmentCache.size;
}
