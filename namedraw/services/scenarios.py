from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class Scenario:
    id: str
    name: str
    subject: str
    template_body: str
    participants: List[str] = field(default_factory=list)


class ScenarioRepository:
    def __init__(self, source_path: Path):
        self._source = source_path
        if not self._source.exists():
            # Create default if not exists
            self._save_scenarios([])

    def list_scenarios(self) -> List[Scenario]:
        with self._source.open("r", encoding="utf-8") as f:
            try:
                payload = json.load(f)
            except json.JSONDecodeError:
                return []

        scenarios = []
        for entry in payload:
            scenarios.append(
                Scenario(
                    id=entry.get("id", str(uuid.uuid4())),
                    name=entry.get("name", "Unnamed Scenario"),
                    subject=entry.get("subject", "Secret Santa"),
                    template_body=entry.get("template_body", ""),
                    participants=entry.get("participants", []),
                )
            )
        return scenarios

    def get_scenario(self, scenario_id: str) -> Optional[Scenario]:
        scenarios = self.list_scenarios()
        for s in scenarios:
            if s.id == scenario_id:
                return s
        return None

    def save_scenario(self, scenario: Scenario) -> None:
        scenarios = self.list_scenarios()
        existing_idx = next((i for i, s in enumerate(scenarios) if s.id == scenario.id), -1)
        
        if existing_idx >= 0:
            scenarios[existing_idx] = scenario
        else:
            scenarios.append(scenario)
        
        self._save_scenarios(scenarios)

    def delete_scenario(self, scenario_id: str) -> None:
        scenarios = self.list_scenarios()
        scenarios = [s for s in scenarios if s.id != scenario_id]
        self._save_scenarios(scenarios)

    def _save_scenarios(self, scenarios: List[Scenario]) -> None:
        payload = [
            {
                "id": s.id,
                "name": s.name,
                "subject": s.subject,
                "template_body": s.template_body,
                "participants": s.participants,
            }
            for s in scenarios
        ]
        with self._source.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
