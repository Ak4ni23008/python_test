# Backtesting (20-minute hold) from your NSE CSV

This project **does backtesting only** using your `NIFTY 100_5minute.csv`.

It does **not** place real orders on Dhan. (Your Dhan `CLIENT_ID` / `ACCESS_TOKEN` should never be used for backtesting.)

## Setup (VS Code)

1. Open this folder in VS Code: `back_testing`
2. Create a venv and install deps:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run backtest

Default (your requirement): **buy at 09:15 and sell at 09:35** (same day), at market prices (`open` by default):

```bash
python backtest_20min.py --csv "C:\Users\akash\Downloads\NIFTY 100_5minute.csv" --entry-mode buy_0915_sell_0935 --entry-price open --exit-price open
```

If you want “first bar of the day” (not strict 09:15), use:

```bash
python backtest_20min.py --csv "C:\Users\akash\Downloads\NIFTY 100_5minute.csv" --entry-mode first_bar_each_day --hold-minutes 20 --entry-price open --exit-price open
```

More aggressive example (enter every candle, hold 20 minutes):

```bash
python backtest_20min.py --csv "C:\Users\akash\Downloads\NIFTY 100_5minute.csv" --entry-mode every_bar --hold-minutes 20
```

Add costs (example: ₹5 per order + 10 bps slippage):

```bash
python backtest_20min.py --csv "C:\Users\akash\Downloads\NIFTY 100_5minute.csv" --brokerage 5 --slippage-bps 10
```

Export all trades:

```bash
python backtest_20min.py --csv "C:\Users\akash\Downloads\NIFTY 100_5minute.csv" --out trades.csv
```

## Where to put your “algo”

Right now, `--entry-mode` controls *when* we buy:

- `buy_0915_sell_0935`: buys at 09:15, sells at 09:35 (strict).
- `first_bar_each_day`: buys the first candle of each day, sells after 20 minutes.
- `every_bar`: buys every candle, sells each after 20 minutes.

If you tell me your real entry rule (example: “buy when close crosses above 20 EMA”), I’ll add it as a new `--entry-mode`.

## Run in the cloud (Railway)

To host the dashboard on Railway instead of your laptop, see **[RAILWAY.md](./RAILWAY.md)** for step-by-step setup (GitHub → Railway → env vars → public URL).

Quick start after pushing to GitHub:

1. [railway.app](https://railway.app) → New Project → Deploy from GitHub.
2. Add variables: `DHAN_CLIENT_ID`, `DHAN_ACCESS_TOKEN`.
3. Generate a public domain and open it.
4. Upload your CSV in the Backtesting page (cloud has no access to `C:\...` paths).

