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
import { ErrorView, LoadingView } from '../components/LoadingView';
import {
  useAddBrokerAccountMutation,
  useConnectBrokerAccountMutation,
  useDeleteBrokerAccountMutation,
  useDisconnectBrokerMutation,
  useGetBrokerAccountsQuery,
  useGetMarketStatusQuery,
  type BrokerAccount,
} from '../store/api/tradingApi';
import { useTheme } from '../theme/ThemeContext';

const DEFAULT_SERVER = 'XMGlobal-MT5';

function AccountCard({
  account,
  onConnect,
  onDelete,
}: {
  account: BrokerAccount;
  onConnect: (id: number) => void;
  onDelete: (id: number) => void;
}) {
  const { colors } = useTheme();

  return (
    <View style={[styles.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
      <View style={styles.cardHeader}>
        <Text style={[styles.cardTitle, { color: colors.text }]}>{account.name}</Text>
        {account.is_active ? (
          <Text style={{ color: colors.success, fontWeight: '700', fontSize: 12 }}>Active</Text>
        ) : null}
      </View>
      <Text style={{ color: colors.textSecondary, fontSize: 12 }}>
        {account.broker} · {account.account_type} · Login {account.mt5_login}
      </Text>
      <Text style={{ color: colors.textSecondary, fontSize: 12, marginTop: 4 }}>
        {account.mt5_server} · ${account.balance.toFixed(2)} balance
      </Text>
      <Text style={{ color: colors.textSecondary, fontSize: 12, marginTop: 2 }}>
        {account.is_connected ? 'Connected' : 'Disconnected'}
      </Text>
      <View style={styles.cardActions}>
        {!account.is_active || !account.is_connected ? (
          <Pressable
            style={[styles.smallBtn, { backgroundColor: colors.primary }]}
            onPress={() => onConnect(account.id)}
          >
            <Text style={styles.smallBtnText}>Connect</Text>
          </Pressable>
        ) : null}
        <Pressable
          style={[styles.smallBtnOutline, { borderColor: colors.border }]}
          onPress={() => onDelete(account.id)}
        >
          <Text style={{ color: colors.danger, fontWeight: '600' }}>Remove</Text>
        </Pressable>
      </View>
    </View>
  );
}

export function BrokerAccountScreen() {
  const { colors } = useTheme();
  const { data: accounts, isLoading, isError, refetch } = useGetBrokerAccountsQuery();
  const { data: marketStatus, refetch: refetchStatus } = useGetMarketStatusQuery();
  const [addAccount, { isLoading: adding }] = useAddBrokerAccountMutation();
  const [connectAccount] = useConnectBrokerAccountMutation();
  const [disconnect] = useDisconnectBrokerMutation();
  const [deleteAccount] = useDeleteBrokerAccountMutation();

  const [name, setName] = useState('XM Demo Account');
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [server, setServer] = useState(DEFAULT_SERVER);
  const [accountType, setAccountType] = useState<'demo' | 'live'>('demo');

  useEffect(() => {
    refetchStatus();
  }, [accounts, refetchStatus]);

  const onSaveAndConnect = async () => {
    const mt5Login = Number(login);
    if (!mt5Login || !password.trim() || !server.trim()) {
      Alert.alert('Missing fields', 'Enter MT5 login, password, and server.');
      return;
    }

    try {
      const result = await addAccount({
        name: name.trim() || 'XM Account',
        broker: 'XM',
        account_type: accountType,
        mt5_login: mt5Login,
        mt5_password: password,
        mt5_server: server.trim(),
      }).unwrap();
      setPassword('');
      Alert.alert('Connected', result.message);
      refetch();
      refetchStatus();
    } catch (err: unknown) {
      const message =
        err && typeof err === 'object' && 'data' in err
          ? String((err as { data?: { detail?: string } }).data?.detail ?? 'Connection failed')
          : 'Connection failed';
      Alert.alert('Error', message);
    }
  };

  const onConnect = async (id: number) => {
    try {
      const result = await connectAccount(id).unwrap();
      Alert.alert('Connected', result.message);
      refetch();
      refetchStatus();
    } catch {
      Alert.alert('Error', 'Failed to connect account');
    }
  };

  const onDisconnect = async () => {
    try {
      const result = await disconnect().unwrap();
      Alert.alert('Disconnected', result.message);
      refetch();
      refetchStatus();
    } catch {
      Alert.alert('Error', 'Failed to disconnect');
    }
  };

  const onDelete = (id: number) => {
    Alert.alert('Remove account', 'Remove this saved broker account?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Remove',
        style: 'destructive',
        onPress: async () => {
          try {
            await deleteAccount(id).unwrap();
            refetch();
            refetchStatus();
          } catch {
            Alert.alert('Error', 'Failed to remove account');
          }
        },
      },
    ]);
  };

  if (isLoading) return <LoadingView />;
  if (isError) return <ErrorView message="Failed to load accounts" onRetry={refetch} />;

  const connected = marketStatus?.connected ?? false;

  return (
    <ScrollView style={{ backgroundColor: colors.background }} contentContainerStyle={styles.content}>
      <View style={[styles.statusCard, { backgroundColor: colors.card, borderColor: colors.border }]}>
        <Text style={[styles.section, { color: colors.text, marginTop: 0 }]}>MT5 Connection</Text>
        <Text style={{ color: connected ? colors.success : colors.textSecondary, fontWeight: '700' }}>
          {connected ? 'Connected' : 'Disconnected'}
        </Text>
        <Text style={{ color: colors.textSecondary, fontSize: 12, marginTop: 4 }}>
          Provider: {marketStatus?.provider ?? '—'}
          {marketStatus?.login ? ` · Login ${marketStatus.login}` : ''}
        </Text>
        {marketStatus?.message ? (
          <Text style={{ color: colors.textSecondary, fontSize: 11, marginTop: 6 }}>
            {marketStatus.message}
          </Text>
        ) : null}
        {connected ? (
          <Pressable style={[styles.btnOutline, { borderColor: colors.border }]} onPress={onDisconnect}>
            <Text style={{ color: colors.text, fontWeight: '600' }}>Disconnect</Text>
          </Pressable>
        ) : null}
      </View>

      <Text style={[styles.section, { color: colors.text }]}>Add Broker Account</Text>
      <Text style={[styles.hint, { color: colors.textSecondary }]}>
        Enter your XM / MT5 credentials. On Mac, mock data is used for development. Real trading
        requires Windows + MT5 terminal on the server.
      </Text>

      <Text style={[styles.label, { color: colors.textSecondary }]}>Account name</Text>
      <TextInput
        style={[styles.input, { backgroundColor: colors.card, color: colors.text, borderColor: colors.border }]}
        value={name}
        onChangeText={setName}
      />

      <Text style={[styles.label, { color: colors.textSecondary }]}>MT5 Login</Text>
      <TextInput
        style={[styles.input, { backgroundColor: colors.card, color: colors.text, borderColor: colors.border }]}
        value={login}
        onChangeText={setLogin}
        keyboardType="number-pad"
        placeholder="12345678"
        placeholderTextColor={colors.textSecondary}
      />

      <Text style={[styles.label, { color: colors.textSecondary }]}>MT5 Password</Text>
      <TextInput
        style={[styles.input, { backgroundColor: colors.card, color: colors.text, borderColor: colors.border }]}
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        placeholder="Investor or main password"
        placeholderTextColor={colors.textSecondary}
      />

      <Text style={[styles.label, { color: colors.textSecondary }]}>Server</Text>
      <TextInput
        style={[styles.input, { backgroundColor: colors.card, color: colors.text, borderColor: colors.border }]}
        value={server}
        onChangeText={setServer}
        autoCapitalize="none"
      />

      <Text style={[styles.label, { color: colors.textSecondary }]}>Account type</Text>
      <View style={styles.row}>
        {(['demo', 'live'] as const).map((type) => (
          <Pressable
            key={type}
            onPress={() => setAccountType(type)}
            style={[
              styles.chip,
              {
                backgroundColor: accountType === type ? colors.primary : colors.card,
                borderColor: colors.border,
              },
            ]}
          >
            <Text style={{ color: accountType === type ? '#fff' : colors.text }}>{type}</Text>
          </Pressable>
        ))}
      </View>

      <Pressable
        style={[styles.btn, { backgroundColor: colors.primary, opacity: adding ? 0.6 : 1 }]}
        onPress={onSaveAndConnect}
        disabled={adding}
      >
        <Text style={styles.btnText}>{adding ? 'Connecting…' : 'Save & Connect'}</Text>
      </Pressable>

      <Text style={[styles.section, { color: colors.text }]}>Saved Accounts</Text>
      {(accounts ?? []).length === 0 ? (
        <Text style={{ color: colors.textSecondary, textAlign: 'center', marginTop: 12 }}>
          No broker accounts saved yet
        </Text>
      ) : (
        (accounts ?? []).map((account) => (
          <AccountCard
            key={account.id}
            account={account}
            onConnect={onConnect}
            onDelete={onDelete}
          />
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: 16, paddingBottom: 40 },
  section: { fontSize: 18, fontWeight: '700', marginTop: 16, marginBottom: 8 },
  hint: { fontSize: 12, lineHeight: 17, marginBottom: 8 },
  label: { fontSize: 12, marginBottom: 6 },
  input: { borderWidth: 1, borderRadius: 10, padding: 12, marginBottom: 8, fontSize: 14 },
  btn: { padding: 14, borderRadius: 10, alignItems: 'center', marginTop: 8 },
  btnOutline: { padding: 12, borderRadius: 10, borderWidth: 1, alignItems: 'center', marginTop: 10 },
  btnText: { color: '#fff', fontWeight: '700' },
  row: { flexDirection: 'row', gap: 8, marginBottom: 8 },
  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, borderWidth: 1 },
  statusCard: { padding: 14, borderRadius: 12, borderWidth: 1 },
  card: { padding: 14, borderRadius: 12, borderWidth: 1, marginBottom: 8 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cardTitle: { fontSize: 16, fontWeight: '700' },
  cardActions: { flexDirection: 'row', gap: 8, marginTop: 10 },
  smallBtn: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8 },
  smallBtnText: { color: '#fff', fontWeight: '600', fontSize: 12 },
  smallBtnOutline: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8, borderWidth: 1 },
});
