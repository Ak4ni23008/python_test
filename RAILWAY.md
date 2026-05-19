# Deploy to Railway (cloud)

Run the **Streamlit dashboard** on Railway so you don't need your laptop on. Use a **second Railway service + cron** for scheduled live trading.

## What runs where

| Component | Railway service | How |
|-----------|-----------------|-----|
| Dashboard (backtest UI) | **Web service** | `Procfile` → Streamlit on `$PORT` |
| Live buy/sell at market time | **Cron job** (optional 2nd service) | Runs `live_trade_0920_0921.py` on a schedule |

> **Important:** The "Start Live Trading" button in the dashboard starts a long-running process. On Railway that often **times out** over HTTP. For real live trading in the cloud, use the **cron service** below—not the dashboard button.

---

## Step 1 — Push code to GitHub

Railway deploys from Git. In the `back_testing` folder:

```powershell
cd "C:\Users\akash\Downloads\dhan\Users\mahad\Downloads\Users\akash\OneDrive\Desktop\trading\back_testing"

git init
git add .
git commit -m "Add Railway deployment"
```

Create a repo on GitHub, then:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

`.env` is in `.gitignore` — never commit API keys.

---

## Step 2 — Create Railway project

1. Go to [railway.app](https://railway.app) and sign in (GitHub is easiest).
2. **New Project** → **Deploy from GitHub repo**.
3. Select your repo.
4. If asked for root directory, set it to `/` (repo root = `back_testing` folder contents).

Railway detects `Procfile` and installs `requirements.txt` automatically.

---

## Step 3 — Environment variables (dashboard + live)

In Railway: **your service** → **Variables** → add:

| Variable | Value |
|----------|--------|
| `DHAN_CLIENT_ID` | Your Dhan client ID |
| `DHAN_ACCESS_TOKEN` | Your Dhan access token |
| `DHAN_DISABLE_SSL_VERIFY` | `1` only if you get SSL errors (less secure) |

Copy values from your local `.env` — do not upload `.env` to Git.

---

## Step 4 — Networking & domain

1. Service → **Settings** → **Networking** → **Generate Domain**.
2. Open the URL — you should see the Streamlit dashboard.
3. Health check path should be `/` (already set in `railway.toml`).

---

## Step 5 — Backtest in the cloud

1. Open your Railway URL.
2. Go to **Backtesting**.
3. **Upload** your `NIFTY 100_5minute.csv` (or any OHLC CSV). Laptop paths like `C:\Users\...` do not exist on Railway.
4. Click **Run Backtest**.

The bundled `yesbank_5m.csv` still works if you leave the default path and don't upload a file (demo data only).

---

## Step 6 (optional) — Live trading on a schedule

Create a **second service** from the same repo:

1. In your Railway project: **+ New** → **GitHub Repo** → same repo (or **Empty Service** and link the repo).
2. **Settings** → **Deploy** → **Custom Start Command**:

```bash
python live_trade_0920_0921.py --qty 1 --buy 11:55 --sell 11:56
```

Add the same `DHAN_*` variables. Remove `--dry-run` only when you want real orders.

3. **Settings** → **Cron Schedule** (enable cron on this service).

Market times are **IST**. Railway cron uses **UTC**.

| IST (buy) | UTC cron (Mon–Fri) |
|-----------|-------------------|
| 11:55 | `25 6 * * 1-5` |

Example: start at **06:20 UTC** so the script can wait until 11:55 IST:

```cron
20 6 * * 1-5
```

4. Use a **paid plan** if you need reliable cron; free tier has limits.

**Dry run first** (test without real money):

```bash
python live_trade_0920_0921.py --qty 1 --buy 11:55 --sell 11:56 --dry-run
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Build fails | Check **Deploy Logs**; ensure `streamlit` and `plotly` are in `requirements.txt`. |
| 502 / app not loading | Start command must use `$PORT` (see `Procfile`). Don't hardcode port 8501. |
| CSV not found | Upload CSV in the UI; don't use `C:\...` paths. |
| Dhan auth error | Set `DHAN_CLIENT_ID` and `DHAN_ACCESS_TOKEN` in Railway Variables. |
| Live trade from UI fails | Use cron service instead (Step 6). |

---

## Cost note

Railway gives a monthly credit on the Hobby plan. A small Streamlit app + occasional cron is usually low cost; check [railway.app/pricing](https://railway.app/pricing).

---

## Redeploy after code changes

```powershell
git add .
git commit -m "Your change"
git push
```

Railway redeploys automatically on push.
