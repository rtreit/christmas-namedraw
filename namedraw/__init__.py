import os
from pathlib import Path
from flask import Flask, render_template
from dotenv import load_dotenv

from .config import AppConfig
from .routes import create_api_blueprint
from .services.draw import NameDrawService
from .services.mailer import GraphMailer
from .services.participants import ParticipantRepository
from .services.scenarios import ScenarioRepository
from .services.tokens import TokenCache
from .auth import auth_bp, login_required


def create_app(config_path: str | None = None) -> Flask:
    """Application factory for the modernized name draw experience."""
    
    load_dotenv()

    package_root = Path(__file__).resolve().parent
    project_root = package_root.parent

    app = Flask(
        __name__,
        static_folder=str(project_root / "static"),
        template_folder=str(project_root / "templates"),
    )
    
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-key-please-change")

    cfg = AppConfig.load(Path(config_path or "config.json"))

    participant_repo = ParticipantRepository(Path(cfg.participant_file))
    scenario_repo = ScenarioRepository(project_root / "data" / "scenarios.json")
    token_cache = TokenCache(Path(cfg.token_cache_file))
    mailer = GraphMailer(cfg, token_cache)
    draw_service = NameDrawService(participant_repo, mailer)

    app.register_blueprint(auth_bp)

    api_bp = create_api_blueprint(draw_service, participant_repo, scenario_repo)
    # Protect all API routes
    @api_bp.before_request
    @login_required
    def before_api_request():
        pass
        
    app.register_blueprint(api_bp)

    @app.get("/")
    @login_required
    def home():
        family = participant_repo.list_participants()
        scenarios = scenario_repo.list_scenarios()
        return render_template("index.html", family=family, scenario=cfg.scenario_name, scenarios=scenarios)
    
    @app.get("/admin")
    @login_required
    def admin():
        return render_template("admin.html")

    @app.get("/health")
    def healthcheck():
        return {"status": "ok"}

    return app
