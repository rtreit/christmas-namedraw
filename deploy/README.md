# Buddy the Elf Name Draw

A modern, animated Secret Santa-style experience that draws names, sends Graph emails, and keeps the magic in a gorgeous Elf-themed UI.

## Features

- 🎩 Animated hat + Buddy portrait with confetti + slip animation
- 🔐 Secure token cache + Microsoft Graph `sendMail`
- 📜 Participant roster + dynamic exclusions
- ✉️ Email button opens a one-click mail draft that whispers each buddy privately
- 🧰 REST API: `/api/participants`, `/api/draw`

## Quickstart (uv)

```bash
uv venv
uv sync
copy config.example.json config.json               # update with your Azure app + mailbox
copy data/participants.example.json data/participants.json
- Toggle **Allow public client flows** so the app accepts native auth without a secret.
# ensure scopes include https://graph.microsoft.com/Mail.Send
uv run python scripts/cache_refresh_token.py
uv run flask --app app run --debug
```

Browse to `http://localhost:5000` and watch Buddy work.


## Project Layout

```
app.py                 # Flask entrypoint

**Azure app checklist**
- Set `tenant=consumers` for Outlook.com/MSA, or use your tenant GUID for Entra ID.
- Ensure scopes include `https://graph.microsoft.com/Mail.Send` plus `offline_access openid profile`.
- In the portal, add `http://localhost:8076` under *Mobile and desktop applications* and enable *Allow public client flows*.
- For personal Microsoft accounts, use the `App registrations (preview)` blade in Azure Portal > **Accounts in any organizational directory and personal Microsoft accounts (MSA)**.
- If the helper prints `<no-body>`, re-run and grab the full status/header dump to share; it usually means Azure rejected the request before returning JSON.
namedraw/              # Application package
	config.py            # App config loader
	routes.py            # API blueprint
	services/            # Tokens, mailer, draw logic
scripts/cache_refresh_token.py  # helper to bootstrap refresh token
data/participants.example.json # sample roster template
static/                # CSS/JS assets

### Secrets & local data

- `config.json`, `data/participants.json`, and `data/refresh_token.json` stay local only—Git ignores them.
- Use the `.example` files as templates, then update the real files with your tenant + family details.
- If a refresh token ever leaks, revoke the app's permissions in account.microsoft.com (or Azure Portal) and rerun the helper.
```
