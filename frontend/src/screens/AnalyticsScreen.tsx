import React from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { EquityChart } from '../components/EquityChart';
import { StatCard } from '../components/StatCard';
import { ErrorView, LoadingView } from '../components/LoadingView';
import {
  useGetAnalyticsOverviewQuery,
  useGetDailyPnlQuery,
  useGetEquityCurveQuery,
} from '../store/api/tradingApi';
import { useTheme } from '../theme/ThemeContext';

export function AnalyticsScreen() {
  const { colors } = useTheme();
  const { data: overview, isLoading, isError, refetch } = useGetAnalyticsOverviewQuery(30);
  const { data: equity } = useGetEquityCurveQuery(30);
  const { data: daily } = useGetDailyPnlQuery();

  if (isLoading) return <LoadingView />;
  if (isError || !overview) {
    return <ErrorView message="Failed to load analytics" onRetry={refetch} />;
  }

  return (
    <ScrollView style={{ backgroundColor: colors.background }} contentContainerStyle={styles.content}>
      <Text style={[styles.title, { color: colors.text }]}>Analytics</Text>
      <View style={styles.statsRow}>
        <StatCard label="Total Trades" value={String(overview.total_trades)} />
        <StatCard label="Win Rate" value={`${overview.win_rate}%`} />
      </View>
      <View style={styles.statsRow}>
        <StatCard
          label="Total P/L"
          value={`$${overview.total_pnl.toFixed(2)}`}
          tone={overview.total_pnl >= 0 ? 'success' : 'danger'}
        />
        <StatCard label="Avg Win" value={`$${overview.average_win.toFixed(2)}`} tone="success" />
      </View>

      {equity ? <EquityChart points={equity.points} /> : null}

      <Text style={[styles.section, { color: colors.text }]}>Daily P/L</Text>
      {(daily?.series ?? []).slice(-7).map((d: { date: string; pnl: number }) => (
        <View
          key={d.date}
          style={[styles.barRow, { backgroundColor: colors.card, borderColor: colors.border }]}
        >
          <Text style={{ color: colors.textSecondary, fontSize: 12 }}>{d.date}</Text>
          <Text style={{ color: d.pnl >= 0 ? colors.success : colors.danger, fontWeight: '700' }}>
            ${d.pnl.toFixed(2)}
          </Text>
        </View>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: 16, paddingBottom: 32 },
  title: { fontSize: 22, fontWeight: '800', marginBottom: 12 },
  statsRow: { flexDirection: 'row', marginHorizontal: -4 },
  section: { fontSize: 16, fontWeight: '700', marginTop: 16, marginBottom: 8 },
  barRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: 10,
    borderRadius: 8,
    borderWidth: 1,
    marginBottom: 4,
  },
});
