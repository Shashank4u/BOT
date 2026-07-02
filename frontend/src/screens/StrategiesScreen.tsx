import React from 'react';
import {
  Alert,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { ErrorView, LoadingView } from '../components/LoadingView';
import {
  useGetStrategiesQuery,
  useSeedStrategiesMutation,
  useUpdateStrategyMutation,
  type Strategy,
} from '../store/api/tradingApi';
import { useTheme } from '../theme/ThemeContext';
import type { StrategiesStackParamList } from '../navigation/types';

type Props = NativeStackScreenProps<StrategiesStackParamList, 'StrategiesList'>;

function StrategyCard({
  item,
  onToggle,
}: {
  item: Strategy;
  onToggle: (strategy: Strategy) => void;
}) {
  const { colors } = useTheme();
  const isActive = item.status === 'active';

  return (
    <View style={[styles.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
      <View style={styles.cardHeader}>
        <Text style={[styles.name, { color: colors.text }]}>{item.name}</Text>
        <Pressable
          style={[
            styles.statusBtn,
            {
              backgroundColor: isActive ? colors.success : colors.card,
              borderColor: isActive ? colors.success : colors.border,
            },
          ]}
          onPress={() => onToggle(item)}
        >
          <Text style={{ color: isActive ? '#fff' : colors.text, fontWeight: '700', fontSize: 12 }}>
            {isActive ? 'Active' : 'Paused'}
          </Text>
        </Pressable>
      </View>
      <Text style={{ color: colors.textSecondary, fontSize: 12 }}>
        {item.strategy_type} · {(item.symbols ?? []).join(', ') || 'EURUSD'}
      </Text>
      <Text style={{ color: colors.textSecondary, fontSize: 12, marginTop: 4 }}>
        SL {item.stop_loss_pips ?? '—'} / TP {item.take_profit_pips ?? '—'} pips
      </Text>
    </View>
  );
}

export function StrategiesScreen({ navigation }: Props) {
  const { colors } = useTheme();
  const { data, isLoading, isError, refetch } = useGetStrategiesQuery();
  const [seed, { isLoading: seeding }] = useSeedStrategiesMutation();
  const [updateStrategy] = useUpdateStrategyMutation();

  const onToggleStatus = async (strategy: Strategy) => {
    const nextStatus = strategy.status === 'active' ? 'paused' : 'active';
    try {
      await updateStrategy({ id: strategy.id, body: { status: nextStatus } }).unwrap();
    } catch {
      Alert.alert('Error', 'Failed to update strategy status');
    }
  };

  if (isLoading) return <LoadingView />;
  if (isError) return <ErrorView message="Failed to load strategies" onRetry={refetch} />;

  return (
    <View style={{ flex: 1, backgroundColor: colors.background }}>
      <View style={styles.actions}>
        <Pressable
          style={[styles.btn, { backgroundColor: colors.primary }]}
          onPress={() => navigation.navigate('StrategyBuilder')}
        >
          <Text style={styles.btnText}>+ New Strategy</Text>
        </Pressable>
        <Pressable
          style={[styles.btnOutline, { borderColor: colors.border }]}
          onPress={() => seed()}
          disabled={seeding}
        >
          <Text style={{ color: colors.text }}>{seeding ? 'Seeding…' : 'Seed Samples'}</Text>
        </Pressable>
      </View>
      <FlatList
        data={data ?? []}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={{ padding: 16 }}
        renderItem={({ item }) => <StrategyCard item={item} onToggle={onToggleStatus} />}
        ListEmptyComponent={
          <Text style={{ color: colors.textSecondary, textAlign: 'center', marginTop: 24 }}>
            No strategies — tap Seed Samples
          </Text>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  actions: { flexDirection: 'row', padding: 16, gap: 8 },
  btn: { flex: 1, padding: 12, borderRadius: 10, alignItems: 'center' },
  btnOutline: { padding: 12, borderRadius: 10, borderWidth: 1, alignItems: 'center' },
  btnText: { color: '#fff', fontWeight: '700' },
  card: { padding: 14, borderRadius: 12, borderWidth: 1, marginBottom: 8 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 },
  name: { fontSize: 16, fontWeight: '700', flex: 1 },
  statusBtn: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16, borderWidth: 1 },
});
