/**
 * Templates de génération de texte pour les cartes Brief
 * 
 * Approche hybride: templates locaux pour les cartes standard,
 * backend IA pour les insights complexes.
 */

import { BriefCard } from '../types/brief';
import { PulseScoreResult } from '../types/brief';

/**
 * Carte 1: Le Verdict (Score + Message d'accueil)
 * Badge principal = Pulse Score (pas Oura!)
 * Messages biologiquement pertinents et actionnables
 */
export function generateVerdictCard(
  firstName: string,
  pulseResult: PulseScoreResult,
  readinessScore: number | null,
  timingScore: number,
  date?: string
): BriefCard {
  let title = '';
  let content = '';
  let actionLabel = undefined;
  
  const { score, state, weakestMetric } = pulseResult;
  
  // Génération du header avec date et prénom
  const today = date || new Date().toLocaleDateString('fr-FR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  });
  const headerText = `${today} • Bonjour ${firstName}`;
  
  if (state === 'optimal') {
    title = `Système Optimal`;
    content = `Vos métriques sont alignées. Votre corps est prêt pour les défis.`;
    actionLabel = 'Planifier objectif';
  } else if (state === 'warning') {
    title = 'Vigilance Requise';
    if (readinessScore && readinessScore > score + 10) {
      content = `Oura dit ${readinessScore}%, Pulse détecte ${score}%. Votre ${weakestMetric.name.toLowerCase()} masque une fragilité réelle.`;
    } else {
      content = `${score}%. Votre ${weakestMetric.name.toLowerCase()} nécessite attention. Adaptez l'intensité aujourd'hui.`;
    }
    actionLabel = 'Voir détails';
  } else {
    // Score < 60
    title = 'Alerte Surmenage';
    content = 'Votre corps simule la forme, mais votre cœur lutte. Repos prioritaire.';
    actionLabel = 'Reposez-vous';
  }
  
  return {
    id: 'verdict',
    type: 'verdict',
    title,
    content,
    state,
    iconName: 'Activity',
    badge: score,
    priority: 100,
    headerText,
    actionButton: actionLabel ? { label: actionLabel, onPress: () => {} } : undefined,
  };
}

/**
 * Carte 2: Alerte Critique (conditionnelle si métrique < 40)
 * Messages biologiquement sensés et actionnables
 */
export function generateCriticalAlert(
  metric: string,
  value: number,
  threshold: number = 40
): BriefCard | null {
  if (value >= threshold) return null;
  
  const metricNames: Record<string, { display: string; icon: string; warning: string; action: string }> = {
    'Timing': {
      display: 'Décalage Circadien',
      icon: 'Clock',
      warning: `Décalage horaire social détecté (Score: ${value}). Votre cortisol est déréglé.`,
      action: 'Ajuster horaires'
    },
    'Sommeil Profond': {
      display: 'Sommeil Profond Critique',
      icon: 'Moon',
      warning: `Récupération musculaire insuffisante. Votre système nerveux n'a pas régénéré.`,
      action: 'Sommeil réparateur'
    },
    'HRV': {
      display: 'Stress Nerveux',
      icon: 'HeartPulse',
      warning: 'Votre système nerveux autonome est en déséquilibre. Évitez les efforts intenses.',
      action: 'Respiration guidée'
    },
    'Repos Cardiaque': {
      display: 'Alerte Cardiaque',
      icon: 'Heart',
      warning: 'Fréquence cardiaque au repos élevée. Votre cœur compense un déficit de récupération.',
      action: 'Repos actif'
    }
  };
  
  const metricInfo = metricNames[metric] || {
    display: metric,
    icon: 'AlertTriangle',
    warning: 'Cette métrique nécessite votre attention immédiate.',
    action: 'Consulter'
  };
  
  return {
    id: `critical-${metric.toLowerCase()}`,
    type: 'critical',
    title: metricInfo.display,
    content: metricInfo.warning,
    state: 'alert',
    iconName: metricInfo.icon,
    badge: value,
    priority: 90,
    actionButton: { label: metricInfo.action, onPress: () => {} },
  };
}

/**
 * Carte 3: Focus Biologique (analyse du point faible)
 */
export function generateBiologicalFocus(
  weakestMetric: { name: string; value: number; impact: number },
  baseline: number | null,
  nextEvent?: { title: string; startDate: Date }
): BriefCard {
  const { name, value, impact } = weakestMetric;
  
  let content = `Votre ${name.toLowerCase()} est à ${value}/100`;
  
  if (baseline) {
    const diff = Math.round(((value - baseline) / baseline) * 100);
    if (diff < 0) {
      content += `, soit ${Math.abs(diff)}% sous votre moyenne`;
    }
  }
  
  content += `. Impact estimé: ${impact}% sur vos performances.`;
  
  if (nextEvent && name === 'Sommeil Profond') {
    content += ` Attention aux articulations lors de votre ${nextEvent.title}.`;
  } else if (nextEvent && name === 'Timing') {
    content += ` Vigilance réduite pour votre ${nextEvent.title}.`;
  }
  
  return {
    id: 'focus',
    type: 'focus',
    title: `Point de Vigilance: ${name}`,
    content,
    state: value < 40 ? 'alert' : value < 60 ? 'warning' : 'optimal',
    iconName: name.includes('Sommeil') ? 'Moon' : name.includes('Timing') ? 'Clock' : 'Activity',
    badge: value,
    priority: 80,
  };
}

/**
 * Carte 4: Anticipateur d'Agenda (corrélation état/événements)
 * Format simple sans puces: "Prochain: Alexandre CADRAN (11:45)"
 */
export function generateAgendaAnticipator(
  events: Array<{ title: string; startDate: Date; location?: string }>,
  pulseScore: number,
  deepSleepScore: number,
  timingScore: number
): BriefCard | null {
  if (events.length === 0) return null;
  
  const nextEvent = events[0];
  const time = nextEvent.startDate.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  
  let content = `Prochain: ${nextEvent.title} (${time})`;
  let warning = '';
  let actionLabel = 'Voir calendrier';
  
  // Analyse contextuelle basée sur le type d'événement et l'état
  if (nextEvent.title.toLowerCase().includes('sport') || nextEvent.title.toLowerCase().includes('padel') || nextEvent.title.toLowerCase().includes('gym')) {
    if (deepSleepScore < 50) {
      warning = 'Récupération musculaire insuffisante. Risque de blessure accru.';
      actionLabel = 'Échauffement long';
    } else if (pulseScore > 75) {
      warning = 'Condition optimale. Performance maximale possible.';
      actionLabel = 'Objectif perso';
    }
  } else if (nextEvent.title.toLowerCase().includes('réunion') || nextEvent.title.toLowerCase().includes('meeting')) {
    if (timingScore < 40) {
      warning = 'Vigilance réduite. Concentration difficile.';
      actionLabel = 'Café + notes';
    } else if (pulseScore > 75) {
      warning = 'Focus optimal. Moment idéal pour décisions importantes.';
      actionLabel = 'Préparer arguments';
    }
  }
  
  if (warning) {
    content += `\n\n${warning}`;
  }
  
  return {
    id: 'agenda',
    type: 'agenda',
    title: 'Prochain Événement',
    content: content.trim(),
    state: pulseScore < 60 ? 'warning' : 'optimal',
    iconName: 'Calendar',
    priority: 70,
    actionButton: { label: actionLabel, onPress: () => {} },
  };
}

/**
 * Carte 5: Rapport d'Activité (synthèse mouvement)
 * Messages biologiquement pertinents: "Inactivité sévère" si < 2000 pas
 */
export function generateActivityReport(
  steps: number | null,
  sedentaryMinutes: number | null,
  calories: number | null,
  goal: number = 10000
): BriefCard {
  const stepsValue = steps || 0;
  const progress = Math.round((stepsValue / goal) * 100);
  
  let title = 'Mouvement';
  let content = '';
  let state: 'optimal' | 'warning' | 'alert' | 'neutral' = 'optimal';
  let actionLabel = 'Voir stats';
  
  if (stepsValue < 2000) {
    // Inactivité sévère
    state = 'alert';
    title = 'Inactivité Sévère';
    content = `${stepsValue.toLocaleString()} pas. Votre métabolisme est en veille. Risque cardiovasculaire accru.`;
    actionLabel = 'Marchez 10 min';
  } else if (progress < 50) {
    state = 'warning';
    title = 'Mouvement Insuffisant';
    content = `${stepsValue.toLocaleString()} pas (${progress}% de l'objectif). Bougez toutes les 2h pour maintenir la circulation.`;
    actionLabel = 'Objectif 5000';
  } else if (progress >= 100) {
    state = 'optimal';
    title = 'Objectif Atteint';
    content = `${stepsValue.toLocaleString()} pas. Excellent! Votre système cardiovasculaire est stimulé.`;
    actionLabel = 'Nouveau record';
  } else {
    content = `${stepsValue.toLocaleString()} pas (${progress}%). En bonne voie vers l'objectif.`;
    actionLabel = 'Continuer';
  }
  
  return {
    id: 'activity',
    type: 'activity',
    title,
    content,
    state,
    iconName: 'TrendingUp',
    badge: progress,
    priority: 60,
    actionButton: { label: actionLabel, onPress: () => {} },
  };
}

/**
 * Carte Empty State: État de synchronisation
 */
export function generateEmptyState(hasConnections: boolean, onConnectPress?: () => void): BriefCard {
  let title = 'Synchronisation en cours...';
  let content = 'Pulse collecte vos premières données de santé. Cela peut prendre quelques minutes.';
  let actionButton = undefined;
  
  if (!hasConnections) {
    title = 'Aucune source connectée';
    content = 'Connectez Oura, Apple Health ou un autre appareil pour commencer à recevoir votre Brief quotidien personnalisé.';
    
    if (onConnectPress) {
      actionButton = {
        label: 'Connecter une source',
        onPress: onConnectPress
      };
    }
  }
  
  return {
    id: 'empty',
    type: 'empty',
    title,
    content,
    state: 'neutral',
    iconName: 'RefreshCw',
    priority: 0,
    actionButton,
  };
}
