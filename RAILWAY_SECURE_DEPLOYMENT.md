# 🚀 Railway Deployment Guide - Secure Setup

## ⚠️ SECURITY FIRST - How Secrets Are Protected

### Secret Storage Hierarchy
```
1. Railway Dashboard (SECURE) ✅
   - All API keys stored here
   - Encrypted at rest
   - Never exposed in logs
   - Never visible in GitHub

2. .env.example (PUBLIC) ✅
   - Only placeholder values
   - Safe to commit to GitHub
   - Shows what variables are needed

3. .env (LOCAL ONLY) ✅
   - Real credentials for local testing
   - IGNORED by git (.gitignore)
   - Never committed to GitHub

4. GitHub (SAFE) ✅
   - No real API keys
   - No credentials
   - Only source code
```

---

## 📋 Prerequisites

1. **GitHub Account** - Already have repo pushed
2. **Railway Account** - Create at https://railway.app
3. **Your API Keys** (Keep these secure!):
   - `GEMINI_API_KEY` from https://aistudio.google.com/apikey
   - `DHAN_CLIENT_ID` from https://www.dhan.co/
   - `DHAN_ACCESS_TOKEN` from Dhan account

---

## 🔐 Step 1: Verify No Secrets in GitHub

### 1.1 Check what will be pushed
```bash
# Before pushing, verify no .env in git
git status

# Should show:
# - modified:   .env (NOT in tracked files)
# - untracked:  .env (in gitignore)

# Confirm .gitignore has .env
grep "^.env$" .gitignore

# Output should be: .env
```

### 1.2 If .env was accidentally committed (do this)
```bash
# Remove from git history (but keep local copy)
git rm --cached .env
git commit -m "Remove .env from git tracking (move secrets to Railway)"

# Push to GitHub
git push

# Verify it's gone
git log --all --full-history -- .env
```

---

## 🚂 Step 2: Create Railway Project

### 2.1 Login to Railway
1. Go to https://railway.app/dashboard
2. Click **New Project**
3. Select **Deploy from GitHub repo**

### 2.2 Connect GitHub
1. Authorize Railway to access GitHub
2. Select repository: `Ak4ni23008/python_test`
3. Click **Deploy**

