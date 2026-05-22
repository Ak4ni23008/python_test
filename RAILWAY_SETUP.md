# Railway setup for CloudTrade

**Production API:** https://pythontest-production-9440.up.railway.app/

## 1. Add variables (Railway → your service → Variables)

| Variable | Value |
|----------|--------|
| `GEMINI_API_KEY` | Your Gemini key (same as local `.env`) |
| `GEMINI_MODEL` | `gemini-2.0-flash` |
| `CORS_ORIGINS` | `https://pythontest-production-9440.up.railway.app,http://localhost:3000` |
| `ENVIRONMENT` | `production` |
| `DHAN_CLIENT_ID` | (optional, from your `.env`) |
| `DHAN_ACCESS_TOKEN` | (optional, from your `.env`) |

After adding PostgreSQL plugin, Railway injects `DATABASE_URL` automatically.

## 2. API service start command

```
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Health check: `/health`

## 3. Worker service (second service, same repo)

Start command:

```
cd backend && python -m app.workers.live_worker
```

Copy the same env vars (especially `DATABASE_URL` and `GEMINI_API_KEY`).

## 4. Deploy

Push to GitHub → Railway redeploys.

**Note:** Until you deploy the new `backend/` code, the live URL still shows the old HTML Trading App. After deploy, use:

- API docs: `https://pythontest-production-9440.up.railway.app/docs`
- Cloud status: `https://pythontest-production-9440.up.railway.app/api/cloud/status`

## 5. Frontend (your PC)

```powershell
cd frontend
npm install
npm run dev
```

`frontend/.env.local` already points to your Railway API.
