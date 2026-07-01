"""Risk calculator unit tests."""

import pytest

from app.trading.risk.calculator import (
    calculate_lot_size,
    calculate_margin,
    calculate_risk_reward,
    pip_size,
)


class TestRiskCalculator:
    def test_pip_size_forex(self) -> None:
        assert pip_size("EURUSD") == 0.0001

    def test_pip_size_jpy(self) -> None:
        assert pip_size("USDJPY") == 0.01

    def test_pip_size_gold(self) -> None:
        assert pip_size("XAUUSD") == 0.1

    def test_calculate_lot_size(self) -> None:
        result = calculate_lot_size(10000, 1.0, 20, "EURUSD")
        assert result.lot_size >= 0.01
        assert result.risk_amount == 100.0
        assert result.risk_percent == 1.0

    def test_calculate_lot_size_invalid(self) -> None:
        with pytest.raises(ValueError):
            calculate_lot_size(10000, 1.0, 0, "EURUSD")

    def test_calculate_risk_reward_buy(self) -> None:
        result = calculate_risk_reward(1.1000, 1.0980, 1.1040, "EURUSD", "buy")
        assert result.risk_pips == 20.0
        assert result.reward_pips == 40.0
        assert result.risk_reward_ratio == 2.0

    def test_calculate_margin(self) -> None:
        result = calculate_margin(0.1, "EURUSD", 1.10, 100, 5000)
        assert result.required_margin > 0
        assert result.leverage == 100
