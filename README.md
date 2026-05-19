# Cloud Code Runner

Paste Python → **Run** → executes on **Railway** (cloud).

## Option A — Use Railway URL (recommended)

1. Railway → **Networking** → copy your public URL (e.g. `https://python-test-production-xxxx.up.railway.app`)
2. Open that URL in the browser
3. Paste code → **▶ Run in cloud**

You should see: **Running on: ☁️ Railway cloud**

## Option B — Local Streamlit → remote Railway

```powershell
cd "C:\Users\akash\Downloads\dhan\Users\mahad\Downloads\Users\akash\OneDrive\Desktop\trading\back_testing"

$env:CLOUD_RUNNER_URL = "https://YOUR-RAILWAY-URL.up.railway.app"

python -m pip install streamlit requests
python -m streamlit run cloud_app.py
```

Click **▶ Run on Railway** — code runs on Railway, not your PC.

## Railway variables

| Variable | Purpose |
|----------|---------|
| `GITHUB_TOKEN` | Save to GitHub button (optional) |

## Do NOT use

- `http://localhost:8501` — runs on your laptop only
- `http://10.10.x.x:8501` — same, your local network

Use your **Railway public HTTPS URL** for cloud runs.
