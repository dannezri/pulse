import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Calendar, MapPin } from 'lucide-react-native';
import { CalendarEvent } from '../hooks/useCalendarEvents';

interface Props {
  event: CalendarEvent;
  onPress: () => void;
}

export function CalendarEventCard({ event, onPress }: Props) {
  const startTime = event.startDate.toLocaleTimeString('fr-FR', { 
    hour: '2-digit', 
    minute: '2-digit' 
  });
  const endTime = event.endDate.toLocaleTimeString('fr-FR', { 
    hour: '2-digit', 
    minute: '2-digit' 
  });

  return (
    <TouchableOpacity style={styles.container} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.timeContainer}>
        <Text style={styles.time}>{startTime}</Text>
        <Text style={styles.timeSeparator}>-</Text>
        <Text style={styles.time}>{endTime}</Text>
      </View>

      <View style={styles.content}>
        <View style={styles.header}>
          <Calendar size={16} color="#8E8E93" />
          <Text style={styles.title} numberOfLines={2}>
            {event.title}
          </Text>
        </View>

        {event.location && (
          <View style={styles.locationContainer}>
            <MapPin size={14} color="#8E8E93" />
            <Text style={styles.location} numberOfLines={1}>
              {event.location}
            </Text>
          </View>
        )}
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
  },
  timeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 16,
    minWidth: 80,
  },
  time: {
    fontSize: 14,
    color: '#FFFFFF',
    fontWeight: '600',
  },
  timeSeparator: {
    fontSize: 14,
    color: '#8E8E93',
    marginHorizontal: 4,
  },
  content: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  title: {
    fontSize: 15,
    color: '#FFFFFF',
    fontWeight: '600',
    marginLeft: 8,
    flex: 1,
  },
  locationContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  location: {
    fontSize: 13,
    color: '#8E8E93',
    marginLeft: 6,
    flex: 1,
  },
});
