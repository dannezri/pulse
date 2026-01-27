import React from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { AlertCircle, RefreshCw } from 'lucide-react-native';

interface ErrorViewProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorView({ message, onRetry }: ErrorViewProps) {
  return (
    <View className="flex-1 items-center justify-center p-6">
      <View className="bg-[#1C1C1E] rounded-2xl p-8 items-center max-w-sm">
        <AlertCircle size={48} color="#FF453A" />
        <Text className="text-white text-lg font-semibold mt-4 text-center">
          Une erreur est survenue
        </Text>
        <Text className="text-gray-400 text-sm mt-2 text-center">
          {message}
        </Text>
        {onRetry && (
          <TouchableOpacity
            className="flex-row items-center bg-[#5E5CE6] py-3 px-6 rounded-lg mt-6"
            onPress={onRetry}
          >
            <RefreshCw size={16} color="#FFFFFF" />
            <Text className="text-white text-sm font-semibold ml-2">
              Réessayer
            </Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}
