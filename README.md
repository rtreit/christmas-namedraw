# Buddy the Elf Name Draw

A modern, animated Secret Santa-style experience that draws names, sends Graph emails, and keeps the magic in a gorgeous Elf-themed UI.

## Features

- 🎩 **Animated Experience**: Buddy the Elf guides you through the process with animations and confetti.
- 🔐 **Secure & Modern**: Uses Microsoft Graph API for sending emails securely.
- ☁️ **Azure Ready**: Deploys easily to Azure App Service (Free Tier) with Bicep infrastructure-as-code.
- 📱 **Responsive Design**: Works great on mobile and desktop.
- 🛠️ **Admin Tools**: Built-in tools to manage participants and test email sending.

## Quickstart (Local Development)

1.  **Prerequisites**: Python 3.11+, `uv` (or pip).
2.  **Setup Environment**:
    ```bash
    uv venv
    uv sync
    ```
3.  **Configuration**:
    - Copy `config.example.json` to `config.json` and update with your Azure App Registration details.
    - Copy `data/participants.example.json` to `data/participants.json` and add your family/friends.
    - Create a `.env` file with `BUDDY_PASSWORD` (for admin login) and `FLASK_SECRET_KEY`.
4.  **Authentication**:
    - Run the helper script to cache your initial refresh token:
      ```bash
      uv run scripts/cache_refresh_token.py
      ```
5.  **Run**:
    ```bash
    uv run flask --app app run --debug
    ```
    Browse to `http://localhost:5000`.

## Deployment to Azure

This project includes a `deploy.ps1` script that automates the entire deployment process to Azure App Service (Linux Free Tier).

1.  **Prerequisites**: Azure CLI (`az login`), PowerShell.
2.  **Configure**: Ensure your `.env` and `config.json` are set up locally.
3.  **Deploy**:
    ```powershell
    ./deploy.ps1
    ```
    This script will:
    - Package the application.
    - Create/Update Azure resources using Bicep.
    - Deploy the code.
    - Configure App Settings (Secrets) automatically.

## Project Structure

- `app.py`: Flask entry point.
- `namedraw/`: Main application package.
  - `routes.py`: Web routes and API endpoints.
  - `services/`: Business logic (Draw, Mailer, Tokens).
- `static/` & `templates/`: Frontend assets (HTML/CSS/JS).
- `deploy.ps1`: One-click deployment script.
- `main.bicep`: Azure Infrastructure as Code definition.

## Security Note

- `config.json`, `data/participants.json`, and `data/refresh_token.json` are **ignored by Git** to prevent accidental commit of secrets.
- In Azure, secrets are managed via App Service Application Settings.

## Token Expiration & Maintenance

The application uses a long-lived Refresh Token to authenticate with Microsoft Graph for sending emails. If the app fails to send emails (e.g., after 90 days of inactivity), the token may have expired.

**The Fix:**
1.  Run the helper script locally to generate a fresh token:
    ```bash
    uv run scripts/cache_refresh_token.py
    ```
2.  Redeploy the application to update the token in Azure:
    ```powershell
    ./deploy.ps1
    ```

