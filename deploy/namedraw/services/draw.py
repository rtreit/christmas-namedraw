from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable

from .participants import Participant, ParticipantRepository
from .mailer import GraphMailer


@dataclass(slots=True)
class Assignment:
    drawer: Participant
    recipient: Participant


class NameDrawService:
    def __init__(self, repository: ParticipantRepository, mailer: GraphMailer):
        self.repository = repository
        self.mailer = mailer

    def run_draw(self, send_notifications: bool = True, allowed_participants: list[str] = None, 
                 subject_template: str = None, body_template: str = None, scenario_name: str = None) -> list[Assignment]:
        family = self.repository.list_participants()
        
        if allowed_participants is not None:
            family = [p for p in family if p.name in allowed_participants]
            
        pairings = self._paired_assignments(family)

        if send_notifications:
            for assignment in pairings:
                self.mailer.send_assignment(assignment, subject_template, body_template, scenario_name)
        return pairings

    def _paired_assignments(self, family: Iterable[Participant]) -> list[Assignment]:
        candidates = list(family)
        recipients = candidates.copy()
        max_attempts = 200

        for attempt in range(max_attempts):
            random.shuffle(recipients)
            proposed = list(zip(candidates, recipients, strict=False))
            try:
                assignments = [
                    Assignment(drawer=d, recipient=r)
                    for d, r in proposed
                    if self._is_valid_pair(d, r)
                ]
                if len(assignments) == len(candidates):
                    return assignments
            except ValueError:
                continue
        raise RuntimeError("Unable to find a valid draw after several attempts. Adjust exclusions and try again.")

    @staticmethod
    def _is_valid_pair(drawer: Participant, recipient: Participant) -> bool:
        if drawer.name == recipient.name:
            return False
        if recipient.name in drawer.exclusions:
            return False
        if drawer.name in recipient.exclusions:
            return False
        return True
