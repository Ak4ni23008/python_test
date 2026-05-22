# CloudTrade — Cloud Algo Trading MVP

Production-style MVP where **all strategy execution runs on Railway cloud workers**, not on the user's phone or laptop.

## Architecture

```
┌─────────────┐     HTTPS      ┌──────────────────┐
│  Next.js    │ ─────────────► │  FastAPI (web)   │
│  Frontend   │                │  Railway Service │
└─────────────┘                └────────┬─────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
             ┌────────────┐      ┌────────────┐      ┌──────────────┐
             │ PostgreSQL │      │   Gemini   │      │ Live Worker  │
             │ (Railway)  │      │  (backend) │      │ (continuous) │
             └────────────┘      └────────────┘      └──────────────┘
```

### Safe AI flow (no arbitrary Python)

1. User enters strategy in **plain English**
2. **Gemini** (backend only) → validated **JSON config**
3. Template engines run **backtest** and **live simulation**

Supported templates: `RSI`, `MACD`, `SMA_CROSS`, `TIME_BASED`

## Project structure

```
backend/          FastAPI API + engines + Gemini + worker
frontend/         Next.js mobile-first dashboard
Procfile          web + worker processes
railway.json      API service deploy
railway.worker.json  Worker service deploy
```

## Railway deployment

### 1. Create project

1. Push this repo to GitHub
2. [Railway](https://railway.app) → New Project → Deploy from GitHub

### 2. Add PostgreSQL

- Railway dashboard → **+ New** → **Database** → **PostgreSQL**
- `DATABASE_URL` is injected automatically into services

### 3. API service (web)

- Service settings → **Start Command**:
  ```
  cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```
- Or use root `railway.json`

### 4. Worker service (required for live trading)

- **+ New Service** → same repo
- **Start Command**:
  ```
  cd backend && python -m app.workers.live_worker
  ```
- Or copy config from `railway.worker.json`
- This process runs the **continuous strategy loop** in the cloud

### 5. Environment variables (both services)

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `DATABASE_URL` | Yes (prod) | From Railway PostgreSQL |
| `GEMINI_MODEL` | No | Default `gemini-2.0-flash` |
| `CORS_ORIGINS` | Yes | Your frontend URL(s) |
| `ENVIRONMENT` | No | `production` |
| `WORKER_POLL_SECONDS` | No | Default `2.0` |
| `RATE_LIMIT_PER_MINUTE` | No | Default `60` |

### 6. Frontend (Vercel / Railway / local)

```bash
cd frontend
npm install
# Point to Railway API:
echo NEXT_PUBLIC_API_URL=https://your-api.up.railway.app > .env.local
npm run dev
```

Deploy frontend separately; set `NEXT_PUBLIC_API_URL` to your Railway API URL.

## Local development

### Backend API

```powershell
cd backend
pip install -r requirements.txt
$env:GEMINI_API_KEY = "your-key"
$env:DATABASE_URL = "sqlite:///./cloudtrade.db"
uvicorn app.main:app --reload --port 8000
```

### Cloud worker (separate terminal)

```powershell
cd backend
python -m app.workers.live_worker
```

### Frontend

```powershell
cd frontend
npm install
$env:NEXT_PUBLIC_API_URL = "http://localhost:8000"
npm run dev
```

Open http://localhost:3000

## Dashboard pages

| Page | Path | Purpose |
|------|------|---------|
| Home | `/` | Overview + strategy list |
| Create | `/strategies/new` | English → Gemini → JSON |
| Backtest | `/backtest/[id]` | Charts, metrics, trade log, download JSON |
| Live | `/live` | Simulated live prices, PnL, deploy/stop |
| Deployments | `/deployments` | Cloud deployment status |
| Logs | `/logs` | Execution logs from worker |

## API docs

When API is running: `https://your-api.up.railway.app/docs`

Key endpoints:

- `POST /api/strategies/parse` — English → config (Gemini)
- `POST /api/strategies/{id}/backtest` — Run backtest
- `POST /api/strategies/{id}/deploy` — Start cloud worker execution
- `POST /api/deployments/{id}/stop` — Stop execution
- `GET /api/cloud/status` — Cloud host + Gemini status

## Security

- Gemini key **only** on backend (`GEMINI_API_KEY`)
- Frontend never sees API keys
- Strategy execution uses **validated JSON templates** only
- Rate limiting on API routes

## Legacy app

The original HTML trading app (`server.py`) remains for backward compatibility. CloudTrade is the new platform under `backend/` + `frontend/`.
