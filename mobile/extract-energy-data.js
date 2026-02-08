#!/usr/bin/env node
/**
 * Script d'extraction des données de la page Énergie
 * 
 * Usage:
 *   node extract-energy-data.js <user-uuid> [--force]
 * 
 * Ou via variable d'environnement:
 *   export DEV_USER_UUID=votre-uuid
 *   node extract-energy-data.js [--force]
 */

const fetch = require('node-fetch');

// Configuration
// L'UUID par défaut doit être passé en argument ou via variable d'environnement
const DEFAULT_USER_ID = process.env.DEV_USER_UUID || null;
const API_BASE_URL = process.env.API_URL || 'http://localhost:9000';

/**
 * Extrait toutes les données de la page Énergie
 */
async function extractEnergyData(userId, forceRefresh = false) {
  console.log('┌─────────────────────────────────────────────────┐');
  console.log('│  📊 EXTRACTION DONNÉES PAGE ÉNERGIE - PULSE    │');
  console.log('└─────────────────────────────────────────────────┘\n');
  
  console.log(`🆔 User ID: ${userId}`);
  console.log(`🌐 API URL: ${API_BASE_URL}`);
  console.log(`🔄 Force Refresh: ${forceRefresh ? 'OUI' : 'NON'}\n`);

  try {
    // 1. Appel à l'API generate-brief
    console.log('📡 Appel de l\'API /api/v1/generate-brief...');
    const response = await fetch(`${API_BASE_URL}/api/v1/generate-brief`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        force_refresh: forceRefresh,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Erreur API ${response.status}: ${errorText}`);
    }

    const data = await response.json();
    console.log('✅ Données reçues avec succès!\n');

    // 2. Extraction des données pertinentes pour la page Énergie
    const energyData = extractEnergyPageData(data);

    // 3. Affichage détaillé
    displayEnergyData(energyData);

    // 4. Sauvegarde dans un fichier JSON
    const fs = require('fs');
    const outputFile = `energy-data-${userId}-${new Date().toISOString().split('T')[0]}.json`;
    fs.writeFileSync(outputFile, JSON.stringify(energyData, null, 2), 'utf-8');
    console.log(`\n💾 Données sauvegardées dans: ${outputFile}`);

    return energyData;
  } catch (error) {
    console.error('❌ Erreur lors de l\'extraction:', error.message);
    process.exit(1);
  }
}

/**
 * Extrait les données spécifiques à la page Énergie
 */
function extractEnergyPageData(briefData) {
  const forecast = briefData.intraday_energy_forecast || {};
  
  return {
    // Métadonnées générales
    metadata: {
      user_id: briefData.user_id,
      analyzed_at: briefData.analyzed_at,
      cached: briefData.cached,
      pulse_score: briefData.pulseScore,
    },

    // Données de forecast d'énergie
    energy_forecast: {
      type: forecast.type,
      model_version: forecast.model_version,
      generated_at: forecast.generated_at,
      forecast_date: forecast.date,
      timezone: forecast.timezone,
      confidence: forecast.confidence,
      
      // Énergie actuelle
      current_energy: getCurrentEnergy(forecast),
      
      // Courbe prédictive
      forecast_curve: forecast.points || [],
      total_points: (forecast.points || []).length,
      
      // Fenêtres temporelles
      windows: forecast.windows || [],
      
      // Événements prédits
      events: forecast.events || [],
      
      // Influenceurs (facteurs d'impact)
      influencers: forecast.influencers || [],
      positive_influencers: (forecast.influencers || []).filter(i => i.status === 'positive'),
      negative_influencers: (forecast.influencers || []).filter(i => i.status === 'negative'),
      
      // Notes explicatives
      notes: forecast.notes || [],
    },

    // Statistiques calculées
    statistics: calculateStatistics(forecast),

    // Cartes Brief (contexte additionnel)
    brief_cards: briefData.cards || [],
  };
}

/**
 * Récupère l'énergie actuelle
 */
function getCurrentEnergy(forecast) {
  if (forecast.current_energy !== undefined) {
    return forecast.current_energy;
  }
  
  // Fallback: prendre le premier point
  if (forecast.points && forecast.points.length > 0) {
    return forecast.points[0].energy;
  }
  
  return null;
}

/**
 * Calcule les statistiques de la page énergie
 */
function calculateStatistics(forecast) {
  const points = forecast.points || [];
  const influencers = forecast.influencers || [];
  
  // Calcul des impacts
  const positiveInfluencers = influencers.filter(i => i.status === 'positive');
  const negativeInfluencers = influencers.filter(i => i.status === 'negative');
  
  const totalPositiveImpact = positiveInfluencers.reduce((sum, inf) => {
    const impact = parseFloat(inf.impact?.replace('%', '') || '0');
    return sum + Math.abs(impact);
  }, 0);
  
  const totalNegativeImpact = negativeInfluencers.reduce((sum, inf) => {
    const impact = parseFloat(inf.impact?.replace('%', '') || '0');
    return sum + Math.abs(impact);
  }, 0);
  
  // Statistiques de la courbe
  const energyValues = points.map(p => p.energy || 0).filter(e => e > 0);
  
  return {
    // Balance énergétique
    total_positive_impact: totalPositiveImpact,
    total_negative_impact: totalNegativeImpact,
    net_balance: totalPositiveImpact - totalNegativeImpact,
    positive_factors_count: positiveInfluencers.length,
    negative_factors_count: negativeInfluencers.length,
    
    // Statistiques de courbe
    min_energy: energyValues.length > 0 ? Math.min(...energyValues) : null,
    max_energy: energyValues.length > 0 ? Math.max(...energyValues) : null,
    avg_energy: energyValues.length > 0 
      ? energyValues.reduce((a, b) => a + b, 0) / energyValues.length 
      : null,
    
    // Plage horaire
    time_range: points.length > 0 ? {
      start: points[0].t,
      end: points[points.length - 1].t,
    } : null,
  };
}

/**
 * Affiche les données de manière formatée
 */
function displayEnergyData(data) {
  console.log('═══════════════════════════════════════════════════');
  console.log('  📊 DONNÉES COMPLÈTES PAGE ÉNERGIE');
  console.log('═══════════════════════════════════════════════════\n');

  // 1. Métadonnées
  console.log('📋 MÉTADONNÉES');
  console.log('─'.repeat(50));
  console.log(`User ID         : ${data.metadata.user_id}`);
  console.log(`Analysé le      : ${data.metadata.analyzed_at}`);
  console.log(`Depuis cache    : ${data.metadata.cached ? 'OUI' : 'NON'}`);
  console.log(`Pulse Score     : ${data.metadata.pulse_score}%`);
  console.log('');

  // 2. Forecast d'énergie
  const forecast = data.energy_forecast;
  console.log('⚡ FORECAST D\'ÉNERGIE');
  console.log('─'.repeat(50));
  console.log(`Type            : ${forecast.type || 'N/A'}`);
  console.log(`Version modèle  : ${forecast.model_version || 'N/A'}`);
  console.log(`Généré le       : ${forecast.generated_at || 'N/A'}`);
  console.log(`Date forecast   : ${forecast.forecast_date || 'N/A'}`);
  console.log(`Timezone        : ${forecast.timezone || 'N/A'}`);
  console.log(`Confiance       : ${forecast.confidence ? (forecast.confidence * 100).toFixed(1) + '%' : 'N/A'}`);
  console.log('');

  // 3. Énergie actuelle
  console.log('🎯 ÉNERGIE ACTUELLE');
  console.log('─'.repeat(50));
  const currentEnergy = forecast.current_energy;
  if (currentEnergy !== null) {
    console.log(`Score           : ${Math.round(currentEnergy)}%`);
    console.log(`État            : ${getEnergyState(currentEnergy)}`);
    console.log(`Label           : ${getEnergyLabel(currentEnergy)}`);
  } else {
    console.log('❌ Aucune donnée d\'énergie actuelle');
  }
  console.log('');

  // 4. Courbe prédictive
  console.log('📈 COURBE PRÉDICTIVE');
  console.log('─'.repeat(50));
  console.log(`Points totaux   : ${forecast.total_points}`);
  if (data.statistics.time_range) {
    console.log(`Plage horaire   : ${formatTime(data.statistics.time_range.start)} → ${formatTime(data.statistics.time_range.end)}`);
  }
  if (forecast.forecast_curve.length > 0) {
    console.log(`\nPremiers points:`);
    forecast.forecast_curve.slice(0, 5).forEach(point => {
      console.log(`  ${formatTime(point.t)} : ${Math.round(point.energy || 0)}%`);
    });
    if (forecast.forecast_curve.length > 5) {
      console.log(`  ... et ${forecast.forecast_curve.length - 5} autres points`);
    }
  }
  console.log('');

  // 5. Statistiques de courbe
  const stats = data.statistics;
  console.log('📊 STATISTIQUES');
  console.log('─'.repeat(50));
  console.log(`Énergie min     : ${stats.min_energy !== null ? Math.round(stats.min_energy) + '%' : 'N/A'}`);
  console.log(`Énergie max     : ${stats.max_energy !== null ? Math.round(stats.max_energy) + '%' : 'N/A'}`);
  console.log(`Énergie moy     : ${stats.avg_energy !== null ? Math.round(stats.avg_energy) + '%' : 'N/A'}`);
  console.log('');

  // 6. Balance énergétique
  console.log('⚖️  BALANCE ÉNERGÉTIQUE');
  console.log('─'.repeat(50));
  console.log(`Facteurs +      : ${stats.positive_factors_count} (total: +${stats.total_positive_impact.toFixed(1)}%)`);
  console.log(`Facteurs -      : ${stats.negative_factors_count} (total: -${stats.total_negative_impact.toFixed(1)}%)`);
  console.log(`Balance nette   : ${stats.net_balance >= 0 ? '+' : ''}${stats.net_balance.toFixed(1)}%`);
  console.log('');

  // 7. Influenceurs positifs
  if (forecast.positive_influencers.length > 0) {
    console.log('✅ FACTEURS POSITIFS');
    console.log('─'.repeat(50));
    forecast.positive_influencers.forEach(inf => {
      console.log(`  ${inf.name || inf.type}`);
      console.log(`    Type   : ${inf.type || 'N/A'}`);
      console.log(`    Code   : ${inf.code || 'N/A'}`);
      console.log(`    Impact : ${inf.impact || 'N/A'}`);
      console.log('');
    });
  }

  // 8. Influenceurs négatifs
  if (forecast.negative_influencers.length > 0) {
    console.log('❌ FACTEURS NÉGATIFS');
    console.log('─'.repeat(50));
    forecast.negative_influencers.forEach(inf => {
      console.log(`  ${inf.name || inf.type}`);
      console.log(`    Type   : ${inf.type || 'N/A'}`);
      console.log(`    Code   : ${inf.code || 'N/A'}`);
      console.log(`    Impact : ${inf.impact || 'N/A'}`);
      console.log('');
    });
  }

  // 9. Notes explicatives
  if (forecast.notes.length > 0) {
    console.log('📝 NOTES EXPLICATIVES');
    console.log('─'.repeat(50));
    forecast.notes.forEach((note, index) => {
      console.log(`  ${index + 1}. ${note}`);
    });
    console.log('');
  }

  // 10. Fenêtres temporelles
  if (forecast.windows.length > 0) {
    console.log('🕐 FENÊTRES TEMPORELLES');
    console.log('─'.repeat(50));
    forecast.windows.forEach(window => {
      console.log(`  ${window.label || window.kind}`);
      console.log(`    ${formatTime(window.from)} → ${formatTime(window.to)}`);
      console.log('');
    });
  }

  // 11. Événements prédits
  if (forecast.events.length > 0) {
    console.log('📅 ÉVÉNEMENTS PRÉDITS');
    console.log('─'.repeat(50));
    forecast.events.forEach(event => {
      console.log(`  ${event.title}`);
      console.log(`    Début      : ${formatTime(event.start)}`);
      console.log(`    Fin        : ${formatTime(event.end)}`);
      console.log(`    Impact     : ${event.impact}%`);
      console.log(`    Confiance  : ${(event.confidence * 100).toFixed(1)}%`);
      console.log(`    Tags       : ${event.tags.join(', ')}`);
      console.log('');
    });
  }

  // 12. Diagnostic
  console.log('🔍 DIAGNOSTIC');
  console.log('─'.repeat(50));
  
  // Problèmes détectés
  const issues = [];
  if (forecast.influencers.length === 0) {
    issues.push('❌ CRITIQUE: Aucun influenceur détecté (tableau vide)');
  }
  if (forecast.total_points === 0) {
    issues.push('⚠️  Aucun point de courbe prédictive');
  }
  if (forecast.notes.length === 0) {
    issues.push('⚠️  Aucune note explicative');
  }
  if (!data.statistics.time_range) {
    issues.push('⚠️  Plage horaire non définie');
  }
  if (forecast.confidence && forecast.confidence < 0.5) {
    issues.push(`⚠️  Confiance faible (${(forecast.confidence * 100).toFixed(1)}%)`);
  }
  
  if (issues.length > 0) {
    console.log('Problèmes détectés:');
    issues.forEach(issue => console.log(`  ${issue}`));
  } else {
    console.log('✅ Toutes les données essentielles sont présentes');
  }
  console.log('');

  console.log('═══════════════════════════════════════════════════\n');
}

/**
 * Détermine l'état d'énergie
 */
function getEnergyState(energy) {
  if (energy < 20) return '🔴';
  if (energy < 40) return '🟠';
  if (energy < 60) return '🟡';
  if (energy < 80) return '🟢';
  return '🟢🟢';
}

/**
 * Retourne le label d'énergie
 */
function getEnergyLabel(energy) {
  if (energy < 20) return 'Repos nécessaire';
  if (energy < 40) return 'Énergie basse';
  if (energy < 60) return 'Énergie modérée';
  if (energy < 80) return 'Bonne énergie';
  return 'Énergie excellente';
}

/**
 * Formate un timestamp ISO en format lisible
 */
function formatTime(isoString) {
  if (!isoString) return 'N/A';
  const date = new Date(isoString);
  return date.toLocaleString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit',
    day: '2-digit',
    month: '2-digit',
  });
}

// Point d'entrée
if (require.main === module) {
  const args = process.argv.slice(2);
  const userId = args[0] || DEFAULT_USER_ID;
  const forceRefresh = args.includes('--force');
  
  // Vérifier que l'UUID est fourni
  if (!userId) {
    console.error('❌ Erreur: UUID utilisateur requis');
    console.error('');
    console.error('Usage:');
    console.error('  node extract-energy-data.js <user-uuid> [--force]');
    console.error('');
    console.error('Ou définir la variable d\'environnement:');
    console.error('  export DEV_USER_UUID=votre-uuid');
    console.error('  node extract-energy-data.js [--force]');
    process.exit(1);
  }
  
  extractEnergyData(userId, forceRefresh)
    .then(() => {
      console.log('✅ Extraction terminée avec succès');
      process.exit(0);
    })
    .catch(error => {
      console.error('❌ Erreur fatale:', error);
      process.exit(1);
    });
}

module.exports = { extractEnergyData, extractEnergyPageData };
