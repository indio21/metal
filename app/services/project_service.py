from collections.abc import Mapping

from app.extensions import db
from app.models import Project


PROJECT_STATUS_OPTIONS = [
    ("draft", "Borrador"),
    ("pending_upload", "Pendiente de modelo"),
    ("ready", "Listo para analisis"),
]


def list_projects() -> list[Project]:
    return Project.query.order_by(Project.created_at.desc()).all()


def build_project_form_data(source: Mapping[str, str] | None = None) -> dict[str, str]:
    source = source or {}
    return {
        "name": _clean_text(source.get("name")),
        "part_number": _clean_text(source.get("part_number")),
        "material": _clean_text(source.get("material")),
        "status": source.get("status", "draft").strip() or "draft",
        "notes": _clean_text(source.get("notes")),
    }


def validate_project_form(form_data: dict[str, str]) -> dict[str, str]:
    errors: dict[str, str] = {}
    valid_statuses = {value for value, _label in PROJECT_STATUS_OPTIONS}

    if not form_data["name"]:
        errors["name"] = "El nombre del proyecto es obligatorio."

    if form_data["status"] not in valid_statuses:
        errors["status"] = "Selecciona un estado valido."

    return errors


def create_project(form_data: dict[str, str]) -> Project:
    project = Project(
        name=form_data["name"],
        part_number=form_data["part_number"] or None,
        material=form_data["material"] or None,
        status=form_data["status"],
        notes=form_data["notes"] or None,
    )
    db.session.add(project)
    db.session.commit()
    return project


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    return value.strip()
