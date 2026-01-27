const { withInfoPlist, withEntitlementsPlist } = require('@expo/config-plugins');

/**
 * Config plugin pour Pulse HealthKit
 * Ajoute les permissions et entitlements nécessaires pour HealthKit
 */
module.exports = function withPulseHealthkit(config, options = {}) {
  // Ajouter les descriptions d'utilisation dans Info.plist
  config = withInfoPlist(config, (config) => {
    // Les descriptions sont déjà dans app.json, mais on s'assure qu'elles sont présentes
    if (!config.modResults.NSHealthShareUsageDescription) {
      config.modResults.NSHealthShareUsageDescription = 
        options.healthShareUsageDescription || 
        'Pulse a besoin d\'accéder à vos données de santé pour générer des insights personnalisés sur votre bien-être.';
    }
    
    // Pour la lecture seule, on peut mettre une description minimale pour Update
    if (!config.modResults.NSHealthUpdateUsageDescription) {
      config.modResults.NSHealthUpdateUsageDescription = 
        options.healthUpdateUsageDescription || 
        'Pulse lit uniquement vos données de santé, aucune modification n\'est effectuée.';
    }
    
    return config;
  });

  // Ajouter la capability HealthKit dans les entitlements
  config = withEntitlementsPlist(config, (config) => {
    // Ajouter la capability HealthKit (lecture uniquement)
    if (!config.modResults['com.apple.developer.healthkit']) {
      config.modResults['com.apple.developer.healthkit'] = true;
    }
    
    // Ajouter l'accès HealthKit (lecture uniquement)
    if (!config.modResults['com.apple.developer.healthkit.access']) {
      config.modResults['com.apple.developer.healthkit.access'] = [];
    }
    
    // S'assurer que l'accès HealthKit est configuré
    const healthKitAccess = config.modResults['com.apple.developer.healthkit.access'];
    if (!Array.isArray(healthKitAccess)) {
      config.modResults['com.apple.developer.healthkit.access'] = [];
    }
    
    return config;
  });

  return config;
};
