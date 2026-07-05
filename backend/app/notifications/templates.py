"""Notification message templates."""

from app.models.trade import Trade


def trade_opened_message(trade: Trade, is_demo: bool = True) -> str:
    mode = "DEMO" if is_demo else "LIVE"
    sl = f"{float(trade.stop_loss):.5f}" if trade.stop_loss else "—"
    tp = f"{float(trade.take_profit):.5f}" if trade.take_profit else "—"
    return (
        f"<b>Trade Opened</b> [{mode}]\n"
        f"Symbol: <b>{trade.symbol}</b>\n"
        f"Direction: {trade.direction.upper()}\n"
        f"Lots: {float(trade.lot_size)}\n"
        f"Entry: {float(trade.entry_price):.5f}\n"
        f"SL: {sl}\n"
        f"TP: {tp}\n"
        f"Reason: {trade.entry_reason or 'N/A'}"
    )


def trade_closed_message(trade: Trade, is_demo: bool = True) -> str:
    mode = "DEMO" if is_demo else "LIVE"
    pnl = float(trade.profit_loss or 0)
    emoji = "✅" if pnl >= 0 else "❌"
    exit_px = f"{float(trade.exit_price):.5f}" if trade.exit_price else "—"
    return (
        f"<b>Trade Closed</b> [{mode}] {emoji}\n"
        f"Symbol: <b>{trade.symbol}</b>\n"
        f"Direction: {trade.direction.upper()}\n"
        f"Entry: {float(trade.entry_price):.5f}\n"
        f"Exit: {exit_px}\n"
        f"P/L: <b>${pnl:+.2f}</b>\n"
        f"Reason: {trade.exit_reason or 'N/A'}"
    )


def risk_alert_message(violations: list[str]) -> str:
    lines = "\n".join(f"• {v}" for v in violations)
    return f"<b>⚠️ Risk Alert</b>\nTrade blocked:\n{lines}"


def report_message(report_type: str, summary: str) -> str:
    return f"<b>{report_type.title()} Report</b>\n\n{summary[:3500]}"


def test_message() -> str:
    return (
        "<b>AI Trading Assistant</b>\n"
        "Telegram notifications are working.\n"
        "You will receive trade open/close alerts and risk warnings here."
    )
