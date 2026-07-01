"""Risk calculators — lot size, margin, risk/reward."""

from app.trading.risk.types import MarginResult, PositionSizeResult, RiskRewardResult


def pip_size(symbol: str) -> float:
    """Return pip size for a symbol."""
    symbol = symbol.upper()
    if "JPY" in symbol:
        return 0.01
    if symbol in ("XAUUSD", "XAGUSD"):
        return 0.1
    if symbol in ("BTCUSD", "ETHUSD", "US30", "NAS100"):
        return 1.0
    return 0.0001


def pip_value_per_lot(symbol: str, price: float | None = None) -> float:
    """
    Approximate pip value per standard lot in USD.
    Simplified for major pairs — sufficient for risk sizing.
    """
    symbol = symbol.upper()
    if symbol == "XAUUSD":
        return 10.0
    if symbol == "XAGUSD":
        return 5.0
    if "JPY" in symbol:
        return 6.5
    if symbol in ("BTCUSD", "ETHUSD"):
        return 1.0
    if symbol in ("US30", "NAS100"):
        return 1.0
    return 10.0  # Standard forex lot ~$10/pip


def calculate_lot_size(
    balance: float,
    risk_percent: float,
    stop_loss_pips: float,
    symbol: str,
) -> PositionSizeResult:
    """Calculate position size based on account risk percentage."""
    if stop_loss_pips <= 0:
        raise ValueError("Stop loss pips must be positive")
    if risk_percent <= 0 or risk_percent > 10:
        raise ValueError("Risk percent must be between 0 and 10")

    risk_amount = balance * (risk_percent / 100)
    pv = pip_value_per_lot(symbol)
    raw_lots = risk_amount / (stop_loss_pips * pv)
    lot_size = round(max(0.01, min(raw_lots, 100.0)), 2)

    return PositionSizeResult(
        lot_size=lot_size,
        risk_amount=round(risk_amount, 2),
        risk_percent=risk_percent,
        stop_loss_pips=stop_loss_pips,
        pip_value=pv,
        symbol=symbol.upper(),
    )


def calculate_risk_reward(
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    symbol: str,
    side: str = "buy",
) -> RiskRewardResult:
    """Calculate risk/reward ratio from entry, SL, and TP."""
    pip = pip_size(symbol)
    if side == "buy":
        risk_pips = abs(entry_price - stop_loss) / pip
        reward_pips = abs(take_profit - entry_price) / pip
    else:
        risk_pips = abs(stop_loss - entry_price) / pip
        reward_pips = abs(entry_price - take_profit) / pip

    rr = reward_pips / risk_pips if risk_pips > 0 else 0.0
    return RiskRewardResult(
        risk_pips=round(risk_pips, 1),
        reward_pips=round(reward_pips, 1),
        risk_reward_ratio=round(rr, 2),
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
    )


def calculate_margin(
    lot_size: float,
    symbol: str,
    price: float,
    leverage: int,
    free_margin: float,
) -> MarginResult:
    """Estimate required margin for a position."""
    symbol = symbol.upper()
    # Contract size approximation
    contract_size = 100000 if symbol not in ("XAUUSD", "XAGUSD", "BTCUSD", "ETHUSD", "US30", "NAS100") else 100
    if symbol == "XAUUSD":
        contract_size = 100
    elif symbol in ("BTCUSD", "ETHUSD"):
        contract_size = 1
    elif symbol in ("US30", "NAS100"):
        contract_size = 1

    required = (lot_size * contract_size * price) / leverage
    level = ((free_margin + required) / required * 100) if required > 0 else 0

    return MarginResult(
        required_margin=round(required, 2),
        free_margin=round(free_margin, 2),
        margin_level_after=round(level, 2),
        lot_size=lot_size,
        leverage=leverage,
        symbol=symbol,
    )