### 2.3 Watch deployment
Railway will:
- ✅ Clone your GitHub repo
- ✅ Auto-detect Python project
- ✅ Install dependencies
- ✅ Build backend & worker
- ✅ (Will fail initially - secrets missing, that's expected)

---

## 🔑 Step 3: Add Secrets to Railway Dashboard

### 3.1 Access Railway Variables
1. Go to Railway Dashboard
2. Select your project
3. Click **Variables** tab
4. Add each secret individually

### 3.2 Add Gemini API Key
```
Name:  GEMINI_API_KEY
Value: <your actual key from aistudio.google.com>
```

### 3.3 Add Dhan Credentials
```
Name:  DHAN_CLIENT_ID
Value: <your client ID from Dhan>
```

```
Name:  DHAN_ACCESS_TOKEN
Value: <your access token from Dhan>
```

### 3.4 Add Database Settings (if needed)
```
Name:  DATABASE_URL
Value: <PostgreSQL URL - Railway auto-provides this>
```

### 3.5 Add Environment
```
Name:  ENVIRONMENT
Value: production
```

```
Name:  CORS_ORIGINS
Value: https://YOUR_RAILWAY_DOMAIN.railway.app
```

---

## 🛠️ Step 4: Configure Services

### 4.1 Backend Service
1. **Service**: Select backend
2. **Build Command**: Automatic (or `pip install -r requirements.txt`)
3. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Port**: 8000
5. **Environment**: Add all variables from Step 3

### 4.2 Frontend Service (Next.js)
1. **Service**: Select frontend
2. **Build Command**: `npm run build`
3. **Start Command**: `npm start`
4. **Port**: 3000
5. **Environment Variables**:
   ```
   NEXT_PUBLIC_API_URL=https://backend-service.railway.app
   NODE_ENV=production
   ```

### 4.3 Worker Service (Optional)
1. **Service**: Select worker
2. **Build Command**: Automatic
3. **Start Command**: `python -m app.workers.live_worker`
4. **No port exposure** (background job)

### 4.4 Database Service
1. **Add PostgreSQL** if not auto-detected:
   - Click **Add Service**
   - Select **PostgreSQL**
   - Railway auto-generates `DATABASE_URL`

---

## ✅ Step 5: Verify Deployment

### 5.1 Check Service Health
```
Dashboard → Services → Status
- Backend: Running ✅
- Frontend: Running ✅
- Database: Running ✅
```

### 5.2 View Logs
```
Dashboard → Logs
Watch for:
- ✅ "Application startup complete"
- ❌ Any "API key not found" errors
```

### 5.3 Test Endpoints
```bash
# Get your Railway domain
RAILWAY_DOMAIN="https://your-project-name.railway.app"

# Test backend health
curl $RAILWAY_DOMAIN/api/health

# Test frontend
curl $RAILWAY_DOMAIN

# View API docs
curl $RAILWAY_DOMAIN/api/docs
```

---

## 🔄 Step 6: Continuous Deployment

### 6.1 Auto-Deploy on GitHub Push
Railway auto-deploys when you push to `main`:
```bash
# Make code changes
git add .
git commit -m "Fix: improve strategy generation"
git push origin main

# Railway automatically:
# 1. Detects changes
# 2. Rebuilds containers
# 3. Deploys new version
# No manual action needed!
```

### 6.2 Monitor Deployments
```
Dashboard → Deployments
- View deployment history
- See build logs
- Rollback if needed
```

---

## 🔒 Security Best Practices

### DO ✅
- [x] Store all API keys in Railway Dashboard **Variables**
- [x] Use `.env.example` with placeholders only
- [x] Keep `.env` in `.gitignore`
- [x] Rotate API keys periodically
- [x] Use specific permissions for service accounts
- [x] Enable Railway's security features

### DON'T ❌
- [ ] Never commit `.env` file to GitHub
- [ ] Never paste real keys in README
- [ ] Never use default/test credentials
- [ ] Never share API keys in Slack/Email
- [ ] Never log sensitive values
- [ ] Never use same key across projects

---

## 🆘 Troubleshooting

### Build Failed - "API key not found"
**Solution**: Add `GEMINI_API_KEY` to Railway Variables dashboard

### Services Crashing
**Solution**: Check logs → Look for missing variables
```bash
# View logs
railway logs

# Restart service
railway service restart backend
```

### Frontend Can't Connect to Backend
**Solution**: Update `NEXT_PUBLIC_API_URL` in Railway Variables
```
NEXT_PUBLIC_API_URL=https://your-project-backend.railway.app
```

### Database Connection Error
**Solution**: Ensure `DATABASE_URL` is set (Railway auto-provides)
```bash
railway status
```

---

## 📊 Environment Variable Reference

### Backend Variables
```
GEMINI_API_KEY           (Required) - From Google AI Studio
GEMINI_MODEL             (Optional) - Default: gemini-2.0-flash
DHAN_CLIENT_ID           (Optional) - From Dhan broker
DHAN_ACCESS_TOKEN        (Optional) - From Dhan broker
DATABASE_URL             (Auto)     - PostgreSQL connection
CORS_ORIGINS             (Optional) - Allowed frontends
ENVIRONMENT              (Optional) - "production"
WORKER_POLL_SECONDS      (Optional) - Default: 2.0
RATE_LIMIT_PER_MINUTE    (Optional) - Default: 60
```

### Frontend Variables
```
NEXT_PUBLIC_API_URL      (Required) - Backend URL
NODE_ENV                 (Optional) - "production"
```

### Worker Variables
```
Same as Backend (inherits from shared settings)
```

---

## 🚀 Deployment Commands

### View Status
```bash
railway status
```

### View Logs
```bash
railway logs -f
```

### Restart Service
```bash
railway service restart backend
```

### Scale Service
```bash
# Add replicas
railway service scale backend 3
```

### Download Environment
```bash
# Pull current Railway variables locally
railway env pull
```

### Run Command in Railway
```bash
railway run python manage.py migrate
```

---

## 🔄 Git Workflow

### Safe Development Workflow
```bash
# 1. Create feature branch
git checkout -b feature/new-strategy

# 2. Make changes (secrets in .env locally only)
vim backend/app/ai/code_generator.py

# 3. Commit code (not secrets)
git add backend/app/ai/code_generator.py
git commit -m "Add new strategy generation"

# 4. Push to GitHub (no .env file)
git push origin feature/new-strategy

# 5. Create Pull Request
# 6. Railway auto-deploys preview
# 7. Test staging environment
# 8. Merge to main
# 9. Railway auto-deploys production
```

### Verifying Before Push
```bash
# Check what will be committed
git status

# Should NOT show .env (confirmed in .gitignore)
# Should only show code changes

# Double check
git ls-files | grep -i ".env"
# Should be empty (no output = good!)
```

---

## 📈 Monitoring & Metrics

### View Metrics
```
Dashboard → Metrics
- CPU Usage
- Memory Usage
- Network I/O
- Build time
- Deploy time
```

### Set Alerts
```
Dashboard → Settings → Alerts
- Low disk space
- High memory usage
- Build failures
- Deploy failures
```

---

## 💰 Cost Management

### Free Tier Benefits
```
- 500 hours/month compute (free tier)
- PostgreSQL database (free)
- SSL certificate (free)
- GitHub integration (free)
```

### Optimize Costs
```
1. Use smallest dyno size initially
2. Scale only when needed
3. Remove unused services
4. Set memory limits
5. Monitor costs regularly
```

---

## 🎉 You're Live!

**Your secure Railway deployment is ready:**
- ✅ Code on GitHub (no secrets)
- ✅ Secrets on Railway Dashboard (encrypted)
- ✅ Auto-deployment on git push
- ✅ Auto-restart on failure
- ✅ Production HTTPS enabled

**Access your app:**
```
https://your-project-name.railway.app
```

---

## 🔗 Quick Links

- Railway Dashboard: https://railway.app/dashboard
- GitHub Repo: https://github.com/Ak4ni23008/python_test
- Gemini API: https://aistudio.google.com/apikey
- Dhan API: https://www.dhan.co/
- Railway Docs: https://docs.railway.app

---

**Important: After deployment, NEVER share your Railway environment variables or API keys!** 🔒

For issues: Check Railway logs → Look for error messages → Fix locally → Push to GitHub → Railway auto-deploys
