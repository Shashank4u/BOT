import { baseApi } from './baseApi';

export interface DashboardData {
  connection: { connected: boolean; provider: string; message: string };
  account: {
    balance: number;
    equity: number;
    profit: number;
    currency: string;
    name: string;
  };
  watchlist_prices: Array<{
    symbol: string;
    bid: number;
    ask: number;
    mid: number;
    spread: number;
  }>;
  trading_mode: string;
  bot_status: string;
  market_status: string;
  disclaimer: string;
}

export interface Trade {
  id: number;
  symbol: string;
  direction: string;
  status: string;
  lot_size: number;
  entry_price: number;
  exit_price: number | null;
  profit_loss: number | null;
  opened_at: string;
  closed_at: string | null;
  entry_reason: string | null;
}

export interface Strategy {
  id: number;
  name: string;
  description: string | null;
  status: string;
  strategy_type: string;
  symbols: string[];
  timeframes: string[];
  params: Record<string, unknown>;
  stop_loss_pips: number | null;
  take_profit_pips: number | null;
}

export interface AnalyticsOverview {
  period_days: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  average_win: number;
  average_loss: number;
  current_balance: number;
}

export interface EquityCurve {
  days: number;
  points: Array<{ time: string; equity: number; pnl?: number }>;
}

export interface Notification {
  id: number;
  title: string;
  message: string;
  category: string;
  is_read: boolean;
  created_at: string;
}

export interface RiskSettings {
  max_risk_per_trade: number;
  max_daily_loss: number;
  max_open_trades: number;
  live_trading_confirmed: boolean;
  trading_mode: string;
}

export const api = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getDashboard: builder.query<DashboardData, void>({
      query: () => '/dashboard',
      providesTags: ['Dashboard'],
    }),
    getTrades: builder.query<Trade[], string | void>({
      query: (status) => `/orders/trades${status ? `?status=${status}` : ''}`,
      providesTags: ['Trades'],
    }),
    getStrategies: builder.query<Strategy[], void>({
      query: () => '/strategies',
      providesTags: ['Strategies'],
    }),
    seedStrategies: builder.mutation<{ created: number }, void>({
      query: () => ({ url: '/strategies/seed-samples', method: 'POST' }),
      invalidatesTags: ['Strategies'],
    }),
    createStrategy: builder.mutation<Strategy, Record<string, unknown>>({
      query: (body) => ({ url: '/strategies', method: 'POST', body }),
      invalidatesTags: ['Strategies'],
    }),
    getAnalyticsOverview: builder.query<AnalyticsOverview, number | void>({
      query: (days = 30) => `/analytics/overview?days=${days}`,
      providesTags: ['Analytics'],
    }),
    getEquityCurve: builder.query<EquityCurve, number | void>({
      query: (days = 30) => `/analytics/equity-curve?days=${days}`,
      providesTags: ['Analytics'],
    }),
    getDailyPnl: builder.query<{ series: Array<{ date: string; pnl: number }> }, void>({
      query: () => '/analytics/daily-pnl?days=30',
      providesTags: ['Analytics'],
    }),
    getRiskSettings: builder.query<RiskSettings, void>({
      query: () => '/risk/settings',
      providesTags: ['Risk'],
    }),
    updateRiskSettings: builder.mutation<RiskSettings, Partial<RiskSettings>>({
      query: (body) => ({ url: '/risk/settings', method: 'PATCH', body }),
      invalidatesTags: ['Risk'],
    }),
    confirmLiveTrading: builder.mutation<void, void>({
      query: () => ({ url: '/risk/confirm-live', method: 'POST' }),
      invalidatesTags: ['Risk', 'Dashboard'],
    }),
    getNotifications: builder.query<Notification[], void>({
      query: () => '/notifications?limit=50',
      providesTags: ['Notifications'],
    }),
    markAllNotificationsRead: builder.mutation<{ marked_read: number }, void>({
      query: () => ({ url: '/notifications/read-all', method: 'POST' }),
      invalidatesTags: ['Notifications'],
    }),
    placeMarketOrder: builder.mutation<
      { success: boolean; message: string },
      { symbol: string; side: string; lot_size: number; stop_loss_pips?: number }
    >({
      query: (body) => ({ url: '/orders/market', method: 'POST', body }),
      invalidatesTags: ['Trades', 'Dashboard', 'Notifications', 'Analytics'],
    }),
    runScanner: builder.mutation<{ results: Array<{ symbol: string; signal: string; score: number }> }, void>({
      query: () => ({ url: '/scanner/run', method: 'POST', body: { save: false } }),
    }),
    aiChat: builder.mutation<{ reply: string }, { message: string }>({
      query: (body) => ({ url: '/ai/chat', method: 'POST', body }),
    }),
  }),
});

export const {
  useGetDashboardQuery,
  useGetTradesQuery,
  useGetStrategiesQuery,
  useSeedStrategiesMutation,
  useCreateStrategyMutation,
  useGetAnalyticsOverviewQuery,
  useGetEquityCurveQuery,
  useGetDailyPnlQuery,
  useGetRiskSettingsQuery,
  useUpdateRiskSettingsMutation,
  useConfirmLiveTradingMutation,
  useGetNotificationsQuery,
  useMarkAllNotificationsReadMutation,
  usePlaceMarketOrderMutation,
  useRunScannerMutation,
  useAiChatMutation,
} = api;
