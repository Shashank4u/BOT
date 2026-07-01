import React, { useState } from 'react';
import {
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useCreateStrategyMutation } from '../store/api/tradingApi';
import { useTheme } from '../theme/ThemeContext';
import type { StrategiesStackParamList } from '../navigation/types';

const STRATEGY_TYPES = [
  'ema_cross',
  'ema_rsi',
  'macd_trend',
  'breakout',
  'support_resistance',
  'pullback',
  'scalping',
  'swing',
];

type Props = NativeStackScreenProps<StrategiesStackParamList, 'StrategyBuilder'>;

export function StrategyBuilderScreen({ navigation }: Props) {
  const { colors } = useTheme();
  const [createStrategy, { isLoading }] = useCreateStrategyMutation();

  const [name, setName] = useState('My Strategy');
  const [strategyType, setStrategyType] = useState('ema_cross');
  const [symbol, setSymbol] = useState('EURUSD');
  const [stopLoss, setStopLoss] = useState('20');
  const [takeProfit, setTakeProfit] = useState('40');

  const onSave = async () => {
    try {
      await createStrategy({
        name,
        strategy_type: strategyType,
        symbols: [symbol.toUpperCase()],
        timeframes: ['H1'],
        params: {},
        stop_loss_pips: Number(stopLoss) || 20,
        take_profit_pips: Number(takeProfit) || 40,
        max_risk_percent: 1,
        max_trades: 3,
      }).unwrap();
      Alert.alert('Saved', 'Strategy created successfully');
      navigation.goBack();
    } catch {
      Alert.alert('Error', 'Failed to create strategy');
    }
  };

  return (
    <ScrollView style={{ backgroundColor: colors.background }} contentContainerStyle={styles.content}>
      <Text style={[styles.label, { color: colors.textSecondary }]}>Name</Text>
      <TextInput
        style={[styles.input, { backgroundColor: colors.card, color: colors.text, borderColor: colors.border }]}
        value={name}
        onChangeText={setName}
      />

      <Text style={[styles.label, { color: colors.textSecondary }]}>Strategy Type</Text>
      <View style={styles.types}>
        {STRATEGY_TYPES.map((t) => (
          <Pressable
            key={t}
            onPress={() => setStrategyType(t)}
            style={[
              styles.chip,
              {
                backgroundColor: strategyType === t ? colors.primary : colors.card,
                borderColor: colors.border,
              },
            ]}
          >
            <Text style={{ color: strategyType === t ? '#fff' : colors.text, fontSize: 11 }}>
              {t}
            </Text>
          </Pressable>
        ))}
      </View>

      <Text style={[styles.label, { color: colors.textSecondary }]}>Symbol</Text>
      <TextInput
        style={[styles.input, { backgroundColor: colors.card, color: colors.text, borderColor: colors.border }]}
        value={symbol}
        onChangeText={setSymbol}
        autoCapitalize="characters"
      />

      <View style={styles.row}>
        <View style={{ flex: 1 }}>
          <Text style={[styles.label, { color: colors.textSecondary }]}>Stop Loss (pips)</Text>
          <TextInput
            style={[styles.input, { backgroundColor: colors.card, color: colors.text, borderColor: colors.border }]}
            value={stopLoss}
            onChangeText={setStopLoss}
            keyboardType="numeric"
          />
        </View>
        <View style={{ flex: 1, marginLeft: 8 }}>
          <Text style={[styles.label, { color: colors.textSecondary }]}>Take Profit (pips)</Text>
          <TextInput
            style={[styles.input, { backgroundColor: colors.card, color: colors.text, borderColor: colors.border }]}
            value={takeProfit}
            onChangeText={setTakeProfit}
            keyboardType="numeric"
          />
        </View>
      </View>

      <Pressable
        style={[styles.save, { backgroundColor: colors.primary, opacity: isLoading ? 0.6 : 1 }]}
        onPress={onSave}
        disabled={isLoading}
      >
        <Text style={styles.saveText}>{isLoading ? 'Saving…' : 'Save Strategy'}</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: 16 },
  label: { fontSize: 12, marginBottom: 6, marginTop: 12 },
  input: { borderWidth: 1, borderRadius: 10, padding: 12, fontSize: 15 },
  types: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  chip: { paddingHorizontal: 10, paddingVertical: 8, borderRadius: 8, borderWidth: 1 },
  row: { flexDirection: 'row' },
  save: { marginTop: 24, padding: 14, borderRadius: 12, alignItems: 'center' },
  saveText: { color: '#fff', fontWeight: '700', fontSize: 16 },
});
