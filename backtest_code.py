# Example backtest script — edit and run from Backtesting → Write Code tab
from backtest_20min import BacktestConfig, backtest

CSV = "yesbank_5m.csv"  # change path or upload via Form tab

cfg = BacktestConfig(
    csv_path=CSV,
    entry_mode="buy_0915_sell_0935",
    entry_price="open",
    exit_price="open",
    hold_minutes=20,
    quantity=1,
    brokerage_per_trade=20.0,
    slippage_bps=5.0,
)

trades, stats = backtest(cfg)

print("=== STATS ===")
for k, v in stats.items():
    print(f"{k}: {v}")

print("\n=== LAST 10 TRADES ===")
if len(trades):
    print(trades.tail(10).to_string(index=False))
else:
    print("No trades.")
