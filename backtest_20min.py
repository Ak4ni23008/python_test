from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd


EntryMode = Literal["first_bar_each_day", "every_bar", "buy_0915_sell_0935"]
PriceField = Literal["open", "close"]


@dataclass(frozen=True)
class BacktestConfig:
    csv_path: str
    entry_mode: EntryMode = "first_bar_each_day"
    entry_price: PriceField = "open"
    exit_price: PriceField = "open"
    hold_minutes: int = 20
    bar_minutes: int = 5
    quantity: int = 1
    brokerage_per_trade: float = 0.0  # set if you want fixed cost per entry/exit
    slippage_bps: float = 0.0  # 10 bps = 0.10% (applied on both entry and exit)
    self_check_samples: int = 0


def _load_ohlc(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    required = {"date", "open", "high", "low", "close"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {sorted(missing)}. Found: {list(df.columns)}")

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    for c in ["open", "high", "low", "close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["date", "open", "high", "low", "close"])
    return df


def _apply_slippage(price: pd.Series, side: Literal["buy", "sell"], bps: float) -> pd.Series:
    if bps <= 0:
        return price
    mult = 1.0 + (bps / 10_000.0) if side == "buy" else 1.0 - (bps / 10_000.0)
    return price * mult


def _self_check_strict_times(
    df: pd.DataFrame,
    trades: pd.DataFrame,
    entry_price_field: PriceField,
    exit_price_field: PriceField,
    samples: int,
    seed: int = 42,
) -> None:
    if samples <= 0 or len(trades) == 0:
        return

    samples = min(samples, len(trades))
    rng = np.random.default_rng(seed)
    idx = rng.choice(trades.index.to_numpy(), size=samples, replace=False)
    df_idx = df.set_index("date", drop=False)

    mismatches: list[str] = []
    for i in idx:
        t = trades.loc[i]
        e_dt = pd.Timestamp(t["entry_time"])
        x_dt = pd.Timestamp(t["exit_time"])

        if e_dt not in df_idx.index or x_dt not in df_idx.index:
            mismatches.append(f"missing row for {e_dt} or {x_dt}")
            continue

        e_px = float(df_idx.loc[e_dt, entry_price_field])
        x_px = float(df_idx.loc[x_dt, exit_price_field])

        if not np.isclose(e_px, float(t["entry_price"]), rtol=0, atol=1e-9):
            mismatches.append(f"entry price mismatch @ {e_dt}: csv={e_px} trade={t['entry_price']}")
        if not np.isclose(x_px, float(t["exit_price"]), rtol=0, atol=1e-9):
            mismatches.append(f"exit price mismatch @ {x_dt}: csv={x_px} trade={t['exit_price']}")

        if e_dt.strftime("%H:%M") != "09:15" or x_dt.strftime("%H:%M") != "09:35":
            mismatches.append(f"time mismatch: entry={e_dt} exit={x_dt}")

    if mismatches:
        raise AssertionError("Self-check failed:\n" + "\n".join(mismatches[:20]))


def backtest(cfg: BacktestConfig) -> tuple[pd.DataFrame, dict]:
    df = _load_ohlc(cfg.csv_path)

    hold_bars = int(round(cfg.hold_minutes / cfg.bar_minutes))
    if hold_bars <= 0:
        raise ValueError("hold_minutes must be > 0")

    if cfg.hold_minutes % cfg.bar_minutes != 0:
        raise ValueError(
            f"hold_minutes ({cfg.hold_minutes}) must be a multiple of bar_minutes ({cfg.bar_minutes})."
        )

    if cfg.entry_mode == "buy_0915_sell_0935":
        # Strict: enter only at 09:15 and exit at 09:35 of the same day.
        if cfg.bar_minutes != 5 or cfg.hold_minutes != 20:
            raise ValueError("buy_0915_sell_0935 requires --bar-minutes 5 and --hold-minutes 20")

        df["day"] = df["date"].dt.date
        df["hhmm"] = df["date"].dt.strftime("%H:%M")

        entry = df[df["hhmm"] == "09:15"].copy()
        exit_ = df[df["hhmm"] == "09:35"].copy()

        days_total = int(df["day"].nunique())
        days_with_0915 = int(entry["day"].nunique())
        days_with_0935 = int(exit_["day"].nunique())
        dup_0915_days = int(entry["day"].value_counts().gt(1).sum())
        dup_0935_days = int(exit_["day"].value_counts().gt(1).sum())
        if dup_0915_days or dup_0935_days:
            raise ValueError(
                "CSV has duplicate timestamps for strict mode. "
                f"duplicate 09:15 days={dup_0915_days}, duplicate 09:35 days={dup_0935_days}"
            )

        merged = entry.merge(
            exit_[["day", "date", cfg.exit_price]],
            on="day",
            suffixes=("_entry", "_exit"),
            how="inner",
        )

        entry_dt = merged["date_entry"].to_numpy()
        exit_dt = merged["date_exit"].to_numpy()

        entry_px_raw = merged[f"{cfg.entry_price}_entry"].to_numpy(dtype=float)
        exit_px_raw = merged[f"{cfg.exit_price}_exit"].to_numpy(dtype=float)
    elif cfg.entry_mode == "first_bar_each_day":
        df["day"] = df["date"].dt.date
        entry_idx = df.groupby("day", sort=False).head(1).index.to_numpy()
        exit_idx = entry_idx + hold_bars
        valid = exit_idx < len(df)
        entry_idx = entry_idx[valid]
        exit_idx = exit_idx[valid]

        entry_dt = df.loc[entry_idx, "date"].to_numpy()
        exit_dt = df.loc[exit_idx, "date"].to_numpy()

        entry_px_raw = df.loc[entry_idx, cfg.entry_price].to_numpy(dtype=float)
        exit_px_raw = df.loc[exit_idx, cfg.exit_price].to_numpy(dtype=float)
    elif cfg.entry_mode == "every_bar":
        entry_idx = df.index.to_numpy()
        exit_idx = entry_idx + hold_bars
        valid = exit_idx < len(df)
        entry_idx = entry_idx[valid]
        exit_idx = exit_idx[valid]

        entry_dt = df.loc[entry_idx, "date"].to_numpy()
        exit_dt = df.loc[exit_idx, "date"].to_numpy()

        entry_px_raw = df.loc[entry_idx, cfg.entry_price].to_numpy(dtype=float)
        exit_px_raw = df.loc[exit_idx, cfg.exit_price].to_numpy(dtype=float)
    else:
        raise ValueError(f"Unknown entry_mode: {cfg.entry_mode}")

    entry_px = _apply_slippage(pd.Series(entry_px_raw), "buy", cfg.slippage_bps).to_numpy()
    exit_px = _apply_slippage(pd.Series(exit_px_raw), "sell", cfg.slippage_bps).to_numpy()

    qty = float(cfg.quantity)
    gross_pnl = (exit_px - entry_px) * qty
    costs = (2.0 * cfg.brokerage_per_trade) * np.ones_like(gross_pnl, dtype=float)
    net_pnl = gross_pnl - costs

    trades = pd.DataFrame(
        {
            "entry_time": entry_dt,
            "exit_time": exit_dt,
            "entry_price": entry_px,
            "exit_price": exit_px,
            "quantity": cfg.quantity,
            "gross_pnl": gross_pnl,
            "costs": costs,
            "net_pnl": net_pnl,
            "return_pct": (exit_px / entry_px - 1.0) * 100.0,
        }
    )

    equity = trades["net_pnl"].cumsum()
    max_dd = (equity - equity.cummax()).min() if len(equity) else 0.0

    stats = {
        "bars": int(len(df)),
        "trades": int(len(trades)),
        "win_rate_pct": float((trades["net_pnl"] > 0).mean() * 100.0) if len(trades) else 0.0,
        "total_net_pnl": float(trades["net_pnl"].sum()) if len(trades) else 0.0,
        "avg_net_pnl": float(trades["net_pnl"].mean()) if len(trades) else 0.0,
        "max_drawdown": float(max_dd),
        "best_trade": float(trades["net_pnl"].max()) if len(trades) else 0.0,
        "worst_trade": float(trades["net_pnl"].min()) if len(trades) else 0.0,
    }

    if cfg.entry_mode == "buy_0915_sell_0935":
        stats.update(
            {
                "days_total": days_total,
                "days_with_0915": days_with_0915,
                "days_with_0935": days_with_0935,
                "days_tradable_0915_and_0935": int(len(trades)),
                "days_missing_0915_or_0935": int(days_total - len(trades)),
            }
        )

        _self_check_strict_times(
            df=df,
            trades=trades,
            entry_price_field=cfg.entry_price,
            exit_price_field=cfg.exit_price,
            samples=cfg.self_check_samples,
        )

    return trades, stats


def main() -> int:
    p = argparse.ArgumentParser(description="Backtest 20-minute (4x5m) hold strategy on OHLC CSV.")
    p.add_argument("--csv", required=True, help="Path to CSV (date,open,high,low,close,volume).")
    p.add_argument(
        "--entry-mode",
        default="buy_0915_sell_0935",
        choices=["buy_0915_sell_0935", "first_bar_each_day", "every_bar"],
    )
    p.add_argument("--entry-price", default="open", choices=["open", "close"])
    p.add_argument("--exit-price", default="open", choices=["open", "close"])
    p.add_argument("--qty", type=int, default=1)
    p.add_argument("--hold-minutes", type=int, default=20)
    p.add_argument("--bar-minutes", type=int, default=5)
    p.add_argument("--brokerage", type=float, default=0.0, help="Fixed cost per order (entry or exit).")
    p.add_argument("--slippage-bps", type=float, default=0.0, help="Applied on both entry and exit.")
    p.add_argument(
        "--self-check",
        type=int,
        default=0,
        help="If >0, randomly verifies N trades match raw CSV rows (strict mode only).",
    )
    p.add_argument("--out", default="", help="Optional output trades CSV path.")
    args = p.parse_args()

    cfg = BacktestConfig(
        csv_path=args.csv,
        entry_mode=args.entry_mode,
        entry_price=args.entry_price,
        exit_price=args.exit_price,
        hold_minutes=args.hold_minutes,
        bar_minutes=args.bar_minutes,
        quantity=args.qty,
        brokerage_per_trade=args.brokerage,
        slippage_bps=args.slippage_bps,
        self_check_samples=args.self_check,
    )

    trades, stats = backtest(cfg)

    print("\n=== STATS ===")
    for k, v in stats.items():
        print(f"{k}: {v}")

    print("\n=== LAST 10 TRADES ===")
    if len(trades):
        print(trades.tail(10).to_string(index=False))
    else:
        print("No trades (not enough bars for hold time).")

    if args.out:
        trades.to_csv(args.out, index=False)
        print(f"\nSaved trades to: {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
