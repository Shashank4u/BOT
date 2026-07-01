import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import Svg, { Polyline } from 'react-native-svg';
import { useTheme } from '../theme/ThemeContext';

export function EquityChart({
  points,
}: {
  points: Array<{ time: string; equity: number }>;
}) {
  const { colors } = useTheme();
  if (points.length < 2) {
    return (
      <Text style={{ color: colors.textSecondary, textAlign: 'center', padding: 16 }}>
        Not enough data for chart
      </Text>
    );
  }

  const width = 320;
  const height = 140;
  const values = points.map((p) => p.equity);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const coords = points.map((p, i) => {
    const x = (i / (points.length - 1)) * width;
    const y = height - ((p.equity - min) / range) * (height - 10) - 5;
    return `${x},${y}`;
  });

  return (
    <View style={[styles.wrap, { backgroundColor: colors.card, borderColor: colors.border }]}>
      <Text style={[styles.title, { color: colors.text }]}>Equity Curve</Text>
      <Svg width={width} height={height}>
        <Polyline
          points={coords.join(' ')}
          fill="none"
          stroke={colors.primary}
          strokeWidth={2}
        />
      </Svg>
      <View style={styles.labels}>
        <Text style={{ color: colors.textSecondary, fontSize: 11 }}>
          ${min.toFixed(0)} — ${max.toFixed(0)}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { borderRadius: 12, borderWidth: 1, padding: 12, marginVertical: 8 },
  title: { fontSize: 14, fontWeight: '600', marginBottom: 8 },
  labels: { marginTop: 4 },
});
