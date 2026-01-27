import { View, Text, StyleSheet } from "react-native";
import { Sparkles } from "lucide-react-native";
import { Insight } from "../types/database";

interface InsightCardProps {
  insight: Insight;
  isLatest?: boolean;
}

export function InsightCard({ insight, isLatest = false }: InsightCardProps) {
  const getCategoryEmoji = () => {
    switch (insight.category) {
      case "movement":
        return "🏃";
      case "nutrition":
        return "🍎";
      case "recovery":
        return "💤";
      case "stress":
        return "🧘";
      default:
        return "💡";
    }
  };

  const borderColor =
    insight.priority === 2
      ? "#FF3B30" // Urgent
      : insight.category === "stress"
      ? "#FFD60A" // Stress
      : "#34C759"; // Default/Recovery

  return (
    <View
      style={[
        styles.container,
        {
          borderLeftColor: borderColor,
          shadowColor: borderColor,
          shadowOffset: { width: 0, height: 4 },
          shadowOpacity: 0.1,
          shadowRadius: 8,
        },
      ]}
    >
      {isLatest && (
        <View style={styles.newBadge}>
          <Sparkles size={12} color="#34C759" />
          <Text style={styles.newBadgeText}>NOUVEAU</Text>
        </View>
      )}
      <View style={styles.content}>
        <View style={styles.emojiContainer}>
          <Text style={styles.emoji}>{getCategoryEmoji()}</Text>
        </View>
        <View style={styles.textContainer}>
          <Text style={styles.text}>{insight.content}</Text>
          {insight.category && (
            <View style={styles.categoryBadgeContainer}>
              <View
                style={[
                  styles.categoryBadge,
                  { backgroundColor: `${borderColor}15` },
                ]}
              >
                <Text style={[styles.categoryText, { color: borderColor }]}>
                  {insight.category}
                </Text>
              </View>
            </View>
          )}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#1C1C1E",
    borderRadius: 20,
    padding: 20,
    marginBottom: 12,
    borderLeftWidth: 4,
  },
  newBadge: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#2C2C2E",
    alignSelf: "flex-start",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginBottom: 12,
    gap: 4,
  },
  newBadgeText: {
    color: "#34C759",
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
  content: {
    flexDirection: "row",
    alignItems: "flex-start",
  },
  emojiContainer: {
    backgroundColor: "#2C2C2E",
    borderRadius: 20,
    padding: 8,
    marginRight: 12,
  },
  emoji: {
    fontSize: 20,
  },
  textContainer: {
    flex: 1,
  },
  text: {
    color: "#FFFFFF",
    fontSize: 15,
    lineHeight: 22,
    fontWeight: "500",
  },
  categoryBadgeContainer: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 8,
  },
  categoryBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  categoryText: {
    fontSize: 11,
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
});
