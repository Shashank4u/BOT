"""Trading engine exceptions."""

from app.core.exceptions import AppException


class MT5Error(AppException):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=503)


class MT5NotConnectedError(MT5Error):
    def __init__(self) -> None:
        super().__init__("Not connected to MetaTrader 5. Call /api/v1/market/connect first.")


class SymbolNotFoundError(AppException):
    def __init__(self, symbol: str) -> None:
        super().__init__(f"Symbol '{symbol}' not found or not available", status_code=404)
