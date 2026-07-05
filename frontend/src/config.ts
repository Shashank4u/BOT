import Constants from 'expo-constants';

export const DEFAULT_API_URL =
  process.env.EXPO_PUBLIC_API_URL ??
  (Constants.expoConfig?.extra?.apiBaseUrl as string) ??
  'http://localhost:8000/api/v1';

export const API_HELP =
  'Android emulator: http://10.0.2.2:8000/api/v1 · iOS simulator: http://localhost:8000/api/v1';
