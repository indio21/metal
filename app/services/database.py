import click
from flask import Flask
from sqlalchemy import inspect, text

from app.extensions import db
from app.models import Template


DEFAULT_TEMPLATES = [
    {
        "name": "Industrial basico A4",
        "code": "industrial-a4",
        "description": "Template preliminar con cajetin editable para piezas individuales.",
        "is_default": True,
    },
    {
        "name": "Industrial compacto A3",
        "code": "industrial-a3",
        "description": "Template compacto para piezas con revision rapida de taller.",
        "is_default": False,
    }
]


def initialize_database() -> None:
    db.create_all()
    synchronize_legacy_schema()
    seed_templates()


def synchronize_legacy_schema() -> None:
    inspector = inspect(db.engine)
    table_names = set(inspector.get_table_names())
    if "projects" not in table_names:
        return

    with db.engine.begin() as connection:
        project_columns = {column["name"] for column in inspector.get_columns("projects")}
        if "updated_at" not in project_columns:
            connection.execute(text("ALTER TABLE projects ADD COLUMN updated_at DATETIME"))
            connection.execute(
                text("UPDATE projects SET updated_at = created_at WHERE updated_at IS NULL")
            )
        if "revision" not in project_columns:
            connection.execute(text("ALTER TABLE projects ADD COLUMN revision VARCHAR(32)"))
            connection.execute(text("UPDATE projects SET revision = 'A' WHERE revision IS NULL"))
        if "author" not in project_columns:
            connection.execute(text("ALTER TABLE projects ADD COLUMN author VARCHAR(120)"))
        if "template_id" not in project_columns:
            connection.execute(text("ALTER TABLE projects ADD COLUMN template_id INTEGER"))
        if "drawing_jobs" in table_names:
            drawing_job_columns = {column["name"] for column in inspector.get_columns("drawing_jobs")}
            if "uploaded_model_id" not in drawing_job_columns:
                connection.execute(text("ALTER TABLE drawing_jobs ADD COLUMN uploaded_model_id INTEGER"))
            if "analyzer_backend" not in drawing_job_columns:
                connection.execute(text("ALTER TABLE drawing_jobs ADD COLUMN analyzer_backend VARCHAR(64)"))
            if "analysis_summary" not in drawing_job_columns:
                connection.execute(text("ALTER TABLE drawing_jobs ADD COLUMN analysis_summary TEXT"))


def seed_templates() -> None:
    existing_codes = {template.code for template in Template.query.all()}
    templates_to_add = [
        Template(**template_data)
        for template_data in DEFAULT_TEMPLATES
        if template_data["code"] not in existing_codes
    ]

    if templates_to_add:
        db.session.add_all(templates_to_add)
        db.session.commit()


def register_database_commands(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db_command() -> None:
        initialize_database()
        click.echo("Base de datos inicializada.")
