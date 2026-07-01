"""Default symbols and trading constants."""

DEFAULT_SYMBOLS = [
    "XAUUSD",   # Gold
    "XAGUSD",   # Silver
    "BTCUSD",
    "ETHUSD",
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "US30",
    "NAS100",
]

# Base prices for mock data (approximate, for development only)
MOCK_BASE_PRICES: dict[str, float] = {
    "XAUUSD": 2650.0,
    "XAGUSD": 31.5,
    "BTCUSD": 97000.0,
    "ETHUSD": 3400.0,
    "EURUSD": 1.0850,
    "GBPUSD": 1.2650,
    "USDJPY": 149.50,
    "AUDUSD": 0.6550,
    "US30": 42000.0,
    "NAS100": 19500.0,
}

# Typical spreads in price units (mock)
MOCK_SPREADS: dict[str, float] = {
    "XAUUSD": 0.30,
    "XAGUSD": 0.03,
    "BTCUSD": 50.0,
    "ETHUSD": 2.0,
    "EURUSD": 0.00012,
    "GBPUSD": 0.00015,
    "USDJPY": 0.012,
    "AUDUSD": 0.00014,
    "US30": 2.0,
    "NAS100": 1.5,
}
