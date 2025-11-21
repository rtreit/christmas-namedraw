"""Interactive helper to capture and cache a refresh token for Buddy the Elf."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import requests

from namedraw.config import AppConfig
from namedraw.services.tokens import TokenCache


class OAuthHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, config: AppConfig, cache: TokenCache, **kwargs):
        self.config = config
        self.cache = cache
        super().__init__(*args, **kwargs)

    def do_GET(self):  # noqa: N802
        raw_path = self.path
        if "code=" not in raw_path:
            self._write_response("Missing code parameter. Please approve the app again.")
            return
        code = raw_path.split("code=")[1].split("&")[0]
        try:
            token = self._exchange_code(code)
        except requests.HTTPError as exc:  # type: ignore[name-defined]
            if getattr(exc, "response", None) is not None:
                print("Failed to exchange auth code. Response from Azure:")
                print("Status:", exc.response.status_code)
                print("Headers:", exc.response.headers)
                print("Body:", exc.response.text)
            else:
                print("Failed to exchange auth code (no response body):", exc)
            self._write_response(
                "Exchange failed. Check the terminal output for 'AADSTS' details — typically redirect URI, tenant, or public-client settings."
            )
            return
        self.cache.save_refresh_token(token)
        self._write_response("Refresh token cached! You can close this window.")

    def _exchange_code(self, auth_code: str) -> str:
        response = requests.post(
            f"https://login.microsoftonline.com/{self.config.tenant}/oauth2/v2.0/token",
            data={
                "client_id": self.config.client_id,
                "scope": self.config.scopes,
                "code": auth_code,
                "redirect_uri": self.config.redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["refresh_token"]

    def _write_response(self, message: str):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(message.encode("utf-8"))


def main():
    config = AppConfig.load(Path("config.json"))
    cache = TokenCache(Path(config.token_cache_file))

    auth_url = (
        f"https://login.microsoftonline.com/{config.tenant}/oauth2/v2.0/authorize"
        f"?client_id={config.client_id}"
        f"&redirect_uri={config.redirect_uri}"
        f"&response_type=code&scope={config.scopes}"
    )

    print("Opening browser for consent...")
    import webbrowser

    webbrowser.open(auth_url, new=2)

    def handler(*args, **kwargs):
        OAuthHandler(*args, config=config, cache=cache, **kwargs)

    server = HTTPServer(("127.0.0.1", 8076), handler)
    print("Listening for OAuth callback on http://127.0.0.1:8076")
    server.serve_forever()


if __name__ == "__main__":
    main()
