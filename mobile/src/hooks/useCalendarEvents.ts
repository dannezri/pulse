import { useQuery } from '@tanstack/react-query';
import { Platform } from 'react-native';

// Lazy import for expo-calendar (fails gracefully in Expo Go)
let Calendar: any = null;
try {
  Calendar = require('expo-calendar');
} catch (e) {
  console.warn('[useCalendarEvents] expo-calendar not available (requires Development Build)');
}

export interface CalendarEvent {
  id: string;
  title: string;
  startDate: Date;
  endDate: Date;
  location?: string;
  notes?: string;
  allDay?: boolean;
}

async function fetchTodayEvents(): Promise<CalendarEvent[]> {
  // Check if expo-calendar is available
  if (!Calendar) {
    console.warn('[useCalendarEvents] expo-calendar not available, returning empty events');
    return [];
  }

  // 1. Demander permissions
  const { status } = await Calendar.requestCalendarPermissionsAsync();
  if (status !== 'granted') {
    console.warn('[useCalendarEvents] Permission refusée');
    return [];
  }

  // 2. Récupérer les calendriers
  const calendars = await Calendar.getCalendarsAsync(Calendar.EntityTypes.EVENT);
  
  // 3. Filtrer les calendriers pertinents (éviter les calendriers de spam)
  const relevantCalendars = calendars.filter(cal => 
    cal.allowsModifications || cal.type === Calendar.CalendarType.LOCAL
  );

  if (relevantCalendars.length === 0) {
    console.warn('[useCalendarEvents] Aucun calendrier trouvé');
    return [];
  }

  // 4. Récupérer les événements d'aujourd'hui
  const today = new Date();
  const startOfDay = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 0, 0, 0);
  const endOfDay = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 23, 59, 59);

  const events = await Calendar.getEventsAsync(
    relevantCalendars.map(c => c.id),
    startOfDay,
    endOfDay
  );

  // 5. Transformer et trier par heure de début
  return events
    .map(e => ({
      id: e.id,
      title: e.title,
      startDate: new Date(e.startDate),
      endDate: new Date(e.endDate),
      location: e.location,
      notes: e.notes,
      allDay: e.allDay,
    }))
    .sort((a, b) => a.startDate.getTime() - b.startDate.getTime());
}

export function useCalendarEvents() {
  return useQuery({
    queryKey: ['calendarEvents'],
    queryFn: fetchTodayEvents,
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: false,
  });
}
