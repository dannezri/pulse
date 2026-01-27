import React, { useMemo } from 'react';
import { View, StyleSheet, Dimensions } from 'react-native';
import Svg, { Path, Line, Defs, LinearGradient as SvgLinearGradient, Stop } from 'react-native-svg';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const CHART_WIDTH = SCREEN_WIDTH - 80;
const CHART_HEIGHT = 120;
const PADDING = 10;

export interface MetricDataPoint {
  date: string;
  value: number;
}

interface LifeLineChartProps {
  data: MetricDataPoint[];
  baseline?: number; // Si non fourni, sera calculé comme la moyenne
  color: string;
  title?: string;
  unit?: string;
}

/**
 * Graphique "Ligne de Vie" avec baseline et zones colorées
 * - Ligne de baseline pointillée (grise)
 * - Ligne fluide des données avec courbes de Bézier
 * - Zone entre les deux remplie en dégradé (vert si au-dessus, orange si en dessous)
 */
export function LifeLineChart({ data, baseline, color }: LifeLineChartProps) {
  const { 
    baselineValue, 
    minValue, 
    maxValue, 
    pathData, 
    baselineY,
    areaPathAbove,
    areaPathBelow,
  } = useMemo(() => {
    if (!data || data.length === 0) {
      return {
        baselineValue: 0,
        minValue: 0,
        maxValue: 0,
        pathData: '',
        baselineY: CHART_HEIGHT / 2,
        areaPathAbove: '',
        areaPathBelow: '',
      };
    }

    // Filtrer les valeurs invalides
    const validData = data.filter(d => d && typeof d.value === 'number' && !isNaN(d.value) && isFinite(d.value));
    
    if (validData.length === 0) {
      return {
        baselineValue: 0,
        minValue: 0,
        maxValue: 0,
        pathData: '',
        baselineY: CHART_HEIGHT / 2,
        areaPathAbove: '',
        areaPathBelow: '',
      };
    }

    // Calculer la baseline (moyenne si non fournie)
    const baselineValue = baseline ?? validData.reduce((sum, d) => sum + d.value, 0) / validData.length;

    // Trouver min/max pour le scaling
    const values = validData.map(d => d.value);
    const minValue = Math.min(...values, baselineValue);
    const maxValue = Math.max(...values, baselineValue);
    const range = maxValue - minValue || 1; // Éviter division par zéro

    // Fonction pour convertir une valeur en coordonnée Y
    const valueToY = (value: number) => {
      const normalized = (maxValue - value) / range;
      return PADDING + normalized * (CHART_HEIGHT - 2 * PADDING);
    };

    // Calculer la position Y de la baseline
    const baselineY = valueToY(baselineValue);

    // Calculer les points pour la courbe
    const points = validData.map((d, i) => {
      const xPos = validData.length === 1 
        ? CHART_WIDTH / 2 
        : PADDING + (i / (validData.length - 1)) * (CHART_WIDTH - 2 * PADDING);
      
      return {
        x: xPos,
        y: valueToY(d.value),
        value: d.value,
      };
    });

    // Créer le path avec courbes de Bézier (lissage)
    let pathData = '';
    let areaPathAbove = '';
    let areaPathBelow = '';

    if (points.length === 1) {
      // Un seul point : ligne droite
      pathData = `M ${points[0].x} ${points[0].y}`;
    } else {
      // Plusieurs points : courbes de Bézier
      pathData = `M ${points[0].x} ${points[0].y}`;
      
      for (let i = 0; i < points.length - 1; i++) {
        const current = points[i];
        const next = points[i + 1];
        
        // Points de contrôle pour la courbe de Bézier (lissage)
        const cp1x = current.x + (next.x - current.x) / 3;
        const cp1y = current.y;
        const cp2x = current.x + 2 * (next.x - current.x) / 3;
        const cp2y = next.y;
        
        pathData += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${next.x} ${next.y}`;
      }
    }

    // Créer les zones remplies (au-dessus et en dessous de la baseline)
    if (points.length > 0) {
      // Zone au-dessus de la baseline (vert)
      areaPathAbove = `M ${points[0].x} ${baselineY}`;
      for (let i = 0; i < points.length; i++) {
        const point = points[i];
        if (i === 0) {
          areaPathAbove += ` L ${point.x} ${Math.min(point.y, baselineY)}`;
        } else {
          const prev = points[i - 1];
          const cp1x = prev.x + (point.x - prev.x) / 3;
          const cp1y = Math.min(prev.y, baselineY);
          const cp2x = prev.x + 2 * (point.x - prev.x) / 3;
          const cp2y = Math.min(point.y, baselineY);
          areaPathAbove += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${point.x} ${Math.min(point.y, baselineY)}`;
        }
      }
      areaPathAbove += ` L ${points[points.length - 1].x} ${baselineY} Z`;

      // Zone en dessous de la baseline (orange)
      areaPathBelow = `M ${points[0].x} ${baselineY}`;
      for (let i = 0; i < points.length; i++) {
        const point = points[i];
        if (i === 0) {
          areaPathBelow += ` L ${point.x} ${Math.max(point.y, baselineY)}`;
        } else {
          const prev = points[i - 1];
          const cp1x = prev.x + (point.x - prev.x) / 3;
          const cp1y = Math.max(prev.y, baselineY);
          const cp2x = prev.x + 2 * (point.x - prev.x) / 3;
          const cp2y = Math.max(point.y, baselineY);
          areaPathBelow += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${point.x} ${Math.max(point.y, baselineY)}`;
        }
      }
      areaPathBelow += ` L ${points[points.length - 1].x} ${baselineY} Z`;
    }

    return {
      baselineValue,
      minValue,
      maxValue,
      pathData,
      baselineY,
      areaPathAbove,
      areaPathBelow,
    };
  }, [data, baseline]);

  if (!data || data.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        {/* Placeholder vide */}
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Svg width={CHART_WIDTH} height={CHART_HEIGHT}>
        <Defs>
          {/* Dégradé vert (au-dessus de la baseline) */}
          <SvgLinearGradient id="gradientAbove" x1="0" y1="0" x2="0" y2="1">
            <Stop offset="0" stopColor="#00FF41" stopOpacity="0.4" />
            <Stop offset="1" stopColor="#00FF41" stopOpacity="0.05" />
          </SvgLinearGradient>
          
          {/* Dégradé orange (en dessous de la baseline) */}
          <SvgLinearGradient id="gradientBelow" x1="0" y1="0" x2="0" y2="1">
            <Stop offset="0" stopColor="#FF9500" stopOpacity="0.05" />
            <Stop offset="1" stopColor="#FF9500" stopOpacity="0.4" />
          </SvgLinearGradient>
        </Defs>

        {/* Zone au-dessus de la baseline (vert) */}
        {areaPathAbove && (
          <Path
            d={areaPathAbove}
            fill="url(#gradientAbove)"
          />
        )}

        {/* Zone en dessous de la baseline (orange) */}
        {areaPathBelow && (
          <Path
            d={areaPathBelow}
            fill="url(#gradientBelow)"
          />
        )}

        {/* Ligne de baseline pointillée */}
        <Line
          x1={PADDING}
          y1={baselineY}
          x2={CHART_WIDTH - PADDING}
          y2={baselineY}
          stroke="#8E8E93"
          strokeWidth={1.5}
          strokeDasharray="6,4"
          opacity={0.6}
        />

        {/* Ligne des données */}
        <Path
          d={pathData}
          stroke={color}
          strokeWidth={2.5}
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </Svg>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyContainer: {
    width: CHART_WIDTH,
    height: CHART_HEIGHT,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
