"""Symbol to currency mapping for news filtering."""

SYMBOL_CURRENCIES: dict[str, list[str]] = {
    "XAUUSD": ["USD"],
    "XAGUSD": ["USD"],
    "BTCUSD": ["USD"],
    "ETHUSD": ["USD"],
    "EURUSD": ["EUR", "USD"],
    "GBPUSD": ["GBP", "USD"],
    "USDJPY": ["USD", "JPY"],
    "AUDUSD": ["AUD", "USD"],
    "US30": ["USD"],
    "NAS100": ["USD"],
    "NZDUSD": ["NZD", "USD"],
    "USDCAD": ["USD", "CAD"],
    "USDCHF": ["USD", "CHF"],
}


def currencies_for_symbol(symbol: str) -> list[str]:
    symbol = symbol.upper()
    if symbol in SYMBOL_CURRENCIES:
        return SYMBOL_CURRENCIES[symbol]
    if len(symbol) == 6:
        return [symbol[:3], symbol[3:]]
    return ["USD"]
