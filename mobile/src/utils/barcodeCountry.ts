/**
 * Détection du pays d'origine d'un code-barres EAN-13
 * Basé sur les préfixes GS1 standards
 */

export interface CountryInfo {
  code: string;
  name: string;
  flag: string;
  supported: boolean;
}

/**
 * Détecte le pays d'origine d'un code-barres EAN-13
 */
export function detectCountryByEAN(ean13: string): CountryInfo {
  if (!ean13 || ean13.length < 3) {
    return {
      code: 'UNKNOWN',
      name: 'Inconnu',
      flag: '🌍',
      supported: false,
    };
  }

  const prefix = parseInt(ean13.substring(0, 3), 10);

  // France : 30-37
  if (prefix >= 300 && prefix <= 379) {
    return {
      code: 'FR',
      name: 'France',
      flag: '🇫🇷',
      supported: true,
    };
  }

  // Italie : 80-83
  if (prefix >= 800 && prefix <= 839) {
    return {
      code: 'IT',
      name: 'Italie',
      flag: '🇮🇹',
      supported: false,
    };
  }

  // Belgique & Luxembourg : 54
  if (prefix >= 540 && prefix <= 549) {
    return {
      code: 'BE',
      name: 'Belgique',
      flag: '🇧🇪',
      supported: false,
    };
  }

  // Allemagne : 40-44
  if (prefix >= 400 && prefix <= 440) {
    return {
      code: 'DE',
      name: 'Allemagne',
      flag: '🇩🇪',
      supported: false,
    };
  }

  // Espagne : 84
  if (prefix >= 840 && prefix <= 849) {
    return {
      code: 'ES',
      name: 'Espagne',
      flag: '🇪🇸',
      supported: false,
    };
  }

  // Royaume-Uni : 50
  if (prefix >= 500 && prefix <= 509) {
    return {
      code: 'GB',
      name: 'Royaume-Uni',
      flag: '🇬🇧',
      supported: false,
    };
  }

  // Suisse & Liechtenstein : 76
  if (prefix >= 760 && prefix <= 769) {
    return {
      code: 'CH',
      name: 'Suisse',
      flag: '🇨🇭',
      supported: false,
    };
  }

  // Portugal : 560
  if (prefix >= 560 && prefix <= 569) {
    return {
      code: 'PT',
      name: 'Portugal',
      flag: '🇵🇹',
      supported: false,
    };
  }

  // Pays-Bas : 87
  if (prefix >= 870 && prefix <= 879) {
    return {
      code: 'NL',
      name: 'Pays-Bas',
      flag: '🇳🇱',
      supported: false,
    };
  }

  // Autriche : 90-91
  if (prefix >= 900 && prefix <= 919) {
    return {
      code: 'AT',
      name: 'Autriche',
      flag: '🇦🇹',
      supported: false,
    };
  }

  // USA & Canada : 00-13
  if (prefix >= 0 && prefix <= 139) {
    return {
      code: 'US',
      name: 'États-Unis/Canada',
      flag: '🇺🇸',
      supported: false,
    };
  }

  // Autre pays
  return {
    code: 'OTHER',
    name: 'International',
    flag: '🌍',
    supported: false,
  };
}

/**
 * Vérifie si un code-barres est un médicament français
 */
export function isFrenchMedication(ean13: string): boolean {
  const country = detectCountryByEAN(ean13);
  return country.code === 'FR';
}

/**
 * Génère un message d'erreur personnalisé pour un code non-français
 */
export function getUnsupportedCountryMessage(ean13: string): {
  title: string;
  message: string;
} {
  const country = detectCountryByEAN(ean13);

  if (country.code === 'UNKNOWN') {
    return {
      title: 'Code non reconnu',
      message: `Le code scanné (${ean13}) n'est pas reconnu comme un code-barres de médicament valide.\n\nVeuillez réessayer ou saisir le nom manuellement.`,
    };
  }

  return {
    title: `Médicament ${country.flag} ${country.name}`,
    message: `Le produit scanné provient de ${country.name}. Actuellement, seuls les médicaments français sont automatiquement reconnus.\n\n💡 Recherchez le nom du médicament dans la barre de recherche ci-dessus.`,
  };
}
