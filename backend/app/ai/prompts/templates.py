"""Optimized AI prompt templates."""

from app.ai.prompts.system import DISCLAIMER


def trade_review_prompt(trade: dict, journal: dict | None) -> str:
    journal_section = ""
    if journal:
        journal_section = f"""
Trader notes: {journal.get('notes', 'None')}
Emotion: {journal.get('emotion', 'Not recorded')}
Lessons learned: {journal.get('lessons_learned', 'None')}
Tags: {journal.get('tags', [])}
"""
    return f"""Analyze this completed trade. Explain what happened and suggest process improvements.

TRADE DATA:
- Symbol: {trade.get('symbol')}
- Direction: {trade.get('direction')}
- Lot size: {trade.get('lot_size')}
- Entry: {trade.get('entry_price')} at {trade.get('opened_at')}
- Exit: {trade.get('exit_price')} at {trade.get('closed_at')}
- P/L: {trade.get('profit_loss')}
- Entry reason: {trade.get('entry_reason', 'Not recorded')}
- Exit reason: {trade.get('exit_reason', 'Not recorded')}
- Strategy ID: {trade.get('strategy_id', 'Manual')}
- Indicators at entry: {trade.get('indicators_snapshot', 'Not recorded')}
{journal_section}
Provide:
1. **What happened** — factual summary of the trade
2. **What went well** — if anything
3. **What could improve** — process, not prediction
4. **Risk assessment** — was position sizing appropriate?
5. **Behavioral note** — any emotional or discipline patterns

End with: "{DISCLAIMER}"
"""


def signal_explanation_prompt(signal: dict) -> str:
    return f"""Explain why this strategy signal occurred. Do NOT predict what will happen next.

SIGNAL DATA:
- Strategy: {signal.get('strategy_name')} ({signal.get('strategy_type')})
- Symbol: {signal.get('symbol')}
- Timeframe: {signal.get('timeframe')}
- Action: {signal.get('action')}
- Confidence: {signal.get('confidence')}
- Reasons: {signal.get('reasons')}
- Indicators: {signal.get('indicators')}
- Patterns: {signal.get('patterns')}
- Price: {signal.get('price')}
- Stop loss: {signal.get('stop_loss')}
- Take profit: {signal.get('take_profit')}

Explain in plain language:
1. What conditions triggered this signal
2. What the indicator/pattern values mean in context
3. What uncertainties exist (this is NOT a prediction)
4. Risk considerations before acting

End with: "{DISCLAIMER}"
"""


def period_report_prompt(report_type: str, metrics: dict, trades_summary: list) -> str:
    trades_text = "\n".join(
        f"- {t['symbol']} {t['direction']} P/L: {t.get('profit_loss', 'N/A')}"
        for t in trades_summary[:20]
    ) or "No trades in this period."
    return f"""Generate a {report_type} trading performance report based ONLY on this data.

PERIOD METRICS:
- Total trades: {metrics.get('total_trades', 0)}
- Winning: {metrics.get('winning_trades', 0)}
- Losing: {metrics.get('losing_trades', 0)}
- Win rate: {metrics.get('win_rate', 0)}%
- Total P/L: {metrics.get('total_pnl', 0)}
- Best symbol: {metrics.get('best_symbol', 'N/A')}
- Worst symbol: {metrics.get('worst_symbol', 'N/A')}
- Average hold time: {metrics.get('avg_hold_hours', 'N/A')} hours
- Consecutive losses (max): {metrics.get('max_consecutive_losses', 0)}
- Risk violations: {metrics.get('risk_violations', 0)}

TRADES:
{trades_text}

Provide:
1. **Summary** — 2-3 sentence overview
2. **Performance highlights** — what worked
3. **Areas to improve** — discipline, risk, strategy adherence
4. **Behavioral patterns** — overtrading, revenge trading, etc.
5. **Recommendations** — process improvements only, no trade signals

Do NOT predict next period performance.
End with: "{DISCLAIMER}"
"""


def journal_analysis_prompt(journals: list[dict]) -> str:
    entries = "\n".join(
        f"- Trade {j.get('trade_id')}: emotion={j.get('emotion')}, notes={j.get('notes', '')[:100]}"
        for j in journals[:15]
    ) or "No journal entries."
    return f"""Analyze these trade journal entries for behavioral patterns.

ENTRIES:
{entries}

Identify:
1. Recurring emotions and their correlation with outcomes
2. Common mistakes mentioned
3. Positive habits to reinforce
4. Suggestions for better journaling

Do NOT predict markets. End with: "{DISCLAIMER}"
"""


def chat_prompt(user_message: str, context: dict) -> str:
    return f"""The trader asks: "{user_message}"

AVAILABLE CONTEXT:
- Trading mode: {context.get('trading_mode', 'demo')}
- Open trades: {context.get('open_trades', 0)}
- Recent P/L (30d): {context.get('monthly_pnl', 0)}
- Win rate (30d): {context.get('win_rate', 'N/A')}%

Answer helpfully using only the context provided. If you lack data, say so.
Never predict prices or guarantee profits.
End with a brief risk reminder."""
