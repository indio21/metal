from collections.abc import Mapping

from sqlalchemy import func
from app.extensions import db
from app.models import Project, Template


PROJECT_STATUS_OPTIONS = [
    ("draft", "Borrador"),
    ("pending_upload", "Pendiente de modelo"),
    ("ready", "Listo para analisis"),
]


def list_projects() -> list[Project]:
    return Project.query.order_by(Project.updated_at.desc(), Project.created_at.desc()).all()


def get_project_dashboard_data() -> dict[str, object]:
    total_projects = Project.query.count()
    draft_count = Project.query.filter_by(status="draft").count()
    pending_upload_count = Project.query.filter_by(status="pending_upload").count()
    ready_count = Project.query.filter_by(status="ready").count()
    assigned_template_count = Project.query.filter(Project.template_id.isnot(None)).count()
    latest_update = db.session.query(func.max(Project.updated_at)).scalar()
    recent_projects = Project.query.order_by(Project.updated_at.desc()).limit(6).all()

    return {
        "total_projects": total_projects,
        "draft_count": draft_count,
        "pending_upload_count": pending_upload_count,
        "ready_count": ready_count,
        "assigned_template_count": assigned_template_count,
        "latest_update": latest_update,
        "recent_projects": recent_projects,
    }


def list_active_templates() -> list[Template]:
    return (
        Template.query.filter_by(is_active=True)
        .order_by(Template.is_default.desc(), Template.name.asc())
        .all()
    )


def build_project_form_data(
    source: Mapping[str, str] | None = None,
    project: Project | None = None,
) -> dict[str, str]:
    source = source or {}
    if project is not None and not source:
        return {
            "name": project.name,
            "part_number": project.part_number or "",
            "revision": project.revision or "A",
            "material": project.material or "",
            "author": project.author or "",
            "template_id": str(project.template_id or ""),
            "status": project.status,
            "notes": project.notes or "",
        }

    return {
        "name": _clean_text(source.get("name")),
        "part_number": _clean_text(source.get("part_number")),
        "revision": _clean_text(source.get("revision")) or "A",
        "material": _clean_text(source.get("material")),
        "author": _clean_text(source.get("author")),
        "template_id": _clean_text(source.get("template_id")),
        "status": source.get("status", "draft").strip() or "draft",
        "notes": _clean_text(source.get("notes")),
    }


def validate_project_form(
    form_data: dict[str, str],
    templates: list[Template],
) -> dict[str, str]:
    errors: dict[str, str] = {}
    valid_statuses = {value for value, _label in PROJECT_STATUS_OPTIONS}
    valid_template_ids = {str(template.id) for template in templates}

    if not form_data["name"]:
        errors["name"] = "El nombre de pieza es obligatorio."

    if not form_data["revision"]:
        errors["revision"] = "La revision es obligatoria."

    if form_data["status"] not in valid_statuses:
        errors["status"] = "Selecciona un estado valido."

    if form_data["template_id"] and form_data["template_id"] not in valid_template_ids:
        errors["template_id"] = "Selecciona un template valido."

    return errors


def create_project(form_data: dict[str, str]) -> Project:
    project = Project(
        name=form_data["name"],
        part_number=form_data["part_number"] or None,
        revision=form_data["revision"] or "A",
        material=form_data["material"] or None,
        author=form_data["author"] or None,
        template_id=int(form_data["template_id"]) if form_data["template_id"] else None,
        status=form_data["status"],
        notes=form_data["notes"] or None,
    )
    db.session.add(project)
    db.session.commit()
    return project


def update_project(project: Project, form_data: dict[str, str]) -> Project:
    project.name = form_data["name"]
    project.part_number = form_data["part_number"] or None
    project.revision = form_data["revision"] or "A"
    project.material = form_data["material"] or None
    project.author = form_data["author"] or None
    project.template_id = int(form_data["template_id"]) if form_data["template_id"] else None
    project.status = form_data["status"]
    project.notes = form_data["notes"] or None
    db.session.commit()
    return project


def delete_project(project: Project) -> None:
    db.session.delete(project)
    db.session.commit()


def rollback_session() -> None:
    db.session.rollback()


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    return value.strip()
