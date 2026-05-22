"""Single-tick live simulation step — called by cloud worker."""

from __future__ import annotations

from datetime import datetime

from app.engines.indicators import rsi
from app.engines.strategy_schema import StrategyConfig
from app.mock_data.generator import simulate_live_tick


class LiveState:
    """In-memory indicator buffer per deployment (worker persists to DB)."""

    def __init__(self) -> None:
        self.prices: list[float] = []
        self.rsi_values: list[float] = []
        self.last_macd: float | None = None


_states: dict[str, LiveState] = {}


def get_state(deployment_id: str) -> LiveState:
    if deployment_id not in _states:
        _states[deployment_id] = LiveState()
    return _states[deployment_id]


def clear_state(deployment_id: str) -> None:
    _states.pop(deployment_id, None)


def process_tick(
    config: StrategyConfig,
    deployment_id: str,
    last_price: float,
    tick: int,
    open_position: bool,
    entry_price: float | None,
) -> dict:
    """
    One cloud worker tick: update price, evaluate template strategy, return events.
    """
    price = simulate_live_tick(last_price if last_price > 0 else 85.0, tick)
    state = get_state(deployment_id)
    state.prices.append(price)
    if len(state.prices) > 200:
        state.prices = state.prices[-200:]

    events: list[dict] = []
    side = None
    pnl_delta = 0.0

    if config.strategy_type == "RSI" and len(state.prices) >= 15:
        import pandas as pd

        series = pd.Series(state.prices)
        r = float(rsi(series).iloc[-1])
        prev = float(rsi(series).iloc[-2]) if len(series) > 15 else r
        state.rsi_values.append(r)

        buy_hit = (
            (config.buy_condition == "below" and r < config.buy_value)
            or (config.buy_condition == "crosses_below" and prev >= config.buy_value > r)
        )
        sell_hit = (
            (config.sell_condition == "above" and r > config.sell_value)
            or (config.sell_condition == "crosses_above" and prev <= config.sell_value < r)
        )

        if buy_hit and not open_position:
            side = "buy"
            events.append({"type": "buy", "price": price, "rsi": round(r, 2)})
        elif sell_hit and open_position:
            side = "sell"
            if entry_price:
                pnl_delta = (price - entry_price) * config.quantity
            events.append({"type": "sell", "price": price, "rsi": round(r, 2), "pnl": round(pnl_delta, 2)})

    elif config.strategy_type == "TIME_BASED":
        now = datetime.utcnow()
        h, m = now.hour, now.minute
        t = f"{h:02d}:{m:02d}"
        if t >= config.buy_time and t < config.sell_time and not open_position:
            side = "buy"
            events.append({"type": "buy", "price": price, "time": t})
        elif t >= config.sell_time and open_position:
            side = "sell"
            if entry_price:
                pnl_delta = (price - entry_price) * config.quantity
            events.append({"type": "sell", "price": price, "time": t, "pnl": round(pnl_delta, 2)})

    else:
        # MACD / SMA: simplified momentum on ticks
        if len(state.prices) >= 3:
            momentum = state.prices[-1] - state.prices[-3]
            if momentum > 0 and not open_position:
                side = "buy"
                events.append({"type": "buy", "price": price})
            elif momentum < 0 and open_position:
                side = "sell"
                if entry_price:
                    pnl_delta = (price - entry_price) * config.quantity
                events.append({"type": "sell", "price": price, "pnl": round(pnl_delta, 2)})

    return {
        "price": round(price, 2),
        "events": events,
        "side": side,
        "pnl_delta": pnl_delta,
        "timestamp": datetime.utcnow().isoformat(),
    }
