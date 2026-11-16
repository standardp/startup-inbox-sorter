# Startup Inbox

A dashboard that sorts the startup emails in your Gmail by industry (Fintech, AI / ML, Climate, ...) using an LLM.

- **GitHub Actions** runs `sync.py` every day at 07:00 (America/Bogota). It reads new Gmail messages (read-only IMAP), classifies them with [Lyber](https://www.lyber.ai) (keyword fallback without a key) and writes `docs/data.json`.
- **GitHub Pages** serves the dashboard in `docs/`.
- **Privacy:** `docs/data.json` is encrypted with AES-256-GCM (PBKDF2-SHA256 key from your passphrase). The dashboard decrypts it in your browser. Gmail and Lyber credentials live only in GitHub Actions secrets. The code is public; your emails and keys are not.

Only emails received on or after `GMAIL_START_DATE` (default `2026-11-17`) are sorted. Emails you sent, calendar invites, and the Promotions/Social tabs are skipped.

## Set up your own copy

1. Fork or copy this repo.
2. Create a Gmail app password at https://myaccount.google.com/apppasswords (needs 2-Step Verification).
3. In **Settings → Secrets and variables → Actions**, add these secrets:
   - `GMAIL_ADDRESS`
   - `GMAIL_APP_PASSWORD`
   - `LYBER_API_KEY` (optional; without it, keyword matching is used)
   - `DASHBOARD_PASSPHRASE`: the passphrase you'll type to open the dashboard

   Optionally add the variable `GMAIL_START_DATE` (YYYY-MM-DD).
4. Delete `docs/data.json` in your copy. It's encrypted with someone else's passphrase, so the sync would fail.
5. **Settings → Pages → Source: GitHub Actions.**
6. **Actions → "Sort emails and publish dashboard" → Run workflow** to run it once now. After that it runs daily.
7. Open `https://<you>.github.io/startup-inbox-sorter/` and enter your passphrase.

Manual industry corrections are saved in your browser (localStorage).

## Run locally

```bash
pip install -r requirements.txt
python sync.py --sample          # demo data, passphrase "demo"
cd docs && python -m http.server 8000
```

Open http://localhost:8000. For real mail, copy `.env.example` to `.env`, fill it in, and run `python sync.py`.
