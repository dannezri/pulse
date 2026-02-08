/**
 * Custom Time Picker pour iOS
 * Solution au bug du DateTimePicker qui ignore la prop value
 */

import React, { useState, useRef, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, Dimensions } from 'react-native';
import { PressableScale } from './PressableScale';

interface CustomTimePickerProps {
  initialHour: number;
  initialMinute: number;
  onConfirm: (hour: number, minute: number) => void;
  onCancel: () => void;
}

const ITEM_HEIGHT = 44;
const VISIBLE_ITEMS = 5;

export function CustomTimePicker({ initialHour, initialMinute, onConfirm, onCancel }: CustomTimePickerProps) {
  const [selectedHour, setSelectedHour] = useState(initialHour);
  const [selectedMinute, setSelectedMinute] = useState(initialMinute);
  
  const hourScrollRef = useRef<ScrollView>(null);
  const minuteScrollRef = useRef<ScrollView>(null);

  // Générer les tableaux d'heures (0-23) et minutes (0-59)
  const hours = Array.from({ length: 24 }, (_, i) => i);
  const minutes = Array.from({ length: 60 }, (_, i) => i);

  // Initialiser la position de scroll
  useEffect(() => {
    // Petit délai pour que le ScrollView soit monté
    setTimeout(() => {
      hourScrollRef.current?.scrollTo({
        y: initialHour * ITEM_HEIGHT,
        animated: false,
      });
      minuteScrollRef.current?.scrollTo({
        y: initialMinute * ITEM_HEIGHT,
        animated: false,
      });
    }, 100);
  }, [initialHour, initialMinute]);

  const handleHourScroll = (event: any) => {
    const offsetY = event.nativeEvent.contentOffset.y;
    const index = Math.round(offsetY / ITEM_HEIGHT);
    setSelectedHour(Math.max(0, Math.min(23, index)));
  };

  const handleMinuteScroll = (event: any) => {
    const offsetY = event.nativeEvent.contentOffset.y;
    const index = Math.round(offsetY / ITEM_HEIGHT);
    setSelectedMinute(Math.max(0, Math.min(59, index)));
  };

  const handleConfirm = () => {
    onConfirm(selectedHour, selectedMinute);
  };

  return (
    <View style={styles.container}>
      <View style={styles.pickerContainer}>
        {/* Overlay de sélection */}
        <View style={styles.selectionOverlay} pointerEvents="none">
          <View style={styles.selectionBar} />
        </View>

        {/* Heures */}
        <ScrollView
          ref={hourScrollRef}
          style={styles.scrollView}
          showsVerticalScrollIndicator={false}
          snapToInterval={ITEM_HEIGHT}
          decelerationRate="fast"
          onMomentumScrollEnd={handleHourScroll}
          contentContainerStyle={styles.scrollContent}
        >
          {/* Padding top */}
          <View style={{ height: ITEM_HEIGHT * 2 }} />
          
          {hours.map((hour) => (
            <View key={hour} style={styles.item}>
              <Text
                style={[
                  styles.itemText,
                  selectedHour === hour && styles.itemTextSelected,
                ]}
              >
                {hour.toString().padStart(2, '0')}
              </Text>
            </View>
          ))}
          
          {/* Padding bottom */}
          <View style={{ height: ITEM_HEIGHT * 2 }} />
        </ScrollView>

        <Text style={styles.separator}>:</Text>

        {/* Minutes */}
        <ScrollView
          ref={minuteScrollRef}
          style={styles.scrollView}
          showsVerticalScrollIndicator={false}
          snapToInterval={ITEM_HEIGHT}
          decelerationRate="fast"
          onMomentumScrollEnd={handleMinuteScroll}
          contentContainerStyle={styles.scrollContent}
        >
          {/* Padding top */}
          <View style={{ height: ITEM_HEIGHT * 2 }} />
          
          {minutes.map((minute) => (
            <View key={minute} style={styles.item}>
              <Text
                style={[
                  styles.itemText,
                  selectedMinute === minute && styles.itemTextSelected,
                ]}
              >
                {minute.toString().padStart(2, '0')}
              </Text>
            </View>
          ))}
          
          {/* Padding bottom */}
          <View style={{ height: ITEM_HEIGHT * 2 }} />
        </ScrollView>
      </View>

      {/* Bouton OK */}
      <PressableScale onPress={handleConfirm} style={styles.confirmButton}>
        <Text style={styles.confirmButtonText}>OK</Text>
      </PressableScale>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
  },
  pickerContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    height: ITEM_HEIGHT * VISIBLE_ITEMS,
    position: 'relative',
  },
  selectionOverlay: {
    position: 'absolute',
    top: ITEM_HEIGHT * 2,
    left: 0,
    right: 0,
    height: ITEM_HEIGHT,
    justifyContent: 'center',
    zIndex: 1,
  },
  selectionBar: {
    height: ITEM_HEIGHT,
    backgroundColor: 'rgba(94, 92, 230, 0.15)',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(94, 92, 230, 0.3)',
  },
  scrollView: {
    width: 80,
    height: ITEM_HEIGHT * VISIBLE_ITEMS,
  },
  scrollContent: {
    alignItems: 'center',
  },
  item: {
    height: ITEM_HEIGHT,
    justifyContent: 'center',
    alignItems: 'center',
  },
  itemText: {
    fontSize: 24,
    color: '#8E8E93',
    fontWeight: '400',
  },
  itemTextSelected: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  separator: {
    fontSize: 28,
    color: '#FFFFFF',
    fontWeight: '600',
    marginHorizontal: 10,
  },
  confirmButton: {
    marginTop: 20,
    backgroundColor: '#5E5CE6',
    paddingHorizontal: 40,
    paddingVertical: 12,
    borderRadius: 12,
    width: '100%',
    alignItems: 'center',
  },
  confirmButtonText: {
    color: '#FFFFFF',
    fontSize: 17,
    fontWeight: '600',
  },
});
