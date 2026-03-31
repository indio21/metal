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
    }
]


def initialize_database() -> None:
    db.create_all()
    synchronize_legacy_schema()
    seed_templates()


def synchronize_legacy_schema() -> None:
    inspector = inspect(db.engine)
    if "projects" not in inspector.get_table_names():
        return

    project_columns = {column["name"] for column in inspector.get_columns("projects")}
    with db.engine.begin() as connection:
        if "updated_at" not in project_columns:
            connection.execute(text("ALTER TABLE projects ADD COLUMN updated_at DATETIME"))
            connection.execute(
                text("UPDATE projects SET updated_at = created_at WHERE updated_at IS NULL")
            )


def seed_templates() -> None:
    if Template.query.count() > 0:
        return

    templates = [Template(**template_data) for template_data in DEFAULT_TEMPLATES]
    db.session.add_all(templates)
    db.session.commit()


def register_database_commands(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db_command() -> None:
        initialize_database()
        click.echo("Base de datos inicializada.")
