import React from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { useTheme } from '../theme/ThemeContext';

export function LoadingView({ label = 'Loading…' }: { label?: string }) {
  const { colors } = useTheme();
  return (
    <View style={[styles.center, { backgroundColor: colors.background }]}>
      <ActivityIndicator size="large" color={colors.primary} />
      <Text style={[styles.text, { color: colors.textSecondary }]}>{label}</Text>
    </View>
  );
}

export function ErrorView({ message, onRetry }: { message: string; onRetry?: () => void }) {
  const { colors } = useTheme();
  return (
    <View style={[styles.center, { backgroundColor: colors.background }]}>
      <Text style={[styles.error, { color: colors.danger }]}>{message}</Text>
      {onRetry ? (
        <Text style={[styles.retry, { color: colors.primary }]} onPress={onRetry}>
          Tap to retry
        </Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 },
  text: { marginTop: 12, fontSize: 14 },
  error: { fontSize: 15, textAlign: 'center', marginBottom: 12 },
  retry: { fontSize: 15, fontWeight: '600' },
});
