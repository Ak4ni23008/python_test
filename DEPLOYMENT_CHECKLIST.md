# ⚡ Railway Deployment Checklist

## Your GitHub Repo
✅ https://github.com/Ak4ni23008/python_test.git
✅ Code just pushed (commit e28f7b3)

## Railway Web Service Setup

### 1. **Start Command** (Settings → Start Command)
```
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 2. **Environment Variables** (Settings → Variables)
```
GEMINI_API_KEY=AIzaSyAE6vqeYE6QohV3_2rOh6MbILSIeOkLBe4
GEMINI_MODEL=gemini-2.0-flash
DATABASE_URL=postgres://...  (Railway auto-injects)
CORS_ORIGINS=http://localhost:3000,https://pythontest-production-9440.up.railway.app
ENVIRONMENT=production
```

### 3. **Root Directory** (Settings → Root Directory)
```
.   (leave empty or .)
```

### 4. **Add PostgreSQL** (if not already added)
- Dashboard → + New → Database → PostgreSQL
- Railway auto-injects DATABASE_URL

## Test After Deploy
```bash
# Wait 2-3 minutes for Railway to build & deploy

# Then test:
curl https://pythontest-production-9440.up.railway.app/api/cloud/status

# Should return:
{
  "host": "railway",
  "environment": "production",
  "is_railway": true,
  "gemini_configured": true,
  ...
}
```

## Frontend Deployment (Next)
- Deploy to Vercel: https://vercel.com
- Set env var: `NEXT_PUBLIC_API_URL=https://pythontest-production-9440.up.railway.app`
- Or deploy to Railway too

## ✅ Completion Checklist
- [ ] Verify Railway start command set
- [ ] Verify env variables set
- [ ] Test `/api/cloud/status` endpoint
- [ ] Deploy frontend
- [ ] Test chat interface live
- [ ] Create new strategy via chat
- [ ] Execute code and backtest
