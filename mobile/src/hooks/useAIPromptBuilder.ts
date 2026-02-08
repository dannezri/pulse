import { useQuery } from '@tanstack/react-query';
import { supabase } from '../lib/supabase';
import { CalendarEvent } from './useCalendarEvents';
import { DailyContextRow, getDetailsDescription } from '../types/dailyContext';

interface AIPromptData {
  systemInstructions: string;
  eventInfo: string;
  biometricData: string;
  contextData: string;
  fullPrompt: string;
}

async function buildAIPrompt(
  userId: string | null, 
  event: CalendarEvent, 
  readinessScore: number | null
): Promise<AIPromptData> {
  if (!userId) {
    return {
      systemInstructions: '',
      eventInfo: '',
      biometricData: '',
      contextData: '',
      fullPrompt: 'Erreur: utilisateur non connecté',
    };
  }

  // Section 1: Consignes Système
  const systemInstructions = `Tu es Pulse, un expert en bio-hacking et un assistant de performance biologique. Ton rôle est d'analyser les données biométriques de l'utilisateur (HRV, Sommeil, RHR) et de les croiser avec son agenda et son contexte de vie (repas, symptômes) pour lui donner une feuille de route pédagogique.

TES RÈGLES D'ANALYSE :
• La Corrélation est Reine : Ne te contente pas de dire 'ton HRV est bas'. Cherche la cause dans le contexte. (Ex: 'Ton HRV est bas parce que ton dîner de 21h30 était riche en glucides, ce qui a maintenu ton métabolisme actif cette nuit').

• Pédagogie Scientifique : Explique brièvement le 'Pourquoi'. Si le système nerveux est fatigué, explique l'impact sur la prise de décision ou la force physique.

• Arbitrage d'Agenda : Pour l'événement spécifié, donne un avis tranché :
  - GO : Tu es au top, fonce.
  - VIGILANCE : Fais-le, mais avec une stratégie d'économie (ex: moins de caféine, plus de pauses).
  - PIVOT : Ton corps n'est pas prêt. Si c'est du sport, recommande de la marche. Si c'est une réunion, recommande des outils de focus.

STRUCTURE DE TA RÉPONSE (Strictement pédagogique) :

1. Diagnostic Flash : Un verdict en une phrase sur l'état actuel vs l'événement.

2. Le "Pourquoi" (Lien de Cause à Effet) : Analyse le lien entre les dernières 24h (repas/sommeil) et le score de Readiness.

3. Protocole de Préparation (Le "Comment") :
   - Action Immédiate : (ex: exposition à la lumière, respiration, hydratation spécifique).
   - Stratégie pendant l'événement : (ex: gestion de l'énergie, posture).
   - Récupération prévue : (ex: ce qu'il faut faire ce soir pour réparer les dégâts).

TON TON :
Direct, expert, mais très humain. Tu es le coach qui connaît les secrets de sa biologie.`;

  // Section 2: Événement
  const eventInfo = `Événement: ${event.title}
Heure: ${event.startDate.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })} - ${event.endDate.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
Lieu: ${event.location || 'Non spécifié'}
${event.notes ? `Notes: ${event.notes}` : ''}`;

  // Section 3: État Biologique (Dernières 24h via RPC)
  const { data: biometrics } = await supabase
    .rpc('get_recent_biometrics', { 
      p_user_id: userId, 
      p_limit: 50 
    });

  let biometricData = 'Données biométriques (dernières 24h):\n';
  
  if (!biometrics || biometrics.length === 0) {
    biometricData += 'Aucune donnée disponible';
  } else {
    // Regrouper par type de métrique
    const grouped = biometrics.reduce((acc: any, b: any) => {
      if (!acc[b.metric_type]) acc[b.metric_type] = [];
      acc[b.metric_type].push(b);
      return acc;
    }, {});

    // HRV
    const hrvData = grouped['hrv']?.[0];
    if (hrvData) {
      biometricData += `HRV: ${Math.round(hrvData.value)} ms\n`;
    }

    // Heart Rate
    const hrData = grouped['heart_rate']?.[0];
    if (hrData) {
      biometricData += `Rythme Cardiaque Repos: ${Math.round(hrData.value)} bpm\n`;
    }

    // Sleep
    const sleepData = grouped['sleep_duration']?.[0] || grouped['sleep']?.[0];
    if (sleepData) {
      const hours = Math.floor(sleepData.value / 60);
      const minutes = Math.round(sleepData.value % 60);
      biometricData += `Sommeil: ${hours}h${minutes.toString().padStart(2, '0')}\n`;
    }

    // Readiness Score
    if (readinessScore !== null) {
      biometricData += `Score de Readiness: ${readinessScore}%\n`;
    }
  }

  // Section 4: Contexte Quotidien (Nutrition, Symptômes) avec typage robuste
  const { data: dailyContext } = await supabase
    .rpc('get_recent_daily_context', { 
      p_user_id: userId, 
      p_limit: 10 
    });

  let contextData = 'Contexte récent:\n';
  
  if (!dailyContext || dailyContext.length === 0) {
    contextData += 'Aucune donnée de contexte';
  } else {
    (dailyContext as DailyContextRow[]).forEach((ctx) => {
      const time = new Date(ctx.logged_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
      const description = getDetailsDescription(ctx.details);
      
      if (ctx.category === 'nutrition') {
        contextData += `[${time}] Repas: ${description}\n`;
      } else if (ctx.category === 'symptoms') {
        contextData += `[${time}] Symptôme: ${description}\n`;
      } else if (ctx.category === 'medication') {
        contextData += `[${time}] Médicament: ${description}\n`;
      } else {
        contextData += `[${time}] ${ctx.category}: ${description}\n`;
      }
    });
  }

  // Combiner tout
  const fullPrompt = `${systemInstructions}

---

${eventInfo}

---

${biometricData}

---

${contextData}`;

  return {
    systemInstructions,
    eventInfo,
    biometricData,
    contextData,
    fullPrompt,
  };
}

export function useAIPromptBuilder(
  userId: string | null, 
  event: CalendarEvent | null, 
  readinessScore: number | null
) {
  return useQuery({
    queryKey: ['aiPrompt', userId, event?.id, readinessScore],
    queryFn: () => buildAIPrompt(userId, event!, readinessScore),
    enabled: !!userId && !!event,
  });
}
