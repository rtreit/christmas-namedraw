from __future__ import annotations

from flask import Blueprint, jsonify, request

from .services.draw import NameDrawService
from .services.participants import ParticipantRepository
from .services.scenarios import ScenarioRepository, Scenario


def create_api_blueprint(draw_service: NameDrawService, repository: ParticipantRepository, scenario_repo: ScenarioRepository) -> Blueprint:
    bp = Blueprint("namedraw_api", __name__, url_prefix="/api")

    @bp.get("/participants")
    def list_participants():
        participants = [
            {"name": member.name, "email": member.email}
            for member in repository.list_participants()
        ]
        return jsonify({"participants": participants})

    @bp.get("/scenarios")
    def list_scenarios():
        scenarios = [
            {
                "id": s.id,
                "name": s.name,
                "subject": s.subject,
                "template_body": s.template_body,
                "participants": s.participants
            }
            for s in scenario_repo.list_scenarios()
        ]
        return jsonify({"scenarios": scenarios})

    @bp.post("/scenarios")
    def save_scenario():
        data = request.get_json()
        scenario = Scenario(
            id=data.get("id"),
            name=data.get("name"),
            subject=data.get("subject"),
            template_body=data.get("template_body"),
            participants=data.get("participants", [])
        )
        scenario_repo.save_scenario(scenario)
        return jsonify({"status": "saved"})

    @bp.delete("/scenarios/<scenario_id>")
    def delete_scenario(scenario_id):
        scenario_repo.delete_scenario(scenario_id)
        return jsonify({"status": "deleted"})

    @bp.post("/draw")
    def draw_names():
        payload = request.get_json(silent=True) or {}
        send_mail = payload.get("send", True)
        scenario_id = payload.get("scenario_id")
        
        allowed_participants = None
        subject_template = None
        body_template = None
        scenario_name = None
        
        if scenario_id:
            scenario = scenario_repo.get_scenario(scenario_id)
            if scenario:
                allowed_participants = scenario.participants
                subject_template = scenario.subject
                body_template = scenario.template_body
                scenario_name = scenario.name

        assignments = draw_service.run_draw(
            send_notifications=send_mail,
            allowed_participants=allowed_participants,
            subject_template=subject_template,
            body_template=body_template,
            scenario_name=scenario_name
        )
        return jsonify(
            {
                "assignments": [
                    {
                        "drawer": pair.drawer.name,
                        "email": pair.drawer.email,
                    }
                    for pair in assignments
                ]
            }
        )

    return bp
