"""Demo historical and live mock market data."""

from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DEMO_CSV = ROOT / "yesbank_5m.csv"


def load_demo_ohlcv() -> pd.DataFrame:
    if DEMO_CSV.exists():
        df = pd.read_csv(DEMO_CSV)
        cols = {c.lower(): c for c in df.columns}
        rename = {}
        for want in ("datetime", "date", "time", "timestamp"):
            if want in cols:
                rename[cols[want]] = "datetime"
                break
        for field in ("open", "high", "low", "close", "volume"):
            if field in cols:
                rename[cols[field]] = field
        df = df.rename(columns=rename)
        if "datetime" not in df.columns:
            df["datetime"] = pd.date_range("2024-01-01", periods=len(df), freq="5min")
        else:
            df["datetime"] = pd.to_datetime(df["datetime"])
        for c in ("open", "high", "low", "close"):
            if c not in df.columns:
                df[c] = df.get("close", 100.0)
        if "volume" not in df.columns:
            df["volume"] = 100000
        return df.sort_values("datetime").reset_index(drop=True)

    return generate_synthetic_ohlcv(days=30)


def generate_synthetic_ohlcv(days: int = 30, bars_per_day: int = 75) -> pd.DataFrame:
    """Generate realistic-ish 5m OHLCV when CSV missing."""
    n = days * bars_per_day
    rng = np.random.default_rng(42)
    start = datetime(2024, 1, 1, 9, 15)
    times = [start + timedelta(minutes=5 * i) for i in range(n)]
    price = 85.0
    rows = []
    for t in times:
        ret = rng.normal(0, 0.002)
        price = max(50.0, price * (1 + ret))
        high = price * (1 + abs(rng.normal(0, 0.003)))
        low = price * (1 - abs(rng.normal(0, 0.003)))
        open_p = (high + low) / 2
        close = price
        rows.append(
            {
                "datetime": t,
                "open": round(open_p, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "volume": int(rng.integers(50000, 200000)),
            }
        )
    return pd.DataFrame(rows)


def simulate_live_tick(last_price: float, tick: int) -> float:
    """Random walk tick for live simulation."""
    drift = math.sin(tick / 15) * 0.001
    shock = random.gauss(0, 0.003)
    return max(50.0, last_price * (1 + drift + shock))
