import { View, Text, StyleSheet } from "react-native";
import { ArrowUp, ArrowDown, Minus, TrendingUp } from "lucide-react-native";

interface MetricCardProps {
  title: string;
  value: string | number | null;
  subtitle?: string;
  trend?: "up" | "down" | "stable" | null;
  icon?: React.ReactNode;
  color?: string;
}

export function MetricCard({
  title,
  value,
  subtitle,
  trend,
  icon,
  color = "#34C759",
}: MetricCardProps) {
  const getTrendIcon = () => {
    if (trend === "up") return <ArrowUp size={14} color="#34C759" />;
    if (trend === "down") return <ArrowDown size={14} color="#FF3B30" />;
    if (trend === "stable") return <Minus size={14} color="#8E8E93" />;
    return null;
  };

  const isEmpty = value === null || value === "--";
  const displayValue = value !== null ? String(value) : "--";

  return (
    <View
      style={[
        styles.container,
        { 
          borderColor: isEmpty ? "#1C1C1E" : "#2C2C2E",
          opacity: isEmpty ? 0.7 : 1
        }
      ]}
    >
      {/* Header avec icône */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          {icon && <View style={styles.iconContainer}>{icon}</View>}
          <Text style={styles.title}>{title}</Text>
        </View>
        {trend && getTrendIcon() && (
          <View style={styles.trendBadge}>{getTrendIcon()}</View>
        )}
      </View>

      {/* Valeur principale */}
      <View style={styles.valueContainer}>
        {isEmpty ? (
          <View style={styles.emptyValue}>
            <Text style={styles.emptyValueText}>--</Text>
            <View style={styles.emptyBadge}>
              <Text style={styles.emptyBadgeText}>Aucune donnée</Text>
            </View>
          </View>
        ) : (
          <Text style={[styles.value, { color }]}>{displayValue}</Text>
        )}
      </View>

      {/* Subtitle ou message */}
      {isEmpty ? (
        <View style={styles.syncHint}>
          <TrendingUp size={10} color="#444" />
          <Text style={styles.syncHintText}>Synchronisez vos données</Text>
        </View>
      ) : subtitle ? (
        <Text style={styles.subtitle}>{subtitle}</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#1C1C1E",
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 12,
  },
  headerLeft: {
    flexDirection: "row",
    alignItems: "center",
  },
  iconContainer: {
    marginRight: 8,
  },
  title: {
    color: "#8E8E93",
    fontSize: 11,
    textTransform: "uppercase",
    fontWeight: "700",
    letterSpacing: 0.5,
  },
  trendBadge: {
    backgroundColor: "#2C2C2E",
    borderRadius: 12,
    padding: 4,
  },
  valueContainer: {
    marginBottom: 8,
  },
  emptyValue: {
    flexDirection: "row",
    alignItems: "center",
  },
  emptyValueText: {
    color: "#48484A",
    fontSize: 24,
    fontWeight: "700",
  },
  emptyBadge: {
    marginLeft: 8,
    backgroundColor: "#2C2C2E",
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  emptyBadgeText: {
    color: "#8E8E93",
    fontSize: 10,
    fontWeight: "600",
  },
  value: {
    fontSize: 28,
    fontWeight: "700",
  },
  syncHint: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 4,
  },
  syncHintText: {
    color: "#48484A",
    fontSize: 10,
    marginLeft: 4,
  },
  subtitle: {
    color: "#8E8E93",
    fontSize: 12,
  },
});
