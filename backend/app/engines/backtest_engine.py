"""Template-based backtesting — no arbitrary code execution."""

from __future__ import annotations

from datetime import time as dtime

import pandas as pd

from app.engines.indicators import macd, rsi, sma
from app.engines.strategy_schema import StrategyConfig
from app.mock_data.generator import load_demo_ohlcv


def _parse_time(s: str) -> dtime:
    h, m = s.split(":")
    return dtime(int(h), int(m))


def _condition_met(val: float, prev: float, condition: str, threshold: float) -> bool:
    if condition == "below":
        return val < threshold
    if condition == "above":
        return val > threshold
    if condition == "crosses_below":
        return prev >= threshold and val < threshold
    if condition == "crosses_above":
        return prev <= threshold and val > threshold
    return False


def run_backtest(config: StrategyConfig) -> dict:
    df = load_demo_ohlcv().copy()
    close = df["close"]
    df["signal"] = 0

    if config.strategy_type == "RSI":
        df["indicator"] = rsi(close)
        for i in range(1, len(df)):
            ind, prev = df["indicator"].iloc[i], df["indicator"].iloc[i - 1]
            if pd.isna(ind) or pd.isna(prev):
                continue
            if _condition_met(ind, prev, config.buy_condition, config.buy_value):
                df.loc[df.index[i], "signal"] = 1
            elif _condition_met(ind, prev, config.sell_condition, config.sell_value):
                df.loc[df.index[i], "signal"] = -1

    elif config.strategy_type == "MACD":
        m, s, _ = macd(close, config.fast_period, config.slow_period, config.signal_period)
        df["indicator"] = m - s
        for i in range(1, len(df)):
            ind, prev = df["indicator"].iloc[i], df["indicator"].iloc[i - 1]
            if pd.isna(ind):
                continue
            if _condition_met(ind, prev, config.buy_condition, config.buy_value):
                df.loc[df.index[i], "signal"] = 1
            elif _condition_met(ind, prev, config.sell_condition, config.sell_value):
                df.loc[df.index[i], "signal"] = -1

    elif config.strategy_type == "SMA_CROSS":
        df["fast"] = sma(close, config.sma_fast)
        df["slow"] = sma(close, config.sma_slow)
        for i in range(1, len(df)):
            f, sl = df["fast"].iloc[i], df["slow"].iloc[i]
            pf, psl = df["fast"].iloc[i - 1], df["slow"].iloc[i - 1]
            if pd.isna(f) or pd.isna(sl):
                continue
            if pf <= psl and f > sl:
                df.loc[df.index[i], "signal"] = 1
            elif pf >= psl and f < sl:
                df.loc[df.index[i], "signal"] = -1

    else:  # TIME_BASED
        buy_t, sell_t = _parse_time(config.buy_time), _parse_time(config.sell_time)
        for i in range(len(df)):
            t = df["datetime"].iloc[i].time()
            if buy_t <= t < sell_t and df.loc[df.index[i], "signal"] == 0:
                if t == buy_t or (i > 0 and df["datetime"].iloc[i - 1].time() < buy_t <= t):
                    df.loc[df.index[i], "signal"] = 1
            if t >= sell_t and df.loc[df.index[i], "signal"] in (0, 1):
                if t == sell_t or (i > 0 and df["datetime"].iloc[i - 1].time() < sell_t <= t):
                    df.loc[df.index[i], "signal"] = -1

    trades = []
    position = None
    equity = 100000.0
    equity_curve = []
    peak = equity

    for i in range(len(df)):
        row = df.iloc[i]
        price = float(row["close"])
        sig = int(row["signal"])

        if sig == 1 and position is None:
            position = {"entry": price, "time": str(row["datetime"]), "qty": config.quantity}
        elif sig == -1 and position is not None:
            pnl = (price - position["entry"]) * position["qty"]
            equity += pnl
            trades.append(
                {
                    "entry_time": position["time"],
                    "exit_time": str(row["datetime"]),
                    "entry_price": position["entry"],
                    "exit_price": price,
                    "quantity": position["qty"],
                    "pnl": round(pnl, 2),
                }
            )
            position = None

        peak = max(peak, equity)
        equity_curve.append(
            {"time": str(row["datetime"]), "equity": round(equity, 2), "price": price}
        )

    drawdown_curve = []
    peak_eq = 100000.0
    for pt in equity_curve:
        peak_eq = max(peak_eq, pt["equity"])
        dd = (pt["equity"] - peak_eq) / peak_eq * 100 if peak_eq else 0
        drawdown_curve.append({"time": pt["time"], "drawdown_pct": round(dd, 4)})

    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    total_return_pct = round((equity - 100000) / 100000 * 100, 2)
    win_rate = round(len(wins) / len(trades) * 100, 2) if trades else 0.0
    max_dd = min((d["drawdown_pct"] for d in drawdown_curve), default=0.0)

    metrics = {
        "total_return_pct": total_return_pct,
        "final_equity": round(equity, 2),
        "win_rate": win_rate,
        "num_trades": len(trades),
        "avg_profit": round(sum(t["pnl"] for t in wins) / len(wins), 2) if wins else 0,
        "avg_loss": round(sum(t["pnl"] for t in losses) / len(losses), 2) if losses else 0,
        "max_drawdown_pct": round(max_dd, 2),
        "symbol": config.symbol,
        "strategy_type": config.strategy_type,
    }

    return {
        "metrics": metrics,
        "equity_curve": equity_curve[:: max(1, len(equity_curve) // 500)],
        "drawdown_curve": drawdown_curve[:: max(1, len(drawdown_curve) // 500)],
        "trades": trades,
    }
