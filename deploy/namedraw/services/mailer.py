from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from html import escape
from typing import Any, TYPE_CHECKING
from urllib.parse import quote_plus

import jwt
import requests

from ..config import AppConfig
from .tokens import TokenCache, TokenProvider

if TYPE_CHECKING:
    from .draw import Assignment


@dataclass(slots=True)
class MailResult:
    drawer: str
    recipient: str
    status: str
    message_id: str | None = None


class GraphMailer:
    def __init__(self, config: AppConfig, token_cache: TokenCache):
        self.config = config
        self.token_provider = TokenProvider(config, token_cache)

    def send_assignment(self, assignment: "Assignment", subject_template: str = None, body_template: str = None, scenario_name: str = None) -> MailResult:
        access_token, sender = self.token_provider.get_access_token()
        encoded_name = self._encode_name(assignment.recipient.name)
        reveal_link = self._reveal_link(assignment.recipient.name)
        
        current_scenario_name = scenario_name or self.config.scenario_name
        subject = subject_template.format(scenario_name=current_scenario_name) if subject_template else f"You did it! {current_scenario_name}"
        
        if body_template:
            # Simple format replacement for the custom template
            content = body_template.replace("{drawer_name}", assignment.drawer.name)\
                                   .replace("{encoded_name}", encoded_name)\
                                   .replace("{reveal_link}", escape(reveal_link, quote=True))
        else:
            content = self._mail_body(assignment.drawer.name, encoded_name, reveal_link)

        mail_json = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": content,
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": assignment.drawer.email,
                        }
                    }
                ],
            }
        }

        response = requests.post(
            f"https://graph.microsoft.com/v1.0/users/{sender}/sendMail",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            data=json.dumps(mail_json),
            timeout=30,
        )
        try:
            response.raise_for_status()
            payload: Any = response.json() if response.content else {}
            return MailResult(
                drawer=assignment.drawer.name,
                recipient=assignment.recipient.name,
                status="sent",
                message_id=payload.get("id"),
            )
        except Exception as exc:  # noqa: BLE001
            return MailResult(
                drawer=assignment.drawer.name,
                recipient=assignment.recipient.name,
                status=f"error: {exc}",
            )

    @staticmethod
    def _encode_name(name: str) -> str:
        payload = name.encode("utf-8")
        return base64.b64encode(payload).decode("utf-8")

    @staticmethod
    def _reveal_link(recipient_name: str) -> str:
        subject = quote_plus("Buddy's Secret Assignment")
        body = quote_plus(
            f"🎁 Buddy whispered that you're shopping for: {recipient_name}\n\n(Just close this draft after reading.)"
        )
        return f"mailto:?subject={subject}&body={body}"

    def _mail_body(self, drawer_name: str, encoded_name: str, reveal_link: str) -> str:
        safe_code = escape(encoded_name)
        safe_link = escape(reveal_link, quote=True)
        return f"""
        <body style=\"font-family: 'Segoe UI', sans-serif; color:#0f5132; background:#fffbe6;\">
          <div style=\"text-align:center;padding:32px;\">
            <img src=\"https://cdn.costumewall.com/wp-content/uploads/2016/09/buddy-the-elf-costume.jpg?w=640\" alt=\"Buddy the Elf\" style=\"max-width: 220px; border-radius: 12px; box-shadow:0 12px 25px rgba(0,0,0,0.2);\"/>
            <h1 style=\"color:#0f5132;\">It's Christmas Time {drawer_name}!!!</h1>
            <p style=\"font-size:18px;\">Buddy masked the name so your Sent Items stay spoiler-free.</p>
            <p style=\"margin:28px 0 16px;\">Tap once to open a draft note⏤the first line spells out your buddy. Close the draft after reading.</p>
            <a href=\"{safe_link}\" style=\"display:inline-block;padding:14px 26px;background:#d5275a;color:#fff;border-radius:999px;font-weight:bold;text-decoration:none;\">Reveal My Buddy</a>
            <p style=\"font-size:14px;margin-top:24px;color:#0f5132;\">Backup plan: paste this snow code into any Base64 decoder:</p>
            <code style=\"display:inline-block;padding:8px 16px;background:#fff;border-radius:12px;font-size:13px;letter-spacing:1px;\">{safe_code}</code>
          </div>
        </body>
        """
