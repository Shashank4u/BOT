import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import type { Trade } from '../store/api/tradingApi';
import { useTheme } from '../theme/ThemeContext';

export function TradeCard({ trade }: { trade: Trade }) {
  const { colors } = useTheme();
  const pnl = trade.profit_loss ?? 0;
  const pnlColor = pnl >= 0 ? colors.success : colors.danger;

  return (
    <View style={[styles.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
      <View style={styles.row}>
        <Text style={[styles.symbol, { color: colors.text }]}>{trade.symbol}</Text>
        <Text style={[styles.badge, { color: colors.primary }]}>
          {trade.direction.toUpperCase()}
        </Text>
      </View>
      <Text style={{ color: colors.textSecondary, fontSize: 12 }}>
        {trade.status} · {trade.lot_size} lots @ {trade.entry_price.toFixed(5)}
      </Text>
      {trade.profit_loss !== null ? (
        <Text style={[styles.pnl, { color: pnlColor }]}>${pnl.toFixed(2)}</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { padding: 14, borderRadius: 12, borderWidth: 1, marginBottom: 8 },
  row: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 4 },
  symbol: { fontSize: 16, fontWeight: '700' },
  badge: { fontSize: 12, fontWeight: '600' },
  pnl: { marginTop: 6, fontSize: 16, fontWeight: '700' },
});
