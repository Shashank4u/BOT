import React, { useState } from 'react';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { TradeCard } from '../components/TradeCard';
import { ErrorView, LoadingView } from '../components/LoadingView';
import { useGetTradesQuery } from '../store/api/tradingApi';
import { useTheme } from '../theme/ThemeContext';

const FILTERS = ['all', 'open', 'closed'] as const;

export function TradesScreen() {
  const { colors } = useTheme();
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>('all');
  const status = filter === 'all' ? undefined : filter;
  const { data, isLoading, isError, refetch } = useGetTradesQuery(status);

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
        contentContainerStyle={{ padding: 16 }}
        renderItem={({ item }) => <TradeCard trade={item} />}
        ListEmptyComponent={
          <Text style={{ color: colors.textSecondary, textAlign: 'center', marginTop: 40 }}>
            No trades yet
          </Text>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  filters: { flexDirection: 'row', padding: 16, gap: 8 },
  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, borderWidth: 1 },
});
