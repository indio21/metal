from flask import Blueprint, render_template

projects_bp = Blueprint("projects", __name__, url_prefix="/projects")


@projects_bp.get("/new")
def new_project():
    return render_template("projects/new.html")
