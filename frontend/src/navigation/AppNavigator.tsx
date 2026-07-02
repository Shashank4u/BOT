import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { AnalyticsScreen } from '../screens/AnalyticsScreen';
import { DashboardScreen } from '../screens/DashboardScreen';
import { BrokerAccountScreen } from '../screens/BrokerAccountScreen';
import { NotificationsScreen } from '../screens/NotificationsScreen';
import { SettingsScreen } from '../screens/SettingsScreen';
import { StrategiesScreen } from '../screens/StrategiesScreen';
import { StrategyBuilderScreen } from '../screens/StrategyBuilderScreen';
import { TradesScreen } from '../screens/TradesScreen';
import { useTheme } from '../theme/ThemeContext';
import type { MoreStackParamList, RootTabParamList, StrategiesStackParamList } from './types';

const Tab = createBottomTabNavigator<RootTabParamList>();
const StrategiesStack = createNativeStackNavigator<StrategiesStackParamList>();
const MoreStack = createNativeStackNavigator<MoreStackParamList>();

function TabIcon({ label, focused, color }: { label: string; focused: boolean; color: string }) {
  const icons: Record<string, string> = {
    Dashboard: '◉',
    Trades: '⇄',
    Strategies: '⚡',
    Analytics: '▤',
    More: '☰',
  };
  return (
    <Text style={{ color, fontSize: focused ? 18 : 16, fontWeight: focused ? '700' : '400' }}>
      {icons[label] ?? '•'}
    </Text>
  );
}

function StrategiesNavigator() {
  const { colors } = useTheme();
  return (
    <StrategiesStack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: colors.card },
        headerTintColor: colors.text,
        contentStyle: { backgroundColor: colors.background },
      }}
    >
      <StrategiesStack.Screen
        name="StrategiesList"
        component={StrategiesScreen}
        options={{ title: 'Strategies' }}
      />
      <StrategiesStack.Screen
        name="StrategyBuilder"
        component={StrategyBuilderScreen}
        options={{ title: 'New Strategy' }}
      />
    </StrategiesStack.Navigator>
  );
}

type MoreMenuProps = NativeStackScreenProps<MoreStackParamList, 'MoreMenu'>;

function MoreMenuScreen({ navigation }: MoreMenuProps) {
  const { colors } = useTheme();
  const items: Array<{ label: string; screen: keyof MoreStackParamList }> = [
    { label: 'Broker Account', screen: 'BrokerAccount' },
    { label: 'Notifications', screen: 'Notifications' },
    { label: 'Settings', screen: 'Settings' },
  ];

  return (
    <View style={[styles.menu, { backgroundColor: colors.background }]}>
      {items.map((item) => (
        <Pressable
          key={item.screen}
          style={[styles.menuItem, { backgroundColor: colors.card, borderColor: colors.border }]}
          onPress={() => navigation.navigate(item.screen)}
        >
          <Text style={{ color: colors.text, fontSize: 16, fontWeight: '600' }}>{item.label}</Text>
          <Text style={{ color: colors.textSecondary }}>›</Text>
        </Pressable>
      ))}
    </View>
  );
}

function MoreNavigator() {
  const { colors } = useTheme();
  return (
    <MoreStack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: colors.card },
        headerTintColor: colors.text,
        contentStyle: { backgroundColor: colors.background },
      }}
    >
      <MoreStack.Screen name="MoreMenu" component={MoreMenuScreen} options={{ title: 'More' }} />
      <MoreStack.Screen name="BrokerAccount" component={BrokerAccountScreen} options={{ title: 'Broker Account' }} />
      <MoreStack.Screen name="Notifications" component={NotificationsScreen} />
      <MoreStack.Screen name="Settings" component={SettingsScreen} />
    </MoreStack.Navigator>
  );
}

export function AppNavigator() {
  const { colors } = useTheme();

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerStyle: { backgroundColor: colors.card },
        headerTintColor: colors.text,
        tabBarStyle: { backgroundColor: colors.card, borderTopColor: colors.border },
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textSecondary,
        tabBarIcon: ({ focused, color }) => (
          <TabIcon label={route.name} focused={focused} color={color} />
        ),
      })}
    >
      <Tab.Screen name="Dashboard" component={DashboardScreen} />
      <Tab.Screen name="Trades" component={TradesScreen} />
      <Tab.Screen
        name="Strategies"
        component={StrategiesNavigator}
        options={{ headerShown: false }}
      />
      <Tab.Screen name="Analytics" component={AnalyticsScreen} />
      <Tab.Screen name="More" component={MoreNavigator} options={{ headerShown: false }} />
    </Tab.Navigator>
  );
}

const styles = StyleSheet.create({
  menu: { flex: 1, padding: 16 },
  menuItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 10,
  },
});
