import React, { createContext, useContext, useMemo } from 'react';
import { useColorScheme } from 'react-native';
import { useAppSelector } from '../store/hooks';
import { darkColors, lightColors, ThemeColors } from './colors';

type ThemeContextValue = {
  colors: ThemeColors;
  isDark: boolean;
};

const ThemeContext = createContext<ThemeContextValue>({
  colors: darkColors,
  isDark: true,
});

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const systemScheme = useColorScheme();
  const darkMode = useAppSelector((s) => s.settings.darkMode);

  const isDark = darkMode === 'system' ? systemScheme === 'dark' : darkMode === 'dark';

  const value = useMemo(
    () => ({ colors: isDark ? darkColors : lightColors, isDark }),
    [isDark],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  return useContext(ThemeContext);
}
