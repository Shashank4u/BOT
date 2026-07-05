import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { DEFAULT_API_URL } from '../config';

export type DarkModeSetting = 'light' | 'dark' | 'system';

export interface SettingsState {
  apiBaseUrl: string;
  apiKey: string;
  darkMode: DarkModeSetting;
}

const initialState: SettingsState = {
  apiBaseUrl: DEFAULT_API_URL,
  apiKey: '',
  darkMode: 'dark',
};

const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    setApiBaseUrl(state, action: PayloadAction<string>) {
      state.apiBaseUrl = action.payload;
    },
    setApiKey(state, action: PayloadAction<string>) {
      state.apiKey = action.payload;
    },
    setDarkMode(state, action: PayloadAction<DarkModeSetting>) {
      state.darkMode = action.payload;
    },
  },
});

export const { setApiBaseUrl, setApiKey, setDarkMode } = settingsSlice.actions;
export default settingsSlice.reducer;
