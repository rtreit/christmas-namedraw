from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Tuple

import jwt
import requests

from ..config import AppConfig


@dataclass(slots=True)
class TokenCache:
    path: Path

    def read_refresh_token(self) -> str:
        # Try file first (it might have a newer token than the env var)
        if self.path.exists():
            try:
                with self.path.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)
                return data["refresh_token"]
            except Exception:
                pass  # Fallback to env var if file is corrupt

        # Try environment variable
        env_token = os.getenv("REFRESH_TOKEN")
        if env_token:
            return env_token

        raise FileNotFoundError(
            f"Refresh token cache '{self.path}' is missing. Run scripts/cache_refresh_token.py to generate it."
        )

    def save_refresh_token(self, refresh_token: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump({"refresh_token": refresh_token}, handle, indent=2)


class TokenProvider:
    def __init__(self, config: AppConfig, cache: TokenCache):
        self.config = config
        self.cache = cache

    def get_access_token(self) -> Tuple[str, str]:
        refresh_token = self.cache.read_refresh_token()
        payload = {
            "client_id": self.config.client_id,
            "scope": self.config.scopes,
            "refresh_token": refresh_token,
            "redirect_uri": self.config.redirect_uri,
            "grant_type": "refresh_token",
        }
        response = requests.post(
            f"https://login.microsoftonline.com/{self.config.tenant}/oauth2/v2.0/token",
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        response.raise_for_status()
        tokens = response.json()
        access_token = tokens["access_token"]
        new_refresh = tokens.get("refresh_token")
        if new_refresh:
            self.cache.save_refresh_token(new_refresh)

        id_token = tokens["id_token"]
        decoded = jwt.decode(id_token, options={"verify_signature": False}, algorithms=["RS256"])
        sender = decoded.get("preferred_username", self.config.sender_upn)
        return access_token, sender
