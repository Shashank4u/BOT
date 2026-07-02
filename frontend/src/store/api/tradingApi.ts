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
  active_strategies: number;
  auto_trading_enabled: boolean;
  market_status: string;
  disclaimer: string;
}

export interface AutoTradingStatus {
  enabled: boolean;
  interval_seconds: number;
  min_confidence: number;
  bot_status: string;
  active_strategies: number;
  last_scan_at: string | null;
  last_message: string | null;
  last_error: string | null;
  orders_placed_last_scan: number;
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

export interface BrokerAccount {
  id: number;
  name: string;
  broker: string;
  account_type: string;
  mt5_login: number;
  mt5_server: string;
  currency: string;
  leverage: number;
  balance: number;
  equity: number;
  margin: number;
  free_margin: number;
  is_active: boolean;
  is_connected: boolean;
  created_at: string | null;
}

export interface MarketStatus {
  connected: boolean;
  provider: string;
  server: string | null;
  login: number | null;
  message: string;
}

export interface BrokerConnectResult {
  account: BrokerAccount;
  connection: MarketStatus;
  message: string;
}
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
    getMarketStatus: builder.query<MarketStatus, void>({
      query: () => '/market/status',
      providesTags: ['Broker'],
    }),
    getBrokerAccounts: builder.query<BrokerAccount[], void>({
      query: () => '/accounts',
      providesTags: ['Broker'],
    }),
    getActiveBrokerAccount: builder.query<BrokerAccount | null, void>({
      query: () => '/accounts/active',
      providesTags: ['Broker'],
    }),
    addBrokerAccount: builder.mutation<BrokerConnectResult, Record<string, unknown>>({
      query: (body) => ({ url: '/accounts', method: 'POST', body }),
      invalidatesTags: ['Broker', 'Dashboard'],
    }),
    connectBrokerAccount: builder.mutation<BrokerConnectResult, number>({
      query: (id) => ({ url: `/accounts/${id}/connect`, method: 'POST' }),
      invalidatesTags: ['Broker', 'Dashboard'],
    }),
    disconnectBroker: builder.mutation<{ message: string; connection: MarketStatus }, void>({
      query: () => ({ url: '/accounts/disconnect', method: 'POST' }),
      invalidatesTags: ['Broker', 'Dashboard'],
    }),
    deleteBrokerAccount: builder.mutation<void, number>({
      query: (id) => ({ url: `/accounts/${id}`, method: 'DELETE' }),
      invalidatesTags: ['Broker', 'Dashboard'],
    }),
    getTrades: builder.query<Trade[], string | void>({
      query: (status) => `/orders/trades${status ? `?status=${status}` : ''}`,
      providesTags: ['Trades'],
      refetchOnMountOrArgChange: true,
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
    updateStrategy: builder.mutation<Strategy, { id: number; body: Record<string, unknown> }>({
      query: ({ id, body }) => ({ url: `/strategies/${id}`, method: 'PATCH', body }),
      invalidatesTags: ['Strategies', 'Dashboard'],
    }),
    getAutoTradingStatus: builder.query<AutoTradingStatus, void>({
      query: () => '/auto-trading/status',
      providesTags: ['AutoTrading'],
    }),
    startAutoTrading: builder.mutation<AutoTradingStatus, void>({
      query: () => ({ url: '/auto-trading/start', method: 'POST' }),
      invalidatesTags: ['AutoTrading', 'Dashboard', 'Trades', 'Notifications'],
    }),
    stopAutoTrading: builder.mutation<AutoTradingStatus, void>({
      query: () => ({ url: '/auto-trading/stop', method: 'POST' }),
      invalidatesTags: ['AutoTrading', 'Dashboard'],
    }),
    runAutoTradingOnce: builder.mutation<
      { scanned: number; orders_placed: number },
      void
    >({
      query: () => ({ url: '/auto-trading/run-once', method: 'POST' }),
      invalidatesTags: ['AutoTrading', 'Dashboard', 'Trades', 'Notifications', 'Analytics'],
    }),
    updateAutoTradingSettings: builder.mutation<
      AutoTradingStatus,
      { interval_seconds?: number; min_confidence?: number }
    >({
      query: (body) => ({ url: '/auto-trading/settings', method: 'PATCH', body }),
      invalidatesTags: ['AutoTrading'],
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
  useGetMarketStatusQuery,
  useGetBrokerAccountsQuery,
  useGetActiveBrokerAccountQuery,
  useAddBrokerAccountMutation,
  useConnectBrokerAccountMutation,
  useDisconnectBrokerMutation,
  useDeleteBrokerAccountMutation,
  useGetTradesQuery,
  useGetStrategiesQuery,
  useSeedStrategiesMutation,
  useCreateStrategyMutation,
  useUpdateStrategyMutation,
  useGetAutoTradingStatusQuery,
  useStartAutoTradingMutation,
  useStopAutoTradingMutation,
  useRunAutoTradingOnceMutation,
  useUpdateAutoTradingSettingsMutation,
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
