import {
  BaseQueryFn,
  createApi,
  FetchArgs,
  fetchBaseQuery,
  FetchBaseQueryError,
} from '@reduxjs/toolkit/query/react';
import type { SettingsState } from '../settingsSlice';

type ApiRootState = { settings: SettingsState };

export const dynamicBaseQuery: BaseQueryFn<
  string | FetchArgs,
  unknown,
  FetchBaseQueryError
> = async (args, api, extraOptions) => {
  const state = api.getState() as ApiRootState;
  const baseUrl = state.settings.apiBaseUrl.replace(/\/$/, '');

  const rawBaseQuery = fetchBaseQuery({
    baseUrl,
    prepareHeaders: (headers) => {
      const key = state.settings.apiKey;
      if (key) headers.set('X-API-Key', key);
      return headers;
    },
  });

  return rawBaseQuery(args, api, extraOptions);
};

export const baseApi = createApi({
  reducerPath: 'api',
  baseQuery: dynamicBaseQuery,
  tagTypes: [
    'Dashboard',
    'Trades',
    'Strategies',
    'Risk',
    'Notifications',
    'Analytics',
    'Journal',
  ],
  endpoints: () => ({}),
});
