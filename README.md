# Trading App on Railway

One URL for **Backtesting**, **Live Trading**, and **Custom Code**.

**Live URL:** https://pythontest-production-9440.up.railway.app/

## Pages

| URL | What it does |
|-----|----------------|
| `/` | Dashboard home |
| `/backtest` | Run backtest on CSV (upload or demo `yesbank_5m.csv`) |
| `/live` | Dhan live strategy (Yes Bank) — use **Dry Run** first |
| `/code` | Paste & run Python |

## Railway Variables

| Variable | Required for |
|----------|----------------|
| `DHAN_CLIENT_ID` | Real live trading |
| `DHAN_ACCESS_TOKEN` | Real live trading |
| `GITHUB_TOKEN` | Save to GitHub button (optional) |

## Live trading tips

- Keep **Dry Run** checked until ready for real orders
- **Instant test** runs buy/sell in ~5 seconds (good for cloud testing)
- Uncheck Instant to use real market times (will wait until buy/sell time)

## Deploy

Push to [github.com/Ak4ni23008/python_test](https://github.com/Ak4ni23008/python_test) → Railway auto-redeploys.
