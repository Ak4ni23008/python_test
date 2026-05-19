# python_test — Cloud Runner

Open your **Railway URL** → click **▶ Run** → code in `job.py` runs on the server (not your laptop).

## Files

| File | Purpose |
|------|---------|
| `cloud_app.py` | Web page with Run button |
| `job.py` | Logic to run when you click Run (edit this for Dhan trading) |
| `railway.json` | Railway start command (Streamlit) |

## Daily use

- **Run strategy:** open Railway URL → click **Run** (no git push)
- **Change code:** edit `job.py` → `git push` → Railway redeploys

## Dhan API (later)

In Railway → **Variables** (not in this repo):

- `DHAN_CLIENT_ID`
- `DHAN_ACCESS_TOKEN`

Repo: [github.com/Ak4ni23008/python_test](https://github.com/Ak4ni23008/python_test)
