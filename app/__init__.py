from flask import Flask

from app.extensions import db
from app.routes.errors import register_error_handlers
from app.services.database import initialize_database, register_database_commands
from config import config_by_name


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=False)
    selected_config = config_name or "development"
    app.config.from_object(config_by_name.get(selected_config, config_by_name["development"]))

    initialize_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)
    register_database_commands(app)
    ensure_directories(app)

    with app.app_context():
        from app import models as registered_models  # noqa: F401

        initialize_database()

    return app


def initialize_extensions(app: Flask) -> None:
    db.init_app(app)


def register_blueprints(app: Flask) -> None:
    from app.routes.main import main_bp
    from app.routes.projects import projects_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(projects_bp)


def ensure_directories(app: Flask) -> None:
    for folder in (app.config["UPLOAD_FOLDER"], app.config["EXPORT_FOLDER"]):
        folder.mkdir(parents=True, exist_ok=True)
