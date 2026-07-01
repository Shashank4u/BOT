import React from 'react';
import {
  Alert,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { ErrorView, LoadingView } from '../components/LoadingView';
import {
  useGetNotificationsQuery,
  useMarkAllNotificationsReadMutation,
} from '../store/api/tradingApi';
import { useTheme } from '../theme/ThemeContext';

export function NotificationsScreen() {
  const { colors } = useTheme();
  const { data, isLoading, isError, refetch } = useGetNotificationsQuery();
  const [markAll] = useMarkAllNotificationsReadMutation();

  if (isLoading) return <LoadingView />;
  if (isError) return <ErrorView message="Failed to load notifications" onRetry={refetch} />;

  const onMarkAll = async () => {
    try {
      const res = await markAll().unwrap();
      Alert.alert('Done', `${res.marked_read} marked as read`);
    } catch {
      Alert.alert('Error', 'Could not update notifications');
    }
  };

  return (
    <View style={{ flex: 1, backgroundColor: colors.background }}>
      <Pressable style={styles.markAll} onPress={onMarkAll}>
        <Text style={{ color: colors.primary, fontWeight: '600' }}>Mark all read</Text>
      </Pressable>
      <FlatList
        data={data ?? []}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={{ padding: 16 }}
        renderItem={({ item }) => (
          <View
            style={[
              styles.card,
              {
                backgroundColor: colors.card,
                borderColor: colors.border,
                opacity: item.is_read ? 0.7 : 1,
              },
            ]}
          >
            <Text style={[styles.title, { color: colors.text }]}>{item.title}</Text>
            <Text style={{ color: colors.textSecondary, fontSize: 13 }}>{item.message}</Text>
            <Text style={{ color: colors.textSecondary, fontSize: 11, marginTop: 6 }}>
              {item.category} · {new Date(item.created_at).toLocaleString()}
            </Text>
          </View>
        )}
        ListEmptyComponent={
          <Text style={{ color: colors.textSecondary, textAlign: 'center', marginTop: 40 }}>
            No notifications
          </Text>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  markAll: { alignItems: 'flex-end', padding: 16, paddingBottom: 0 },
  card: { padding: 14, borderRadius: 12, borderWidth: 1, marginBottom: 8 },
  title: { fontSize: 15, fontWeight: '700', marginBottom: 4 },
});
