from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import List


@dataclass(slots=True)
class Participant:
    name: str
    email: str
    exclusions: list[str]


class ParticipantRepository:
    def __init__(self, source_path: Path):
        self._source = source_path
        if not self._source.exists():
            raise FileNotFoundError(
                f"Participant roster '{self._source}' not found. Populate it before running the draw."
            )

    def list_participants(self) -> list[Participant]:
        with self._source.open("r", encoding="utf-8") as roster:
            payload = json.load(roster)

        participants: List[Participant] = []
        for entry in payload:
            participants.append(
                Participant(
                    name=entry["name"],
                    email=entry["email"],
                    exclusions=entry.get("exclusions", []),
                )
            )
        return participants
