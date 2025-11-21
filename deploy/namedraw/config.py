from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import os
from typing import Any, Dict


@dataclass(slots=True)
class AppConfig:
    client_id: str
    redirect_uri: str
    scopes: str
    sender_upn: str
    scenario_name: str
    participant_file: str
    token_cache_file: str
    tenant: str
    exclusions: dict[str, list[str]]

    @classmethod
    def load(cls, path: Path) -> "AppConfig":
        raw = {}
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                raw = json.load(handle)

        # allow environment variable overrides
        client_id = os.getenv("NAMEDRAW_CLIENT_ID", raw.get("client_id"))
        redirect_uri = os.getenv("NAMEDRAW_REDIRECT_URI", raw.get("redirect_uri"))
        scopes = os.getenv(
            "NAMEDRAW_SCOPES",
            raw.get("scopes", "offline_access openid profile https://graph.microsoft.com/Mail.Send"),
        )
        sender_upn = os.getenv("NAMEDRAW_SENDER", raw.get("sender_upn", "buddythechristmaself@outlook.com"))
        scenario_name = raw.get("scenario_name", "Christmas Morning Elf Gift")
        participant_file = raw.get("participant_file", "data/participants.json")
        token_cache_file = raw.get("token_cache_file", "data/refresh_token.json")
        tenant = os.getenv("NAMEDRAW_TENANT", raw.get("tenant", "common"))
        exclusions = raw.get("exclusions", {})

        if not client_id:
             # Fallback for local dev if file missing and no env var, though we prefer env vars in cloud
             if not path.exists():
                 raise FileNotFoundError(
                     f"Configuration file '{path}' not found and NAMEDRAW_CLIENT_ID not set."
                 )
             raise ValueError("Client ID is missing in configuration.")

        return cls(
            client_id=client_id,
            redirect_uri=redirect_uri,
            scopes=scopes,
            sender_upn=sender_upn,
            scenario_name=scenario_name,
            participant_file=participant_file,
            token_cache_file=token_cache_file,
            tenant=tenant,
            exclusions=exclusions,
        )
