from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.extensions import db
from app.models import Project
from app.services.project_service import (
    PROJECT_STATUS_OPTIONS,
    build_project_form_data,
    create_project,
    list_projects,
    validate_project_form,
)

projects_bp = Blueprint("projects", __name__, url_prefix="/projects")

@projects_bp.get("")
def index():
    projects = list_projects()
    return render_template("projects/index.html", projects=projects)


@projects_bp.route("/new", methods=["GET", "POST"])
def new_project():
    form_data = build_project_form_data()
    errors: dict[str, str] = {}

    if request.method == "POST":
        form_data = build_project_form_data(request.form)
        errors = validate_project_form(form_data)

        if not errors:
            project = create_project(form_data)
            flash("Proyecto creado correctamente.", "success")
            return redirect(url_for("projects.detail", project_id=project.id))

        flash("Revisa los datos del formulario para continuar.", "danger")

    return render_template(
        "projects/new.html",
        form_data=form_data,
        errors=errors,
        status_options=PROJECT_STATUS_OPTIONS,
    )


@projects_bp.get("/<int:project_id>")
def detail(project_id: int):
    project = db.get_or_404(Project, project_id)
    return render_template("projects/detail.html", project=project)
