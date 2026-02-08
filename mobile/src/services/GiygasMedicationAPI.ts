/**
 * Service d'API pour la recherche de médicaments via Giygas API
 * Remplace l'ancienne base locale par des appels au backend Pulse
 */

import { API_URL } from '../config/api';

export interface MedicationSuggestion {
  id: string; // CIS (Code Identifiant de Spécialité)
  name: string; // Dénomination du médicament
  dosage?: string;
  form?: string; // Forme pharmaceutique
  laboratory?: string;
  activeSubstance?: string; // Substance active (DCI)
  status?: string; // Statut administratif
  // Nouveau : support des données enrichies
  cis?: string; // CIS explicite
  presentations?: {
    cip13: string;
    cip7?: string;
    label?: string;
    price?: number;
    reimbursement_rate?: number;
  }[];
}

interface BackendSearchResponse {
  results: {
    cis: string;
    name: string;
    form?: string;
    laboratory?: string;
    active_substance?: string;
    status?: string;
  }[];
}

interface BackendDetailResponse {
  medication: {
    cis: string;
    name: string;
    form?: string;
    laboratory?: string;
    active_substance?: string;
    status?: string;
    composition?: {
      substance: string;
      dosage?: string;
      dosage_unit?: string;
    }[];
    presentations?: {
      cip13: string;
      cip7?: string;
      label?: string;
      price?: number;
      reimbursement_rate?: number;
    }[];
    generics?: {
      group_id?: string;
      type?: string;
      cis: string;
      name: string;
    }[];
    conditions?: {
      prescription?: string;
      administration?: string;
    };
  };
}

/**
 * Recherche de médicaments via le backend Pulse (qui utilise Giygas)
 */
export async function searchMedications(query: string): Promise<MedicationSuggestion[]> {
  if (!query || query.trim().length < 2) {
    return [];
  }

  // Créer un AbortController pour le timeout (compatible React Native)
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 secondes

  try {
    const url = `${API_URL}/api/medications/search?q=${encodeURIComponent(query.trim())}`;
    console.log('[GiygasMedicationAPI] Recherche:', url);

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      console.warn('[GiygasMedicationAPI] Erreur HTTP:', response.status);
      return [];
    }

    const data: BackendSearchResponse = await response.json();

    if (!data.results || !Array.isArray(data.results)) {
      console.warn('[GiygasMedicationAPI] Format de réponse invalide');
      return [];
    }

    // Transformer les résultats backend vers notre interface
    const suggestions: MedicationSuggestion[] = data.results.map((item) => ({
      id: item.cis,
      cis: item.cis,
      name: item.name,
      form: item.form,
      laboratory: item.laboratory,
      activeSubstance: item.active_substance,
      status: item.status,
    }));

    console.log(`[GiygasMedicationAPI] ✅ ${suggestions.length} résultats trouvés`);
    return suggestions;

  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      console.error('[GiygasMedicationAPI] Timeout dépassé (10s)');
    } else {
      console.error('[GiygasMedicationAPI] Erreur recherche:', error);
    }
    return [];
  }
}

/**
 * Récupérer les détails d'un médicament par CIS
 */
export async function getMedicationDetails(cis: string): Promise<MedicationSuggestion | null> {
  if (!cis) {
    return null;
  }

  // Créer un AbortController pour le timeout (compatible React Native)
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 secondes

  try {
    const url = `${API_URL}/api/medications/${cis}`;
    console.log('[GiygasMedicationAPI] Détails:', url);

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      console.warn('[GiygasMedicationAPI] Erreur HTTP:', response.status);
      return null;
    }

    const data: BackendDetailResponse = await response.json();

    if (!data.medication) {
      console.warn('[GiygasMedicationAPI] Médicament non trouvé');
      return null;
    }

    const med = data.medication;

    // Extraire le dosage principal de la composition si disponible
    const mainComposition = med.composition?.[0];
    const dosage = mainComposition 
      ? `${mainComposition.dosage || ''}${mainComposition.dosage_unit || ''}`.trim()
      : undefined;

    const suggestion: MedicationSuggestion = {
      id: med.cis,
      cis: med.cis,
      name: med.name,
      form: med.form,
      laboratory: med.laboratory,
      activeSubstance: med.active_substance,
      status: med.status,
      dosage,
      presentations: med.presentations,
    };

    console.log(`[GiygasMedicationAPI] ✅ Détails récupérés pour ${med.name}`);
    return suggestion;

  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      console.error('[GiygasMedicationAPI] Timeout dépassé (10s)');
    } else {
      console.error('[GiygasMedicationAPI] Erreur détails:', error);
    }
    return null;
  }
}

/**
 * Scanner un code-barres (GS1 DataMatrix) pour obtenir les détails du médicament
 * @param barcode Code-barres scanné (GTIN ou CIP13)
 */
export async function scanMedicationBarcode(barcode: string): Promise<MedicationSuggestion | null> {
  if (!barcode || barcode.trim().length === 0) {
    return null;
  }

  // Créer un AbortController pour le timeout (compatible React Native)
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 secondes

  try {
    const url = `${API_URL}/api/medications/scan`;
    console.log('[GiygasMedicationAPI] Scan barcode:', barcode);

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ gtin: barcode.trim() }), // Le backend attend 'gtin' et non 'barcode'
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      console.warn('[GiygasMedicationAPI] Erreur HTTP scan:', response.status);
      const errorData = await response.json().catch(() => ({}));
      console.warn('[GiygasMedicationAPI] Détails erreur:', errorData);
      return null;
    }

    const data: BackendDetailResponse = await response.json();

    if (!data.medication) {
      console.warn('[GiygasMedicationAPI] Médicament non trouvé pour ce code-barres');
      return null;
    }

    const med = data.medication;

    const suggestion: MedicationSuggestion = {
      id: med.cis,
      cis: med.cis,
      name: med.name,
      form: med.form,
      laboratory: med.laboratory,
      activeSubstance: med.active_substance,
      status: med.status,
      presentations: med.presentations,
    };

    console.log(`[GiygasMedicationAPI] ✅ Scan réussi: ${med.name}`);
    return suggestion;

  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      console.error('[GiygasMedicationAPI] Timeout scan dépassé (15s)');
    } else {
      console.error('[GiygasMedicationAPI] Erreur scan:', error);
    }
    return null;
  }
}

/**
 * Version synchrone pour compatibilité (non applicable avec API backend)
 * Retourne un tableau vide car toute recherche nécessite un appel réseau
 */
export function searchMedicationsSync(query: string): MedicationSuggestion[] {
  console.warn('[GiygasMedicationAPI] searchMedicationsSync() est obsolète, utilisez searchMedications() (async)');
  return [];
}

/**
 * Obtenir les médicaments populaires (non applicable avec l'API Giygas)
 * Retourne un tableau vide
 */
export function getPopularMedications(): MedicationSuggestion[] {
  console.warn('[GiygasMedicationAPI] getPopularMedications() n\'est plus supporté avec l\'API Giygas');
  return [];
}
