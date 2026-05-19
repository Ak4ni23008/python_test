# Cloud Code Runner

Paste Python in the browser → **Run in cloud** → code runs on **Railway** and is **pushed to GitHub**.

Repo: [github.com/Ak4ni23008/python_test](https://github.com/Ak4ni23008/python_test)

## Railway setup (one time)

1. Deploy from this repo (already connected).
2. **Variables** → add:
   - `GITHUB_TOKEN` — [GitHub PAT](https://github.com/settings/tokens) with **repo** scope
   - `GITHUB_REPO` = `Ak4ni23008/python_test` (optional, this is the default)
   - `GITHUB_BRANCH` = `main` (optional)

3. Open your Railway public URL.

## Daily use

1. Paste or edit code in the text box.
2. Click **▶ Run in cloud**.
3. See output on the page (runs on Railway immediately).
4. Code is saved to `user_code.py` on GitHub (Railway redeploys in the background).

## Files

| File | Role |
|------|------|
| `cloud_app.py` | Web UI |
| `code_runner.py` | Runs pasted code on the server |
| `github_push.py` | Pushes to GitHub API |
| `user_code.py` | Last saved code (in repo) |
