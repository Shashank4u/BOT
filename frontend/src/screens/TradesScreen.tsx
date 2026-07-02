import React, { useCallback, useState } from 'react';
import {
  Alert,
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { TradeCard } from '../components/TradeCard';
import { ErrorView, LoadingView } from '../components/LoadingView';
import { useGetTradesQuery, usePlaceMarketOrderMutation } from '../store/api/tradingApi';
import { useTheme } from '../theme/ThemeContext';

const FILTERS = ['all', 'open', 'closed'] as const;

export function TradesScreen() {
  const { colors } = useTheme();
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>('all');
  const status = filter === 'all' ? undefined : filter;
  const { data, isLoading, isError, refetch, isFetching } = useGetTradesQuery(status);
  const [placeOrder, { isLoading: placing }] = usePlaceMarketOrderMutation();

  useFocusEffect(
    useCallback(() => {
      refetch();
    }, [refetch]),
  );

  const onDemoTrade = async () => {
    try {
      await placeOrder({
        symbol: 'EURUSD',
        side: 'buy',
        lot_size: 0.01,
        stop_loss_pips: 20,
      }).unwrap();
      refetch();
      Alert.alert('Success', 'Demo EURUSD buy order placed');
    } catch {
      Alert.alert('Error', 'Failed to place trade. Check backend is running on port 8000.');
    }
  };

  if (isLoading) return <LoadingView />;
  if (isError) return <ErrorView message="Failed to load trades" onRetry={refetch} />;

  return (
    <View style={{ flex: 1, backgroundColor: colors.background }}>
      <View style={styles.filters}>
        {FILTERS.map((f) => (
          <Pressable
            key={f}
            onPress={() => setFilter(f)}
            style={[
              styles.chip,
              {
                backgroundColor: filter === f ? colors.primary : colors.card,
                borderColor: colors.border,
              },
            ]}
          >
            <Text style={{ color: filter === f ? '#fff' : colors.text, fontWeight: '600' }}>
              {f}
            </Text>
          </Pressable>
        ))}
      </View>
      <FlatList
        data={data ?? []}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
        refreshControl={
          <RefreshControl refreshing={isFetching} onRefresh={refetch} tintColor={colors.primary} />
        }
        renderItem={({ item }) => <TradeCard trade={item} />}
        ListHeaderComponent={
          <Pressable
            style={[styles.demoBtn, { backgroundColor: colors.primary, opacity: placing ? 0.6 : 1 }]}
            onPress={onDemoTrade}
            disabled={placing}
          >
            <Text style={styles.demoBtnText}>{placing ? 'Placing…' : '+ Place Demo Trade (EURUSD)'}</Text>
          </Pressable>
        }
        ListEmptyComponent={
          <Text style={{ color: colors.textSecondary, textAlign: 'center', marginTop: 24 }}>
            No trades yet — tap the button above or pull down to refresh
          </Text>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  filters: { flexDirection: 'row', padding: 16, gap: 8, paddingBottom: 0 },
  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, borderWidth: 1 },
  demoBtn: { padding: 14, borderRadius: 10, alignItems: 'center', marginBottom: 12 },
  demoBtnText: { color: '#fff', fontWeight: '700' },
});
