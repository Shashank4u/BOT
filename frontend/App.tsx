import React, { useEffect, useState } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { NavigationContainer, DarkTheme, DefaultTheme } from '@react-navigation/native';
import { StatusBar } from 'expo-status-bar';
import { Provider } from 'react-redux';
import { AppNavigator } from './src/navigation/AppNavigator';
import { loadStoredSettings, store } from './src/store';
import { useAppDispatch } from './src/store/hooks';
import { setApiBaseUrl, setApiKey, setDarkMode } from './src/store/settingsSlice';
import { ThemeProvider, useTheme } from './src/theme/ThemeContext';

function Bootstrap({ children }: { children: React.ReactNode }) {
  const dispatch = useAppDispatch();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    loadStoredSettings().then((stored) => {
      if (stored.apiBaseUrl) dispatch(setApiBaseUrl(stored.apiBaseUrl));
      if (stored.apiKey) dispatch(setApiKey(stored.apiKey));
      if (stored.darkMode) dispatch(setDarkMode(stored.darkMode));
      setReady(true);
    });
  }, [dispatch]);

  if (!ready) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return <>{children}</>;
}

function RootNav() {
  const { isDark, colors } = useTheme();
  const navTheme = isDark
    ? { ...DarkTheme, colors: { ...DarkTheme.colors, background: colors.background, card: colors.card } }
    : { ...DefaultTheme, colors: { ...DefaultTheme.colors, background: colors.background, card: colors.card } };

  return (
    <NavigationContainer theme={navTheme}>
      <StatusBar style={isDark ? 'light' : 'dark'} />
      <AppNavigator />
    </NavigationContainer>
  );
}

export default function App() {
  return (
    <Provider store={store}>
      <ThemeProvider>
        <Bootstrap>
          <RootNav />
        </Bootstrap>
      </ThemeProvider>
    </Provider>
  );
}
