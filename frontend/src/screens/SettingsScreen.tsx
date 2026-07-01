import React, { useEffect, useState } from 'react';
import {
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
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
  useGetRiskSettingsQuery,
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

  const { data: risk } = useGetRiskSettingsQuery();
  const [updateRisk] = useUpdateRiskSettingsMutation();
  const [confirmLive] = useConfirmLiveTradingMutation();

  useEffect(() => {
    if (risk) setMaxRisk(String(risk.max_risk_per_trade));
  }, [risk]);

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
});
