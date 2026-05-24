# ✅ Railway Secure Deployment Checklist

## Phase 1: Clean GitHub (NO SECRETS) ✅

- [ ] Remove real credentials from `.env` file
- [ ] Verify `.env` is in `.gitignore`
- [ ] Check git doesn't track `.env`
  ```bash
  git ls-files | grep ".env"
  # Should show nothing
  ```
- [ ] Remove any hardcoded API keys from code
- [ ] Commit & push clean code to GitHub
  ```bash
  git add .
  git commit -m "Security: Move all secrets to Railway Dashboard"
  git push
  ```

---

## Phase 2: Create Railway Project 🚂

- [ ] Create Railway account at https://railway.app
- [ ] Login to Railway Dashboard
- [ ] Click "New Project" → "Deploy from GitHub"
- [ ] Authorize Railway + select repo: `Ak4ni23008/python_test`
- [ ] Click "Deploy"
- [ ] Railway starts building (will show some warnings, that's ok)

---

## Phase 3: Add Secrets to Railway Dashboard 🔐

**IMPORTANT: Do this via Railway UI, NOT in code!**

### Backend Variables
- [ ] `GEMINI_API_KEY`
  - Source: https://aistudio.google.com/apikey
  - Paste: Your actual Gemini API key
  
- [ ] `DHAN_CLIENT_ID`
  - Source: Your Dhan account
  - Paste: Your client ID
  
- [ ] `DHAN_ACCESS_TOKEN`
  - Source: Your Dhan account
  - Paste: Your access token

- [ ] `ENVIRONMENT`
  - Value: `production`

- [ ] `CORS_ORIGINS` (optional)
  - Value: `https://your-project-name.railway.app`

### Frontend Variables
- [ ] `NEXT_PUBLIC_API_URL`
  - Value: `https://backend-service-url.railway.app`

- [ ] `NODE_ENV`
  - Value: `production`

---

## Phase 4: Configure Services 🛠️

### Backend Service
- [ ] Service name: `backend`
- [ ] Build command: `pip install -r requirements.txt`
- [ ] Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Port: 8000
- [ ] All variables from Phase 3 added

### Frontend Service
- [ ] Service name: `frontend`
- [ ] Build command: `npm install && npm run build`
- [ ] Start command: `npm start`
- [ ] Port: 3000
- [ ] Variables: `NEXT_PUBLIC_API_URL`, `NODE_ENV`

### Database Service (if needed)
- [ ] Add PostgreSQL service
- [ ] Note the `DATABASE_URL` (auto-provided)

---

## Phase 5: Verify Deployment ✅

### Check Service Health
```bash
# Via Railway Dashboard → Services
- [ ] Backend: Status "Running" ✅
- [ ] Frontend: Status "Running" ✅
- [ ] Database: Status "Running" ✅ (if added)
```

### Test Endpoints
```bash
# Replace YOUR_DOMAIN with your Railway domain
DOMAIN="https://your-project-name.railway.app"

# Test backend health
curl $DOMAIN/api/health

# Test frontend
curl $DOMAIN

# Check API documentation
# Open in browser: $DOMAIN/api/docs
```

### View Logs
- [ ] Open Railway Dashboard → Logs
- [ ] Look for "Application startup complete" (good sign)
- [ ] No errors about missing API keys

---

## Phase 6: Verify Security ✅

- [ ] No `.env` file visible in GitHub
  ```bash
  # Verify online at GitHub
  # If .env appears, it means .gitignore failed
  ```

- [ ] No real API keys in GitHub code
  ```bash
  git log --all -S "sk-" 2>/dev/null | grep "^commit"
  # Should return nothing (no commits with API keys)
  ```

- [ ] All secrets are in Railway Dashboard Variables
  ```
  Railway Dashboard → Variables
  - Should see: GEMINI_API_KEY, DHAN_CLIENT_ID, etc.
  ```

- [ ] `.env` file only has empty placeholders locally
  ```bash
  cat .env | grep "="
  # Should show GEMINI_API_KEY= (empty)
  ```

---

## Phase 7: Test Functionality 📊

- [ ] Create new strategy via chat UI
  - Go to `https://your-project-name.railway.app`
  - Click "💬 Chat Builder"
  - Enter: "Buy when RSI below 30"
  - Should generate code (uses Gemini API)

- [ ] Run backtest
  - Click "Backtest" on generated strategy
  - Should execute and show results

- [ ] Verify live trading ready
  - Check worker logs: `railway logs worker`
  - Should say "Worker polling for strategies"

---

## Phase 8: Enable Auto-Deployment 🔄

- [ ] Push code to GitHub
  ```bash
  git add .
  git commit -m "New feature: XYZ"
  git push
  ```

- [ ] Watch Railway auto-deploy
  - Dashboard → Deployments
  - New deployment should start automatically
  - Should complete in 2-3 minutes

- [ ] Test new code live
  - Visit your app URL
  - Verify changes are live

---

## Phase 9: Security Audit 🔒

### Do NOT commit these:
- [ ] `.env` file with real secrets ✅ (should be in gitignore)
- [ ] API keys in code ✅ (should use env vars)
- [ ] Database passwords ✅ (Railway manages)
- [ ] Auth tokens ✅ (Railway manages)

### Proper security patterns:
- [ ] All secrets in Railway Dashboard
- [ ] Code only has `os.getenv("SECRET_NAME")`
- [ ] `.env.example` has empty placeholders
- [ ] `.gitignore` prevents .env commits

---

## Phase 10: Ongoing Maintenance 🔄

### Daily
- [ ] Monitor Railway Logs for errors
- [ ] Check service status
- [ ] Verify app is accessible

### Weekly
- [ ] Review Railway costs
- [ ] Check metrics (CPU, memory, disk)
- [ ] Update code if needed (auto-deploys)

### Monthly
- [ ] Rotate API keys
  - Generate new Gemini key
  - Update Railway Variables
  - Remove old key from Gemini console
  
- [ ] Review security settings
- [ ] Backup database
- [ ] Update dependencies

---

## ⚠️ Emergency Procedures

### Service Down
1. Check Railway Logs
2. Look for error messages
3. Fix issue locally
4. Push fix to GitHub
5. Railway auto-redeploys

### Need to Restart
```bash
# Via Railway CLI
railway service restart backend

# Or via Dashboard
Dashboard → Services → Backend → Restart
```

### Need to View Secrets (emergency only)
```bash
# Railway provides this command
railway env pull

# Shows all variables (don't screenshot this!)
```

### Accidentally Committed Secret
1. Do NOT panic - Railway keys are safe
2. Rotate that key immediately
3. Create new version on platform
4. Update Railway Variables
5. Verify old key no longer works

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| "API key not found" error | Add `GEMINI_API_KEY` to Railway Variables |
| Frontend can't reach backend | Update `NEXT_PUBLIC_API_URL` in Railway |
| Database connection error | Ensure `DATABASE_URL` is set (auto) |
| Build fails | Check build logs: `railway logs` |
| Port already in use | Railway manages this automatically |
| Need local testing | Use `.env` file locally (in gitignore) |

---

## 📞 Support Checklist

If something breaks:
1. [ ] Check Railway Logs: `railway logs`
2. [ ] Check service status: `railway status`
3. [ ] Verify all variables are set: Railway Dashboard → Variables
4. [ ] Try restarting: `railway service restart <service-name>`
5. [ ] Check GitHub has clean code (no .env)
6. [ ] Force rebuild: `railway build` or delete and re-add service

---

## ✅ Deployment Verification Checklist

Use this to verify everything works:

```bash
# 1. Test backend health
curl https://your-project-name.railway.app/api/health
# Response: {"status": "ok"} ✅

# 2. Test frontend
curl https://your-project-name.railway.app
# Response: HTML page ✅

# 3. Test API status
curl https://your-project-name.railway.app/api/cloud/status
# Response: Service info ✅

# 4. Check no .env in git
git ls-files | grep ".env"
# No output = ✅

# 5. Verify latest code is deployed
# Visit your app, check for your latest changes
```

---

## 🎉 Success Criteria

**Your deployment is successful when:**
- ✅ Code is on GitHub (no secrets)
- ✅ Secrets are on Railway (encrypted)
- ✅ App is live at railway domain
- ✅ Auto-deployment works (push → deploys)
- ✅ All endpoints working
- ✅ Live trading running
- ✅ Can create strategies via chat
- ✅ Can backtest strategies
- ✅ No API keys visible anywhere

---

**After completing this checklist, your deployment is PRODUCTION SECURE!** 🚀🔐
