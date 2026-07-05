import React, { useEffect, useState } from 'react';
import {
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from 'react-native';
import { API_HELP } from '../config';
import { saveSettings } from '../store';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import {
  setApiBaseUrl,
  setApiKey as setApiKeyAction,
  setDarkMode,
  type DarkModeSetting,
} from '../store/settingsSlice';
import {
  useConfirmLiveTradingMutation,
  useGetAutoTradingStatusQuery,
  useGetRiskSettingsQuery,
  useRunAutoTradingOnceMutation,
  useStartAutoTradingMutation,
  useStopAutoTradingMutation,
  useUpdateAutoTradingSettingsMutation,
  useUpdateRiskSettingsMutation,
} from '../store/api/tradingApi';
import { useTheme } from '../theme/ThemeContext';

export function SettingsScreen() {
  const { colors, isDark } = useTheme();
  const dispatch = useAppDispatch();
  const settings = useAppSelector((s) => s.settings);
  const [apiUrl, setApiUrl] = useState(settings.apiBaseUrl);
  const [apiKey, setApiKeyInput] = useState(settings.apiKey);
  const [maxRisk, setMaxRisk] = useState('1');
  const [scanInterval, setScanInterval] = useState('300');

  const { data: risk } = useGetRiskSettingsQuery();
  const { data: autoTrading } = useGetAutoTradingStatusQuery();
  const [updateRisk] = useUpdateRiskSettingsMutation();
  const [confirmLive] = useConfirmLiveTradingMutation();
  const [startAuto] = useStartAutoTradingMutation();
  const [stopAuto] = useStopAutoTradingMutation();
  const [runOnce, { isLoading: runningOnce }] = useRunAutoTradingOnceMutation();
  const [updateAutoSettings] = useUpdateAutoTradingSettingsMutation();

  useEffect(() => {
    if (risk) setMaxRisk(String(risk.max_risk_per_trade));
  }, [risk]);

  useEffect(() => {
    if (autoTrading) setScanInterval(String(autoTrading.interval_seconds));
  }, [autoTrading]);

  const persistSettings = async () => {
    dispatch(setApiBaseUrl(apiUrl.trim()));
    dispatch(setApiKeyAction(apiKey.trim()));
    await saveSettings({
      ...settings,
      apiBaseUrl: apiUrl.trim(),
      apiKey: apiKey.trim(),
    });
    Alert.alert('Saved', 'Settings updated');
  };

  const onTestConnection = async () => {
    const base = apiUrl.trim().replace(/\/$/, '');
    const headers: Record<string, string> = {};
    if (apiKey.trim()) headers['X-API-Key'] = apiKey.trim();

    try {
      const healthRes = await fetch(`${base}/health`, { headers });
      if (!healthRes.ok) throw new Error('health failed');
      const health = await healthRes.json();

      const tradesRes = await fetch(`${base}/orders/trades`, { headers });
      if (!tradesRes.ok) throw new Error('trades failed');
      const trades = await tradesRes.json();

      Alert.alert(
        'Connected ✓',
        `Backend: ${health.status}\nMode: ${health.trading_mode}\nDatabase: ${health.database}\nTrades found: ${trades.length}`,
      );
    } catch {
      Alert.alert(
        'Connection Failed',
        'Cannot reach the backend.\n\n1. Run: cd backend && uvicorn app.main:app --port 8000\n2. API URL should be http://localhost:8000/api/v1',
      );
    }
  };

  const onDarkMode = (mode: DarkModeSetting) => {
    dispatch(setDarkMode(mode));
    saveSettings({ ...settings, darkMode: mode });
  };

  const onSaveRisk = async () => {
    try {
      await updateRisk({ max_risk_per_trade: Number(maxRisk) || 1 }).unwrap();
      Alert.alert('Saved', 'Risk settings updated');
    } catch {
      Alert.alert('Error', 'Failed to update risk settings');
    }
  };

  const onToggleAutoTrading = async (enabled: boolean) => {
    try {
      if (enabled) {
        await startAuto().unwrap();
        Alert.alert('Auto-Trading On', 'Active strategies will be scanned automatically.');
      } else {
        await stopAuto().unwrap();
        Alert.alert('Auto-Trading Off', 'No new trades will be placed automatically.');
      }
    } catch {
      Alert.alert('Error', 'Failed to update auto-trading');
    }
  };

  const onSaveAutoSettings = async () => {
    try {
      const seconds = Number(scanInterval) || 300;
      await updateAutoSettings({ interval_seconds: Math.max(60, seconds) }).unwrap();
      Alert.alert('Saved', 'Auto-trading interval updated');
    } catch {
      Alert.alert('Error', 'Failed to save auto-trading settings');
    }
  };

  const onRunScanNow = async () => {
    try {
      const result = await runOnce().unwrap();
      Alert.alert(
        'Scan Complete',
        `Evaluated ${result.scanned} signals · ${result.orders_placed} orders placed`,
      );
    } catch {
      Alert.alert('Error', 'Scan failed — is the backend running?');
    }
  };

  const onConfirmLive = () => {
    Alert.alert(
      'Enable Live Trading',
      'This allows real money trades. Only proceed if you understand the risks.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'I Understand',
          style: 'destructive',
          onPress: async () => {
            try {
              await confirmLive().unwrap();
              Alert.alert('Confirmed', 'Live trading gate unlocked on backend');
            } catch {
              Alert.alert('Error', 'Failed to confirm live trading');
            }
          },
        },
      ],
    );
  };

  return (
    <ScrollView style={{ backgroundColor: colors.background }} contentContainerStyle={styles.content}>
      <Text style={[styles.section, { color: colors.text }]}>Connection</Text>
      <Text style={[styles.hint, { color: colors.textSecondary }]}>{API_HELP}</Text>
      <TextInput
        style={[styles.input, { backgroundColor: colors.card, color: colors.text, borderColor: colors.border }]}
        value={apiUrl}
        onChangeText={setApiUrl}
        placeholder="API URL"
        placeholderTextColor={colors.textSecondary}
        autoCapitalize="none"
      />
      <TextInput
        style={[styles.input, { backgroundColor: colors.card, color: colors.text, borderColor: colors.border }]}
        value={apiKey}
        onChangeText={setApiKeyInput}
        placeholder="API Key (optional)"
        placeholderTextColor={colors.textSecondary}
        autoCapitalize="none"
        secureTextEntry
      />
      <Pressable style={[styles.btn, { backgroundColor: colors.primary }]} onPress={persistSettings}>
        <Text style={styles.btnText}>Save Connection</Text>
      </Pressable>
      <Pressable style={[styles.btnOutline, { borderColor: colors.border }]} onPress={onTestConnection}>
        <Text style={{ color: colors.text, fontWeight: '600' }}>Test Connection</Text>
      </Pressable>

      <Text style={[styles.section, { color: colors.text }]}>Appearance</Text>
      <View style={styles.row}>
        {(['dark', 'light', 'system'] as DarkModeSetting[]).map((mode) => (
          <Pressable
            key={mode}
            onPress={() => onDarkMode(mode)}
            style={[
              styles.chip,
              {
                backgroundColor: settings.darkMode === mode ? colors.primary : colors.card,
                borderColor: colors.border,
              },
            ]}
          >
            <Text style={{ color: settings.darkMode === mode ? '#fff' : colors.text }}>{mode}</Text>
          </Pressable>
        ))}
      </View>
      <Text style={{ color: colors.textSecondary, fontSize: 12, marginTop: 4 }}>
        Current: {isDark ? 'Dark' : 'Light'}
      </Text>

      <Text style={[styles.section, { color: colors.text }]}>Risk</Text>
      <Text style={[styles.label, { color: colors.textSecondary }]}>Max risk per trade (%)</Text>
      <TextInput
        style={[styles.input, { backgroundColor: colors.card, color: colors.text, borderColor: colors.border }]}
        value={maxRisk}
        onChangeText={setMaxRisk}
        keyboardType="decimal-pad"
      />
      <Pressable style={[styles.btnOutline, { borderColor: colors.border }]} onPress={onSaveRisk}>
        <Text style={{ color: colors.text, fontWeight: '600' }}>Save Risk Settings</Text>
      </Pressable>

      <Text style={[styles.section, { color: colors.text }]}>Auto Trading</Text>
      <Text style={{ color: colors.textSecondary, fontSize: 12, marginBottom: 8 }}>
        Runs active strategies on a timer. Activate strategies in the Strategies tab first.
      </Text>
      <View style={[styles.switchRow, { borderColor: colors.border }]}>
        <Text style={{ color: colors.text, fontWeight: '600' }}>Enable Auto-Trading</Text>
        <Switch
          value={autoTrading?.enabled ?? false}
          onValueChange={onToggleAutoTrading}
          trackColor={{ false: colors.border, true: colors.primary }}
        />
      </View>
      <Text style={{ color: colors.textSecondary, fontSize: 12, marginBottom: 8 }}>
        Status: {autoTrading?.bot_status ?? 'idle'} · Active strategies:{' '}
        {autoTrading?.active_strategies ?? 0}
      </Text>
      {autoTrading?.last_message ? (
        <Text style={{ color: colors.textSecondary, fontSize: 11, marginBottom: 8 }}>
          {autoTrading.last_message}
        </Text>
      ) : null}
      <Text style={[styles.label, { color: colors.textSecondary }]}>Scan interval (seconds)</Text>
      <TextInput
        style={[styles.input, { backgroundColor: colors.card, color: colors.text, borderColor: colors.border }]}
        value={scanInterval}
        onChangeText={setScanInterval}
        keyboardType="number-pad"
      />
      <Pressable style={[styles.btnOutline, { borderColor: colors.border }]} onPress={onSaveAutoSettings}>
        <Text style={{ color: colors.text, fontWeight: '600' }}>Save Interval</Text>
      </Pressable>
      <Pressable
        style={[styles.btn, { backgroundColor: colors.primary, opacity: runningOnce ? 0.6 : 1 }]}
        onPress={onRunScanNow}
        disabled={runningOnce}
      >
        <Text style={styles.btnText}>{runningOnce ? 'Scanning…' : 'Run Scan Now'}</Text>
      </Pressable>

      <Text style={[styles.section, { color: colors.text }]}>Live Trading</Text>
      <Text style={{ color: colors.textSecondary, fontSize: 13, marginBottom: 8 }}>
        Mode: {risk?.trading_mode ?? 'demo'} · Confirmed:{' '}
        {risk?.live_trading_confirmed ? 'Yes' : 'No'}
      </Text>
      <Pressable style={[styles.btnDanger, { backgroundColor: colors.danger }]} onPress={onConfirmLive}>
        <Text style={styles.btnText}>Confirm Live Trading</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: 16, paddingBottom: 40 },
  section: { fontSize: 18, fontWeight: '700', marginTop: 16, marginBottom: 8 },
  hint: { fontSize: 11, marginBottom: 8, lineHeight: 15 },
  label: { fontSize: 12, marginBottom: 6 },
  input: { borderWidth: 1, borderRadius: 10, padding: 12, marginBottom: 8, fontSize: 14 },
  btn: { padding: 12, borderRadius: 10, alignItems: 'center', marginTop: 4 },
  btnOutline: { padding: 12, borderRadius: 10, borderWidth: 1, alignItems: 'center', marginTop: 8 },
  btnDanger: { padding: 12, borderRadius: 10, alignItems: 'center', marginTop: 4 },
  btnText: { color: '#fff', fontWeight: '700' },
  row: { flexDirection: 'row', gap: 8 },
  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, borderWidth: 1 },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    borderWidth: 1,
    borderRadius: 10,
    marginBottom: 8,
  },
});
