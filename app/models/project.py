from app.extensions import db
from app.models.mixins import TimestampMixin


class Project(TimestampMixin, db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    part_number = db.Column(db.String(80), nullable=True)
    material = db.Column(db.String(80), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), nullable=False, default="draft")

    uploaded_models = db.relationship(
        "UploadedModel",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    drawing_jobs = db.relationship(
        "DrawingJob",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    export_files = db.relationship(
        "ExportFile",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Project {self.name}>"
