import AsyncStorage from '@react-native-async-storage/async-storage';
import { combineReducers, configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import { baseApi } from './api/baseApi';
import './api/tradingApi';
import settingsReducer, { SettingsState } from './settingsSlice';

const SETTINGS_KEY = '@trading_assistant_settings';

export const loadStoredSettings = async (): Promise<Partial<SettingsState>> => {
  try {
    const raw = await AsyncStorage.getItem(SETTINGS_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
};

export const saveSettings = async (settings: SettingsState) => {
  await AsyncStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
};

const rootReducer = combineReducers({
  settings: settingsReducer,
  [baseApi.reducerPath]: baseApi.reducer,
});

export const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(baseApi.middleware),
});

setupListeners(store.dispatch);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
