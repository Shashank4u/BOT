"""Quick MT5 IPC diagnostic — reads credentials from .env, prints status only."""
from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import dotenv_values

import MetaTrader5 as mt5


def main() -> int:
    cfg = dotenv_values(Path(__file__).resolve().parents[1] / ".env")
    path = cfg.get("MT5_PATH") or r"C:\Program Files\MetaTrader 5\terminal64.exe"
    login = int(cfg["MT5_LOGIN"]) if cfg.get("MT5_LOGIN") else None
    server = cfg.get("MT5_SERVER") or ""
    password = cfg.get("MT5_PASSWORD") or ""

    print(f"python_bits={struct.calcsize('P') * 8}")
    print(f"mt5_path={path}")
    print(f"mt5_pkg={getattr(mt5, '__version__', 'unknown')}")

    # Test 1: attach only
    ok1 = mt5.initialize(path=path)
    err1 = mt5.last_error()
    print(f"test1_initialize_only: ok={ok1} error={err1}")
    if ok1:
        ai = mt5.account_info()
        ti = mt5.terminal_info()
        print(f"  account={ai.login if ai else None} server={ai.server if ai else None}")
        print(f"  terminal_connected={ti.connected if ti else None} trade_allowed={ti.trade_allowed if ti else None}")
        mt5.shutdown()

    # Test 2: initialize with credentials
    ok2 = mt5.initialize(path=path, login=login, password=password, server=server)
    err2 = mt5.last_error()
    print(f"test2_initialize_with_creds: ok={ok2} error={err2}")
    if ok2:
        ai = mt5.account_info()
        print(f"  account={ai.login if ai else None} balance={ai.balance if ai else None} server={ai.server if ai else None}")
        mt5.shutdown()
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
