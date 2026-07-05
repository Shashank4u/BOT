import React from 'react';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { StatCard } from '../components/StatCard';
import { ErrorView, LoadingView } from '../components/LoadingView';
import { useGetAnalyticsOverviewQuery, useGetDashboardQuery, type DashboardData } from '../store/api/tradingApi';
import { useTheme } from '../theme/ThemeContext';

export function DashboardScreen() {
  const { colors } = useTheme();
  const { data, isLoading, isError, refetch, isFetching } = useGetDashboardQuery();
  const { data: analytics } = useGetAnalyticsOverviewQuery(30);

  if (isLoading) return <LoadingView />;
  if (isError || !data) {
    return (
      <ErrorView
        message="Cannot reach backend. Check API URL in Settings."
        onRetry={refetch}
      />
    );
  }

  const modeColor = data.trading_mode === 'demo' ? colors.demo : colors.warning;
  const botColor =
    data.bot_status === 'running'
      ? colors.success
      : data.bot_status === 'error'
        ? colors.danger
        : colors.textSecondary;

  return (
    <ScrollView
      style={{ backgroundColor: colors.background }}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={isFetching} onRefresh={refetch} />}
    >
      <View style={styles.header}>
        <Text style={[styles.title, { color: colors.text }]}>Dashboard</Text>
        <Text style={[styles.mode, { color: modeColor }]}>
          {data.trading_mode.toUpperCase()} · {data.market_status}
        </Text>
        <Text style={[styles.bot, { color: botColor }]}>
          Bot: {data.bot_status}
          {data.auto_trading_enabled ? ` · ${data.active_strategies} active` : ''}
        </Text>
      </View>

      <View style={styles.statsRow}>
        <StatCard label="Balance" value={`$${data.account.balance.toFixed(2)}`} />
        <StatCard label="Equity" value={`$${data.account.equity.toFixed(2)}`} />
      </View>
      <View style={styles.statsRow}>
        <StatCard
          label="30d P/L"
          value={`$${(analytics?.total_pnl ?? 0).toFixed(2)}`}
          tone={(analytics?.total_pnl ?? 0) >= 0 ? 'success' : 'danger'}
        />
        <StatCard label="Win Rate" value={`${analytics?.win_rate ?? 0}%`} />
      </View>

      <Text style={[styles.section, { color: colors.text }]}>Watchlist</Text>
      {data.watchlist_prices.map((tick: DashboardData['watchlist_prices'][number]) => (
        <View
          key={tick.symbol}
          style={[styles.priceRow, { backgroundColor: colors.card, borderColor: colors.border }]}
        >
          <Text style={{ color: colors.text, fontWeight: '600' }}>{tick.symbol}</Text>
          <Text style={{ color: colors.textSecondary }}>
            {tick.bid.toFixed(5)} / {tick.ask.toFixed(5)}
          </Text>
        </View>
      ))}

      <Text style={[styles.disclaimer, { color: colors.textSecondary }]}>{data.disclaimer}</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: 16, paddingBottom: 32 },
  header: { marginBottom: 12 },
  title: { fontSize: 24, fontWeight: '800' },
  mode: { fontSize: 13, marginTop: 4, fontWeight: '600' },
  bot: { fontSize: 12, marginTop: 4, fontWeight: '600' },
  statsRow: { flexDirection: 'row', marginHorizontal: -4 },
  section: { fontSize: 16, fontWeight: '700', marginTop: 16, marginBottom: 8 },
  priceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 6,
  },
  disclaimer: { fontSize: 11, marginTop: 20, lineHeight: 16 },
});
